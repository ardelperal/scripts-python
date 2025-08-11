import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from no_conformidades.no_conformidades_task import NoConformidadesTask


class TestNoConformidadesTask(unittest.TestCase):
    def setUp(self):
        self.task = NoConformidadesTask()

    def test_init(self):
        self.assertEqual(self.task.name, "NoConformidades")
        self.assertEqual(self.task.script_filename, "run_no_conformidades.py")
        self.assertEqual(self.task.task_names, ["NCTecnico", "NCCalidad"])
        self.assertEqual(self.task.frequency_days, 1)

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManagerPure")
    @patch("no_conformidades.no_conformidades_task.register_standard_report")
    def test_execute_specific_logic_success(self, mock_register, mock_mgr_cls):
        mock_mgr = MagicMock()
        mock_mgr.generate_nc_report_html.return_value = "<html>x</html>"
        mock_mgr_cls.return_value = mock_mgr
        mock_register.return_value = True
        result = self.task.execute_specific_logic()
        self.assertTrue(result)
        mock_mgr.generate_nc_report_html.assert_called_once()
        mock_register.assert_called_once()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManagerPure")
    def test_execute_specific_logic_empty_report(self, mock_mgr_cls):
        mock_mgr = MagicMock()
        mock_mgr.generate_nc_report_html.return_value = ""
        mock_mgr_cls.return_value = mock_mgr
        result = self.task.execute_specific_logic()
        self.assertTrue(result)

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManagerPure")
    def test_execute_specific_logic_exception(self, mock_mgr_cls):
        mock_mgr_cls.side_effect = Exception("boom")
        result = self.task.execute_specific_logic()
        self.assertFalse(result)

    def test_close_connections(self):
        # Forzar atributo y cerrar
        db_mock = MagicMock()
        self.task.db_nc = db_mock
        self.task.close_connections()
        db_mock.disconnect.assert_called_once()


if __name__ == "__main__":
    unittest.main()
