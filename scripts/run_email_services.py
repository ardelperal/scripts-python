"""Runner estandarizado para la tarea unificada de servicios de correo (correos + tareas)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from common.logger import setup_global_logging  # type: ignore
from common.utils import ensure_project_root_in_path, execute_task_with_standard_boilerplate  # type: ignore
from email_services.email_task import EmailServicesTask  # type: ignore

ensure_project_root_in_path()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta el servicio unificado de envío de correos (correos + tareas)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="(Reservado) Fuerza la ejecución incluso sin criterios adicionales.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    _ = parse_args(argv)
    setup_global_logging()
    task = EmailServicesTask()
    exit_code = execute_task_with_standard_boilerplate("EMAIL_SERVICES", task_obj=task)
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
