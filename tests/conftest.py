"""
Configuración global para pytest.
"""
import pytest
import tempfile
import os
from pathlib import Path

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
