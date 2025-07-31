import pyodbc
import sys
from pathlib import Path
import datetime

# Añadir src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from common.config import config

def test_date_query():
    print("Probando consulta con fechas...")
    
    expedientes_db = config.get_local_db_path('expedientes')
    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={expedientes_db};PWD={config.db_password};"
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Probar diferentes sintaxis de fecha
        queries = [
            ("SELECT COUNT(*) as total FROM TbExpedientes", []),
            ("SELECT TOP 5 IDExpediente, NumeroExpediente FROM TbExpedientes WHERE IDExpediente > ?", [0]),
            ("SELECT TOP 5 IDExpediente, NumeroExpediente FROM TbExpedientes WHERE IDExpediente BETWEEN ? AND ?", [1, 100]),
            ("SELECT TOP 5 IDExpediente, NumeroExpediente FROM TbExpedientes ORDER BY IDExpediente DESC", [])
        ]
        
        for i, (query, params) in enumerate(queries, 1):
            print(f"\n--- Consulta {i} ---")
            print(f"SQL: {query}")
            print(f"Parámetros: {params}")
            try:
                cursor.execute(query, params)
                result = cursor.fetchall()
                print(f"Resultado: {len(result)} filas")
                if result:
                    print(f"Primera fila: {result[0]}")
            except Exception as e:
                print(f"Error: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    test_date_query()