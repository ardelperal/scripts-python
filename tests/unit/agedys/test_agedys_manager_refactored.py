"""Refactored unit tests for new AgedysManager structure.
Covers: user aggregation queries, per-user technical report generation, grouped quality/economy reports,
HTML empty report behavior, and section execution logging paths.
"""
from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from src.agedys.agedys_manager import AgedysManager

@pytest.fixture
def logger():
    return logging.getLogger("test")

@pytest.fixture
def db():
    return Mock()

@pytest.fixture
def manager(db, logger):
    return AgedysManager(db, logger)

@pytest.mark.parametrize("subquery_rows", [
    # Each element corresponds to rows returned per subquery set inside get_usuarios_facturas_pendientes_visado_tecnico
    [[{"UsuarioRed": "u1", "CorreoUsuario": "u1@acme"}], [], [], []],
    [[], [{"UsuarioRed": "u1", "CorreoUsuario": "u1@acme"}], [], []],
])
def test_get_usuarios_facturas_pendientes_visado_tecnico_dedup(manager, db, subquery_rows):
    # Flatten side_effect sequence
    db.execute_query.side_effect = subquery_rows
    users = manager.get_usuarios_facturas_pendientes_visado_tecnico()
    assert users == [{"UsuarioRed": "u1", "CorreoUsuario": "u1@acme"}]


def test_get_usuarios_facturas_pendientes_visado_tecnico_handles_exceptions(manager, db):
    db.execute_query.side_effect = [Exception("boom"), [], [], []]
    users = manager.get_usuarios_facturas_pendientes_visado_tecnico()
    assert users == []  # No valid rows


def test_get_facturas_pendientes_por_tecnico_merge(manager, db):
    # 4 subqueries -> ensure merge by composed key
    rows = [
        [{"NFactura": "F1", "NDOCUMENTO": "D1"}],
        [{"NFactura": "F1", "NDOCUMENTO": "D1"}],
        [{"NFactura": "F2", "NDOCUMENTO": "D2"}],
        [{"NFactura": "F2", "NDOCUMENTO": "D2"}],
    ]
    db.execute_query.side_effect = rows
    result = manager.get_facturas_pendientes_por_tecnico(123, "Tec")
    assert len(result) == 2
    keys = {(r['NFactura'], r['NDOCUMENTO']) for r in result}
    assert keys == {('F1', 'D1'), ('F2', 'D2')}


def test_execute_section_success(manager, db):
    db.execute_query.return_value = [{"a": 1}]
    rows = manager._execute_section("SELECT 1", "test")
    assert rows == [{"a": 1}]


def test_execute_section_failure(manager, db, caplog):
    db.execute_query.side_effect = Exception("fail")
    with caplog.at_level(logging.ERROR):
        rows = manager._execute_section("SELECT 1", "test")
    assert rows == []
    assert any("Error sección test" in r.message for r in caplog.records)


def test_generate_technical_user_report_empty(manager, db):
    # All underlying section methods return empty lists -> report should be ''
    manager.get_dpds_sin_so_por_tecnico = Mock(return_value=[])
    manager.get_dpds_con_so_sin_ro_por_tecnico = Mock(return_value=[])
    manager.get_dpds_sin_visado_calidad_por_tecnico = Mock(return_value=[])
    manager.get_dpds_rechazados_calidad_por_tecnico = Mock(return_value=[])
    manager.get_facturas_pendientes_por_tecnico = Mock(return_value=[])
    html = manager.generate_technical_user_report_html(1, "Tec", "t@acme")
    assert html == ""  # returns empty


def test_generate_technical_user_report_with_data(manager, db):
    sample = [{"CODPROYECTOS": "DPD1", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-01", "EXPEDIENTE": "E1", "DESCRIPCION": "Desc"}]
    manager.get_dpds_sin_so_por_tecnico = Mock(return_value=sample)
    manager.get_dpds_con_so_sin_ro_por_tecnico = Mock(return_value=[])
    manager.get_dpds_sin_visado_calidad_por_tecnico = Mock(return_value=[])
    manager.get_dpds_rechazados_calidad_por_tecnico = Mock(return_value=[])
    manager.get_facturas_pendientes_por_tecnico = Mock(return_value=[])
    html = manager.generate_technical_user_report_html(1, "Tec", "t@acme")
    assert "DPDs sin SO" in html
    assert "DPD1" in html


def test_generate_quality_report_html(manager):
    manager.get_dpds_sin_visado_calidad_agrupado = Mock(return_value=[{"CODPROYECTOS": "DPD1", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-01", "CodExp": "E1", "DESCRIPCION": "Desc", "ResponsableCalidad": "RC"}])
    html = manager.generate_quality_report_html()
    assert "DPDs sin visado calidad" in html
    assert "DPD1" in html


def test_generate_quality_report_html_empty(manager):
    manager.get_dpds_sin_visado_calidad_agrupado = Mock(return_value=[])
    html = manager.generate_quality_report_html()
    assert html == ""


def test_generate_economy_report_html(manager):
    manager.get_dpds_con_fin_agenda_tecnica_agrupado = Mock(return_value=[{"CODPROYECTOS": "D1", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-01", "EXPEDIENTE": "E", "DESCRIPCION": "Desc"}])
    manager.get_dpds_sin_pedido_agrupado = Mock(return_value=[])
    manager.get_facturas_rechazadas_agrupado = Mock(return_value=[])
    manager.get_facturas_visadas_pendientes_op_agrupado = Mock(return_value=[])
    html = manager.generate_economy_report_html()
    assert "DPDs fin agenda técnica pendientes recepción" in html
    assert "D1" in html


def test_generate_economy_report_html_empty(manager):
    manager.get_dpds_con_fin_agenda_tecnica_agrupado = Mock(return_value=[])
    manager.get_dpds_sin_pedido_agrupado = Mock(return_value=[])
    manager.get_facturas_rechazadas_agrupado = Mock(return_value=[])
    manager.get_facturas_visadas_pendientes_op_agrupado = Mock(return_value=[])
    html = manager.generate_economy_report_html()
    assert html == ""
