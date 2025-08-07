"""
Tarea BRASS - Implementación usando la nueva arquitectura
"""
import logging
import os
from datetime import date

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in os.sys.path:
    os.sys.path.insert(0, src_dir)

from common.base_task import TareaDiaria
from brass.brass_manager import BrassManager

logger = logging.getLogger(__name__)


class BrassTask(TareaDiaria):
    """Tarea BRASS para la nueva arquitectura"""
    
    def __init__(self):
        # Inicializar con los parámetros requeridos por TareaDiaria
        super().__init__(
            name="BRASS",
            script_filename="run_brass.py",
            task_names=["BRASSDiario"],  # Nombre de la tarea en la BD (como en el script original)
            frequency_days=int(os.getenv('BRASS_FRECUENCIA_DIAS', '1'))
        )
        self.manager = None
    
    def get_task_name(self) -> str:
        """Retorna el nombre de la tarea en la base de datos"""
        return "BRASSDiario"
    
    def is_continuous(self) -> bool:
        """Indica si es una tarea continua"""
        return False
    
    def should_run_today(self, check_date: date = None) -> bool:
        """
        Determina si la tarea debe ejecutarse hoy
        
        Args:
            check_date: Fecha a verificar (por defecto hoy)
            
        Returns:
            True si debe ejecutarse
        """
        return self.debe_ejecutarse()
    
    def execute(self) -> bool:
        """
        Ejecuta la tarea BRASS usando el manager
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            logger.info("Iniciando ejecución de tarea BRASS")
            
            # Crear el manager
            self.manager = BrassManager()
            
            # Ejecutar la tarea
            success = self.manager.run()
            
            if success:
                logger.info("Tarea BRASS ejecutada correctamente")
                # Marcar como completada usando el método de la clase base
                self.marcar_como_completada()
            else:
                logger.error("Error en la ejecución de tarea BRASS")
            
            return success
            
        except Exception as e:
            logger.error(f"Error ejecutando tarea BRASS: {e}")
            return False
    
    def close_connections(self):
        """Cierra las conexiones"""
        super().close_connections()
        if self.manager:
            try:
                self.manager.close_connections()
                self.manager = None
            except Exception as e:
                logger.warning(f"Error cerrando conexiones BRASS: {e}")