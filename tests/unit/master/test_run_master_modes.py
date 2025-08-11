import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "run_master.py"


def run(cmd):
    env = os.environ.copy()
    env["MASTER_DRY_SUBPROCESS"] = "1"
    # Insertar src en PYTHONPATH para importaciones internas
    src_path = str(Path(__file__).parent.parent.parent.parent / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src_path + (os.pathsep + existing if existing else "")
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH)] + cmd,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def test_simple_mode_executes(monkeypatch):
    # Simular is_workday True para que intente ejecutar diarias (aunque no haya tareas registradas reales)
    # Si no existen tareas, el runner debe terminar igualmente sin error.
    result = run(["--simple"])
    assert result.returncode == 0, result.stderr
    combined = result.stdout + result.stderr
    # Verificamos específicamente la presencia del resumen de modo simple
    assert "RESUMEN (MODO SIMPLE)" in combined.upper()


def test_classic_single_cycle_mode(monkeypatch):
    # Ejecuta un ciclo único clásico (no simple) para verificar que arranca y finaliza
    result = run(["--single-cycle"])
    assert result.returncode == 0, result.stderr
    # Debe imprimir indicios del ciclo y resumen
    stdout_lower = (result.stdout + result.stderr).lower()
    assert "ciclo" in stdout_lower
    assert "resumen" in stdout_lower
