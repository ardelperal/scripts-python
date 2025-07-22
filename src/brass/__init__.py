"""
Módulo BRASS - Gestión de equipos de medida y calibraciones
"""
try:
    from .brass_manager import BrassManager
except ImportError:
    # Importación directa como fallback
    from brass_manager import BrassManager

__all__ = ['BrassManager']
