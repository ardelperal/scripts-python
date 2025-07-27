#!/usr/bin/env python3
"""
Script de prueba completo para el módulo de No Conformidades.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Agregar el directorio src al path
src_path = Path(__file__).parent / ".." / ".." / "src"
sys.path.insert(0, str(src_path))

from common.config import Config
from noconformidades import NoConformidadesManager

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
        logger = setup_logger("test_noconformidades_completo", "logs/test_noconformidades_completo.log")
        logger.info("Iniciando prueba completa del módulo de No Conformidades")
        
        # Cargar configuración
        config = Config()
        logger.info(f"Configuración cargada - Entorno: {config.environment}")
        
        # Inicializar NoConformidadesManager
        nc_manager = NoConformidadesManager(config=config, logger=logger)
        logger.info("NoConformidadesManager inicializado")
        
        # Probar conexiones
        logger.info("Probando conexiones a bases de datos...")
        try:
            tareas_conn = nc_manager._get_tareas_connection()
            logger.info("✓ Conexión a base de datos de tareas exitosa")
        except Exception as e:
            logger.error(f"✗ Error conectando a base de datos de tareas: {e}")
            
        try:
            nc_conn = nc_manager._get_nc_connection()
            logger.info("✓ Conexión a base de datos de no conformidades exitosa")
        except Exception as e:
            logger.error(f"✗ Error conectando a base de datos de no conformidades: {e}")
        
        # Probar métodos de validación
        logger.info("Probando métodos de validación...")
        
        # Verificar si es día entre semana
        es_dia_semana = nc_manager.es_dia_entre_semana()
        logger.info(f"Es día entre semana: {es_dia_semana}")
        
        # Probar métodos de requerimientos
        try:
            requiere_tecnica = nc_manager.requiere_tarea_tecnica("CALIDAD")
            logger.info(f"Requiere tarea técnica para CALIDAD: {requiere_tecnica}")
        except Exception as e:
            logger.warning(f"Error probando requiere_tarea_tecnica: {e}")
            
        try:
            requiere_calidad = nc_manager.requiere_tarea_calidad("CALIDAD")
            logger.info(f"Requiere tarea calidad para CALIDAD: {requiere_calidad}")
        except Exception as e:
            logger.warning(f"Error probando requiere_tarea_calidad: {e}")
        
        # Probar obtención de colecciones de usuarios
        logger.info("Probando obtención de colecciones de usuarios...")
        try:
            usuarios_arapc = nc_manager._get_col_usuarios_arapc()
            logger.info(f"Usuarios ARAPC obtenidos: {len(usuarios_arapc) if usuarios_arapc else 0}")
        except Exception as e:
            logger.warning(f"Error obteniendo usuarios ARAPC: {e}")
            
        try:
            arapc = nc_manager._get_col_arapc()
            logger.info(f"ARAPC obtenidos: {len(arapc) if arapc else 0}")
        except Exception as e:
            logger.warning(f"Error obteniendo ARAPC: {e}")
        
        # Probar generación de correos
        logger.info("Probando generación de correos...")
        try:
            correo_admin = nc_manager._get_correo("admin")
            logger.info(f"Correo admin generado: {len(correo_admin) if correo_admin else 0} caracteres")
        except Exception as e:
            logger.warning(f"Error generando correo admin: {e}")
            
        try:
            correo_calidad = nc_manager._get_correo("calidad")
            logger.info(f"Correo calidad generado: {len(correo_calidad) if correo_calidad else 0} caracteres")
        except Exception as e:
            logger.warning(f"Error generando correo calidad: {e}")
        
        # Cerrar conexiones
        nc_manager.close_connections()
        logger.info("Conexiones cerradas")
        
        logger.info("Prueba completa del módulo de No Conformidades finalizada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en la prueba: {e}")
        raise

if __name__ == "__main__":
    main()