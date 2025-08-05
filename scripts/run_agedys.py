#!/usr/bin/env python3
"""
Script principal para ejecutar las tareas de AGEDYS
Adaptación del script legacy AGEDYS.VBS a Python

Uso:
    python run_agedys.py                    # Ejecución normal (verifica horarios)
    python run_agedys.py --force            # Fuerza ejecución independientemente del horario
    python run_agedys.py --dry-run          # Simula ejecución sin enviar emails
"""

import sys
import argparse
import logging
from pathlib import Path

# Añadir el directorio raíz del proyecto al path para importaciones
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from common.logger import setup_logger
from common.config import Config
from agedys.agedys_manager import AgedysManager


def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Script para ejecutar tareas de AGEDYS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                    # Ejecución normal (verifica horarios)
  %(prog)s --force            # Fuerza ejecución independientemente del horario
  %(prog)s --dry-run          # Simula ejecución sin enviar emails
        """
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Fuerza la ejecución independientemente del horario'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Simula la ejecución sin enviar emails reales'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Habilita logging detallado'
    )
    
    return parser.parse_args()


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Ejecutar tarea AGEDYS')
    parser.add_argument('--force', action='store_true', help='Forzar ejecución independientemente de las reglas de negocio')
    parser.add_argument('--dry-run', action='store_true', help='Ejecutar en modo simulación')
    
    args = parser.parse_args()
    
    # Configurar logging
    logger = setup_logger(__name__)
    
    try:
        logger.info("=== INICIANDO EJECUCIÓN DE AGEDYS ===")
        
        # Crear instancia del manager
        agedys_manager = AgedysManager()
        
        # Si se fuerza la ejecución, saltamos la verificación de debe_ejecutarse
        if args.force:
            logger.info("Forzando ejecución de AGEDYS...")
            success = agedys_manager.run()
        else:
            # Verificar si debe ejecutarse
            if agedys_manager.debe_ejecutarse():
                success = agedys_manager.run()
            else:
                logger.info("AGEDYS no necesita ejecutarse según las reglas de negocio")
                success = True
        
        if success:
            logger.info("=== AGEDYS COMPLETADO EXITOSAMENTE ===")
            return 0
        else:
            logger.error("=== AGEDYS FALLÓ ===")
            return 1
            
    except Exception as e:
        logger.error(f"ERROR CRITICO: {e}")
        return 1
    finally:
        # Asegurar que las conexiones se cierren
        try:
            if 'agedys_manager' in locals():
                agedys_manager.close_connections()
        except Exception as e:
            logger.warning(f"Error cerrando conexiones: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)