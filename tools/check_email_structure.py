#!/usr/bin/env python3
import sys
from pathlib import Path
SRC_ROOT = Path(__file__).parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.common.database import AccessDatabase
from src.common.config import config

# Verificar la estructura de la tabla y los correos pendientes
conn_str = config.get_db_correos_connection_string()
db = AccessDatabase(conn_str)
with db.get_connection() as conn:
    cursor = conn.cursor()
    query = "SELECT * FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
    cursor.execute(query)
    columns = [c[0] for c in cursor.description]
    result = [dict(zip(columns, r)) for r in cursor.fetchall()]
    
    if result:
        print("Correos pendientes encontrados:")
        for i, row in enumerate(result):
            print(f"Correo {i+1}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
            print()
    else:
        print("No hay correos pendientes")
        
    # Ver el último correo insertado
    query2 = "SELECT TOP 1 * FROM TbCorreosEnviados ORDER BY IDCorreo DESC"
    cursor.execute(query2)
    columns2 = [c[0] for c in cursor.description]
    rows2 = cursor.fetchall()
    result2 = [dict(zip(columns2, r)) for r in rows2]
    
    if result2:
        print("Último correo en la base de datos:")
        for key, value in result2[0].items():
            print(f"  {key}: {value}")
    else:
        print("No hay correos en la base de datos")