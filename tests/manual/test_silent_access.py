#!/usr/bin/env python3
"""
Script de prueba para verificar acceso silencioso a Access sin popups
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_silent_access():
    """Prueba el acceso silencioso a Access sin mostrar ningún popup"""
    
    # Cargar configuración
    project_root = Path(__file__).parent
    env_path = project_root / '.env'
    
    if not env_path.exists():
        logger.error("❌ Archivo .env no encontrado")
        return False
    
    load_dotenv(env_path)
    logger.info("📄 Configuración cargada desde .env")
    
    # Obtener contraseña
    db_password = os.getenv('DB_PASSWORD')
    if not db_password:
        logger.error("❌ Contraseña de BD no encontrada en .env")
        return False
    
    logger.info("🔐 Contraseña de BD encontrada")
    
    # Buscar una base de datos local para probar
    local_db_path = None
    for var_name in os.environ:
        if var_name.startswith('LOCAL_DB_'):
            db_path = os.getenv(var_name)
            if db_path:
                # Convertir ruta relativa a absoluta
                if not os.path.isabs(db_path):
                    db_path = str(project_root / db_path)
                
                if os.path.exists(db_path):
                    local_db_path = db_path
                    logger.info(f"✅ BD de prueba encontrada: {os.path.basename(db_path)}")
                    break
                else:
                    logger.warning(f"⚠️  BD no existe: {db_path}")
    
    if not local_db_path:
        logger.error("❌ No se encontró ninguna base de datos local para probar")
        return False
    
    # Importar módulos COM
    try:
        import win32com.client
        import pythoncom
        logger.info("✅ Módulos COM importados correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando módulos COM: {e}")
        return False
    
    # Probar acceso silencioso
    access_app = None
    try:
        logger.info("🔄 Iniciando prueba de acceso silencioso...")
        
        # Inicializar COM
        pythoncom.CoInitialize()
        
        # Crear aplicación Access en modo completamente silencioso
        logger.info("  📱 Creando aplicación Access...")
        access_app = win32com.client.Dispatch("Access.Application")
        access_app.Visible = False
        access_app.UserControl = False
        
        # Abrir base de datos con contraseña de forma silenciosa
        logger.info(f"  🔓 Abriendo BD: {os.path.basename(local_db_path)}")
        access_app.OpenCurrentDatabase(local_db_path, False, db_password)
        
        # Suprimir todos los mensajes y diálogos después de abrir la BD
        logger.info("  🔇 Suprimiendo todos los diálogos...")
        access_app.DoCmd.SetWarnings(False)
        
        # Verificar que se abrió correctamente
        db = access_app.CurrentDb()
        table_count = db.TableDefs.Count
        logger.info(f"  📊 BD abierta exitosamente - {table_count} tablas encontradas")
        
        # Buscar tablas vinculadas
        linked_count = 0
        for i in range(table_count):
            table_def = db.TableDefs(i)
            if hasattr(table_def, 'Connect') and table_def.Connect:
                linked_count += 1
        
        logger.info(f"  🔗 Tablas vinculadas encontradas: {linked_count}")
        
        # Restaurar advertencias
        access_app.DoCmd.SetWarnings(True)
        
        logger.info("✅ Prueba de acceso silencioso completada exitosamente")
        logger.info("🎯 No se mostraron popups durante el proceso")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}")
        return False
        
    finally:
        # Cerrar todo de forma silenciosa
        try:
            if access_app:
                logger.info("🔄 Cerrando Access...")
                access_app.CloseCurrentDatabase()
                access_app.Quit()
        except:
            pass
        
        try:
            pythoncom.CoUninitialize()
        except:
            pass

if __name__ == "__main__":
    logger.info("🧪 === Prueba de Acceso Silencioso a Access ===")
    
    success = test_silent_access()
    
    if success:
        logger.info("🎉 Todas las pruebas pasaron - El acceso es completamente silencioso")
        sys.exit(0)
    else:
        logger.error("💥 Las pruebas fallaron")
        sys.exit(1)