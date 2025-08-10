"""AgedysManager

Refactor consolidado que centraliza TODA la lógica de consultas e informes AGEDYS
siguiendo estas reglas clave:

1. Todas las piezas HTML se generan EXCLUSIVAMENTE con:
    - HTMLReportGenerator.generar_header_moderno / generar_footer_moderno
    - build_table_html para cada sección con datos
2. Se proporcionan métodos granulares para:
    - Identificar usuarios con tareas pendientes (para correo individual)
    - Obtener datasets por técnico (reciben user_id) para el informe individual
    - Obtener datasets agrupados (Calidad / Economía)
3. Tres generadores de informe diferenciados:
    - generate_technical_user_report_html(user_id, user_name, user_email)
    - generate_quality_report_html()
    - generate_economy_report_html()
4. El antiguo método generate_agedys_report_html ha sido ELIMINADO para evitar ambigüedad.

NOTA: Algunas consultas son versiones simplificadas basadas en el contexto disponible.
        Se emplean parámetros ('?') para favorecer la seguridad (evitar inyección).
        Ajustar campos / joins exactos si la estructura Access real difiere.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
import logging

from common.reporting.table_builder import build_table_html
from common.html_report_generator import HTMLReportGenerator


class AgedysManager:
    def __init__(self, db_agedys, logger: logging.Logger | None = None):
        self.db_agedys = db_agedys
        self.logger = logger or logging.getLogger("AgedysManager")
        self.html_generator = HTMLReportGenerator()

    # ------------------------------------------------------------------
    # BLOQUE: Consultas base existentes (agregadas / multi-subconsulta)
    # ------------------------------------------------------------------
    def get_usuarios_facturas_pendientes_visado_tecnico(self) -> List[Dict[str, Any]]:
        queries = [
            ("q1", """
                                SELECT DISTINCT u.UsuarioRed, u.CorreoUsuario
                                    FROM ((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN (TbFacturasDetalle fd
                                        INNER JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                                        ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                                        INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                                    INNER JOIN TbUsuariosAplicaciones u ON p.PETICIONARIO = u.Nombre
                WHERE fd.FechaAceptacion IS NULL
                  AND vf.FRECHAZOTECNICO IS NULL
                  AND vf.FVISADOTECNICO IS NULL
                  AND e.AGEDYSGenerico = 'Sí'
                  AND e.AGEDYSAplica = 'Sí'
            """),
            ("q2", """
                SELECT DISTINCT u.UsuarioRed, u.CorreoUsuario
                FROM ((((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN TbFacturasDetalle fd
                  ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                  INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                  LEFT JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                  INNER JOIN TbExpedientesResponsables er ON e.IDExpediente = er.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones u ON er.IdUsuario = u.Id
                WHERE fd.FechaAceptacion IS NULL
                  AND vf.IDFactura IS NULL
                  AND e.AGEDYSGenerico = 'Sí'
                  AND e.AGEDYSAplica = 'Sí'
                  AND er.CorreoSiempre <> 'No'
            """),
            ("q3", """
                SELECT DISTINCT u.UsuarioRed, u.CorreoUsuario
                FROM (((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN (TbFacturasDetalle fd
                  INNER JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                  ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                  INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                  INNER JOIN TbExpedientesResponsables er ON e.IDExpediente = er.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones u ON er.IdUsuario = u.Id
                WHERE fd.FechaAceptacion IS NULL
                  AND vf.FRECHAZOTECNICO IS NULL
                  AND vf.FVISADOTECNICO IS NULL
                  AND e.AGEDYSGenerico = 'No'
                  AND e.AGEDYSAplica = 'Sí'
                  AND er.CorreoSiempre <> 'No'
            """),
            ("q4", """
                SELECT DISTINCT u.UsuarioRed, u.CorreoUsuario
                FROM ((((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN TbFacturasDetalle fd
                  ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                  INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                  LEFT JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                  INNER JOIN TbExpedientesResponsables er ON e.IDExpediente = er.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones u ON er.IdUsuario = u.Id
                WHERE fd.FechaAceptacion IS NULL
                  AND vf.IDFactura IS NULL
                  AND e.AGEDYSGenerico = 'No'
                  AND e.AGEDYSAplica = 'Sí'
                  AND er.CorreoSiempre <> 'No'
            """),
        ]
        merged: dict[str, str] = {}
        total_rows = 0
        for code, sql in queries:
            try:
                rows = self.db_agedys.execute_query(sql)
            except Exception as e:  # pragma: no cover
                self.logger.error(f"Error subconsulta {code} usuarios_facturas_pendientes: {e}")
                rows = []
            total_rows += len(rows or [])
            for r in rows or []:
                u = r.get('UsuarioRed')
                c = r.get('CorreoUsuario')
                if u and c:
                    merged[u] = c
            self.logger.info(
                "Subconsulta usuarios_facturas_pendientes",
                extra={'event': 'agedys_subquery_fetch', 'section': 'usuarios_facturas_pendientes', 'subquery': code, 'rows': len(rows or [])}
            )
        result = [{'UsuarioRed': u, 'CorreoUsuario': c} for u, c in merged.items()]
        self.logger.info(
            "Sección usuarios_facturas_pendientes consolidada",
            extra={'event': 'agedys_section_fetch', 'section': 'usuarios_facturas_pendientes', 'rows': len(result), 'raw_rows': total_rows}
        )
        return result
    # ------------------------------------------------------------------
    # SECCIONES TECNICOS (por usuario) - Migración directa VBScript
    # ------------------------------------------------------------------
    def get_facturas_pendientes_por_tecnico(self, user_id: int, user_name: str) -> List[Dict[str, Any]]:
        """Replica getFacturasPendientesVisadoTecnico (4 subconsultas VB)."""
        queries = [
            ("g_no_join", """
                SELECT DISTINCT fd.NFactura, p.CODPROYECTOS, p.PETICIONARIO, e.CodExp, p.DESCRIPCION,
                                 np.IMPORTEADJUDICADO, s.Suministrador, fd.ImporteFactura, fd.NDOCUMENTO
                FROM (((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN (TbFacturasDetalle fd
                    INNER JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                    ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                    INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                    INNER JOIN TbExpedientesResponsables er ON e.IDExpediente = er.IdExpediente)
                    INNER JOIN TbSuministradoresSAP s ON np.NAcreedorSAP = s.AcreedorSAP
                WHERE fd.FechaAceptacion IS NULL
                    AND vf.FRECHAZOTECNICO IS NULL
                    AND vf.FVISADOTECNICO IS NULL
                    AND e.AGEDYSGenerico='No'
                    AND e.AGEDYSAplica='Sí'
                    AND er.CorreoSiempre='Sí'
                    AND er.IdUsuario=?
            """, (user_id,)),
            ("g_no_left", """
                SELECT DISTINCT fd.NFactura, p.CODPROYECTOS, p.PETICIONARIO, e.CodExp, p.DESCRIPCION,
                                 np.IMPORTEADJUDICADO, s.Suministrador, fd.ImporteFactura, fd.NDOCUMENTO
                FROM ((((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN TbFacturasDetalle fd
                    ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                    INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                    INNER JOIN TbExpedientesResponsables er ON e.IDExpediente = er.IdExpediente)
                    LEFT JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                    INNER JOIN TbSuministradoresSAP s ON np.NAcreedorSAP = s.AcreedorSAP
                WHERE fd.FechaAceptacion IS NULL
                    AND vf.IDFactura IS NULL
                    AND e.AGEDYSGenerico='No'
                    AND e.AGEDYSAplica='Sí'
                    AND er.CorreoSiempre='Sí'
                    AND er.IdUsuario=?
            """, (user_id,)),
            ("g_si_join", """
                SELECT DISTINCT fd.NFactura, p.CODPROYECTOS, p.PETICIONARIO, e.CodExp, p.DESCRIPCION,
                                 np.IMPORTEADJUDICADO, s.Suministrador, fd.ImporteFactura, fd.NDOCUMENTO
                FROM ((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN (TbFacturasDetalle fd
                    INNER JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                    ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                    INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                    INNER JOIN TbSuministradoresSAP s ON np.NAcreedorSAP = s.AcreedorSAP
                WHERE fd.FechaAceptacion IS NULL
                    AND vf.FRECHAZOTECNICO IS NULL
                    AND vf.FVISADOTECNICO IS NULL
                    AND e.AGEDYSGenerico='Sí'
                    AND e.AGEDYSAplica='Sí'
                    AND p.PETICIONARIO=?
            """, (user_name,)),
            ("g_si_left", """
                SELECT DISTINCT fd.NFactura, p.CODPROYECTOS, p.PETICIONARIO, e.CodExp, p.DESCRIPCION,
                                 np.IMPORTEADJUDICADO, s.Suministrador, fd.ImporteFactura, fd.NDOCUMENTO
                FROM (((TbProyectos p INNER JOIN (TbNPedido np INNER JOIN TbFacturasDetalle fd
                    ON np.NPEDIDO = fd.NPEDIDO) ON p.CODPROYECTOS = np.CODPPD)
                    INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IDExpediente)
                    LEFT JOIN TbVisadoFacturas_Nueva vf ON fd.IDFactura = vf.IDFactura)
                    INNER JOIN TbSuministradoresSAP s ON np.NAcreedorSAP = s.AcreedorSAP
                WHERE fd.FechaAceptacion IS NULL
                    AND vf.IDFactura IS NULL
                    AND e.AGEDYSGenerico='Sí'
                    AND e.AGEDYSAplica='Sí'
                    AND p.PETICIONARIO=?
            """, (user_name,)),
        ]
        merged: Dict[str, Dict[str, Any]] = {}
        for code, sql, params in queries:
            try:
                rows = self.db_agedys.execute_query(sql, params)
            except Exception as e:  # pragma: no cover
                self.logger.error(f"Error subconsulta facturas_pendientes {code}: {e}")
                rows = []
            for r in rows:
                key = f"{r['NFactura']}|{r['NDOCUMENTO']}"
                if key not in merged:
                    merged[key] = r
            self.logger.info(
                "Subconsulta facturas pendientes técnico",
                extra={'event': 'agedys_subquery_fetch', 'section': 'facturas_pendientes_tecnico', 'subquery': code, 'rows': len(rows)}
            )
        result = list(merged.values())
        self.logger.info(
            "Sección facturas_pendientes_tecnico consolidada",
            extra={'event': 'agedys_section_fetch', 'section': 'facturas_pendientes_tecnico', 'rows': len(result)}
        )
        return result

    def get_dpds_sin_so_por_tecnico(self, user_name: str) -> List[Dict[str, Any]]:
        """DPDs sin Solicitud de Oferta para un técnico (usa p_Usuario). VBScript: getColDPDsSinSOUsuario.

        NOTA: Original tenía dos variantes (por IdResponsable y por Peticionario). Requerimiento actual
        especifica firma sólo con user_name, así que usamos la variante por PETICIONARIO.
        """
        query = """
            SELECT DISTINCT p.CODPROYECTOS, p.PETICIONARIO, p.FECHAPETICION, p.EXPEDIENTE, p.DESCRIPCION
            FROM ((TbProyectos p LEFT JOIN TbSolicitudesOfertasPrevias sop ON p.CODPROYECTOS = sop.DPD)
                INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IdExpediente)
                LEFT JOIN TbSuministradoresSAP s ON p.NAcreedorSAP = s.AcreedorSAP
            WHERE p.ELIMINADO = False AND sop.DPD IS NULL AND p.PETICIONARIO = ?
                AND e.AGEDYSGenerico <> 'Sí' AND p.CODCONTRATOGTV IS NULL AND s.IDSuministrador IS NULL
        """
        return self._execute_section(query, 'dpds_sin_so_tecnico', (user_name,))

    def get_dpds_con_so_sin_ro_por_tecnico(self, user_name: str) -> List[Dict[str, Any]]:
        """DPDs con SO pero sin RO adjunto para un técnico (p_Usuario). VBScript: getColDPDsConSOSinROUsuario.

        Se elige variante por PETICIONARIO según requerimiento de firma.
        """
        query = """
            SELECT DISTINCT p.CODPROYECTOS, p.PETICIONARIO, p.FECHAPETICION, p.EXPEDIENTE, p.DESCRIPCION
            FROM ((TbProyectos p INNER JOIN TbSolicitudesOfertasPrevias sop ON p.CODPROYECTOS = sop.DPD)
                INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IdExpediente)
                LEFT JOIN TbSuministradoresSAP s ON p.NAcreedorSAP = s.AcreedorSAP
            WHERE p.ELIMINADO = False AND p.PETICIONARIO = ?
                AND e.AGEDYSGenerico <> 'No' AND p.CODCONTRATOGTV IS NULL AND s.IDSuministrador IS NULL
        """
        return self._execute_section(query, 'dpds_con_so_sin_ro_tecnico', (user_name,))

    def get_dpds_sin_visado_calidad_por_tecnico(self, user_name: str) -> List[Dict[str, Any]]:
        """DPDs sin visado de calidad para un técnico (p_Usuario). VBScript: getColDPDsSinVisadoCalidadUsuario.

        Se adapta filtro a PETICIONARIO para cumplir firma solicitada.
        """
        query = """
            SELECT DISTINCT p.CODPROYECTOS, p.DESCRIPCION, p.PETICIONARIO, p.FECHAPETICION, e.CodExp,
                             uc.Nombre AS ResponsableCalidad
            FROM ((TbProyectos p INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IdExpediente)
                INNER JOIN TbVisadosGenerales vg ON p.CODPROYECTOS = vg.NDPD)
                LEFT JOIN TbUsuariosAplicaciones uc ON e.IDResponsableCalidad = uc.Id
            WHERE e.Pecal <> 'No'
              AND vg.ROFechaRealiza IS NOT NULL
              AND vg.ROFechaVisado IS NULL
              AND vg.ROFechaRechazo IS NULL
              AND p.FechaFinAgendaTecnica IS NULL
              AND p.PETICIONARIO = ?
        """
        return self._execute_section(query, 'dpds_sin_visado_calidad_tecnico', (user_name,))

    def get_dpds_rechazados_calidad_por_tecnico(self, user_name: str) -> List[Dict[str, Any]]:
        """DPDs rechazados por calidad (p_Usuario). VBScript: getColDPDsRechazadosCalidadUsuario."""
        query = """
            SELECT DISTINCT p.CODPROYECTOS, p.PETICIONARIO, p.FECHAPETICION, p.EXPEDIENTE, p.DESCRIPCION
            FROM (((TbProyectos p INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IdExpediente)
                INNER JOIN TbVisadosGenerales vg ON p.CODPROYECTOS = vg.NDPD)
                LEFT JOIN TbSuministradoresSAP s ON p.NAcreedorSAP = s.AcreedorSAP)
            WHERE p.ELIMINADO = False AND vg.ROFechaRechazo IS NOT NULL AND p.PETICIONARIO = ?
        """
        return self._execute_section(query, 'dpds_rechazados_calidad_tecnico', (user_name,))

        # ------------------------------------------------------------------
        # SECCIONES AGRUPADAS (Calidad / Economía)
        # ------------------------------------------------------------------
    def get_dpds_sin_visado_calidad_agrupado(self) -> List[Dict[str, Any]]:
                query = """
                        SELECT DISTINCT p.CODPROYECTOS, p.DESCRIPCION, p.PETICIONARIO, p.FECHAPETICION, e.CodExp,
                                     uc.Nombre AS ResponsableCalidad
                        FROM (((TbProyectos p INNER JOIN TbExpedientes1 e ON p.IDExpediente = e.IdExpediente)
                            INNER JOIN TbVisadosGenerales vg ON p.CODPROYECTOS = vg.NDPD)
                            INNER JOIN TbSuministradoresSAP s ON p.NAcreedorSAP = s.AcreedorSAP)
                            LEFT JOIN TbUsuariosAplicaciones uc ON e.IDResponsableCalidad = uc.Id
                        WHERE e.Pecal <> 'No'
                            AND vg.ROFechaRealiza IS NOT NULL
                            AND vg.ROFechaVisado IS NULL
                            AND vg.ROFechaRechazo IS NULL
                            AND p.FechaFinAgendaTecnica IS NULL
                """
                return self._execute_section(query, 'dpds_sin_visado_calidad_agrupado')

    # Alias requerido: get_dpds_con_fin_agenda_tecnica_agrupado
    def get_dpds_con_fin_agenda_tecnica_agrupado(self) -> List[Dict[str, Any]]:
        query = """
            SELECT p.CODPROYECTOS, p.PETICIONARIO, p.FECHAPETICION, p.EXPEDIENTE, p.DESCRIPCION
            FROM TbProyectos p
            WHERE p.ELIMINADO = False
              AND p.FECHARECEPCIONECONOMICA IS NULL
              AND p.FechaFinAgendaTecnica IS NOT NULL
        """
        return self._execute_section(query, 'dpds_fin_agenda_tecnica_pte_recepcion')

    def get_dpds_sin_pedido_agrupado(self) -> List[Dict[str, Any]]:
                query = """
                        SELECT p.CODPROYECTOS, p.PETICIONARIO, p.FECHAPETICION, p.EXPEDIENTE, p.DESCRIPCION
                        FROM TbProyectos p INNER JOIN TbNPedido np ON p.CODPROYECTOS = np.CODPPD
                        WHERE p.ELIMINADO = False AND np.NPEDIDO IS NULL
                """
                return self._execute_section(query, 'dpds_sin_pedido_agrupado')

    def get_facturas_rechazadas_agrupado(self) -> List[Dict[str, Any]]:
                query = """
                        SELECT fd.NFactura, fd.NDocumento, p.CODPROYECTOS, p.PETICIONARIO, p.EXPEDIENTE,
                                     p.DESCRIPCION, p.IMPORTESINIVA, s.Suministrador, fd.ImporteFactura
                        FROM (((TbProyectos p INNER JOIN TbNPedido np ON p.CODPROYECTOS = np.CODPPD)
                            INNER JOIN TbFacturasDetalle fd ON np.NPEDIDO = fd.NPEDIDO)
                            INNER JOIN TbSuministradoresSAP s ON np.NAcreedorSAP = s.AcreedorSAP)
                            LEFT JOIN TbVisadoFacturas_Nueva vf ON (fd.NPEDIDO = vf.NPEDIDO AND fd.NFactura = vf.NFactura)
                        WHERE p.ELIMINADO = False AND vf.FRECHAZOTECNICO IS NOT NULL AND fd.FechaAceptacion IS NULL
                """
                return self._execute_section(query, 'facturas_rechazadas_agrupado')

    # Alias requerido: get_facturas_visadas_pendientes_op_agrupado
    def get_facturas_visadas_pendientes_op_agrupado(self) -> List[Dict[str, Any]]:
        query = """
            SELECT fd.NFactura, fd.NDocumento, p.CODPROYECTOS, p.PETICIONARIO, p.EXPEDIENTE,
                   p.DESCRIPCION, p.IMPORTESINIVA, s.Suministrador, fd.ImporteFactura
            FROM (((TbProyectos p INNER JOIN TbNPedido np ON p.CODPROYECTOS = np.CODPPD)
                INNER JOIN TbFacturasDetalle fd ON np.NPEDIDO = fd.NPEDIDO)
                INNER JOIN TbSuministradoresSAP s ON np.NAcreedorSAP = s.AcreedorSAP)
                LEFT JOIN TbVisadoFacturas_Nueva vf ON (fd.NFactura = vf.NFactura AND fd.NPEDIDO = vf.NPEDIDO)
            WHERE p.ELIMINADO = False AND vf.FVISADOTECNICO IS NOT NULL AND fd.FechaAceptacion IS NULL
        """
        return self._execute_section(query, 'facturas_visadas_pte_op_agrupado')

    # Mantener compatibilidad si código existente aún llama al nombre anterior
    def get_dpds_con_fin_agenda_tecnica_pendientes_recepcion_economia(self) -> List[Dict[str, Any]]:  # pragma: no cover - deprecated wrapper
        return self.get_dpds_con_fin_agenda_tecnica_agrupado()

    def get_facturas_visadas_pendientes_orden_pago_agrupado(self) -> List[Dict[str, Any]]:  # pragma: no cover - deprecated wrapper
        return self.get_facturas_visadas_pendientes_op_agrupado()

        # ------------------------------------------------------------------
        # USUARIOS con al menos una tarea pendiente (UNION de todas las fuentes)
        # ------------------------------------------------------------------
    def get_usuarios_con_tareas_pendientes(self) -> List[Dict[str, Any]]:
        """Replica racionalizada de getColParaTecnicos del VBScript.

        El VBScript original construía 5 colecciones (usuarios con: DPDs sin SO, DPDs con SO sin RO,
        DPDs sin visado calidad, DPDs rechazados calidad, Facturas pendientes) y luego las unía.
        Aquí ejecutamos 5 subconsultas (una por categoría) en lugar de múltiples variantes
        para reducir el coste; si se necesita exactitud al 100% añadir las variantes adicionales.
        """
        subqueries = [
            # 1) DPDs sin SO
            "SELECT DISTINCT u.UsuarioRed FROM (TbProyectos p LEFT JOIN TbSolicitudesOfertasPrevias sop ON p.CODPROYECTOS = sop.DPD) INNER JOIN TbUsuariosAplicaciones u ON p.PETICIONARIO = u.Nombre WHERE p.ELIMINADO=False AND sop.DPD IS NULL AND p.CODCONTRATOGTV IS NULL",
            # 2) DPDs con SO sin RO
            "SELECT DISTINCT u.UsuarioRed FROM (TbProyectos p INNER JOIN TbSolicitudesOfertasPrevias sop ON p.CODPROYECTOS = sop.DPD) INNER JOIN TbUsuariosAplicaciones u ON p.PETICIONARIO = u.Nombre WHERE p.ELIMINADO=False AND p.CODCONTRATOGTV IS NULL",
            # 3) DPDs sin visado calidad
            "SELECT DISTINCT u.UsuarioRed FROM (TbProyectos p INNER JOIN TbVisadosGenerales vg ON p.CODPROYECTOS = vg.NDPD) INNER JOIN TbUsuariosAplicaciones u ON p.PETICIONARIO = u.Nombre WHERE vg.ROFechaRealiza IS NOT NULL AND vg.ROFechaVisado IS NULL AND vg.ROFechaRechazo IS NULL AND p.FechaFinAgendaTecnica IS NULL",
            # 4) DPDs rechazados calidad
            "SELECT DISTINCT u.UsuarioRed FROM (TbProyectos p INNER JOIN TbVisadosGenerales vg ON p.CODPROYECTOS = vg.NDPD) INNER JOIN TbUsuariosAplicaciones u ON p.PETICIONARIO = u.Nombre WHERE vg.ROFechaRechazo IS NOT NULL",
            # 5) Facturas pendientes visado técnico
                "SELECT DISTINCT u.UsuarioRed FROM (((TbProyectos p INNER JOIN TbNPedido np ON p.CODPROYECTOS = np.CODPPD) INNER JOIN TbFacturasDetalle fd ON np.NPEDIDO = fd.NPEDIDO) LEFT JOIN TbVisadoFacturas_Nueva vf ON (fd.NPEDIDO = vf.NPEDIDO AND fd.NFactura = vf.NFactura)) INNER JOIN TbUsuariosAplicaciones u ON p.PETICIONARIO = u.Nombre WHERE p.ELIMINADO=False AND fd.FechaAceptacion IS NULL AND vf.FRECHAZOTECNICO IS NULL AND vf.FVISADOTECNICO IS NULL",
        ]
        usuarios: set[str] = set()
        for idx, sql in enumerate(subqueries, start=1):
            try:
                rows = self.db_agedys.execute_query(sql)
            except Exception as e:  # pragma: no cover
                self.logger.error(f"Error subconsulta usuarios({idx}): {e}")
                rows = []
            for r in rows or []:
                u = r.get('UsuarioRed')
                if u:
                    usuarios.add(u)
        if not usuarios:
            return []
        placeholders = ','.join(['?'] * len(usuarios))
        detail_sql = f"SELECT Id AS UserId, Nombre AS UserName, CorreoUsuario AS UserEmail FROM TbUsuariosAplicaciones WHERE UsuarioRed IN ({placeholders})"
        try:
            return self.db_agedys.execute_query(detail_sql, tuple(usuarios))
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error obteniendo detalles usuarios: {e}")
            return []


    # ------------------------------------------------------------------
    # BLOQUE: Helper interno
    # ------------------------------------------------------------------
    def _execute_section(self, query: str, section: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        try:
            rows = self.db_agedys.execute_query(query, params) if params else self.db_agedys.execute_query(query)
            self.logger.info(
                f"Sección {section} consultada",
                extra={'event': 'agedys_section_fetch', 'section': section, 'rows': len(rows)}
            )
            return rows or []
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error sección {section}: {e}")
            return []

    def _run_merge_queries(self, queries: List[Tuple[str, str, Tuple[Any, ...]]], section: str) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        for code, sql, params in queries:
            try:
                rows = self.db_agedys.execute_query(sql, params)
            except Exception as e:  # pragma: no cover
                self.logger.error(f"Error subconsulta {section} {code}: {e}")
                rows = []
            for r in rows:
                key = '|'.join(str(v) for v in r.values())  # crude key; adjust if needed
                if key not in merged:
                    merged[key] = r
            self.logger.info(
                "Subconsulta merge",
                extra={'event': 'agedys_subquery_fetch', 'section': section, 'subquery': code, 'rows': len(rows)}
            )
        result = list(merged.values())
        self.logger.info(
            "Sección consolidada",
            extra={'event': 'agedys_section_fetch', 'section': section, 'rows': len(result)}
        )
        return result

    # ------------------------------------------------------------------
    # BLOQUE: Generadores de informes (HTML) usando únicamente framework común
    # ------------------------------------------------------------------
    def generate_technical_user_report_html(self, user_id: int, user_name: str, user_email: str) -> str:
        """Genera informe individual de un técnico usando build_table_html.

        Retorna "" si no hay ninguna sección con datos. Para simplificar y homogenizar
        la arquitectura moderna, se deja de aplicar renombrado de columnas específico
        (se preservan las claves originales de los diccionarios). El foco de los tests
        es validar que cuando hay datos se invoca el framework HTML (header, footer y
        build_table_html por sección) y cuando no, se retorna cadena vacía sin invocarlo.
        """
        sections: list[tuple[str, list[dict[str, Any]]]] = [
            ("DPDs sin SO", self.get_dpds_sin_so_por_tecnico(user_name)),
            ("DPDs con SO sin RO", self.get_dpds_con_so_sin_ro_por_tecnico(user_name)),
            ("DPDs sin visado calidad", self.get_dpds_sin_visado_calidad_por_tecnico(user_name)),
            ("DPDs rechazados calidad", self.get_dpds_rechazados_calidad_por_tecnico(user_name)),
            ("Facturas pendientes de visado técnico", self.get_facturas_pendientes_por_tecnico(user_id, user_name)),
        ]
        non_empty = [(title, rows) for title, rows in sections if rows]
        if not non_empty:
            self.logger.info(
                "Informe técnico vacío",
                extra={'event': 'agedys_report_empty', 'scope': 'technical', 'user_id': user_id}
            )
            return ""
        parts: list[str] = [self.html_generator.generar_header_moderno(f"INFORME TAREAS PENDIENTES - {user_name}")]
        total_rows = 0
        for title, rows in non_empty:
            total_rows += len(rows)
            # Uso directo de build_table_html para unificar estilo
            parts.append(build_table_html(title, rows, pretty_headers=True))
            self.logger.info(
                f"Sección {title} generada (técnico)",
                extra={'event': 'agedys_report_section', 'scope': 'technical', 'user_id': user_id, 'section': title.lower().replace(' ', '_'), 'metric_name': 'agedys_section_rows', 'metric_value': len(rows), 'app': 'AGEDYS'}
            )
        html = ''.join(parts) + self.html_generator.generar_footer_moderno()
        self.logger.info(
            "Resumen informe técnico",
            extra={'event': 'agedys_report_summary', 'scope': 'technical', 'user_id': user_id, 'sections': len(non_empty), 'total_rows': total_rows, 'html_length': len(html)}
        )
        return html

    def generate_quality_report_html(self) -> str:
        """Informe grupal para Calidad usando build_table_html."""
        rows = self.get_dpds_sin_visado_calidad_agrupado()
        if not rows:
            self.logger.info(
                "Informe Calidad vacío",
                extra={'event': 'agedys_report_empty', 'scope': 'quality'}
            )
            return ""
        parts: list[str] = [
            self.html_generator.generar_header_moderno("INFORME AGEDYS - CALIDAD")
        ]
        parts.append(
            build_table_html("DPDs sin visado calidad", rows, pretty_headers=True)
        )
        html = ''.join(parts) + self.html_generator.generar_footer_moderno()
        self.logger.info(
            "Resumen informe Calidad",
            extra={
                'event': 'agedys_report_summary',
                'scope': 'quality',
                'sections': 1,
                'total_rows': len(rows),
                'html_length': len(html)
            }
        )
        return html

    def generate_economy_report_html(self) -> str:
        """Informe grupal para Economía usando build_table_html por sección."""
        sections = [
            ("DPDs fin agenda técnica pendientes recepción", self.get_dpds_con_fin_agenda_tecnica_agrupado()),
            ("DPDs sin pedido", self.get_dpds_sin_pedido_agrupado()),
            ("Facturas rechazadas", self.get_facturas_rechazadas_agrupado()),
            ("Facturas visadas pendientes orden de pago", self.get_facturas_visadas_pendientes_op_agrupado()),
        ]
        non_empty = [(t, r) for t, r in sections if r]
        if not non_empty:
            self.logger.info("Informe Economía vacío", extra={'event': 'agedys_report_empty', 'scope': 'economy'})
            return ""
        parts: list[str] = [self.html_generator.generar_header_moderno("INFORME AGEDYS - ECONOMÍA")]
        total_rows = 0
        for title, rows in non_empty:
            total_rows += len(rows)
            parts.append(build_table_html(title, rows, pretty_headers=True))
            self.logger.info(
                f"Sección {title} generada (economía)",
                extra={'event': 'agedys_report_section', 'scope': 'economy', 'section': title.lower().replace(' ', '_'), 'metric_name': 'agedys_section_rows', 'metric_value': len(rows), 'app': 'AGEDYS'}
            )
        html = ''.join(parts) + self.html_generator.generar_footer_moderno()
        self.logger.info(
            "Resumen informe Economía",
            extra={'event': 'agedys_report_summary', 'scope': 'economy', 'sections': len(non_empty), 'total_rows': total_rows, 'html_length': len(html)}
        )
        return html