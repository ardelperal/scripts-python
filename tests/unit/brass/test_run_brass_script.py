"""Tests ligeros para script run_brass (argumento --force)."""
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = Path("src") / "brass" / "run_brass.py"


def import_module_fresh():
    if "src.brass.run_brass" in sys.modules:
        del sys.modules["src.brass.run_brass"]
    return importlib.import_module("src.brass.run_brass")


def test_run_brass_normal(monkeypatch):
    """Ejecuta sin --force y simula que debe ejecutarse y se marca completada."""

    class DummyTask:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def debe_ejecutarse(self):
            return True

        def execute_specific_logic(self):
            return True

        def marcar_como_completada(self):
            self.marked = True

    monkeypatch.setattr("src.brass.run_brass.BrassTask", DummyTask)
    testargs = ["run_brass.py"]
    with patch.object(sys, "argv", testargs):
        mod = import_module_fresh()
        # main hace sys.exit -> capturamos
        try:
            mod.main()
        except SystemExit as e:
            assert e.code == 0


def test_run_brass_force(monkeypatch):
    class DummyTask:
        executed = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def debe_ejecutarse(self):
            return False  # con force se ignora

        def execute_specific_logic(self):
            self.executed = True
            return True

        def marcar_como_completada(self):
            self.marked = True

    monkeypatch.setattr("src.brass.run_brass.BrassTask", DummyTask)
    testargs = ["run_brass.py", "--force"]
    with patch.object(sys, "argv", testargs):
        mod = import_module_fresh()
        try:
            mod.main()
        except SystemExit as e:
            assert e.code == 0
