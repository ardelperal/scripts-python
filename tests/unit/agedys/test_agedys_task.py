import logging
from unittest.mock import Mock

import pytest


@pytest.fixture
def logger():
    return logging.getLogger("test")


def build_task(monkeypatch, logger, manager_mock):
    import src.agedys.agedys_task as task_mod

    monkeypatch.setattr(task_mod, "AccessDatabase", lambda *a, **k: Mock())
    monkeypatch.setattr(task_mod, "AgedysManager", lambda *a, **k: manager_mock)
    ers = Mock()
    ers.get_quality_emails.return_value = ["q@acme"]
    ers.get_economy_emails.return_value = ["e@acme"]
    ers.get_admin_emails.return_value = ["admin@acme"]
    monkeypatch.setattr(task_mod, "EmailRecipientsService", lambda *a, **k: ers)
    reg = Mock(return_value=True)
    monkeypatch.setattr(task_mod, "register_standard_report", reg)
    t = task_mod.AgedysTask()
    t.logger = logger

    class Cfg:
        app_id_agedys = 3

    t.config = Cfg()
    return t, reg, ers


def test_execute_specific_logic_no_data(monkeypatch, logger):
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = []
    manager.generate_quality_report_html.return_value = ""
    manager.generate_economy_report_html.return_value = ""
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ok = task.execute_specific_logic()
    assert ok is True
    reg.assert_not_called()


def test_execute_specific_logic_technical_reports(monkeypatch, logger):
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = [
        {"UserId": 1, "UserName": "U1", "UserEmail": "u1@acme"},
        {"UserId": 2, "UserName": "U2", "UserEmail": "u2@acme"},
    ]
    manager.generate_technical_user_report_html.side_effect = ["H1", "H2"]
    manager.generate_quality_report_html.return_value = ""
    manager.generate_economy_report_html.return_value = ""
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ok = task.execute_specific_logic()
    assert ok is True
    assert reg.call_count == 2
    recipients = sorted(c.kwargs["recipients"] for c in reg.call_args_list)
    assert recipients == ["u1@acme", "u2@acme"]


def test_execute_specific_logic_quality_report(monkeypatch, logger):
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = []
    manager.generate_quality_report_html.return_value = "<html>Q</html>"
    manager.generate_economy_report_html.return_value = ""
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ok = task.execute_specific_logic()
    assert ok is True
    reg.assert_called_once()
    assert "Calidad" in reg.call_args.kwargs["subject"]


def test_execute_specific_logic_economy_report(monkeypatch, logger):
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = []
    manager.generate_quality_report_html.return_value = ""
    manager.generate_economy_report_html.return_value = "<html>E</html>"
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ok = task.execute_specific_logic()
    assert ok is True
    reg.assert_called_once()
    assert "Economía" in reg.call_args.kwargs["subject"]


def test_execute_specific_logic_error(monkeypatch, logger):
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.side_effect = Exception("boom")
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ok = task.execute_specific_logic()
    assert ok is False
    reg.assert_not_called()


def test_execute_specific_logic_mixed_reports(monkeypatch, logger):
    """Cubre escenario completo: usuarios técnicos + informes calidad y economía.

    Verifica:
      - Número total de registros (2 técnicos + 1 calidad + 1 economía = 4)
      - Subjects incluyen etiquetas esperadas
      - Destinatarios técnicos individuales y grupales procesados
    """
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = [
        {"UserId": 10, "UserName": "TechA", "UserEmail": "a@acme"},
        {"UserId": 11, "UserName": "TechB", "UserEmail": "b@acme"},
    ]
    manager.generate_technical_user_report_html.side_effect = ["TA", "TB"]
    manager.generate_quality_report_html.return_value = "<html>Q</html>"
    manager.generate_economy_report_html.return_value = "<html>E</html>"
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ok = task.execute_specific_logic()
    assert ok is True
    assert reg.call_count == 4, f"Esperaba 4 registros y hubo {reg.call_count}"
    subjects = [c.kwargs["subject"] for c in reg.call_args_list]
    # 2 técnicos con nombres en subject
    assert any("TechA" in s for s in subjects)
    assert any("TechB" in s for s in subjects)
    # Calidad y Economía
    assert any("Calidad" in s for s in subjects)
    assert any("Economía" in s for s in subjects)
    # Destinatarios: técnicos individuales más listas grupales
    recipients_list = [c.kwargs["recipients"] for c in reg.call_args_list]
    assert "a@acme" in recipients_list
    assert "b@acme" in recipients_list
    # calidad y economía usan concatenación potencial, aquí solo un email cada uno
    assert any("q@acme" in r for r in recipients_list)
    assert any("e@acme" in r for r in recipients_list)


def test_execute_specific_logic_economy_fallback_admin(monkeypatch, logger):
    """Cubre la rama donde economía no tiene destinatarios y se usa admin como fallback."""
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = []
    manager.generate_technical_user_report_html.return_value = ""
    manager.generate_quality_report_html.return_value = ""
    manager.generate_economy_report_html.return_value = "<html>E</html>"
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ers.get_economy_emails.return_value = []  # fuerza fallback
    ers.get_admin_emails.return_value = ["admin@acme"]
    ok = task.execute_specific_logic()
    assert ok is True
    reg.assert_called_once()
    assert "admin@acme" == reg.call_args.kwargs["recipients"]


def test_execute_specific_logic_no_db_connection(monkeypatch, logger):
    """Cubre rama early-return cuando no hay conexión a BD AGEDYS."""
    manager = Mock()
    # Construir task y luego simular pérdida de conexión
    task, reg, ers = build_task(monkeypatch, logger, manager)
    task.db_agedys = None  # fuerza rama
    ok = task.execute_specific_logic()
    assert ok is True
    reg.assert_not_called()


def test_execute_specific_logic_quality_no_recipients(monkeypatch, logger):
    """Calidad con HTML pero sin destinatarios (branch 'Sin destinatarios calidad; se omite envío')."""
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = []
    manager.generate_technical_user_report_html.return_value = ""
    manager.generate_quality_report_html.return_value = "<html>Q</html>"
    manager.generate_economy_report_html.return_value = ""
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ers.get_quality_emails.return_value = []  # fuerza ausencia
    ok = task.execute_specific_logic()
    assert ok is True
    # No se registró porque no había destinatarios
    reg.assert_not_called()


def test_execute_specific_logic_economy_no_recipients_after_fallback(
    monkeypatch, logger
):
    """Economía con HTML pero sin destinatarios incluso tras fallback admin."""
    manager = Mock()
    manager.get_usuarios_con_tareas_pendientes.return_value = []
    manager.generate_technical_user_report_html.return_value = ""
    manager.generate_quality_report_html.return_value = ""
    manager.generate_economy_report_html.return_value = "<html>E</html>"
    task, reg, ers = build_task(monkeypatch, logger, manager)
    ers.get_economy_emails.return_value = []
    ers.get_admin_emails.return_value = []  # fallback vacío
    ok = task.execute_specific_logic()
    assert ok is True
    # No se registró informe economía
    reg.assert_not_called()
