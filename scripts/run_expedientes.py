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

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
from common.utils import ensure_project_root_in_path  # type: ignore
ensure_project_root_in_path()

from common.utils import execute_task_with_standard_boilerplate  # type: ignore
from expedientes.expedientes_task import ExpedientesTask  # type: ignore


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta la tarea de Expedientes")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la ejecución aunque no toque según planificación (NO marca como completada).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    args = parse_args(argv)
    task = ExpedientesTask()
    exit_code = execute_task_with_standard_boilerplate(
        "EXPEDIENTES", task, force=args.force
    )
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()