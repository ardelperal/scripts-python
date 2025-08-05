"""
Tarea de Correo de Tareas
Adaptación del script legacy EnviarCorreoTareas.vbs
"""
import logging
from common.base_task import TareaContinua
from .correo_tareas_manager import CorreoTareasManager

logger = logging.getLogger(__name__)


class CorreoTareasTask(TareaContinua):
    """Tarea continua para envío de correos de tareas"""
    
    def __init__(self):
        super().__init__(
            name="CorreoTareas",
            script_filename="run_correo_tareas.py"
        )
        self.manager = None
    
    def initialize(self):
        """Inicializar el manager de correo de tareas"""
        try:
            logger.info("Inicializando CorreoTareasTask")
            self.manager = CorreoTareasManager()
            logger.info("CorreoTareasTask inicializado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error inicializando CorreoTareasTask: {e}")
            return False
    
    def execute(self) -> bool:
        """
        Ejecutar la tarea de envío de correos de tareas
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            if not self.manager:
                logger.error("Manager no inicializado")
                return False
            
            logger.info("Ejecutando tarea de correo de tareas")
            
            # Ejecutar la tarea continua
            success = self.manager.execute_continuous_task()
            
            if success:
                logger.info("Tarea de correo de tareas completada exitosamente")
                self.mark_as_completed()
            else:
                logger.error("Error ejecutando tarea de correo de tareas")
            
            return success
            
        except Exception as e:
            logger.error(f"Error ejecutando CorreoTareasTask: {e}")
            return False
    
    def close_connections(self):
        """Cerrar conexiones del manager"""
        try:
            if self.manager and hasattr(self.manager, 'db_pool'):
                self.manager.db_pool.close_all_connections()
                logger.info("Conexiones de CorreoTareasTask cerradas")
        except Exception as e:
            logger.error(f"Error cerrando conexiones de CorreoTareasTask: {e}")