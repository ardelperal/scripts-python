"""Runner de la tarea BRASS (estandarizado).

Responsabilidad:
  - Parsear argumentos (--force, --dry-run)
  - Configurar logging unificado
  - Ejecutar la lógica de BrassTask respetando planificación
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap mínimo para poder importar módulos del proyecto antes de importarlos
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from common.utils import ensure_project_root_in_path, execute_task_with_standard_boilerplate  # type: ignore
from brass.brass_task import BrassTask  # type: ignore

ensure_project_root_in_path()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta la tarea BRASS")
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Fuerza la ejecución ignorando planificación",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula la ejecución sin marcar ni registrar.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    args = parse_args(argv)
    task = BrassTask()
    exit_code = execute_task_with_standard_boilerplate(
        "BRASS", task, force=args.force, dry_run=args.dry_run
    )
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
