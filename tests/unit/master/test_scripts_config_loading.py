import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent.parent.parent / "scripts" / "run_master.py"
CONFIG = Path(__file__).parent.parent.parent.parent / "scripts_config.json"


def test_scripts_config_exists():
    assert CONFIG.exists(), "scripts_config.json debe existir"
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert "scripts" in data
    assert "brass" in data["scripts"]


def test_run_master_loads_config(monkeypatch):
    env = os.environ.copy()
    env["MASTER_DRY_SUBPROCESS"] = "1"  # dry-run rápido
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--single-cycle", "--verbose"],
        capture_output=True,
        text=True,
        timeout=8,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout.lower() + proc.stderr.lower()
    # Debe mostrar los scripts cargados (al menos brass y riesgos)
    assert "brass" in out
    assert "riesgos" in out
