"""AgedysPureManager

Responsabilidades:
    - Encapsular consultas de negocio AGEDYS (usuarios facturas pendientes + DPDs varias situaciones).
    - Generar informe HTML moderno reutilizando HTMLReportGenerator y build_table_html.
    - Logging estructurado homogéneo (event, section, metric_name, metric_value, app="AGEDYS").

Notas:
    - La sección "usuarios_facturas_pendientes" replica la lógica legacy compuesta de 4 consultas unificadas por UsuarioRed.
    - Consultas marcadas como 'Simplificado' deben ajustarse si el esquema real difiere; placeholders iniciales para completar en siguientes iteraciones.
    - No gestiona scheduling ni registro de correos (responsabilidad de AgedysTask).
"""
from __future__ import annotations

from typing import List, Dict, Any
import logging

from src.common.reporting.table_builder import build_table_html
from src.common.html_report_generator import HTMLReportGenerator


class AgedysPureManager:
    def __init__(self, db_agedys, logger: logging.Logger | None = None):
        self.db_agedys = db_agedys
        self.logger = logger or logging.getLogger("AgedysPureManager")
        self.html_generator = HTMLReportGenerator()

    # ---------------------- Consultas ----------------------
    def get_usuarios_facturas_pendientes_visado_tecnico(self) -> List[Dict[str, Any]]:
                """Replica la lógica legacy: 4 consultas combinadas por UsuarioRed.

                Se unifican resultados en un diccionario para evitar duplicados y luego se devuelve lista.
                """
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
                                usuario = r.get('UsuarioRed')
                                correo = r.get('CorreoUsuario')
                                if usuario and correo:
                                        merged[usuario] = correo
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

    def get_dpds_sin_visado_calidad(self) -> List[Dict[str, Any]]:
        query = """
            SELECT DISTINCT e.CODPROYECTOS, e.CODIGO, e.Descripcion
            FROM TbExpedientes1 e
            LEFT JOIN TbVisadoFacturas_Nueva vf ON e.IDExpediente = vf.IDExpediente
            WHERE e.AGEDYSAplica = 'Sí'
              AND vf.IDExpediente IS NULL;
        """  # Simplificado; ajustar a estructura real si difiere
        return self._execute_section(query, 'dpds_sin_visado_calidad')

    def get_dpds_rechazados_calidad(self) -> List[Dict[str, Any]]:
        query = """
            SELECT DISTINCT e.CODPROYECTOS, e.CODIGO, e.Descripcion, vf.FRECHAZOTECNICO
            FROM TbExpedientes1 e
              INNER JOIN TbVisadoFacturas_Nueva vf ON e.IDExpediente = vf.IDExpediente
            WHERE vf.FRECHAZOTECNICO IS NOT NULL;
        """  # Simplificado
        return self._execute_section(query, 'dpds_rechazados_calidad')

    def get_dpds_sin_pedido(self) -> List[Dict[str, Any]]:
        query = """
            SELECT DISTINCT e.CODPROYECTOS, e.CODIGO, e.Descripcion
            FROM TbExpedientes1 e
            LEFT JOIN TbNPedido np ON e.IDExpediente = np.IDExpediente
            WHERE np.NPEDIDO IS NULL AND e.AGEDYSAplica = 'Sí';
        """  # Simplificado
        return self._execute_section(query, 'dpds_sin_pedido')

    def _execute_section(self, query: str, section: str) -> List[Dict[str, Any]]:
        try:
            rows = self.db_agedys.execute_query(query)
            self.logger.info(
                f"Sección {section} consultada",
                extra={'event': 'agedys_section_fetch', 'section': section, 'rows': len(rows)}
            )
            return rows or []
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error sección {section}: {e}")
            return []

    # -------------------- Informe HTML --------------------
    def generate_agedys_report_html(self) -> str:
        sections = [
            ("Usuarios con facturas pendientes de visado técnico", self.get_usuarios_facturas_pendientes_visado_tecnico()),
            ("DPDs sin visado calidad", self.get_dpds_sin_visado_calidad()),
            ("DPDs rechazados calidad", self.get_dpds_rechazados_calidad()),
            ("DPDs sin pedido", self.get_dpds_sin_pedido()),
        ]
        non_empty = [(title, data) for title, data in sections if data]
        if not non_empty:
            self.logger.info("Informe AGEDYS vacío", extra={'event': 'agedys_report_empty'})
            return ""
        parts: list[str] = []
        parts.append(self.html_generator.generar_header_moderno("INFORME TAREAS PENDIENTES (AGEDYS)"))
        total_rows = 0
        for title, data in non_empty:
            total_rows += len(data)
            parts.append(build_table_html(title, data, sort_headers=True))
            self.logger.info(
                f"Sección {title} generada",
                extra={'event': 'agedys_report_section', 'section': title.lower().replace(' ', '_'), 'metric_name': 'agedys_section_rows', 'metric_value': len(data), 'app': 'AGEDYS'}
            )
        html = ''.join(parts) + self.html_generator.generar_footer_moderno()
        self.logger.info(
            "Resumen informe AGEDYS",
            extra={'event': 'agedys_report_summary', 'metric_name': 'agedys_report_sections', 'metric_value': len(non_empty), 'total_rows': total_rows, 'html_length': len(html), 'app': 'AGEDYS'}
        )
        self.logger.info(
            "Longitud informe AGEDYS",
            extra={'event': 'agedys_report_length', 'metric_name': 'agedys_report_length_chars', 'metric_value': len(html), 'app': 'AGEDYS'}
        )
        return html
