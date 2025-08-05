"""
Tarea de Expedientes - Migración del sistema legacy
"""

from src.common.base_task import TareaDiaria
from expedientes.expedientes_manager import ExpedientesManager


class ExpedientesTask(TareaDiaria):
    """Tarea para el sistema de Expedientes"""
    
    def __init__(self):
        super().__init__(
            name="EXPEDIENTES",
            script_filename="run_expedientes.py",
            task_names=["ExpedientesDiario"],  # Nombre corregido según indicación del usuario
            frequency_days=1  # Tarea diaria
        )