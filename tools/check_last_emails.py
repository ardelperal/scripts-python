#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.common.database_adapter import AccessAdapter
from src.common.config import config

def main():
    with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
        query = """
        SELECT TOP 5 IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio 
        FROM TbCorreosEnviados 
        ORDER BY IDCorreo DESC
        """
        result = db.execute_query(query)
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