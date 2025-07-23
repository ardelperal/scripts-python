"""
Test completo para verificar la migración de EnviarCorreoNoEnviado.vbs a Python
Equivalente al testing que hicimos con BRASS
"""
import sys
import logging
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import pyodbc

# Configurar path para importaciones
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from src.scripts.enviar_correo_no_enviado import EmailSender
from src.common.config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

import sqlite3
import pyodbc
import os

DB_SQLITE = r'dbs-sqlite/correos_datos.sqlite'
DB_ACCESS = r'C:/Users/adm1/Desktop/Proyectos/scripts-python/dbs-locales/correos_datos.accdb'
DB_PASSWORD = os.getenv('DB_PASSWORD', 'dpddpd')

def get_ids(sql, dbtype='sqlite'):
    if dbtype == 'sqlite':
        conn = sqlite3.connect(DB_SQLITE)
    else:
        conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_ACCESS};PWD={DB_PASSWORD};"
        conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(sql)
    ids = set(row[0] for row in cursor.fetchall())
    conn.close()
    return ids

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
