import pyodbc
import os
import sys
from pathlib import Path

# Añadir src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from common.config import config

def list_tables(db_path, db_name):
    print(f"\n=== Tablas en {db_name} ===")
    try:
        conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD={config.db_password};"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Obtener lista de tablas
        tables = cursor.tables(tableType='TABLE')
        table_names = []
        for table in tables:
            table_name = table.table_name
            if not table_name.startswith('MSys'):  # Filtrar tablas del sistema
                table_names.append(table_name)
        
        if table_names:
            for table in sorted(table_names):
                print(f"  - {table}")
        else:
            print("  No se encontraron tablas")
            
        conn.close()
        return table_names
        
    except Exception as e:
        print(f"Error al conectar con {db_name}: {e}")
        return []

if __name__ == "__main__":
    print("Verificando tablas en las bases de datos locales...")
    
    # Usar las rutas de configuración común
    expedientes_db = config.get_local_db_path('expedientes')
    tareas_db = config.get_local_db_path('tareas')
    
    # Verificar que los archivos existen
    if os.path.exists(expedientes_db):
        expedientes_tables = list_tables(expedientes_db, "Expedientes")
    else:
        print(f"No se encontró: {expedientes_db}")
        expedientes_tables = []
    
    if os.path.exists(tareas_db):
        tareas_tables = list_tables(tareas_db, "Tareas")
    else:
        print(f"No se encontró: {tareas_db}")
        tareas_tables = []
    
    print(f"\nResumen:")
    print(f"Tablas en Expedientes: {len(expedientes_tables)}")
    print(f"Tablas en Tareas: {len(tareas_tables)}")