"""
Script principal para ejecutar las tareas de Expedientes
Equivalente al Expedientes.vbs original

Uso:
    python run_expedientes.py                    # Ejecución normal (verifica horarios)
    python run_expedientes.py --force            # Fuerza ejecución independientemente del horario
    python run_expedientes.py --dry-run          # Simula ejecución sin enviar emails
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.common.logger import setup_logger
from src.common.utils import should_execute_task, register_task_completion
from src.expedientes.expedientes_manager import ExpedientesManager


def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Script para ejecutar tareas de Expedientes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                    # Ejecución normal (verifica horarios)
  %(prog)s --force            # Fuerza ejecución independientemente del horario
  %(prog)s --dry-run          # Simula ejecución sin enviar emails
        """
    )
    
    # Opciones de forzado
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Fuerza la ejecución independientemente del horario'
    )
    
    # Opciones adicionales
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


def ejecutar_tarea_expedientes(dry_run=False):
    """Ejecuta la tarea de expedientes."""
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO TAREA DE EXPEDIENTES ===")
    if dry_run:
        logger.info("MODO DRY-RUN: No se enviarán emails reales")

    try:
        with ExpedientesManager() as expedientes_manager:
            logger.info("Ejecutando lógica específica de expedientes...")
            
            if dry_run:
                # En modo dry-run, podríamos simular la ejecución
                logger.info("DRY-RUN: Simulando ejecución de expedientes...")
                resultado = True
            else:
                resultado = expedientes_manager.ejecutar_logica_especifica()
            
            if resultado:
                logger.info("Tarea de expedientes ejecutada correctamente.")
                if not dry_run:
                    register_task_completion(expedientes_manager.db_tareas, "Expedientes")
                else:
                    logger.info("DRY-RUN: Se habría registrado la ejecución de la tarea.")
            else:
                logger.error("Error al ejecutar la tarea de expedientes.")
                return False

        logger.info("=== TAREA DE EXPEDIENTES COMPLETADA ===")
        return True
        
    except Exception as e:
        logger.error(f"Error ejecutando tarea de expedientes: {e}")
        return False


def main():
    """Función principal que determina si ejecutar la tarea"""
    # Parsear argumentos de línea de comandos
    args = parse_arguments()
    
    logger = setup_logger(__name__)
    logger.info("=== INICIANDO PROCESAMIENTO DE EXPEDIENTES ===")
    
    if args.dry_run:
        logger.info("MODO DRY-RUN ACTIVADO: No se enviarán emails ni se registrarán ejecuciones")
    
    # Determinar si ejecutar la tarea basado en argumentos
    ejecutar_tarea = False
    
    if args.force:
        logger.info("FORZANDO EJECUCIÓN DE TAREA DE EXPEDIENTES")
        ejecutar_tarea = True
    else:
        # Verificar horarios normales
        logger.info("Verificando horarios para ejecución normal...")
        
        try:
            # Usar context manager para verificar si se requiere ejecutar la tarea
            with ExpedientesManager() as expedientes_manager:
                # Verificar si se requiere ejecutar tarea usando función común
                # Tareas de expedientes: diarias (configurables via .env)
                frecuencia_expedientes = int(os.getenv('EXPEDIENTES_FRECUENCIA_DIAS', '1'))
                ejecutar_tarea = should_execute_task(
                    expedientes_manager.db_tareas, 
                    "Expedientes", 
                    frecuencia_expedientes, 
                    logger
                )
                logger.info(f"Requiere tarea de expedientes (cada {frecuencia_expedientes} días): {ejecutar_tarea}")
                
        except Exception as e:
            logger.error(f"Error verificando horarios: {e}")
            return False
    
    # Ejecutar tarea según sea necesario
    resultado = True
    
    if ejecutar_tarea:
        logger.info("Ejecutando tarea de expedientes...")
        resultado = ejecutar_tarea_expedientes(dry_run=args.dry_run)
    else:
        logger.info("No se requirió ejecutar la tarea de expedientes")
    
    # Resumen de resultados
    if ejecutar_tarea:
        logger.info("=== RESUMEN DE EJECUCIÓN ===")
        estado = "EXITOSA" if resultado else "FALLIDA"
        logger.info(f"Tarea Expedientes: {estado}")
    
    logger.info("=== PROCESAMIENTO COMPLETADO ===")
    
    return resultado


if __name__ == "__main__":
    import sys
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger = setup_logger(__name__)
        logger.error(f"Error crítico en ejecución: {e}")
        sys.exit(1)