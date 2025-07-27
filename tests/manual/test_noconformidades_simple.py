#!/usr/bin/env python3
"""
Script de prueba simplificado para el módulo de No Conformidades.
"""

import sys
import os
import logging
from pathlib import Path

# Agregar el directorio src al path
src_path = Path(__file__).parent / ".." / ".." / "src"
sys.path.insert(0, str(src_path))

from common.config import Config
from common.database import AccessDatabase

def setup_logger(name, log_file):
    """Configurar logger básico."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Crear directorio de logs si no existe
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def main():
    """Función principal de prueba."""
    try:
        # Configurar logging
        logger = setup_logger("test_noconformidades_simple", "logs/test_noconformidades_simple.log")
        logger.info("Iniciando prueba simplificada del módulo de No Conformidades")
        
        # Cargar configuración
        config = Config()
        logger.info(f"Configuración cargada - Entorno: {config.environment}")
        
        # Probar conexión a tareas
        try:
            tareas_conn_str = config.get_db_tareas_connection_string()
            logger.info("Probando conexión a base de datos de tareas...")
            tareas_db = AccessDatabase(tareas_conn_str)
            tareas_db.connect()
            logger.info("✓ Conexión a base de datos de tareas exitosa")
            tareas_db.disconnect()
        except Exception as e:
            logger.error(f"✗ Error conectando a base de datos de tareas: {e}")
            
        # Probar conexión a no conformidades
        try:
            nc_conn_str = config.get_db_noconformidades_connection_string()
            logger.info("Probando conexión a base de datos de no conformidades...")
            nc_db = AccessDatabase(nc_conn_str)
            nc_db.connect()
            logger.info("✓ Conexión a base de datos de no conformidades exitosa")
            nc_db.disconnect()
        except Exception as e:
            logger.error(f"✗ Error conectando a base de datos de no conformidades: {e}")
        
        logger.info("Prueba simplificada completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en la prueba: {e}")
        raise

if __name__ == "__main__":
    main()