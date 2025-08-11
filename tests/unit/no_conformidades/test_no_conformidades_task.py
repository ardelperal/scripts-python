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

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_execute_specific_logic_success(self, mock_mgr_cls):
        mock_mgr = MagicMock()
        mock_mgr._generar_correo_calidad.return_value = None
        mock_mgr._generar_correos_tecnicos.return_value = None
        mock_mgr_cls.return_value = mock_mgr
        # Forzar decisiones verdaderas
        with patch.object(self.task, "debe_ejecutar_tarea_calidad", return_value=True), patch.object(
            self.task, "debe_ejecutar_tarea_tecnica", return_value=True
        ):
            result = self.task.execute_specific_logic()
        self.assertTrue(result)
        mock_mgr._generar_correo_calidad.assert_called_once()
        mock_mgr._generar_correos_tecnicos.assert_called_once()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_execute_specific_logic_no_subtasks(self, mock_mgr_cls):
        mock_mgr_cls.return_value = MagicMock()
        with patch.object(self.task, "debe_ejecutar_tarea_calidad", return_value=False), patch.object(
            self.task, "debe_ejecutar_tarea_tecnica", return_value=False
        ):
            result = self.task.execute_specific_logic()
        self.assertTrue(result)

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
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
