"""Runner de AGEDYS con argumento --force para ejecución manual.
Replica el patrón de brass y no_conformidades.
"""
from __future__ import annotations

import argparse

from agedys.agedys_task import AgedysTask
from common.config import config
from common.utils import setup_logging


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ejecuta tarea AGEDYS")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la ejecución, ignorando planificación.",
    )
    args = parser.parse_args(argv)

    setup_logging(config.log_file)
    task = AgedysTask()

    if args.force or task.debe_ejecutarse():
        task.ejecutar()
    else:
        print("Ejecución omitida (no toca hoy y sin --force)")
    task.close_connections()


if __name__ == "__main__":  # pragma: no cover
    main()
