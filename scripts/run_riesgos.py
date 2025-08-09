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

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.config import Config
from src.riesgos.riesgos_manager import RiesgosManager


def setup_logging(verbose: bool = False):
    """
    Configura el sistema de logging.
    
    Args:
        verbose: Si True, muestra logs de nivel DEBUG
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Usar ruta absoluta basada en el directorio del proyecto
    project_root = Path(__file__).parent.parent
    log_file = project_root / "logs" / "riesgos.log"
    
    # Asegurar que el directorio de logs existe
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
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
        from src.common.config import config
        logger.info(f"Configuración cargada para entorno: {config.environment}")
        
        # Crear manager de riesgos
        manager = RiesgosManager(config, logger)
        
        # Conectar a las bases de datos
        manager.connect_to_database()
        
        try:
            # Ejecutar tareas según los parámetros
            results = manager.run_daily_tasks(
                force_technical=args.force_technical,
                force_quality=args.force_quality,
                force_monthly=args.force_monthly
            )
            
            # Verificar resultados
            success = True
            if args.force_technical and not results.get('technical', False):
                logger.error("Error ejecutando tarea técnica")
                success = False
            if args.force_quality and not results.get('quality', False):
                logger.error("Error ejecutando tarea de calidad")
                success = False
            if args.force_monthly and not results.get('monthly', False):
                logger.error("Error ejecutando tarea mensual")
                success = False
            
            if success:
                logger.info("Todas las tareas solicitadas se ejecutaron exitosamente")
                return 0
            else:
                logger.error("Algunas tareas fallaron")
                return 1
                
        finally:
            manager.disconnect_from_database()
        
        return 0
        
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())