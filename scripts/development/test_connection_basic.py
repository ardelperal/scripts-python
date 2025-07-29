#!/usr/bin/env python3
"""
Script de diagnóstico básico para verificar la conexión a la base de datos
"""

import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from common.config import Config
from common.database import get_database_instance

def diagnostico_basico():
    """Diagnóstico básico de conexión"""
    print("=== Diagnóstico básico de conexión ===")
    
    try:
        config = Config()
        nc_connection_string = config.get_db_no_conformidades_connection_string()
        print(f"Cadena de conexión: {nc_connection_string}")
        
        db = get_database_instance(nc_connection_string)
        print("✓ Instancia de base de datos creada")
        
        # Probar conexión básica
        try:
            # Intentar una consulta muy simple
            test_query = "SELECT 1 as test"
            result = db.execute_query(test_query)
            print(f"✓ Consulta básica exitosa: {result}")
            
        except Exception as e:
            print(f"✗ Error en consulta básica: {e}")
            print(f"Tipo de error: {type(e)}")
            
        # Intentar listar tablas usando MSysObjects
        try:
            tables_query = "SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0"
            tables = db.execute_query(tables_query)
            print(f"✓ Consulta de tablas exitosa. Encontradas: {len(tables) if tables else 0}")
            if tables:
                for table in tables[:5]:  # Mostrar solo las primeras 5
                    print(f"  - {table[0]}")
                    
        except Exception as e:
            print(f"✗ Error listando tablas: {e}")
            
        # Intentar acceso directo a una tabla conocida
        try:
            direct_query = "SELECT TOP 1 IDNoConformidad FROM TbNoConformidades"
            direct_result = db.execute_query(direct_query)
            print(f"✓ Acceso directo a TbNoConformidades exitoso: {direct_result}")
            
        except Exception as e:
            print(f"✗ Error acceso directo: {e}")
            print(f"Detalles del error: {str(e)}")
            
        # Verificar el estado del objeto database
        print(f"\nEstado del objeto database:")
        print(f"  Tipo: {type(db)}")
        print(f"  Tiene cursor: {hasattr(db, 'cursor')}")
        if hasattr(db, 'cursor'):
            print(f"  Cursor: {db.cursor}")
        print(f"  Tiene connection: {hasattr(db, 'connection')}")
        if hasattr(db, 'connection'):
            print(f"  Connection: {db.connection}")
            
    except Exception as e:
        print(f"✗ Error general: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            if 'db' in locals():
                db.disconnect()
                print("✓ Desconexión exitosa")
        except Exception as e:
            print(f"✗ Error en desconexión: {e}")

if __name__ == "__main__":
    diagnostico_basico()