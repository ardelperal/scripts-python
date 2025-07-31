#!/usr/bin/env python3
"""
Script para probar consultas SQL que funcionan en el código legacy
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.database import AccessDatabase
from common.config import Config

def test_working_queries():
    """Probar consultas SQL que funcionan en el código legacy"""
    
    config = Config()
    connection_string = config.get_db_expedientes_connection_string()
    
    db = AccessDatabase(connection_string)
    db.connect()
    
    # Consultas basadas en el código legacy que funcionan
    queries = [
        # Consulta simple sin JOIN
        ("SELECT TOP 5 IDExpediente, CodExp, Nemotecnico FROM TbExpedientes", []),
        
        # Consulta con LEFT JOIN como en el código legacy (línea 711)
        ("SELECT TOP 5 IDExpediente, CodExp, Nemotecnico, Titulo, Nombre FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id", []),
        
        # Consulta con INNER JOIN anidado como en el código legacy (línea 792)
        ("SELECT TOP 5 TbExpedientesHitos.IDExpediente, CodExp, Nemotecnico FROM (TbExpedientesHitos INNER JOIN TbExpedientes ON TbExpedientesHitos.IDExpediente = TbExpedientes.IDExpediente)", []),
        
        # Consulta con COUNT simple
        ("SELECT COUNT(*) as total FROM TbExpedientes", []),
        
        # Consulta con subconsulta
        ("SELECT TOP 5 IDExpediente, (SELECT COUNT(*) FROM TbExpedientesAnexos WHERE TbExpedientesAnexos.IDExpediente = TbExpedientes.IDExpediente) AS TotalAnexos FROM TbExpedientes", [])
    ]
    
    for i, (query, params) in enumerate(queries, 1):
        try:
            print(f"\n{i}. Probando consulta:")
            print(f"   {query}")
            
            result = db.execute_query(query, params)
            print(f"   ✓ ÉXITO - Devolvió {len(result)} registros")
            
            if result:
                print(f"   Primer registro: {result[0]}")
                
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
    
    db.disconnect()

if __name__ == "__main__":
    test_working_queries()