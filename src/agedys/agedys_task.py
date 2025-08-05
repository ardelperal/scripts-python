#!/usr/bin/env python3
"""
Tarea AGEDYS - Implementación de la interfaz de tarea para AGEDYS
"""

import os
import sys
from pathlib import Path

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from common.base_task import TareaDiaria
from agedys.agedys_manager import AgedysManager


class AgedysTask(TareaDiaria):
    """Tarea AGEDYS que hereda de TareaDiaria"""
    
    def __init__(self):
        super().__init__(
            name="AGEDYS",
            script_filename="run_agedys.py",
            task_names=["Tareas"],  # Nombre de la tarea en la BD (como en legacy)
            frequency_days=int(os.getenv('AGEDYS_FRECUENCIA_DIAS', '1'))
        )
        self.manager = None
    
    def execute(self) -> bool:
        """Ejecuta la lógica específica de AGEDYS"""
        try:
            if not self.debe_ejecutarse():
                return True
            
            # Crear el manager y ejecutar
            self.manager = AgedysManager()
            success = self.manager.run()
            
            if success:
                self.marcar_como_completada()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error ejecutando AGEDYS: {e}")
            return False
    
    def close_connections(self):
        """Cierra las conexiones de base de datos"""
        if self.manager:
            self.manager.close_connections()
        super().close_connections()