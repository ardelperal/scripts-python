"""Shim de compatibilidad para tests que importan src.brass.run_brass.

Delegamos en scripts/run_brass.py exponiendo BrassTask, parse_args y main.
Mantener mínimo para no duplicar lógica.
"""
from __future__ import annotations

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
scripts_runner = _PROJECT_ROOT / "scripts" / "run_brass.py"

if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

# Reutilizamos funciones reales importándolas desde scripts.run_brass
try:  # pragma: no cover
    from scripts.run_brass import main, parse_args  # type: ignore
except Exception:  # pragma: no cover
    # Fallback simplificado si hubiera problemas de import
    def parse_args(argv=None):  # type: ignore
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("--force", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        return p.parse_args(argv)

    def main(argv=None):  # type: ignore
        from brass.brass_task import BrassTask  # local import
        from common.utils import execute_task_with_standard_boilerplate
        args = parse_args(argv)
        task = BrassTask()
        return execute_task_with_standard_boilerplate("BRASS", task, force=args.force, dry_run=args.dry_run)

from brass.brass_task import BrassTask  # reexport para monkeypatch en tests

__all__ = ["BrassTask", "main", "parse_args"]
"""Script de entrada para la ejecución de la Tarea BRASS.
"""
import argparse
import logging
import sys
from pathlib import Path

from brass.brass_task import BrassTask
from common.utils import setup_logging

# Añadir el directorio src al path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(SRC_DIR))


def main():
    parser = argparse.ArgumentParser(description="Ejecuta la tarea de BRASS.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la ejecución de la tarea, ignorando la planificación.",
    )
    args = parser.parse_args()

    # Si ya hay logging global configurado (p.ej. lanzado desde un orquestador), no duplicar handlers
    if not logging.getLogger().handlers:
        # Reutilizamos la función estándar apuntando al log unificado por defecto
        setup_logging()
    logger = logging.getLogger()

    logger.info("===============================================")
    logger.info("=         INICIANDO TAREA DE BRASS            =")
    logger.info("===============================================")
    if args.force:
        logger.warning("-> MODO FORZADO ACTIVADO <-")

    exit_code = 0
    try:
        with BrassTask() as task:
            if args.force or task.debe_ejecutarse():
                if task.execute_specific_logic():
                    if not args.force:
                        task.marcar_como_completada()
                    logger.info("Tarea BRASS finalizada con éxito.")
                else:
                    logger.error("La lógica específica de la tarea BRASS falló.")
                    exit_code = 1
            else:
                logger.info("La tarea BRASS no requiere ejecución hoy.")
    except Exception as e:
        logger.critical(
            f"Error fatal no controlado en la tarea BRASS: {e}", exc_info=True
        )
        exit_code = 1

    logger.info("Finalizada la ejecución de la tarea BRASS.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
