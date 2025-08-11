"""
Paquete común con utilidades compartidas
"""
from .config import config
from .database import AccessDatabase
from .utils import (
    format_date,
    get_admin_emails_string,
    get_admin_users,
    get_economy_emails_string,
    get_economy_users,
    get_last_task_execution_date,
    get_quality_emails_string,
    get_quality_users,
    get_technical_emails_string,
    get_technical_users,
    get_user_email,
    is_night_time,
    is_task_completed_today,
    is_workday,
    load_css_content,
    register_email_in_database,
    safe_str,
    setup_logging,
    should_execute_task,
)

# Limpieza: se eliminan importaciones duplicadas previamente listadas

__all__ = [
    "config",
    "AccessDatabase",
    "setup_logging",
    "is_workday",
    "is_night_time",
    "load_css_content",
    "safe_str",
]
