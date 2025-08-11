"""Tests unitarios para la clase AccessDatabase
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from common.db.database import AccessDatabase

# Añadir src al path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestAccessDatabase:
    """Tests para la clase AccessDatabase"""

    @pytest.fixture
    def mock_connection_string(self):
        """Fixture con cadena de conexión de prueba"""
        return (
            "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=test.accdb;PWD=test;"
        )

    @pytest.fixture
    def access_db(self, mock_connection_string):
        """Fixture que crea una instancia AccessDatabase"""
        return AccessDatabase(mock_connection_string)

    def test_init(self, access_db, mock_connection_string):
        """Test inicialización de AccessDatabase"""
        assert access_db.connection_string == mock_connection_string
        assert access_db._connection is None

    @patch("common.db.database.pyodbc.connect")
    def test_connect_success(self, mock_connect, access_db):
        """Test conexión exitosa"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        result = access_db.connect()

        mock_connect.assert_called_once_with(access_db.connection_string)
        assert result == mock_connection
        assert access_db._connection == mock_connection

    @patch("common.db.database.pyodbc.connect")
    def test_connect_failure(self, mock_connect, access_db):
        """Test fallo en conexión"""
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception) as exc_info:
            access_db.connect()

        assert "Connection failed" in str(exc_info.value)

    def test_disconnect(self, access_db):
        """Test desconexión"""
        mock_connection = Mock()
        access_db._connection = mock_connection

        access_db.disconnect()

        mock_connection.close.assert_called_once()
        assert access_db._connection is None

    @patch.object(AccessDatabase, "connect")
    @patch.object(AccessDatabase, "disconnect")
    def test_get_connection_context_manager(
        self, mock_disconnect, mock_connect, access_db
    ):
        """Test context manager de conexión"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        with access_db.get_connection() as conn:
            assert conn == mock_connection

        mock_connect.assert_called_once()
        mock_disconnect.assert_called_once()

    @patch("common.db.database.pyodbc.connect")
    def test_execute_query_success(self, mock_connect, access_db):
        """Test ejecución exitosa de consulta"""
        # Mock de conexión y cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock de descripción de columnas y datos
        mock_cursor.description = [("id", None), ("name", None)]
        mock_cursor.fetchall.return_value = [(1, "Test"), (2, "Test2")]

        result = access_db.execute_query("SELECT * FROM test")

        mock_cursor.execute.assert_called_once_with("SELECT * FROM test")
        expected = [{"id": 1, "name": "Test"}, {"id": 2, "name": "Test2"}]
        assert result == expected

    @patch("common.db.database.pyodbc.connect")
    def test_execute_query_with_params(self, mock_connect, access_db):
        """Test ejecución de consulta con parámetros"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_cursor.description = [("count", None)]
        mock_cursor.fetchall.return_value = [(5,)]

        params = (1, "test")
        result = access_db.execute_query(
            "SELECT COUNT(*) FROM test WHERE id = ? AND name = ?", params
        )

        mock_cursor.execute.assert_called_once_with(
            "SELECT COUNT(*) FROM test WHERE id = ? AND name = ?", params
        )
        assert result == [{"count": 5}]

    @patch("common.db.database.pyodbc.connect")
    def test_execute_non_query_success(self, mock_connect, access_db):
        """Test ejecución exitosa de consulta no-SELECT"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = access_db.execute_non_query("UPDATE test SET name = 'updated'")

        mock_cursor.execute.assert_called_once_with("UPDATE test SET name = 'updated'")
        mock_conn.commit.assert_called_once()
        assert result == 3

    @patch.object(AccessDatabase, "execute_query")
    def test_get_max_id(self, mock_execute_query, access_db):
        """Test obtención de ID máximo"""
        mock_execute_query.return_value = [{"MaxID": 42}]

        result = access_db.get_max_id("TestTable", "ID")

        mock_execute_query.assert_called_once_with(
            "SELECT MAX(ID) as MaxID FROM TestTable"
        )
        assert result == 42

    @patch.object(AccessDatabase, "execute_query")
    def test_get_max_id_no_records(self, mock_execute_query, access_db):
        """Test obtención de ID máximo sin registros"""
        mock_execute_query.return_value = [{"MaxID": None}]

        result = access_db.get_max_id("TestTable", "ID")

        assert result == 0

    @patch.object(AccessDatabase, "execute_non_query")
    def test_insert_record_success(self, mock_execute_non_query, access_db):
        """Test inserción exitosa de registro"""
        mock_execute_non_query.return_value = 1

        data = {"name": "Test", "value": 123}
        result = access_db.insert_record("TestTable", data)

        expected_query = "INSERT INTO TestTable (name, value) VALUES (?, ?)"
        expected_params = ("Test", 123)

        mock_execute_non_query.assert_called_once_with(expected_query, expected_params)
        assert result is True

    @patch.object(AccessDatabase, "execute_non_query")
    def test_update_record_success(self, mock_execute_non_query, access_db):
        """Test actualización exitosa de registro"""
        mock_execute_non_query.return_value = 2

        data = {"name": "Updated", "value": 456}
        where_condition = "id = ?"
        where_params = (1,)

        result = access_db.update_record(
            "TestTable", data, where_condition, where_params
        )

        expected_query = "UPDATE TestTable SET name = ?, value = ? WHERE id = ?"
        expected_params = ("Updated", 456, 1)

        mock_execute_non_query.assert_called_once_with(expected_query, expected_params)
        assert result is True
