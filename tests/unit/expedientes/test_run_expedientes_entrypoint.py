"""Smoke tests del entrypoint scripts/run_expedientes.py.

Casos cubiertos:
 - No ejecución cuando debe_ejecutarse() = False
 - Ejecución exitosa marca completada y exit 0
 - Ejecución con fallo de lógica exit 1
"""
import unittest
from unittest.mock import patch, MagicMock


class TestRunExpedientesEntrypoint(unittest.TestCase):
    def _prepare_task_mock(self, *, debe: bool, logic_ok: bool):
        task = MagicMock()
        task.__enter__.return_value = task
        task.__exit__.return_value = False
        task.debe_ejecutarse.return_value = debe
        task.execute_specific_logic.return_value = logic_ok
        return task

    @patch('scripts.run_expedientes.ExpedientesTask')
    @patch('scripts.run_expedientes.sys.exit')
    def test_main_no_execution(self, mock_exit, mock_task_cls):
        task = self._prepare_task_mock(debe=False, logic_ok=True)
        mock_task_cls.return_value = task
        import scripts.run_expedientes as mod
        mod.main()
        task.debe_ejecutarse.assert_called_once()
        task.execute_specific_logic.assert_not_called()
        task.marcar_como_completada.assert_not_called()
        mock_exit.assert_called_once_with(0)

    @patch('scripts.run_expedientes.ExpedientesTask')
    @patch('scripts.run_expedientes.sys.exit')
    def test_main_execution_success(self, mock_exit, mock_task_cls):
        task = self._prepare_task_mock(debe=True, logic_ok=True)
        mock_task_cls.return_value = task
        import scripts.run_expedientes as mod
        mod.main()
        task.execute_specific_logic.assert_called_once()
        task.marcar_como_completada.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('scripts.run_expedientes.ExpedientesTask')
    @patch('scripts.run_expedientes.sys.exit')
    def test_main_execution_failure(self, mock_exit, mock_task_cls):
        task = self._prepare_task_mock(debe=True, logic_ok=False)
        mock_task_cls.return_value = task
        import scripts.run_expedientes as mod
        mod.main()
        task.execute_specific_logic.assert_called_once()
        task.marcar_como_completada.assert_not_called()
        mock_exit.assert_called_once_with(1)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
