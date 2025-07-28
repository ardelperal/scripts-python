#!/usr/bin/env python3
"""
Script de ejecución para el módulo de gestión de riesgos.

Este script ejecuta las tareas diarias de gestión de riesgos,
equivalente al script VBScript GestionRiesgos.vbs.

Uso:
    python run_riesgos.py [--verbose] [--force-technical] [--force-quality] [--force-monthly]

Ejemplos:
    python run_riesgos.py
    python run_riesgos.py --verbose
    python run_riesgos.py --force-technical --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from common.config import Config
from riesgos.riesgos_manager import RiesgosManager


def setup_logging(verbose: bool = False):
    """
    Configura el sistema de logging.
    
    Args:
        verbose: Si True, muestra logs de nivel DEBUG
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/riesgos.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Ejecuta las tareas de gestión de riesgos'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar logs detallados'
    )
    parser.add_argument(
        '--force-technical',
        action='store_true',
        help='Forzar ejecución de tarea técnica'
    )
    parser.add_argument(
        '--force-quality',
        action='store_true',
        help='Forzar ejecución de tarea de calidad'
    )
    parser.add_argument(
        '--force-monthly',
        action='store_true',
        help='Forzar ejecución de tarea mensual'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Cargar configuración
        from common.config import config
        logger.info(f"Configuración cargada para entorno: {config.environment}")
        
        # Crear manager de riesgos
        manager = RiesgosManager(config)
        
        # Ejecutar tareas específicas si se solicita
        if args.force_technical or args.force_quality or args.force_monthly:
            if not manager.connect():
                logger.error("No se pudo conectar a la base de datos")
                return 1
            
            try:
                if args.force_technical:
                    logger.info("Forzando ejecución de tarea técnica")
                    if manager.execute_technical_task():
                        manager.record_task_execution('TECNICA')
                        logger.info("Tarea técnica ejecutada exitosamente")
                    else:
                        logger.error("Error ejecutando tarea técnica")
                        return 1
                
                if args.force_quality:
                    logger.info("Forzando ejecución de tarea de calidad")
                    if manager.execute_quality_task():
                        manager.record_task_execution('CALIDAD')
                        logger.info("Tarea de calidad ejecutada exitosamente")
                    else:
                        logger.error("Error ejecutando tarea de calidad")
                        return 1
                
                if args.force_monthly:
                    logger.info("Forzando ejecución de tarea mensual")
                    if manager.execute_monthly_quality_task():
                        manager.record_task_execution('CALIDADMENSUAL')
                        logger.info("Tarea mensual ejecutada exitosamente")
                    else:
                        logger.error("Error ejecutando tarea mensual")
                        return 1
            finally:
                manager.disconnect()
        else:
            # Ejecutar tareas diarias normales
            logger.info("Iniciando ejecución de tareas diarias de gestión de riesgos")
            
            if manager.execute_daily_task():
                logger.info("Tareas diarias ejecutadas exitosamente")
                return 0
            else:
                logger.error("Error ejecutando tareas diarias")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())