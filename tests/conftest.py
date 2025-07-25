"""
Configuración global para pytest.
"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

@pytest.fixture(scope="session")
def test_db():
    """Fixture para base de datos de pruebas."""
    db_path = "tests/data/test_database.db"
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Crear conexión
    conn = sqlite3.connect(db_path)
    
    # Crear tabla si no existe
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TbCorreosEnviados (
            IDCorreo INTEGER PRIMARY KEY AUTOINCREMENT,
            URLAdjunto TEXT,
            Aplicacion TEXT,
            Originador TEXT,
            Destinatarios TEXT,
            Asunto TEXT,
            Cuerpo TEXT,
            FechaEnvio DATETIME,
            Observaciones TEXT,
            NDPD TEXT,
            NPEDIDO TEXT,
            NFACTURA TEXT,
            FechaGrabacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            CuerpoHTML TEXT,
            IDEdicion INTEGER
        )
    """)
    conn.commit()
    
    yield conn
    
    conn.close()

@pytest.fixture
def clean_db(test_db):
    """Fixture para limpiar la base de datos antes de cada test."""
    cursor = test_db.cursor()
    cursor.execute("DELETE FROM TbCorreosEnviados")
    test_db.commit()
    yield test_db

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
