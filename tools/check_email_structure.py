#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.database_adapter import AccessAdapter
from common.config import config

# Verificar la estructura de la tabla y los correos pendientes
with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
    # Ver correos pendientes con todos los campos
    query = "SELECT * FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
    result = db.execute_query(query)
    
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
    result2 = db.execute_query(query2)
    
    if result2:
        print("Último correo en la base de datos:")
        for key, value in result2[0].items():
            print(f"  {key}: {value}")
    else:
        print("No hay correos en la base de datos")