"""Cobertura adicional RiesgosManager para caminos no cubiertos."""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from riesgos.riesgos_manager import RiesgosManager


@pytest.fixture
def manager():
    cfg = MagicMock()
    logger = MagicMock()
    m = RiesgosManager(cfg, logger)
    m.db = MagicMock()
    m.db_tareas = MagicMock()
    return m


def test_generate_table_html_unknown_type(manager):
    html = manager.generate_table_html([], "tipo_inexistente")
    assert html == ""  # warning pathway


def test_get_summary_stats_initial(manager):
    stats = manager.get_summary_stats()
    assert stats["error_count"] == 0 and stats["warning_count"] == 0
    assert stats["has_errors"] is False and stats["has_warnings"] is False


def test_execute_quality_task_no_users_fallback(manager, monkeypatch):
    # Forzar base report OK y cero quality users retornando admin fallback
    manager._generate_quality_report_html = lambda: "<html>base</html>"
    monkeypatch.setattr(
        "src.riesgos.riesgos_manager.get_quality_users", lambda *a, **k: []
    )
    monkeypatch.setattr(
        "src.riesgos.riesgos_manager.get_admin_emails_string",
        lambda *a, **k: "admin@test",
    )
    monkeypatch.setattr(
        "src.common.utils.register_email_in_database", lambda *a, **k: True
    )
    monkeypatch.setattr(
        "src.common.utils.register_task_completion", lambda *a, **k: True
    )
    assert manager.execute_quality_task() is True


def test_execute_monthly_quality_task_admin_fallback(manager, monkeypatch):
    monkeypatch.setattr(
        "src.riesgos.riesgos_manager.get_quality_users", lambda *a, **k: []
    )
    monkeypatch.setattr(
        "src.riesgos.riesgos_manager.get_admin_emails_string",
        lambda *a, **k: "admin@test",
    )
    monkeypatch.setattr(
        "src.common.utils.register_email_in_database", lambda *a, **k: True
    )
    monkeypatch.setattr(
        "src.common.utils.register_task_completion", lambda *a, **k: True
    )
    manager._generate_monthly_quality_report_html = lambda: "<html>mensual</html>"
    assert manager.execute_monthly_quality_task() is True


def test_generate_generic_table_days_formatting(manager):
    data = [
        {"Nemotecnico": "PR1", "Dias": -1, "Fecha": datetime.now()},
        {"Nemotecnico": "PR2", "Dias": 3, "Fecha": datetime.now()},
        {"Nemotecnico": "PR3", "Dias": 10, "Fecha": datetime.now()},
    ]
    columns = [
        {"header": "Proyecto", "field": "Nemotecnico"},
        {"header": "Faltan", "field": "Dias", "format": "days"},
    ]
    html = manager._generate_generic_table(data, "Titulo", columns)
    assert 'style="color: red' in html
    assert 'style="color: orange' in html
    assert "PR3" in html  # normal branch


def test_generate_generic_table_css_days(manager):
    data = [
        {"Nemotecnico": "PR1", "Dias": -2},
        {"Nemotecnico": "PR2", "Dias": 5},
        {"Nemotecnico": "PR3", "Dias": 20},
    ]
    columns = [
        {"header": "Proyecto", "field": "Nemotecnico"},
        {"header": "Faltan", "field": "Dias", "format": "css_days"},
    ]
    html = manager._generate_generic_table(data, "Titulo", columns)
    assert "negativo" in html and "critico" in html and "normal" in html


def test_get_css_class_for_days(manager):
    assert manager._get_css_class_for_days(-1) == "negativo"
    assert manager._get_css_class_for_days(0) == "negativo"
    assert manager._get_css_class_for_days(5) == "critico"
    assert manager._get_css_class_for_days(10) == "normal"


def test_normalize_date_variants(manager):
    now = datetime.now()
    assert manager._normalize_date(now) == now
    assert manager._normalize_date(now.date()) == datetime.combine(
        now.date(), datetime.min.time()
    )
    assert manager._normalize_date(now.strftime("%Y-%m-%d")) == datetime.strptime(
        now.strftime("%Y-%m-%d"), "%Y-%m-%d"
    )
    # Formato inválido -> None
    manager.logger.warning.reset_mock() if hasattr(manager.logger, "warning") else None
    assert manager._normalize_date("32/13/9999") is None


def test_calculate_days_difference_errors(manager, monkeypatch):
    # target None -> 0
    assert manager._calculate_days_difference(None) == 0
    # referencia pasada (string parse)
    ref = datetime.now().strftime("%Y-%m-%d")
    assert isinstance(manager._calculate_days_difference(datetime.now(), ref), int)


def test_generate_personalized_quality_report_html(manager):
    # Incluir nombres dentro del HTML para poder localizar el orden
    sections = {
        "UserA": "<div>UserA contenido</div>",
        "UserB": "<div>UserB contenido</div>",
    }
    html = manager._generate_personalized_quality_report_html("UserB", sections)
    # usuario primario debe aparecer primero seguido de hr
    first_index = html.find("UserB")
    second_index = html.find("UserA")
    assert 0 <= first_index < second_index


def test_generate_quality_member_section_html_empty(manager, monkeypatch):
    # Forzar datos vacíos
    monkeypatch.setattr(
        manager, "_get_editions_ready_for_publication_data", lambda *a, **k: []
    )
    monkeypatch.setattr(
        manager, "_get_editions_about_to_expire_data", lambda *a, **k: []
    )
    monkeypatch.setattr(manager, "_get_expired_editions_data", lambda *a, **k: [])
    monkeypatch.setattr(manager, "_get_risks_to_reclassify_data", lambda *a, **k: [])
    monkeypatch.setattr(
        manager, "_get_accepted_risks_to_approve_data", lambda *a, **k: []
    )
    monkeypatch.setattr(
        manager, "_get_retired_risks_to_approve_data", lambda *a, **k: []
    )
    monkeypatch.setattr(
        manager, "_get_materialized_risks_to_decide_data", lambda *a, **k: []
    )
    html = manager._generate_quality_member_section_html("CalidadX")
    assert "No hay tareas pendientes" in html


def test_generate_monthly_quality_report_html_sections(manager, monkeypatch):
    # Mock cada sección para asegurar inclusión
    monkeypatch.setattr(
        manager,
        "_get_accepted_risks_pending_approval_data",
        lambda: [{"Nemotecnico": "P1"}],
    )
    monkeypatch.setattr(
        manager,
        "_get_retired_risks_pending_approval_data",
        lambda: [{"Nemotecnico": "P2"}],
    )
    monkeypatch.setattr(
        manager,
        "_get_materialized_risks_pending_decision_data",
        lambda: [{"Nemotecnico": "P3"}],
    )
    monkeypatch.setattr(
        manager,
        "_get_all_editions_ready_for_publication_data",
        lambda: [{"Nemotecnico": "P4"}],
    )
    monkeypatch.setattr(
        manager, "_get_active_editions_data", lambda: [{"Proyecto": "P5"}]
    )
    monkeypatch.setattr(
        manager, "_get_closed_editions_last_month_data", lambda: [{"IDEdicion": 1}]
    )
    html = manager._generate_monthly_quality_report_html()
    # Debe contener partes de varios datasets
    for token in ["P1", "P2", "P3", "P4"]:
        assert token in html
