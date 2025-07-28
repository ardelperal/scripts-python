#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.database_adapter import AccessAdapter
from common.config import config

# Verificar todos los correos y sus IDs
with AccessAdapter(Path(config.db_correos_path), config.db_password) as db:
    # Ver todos los correos con ID válido
    query = "SELECT IDCorreo, Aplicacion, Asunto FROM TbCorreosEnviados WHERE IDCorreo IS NOT NULL ORDER BY IDCorreo DESC"
    result = db.execute_query(query)
    
    if result:
        print("Correos con ID válido:")
        for row in result:
            print(f"  ID: {row['IDCorreo']}, App: {row['Aplicacion']}, Asunto: {row['Asunto']}")
    else:
        print("No hay correos con ID válido")
        
    # Ver todos los correos con ID NULL
    query2 = "SELECT COUNT(*) as Total FROM TbCorreosEnviados WHERE IDCorreo IS NULL"
    result2 = db.execute_query(query2)
    
    if result2:
        print(f"Correos con ID NULL: {result2[0]['Total']}")
        
    # Intentar obtener el esquema de la tabla
    try:
        tables = db.get_tables()
        print(f"Tablas disponibles: {tables}")
    except Exception as e:
        print(f"Error obteniendo tablas: {e}")
        
    # Intentar una consulta diferente para ver la estructura
    try:
        query3 = "SELECT TOP 1 * FROM TbCorreosEnviados"
        result3 = db.execute_query(query3)
        if result3:
            print("Campos disponibles en la tabla:")
            for key in result3[0].keys():
                print(f"  - {key}")
    except Exception as e:
        print(f"Error obteniendo estructura: {e}")