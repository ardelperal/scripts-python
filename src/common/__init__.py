"""
Paquete común con utilidades compartidas
"""
from .config import config
from .database import AccessDatabase
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
    'setup_logging',
    'is_workday',
    'is_night_time',
    'load_css_content',
    'generate_html_header',
    'generate_html_footer',
    'safe_str'
]
