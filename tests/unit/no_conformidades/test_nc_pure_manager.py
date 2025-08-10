import unittest
from unittest.mock import MagicMock
from no_conformidades.nc_pure_manager import NoConformidadesManagerPure


class TestNoConformidadesManagerPure(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.manager = NoConformidadesManagerPure(self.db)

    def test_report_empty(self):
        self.db.execute_query.return_value = []
        html = self.manager.generate_nc_report_html()
        self.assertEqual(html, "")

    def test_report_with_sections(self):
        # Sequence of calls: ars_proximas, ncs_pendientes, ncs_sin_acciones, ars_para_replanificar
        self.db.execute_query.side_effect = [
            [{'CodigoNoConformidad': 'NC1', 'Nemotecnico': 'NEMO', 'DESCRIPCION': 'Desc', 'RESPONSABLECALIDAD': 'RC', 'FECHAAPERTURA': '2025-01-01', 'FPREVCIERRE': '2025-01-10', 'DiasParaCierre': 5}],
            [],
            [],
            []
        ]
        html = self.manager.generate_nc_report_html()
        self.assertIn('INFORME NO CONFORMIDADES', html)
        self.assertIn('NC1', html)
        self.assertIn('<table', html)

    def test_report_only_ncs_sin_acciones(self):
        # First two sections empty, third has data, fourth empty
        self.db.execute_query.side_effect = [
            [],  # ars_proximas
            [],  # ncs_pendientes
            [{'CodigoNoConformidad': 'NC2', 'Nemotecnico': 'NM2', 'DESCRIPCION': 'Desc2', 'RESPONSABLECALIDAD': 'RC2', 'FECHAAPERTURA': '2025-02-01', 'FPREVCIERRE': '2025-02-10'}],
            []   # ars_para_replanificar
        ]
        html = self.manager.generate_nc_report_html()
        self.assertIn('NCs Sin Acciones', html)
        self.assertIn('NC2', html)
        self.assertIn('<table', html)

    def test_report_only_ars_para_replanificar(self):
        # First three sections empty, fourth has data
        self.db.execute_query.side_effect = [
            [],  # ars_proximas
            [],  # ncs_pendientes
            [],  # ncs_sin_acciones
            [{'CodigoNoConformidad': 'NC3', 'Nemotecnico': 'NM3', 'Accion': 'AccionX', 'Tarea': 'TareaX', 'Tecnico': 'Tec', 'RESPONSABLECALIDAD': 'RC3', 'FechaFinPrevista': '2025-03-05', 'Dias': 3}]
        ]
        html = self.manager.generate_nc_report_html()
        self.assertIn('ARs Para Replanificar', html)
        self.assertIn('NC3', html)
        self.assertIn('<table', html)


if __name__ == '__main__':
    unittest.main()
