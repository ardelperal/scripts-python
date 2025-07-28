#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de limpiar y rellenar la base de correos
"""

import os
import sys
import time
import logging
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

def main():
    """Función principal de prueba"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Verificar rutas de bases de datos
        office_db = os.getenv('OFFICE_DB_CORREOS')
        local_db = os.getenv('LOCAL_DB_CORREOS')
        
        if not office_db or not local_db:
            logger.error("❌ Variables de entorno de bases de datos no encontradas")
            return False
        
        logger.info(f"📋 Base de oficina: {office_db}")
        logger.info(f"📋 Base local: {local_db}")
        
        # Verificar que la base de oficina existe
        if not os.path.exists(office_db):
            logger.error(f"❌ Base de oficina no encontrada: {office_db}")
            return False
        
        # Importar la clase
        from setup_local_environment import LocalEnvironmentSetup
        
        # Crear instancia
        setup = LocalEnvironmentSetup()
        
        # Verificar si la base local existe
        local_exists = os.path.exists(local_db)
        logger.info(f"📊 Base local existe: {'Sí' if local_exists else 'No'}")
        
        # Usar siempre el método principal que maneja ambos casos
        logger.info("🔄 Configurando base de correos (modo ligero)...")
        start_time = time.time()
        success = setup._setup_correos_database_light(office_db, local_db)
        end_time = time.time()
        
        if success:
            logger.info(f"✅ Operación completada en {end_time - start_time:.2f} segundos")
            
            # Verificar el tamaño de la base local
            if os.path.exists(local_db):
                size_mb = os.path.getsize(local_db) / (1024 * 1024)
                logger.info(f"📊 Tamaño de base local: {size_mb:.2f} MB")
            else:
                logger.error("❌ Base local no encontrada después de la operación")
                return False
        else:
            logger.error("❌ Operación falló")
            return False
        
        logger.info("🎉 Prueba completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)