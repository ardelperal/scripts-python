"""
Módulo BRASS - Gestión de equipos de medida y calibraciones
"""
import sys
import os

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from brass.brass_manager import BrassManager

__all__ = ['BrassManager']
