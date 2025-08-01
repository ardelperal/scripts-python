"""
Paquete común con utilidades compartidas
"""
from .config import config
from .database import AccessDatabase, DemoDatabase, get_database_instance
from .utils import (
    setup_logging,
    is_workday,
    is_night_time,
    load_css_content,
    generate_html_header,
    generate_html_footer,
    safe_str,
    get_admin_users,
    get_admin_emails_string,
    get_technical_users,
    get_technical_emails_string,
    get_quality_users,
    get_quality_emails_string,
    get_economy_users,
    get_economy_emails_string,
    get_user_email,
    register_email_in_database,
    send_notification_email,
    get_last_task_execution_date,
    is_task_completed_today,
    should_execute_task
)

__all__ = [
    'config',
    'AccessDatabase',
    'DemoDatabase',
    'get_database_instance',
    'setup_logging',
    'is_workday',
    'is_night_time',
    'load_css_content',
    'generate_html_header',
    'generate_html_footer',
    'safe_str'
]
