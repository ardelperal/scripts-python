"""Runner estandarizado Gestión de Riesgos.

Ejemplos:
  python run_riesgos.py
  python run_riesgos.py --force-technical --verbose
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

from common.logger import setup_global_logging  # type: ignore
from common.config import config  # type: ignore
from common.utils import ensure_project_root_in_path, execute_task_with_standard_boilerplate  # type: ignore
from riesgos.riesgos_task import RiesgosTask  # type: ignore

ensure_project_root_in_path()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tareas de gestión de riesgos")
    parser.add_argument(
        "--force-technical", action="store_true", help="Forzar tarea técnica"
    )
    parser.add_argument(
        "--force-quality", action="store_true", help="Forzar tarea de calidad"
    )
    parser.add_argument(
        "--force-monthly", action="store_true", help="Forzar tarea mensual"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simula sin registrar/envíar correos"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Logging detallado"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):  # pragma: no cover
    args = parse_args(argv)
    setup_global_logging("DEBUG" if args.verbose else "INFO")

    # Adaptar a execute_task_with_standard_boilerplate: crear task wrapper con método execute
    class _Wrapper:
        def __init__(self):
            self.inner = RiesgosTask()

        def execute(self):  # método detectado por util
            logger = logging.getLogger("tasks.RIESGOS")
            if args.verbose:
                logger.setLevel(logging.DEBUG)
            logger.info("Config entorno: %s", config.environment)
            results = self.inner.run_tasks(
                force_technical=args.force_technical,
                force_quality=args.force_quality,
                force_monthly=args.force_monthly,
            )
            ok = True
            if args.force_technical and not results.get("technical"):
                logger.error("Fallo tarea técnica")
                ok = False
            if args.force_quality and not results.get("quality"):
                logger.error("Fallo tarea calidad")
                ok = False
            if args.force_monthly and not results.get("monthly"):
                logger.error("Fallo tarea mensual")
                ok = False
            if ok:
                logger.info("Tareas completadas")
            return ok

    exit_code = execute_task_with_standard_boilerplate("RIESGOS", task_obj=_Wrapper())
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
