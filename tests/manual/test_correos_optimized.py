#!/usr/bin/env python3
"""
Script de prueba optimizado para verificar la funcionalidad de base de datos de correos ligera
"""

import os
import sys
import logging
import time
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
        logger.info("🧪 Iniciando prueba optimizada de base de datos de correos...")
        
        # Cargar configuración
        load_dotenv()
        
        # Obtener rutas de las bases de datos
        office_db = os.getenv('OFFICE_DB_CORREOS')
        local_db = os.getenv('LOCAL_DB_CORREOS')
        
        if not office_db or not local_db:
            logger.error("No se encontraron las variables de entorno para las bases de datos de correos")
            return False
        
        logger.info(f"Base de oficina: {office_db}")
        logger.info(f"Base local: {local_db}")
        
        # Verificar que la base de oficina existe
        if not os.path.exists(office_db):
            logger.error(f"La base de datos de oficina no existe: {office_db}")
            return False
        
        # Importar y usar la clase LocalEnvironmentSetup
        from setup_local_environment import LocalEnvironmentSetup
        
        # Crear instancia
        setup = LocalEnvironmentSetup()
        
        # Medir tiempo de ejecución
        start_time = time.time()
        
        # Ejecutar la configuración optimizada
        logger.info("Ejecutando configuración optimizada...")
        result = setup._setup_correos_database_light(office_db, local_db)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result:
            logger.info(f"✅ Configuración completada exitosamente en {execution_time:.2f} segundos")
            
            # Verificar resultado
            if os.path.exists(local_db):
                file_size = os.path.getsize(local_db) / (1024 * 1024)  # MB
                logger.info(f"📁 Base de datos local creada: {file_size:.2f} MB")
                return True
            else:
                logger.error("❌ La base de datos local no fue creada")
                return False
        else:
            logger.error(f"❌ Error en la configuración después de {execution_time:.2f} segundos")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en la prueba: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)