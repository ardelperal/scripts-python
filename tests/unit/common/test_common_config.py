"""Tests para el módulo común - configuración
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

from common.config import Config

# Añadir src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestConfig:
    """Tests para la clase Config"""

    @patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "local",
            "DB_PASSWORD": "test_pass",
            "LOCAL_DB_BRASS": "test_brass.accdb",
            "LOCAL_DB_TAREAS": "test_tareas.accdb",
            "DEFAULT_RECIPIENT": "test@example.com",
        },
    )
    def test_config_local_environment(self):
        """Test configuración para entorno local"""
        config = Config()

        assert config.environment == "local"
        assert config.db_password == "test_pass"
        assert config.default_recipient == "test@example.com"

        # Verificar que las rutas son relativas al proyecto
        assert "test_brass.accdb" in str(config.db_brass_path)
        assert "test_tareas.accdb" in str(config.db_tareas_path)

    @patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "oficina",
            "DB_PASSWORD": "office_pass",
            "OFFICE_DB_BRASS": r"\\server\brass.accdb",
            "OFFICE_DB_TAREAS": r"\\server\tareas.accdb",
        },
    )
    def test_config_office_environment(self):
        """Test configuración para entorno oficina"""
        config = Config()

        assert config.environment == "oficina"
        assert config.db_password == "office_pass"

        # Verificar que las rutas son absolutas del servidor
        assert str(config.db_brass_path).rstrip("\\") == r"\\server\brass.accdb"
        assert str(config.db_tareas_path).rstrip("\\") == r"\\server\tareas.accdb"

    def test_connection_strings(self):
        """Test generación de cadenas de conexión"""
        config = Config()

        brass_conn = config.get_db_brass_connection_string()
        tareas_conn = config.get_db_tareas_connection_string()

        assert "Driver={Microsoft Access Driver" in brass_conn
        assert f"PWD={config.db_password}" in brass_conn
        assert "Driver={Microsoft Access Driver" in tareas_conn
        assert f"PWD={config.db_password}" in tareas_conn
