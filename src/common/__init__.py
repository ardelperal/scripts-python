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
    safe_str
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
