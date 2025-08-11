import unittest
from unittest.mock import Mock, patch

from common.db.database import AccessDatabase
from expedientes.expedientes_manager import ExpedientesManager


class TestExpedientesManagerReport(unittest.TestCase):
    def setUp(self):
        self.db_exped = Mock(spec=AccessDatabase)
        self.db_tareas = Mock(spec=AccessDatabase)
        self.manager = ExpedientesManager(self.db_exped, self.db_tareas, logger=Mock())

    def _patch_all_empty(self):
        patchers = []
        method_names = [
            "get_expedientes_tsol_sin_cod_s4h",
            "get_expedientes_a_punto_finalizar",
            "get_hitos_a_punto_finalizar",
            "get_expedientes_estado_desconocido",
            "get_expedientes_adjudicados_sin_contrato",
            "get_expedientes_fase_oferta_mucho_tiempo",
        ]
        for name in method_names:
            p = patch.object(self.manager, name, return_value=[])
            patchers.append(p)
            p.start()
        return patchers

    def test_generate_report_empty(self):
        patchers = self._patch_all_empty()
        try:
            html = self.manager.generate_expedientes_report_html()
            self.assertEqual(html, "")
        finally:
            for p in patchers:
                p.stop()

    def test_generate_report_with_some_sections(self):
        with patch.object(
            self.manager, "get_expedientes_tsol_sin_cod_s4h", return_value=[{"A": 1}]
        ), patch.object(
            self.manager, "get_expedientes_a_punto_finalizar", return_value=[]
        ), patch.object(
            self.manager, "get_hitos_a_punto_finalizar", return_value=[{"B": 2}]
        ), patch.object(
            self.manager, "get_expedientes_estado_desconocido", return_value=[]
        ), patch.object(
            self.manager, "get_expedientes_adjudicados_sin_contrato", return_value=[]
        ), patch.object(
            self.manager, "get_expedientes_fase_oferta_mucho_tiempo", return_value=[]
        ):
            html = self.manager.generate_expedientes_report_html()
            self.assertIn("INFORME DE AVISOS DE EXPEDIENTES", html)
            self.assertIn("Expedientes TSOL adjudicados sin código S4H", html)
            self.assertIn("Hitos a punto de finalizar", html)
            self.assertNotIn("Expedientes adjudicados sin contrato", html)
            self.assertTrue(html.endswith("</html>") or "</body>" in html)


if __name__ == "__main__":
    unittest.main()
