"""Tests unitarios para NoConformidadesManager.registrar_aviso_ar

Escenarios:
 - Inserción de nuevo aviso (no existe registro previo para IDAR)
 - Actualización de aviso existente (registro ya presente)
"""
from unittest.mock import MagicMock, patch

from no_conformidades.no_conformidades_manager import (
    AVISO_15_DIAS,
    NoConformidadesManager,
)


def _build_mock_db_insert(maximo=5):
    """Crea un mock de DB para el flujo de inserción.

    Orden de llamadas a execute_query en registrar_aviso_ar:
      1) SELECT IDAR ... -> [] (no existe)
      2) SELECT Max ... -> [{'Maximo': maximo}]
    """
    mock_db = MagicMock()
    mock_db.execute_query.side_effect = [[], [{"Maximo": maximo}]]
    mock_db.execute_non_query.return_value = 1
    return mock_db


def _build_mock_db_update():
    """Crea un mock de DB para el flujo de actualización.

    Orden de llamadas a execute_query:
      1) SELECT IDAR ... -> [{'IDAR': <idar>}]
    """
    mock_db = MagicMock()
    mock_db.execute_query.side_effect = [[{"IDAR": 42}]]
    mock_db.execute_non_query.return_value = 1
    return mock_db


def test_registrar_aviso_ar_inserta_nuevo():
    manager = NoConformidadesManager()
    mock_db = _build_mock_db_insert(maximo=7)
    with patch.object(manager, "_get_nc_connection", return_value=mock_db):
        manager.registrar_aviso_ar(id_ar=123, id_correo=555, tipo_aviso=AVISO_15_DIAS)

    # Verifica orden de queries
    assert mock_db.execute_query.call_count == 2
    # Primera llamada: comprobación existencia
    exists_query, exists_params = mock_db.execute_query.call_args_list[0][0]
    assert "SELECT IDAR FROM TbNCARAvisos" in exists_query
    assert exists_params == (123,)
    # Segunda llamada: max id
    second_call_args = mock_db.execute_query.call_args_list[1][0]
    max_query = second_call_args[0]
    assert "SELECT Max(TbNCARAvisos.ID)" in max_query
    # Insert ejecutado
    mock_db.execute_non_query.assert_called_once()
    insert_query, insert_params = mock_db.execute_non_query.call_args[0]
    assert "INSERT INTO TbNCARAvisos" in insert_query
    # next_id = 7 + 1 = 8
    assert insert_params[0] == 8  # ID
    assert insert_params[1] == 123  # IDAR
    assert insert_params[2] == 555  # IDCorreo15


def test_registrar_aviso_ar_actualiza_existente():
    manager = NoConformidadesManager()
    mock_db = _build_mock_db_update()
    with patch.object(manager, "_get_nc_connection", return_value=mock_db):
        manager.registrar_aviso_ar(id_ar=321, id_correo=777, tipo_aviso=AVISO_15_DIAS)

    # Sólo una consulta (exists) y luego un update
    assert mock_db.execute_query.call_count == 1
    exists_query, exists_params = mock_db.execute_query.call_args_list[0][0]
    assert "SELECT IDAR FROM TbNCARAvisos" in exists_query
    assert exists_params == (321,)
    mock_db.execute_non_query.assert_called_once()
    update_query, update_params = mock_db.execute_non_query.call_args[0]
    assert update_query.startswith("UPDATE TbNCARAvisos SET IDCorreo15")
    assert update_params == (777, 321)
