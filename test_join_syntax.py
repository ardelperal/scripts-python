#!/usr/bin/env python3
"""
Script para probar diferentes sintaxis de LEFT JOIN en Access
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.database import AccessDatabase
from common.config import config

def test_join_queries():
    """Probar diferentes sintaxis de LEFT JOIN"""
    
    try:
        # Usar la configuración local de expedientes
        connection_string = config.get_db_expedientes_connection_string()
        print(f"Usando connection string: {connection_string}")
        
        db = AccessDatabase(connection_string)
        db.connect()
        print("Conexión exitosa a la base de datos")
        
        # Consulta 0: Primero probar una consulta simple sin JOIN
        print("\n=== Consulta 0: Simple SELECT sin JOIN ===")
        query0 = "SELECT TOP 5 IDExpediente, NumeroExpediente FROM TbExpedientes"
        try:
            result0 = db.execute_query(query0)
            print(f"✓ Consulta 0 exitosa: {len(result0)} registros")
        except Exception as e:
            print(f"✗ Consulta 0 falló: {e}")
        
        # Consulta 1: LEFT JOIN exactamente como en Expedientes.vbs
        print("\n=== Consulta 1: LEFT JOIN como en legacy ===")
        query1 = """
        SELECT TOP 5 TbExpedientes.IDExpediente, TbExpedientes.NumeroExpediente, TbExpedientesAnexos.IDAnexo
        FROM TbExpedientes LEFT JOIN TbExpedientesAnexos 
        ON TbExpedientes.IDExpediente = TbExpedientesAnexos.IDExpediente
        """
        try:
            result1 = db.execute_query(query1)
            print(f"✓ Consulta 1 exitosa: {len(result1)} registros")
        except Exception as e:
            print(f"✗ Consulta 1 falló: {e}")
        
        # Consulta 2: INNER JOIN simple para comparar
        print("\n=== Consulta 2: INNER JOIN simple ===")
        query2 = """
        SELECT TOP 5 TbExpedientes.IDExpediente, TbExpedientes.NumeroExpediente, TbExpedientesAnexos.IDAnexo
        FROM TbExpedientes INNER JOIN TbExpedientesAnexos 
        ON TbExpedientes.IDExpediente = TbExpedientesAnexos.IDExpediente
        """
        try:
            result2 = db.execute_query(query2)
            print(f"✓ Consulta 2 exitosa: {len(result2)} registros")
        except Exception as e:
            print(f"✗ Consulta 2 falló: {e}")
        
        # Consulta 3: LEFT JOIN con WHERE IS NULL (como en legacy)
        print("\n=== Consulta 3: LEFT JOIN con WHERE IS NULL ===")
        query3 = """
        SELECT TOP 5 TbExpedientes.IDExpediente, TbExpedientes.NumeroExpediente
        FROM TbExpedientes LEFT JOIN TbExpedientesAnexos 
        ON TbExpedientes.IDExpediente = TbExpedientesAnexos.IDExpediente
        WHERE TbExpedientesAnexos.IDExpediente IS NULL
        """
        try:
            result3 = db.execute_query(query3)
            print(f"✓ Consulta 3 exitosa: {len(result3)} registros")
        except Exception as e:
            print(f"✗ Consulta 3 falló: {e}")
        
        # Consulta 4: Probar con subconsulta EXISTS
        print("\n=== Consulta 4: Subconsulta con EXISTS ===")
        query4 = """
        SELECT TOP 5 IDExpediente, NumeroExpediente
        FROM TbExpedientes
        WHERE EXISTS (SELECT 1 FROM TbExpedientesAnexos WHERE TbExpedientesAnexos.IDExpediente = TbExpedientes.IDExpediente)
        """
        try:
            result4 = db.execute_query(query4)
            print(f"✓ Consulta 4 exitosa: {len(result4)} registros")
        except Exception as e:
            print(f"✗ Consulta 4 falló: {e}")
        
        db.disconnect()
        
    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    test_join_queries()