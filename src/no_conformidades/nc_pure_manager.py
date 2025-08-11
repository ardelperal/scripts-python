"""Manager puro para No Conformidades (refactor incremental).

Responsabilidad:
  - Consultar datasets relevantes (subset inicial) de No Conformidades.
  - Generar informe HTML mediante HTMLReportGenerator + build_table_html.
  - Emitir métricas estructuradas homogéneas.

No contiene lógica de scheduling ni registro de correos.
Se apoya directamente en conexiones inyectadas.

NOTA: Refactor incremental: sólo se incluyen algunas secciones iniciales (ARs próximas
      a vencer y NCs pendientes de control eficacia). El resto de secciones legacy
      permanecen en el manager antiguo hasta completar migración.
"""
from __future__ import annotations

import logging
from typing import Any

from common.html_report_generator import HTMLReportGenerator
from common.reporting.table_builder import build_table_html


class NoConformidadesManagerPure:
    """Manager desacoplado para generación parcial de informe NC."""

    def __init__(self, db_nc, logger: logging.Logger | None = None):
        self.db_nc = db_nc
        self.logger = logger or logging.getLogger("NoConformidadesManagerPure")
        self.html_generator = HTMLReportGenerator()

    # -------------------- Consultas --------------------
    def get_ars_proximas_vencer_calidad(self) -> list[dict[str, Any]]:
        try:
            query = """
                SELECT DISTINCT DateDiff('d',Now(),[FPREVCIERRE]) AS DiasParaCierre,
                       TbNoConformidades.CodigoNoConformidad,
                       TbNoConformidades.Nemotecnico,
                       TbNoConformidades.DESCRIPCION,
                       TbNoConformidades.RESPONSABLECALIDAD,
                       TbNoConformidades.FECHAAPERTURA,
                       TbNoConformidades.FPREVCIERRE
                FROM TbNoConformidades
                INNER JOIN (TbNCAccionCorrectivas
                  INNER JOIN TbNCAccionesRealizadas
                  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
                  AND DateDiff('d',Now(),[FPREVCIERRE]) < 16;
            """
            rows = self.db_nc.execute_query(query)
            self.logger.info(
                "ARs próximas a vencer (Calidad)",
                extra={
                    "event": "nc_section_fetch",
                    "section": "ars_proximas_calidad",
                    "rows": len(rows),
                },
            )
            return rows or []
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error consultando ARs próximas vencer: {e}")
            return []

    def get_ncs_pendientes_eficacia(self) -> list[dict[str, Any]]:
        try:
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad,
                       TbNoConformidades.Nemotecnico,
                       TbNoConformidades.DESCRIPCION,
                       TbNoConformidades.RESPONSABLECALIDAD,
                       TbNoConformidades.FECHACIERRE,
                       TbNoConformidades.FechaPrevistaControlEficacia,
                       DateDiff('d',Now(),[FechaPrevistaControlEficacia]) AS Dias
                FROM TbNoConformidades
                INNER JOIN (TbNCAccionCorrectivas
                  INNER JOIN TbNCAccionesRealizadas
                  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
                WHERE DateDiff('d',Now(),[FechaPrevistaControlEficacia]) < 30
                  AND TbNCAccionesRealizadas.FechaFinReal IS NOT NULL
                  AND TbNoConformidades.FECHACIERRE IS NOT NULL;
            """
            rows = self.db_nc.execute_query(query)
            self.logger.info(
                "NCs pendientes control eficacia",
                extra={
                    "event": "nc_section_fetch",
                    "section": "ncs_pendientes_eficacia",
                    "rows": len(rows),
                },
            )
            return rows or []
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error consultando NCs pendientes eficacia: {e}")
            return []

    def get_ncs_sin_acciones(self) -> list[dict[str, Any]]:
        """NCs sin acciones correctivas registradas."""
        try:
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad,
                                TbNoConformidades.Nemotecnico,
                                TbNoConformidades.DESCRIPCION,
                                TbNoConformidades.RESPONSABLECALIDAD,
                                TbNoConformidades.FECHAAPERTURA,
                                TbNoConformidades.FPREVCIERRE
                FROM TbNoConformidades
                LEFT JOIN TbNCAccionCorrectivas
                    ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
                WHERE TbNCAccionCorrectivas.IDNoConformidad IS NULL;
            """
            rows = self.db_nc.execute_query(query)
            self.logger.info(
                "NCs sin acciones",
                extra={
                    "event": "nc_section_fetch",
                    "section": "ncs_sin_acciones",
                    "rows": len(rows),
                },
            )
            return rows or []
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error consultando NCs sin acciones: {e}")
            return []

    def get_ars_para_replanificar(self) -> list[dict[str, Any]]:
        """ARs cuya FechaFinPrevista está <16 días (o pasada) y sin cierre."""
        try:
            query = """
                SELECT TbNoConformidades.CodigoNoConformidad,
                                TbNoConformidades.Nemotecnico,
                                TbNCAccionCorrectivas.AccionCorrectiva AS Accion,
                                TbNCAccionesRealizadas.AccionRealizada AS Tarea,
                                TbUsuariosAplicaciones.Nombre AS Tecnico,
                                TbNoConformidades.RESPONSABLECALIDAD,
                                TbNCAccionesRealizadas.FechaFinPrevista,
                                DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) AS Dias
                FROM (TbNoConformidades
                    INNER JOIN (TbNCAccionCorrectivas
                        INNER JOIN TbNCAccionesRealizadas
                        ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                    ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbUsuariosAplicaciones
                    ON TbNCAccionesRealizadas.Responsable = TbUsuariosAplicaciones.UsuarioRed
                WHERE DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) < 16
                    AND TbNCAccionesRealizadas.FechaFinReal IS NULL;
            """
            rows = self.db_nc.execute_query(query)
            self.logger.info(
                "ARs para replanificar",
                extra={
                    "event": "nc_section_fetch",
                    "section": "ars_para_replanificar",
                    "rows": len(rows),
                },
            )
            return rows or []
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error consultando ARs para replanificar: {e}")
            return []

    # ----------------- Informe HTML --------------------
    def generate_nc_report_html(self) -> str:
        """Genera informe parcial (secciones migradas). Vacío si no hay secciones con datos."""
        sections = [
            ("ARs Próximas a Vencer (Calidad)", self.get_ars_proximas_vencer_calidad()),
            (
                "NCs Pendientes de Control de Eficacia",
                self.get_ncs_pendientes_eficacia(),
            ),
            ("NCs Sin Acciones", self.get_ncs_sin_acciones()),
            ("ARs Para Replanificar", self.get_ars_para_replanificar()),
        ]
        non_empty = [(title, data) for title, data in sections if data]
        if not non_empty:
            self.logger.info(
                "Informe NC parcial vacío", extra={"event": "nc_report_empty"}
            )
            return ""
        parts: list[str] = []
        parts.append(
            self.html_generator.generar_header_moderno(
                "INFORME NO CONFORMIDADES (PARCIAL)"
            )
        )
        total_rows = 0
        for title, data in non_empty:
            total_rows += len(data)
            table_html = build_table_html(title, data, sort_headers=True)
            parts.append(table_html)
            self.logger.info(
                f"Sección {title} generada",
                extra={
                    "event": "nc_report_section",
                    "section": title.lower().replace(" ", "_"),
                    "metric_name": "nc_section_rows",
                    "metric_value": len(data),
                    "app": "NC",
                },
            )
        html = "".join(parts) + self.html_generator.generar_footer_moderno()
        self.logger.info(
            "Resumen informe NC parcial",
            extra={
                "event": "nc_report_summary",
                "metric_name": "nc_report_sections",
                "metric_value": len(non_empty),
                "total_rows": total_rows,
                "html_length": len(html),
                "app": "NC",
            },
        )
        self.logger.info(
            "Longitud informe NC parcial",
            extra={
                "event": "nc_report_length",
                "metric_name": "nc_report_length_chars",
                "metric_value": len(html),
                "app": "NC",
            },
        )
        return html
