"""
Script de prueba para verificar la conexión a las bases de datos Access usando el módulo común
"""
import os
import sys
from pathlib import Path

# Agregar el directorio src al path para importar los módulos
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from common.config import Config
from common.database import get_database_instance

def test_database_connection_with_config(db_name, db_type, config):
    """Prueba la conexión a una base de datos específica usando la configuración común"""
    print(f"\n=== Probando conexión a {db_name} ===")
    
    try:
        # Obtener la ruta de la base de datos desde la configuración
        db_path = config.get_database_path(db_type)
        
        # Verificar que el archivo existe
        if not os.path.exists(db_path):
            print(f"❌ ERROR: El archivo {db_path} no existe")
            return False
        
        print(f"✅ Archivo encontrado: {db_path}")
        
        # Obtener la cadena de conexión correcta
        if db_type == 'tareas':
            connection_string = config.get_db_tareas_connection_string()
        elif db_type == 'no_conformidades':
            connection_string = config.get_db_no_conformidades_connection_string()
        else:
            # Para otras bases de datos, usar el método genérico
            connection_string = config.get_db_connection_string(db_type)
        
        print(f"🔗 Cadena de conexión: {connection_string[:50]}...")
        
        # Crear instancia de base de datos
        db = get_database_instance(connection_string)
        
        # Probar conexión básica
        print(f"📡 Probando conexión...")
        
        # Intentar listar tablas (consulta simple que no requiere permisos especiales)
        query = "SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0"
        try:
            result = db.execute_query(query)
        except Exception as e:
            # Si falla MSysObjects, intentar con una consulta más simple
            print(f"⚠️  MSysObjects no accesible, probando consulta alternativa...")
            try:
                 # Probar con una consulta muy simple que no depende de tablas específicas
                 query = "SELECT 1 as test"
                 result = db.execute_query(query)
                 print(f"✅ Conexión exitosa a {db_name} (consulta básica)")
                 return True
            except Exception as e2:
                print(f"❌ Error en consulta alternativa: {str(e2)}")
                raise e
        
        if result:
            print(f"✅ Conexión exitosa a {db_name}")
            print(f"📋 Tablas encontradas: {len(result)}")
            for i, row in enumerate(result[:5]):  # Mostrar solo las primeras 5
                print(f"   - {row[0]}")
            if len(result) > 5:
                print(f"   ... y {len(result) - 5} más")
            return True
        else:
            print(f"⚠️  Conexión establecida pero no se encontraron tablas en {db_name}")
            return True
            
    except Exception as e:
        print(f"❌ ERROR al conectar a {db_name}: {str(e)}")
        return False

def test_tareas_database_queries(config):
    """Prueba consultas específicas en la base de datos de Tareas"""
    print(f"\n=== Probando consultas específicas en Tareas ===")
    
    try:
        db_path = config.get_database_path('tareas')
        connection_string = config.get_db_tareas_connection_string()
        db = get_database_instance(connection_string)
        
        # Consultar tabla de correos registrados
        print("📧 Consultando correos registrados...")
        query = "SELECT TOP 5 * FROM Correos ORDER BY ID DESC"
        result = db.execute_query(query)
        
        if result:
            print(f"✅ Se encontraron {len(result)} correos recientes")
            for row in result:
                print(f"   ID: {row[0]}, Aplicación: {row[1]}, Asunto: {row[2][:50]}...")
        else:
            print("ℹ️  No se encontraron correos registrados")
        
        # Consultar tabla de tareas completadas
        print("\n📋 Consultando tareas completadas...")
        query = "SELECT TOP 5 * FROM Tareas_Completadas ORDER BY ID DESC"
        result = db.execute_query(query)
        
        if result:
            print(f"✅ Se encontraron {len(result)} tareas completadas recientes")
            for row in result:
                print(f"   ID: {row[0]}, Aplicación: {row[1]}, Fecha: {row[2]}")
        else:
            print("ℹ️  No se encontraron tareas completadas")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR en consultas específicas: {str(e)}")
        return False

def main():
    """Función principal para probar todas las conexiones"""
    print("🔍 Iniciando pruebas de conexión a bases de datos usando configuración común...")
    
    # Crear instancia de configuración
    config = Config()
    print(f"🌍 Entorno: {config.environment}")
    print(f"🔑 Contraseña BD configurada: {'Sí' if config.db_password else 'No'}")
    
    # Bases de datos a probar
    databases = {
        'Tareas': 'tareas',
        'No Conformidades': 'no_conformidades'
    }
    
    results = {}
    
    for db_name, db_type in databases.items():
        results[db_name] = test_database_connection_with_config(db_name, db_type, config)
    
    # Pruebas específicas en la base de datos de Tareas
    if results.get('Tareas', False):
        test_tareas_database_queries(config)
    
    # Resumen final
    print(f"\n{'='*50}")
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"{'='*50}")
    
    successful = 0
    for db_name, success in results.items():
        status = "✅ EXITOSA" if success else "❌ FALLIDA"
        print(f"{db_name}: {status}")
        if success:
            successful += 1
    
    print(f"\n🎯 Resultado: {successful}/{len(results)} conexiones exitosas")
    
    if successful == len(results):
        print("🎉 ¡Todas las conexiones funcionan correctamente!")
    else:
        print("⚠️  Algunas conexiones fallaron. Revisar configuración.")

if __name__ == "__main__":
    main()