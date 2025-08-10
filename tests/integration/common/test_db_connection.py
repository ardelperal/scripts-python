#!/usr/bin/env python3
"""
Script temporal para probar la conexión a la base de datos de correos
"""

from common.config import config
from common.database import AccessDatabase
import os

def test_correos_db():
    try:
        # Obtener ruta de la base de datos
        db_path = config.get_database_path('correos')
        print(f"DB Path: {db_path}")
        
        # Verificar que el archivo existe
        if not os.path.exists(db_path):
            print(f"ERROR: El archivo de base de datos no existe: {db_path}")
            return False
            
        # Probar conexión usando la función específica de correos con contraseña
        connection_string = config.get_db_correos_connection_string(with_password=True)
        print(f"Connection string: {connection_string}")
        
        db = AccessDatabase(connection_string)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Probar una consulta simple
            cursor.execute("SELECT COUNT(*) FROM TbCorreosEnviados")
            count = cursor.fetchone()[0]
            print(f"Registros en TbCorreosEnviados: {count}")
            
        print("Connection test successful!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_correos_db()