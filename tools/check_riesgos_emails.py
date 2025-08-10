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
        # Verificar todos los correos de Riesgos
        query_riesgos = (
            "SELECT IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio, LEN(Cuerpo) as CuerpoLength "
            "FROM TbCorreosEnviados WHERE Aplicacion = 'Riesgos' ORDER BY IDCorreo DESC"
        )
        cursor.execute(query_riesgos)
        columns = [c[0] for c in cursor.description]
        result_riesgos = [dict(zip(columns, r)) for r in cursor.fetchall()]
        
        if result_riesgos:
            print("=== Correos de Riesgos ===")
            for row in result_riesgos:
                print(f"ID: {row['IDCorreo']}")
                print(f"  App: {row['Aplicacion']}")
                print(f"  Asunto: {row['Asunto']}")
                print(f"  Destinatarios: {row['Destinatarios']}")
                print(f"  Fecha: {row['FechaEnvio']}")
                print(f"  Tamaño cuerpo: {row['CuerpoLength']} caracteres")
                print("-" * 50)
        else:
            print("No se encontraron correos de Riesgos")
        
        # Verificar el último correo registrado independientemente de la aplicación
        query_last = (
            "SELECT TOP 1 IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio "
            "FROM TbCorreosEnviados ORDER BY IDCorreo DESC"
        )
        cursor.execute(query_last)
        columns2 = [c[0] for c in cursor.description]
        rows2 = cursor.fetchall()
        result_last = [dict(zip(columns2, r)) for r in rows2]
        
        if result_last:
            print("\n=== Último correo registrado ===")
            row = result_last[0]
            print(f"ID: {row['IDCorreo']}")
            print(f"  App: {row['Aplicacion']}")
            print(f"  Asunto: {row['Asunto']}")
            print(f"  Destinatarios: {row['Destinatarios']}")
            print(f"  Fecha: {row['FechaEnvio']}")

if __name__ == "__main__":
    main()