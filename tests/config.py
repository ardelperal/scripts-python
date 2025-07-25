# Configuración para tests
import os
from pathlib import Path

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "data"
TEST_DB_PATH = TEST_DATA_DIR / "test_database.db"

# Configuración de email para tests
SMTP_CONFIG = {
    "host": "localhost",
    "port": 1025,
    "use_tls": False,
    "username": None,
    "password": None
}

# Configuración de base de datos para tests
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

# Configuración de cobertura
COVERAGE_THRESHOLD = 80
