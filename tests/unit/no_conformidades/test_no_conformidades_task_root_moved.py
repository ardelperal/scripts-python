import unittest
from unittest.mock import MagicMock, patch

from no_conformidades.no_conformidades_task import NoConformidadesTask


class TestNoConformidadesTaskExecuteSpecificLogic(unittest.TestCase):
    def setUp(self):
        self.task = NoConformidadesTask()
        # Evitar acceso real a BD durante tests
        self.task.db_nc = MagicMock()
        self.task.db_tareas = MagicMock()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_solo_calidad(self, mock_manager_cls):
        self.task.debe_ejecutar_tarea_calidad = MagicMock(return_value=True)
        self.task.debe_ejecutar_tarea_tecnica = MagicMock(return_value=False)
        instancia = mock_manager_cls.return_value
        instancia._generar_correo_calidad.return_value = True
        resultado = self.task.execute_specific_logic()
        self.assertTrue(resultado)
        instancia._generar_correo_calidad.assert_called_once()
        instancia._generar_correos_tecnicos.assert_not_called()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_solo_tecnica(self, mock_manager_cls):
        self.task.debe_ejecutar_tarea_calidad = MagicMock(return_value=False)
        self.task.debe_ejecutar_tarea_tecnica = MagicMock(return_value=True)
        instancia = mock_manager_cls.return_value
        instancia._generar_correos_tecnicos.return_value = True
        resultado = self.task.execute_specific_logic()
        self.assertTrue(resultado)
        instancia._generar_correo_calidad.assert_not_called()
        instancia._generar_correos_tecnicos.assert_called_once()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_ambas(self, mock_manager_cls):
        self.task.debe_ejecutar_tarea_calidad = MagicMock(return_value=True)
        self.task.debe_ejecutar_tarea_tecnica = MagicMock(return_value=True)
        instancia = mock_manager_cls.return_value
        instancia._generar_correo_calidad.return_value = True
        instancia._generar_correos_tecnicos.return_value = True
        resultado = self.task.execute_specific_logic()
        self.assertTrue(resultado)
        instancia._generar_correo_calidad.assert_called_once()
        instancia._generar_correos_tecnicos.assert_called_once()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_ninguna(self, mock_manager_cls):
        self.task.debe_ejecutar_tarea_calidad = MagicMock(return_value=False)
        self.task.debe_ejecutar_tarea_tecnica = MagicMock(return_value=False)
        instancia = mock_manager_cls.return_value
        resultado = self.task.execute_specific_logic()
        self.assertTrue(resultado)  # Nada que ejecutar = éxito
        instancia._generar_correo_calidad.assert_not_called()
        instancia._generar_correos_tecnicos.assert_not_called()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_excepcion_en_calidad(self, mock_manager_cls):
        self.task.debe_ejecutar_tarea_calidad = MagicMock(return_value=True)
        self.task.debe_ejecutar_tarea_tecnica = MagicMock(return_value=False)
        instancia = mock_manager_cls.return_value
        instancia._generar_correo_calidad.side_effect = Exception("Fallo interno")
        with patch.object(self.task.logger, "error") as mock_log_error:
            resultado = self.task.execute_specific_logic()
        self.assertFalse(resultado)
        instancia._generar_correo_calidad.assert_called_once()
        instancia._generar_correos_tecnicos.assert_not_called()
        mock_log_error.assert_called()

    @patch("no_conformidades.no_conformidades_task.NoConformidadesManager")
    def test_execute_logic_with_technical_exception(self, mock_manager_cls):
        self.task.debe_ejecutar_tarea_calidad = MagicMock(return_value=True)
        self.task.debe_ejecutar_tarea_tecnica = MagicMock(return_value=True)
        instancia = mock_manager_cls.return_value
        instancia._generar_correo_calidad.return_value = True
        instancia._generar_correos_tecnicos.side_effect = Exception("Fallo técnico simulado")
        with patch.object(self.task.logger, "error") as mock_log_error:
            resultado = self.task.execute_specific_logic()
        self.assertFalse(resultado)
        instancia._generar_correo_calidad.assert_called_once()
        instancia._generar_correos_tecnicos.assert_called_once()
        mock_log_error.assert_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
