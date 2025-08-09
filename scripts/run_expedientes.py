"""Script de entrada para la ejecución de la Tarea de Expedientes.

Responsabilidad:
  - Parsear argumentos CLI (actualmente sólo --force)
  - Instanciar y ejecutar la clase ExpedientesTask respetando la lógica de planificación

Ejecución recomendada (desde la raíz del proyecto):
    python -m scripts.run_expedientes [--force]

--force: Fuerza la ejecución ignorando la planificación y SIN marcar como completada.
"""
from __future__ import annotations

import sys
import logging
import argparse
from pathlib import Path

from src.common.utils import setup_logging
from src.expedientes.expedientes_task import ExpedientesTask


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta la tarea de Expedientes")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la ejecución aunque no toque según planificación (NO marca como completada).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    setup_logging(log_file=Path("logs/expedientes.log"))
    logger = logging.getLogger()

    logger.info("=== INICIO TAREA EXPEDIENTES ===", extra={'event': 'task_start', 'task': 'EXPEDIENTES', 'app': 'EXPEDIENTES'})

    exit_code = 0

    try:
        with ExpedientesTask() as task:
            if args.force:
                logger.info("Ejecución forzada (--force) ignorando planificación. No se marcará como completada.")
                if not task.execute_specific_logic():
                    logger.error("La ejecución forzada de la tarea de Expedientes falló.")
                    exit_code = 1
            else:
                if task.debe_ejecutarse():
                    logger.info("La tarea de Expedientes requiere ejecución.")
                    if task.execute_specific_logic():
                        task.marcar_como_completada()
                        logger.info("Tarea de Expedientes completada y marcada exitosamente.")
                    else:
                        logger.error("La lógica específica de la tarea de Expedientes falló.")
                        exit_code = 1
                else:
                    logger.info("La tarea de Expedientes no requiere ejecución hoy.")
    except Exception as e:  # pragma: no cover (ruta de error global difícil de forzar en smoke tests)
        logging.getLogger().critical(
            f"Error fatal no controlado en la ejecución de la tarea de Expedientes: {e}",
            exc_info=True,
        )
        exit_code = 1

    logger.info("=== FIN TAREA EXPEDIENTES ===", extra={'event': 'task_end', 'task': 'EXPEDIENTES', 'exit_code': exit_code, 'app': 'EXPEDIENTES'})
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()