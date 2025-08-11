"""
Paquete común con utilidades compartidas
"""
from .config import config
from .db.database import AccessDatabase
from .utils import (
    format_date,
    is_night_time,
    is_task_completed_today,
    is_workday,
    load_css_content,
    safe_str,
    setup_logging,
)
from .user_adapter import (
    get_technical_emails_string,
    get_quality_emails_string,
    get_economy_emails_string,
    get_user_email,
)
from .base_task import (
    register_task_completion,
    get_last_task_execution_date,
    should_execute_task,
)

# Limpieza: se eliminan importaciones duplicadas previamente listadas

__all__ = [
    "config",
    "AccessDatabase",
    "setup_logging",
    "register_task_completion",
    "get_last_task_execution_date",
    "should_execute_task",
    "is_workday",
    "is_night_time",
    "load_css_content",
    "safe_str",
    # user/email helpers re-exported
    "get_technical_emails_string",
    "get_quality_emails_string",
    "get_economy_emails_string",
    "get_user_email",
]

# Backward compatibility: create lightweight alias module common.database early
import sys as _sys
import types as _types

if "common.database" not in _sys.modules:  # pragma: no cover
    legacy_mod = _types.ModuleType("common.database")
    legacy_mod.AccessDatabase = AccessDatabase
    try:
        import pyodbc as _pyodbc  # type: ignore

        legacy_mod.pyodbc = _pyodbc  # type: ignore
    except Exception:  # pragma: no cover
        pass
    _sys.modules["common.database"] = legacy_mod
