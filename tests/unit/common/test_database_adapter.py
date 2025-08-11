"""Tests unitarios para AccessAdapter
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.common.database_adapter import AccessAdapter


class TestAccessAdapter:
    """Tests para la clase AccessAdapter"""

    @pytest.fixture
    def mock_db_path(self, tmp_path):
        """Fixture que crea un archivo de base de datos temporal"""
        db_file = tmp_path / "test.accdb"
        db_file.touch()  # Crear archivo vacío
        return db_file

    @pytest.fixture
    def mock_pyodbc_connection(self):
        """Fixture que mockea la conexión pyodbc"""
        with patch("src.common.database_adapter.pyodbc.connect") as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            yield mock_connect, mock_conn

    def test_init_success(self, mock_db_path, mock_pyodbc_connection):
        """Test inicialización exitosa de AccessAdapter"""
        mock_connect, mock_conn = mock_pyodbc_connection

        adapter = AccessAdapter(mock_db_path)

        assert adapter.db_path == mock_db_path
        assert adapter.password is None
        assert adapter.connection == mock_conn
        mock_connect.assert_called_once()

    def test_init_with_password(self, mock_db_path, mock_pyodbc_connection):
        """Test inicialización con contraseña"""
        mock_connect, mock_conn = mock_pyodbc_connection
        password = "test_password"

        adapter = AccessAdapter(mock_db_path, password)

        assert adapter.password == password
        # Verificar que la cadena de conexión incluye la contraseña
        call_args = mock_connect.call_args[0][0]
        assert f"PWD={password};" in call_args

    def test_init_file_not_found(self):
        """Test error cuando el archivo no existe"""
        non_existent_path = Path("non_existent.accdb")

        with pytest.raises(
            FileNotFoundError, match="Base de datos Access no encontrada"
        ):
            AccessAdapter(non_existent_path)

    @patch("src.common.database_adapter.PYODBC_AVAILABLE", False)
    def test_init_pyodbc_not_available(self, mock_db_path):
        """Test error cuando pyodbc no está disponible"""
        with pytest.raises(ImportError, match="pyodbc no está disponible"):
            AccessAdapter(mock_db_path)

    def test_connect_error(self, mock_db_path):
        """Test error en conexión"""
        with patch("src.common.database_adapter.pyodbc.connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                AccessAdapter(mock_db_path)

    def test_execute_query_success(self, mock_db_path, mock_pyodbc_connection):
        """Test ejecución exitosa de consulta SELECT"""
        mock_connect, mock_conn = mock_pyodbc_connection

        # Configurar mock cursor
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("id",), ("name",), ("value",)]
        mock_cursor.fetchall.return_value = [(1, "Test1", 100), (2, "Test2", 200)]

        adapter = AccessAdapter(mock_db_path)
        result = adapter.execute_query("SELECT * FROM test_table")

        expected = [
            {"id": 1, "name": "Test1", "value": 100},
            {"id": 2, "name": "Test2", "value": 200},
        ]
        assert result == expected
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table")

    def test_execute_query_with_params(self, mock_db_path, mock_pyodbc_connection):
        """Test ejecución de consulta con parámetros"""
        mock_connect, mock_conn = mock_pyodbc_connection

        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("count",), ("name",)]
        mock_cursor.fetchall.return_value = [(5,)]

        adapter = AccessAdapter(mock_db_path)
        params = (1,)
        result = adapter.execute_query("SELECT * FROM test_table WHERE id = ?", params)

        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM test_table WHERE id = ?", params
        )
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_execute_query_error(self, mock_db_path, mock_pyodbc_connection):
        """Test error en ejecución de consulta"""
        mock_connect, mock_conn = mock_pyodbc_connection

        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Query failed")

        adapter = AccessAdapter(mock_db_path)

        with pytest.raises(Exception, match="Query failed"):
            adapter.execute_query("SELECT * FROM test_table")

    def test_execute_non_query_success(self, mock_db_path, mock_pyodbc_connection):
        """Test ejecución exitosa de consulta de modificación"""
        mock_connect, mock_conn = mock_pyodbc_connection

        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        adapter = AccessAdapter(mock_db_path)
        result = adapter.execute_non_query(
            "INSERT INTO test_table (name) VALUES ('Test')"
        )

        assert result == 1
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_execute_non_query_with_params(self, mock_db_path, mock_pyodbc_connection):
        """Test ejecución de consulta de modificación con parámetros"""
        mock_connect, mock_conn = mock_pyodbc_connection

        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        adapter = AccessAdapter(mock_db_path)
        params = ("Test",)
        result = adapter.execute_non_query(
            "INSERT INTO test_table (name) VALUES (?)", params
        )

        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO test_table (name) VALUES (?)", params
        )
        assert result == 1

    def test_execute_non_query_error(self, mock_db_path, mock_pyodbc_connection):
        """Test error en ejecución de consulta de modificación"""
        mock_connect, mock_conn = mock_pyodbc_connection

        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Insert failed")

        adapter = AccessAdapter(mock_db_path)

        with pytest.raises(Exception, match="Insert failed"):
            adapter.execute_non_query("INSERT INTO test_table (name) VALUES ('Test')")

    def test_get_tables_success(self, mock_db_path, mock_pyodbc_connection):
        """Test obtención exitosa de lista de tablas"""
        mock_connect, mock_conn = mock_pyodbc_connection

        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock de objetos tabla
        mock_table1 = Mock()
        mock_table1.table_name = "Table1"
        mock_table2 = Mock()
        mock_table2.table_name = "Table2"

        mock_cursor.tables.return_value = [mock_table1, mock_table2]

        adapter = AccessAdapter(mock_db_path)
        result = adapter.get_tables()

        assert result == ["Table1", "Table2"]
        mock_cursor.tables.assert_called_once_with(tableType="TABLE")

    def test_get_tables_error(self, mock_db_path, mock_pyodbc_connection):
        """Test error al obtener lista de tablas"""
        mock_connect, mock_conn = mock_pyodbc_connection

        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.tables.side_effect = Exception("Tables query failed")

        adapter = AccessAdapter(mock_db_path)
        result = adapter.get_tables()

        assert result == []

    def test_close(self, mock_db_path, mock_pyodbc_connection):
        """Test cierre de conexión"""
        mock_connect, mock_conn = mock_pyodbc_connection

        adapter = AccessAdapter(mock_db_path)
        adapter.close()

        mock_conn.close.assert_called_once()

    def test_close_no_connection(self, mock_db_path):
        """Test cierre cuando no hay conexión"""
        with patch("src.common.database_adapter.pyodbc.connect") as mock_connect:
            mock_connect.return_value = None

            adapter = AccessAdapter(mock_db_path)
            adapter.connection = None
            adapter.close()  # No debería fallar

    def test_context_manager(self, mock_db_path, mock_pyodbc_connection):
        """Test uso como context manager"""
        mock_connect, mock_conn = mock_pyodbc_connection

        with AccessAdapter(mock_db_path) as adapter:
            assert adapter.connection == mock_conn

        mock_conn.close.assert_called_once()

    def test_context_manager_with_exception(self, mock_db_path, mock_pyodbc_connection):
        """Test context manager con excepción"""
        mock_connect, mock_conn = mock_pyodbc_connection

        try:
            with AccessAdapter(mock_db_path):
                raise ValueError("Test exception")
        except ValueError:
            # Se espera que se capture la excepción y se cierre la conexión
            pass

        mock_conn.close.assert_called_once()


import importlib


class TestAccessAdapterImportError:
    """Tests para casos de error de importación"""

    def test_import_error_on_module_load(self):
        """Test que se maneja correctamente la falta de pyodbc al cargar el módulo"""
        # Forzamos la simulación de que pyodbc no está instalado
        sys.modules["pyodbc"] = None

        # Recargamos el módulo para que el try/except de importación se re-evalue
        import src.common.database_adapter as db_adapter

        importlib.reload(db_adapter)

        # Verificamos que la bandera se ha puesto a False
        assert db_adapter.PYODBC_AVAILABLE is False

        # Restauramos el módulo para no afectar a otros tests
        del sys.modules["pyodbc"]
        importlib.reload(db_adapter)
        assert db_adapter.PYODBC_AVAILABLE is True
