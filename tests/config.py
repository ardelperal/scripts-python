# Configuración para tests
import os
from pathlib import Path

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "data"

# Configuración de email para tests
SMTP_CONFIG = {
    "host": "localhost",
    "port": 1025,
    "use_tls": False,
    "username": None,
    "password": None
}

# Configuración de cobertura
COVERAGE_THRESHOLD = 80
