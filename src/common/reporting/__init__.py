"""Subpaquete reporting: generadores y configuraciones de tablas HTML."""
from .html_report_generator import HTMLReportGenerator  # noqa: F401
from .table_configurations import *  # noqa: F401,F403

__all__ = ["HTMLReportGenerator"]
