"""Tests modernos para No Conformidades (sin legado)."""
from __future__ import annotations

import unittest

from no_conformidades.no_conformidades_manager import NoConformidadesManager


class TestNoConformidadesManagerModern(unittest.TestCase):
    def setUp(self):
        self.manager = NoConformidadesManager()

    def tearDown(self):  # pragma: no cover
        try:
            self.manager.close_connections()
        except Exception:
            pass

    def test_initialization_core_fields(self):
        self.assertEqual(self.manager.name, "NoConformidades")
        self.assertIn("NCTecnico", self.manager.task_names)
        self.assertIn("NCCalidad", self.manager.task_names)
        self.assertIsInstance(self.manager.css_content, str)

    def test_modern_technical_report_html(self):
        ars_15 = [
            {
                "CodigoNoConformidad": "NC-1",
                "Nemotecnico": "TEC1",
                "AccionCorrectiva": "Acción",
                "AccionRealizada": "Tarea",
                "FechaInicio": "2024-01-01",
                "FechaFinPrevista": "2024-01-10",
                "Nombre": "Tecnico 1",
                "DiasParaCaducar": 5,
                "CorreoCalidad": "calidad@example.com",
            }
        ]
        html = self.manager.html_generator.generar_reporte_tecnico_moderno(
            ars_15, [], []
        )
        self.assertIn("Informe de Acciones Correctivas - Técnicos", html)
        self.assertIn("NC-1", html)

    def test_modern_quality_report_html(self):
        ncs_eficacia = [
            {
                "CodigoNoConformidad": "NC-2",
                "Nemotecnico": "TEC2",
                "DESCRIPCION": "Desc",
                "RESPONSABLECALIDAD": "Resp",
                "FECHACIERRE": "2024-01-05",
                "FechaPrevistaControlEficacia": "2024-01-20",
                "Dias": 10,
            }
        ]
        html = self.manager.html_generator.generar_reporte_calidad_moderno(
            [], ncs_eficacia, [], []
        )
        self.assertIn("No Conformidades Pendientes de Control de Eficacia", html)
        self.assertIn("NC-2", html)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
