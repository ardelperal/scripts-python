import pytest
from unittest.mock import patch, MagicMock

from correos.correos_task import CorreosTask


def test_correos_task_debe_ejecutarse_true():
    task = CorreosTask(manager_cls=MagicMock())
    assert task.debe_ejecutarse() is True


def test_correos_task_execute_specific_logic_calls_manager():
    mock_manager_instance = MagicMock()
    mock_manager_instance.enviar_correos_no_enviados.return_value = 3

    mock_manager_cls = MagicMock(return_value=mock_manager_instance)

    task = CorreosTask(manager_cls=mock_manager_cls)

    # Patch config path existence check to succeed
    with patch('src.correos.correos_task.config') as mock_config, \
         patch('pathlib.Path.exists', return_value=True):
        mock_config.db_correos_path = 'dummy.accdb'
        ok = task.execute_specific_logic()

    assert ok is True
    mock_manager_cls.assert_called_once()
    mock_manager_instance.enviar_correos_no_enviados.assert_called_once()
