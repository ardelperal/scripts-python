"""
Módulo de configuración de logging para el proyecto.
"""

import logging
import sys
from datetime import datetime


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configura y retorna un logger con formato estándar.
    
    Args:
        name: Nombre del logger (normalmente __name__)
        level: Nivel de logging (por defecto INFO)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers si ya está configurado
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Crear formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger ya configurado o lo configura si no existe.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return setup_logger(name)