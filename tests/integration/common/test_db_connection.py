#!/usr/bin/env python3
"""
Script temporal para probar la conexión a la base de datos de correos
"""

from common.config import config
from common.database import AccessDatabase
import os
import pytest

def test_correos_db():
    """Verifica que la base de datos de correos es accesible y la tabla principal responde."""
    # Obtener ruta de la base de datos
    db_path = config.get_database_path('correos')
    print(f"DB Path: {db_path}")

    assert os.path.exists(db_path), f"El archivo de base de datos no existe: {db_path}"

    # Probar conexión usando la función específica de correos con contraseña
    connection_string = config.get_db_correos_connection_string(with_password=True)
    print(f"Connection string: {connection_string}")

    try:
        db = AccessDatabase(connection_string)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TbCorreosEnviados")
            count = cursor.fetchone()[0]
            print(f"Registros en TbCorreosEnviados: {count}")
            # Simple sanity check: COUNT debe ser >= 0
            assert count >= 0
    except Exception as e:
        pytest.fail(f"Fallo al conectar o consultar la BD de correos: {e}")

if __name__ == "__main__":
    test_correos_db()