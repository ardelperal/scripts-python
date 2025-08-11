"""Script de entrada refactorizado para tarea No Conformidades (parcial).

Usa argparse + --force y patrón execute_specific_logic como Brass/Expedientes.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from common.utils import setup_logging

from .no_conformidades_task import NoConformidadesTask


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta la tarea de No Conformidades (parcial refactor)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la ejecución, ignorando planificación.",
    )
    args = parser.parse_args()

    log_file = Path("logs/no_conformidades.log")
    setup_logging(log_file=log_file)
    logger = logging.getLogger()

    logger.info("===============================================")
    logger.info("=    INICIANDO TAREA NO CONFORMIDADES (NC)    =")
    logger.info("===============================================")
    if args.force:
        logger.warning("-> MODO FORZADO ACTIVADO <-")

    exit_code = 0
    try:
        with NoConformidadesTask() as task:
            if args.force or task.debe_ejecutarse():
                if task.execute_specific_logic():
                    if not args.force:
                        task.marcar_como_completada()
                    logger.info("Tarea NC finalizada con éxito.")
                else:
                    logger.error("La lógica específica de la tarea NC falló.")
                    exit_code = 1
            else:
                logger.info("La tarea NC no requiere ejecución hoy.")
    except Exception as e:  # pragma: no cover
        logger.critical(f"Error fatal no controlado en tarea NC: {e}", exc_info=True)
        exit_code = 1

    logger.info("Finalizada la ejecución de la tarea NC.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
