"""Tests unitarios para AccessDatabase.

Sustituye los antiguos tests del shim `AccessAdapter` ahora eliminado.
"""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.common.db.database import AccessDatabase


@pytest.fixture
def tmp_db_path(tmp_path) -> Path:
    db_file = tmp_path / "dummy.accdb"
    db_file.touch()
    return db_file


def test_connection_string_from_path(tmp_db_path):
    db = AccessDatabase(tmp_db_path)
    assert "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" in db.connection_string
    assert str(tmp_db_path) in db.connection_string


def test_execute_query_success(tmp_db_path):
    with patch("src.common.db.database.pyodbc.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("Id",), ("Nombre",)]
        mock_cursor.fetchall.return_value = [(1, "Alpha"), (2, "Beta")]

        db = AccessDatabase(tmp_db_path)
        rows = db.execute_query("SELECT Id, Nombre FROM Tabla")

        assert rows == [
            {"Id": 1, "Nombre": "Alpha"},
            {"Id": 2, "Nombre": "Beta"},
        ]
        mock_cursor.execute.assert_called_once_with("SELECT Id, Nombre FROM Tabla")


def test_execute_non_query_success(tmp_db_path):
    with patch("src.common.db.database.pyodbc.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 3

        db = AccessDatabase(tmp_db_path)
        affected = db.execute_non_query("DELETE FROM Tabla WHERE Id < 10")

        assert affected == 3
        assert mock_conn.commit.called


def test_context_manager_calls_connect_and_disconnect(tmp_db_path):
    with patch("src.common.db.database.pyodbc.connect") as mock_connect:
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        db = AccessDatabase(tmp_db_path)
        assert db._connection is None
        with db.get_connection() as conn:
            assert conn is mock_conn
            assert db._connection is mock_conn
        assert db._connection is None
        mock_conn.close.assert_called_once()


def test_get_max_id_calls_execute_query(tmp_db_path):
    with patch("src.common.db.database.pyodbc.connect") as mock_connect:
        mock_connect.return_value = Mock()
        db = AccessDatabase(tmp_db_path)
        with patch.object(db, "execute_query", return_value=[{"MaxID": 42}]) as m_exec:
            max_id = db.get_max_id("MiTabla", "Id")
            m_exec.assert_called_once()
            assert max_id == 42


def test_insert_record_success(tmp_db_path):
    with patch("src.common.db.database.pyodbc.connect") as mock_connect:
        mock_connect.return_value = Mock()
        db = AccessDatabase(tmp_db_path)
        with patch.object(db, "execute_non_query", return_value=1) as m_non_query:
            ok = db.insert_record("MiTabla", {"Campo1": "Valor", "Campo2": 5})
            assert ok is True
            assert m_non_query.called


def test_update_record_success(tmp_db_path):
    with patch("src.common.db.database.pyodbc.connect") as mock_connect:
        mock_connect.return_value = Mock()
        db = AccessDatabase(tmp_db_path)
        with patch.object(db, "execute_non_query", return_value=2) as m_non_query:
            ok = db.update_record("MiTabla", {"Campo1": "X"}, "Id = ?", where_params=[7])
            assert ok is True
            m_non_query.assert_called_once()


def test_update_record_failure(tmp_db_path):
    with patch("src.common.db.database.pyodbc.connect") as mock_connect:
        mock_connect.return_value = Mock()
        db = AccessDatabase(tmp_db_path)
        with patch.object(db, "execute_non_query", side_effect=Exception("boom")):
            ok = db.update_record("MiTabla", {"Campo1": "X"}, "Id = 1")
            assert ok is False
