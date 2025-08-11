"""Shim mínimo para compatibilidad de tests (import src.brass.run_brass).

Delegación al runner real en scripts/run_brass.py evitando duplicar lógica.
Tests parchean BrassTask aquí; por eso se reexporta.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:  # pragma: no cover
    from scripts.run_brass import parse_args, main  # type: ignore
except Exception:  # pragma: no cover - fallback mínimo
    def parse_args(argv=None):  # type: ignore
        import argparse
        p = argparse.ArgumentParser(description="Runner BRASS (shim)")
        p.add_argument("--force", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        return p.parse_args(argv)

    def main(argv=None):  # type: ignore
        from brass.brass_task import BrassTask  # local import
        from common.utils import execute_task_with_standard_boilerplate
        args = parse_args(argv)
        task = BrassTask()
        code = execute_task_with_standard_boilerplate(
            "BRASS", task, force=args.force, dry_run=getattr(args, "dry_run", False)
        )
        sys.exit(code)

from brass.brass_task import BrassTask  # type: ignore  # reexport para monkeypatch

__all__ = ["BrassTask", "parse_args", "main"]

if __name__ == "__main__":  # pragma: no cover
    main()
