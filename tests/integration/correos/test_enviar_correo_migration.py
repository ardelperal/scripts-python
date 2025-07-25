"""
Test completo para verificar la migración de EnviarCorreoNoEnviado.vbs a Python
Equivalente al testing que hicimos con BRASS
"""
import sys
import logging
import sqlite3
import os
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Configurar path para importaciones
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuración de bases de datos
DB_SQLITE = 'dbs-sqlite/correos_datos.sqlite'
DB_ACCESS = 'C:/Users/adm1/Desktop/Proyectos/scripts-python/dbs-locales/correos_datos.accdb'
DB_PASSWORD = os.getenv('DB_PASSWORD', 'dpddpd')

def get_ids(sql, dbtype='sqlite'):
    """Obtener IDs de correos según el tipo de base de datos."""
    if dbtype == 'sqlite':
        if not os.path.exists(DB_SQLITE):
            return set()
        conn = sqlite3.connect(DB_SQLITE)
    else:
        try:
            import pyodbc
            conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_ACCESS};PWD={DB_PASSWORD};"
            conn = pyodbc.connect(conn_str)
        except:
            pytest.skip("No se puede conectar a la base de datos Access")
            
    cursor = conn.cursor()
    cursor.execute(sql)
    ids = set(row[0] for row in cursor.fetchall())
    conn.close()
    return ids

@pytest.mark.correos
def test_correos_pendientes_consistency():
    """Verificar que los correos pendientes coinciden entre SQLite y Access."""
    sql = "SELECT IDCorreo FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
    
    ids_sqlite = get_ids(sql, 'sqlite')
    ids_access = get_ids(sql, 'access')
    
    logger.info(f"SQLite correos pendientes: {sorted(ids_sqlite)}")
    logger.info(f"Access correos pendientes: {sorted(ids_access)}")
    
    assert ids_sqlite == ids_access, "Los ID de correos pendientes no coinciden entre SQLite y Access"

@pytest.mark.correos
def test_correos_enviados_consistency():
    """Verificar que los correos enviados coinciden entre SQLite y Access."""
    sql = "SELECT IDCorreo FROM TbCorreosEnviados WHERE FechaEnvio IS NOT NULL"
    
    ids_sqlite = get_ids(sql, 'sqlite')
    ids_access = get_ids(sql, 'access')
    
    logger.info(f"SQLite correos enviados: {sorted(ids_sqlite)}")
    logger.info(f"Access correos enviados: {sorted(ids_access)}")
    
    assert ids_sqlite == ids_access, "Los ID de correos enviados no coinciden entre SQLite y Access"

@pytest.mark.correos
@pytest.mark.integration
def test_database_structure():
    """Verificar que la estructura de la tabla es correcta."""
    if not os.path.exists(DB_SQLITE):
        pytest.skip("Base de datos SQLite no encontrada")
        
    conn = sqlite3.connect(DB_SQLITE)
    cursor = conn.cursor()
    
    # Verificar que la tabla existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TbCorreosEnviados'")
    table_exists = cursor.fetchone() is not None
    
    assert table_exists, "La tabla TbCorreosEnviados no existe"
    
    # Verificar columnas principales
    cursor.execute("PRAGMA table_info(TbCorreosEnviados)")
    columns = [row[1] for row in cursor.fetchall()]
    
    required_columns = ['IDCorreo', 'Destinatarios', 'Asunto', 'Cuerpo', 'FechaEnvio']
    for col in required_columns:
        assert col in columns, f"Columna requerida '{col}' no encontrada"
    
    conn.close()

if __name__ == "__main__":
    # Ejecutar tests manualmente si se ejecuta directamente
    print('--- Verificando correos pendientes ---')
    sql = "SELECT IDCorreo FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
    ids_sqlite = get_ids(sql, 'sqlite')
    ids_access = get_ids(sql, 'access')
    print(f"SQLite: {sorted(ids_sqlite)}")
    print(f"Access: {sorted(ids_access)}")
    if ids_sqlite == ids_access:
        print("[OK] Los ID de correos pendientes coinciden.")
    else:
        print("[ERROR] Los ID de correos pendientes NO coinciden.")

    print('\n--- Verificando correos enviados ---')
    sql = "SELECT IDCorreo FROM TbCorreosEnviados WHERE FechaEnvio IS NOT NULL"
    ids_sqlite = get_ids(sql, 'sqlite')
    ids_access = get_ids(sql, 'access')
    print(f"SQLite: {sorted(ids_sqlite)}")
    print(f"Access: {sorted(ids_access)}")
    if ids_sqlite == ids_access:
        print("[OK] Los ID de correos enviados coinciden.")
    else:
        print("[ERROR] Los ID de correos enviados NO coinciden.")
