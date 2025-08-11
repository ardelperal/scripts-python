"""BrassManager refactorizado (sólo lógica de negocio BRASS).

Responsabilidades:
  - Consultar equipos fuera de calibración (una sola consulta optimizada)
  - Generar informe HTML usando utilidades comunes.

No contiene lógica de scheduling, envío/registro de correos ni gestión de tareas.
Esas responsabilidades se delegan a capas superiores (task / orchestrator).
"""
from __future__ import annotations

import logging
from typing import Any

from common.html_report_generator import HTMLReportGenerator
from common.reporting.table_builder import build_table_html
from common.reporting.table_configurations import BRASS_TABLE_CONFIGURATIONS  # type: ignore


class BrassManager:
    """Manager independiente para lógica BRASS."""

    def __init__(self, db_brass, db_tareas, logger: logging.Logger | None = None):
        self.db_brass = db_brass
        self.db_tareas = db_tareas
        self.logger = logger or logging.getLogger("BrassManager")
        self.html_generator = HTMLReportGenerator()

    # ---------------------------- Datos ---------------------------------
    def get_equipment_out_of_calibration(self) -> list[dict[str, Any]]:
        """Devuelve equipos activos cuya última calibración está vencida o inexistente.

        Implementación optimizada: una sola consulta con subconsulta (MAX fecha fin).
        """
        try:
            # En Microsoft Access, reutilizar el mismo alias puede causar referencia circular.
            # Usamos un alias interno distinto (UltFin) y lo exponemos como FechaFinCalibracion.
            query = """
                SELECT e.IDEquipoMedida,
                       e.NOMBRE,
                       e.NS,
                       e.PN,
                       e.MARCA,
                       e.MODELO,
                       UltFin.UltimaFin AS FechaFinCalibracion
                FROM TbEquiposMedida AS e
                LEFT JOIN (
                    SELECT IDEquipoMedida, MAX(FechaFinCalibracion) AS UltimaFin
                    FROM TbEquiposMedidaCalibraciones
                    GROUP BY IDEquipoMedida
                ) AS UltFin ON e.IDEquipoMedida = UltFin.IDEquipoMedida
                WHERE e.FechaFinServicio IS NULL
                  AND (UltFin.UltimaFin IS NULL OR UltFin.UltimaFin <= Date())
            """
            rows = self.db_brass.execute_query(query)
            self.logger.info(
                "Equipos fuera de calibración obtenidos",
                extra={"event": "brass_out_of_calibration", "count": len(rows)},
            )
            return rows or []
        except Exception as e:  # pragma: no cover - defensivo
            self.logger.error(f"Error consultando equipos fuera de calibración: {e}")
            return []

    # ------------------------- Informe HTML ----------------------------
    def generate_brass_report_html(self) -> str:
        """Genera informe HTML de equipos fuera de calibración.

        Vacío si no hay datos.
        """
        data = self.get_equipment_out_of_calibration()
        if not data:
            self.logger.info(
                "Sin equipos fuera de calibración",
                extra={"event": "brass_report_empty"},
            )
            return ""
        header = self.html_generator.generar_header_moderno(
            "INFORME DE AVISOS DE EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN"
        )
        # Usar configuración centralizada (primer y único key por ahora)
        cfg = BRASS_TABLE_CONFIGURATIONS["equipment_out_of_calibration"]
        table_html = build_table_html(cfg["title"], data, sort_headers=True)
        footer = self.html_generator.generar_footer_moderno()
        html = header + table_html + footer
        self.logger.info(
            "Informe BRASS generado",
            extra={
                "event": "brass_report_generated",
                "rows": len(data),
                "length": len(html),
            },
        )
        return html

    # Backwards compatibility: mantener nombre anterior en tests si existiera
    def generate_html_report(
        self, equipment_list: list[dict[str, Any]] | None = None
    ) -> str:  # pragma: no cover (compat)
        if equipment_list is not None:
            # Si se pasa lista, replicar antiguo comportamiento filtrando sólo si lista no vacía.
            if not equipment_list:
                return ""
            # Construye directamente usando lista proporcionada
            header = self.html_generator.generar_header_moderno(
                "INFORME DE AVISOS DE EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN"
            )
            table_html = build_table_html(
                "Equipos de Medida Fuera de Calibración",
                equipment_list,
                sort_headers=True,
            )
            return header + table_html + self.html_generator.generar_footer_moderno()
        return self.generate_brass_report_html()
