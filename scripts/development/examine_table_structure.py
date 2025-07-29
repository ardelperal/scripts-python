#!/usr/bin/env python3
"""
Script para examinar la estructura real de las tablas en la base de datos de No Conformidades
"""

import os
import sys
sys.path.append('src')

from common.database import get_database_instance
from common.config import Config

def examine_table_structure():
    """Examina la estructura de las tablas principales"""
    print("=== Examinando estructura de tablas en NoConformidades_Datos.accdb ===")
    
    config = Config()
    nc_connection_string = config.get_db_no_conformidades_connection_string()
    print(f"Cadena de conexión: {nc_connection_string}")
    
    # Examinar estructura de tablas principales
    main_tables = ['TbNoConformidades', 'TbNCAccionCorrectivas', 'TbNCAccionesRealizadas']
    
    for table_name in main_tables:
        print(f"\n=== Examinando estructura de {table_name} ===")
        
        try:
            # Método directo: consultar una fila para obtener estructura
            sample_query = f"SELECT TOP 1 * FROM {table_name}"
            print(f"Ejecutando: {sample_query}")
            
            # Usar el método execute_query_with_cursor para obtener información del cursor
            import pyodbc
            
            # Conectar directamente para obtener información del cursor
            conn = pyodbc.connect(nc_connection_string)
            cursor = conn.cursor()
            cursor.execute(sample_query)
            
            # Obtener información de las columnas
            columns_info = cursor.description
            print(f"  Columnas encontradas en {table_name}:")
            for i, col_info in enumerate(columns_info, 1):
                col_name = col_info[0]
                col_type = col_info[1].__name__ if hasattr(col_info[1], '__name__') else str(col_info[1])
                print(f"    {i:2d}. {col_name} ({col_type})")
            
            # Obtener una fila de muestra si existe
            row = cursor.fetchone()
            if row:
                print(f"  Muestra de datos:")
                for i, (col_info, value) in enumerate(zip(columns_info, row)):
                    col_name = col_info[0]
                    print(f"    {col_name}: {value}")
            else:
                print(f"  No hay datos en {table_name}")
            
            cursor.close()
            conn.close()
                
        except Exception as e:
            print(f"  Error examinando {table_name}: {e}")
            
            # Método de respaldo usando el wrapper de la aplicación
            db = get_database_instance(nc_connection_string)
            try:
                print(f"  Intentando método de respaldo...")
                sample_result = db.execute_query(sample_query)
                print(f"  Resultado obtenido: {len(sample_result) if sample_result else 0} filas")
                
                # Intentar obtener información del cursor del wrapper
                if hasattr(db, 'cursor') and db.cursor and hasattr(db.cursor, 'description'):
                    columns = [desc[0] for desc in db.cursor.description]
                    print(f"  Columnas en {table_name} (método respaldo):")
                    for i, col in enumerate(columns, 1):
                        print(f"    {i:2d}. {col}")
                else:
                    print(f"  No se pudo obtener información de columnas para {table_name}")
                    
            except Exception as e2:
                print(f"  Error con método de respaldo para {table_name}: {e2}")
            finally:
                db.disconnect()
    
    # Probar campos específicos que estamos usando en las consultas
    print(f"\n=== Verificando campos específicos usados en consultas ===")
    
    fields_to_test = [
        ('TbNCAccionCorrectivas', 'FechaFinalUltima'),  # Campo sospechoso
        ('TbNCAccionCorrectivas', 'FechaFinPrevista'),  # Campo alternativo
        ('TbNCAccionCorrectivas', 'FechaFin'),          # Campo alternativo
        ('TbNCAccionCorrectivas', 'Responsable'),       # Campo usado
        ('TbNCAccionesRealizadas', 'TipoAccion'),       # Campo que ya sabemos que no existe
        ('TbNoConformidades', 'RequiereControlEficacia'), # Campo del VBS
        ('TbNoConformidades', 'FechaControlEficacia'),    # Campo del VBS
    ]
    
    for table_name, field_name in fields_to_test:
        db = get_database_instance(nc_connection_string)
        try:
            test_query = f"SELECT TOP 1 {field_name} FROM {table_name}"
            db.execute_query(test_query)
            print(f"✓ {table_name}.{field_name} - EXISTE")
        except Exception as e:
            print(f"✗ {table_name}.{field_name} - NO EXISTE")
        finally:
            db.disconnect()

if __name__ == "__main__":
    examine_table_structure()