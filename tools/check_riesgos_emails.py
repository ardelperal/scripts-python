#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.common.database_adapter import AccessAdapter
from src.common.config import config

def main():
    with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
        # Verificar todos los correos de Riesgos
        query_riesgos = """
        SELECT IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio, LEN(Cuerpo) as CuerpoLength
        FROM TbCorreosEnviados 
        WHERE Aplicacion = 'Riesgos'
        ORDER BY IDCorreo DESC
        """
        result_riesgos = db.execute_query(query_riesgos)
        
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
        query_last = """
        SELECT TOP 1 IDCorreo, Aplicacion, Asunto, Destinatarios, FechaEnvio
        FROM TbCorreosEnviados 
        ORDER BY IDCorreo DESC
        """
        result_last = db.execute_query(query_last)
        
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