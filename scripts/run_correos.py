"""Runner estandarizado para envío de correos pendientes."""
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

from correos.correos_task import CorreosTask  # type: ignore
from common.utils import execute_task_with_standard_boilerplate  # type: ignore


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Envía correos no enviados.")
    parser.add_argument(
        "--force", action="store_true", help="(Reservado) Fuerza ejecución incluso si no hay criterios adicionales.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    _ = parse_args(argv)
    task = CorreosTask()
    exit_code = execute_task_with_standard_boilerplate(
        "CORREOS", task_obj=task
    )
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
