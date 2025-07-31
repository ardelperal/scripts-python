from src.common.database import AccessDatabase
from src.common.config import config

# Probar la consulta correcta
db_path = config.get_local_db_path('tareas')
db = AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD={config.db_password};")

query = """
SELECT TbUsuariosAplicaciones.CorreoUsuario
FROM TbUsuariosAplicaciones 
INNER JOIN TbUsuariosAplicacionesPermisos 
ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario
WHERE TbUsuariosAplicacionesPermisos.IDAplicacion = 20 AND TbUsuariosAplicacionesPermisos.EsUsuarioAdministrador = 'Sí'
"""

try:
    result = db.execute_query(query)
    print(f"Consulta exitosa. Resultado: {result}")
except Exception as e:
    print(f"Error en la consulta: {e}")
    
    # Probar consultas más simples para diagnosticar
    print("\n--- Diagnóstico ---")
    
    try:
        # Verificar estructura de TbUsuariosAplicaciones
        result1 = db.execute_query("SELECT TOP 1 * FROM TbUsuariosAplicaciones")
        print(f"TbUsuariosAplicaciones campos: {list(result1[0].keys()) if result1 else 'Sin registros'}")
    except Exception as e1:
        print(f"Error en TbUsuariosAplicaciones: {e1}")
    
    try:
        # Verificar estructura de TbUsuariosAplicacionesPermisos
        result2 = db.execute_query("SELECT TOP 1 * FROM TbUsuariosAplicacionesPermisos")
        print(f"TbUsuariosAplicacionesPermisos campos: {list(result2[0].keys()) if result2 else 'Sin registros'}")
    except Exception as e2:
        print(f"Error en TbUsuariosAplicacionesPermisos: {e2}")