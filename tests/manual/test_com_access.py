#!/usr/bin/env python3
"""
Script de prueba para verificar el acceso COM a bases de datos Access con contraseña
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_com_imports():
    """Prueba si se pueden importar las librerías COM necesarias"""
    try:
        import win32com.client
        import pythoncom
        logger.info("✅ Librerías COM importadas correctamente")
        return True
    except ImportError as e:
        logger.error(f"❌ Error importando librerías COM: {e}")
        logger.error("   Instala pywin32: pip install pywin32")
        return False

def test_access_connection(db_path: str, password: str = None):
    """
    Prueba la conexión a una base de datos Access usando COM
    
    Args:
        db_path: Ruta a la base de datos Access
        password: Contraseña de la base de datos (opcional)
    """
    if not os.path.exists(db_path):
        logger.error(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        import win32com.client
        import pythoncom
        
        # Inicializar COM
        pythoncom.CoInitialize()
        
        # Crear aplicación Access
        access_app = win32com.client.Dispatch("Access.Application")
        access_app.Visible = False
        
        logger.info(f"🔗 Intentando conectar a: {os.path.basename(db_path)}")
        
        # Abrir base de datos con o sin contraseña
        if password:
            logger.info("🔐 Usando contraseña para abrir la base de datos")
            access_app.OpenCurrentDatabase(db_path, False, password)
        else:
            logger.info("🔓 Abriendo base de datos sin contraseña")
            access_app.OpenCurrentDatabase(db_path, False)
        
        # Obtener información básica
        db = access_app.CurrentDb()
        table_count = db.TableDefs.Count
        
        logger.info(f"✅ Conexión exitosa!")
        logger.info(f"   Tablas encontradas: {table_count}")
        
        # Listar algunas tablas
        logger.info("📋 Primeras 5 tablas:")
        for i in range(min(5, table_count)):
            table_def = db.TableDefs(i)
            table_name = table_def.Name
            is_linked = "🔗" if hasattr(table_def, 'Connect') and table_def.Connect else "📄"
            logger.info(f"   {is_linked} {table_name}")
        
        # Cerrar conexión
        access_app.CloseCurrentDatabase()
        access_app.Quit()
        
        # Limpiar COM
        pythoncom.CoUninitialize()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        
        # Limpiar COM en caso de error
        try:
            if 'access_app' in locals():
                access_app.CloseCurrentDatabase()
                access_app.Quit()
            pythoncom.CoUninitialize()
        except:
            pass
        
        return False

def test_environment_setup():
    """Prueba la configuración del entorno y las bases de datos disponibles"""
    # Buscar archivo .env
    current_dir = Path(__file__).parent
    env_path = current_dir / '.env'
    
    if not env_path.exists():
        logger.error(f"❌ Archivo .env no encontrado en: {env_path}")
        return False
    
    logger.info(f"📄 Cargando configuración desde: {env_path}")
    load_dotenv(env_path)
    
    # Obtener contraseña
    db_password = os.getenv('DB_PASSWORD')
    if db_password:
        logger.info(f"🔐 Contraseña de BD encontrada: {'*' * len(db_password)}")
    else:
        logger.warning("⚠️ No se encontró contraseña de BD en .env")
    
    # Buscar bases de datos locales para probar
    local_databases = []
    
    # Patrones de variables de entorno para bases de datos locales
    local_db_vars = [
        'LOCAL_DB_BRASS',
        'LOCAL_DB_TAREAS', 
        'LOCAL_DB_CORREOS',
        'LOCAL_DB_NOCONFORMIDADES',
        'LOCAL_DB_LANZADERA',
        'LOCAL_DB_RIESGOS'
    ]
    
    for var in local_db_vars:
        db_path = os.getenv(var)
        if db_path:
            # Convertir a ruta absoluta si es relativa
            if not os.path.isabs(db_path):
                db_path = current_dir / db_path
            
            if os.path.exists(db_path):
                local_databases.append((var, str(db_path)))
                logger.info(f"✅ BD local encontrada: {var} -> {os.path.basename(db_path)}")
            else:
                logger.warning(f"⚠️ BD local configurada pero no existe: {var} -> {db_path}")
    
    if not local_databases:
        logger.warning("⚠️ No se encontraron bases de datos locales para probar")
        return False
    
    # Probar conexión a la primera base de datos encontrada
    var_name, db_path = local_databases[0]
    logger.info(f"\n🧪 Probando conexión COM con: {os.path.basename(db_path)}")
    
    return test_access_connection(db_path, db_password)

def main():
    """Función principal de prueba"""
    logger.info("🚀 Iniciando pruebas de acceso COM a Access")
    
    # Prueba 1: Importar librerías COM
    logger.info("\n=== PRUEBA 1: Importación de librerías COM ===")
    if not test_com_imports():
        logger.error("❌ Las pruebas no pueden continuar sin las librerías COM")
        return False
    
    # Prueba 2: Configuración del entorno
    logger.info("\n=== PRUEBA 2: Configuración del entorno ===")
    if not test_environment_setup():
        logger.error("❌ Error en la configuración del entorno")
        return False
    
    logger.info("\n✅ Todas las pruebas completadas exitosamente!")
    logger.info("🎯 El sistema está listo para usar COM con Access")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)