"""Tests para BrassTask con inyección y modos force/dry-run."""
import pytest
from unittest.mock import MagicMock, patch
from src.brass.brass_task import BrassTask


class DummyRecipientsService:
    def __init__(self, db_tareas, config, logger):
        self.db_tareas = db_tareas
    def get_admin_emails_string(self):
        return "admin@test.com"


@pytest.fixture
def task():
    # Parchear base_task internals que crean conexiones para aislar pruebas
    with patch("src.common.base_task.AccessDatabase"):
        t = BrassTask(recipients_service_class=DummyRecipientsService)
        # Simular db_tareas con execute_query
        t.db_tareas = MagicMock()
        t.db_tareas.execute_query.return_value = []
        return t


def test_execute_specific_logic_empty(task, monkeypatch):
    manager_mock = MagicMock()
    manager_mock.generate_brass_report_html.return_value = ""
    with patch("src.brass.brass_task.BrassManager", return_value=manager_mock):
        assert task.execute_specific_logic() is True
        manager_mock.generate_brass_report_html.assert_called_once()
        # No se registra correo si html vacío
        task.db_tareas.execute_query.assert_not_called()


def test_execute_specific_logic_with_data(task):
    manager_mock = MagicMock()
    manager_mock.generate_brass_report_html.return_value = "<html>ok</html>"
    with patch("src.brass.brass_task.BrassManager", return_value=manager_mock), \
         patch("src.brass.brass_task.register_standard_report", return_value=True) as reg:
        ok = task.execute_specific_logic()
        assert ok is True
        reg.assert_called_once()


def test_execute_specific_logic_exception(task):
    with patch("src.brass.brass_task.BrassManager", side_effect=Exception("boom")):
        assert task.execute_specific_logic() is False
