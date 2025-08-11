"""
Tests para funciones de seguridad en utils
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from common.utils import hide_password_in_connection_string


class TestSecurityUtils:
    """Tests para funciones de seguridad"""

    def test_hide_password_in_connection_string_with_pwd(self):
        """Test para ocultar contraseña con PWD"""
        conn_str = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=test.accdb;PWD=secretpassword;"
        expected = (
            "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=test.accdb;PWD=***;"
        )
        result = hide_password_in_connection_string(conn_str)
        assert result == expected
        assert "secretpassword" not in result

    def test_hide_password_in_connection_string_with_password(self):
        """Test para ocultar contraseña con Password"""
        conn_str = (
            "Driver={SQL Server};Server=localhost;Database=test;Password=mysecret123;"
        )
        expected = "Driver={SQL Server};Server=localhost;Database=test;Password=***;"
        result = hide_password_in_connection_string(conn_str)
        assert result == expected
        assert "mysecret123" not in result

    def test_hide_password_case_insensitive(self):
        """Test para verificar que funciona sin importar mayúsculas/minúsculas"""
        conn_str = "Driver={Test};pwd=secret;Password=another;"
        result = hide_password_in_connection_string(conn_str)
        assert "secret" not in result
        assert "another" not in result
        assert "pwd=***;" in result
        assert "Password=***;" in result

    def test_hide_password_no_password_in_string(self):
        """Test para cadenas sin contraseña"""
        conn_str = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=test.accdb;"
        result = hide_password_in_connection_string(conn_str)
        assert result == conn_str  # Debe permanecer igual

    def test_hide_password_empty_string(self):
        """Test para cadena vacía"""
        result = hide_password_in_connection_string("")
        assert result == ""

    def test_hide_password_multiple_passwords(self):
        """Test para múltiples contraseñas en la misma cadena"""
        conn_str = "PWD=first;Server=test;Password=second;PWD=third;"
        result = hide_password_in_connection_string(conn_str)
        assert "first" not in result
        assert "second" not in result
        assert "third" not in result
        assert result.count("***") == 3
