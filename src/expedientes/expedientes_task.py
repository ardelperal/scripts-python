"""
Tarea de Expedientes - Migración del sistema original
"""

from src.common.base_task import TareaDiaria
from .expedientes_manager import ExpedientesManager


class ExpedientesTask(TareaDiaria):
    """Tarea para el sistema de Expedientes"""
    
    def __init__(self):
        super().__init__(
            name="EXPEDIENTES",
            script_filename="run_expedientes.py",
            task_names=["ExpedientesDiario"],  # Nombre corregido según indicación del usuario
            frequency_days=1  # Tarea diaria
        )
        self.manager = None
    
    def execute_specific_logic(self) -> bool:
        """
        Ejecuta la lógica específica de la tarea de Expedientes
        
        Returns:
            bool: True si se ejecutó correctamente
        """
        try:
            self.manager = ExpedientesManager()
            return self.manager.ejecutar_logica_especifica()
        except Exception as e:
            self.logger.error(f"Error ejecutando lógica específica de Expedientes: {e}")
            return False
    
    def close_connections(self):
        """Cierra las conexiones del manager"""
        if self.manager:
            try:
                self.manager.close_connections()
            except Exception as e:
                self.logger.warning(f"Error cerrando conexiones del manager: {e}")