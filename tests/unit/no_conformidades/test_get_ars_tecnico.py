"""Tests de los métodos get_ars_tecnico_por_vencer y get_ars_tecnico_vencidas.

Objetivos:
- Verificar generación de consulta para rango 8-15 días (IDCorreo15, BETWEEN 8 AND 15).
- Verificar generación de consulta para rango 1-7 días (IDCorreo7, condición > 0 AND <= 7).
- Verificar generación de consulta para vencidas (IDCorreo0, <= 0).
- Verificar manejo de excepción retornando lista vacía.
"""
from unittest.mock import MagicMock, patch

from no_conformidades.no_conformidades_manager import (
    AVISO_7_DIAS,
    AVISO_15_DIAS,
    AVISO_CADUCADAS,
    NoConformidadesManager,
)


def _mock_db(result_list):
    mock_db = MagicMock()
    mock_db.execute_query.return_value = result_list
    return mock_db


def test_get_ars_tecnico_por_vencer_8_15():
    manager = NoConformidadesManager()
    mock_db = _mock_db([{"CodigoNoConformidad": "NC1"}])
    with patch.object(manager, "_get_nc_connection", return_value=mock_db):
        result = manager.get_ars_tecnico_por_vencer("TEC1", 8, 15, AVISO_15_DIAS)
    assert result and result[0]["CodigoNoConformidad"] == "NC1"
    query, params = mock_db.execute_query.call_args[0]
    assert "BETWEEN 8 AND 15" in query
    assert "IDCorreo15" in query
    assert params == ("TEC1",)


def test_get_ars_tecnico_por_vencer_1_7():
    manager = NoConformidadesManager()
    mock_db = _mock_db([])
    with patch.object(manager, "_get_nc_connection", return_value=mock_db):
        result = manager.get_ars_tecnico_por_vencer("TEC2", 1, 7, AVISO_7_DIAS)
    assert result == []
    query, params = mock_db.execute_query.call_args[0]
    assert "DateDiff(" in query
    assert "> 0 AND DateDiff(" in query and "<= 7" in query
    assert "IDCorreo7" in query
    assert params == ("TEC2",)


def test_get_ars_tecnico_vencidas():
    manager = NoConformidadesManager()
    mock_db = _mock_db([{"CodigoNoConformidad": "NCV"}])
    with patch.object(manager, "_get_nc_connection", return_value=mock_db):
        result = manager.get_ars_tecnico_vencidas("TEC3", AVISO_CADUCADAS)
    assert result and result[0]["CodigoNoConformidad"] == "NCV"
    query, params = mock_db.execute_query.call_args[0]
    assert "DateDiff(" in query and "<= 0" in query
    assert "IDCorreo0" in query
    assert params == ("TEC3",)


def test_get_ars_tecnico_exception():
    manager = NoConformidadesManager()
    with patch.object(manager, "_get_nc_connection", side_effect=Exception("DB fail")):
        result = manager.get_ars_tecnico_por_vencer("TEC4", 8, 15, AVISO_15_DIAS)
    assert result == []
