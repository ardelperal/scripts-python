import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.common.config import Config

# Verificar estructura de la tabla TbCorreosEnviados en la base de datos de tareas
try:
    config = Config()
    
    # Usar la base de datos de tareas
    connection_string = config.get_db_tareas_connection_string()
    print(f"Cadena de conexión: {connection_string}")
    
    import pyodbc
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Obtener información de las columnas de la tabla TbCorreosEnviados
    print("\n=== ESTRUCTURA DE LA TABLA TbCorreosEnviados (Base de datos de tareas) ===")
    cursor.execute("SELECT * FROM TbCorreosEnviados WHERE 1=0")  # Query que no devuelve datos pero sí estructura
    
    columns = [column[0] for column in cursor.description]
    print("Columnas encontradas:")
    for i, col in enumerate(columns, 1):
        print(f"  {i}. {col}")
    
    # Verificar si hay registros
    cursor.execute("SELECT COUNT(*) as Total FROM TbCorreosEnviados")
    result = cursor.fetchone()
    print(f"\nTotal de registros en la tabla: {result[0]}")
    
    # Mostrar algunos registros de ejemplo si existen
    if result[0] > 0:
        cursor.execute("SELECT TOP 3 * FROM TbCorreosEnviados ORDER BY IDCorreo DESC")
        records = cursor.fetchall()
        print(f"\nÚltimos 3 registros:")
        for record in records:
            print(f"  IDCorreo: {record[0]}, Aplicacion: {record[1] if len(record) > 1 else 'N/A'}")
    
    conn.close()
    print("\n✅ Verificación completada exitosamente")
    
except Exception as e:
    print(f"❌ Error verificando estructura: {e}")
    import traceback
    traceback.print_exc()