#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
SRC_ROOT = Path(__file__).parent.parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.common.database import AccessDatabase
from src.common.config import config

def main():
    parser = argparse.ArgumentParser(description='Verificar estado de correos enviados')
    parser.add_argument('--application', default='Riesgos', help='Aplicación a filtrar')
    parser.add_argument('--limit', type=int, default=5, help='Número de correos a mostrar')
    
    args = parser.parse_args()
    
    conn_str = config.get_db_correos_connection_string()
    db = AccessDatabase(conn_str)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        query = (
            f"SELECT TOP {args.limit} IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio "
            "FROM TbCorreosEnviados "
            f"WHERE Aplicacion = '{args.application}' ORDER BY IDCorreo DESC"
        )
        cursor.execute(query)
        columns = [c[0] for c in cursor.description]
        result = [dict(zip(columns, r)) for r in cursor.fetchall()]
        if result:
            print(f"\n=== Últimos {args.limit} correos de {args.application} ===")
            for row in result:
                print(f"ID: {row['IDCorreo']}")
                print(f"  Asunto: {row['Asunto']}")
                print(f"  Destinatarios: {row['Destinatarios']}")
                print(f"  Fecha: {row['FechaEnvio']}")
                print("-" * 50)
        else:
            print(f"No se encontraron correos para {args.application}")

if __name__ == "__main__":
    main()