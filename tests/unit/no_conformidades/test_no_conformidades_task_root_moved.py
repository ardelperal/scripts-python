import unittest
from unittest.mock import MagicMock, patch

from no_conformidades.no_conformidades_task import NoConformidadesTask


class TestNoConformidadesTaskExecuteSpecificLogic(unittest.TestCase):
    def setUp(self):
        self.task = NoConformidadesTask()
        # Evitar acceso real a BD durante tests
        self.task.db_nc = MagicMock()
        self.task.db_tareas = MagicMock()

    @patch.object(NoConformidadesTask, "ejecutar_logica_tecnica")
    @patch.object(NoConformidadesTask, "ejecutar_logica_calidad")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_tecnica")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_calidad")
    def test_solo_calidad(
        self,
        mock_debe_calidad,
        mock_debe_tecnica,
        mock_logica_calidad,
        mock_logica_tecnica,
    ):
        mock_debe_calidad.return_value = True
        mock_debe_tecnica.return_value = False
        mock_logica_calidad.return_value = True

        result = self.task.execute_specific_logic()

        self.assertTrue(result)
        mock_logica_calidad.assert_called_once()
        mock_logica_tecnica.assert_not_called()

    @patch.object(NoConformidadesTask, "ejecutar_logica_tecnica")
    @patch.object(NoConformidadesTask, "ejecutar_logica_calidad")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_tecnica")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_calidad")
    def test_solo_tecnica(
        self,
        mock_debe_calidad,
        mock_debe_tecnica,
        mock_logica_calidad,
        mock_logica_tecnica,
    ):
        mock_debe_calidad.return_value = False
        mock_debe_tecnica.return_value = True
        mock_logica_tecnica.return_value = True

        result = self.task.execute_specific_logic()

        self.assertTrue(result)
        mock_logica_calidad.assert_not_called()
        mock_logica_tecnica.assert_called_once()

    @patch.object(NoConformidadesTask, "ejecutar_logica_tecnica")
    @patch.object(NoConformidadesTask, "ejecutar_logica_calidad")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_tecnica")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_calidad")
    def test_ambas(
        self,
        mock_debe_calidad,
        mock_debe_tecnica,
        mock_logica_calidad,
        mock_logica_tecnica,
    ):
        mock_debe_calidad.return_value = True
        mock_debe_tecnica.return_value = True
        mock_logica_calidad.return_value = True
        mock_logica_tecnica.return_value = True

        result = self.task.execute_specific_logic()

        self.assertTrue(result)
        mock_logica_calidad.assert_called_once()
        mock_logica_tecnica.assert_called_once()

    @patch.object(NoConformidadesTask, "ejecutar_logica_tecnica")
    @patch.object(NoConformidadesTask, "ejecutar_logica_calidad")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_tecnica")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_calidad")
    def test_ninguna(
        self,
        mock_debe_calidad,
        mock_debe_tecnica,
        mock_logica_calidad,
        mock_logica_tecnica,
    ):
        mock_debe_calidad.return_value = False
        mock_debe_tecnica.return_value = False

        result = self.task.execute_specific_logic()

        self.assertTrue(result)  # Nada que ejecutar se considera éxito
        mock_logica_calidad.assert_not_called()
        mock_logica_tecnica.assert_not_called()

    @patch.object(NoConformidadesTask, "ejecutar_logica_tecnica")
    @patch.object(NoConformidadesTask, "ejecutar_logica_calidad")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_tecnica")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_calidad")
    def test_excepcion_en_calidad(
        self,
        mock_debe_calidad,
        mock_debe_tecnica,
        mock_logica_calidad,
        mock_logica_tecnica,
    ):
        mock_debe_calidad.return_value = True
        mock_debe_tecnica.return_value = False
        mock_logica_calidad.side_effect = Exception("Fallo interno")

        result = self.task.execute_specific_logic()

        self.assertFalse(result)
        mock_logica_calidad.assert_called_once()
        mock_logica_tecnica.assert_not_called()

    @patch.object(NoConformidadesTask, "ejecutar_logica_tecnica")
    @patch.object(NoConformidadesTask, "ejecutar_logica_calidad")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_tecnica")
    @patch.object(NoConformidadesTask, "debe_ejecutar_tarea_calidad")
    def test_execute_logic_with_technical_exception(
        self,
        mock_debe_calidad,
        mock_debe_tecnica,
        mock_logica_calidad,
        mock_logica_tecnica,
    ):
        """Ambas subtareas deben ejecutarse; la parte técnica lanza excepción.

        Expected: devuelve False; se llama lógica de calidad y técnica y se registra el error.
        """
        mock_debe_calidad.return_value = True
        mock_debe_tecnica.return_value = True
        mock_logica_calidad.return_value = True
        mock_logica_tecnica.side_effect = Exception("Fallo técnico simulado")
        with patch.object(self.task.logger, "error") as mock_logger_error:
            result = self.task.execute_specific_logic()

        self.assertFalse(result)
        mock_logica_calidad.assert_called_once()
        mock_logica_tecnica.assert_called_once()
        mock_logger_error.assert_called()  # Verifica que se registró el error


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
