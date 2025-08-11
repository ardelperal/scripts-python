"""Runner estandarizado para la tarea AGEDYS."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from common.utils import ensure_project_root_in_path, execute_task_with_standard_boilerplate  # type: ignore
from agedys.agedys_task import AgedysTask  # type: ignore

ensure_project_root_in_path()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta la tarea AGEDYS")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la ejecución ignorando planificación (no marca completada).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    args = parse_args(argv)
    task = AgedysTask()
    exit_code = execute_task_with_standard_boilerplate("AGEDYS", task, force=args.force)
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
