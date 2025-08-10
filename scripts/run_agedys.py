"""
Script de entrada para la ejecución de la Tarea AGEDYS.
"""
import sys
import logging
import argparse
from pathlib import Path

# Añadir el directorio src al path
SRC_DIR = Path(__file__).resolve().parent.parent / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from common.utils import setup_logging
from agedys.agedys_task import AgedysTask

def main():
    parser = argparse.ArgumentParser(description="Ejecuta la tarea de AGEDYS.")
    parser.add_argument(
        '--force',
        action='store_true',
        help='Fuerza la ejecución de la tarea, ignorando la planificación.'
    )
    args = parser.parse_args()

    setup_logging(log_file=Path('logs/agedys.log'))
    logger = logging.getLogger()

    logger.info("===============================================")
    logger.info("=         INICIANDO TAREA DE AGEDYS           =")
    logger.info("===============================================")
    if args.force:
        logger.warning("-> MODO FORZADO ACTIVADO <-")

    exit_code = 0
    try:
        with AgedysTask() as task:
            if args.force or task.debe_ejecutarse():
                if task.execute_specific_logic():
                    if not args.force:
                        task.marcar_como_completada()
                    logger.info("Tarea AGEDYS finalizada con éxito.")
                else:
                    logger.error("La lógica específica de la tarea AGEDYS falló.")
                    exit_code = 1
            else:
                logger.info("La tarea AGEDYS no requiere ejecución hoy.")
    except Exception as e:
        logger.critical(f"Error fatal no controlado en la tarea AGEDYS: {e}", exc_info=True)
        exit_code = 1

    logger.info("Finalizada la ejecución de la tarea AGEDYS.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()