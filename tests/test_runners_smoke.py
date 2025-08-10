"""Smoke tests para validar que cada runner se puede invocar con --help.

Objetivo: detectar errores de sintaxis, imports o configuración temprana antes de ejecutar lógica pesada.
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
import pytest

# Descubrir scripts run_*.py (excluyendo run_master.py) dentro de la carpeta scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Recolectar runners
RUNNER_SCRIPTS = sorted(
    [p for p in SCRIPTS_DIR.glob("run_*.py") if p.name != "run_master.py"]
)

@pytest.mark.parametrize("script_path", RUNNER_SCRIPTS, ids=lambda p: p.name)
def test_runner_help(script_path: Path):
    """Cada runner debe responder correctamente a --help (exit code 0)."""
    # Ejecutar el script con --help
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"{script_path.name} --help retorno {result.returncode}.\n"
        f"STDOUT:\n{result.stdout[:500]}\n---\nSTDERR:\n{result.stderr[:500]}"
    )

# Si no se encontraron scripts, marcamos el test como fallido explícitamente para visibilidad.
# (En circunstancias normales siempre habrá al menos uno.)
if not RUNNER_SCRIPTS:  # pragma: no cover
    def test_no_runners_found():  # type: ignore
        pytest.fail("No se encontraron scripts run_*.py en la carpeta scripts/")
