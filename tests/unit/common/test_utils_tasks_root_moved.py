from unittest.mock import MagicMock

from common.utils import execute_task_with_standard_boilerplate


class DummyTask:
    """Mock sencillo de una Task con interfaz mínima utilizada por el helper."""

    def __init__(self):
        self.debe_ejecutarse = MagicMock(return_value=True)
        self.execute_specific_logic = MagicMock(return_value=True)
        self.marcar_como_completada = MagicMock()
        # Soporta context manager

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_no_force_not_due_skips_logic(tmp_path, monkeypatch):
    task = DummyTask()
    task.debe_ejecutarse.return_value = False

    exit_code = execute_task_with_standard_boilerplate(
        "Dummy", task_obj=task, log_file=tmp_path / "dummy.log"
    )

    task.execute_specific_logic.assert_not_called()
    task.marcar_como_completada.assert_not_called()
    assert exit_code == 0


def test_no_force_due_executes_and_marks(tmp_path):
    task = DummyTask()
    task.debe_ejecutarse.return_value = True

    exit_code = execute_task_with_standard_boilerplate(
        "Dummy", task_obj=task, log_file=tmp_path / "dummy.log"
    )

    task.execute_specific_logic.assert_called_once()
    task.marcar_como_completada.assert_called_once()
    assert exit_code == 0


def test_force_executes_without_mark(tmp_path):
    task = DummyTask()

    exit_code = execute_task_with_standard_boilerplate(
        "Dummy", task_obj=task, force=True, log_file=tmp_path / "dummy.log"
    )

    task.execute_specific_logic.assert_called_once()
    task.marcar_como_completada.assert_not_called()
    assert exit_code == 0


def test_execute_specific_logic_exception_returns_error_code(tmp_path):
    task = DummyTask()
    task.execute_specific_logic.side_effect = RuntimeError("boom")

    exit_code = execute_task_with_standard_boilerplate(
        "Dummy", task_obj=task, log_file=tmp_path / "dummy.log"
    )

    task.execute_specific_logic.assert_called_once()
    # Como falla, no se debería marcar
    task.marcar_como_completada.assert_not_called()
    assert exit_code == 1
