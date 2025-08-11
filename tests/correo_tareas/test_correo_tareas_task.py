import pytest
from unittest.mock import MagicMock

from correo_tareas.correo_tareas_task import CorreoTareasTask


def test_correo_tareas_task_debe_ejecutarse_true():
    task = CorreoTareasTask(manager_cls=MagicMock())
    assert task.debe_ejecutarse() is True


def test_correo_tareas_task_execute_specific_logic_calls_manager():
    mock_manager_instance = MagicMock()
    # Nuevo flujo usa process_pending_emails que devuelve conteo (>=0)
    mock_manager_instance.process_pending_emails.return_value = 0

    mock_manager_cls = MagicMock(return_value=mock_manager_instance)

    task = CorreoTareasTask(manager_cls=mock_manager_cls)

    ok = task.execute_specific_logic()

    assert ok is True
    mock_manager_cls.assert_called_once()
    mock_manager_instance.process_pending_emails.assert_called_once()
