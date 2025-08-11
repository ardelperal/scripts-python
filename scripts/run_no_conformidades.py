"""Runner estandarizado para tareas de No Conformidades.

Ahora la lógica de negocio reside en NoConformidadesTask (execute_specific_logic).
Este runner únicamente decide ejecución según flags y planificación.

Uso:
    python run_no_conformidades.py               # Ejecución normal (si debe)
    python run_no_conformidades.py --force       # Fuerza ejecución (sin marcar completada)
    python run_no_conformidades.py -v --force    # Forzado con verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from common.utils import ensure_project_root_in_path, execute_task_with_standard_boilerplate  # type: ignore
from no_conformidades.no_conformidades_task import NoConformidadesTask  # type: ignore

ensure_project_root_in_path()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Runner No Conformidades")
    parser.add_argument(
        "--force", action="store_true", help="Fuerza ejecución sin registrar completada"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Logging detallado"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    args = parse_args(argv)
    task = NoConformidadesTask()
    exit_code = execute_task_with_standard_boilerplate(
        "NO_CONFORMIDADES",
        task,
        force=args.force,
        dry_run=False,
        log_level=(logging.DEBUG if args.verbose else logging.INFO),
    )
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
