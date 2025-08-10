"""
Script de entrada para la ejecución de la Tarea BRASS.
"""
import sys
import logging
import argparse
from pathlib import Path

# Añadir el directorio src al path
SRC_DIR = Path(__file__).resolve().parent.parent / 'src'
sys.path.append(str(SRC_DIR))

from common.utils import setup_logging
from brass.brass_task import BrassTask

def main():
    parser = argparse.ArgumentParser(description="Ejecuta la tarea de BRASS.")
    parser.add_argument(
        '--force',
        action='store_true',
        help='Fuerza la ejecución de la tarea, ignorando la planificación.'
    )
    args = parser.parse_args()

    setup_logging(log_file=Path('logs/brass.log'))
    logger = logging.getLogger()

    logger.info("===============================================")
    logger.info("=         INICIANDO TAREA DE BRASS            =")
    logger.info("===============================================")
    if args.force:
        logger.warning("-> MODO FORZADO ACTIVADO <-")

    exit_code = 0
    try:
        with BrassTask() as task:
            if args.force or task.debe_ejecutarse():
                if task.execute_specific_logic():
                    if not args.force:
                        task.marcar_como_completada()
                    logger.info("Tarea BRASS finalizada con éxito.")
                else:
                    logger.error("La lógica específica de la tarea BRASS falló.")
                    exit_code = 1
            else:
                logger.info("La tarea BRASS no requiere ejecución hoy.")
    except Exception as e:
        logger.critical(f"Error fatal no controlado en la tarea BRASS: {e}", exc_info=True)
        exit_code = 1

    logger.info("Finalizada la ejecución de la tarea BRASS.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()