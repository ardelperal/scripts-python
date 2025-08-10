#!/usr/bin/env python3
import sys
from pathlib import Path
SRC_ROOT = Path(__file__).parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.common.database import AccessDatabase
from src.common.config import config

def main():
    conn_str = config.get_db_correos_connection_string()
    db = AccessDatabase(conn_str)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        query = (
            "SELECT TOP 5 IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio "
            "FROM TbCorreosEnviados ORDER BY IDCorreo DESC"
        )
        cursor.execute(query)
        columns = [c[0] for c in cursor.description]
        result = [dict(zip(columns, r)) for r in cursor.fetchall()]
        if result:
            print("=== Últimos 5 correos registrados ===")
            for row in result:
                print(f"ID: {row['IDCorreo']}")
                print(f"  App: {row['Aplicacion']}")
                print(f"  Asunto: {row['Asunto']}")
                print(f"  Destinatarios: {row['Destinatarios']}")
                print(f"  Fecha: {row['FechaEnvio']}")
                print("-" * 50)
        else:
            print("No se encontraron correos")

if __name__ == "__main__":
    main()