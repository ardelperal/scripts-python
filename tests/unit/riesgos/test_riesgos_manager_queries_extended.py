"""Cobertura extendida para RiesgosManager (_get_risks_data y run_daily_tasks)."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from riesgos.riesgos_manager import RiesgosManager


@pytest.fixture
def manager():
    cfg = MagicMock()
    logger = MagicMock()
    m = RiesgosManager(cfg, logger)
    m.db = MagicMock()
    m.db_tareas = MagicMock()
    return m


def test_get_risks_data_variants(manager, monkeypatch):
    # Simular respuesta genérica para todas las consultas
    sample_row = {
        'Nemotecnico': 'PR1',
        'Edicion': '1.0',
        'FechaMaxProximaPublicacion': datetime.now() + timedelta(days=10),
        'FechaPreparadaParaPublicar': datetime.now(),
        'UsuarioCalidad': 'CalidadX',
        'CodigoRiesgo': 'R-1',
        'Descripcion': 'Desc',
        'CausaRaiz': 'Causa',
        'FechaRetirado': datetime.now(),
        'FechaRechazoRetiroPorCalidad': datetime.now(),
        'FechaRechazoAceptacionPorCalidad': datetime.now(),
        'DisparadorDelPlan': 'Evt',
        'Accion': 'Act',
        'FechaInicio': datetime.now(),
        'FechaFinPrevista': datetime.now(),
    }
    monkeypatch.setattr(manager, '_execute_query_with_error_logging', lambda *a, **k: [dict(sample_row)])
    query_types = [
        'editions_need_publication',
        'editions_with_rejected_proposals',
        'accepted_risks_unmotivated',
        'accepted_risks_rejected',
        'retired_risks_unmotivated',
        'retired_risks_rejected',
        'mitigation_actions_reschedule',
        'mitigation_actions_pending',
        'contingency_actions_reschedule'
    ]
    for qt in query_types:
        data = manager._get_risks_data(qt, user_id='user1')
        assert data and isinstance(data, list)


def test_generate_table_html_valid_type(manager):
    data = [{
        'Nemotecnico': 'PR1', 'Edicion': '1.0',
        'FechaMaxProximaPublicacion': datetime.now(),
        'FechaPreparadaParaPublicar': datetime.now(),
        'UsuarioCalidad': 'QC', 'Dias': 5
    }]
    html = manager.generate_table_html(data, 'editions_need_publication')
    assert 'Total: 1 elementos' in html and 'PR1' in html


def test_run_daily_tasks_none(manager, monkeypatch):
    monkeypatch.setattr(manager, 'should_execute_technical_task', lambda: False)
    monkeypatch.setattr(manager, 'should_execute_quality_task', lambda: False)
    monkeypatch.setattr(manager, 'should_execute_monthly_quality_task', lambda: False)
    res = manager.run_daily_tasks()
    assert res == {'technical': False, 'quality': False, 'monthly': False}


def test_run_daily_tasks_all(manager, monkeypatch):
    monkeypatch.setattr(manager, 'should_execute_technical_task', lambda: True)
    monkeypatch.setattr(manager, 'should_execute_quality_task', lambda: True)
    monkeypatch.setattr(manager, 'should_execute_monthly_quality_task', lambda: True)
    monkeypatch.setattr(manager, 'execute_technical_task', lambda: True)
    monkeypatch.setattr(manager, 'execute_quality_task', lambda: True)
    monkeypatch.setattr(manager, 'execute_monthly_quality_task', lambda: True)
    res = manager.run_daily_tasks()
    assert res == {'technical': True, 'quality': True, 'monthly': True}
