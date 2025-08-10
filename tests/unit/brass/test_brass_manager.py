"""Tests unitarios para BrassManager refactorizado"""
import pytest
from unittest.mock import MagicMock, patch
from brass.brass_manager import BrassManager


@pytest.fixture
def mock_dbs():
    db_brass = MagicMock()
    db_tareas = MagicMock()
    return db_brass, db_tareas


@pytest.fixture
def manager(mock_dbs):
    db_brass, db_tareas = mock_dbs
    return BrassManager(db_brass, db_tareas)


def test_get_equipment_out_of_calibration_returns_rows(manager, mock_dbs):
    db_brass, _ = mock_dbs
    sample = [
        {'IDEquipoMedida': 1, 'NOMBRE': 'Equipo1', 'NS': 'NS1', 'PN': 'PN1', 'MARCA': 'Marca', 'MODELO': 'M1'},
        {'IDEquipoMedida': 2, 'NOMBRE': 'Equipo2', 'NS': 'NS2', 'PN': 'PN2', 'MARCA': 'Marca', 'MODELO': 'M2'}
    ]
    db_brass.execute_query.return_value = sample
    rows = manager.get_equipment_out_of_calibration()
    assert rows == sample
    assert db_brass.execute_query.called


def test_get_equipment_out_of_calibration_exception(manager, mock_dbs):
    db_brass, _ = mock_dbs
    db_brass.execute_query.side_effect = Exception("fail")
    rows = manager.get_equipment_out_of_calibration()
    assert rows == []


def test_generate_brass_report_html_empty(manager):
    with patch.object(manager, 'get_equipment_out_of_calibration', return_value=[]):
        html = manager.generate_brass_report_html()
        assert html == ""


def test_generate_brass_report_html_with_data(manager):
    sample = [
        {'IDEquipoMedida': 1, 'NOMBRE': 'Equipo1', 'NS': 'NS1', 'PN': 'PN1', 'MARCA': 'Marca', 'MODELO': 'M1'}
    ]
    with patch.object(manager, 'get_equipment_out_of_calibration', return_value=sample):
        html = manager.generate_brass_report_html()
    assert 'INFORME DE AVISOS DE EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN' in html
    assert 'Equipo1' in html
    assert '<table' in html


def test_backward_compat_generate_html_report_with_list(manager):
    sample = [
        {'IDEquipoMedida': 1, 'NOMBRE': 'Equipo1', 'NS': 'NS1', 'PN': 'PN1', 'MARCA': 'Marca', 'MODELO': 'M1'}
    ]
    html = manager.generate_html_report(sample)
    assert 'Equipo1' in html


def test_backward_compat_generate_html_report_empty(manager):
    assert manager.generate_html_report([]) == ""