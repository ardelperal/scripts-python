#!/usr/bin/env python3
"""
Script de prueba para el módulo de No Conformidades.
"""

import sys
import os
import logging
from pathlib import Path

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
        logger = setup_logger("test_noconformidades", "logs/test_noconformidades.log")
        logger.info("Iniciando prueba del módulo de No Conformidades")
        
        # Cargar configuración
        config = Config()
        logger.info(f"Configuración cargada - Entorno: {config.environment}")
        
        # Crear instancia del manager
        nc_manager = NoConformidadesManager(config, logger)
        logger.info("NoConformidadesManager creado exitosamente")
        
        # Verificar conexiones
        logger.info("Verificando conexiones a bases de datos...")
        
        # Probar conexión a tareas
        try:
            conn_tareas = nc_manager._get_tareas_connection()
            logger.info("✓ Conexión a base de datos de tareas exitosa")
        except Exception as e:
            logger.error(f"✗ Error conectando a base de datos de tareas: {e}")
            
        # Probar conexión a no conformidades
        try:
            conn_nc = nc_manager._get_nc_connection()
            logger.info("✓ Conexión a base de datos de no conformidades exitosa")
        except Exception as e:
            logger.error(f"✗ Error conectando a base de datos de no conformidades: {e}")
        
        # Verificar si es día entre semana
        es_dia_semana = nc_manager.es_dia_entre_semana()
        logger.info(f"Es día entre semana: {es_dia_semana}")
        
        # Verificar si se requieren tareas
        requiere_tecnica = nc_manager.requiere_tarea_tecnica()
        requiere_calidad = nc_manager.requiere_tarea_calidad()
        
        logger.info(f"Requiere tarea técnica: {requiere_tecnica}")
        logger.info(f"Requiere tarea calidad: {requiere_calidad}")
        
        # Probar obtención de usuarios con las nuevas funciones
        logger.info("Probando obtención de usuarios con nuevas funciones...")
        
        usuarios_admin = nc_manager.get_col_usuarios_administradores()
        usuarios_calidad = nc_manager.get_col_usuarios_calidad()
        
        logger.info(f"Usuarios administradores encontrados: {len(usuarios_admin)}")
        logger.info(f"Usuarios calidad encontrados: {len(usuarios_calidad)}")
        
        # Mostrar algunos detalles de los usuarios
        if usuarios_admin:
            logger.info(f"Primer usuario admin: {usuarios_admin[0].get('Nombre', 'N/A')}")
        if usuarios_calidad:
            logger.info(f"Primer usuario calidad: {usuarios_calidad[0].get('Nombre', 'N/A')}")
        
        # Obtener cadenas de correo
        correos_admin = nc_manager.get_cadena_correo_administradores()
        correos_calidad = nc_manager.get_cadena_correo_calidad()
        
        logger.info(f"Correos administradores: {correos_admin}")
        logger.info(f"Correos calidad: {correos_calidad}")
        
        logger.info("Prueba completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en la prueba: {e}")
        raise
    finally:
        # Cerrar conexiones
        if 'nc_manager' in locals():
            nc_manager.close_connections()
            logger.info("Conexiones cerradas")

if __name__ == "__main__":
    main()