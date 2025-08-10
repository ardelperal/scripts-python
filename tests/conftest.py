"""
Configuración global para pytest.
"""
import pytest
import sys
from pathlib import Path

# Ensure 'src' is importable without needing explicit 'src.' prefixes
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

@pytest.fixture
def smtp_config():
    """Configuración SMTP para tests."""
    return {
        "host": "localhost",
        "port": 1025,
        "use_tls": False,
        "username": None,
        "password": None
    }
