"""Runner estandarizado para notificaciones de tareas (correo_tareas)."""
from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
from common.utils import ensure_project_root_in_path  # type: ignore
ensure_project_root_in_path()

from correo_tareas.correo_tareas_task import CorreoTareasTask  # type: ignore
from common.utils import execute_task_with_standard_boilerplate  # type: ignore


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta notificaciones de correo de tareas.")
    parser.add_argument(
        "--force", action="store_true", help="(Reservado) Fuerza ejecución incluso sin criterios.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    _ = parse_args(argv)
    task = CorreoTareasTask()
    exit_code = execute_task_with_standard_boilerplate(
        "CORREO_TAREAS", task_obj=task
    )
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
