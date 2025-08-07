"""
Tarea de Correos
Adaptación del script original EnviarCorreoNoEnviado.vbs
"""
import logging
from common.base_task import TareaContinua
from .correos_manager import CorreosManager

logger = logging.getLogger(__name__)


class CorreosTask(TareaContinua):
    """Tarea continua para envío de correos pendientes"""
    
    def __init__(self):
        super().__init__(
            name="Correos",
            script_filename="run_correos.py"
        )
        self.manager = None
    
    def initialize(self):
        """Inicializar el manager de correos"""
        try:
            logger.info("Inicializando CorreosTask")
            self.manager = CorreosManager()
            logger.info("CorreosTask inicializado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error inicializando CorreosTask: {e}")
            return False
    
    def execute(self) -> bool:
        """
        Ejecutar la tarea de envío de correos
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            if not self.manager:
                logger.error("Manager no inicializado")
                return False
            
            logger.info("Ejecutando tarea de correos")
            
            # Ejecutar la tarea diaria
            success = self.manager.execute_daily_task()
            
            if success:
                logger.info("Tarea de correos completada exitosamente")
                self.mark_as_completed()
            else:
                logger.error("Error ejecutando tarea de correos")
            
            return success
            
        except Exception as e:
            logger.error(f"Error ejecutando CorreosTask: {e}")
            return False
    
    def close_connections(self):
        """Cerrar conexiones del manager"""
        try:
            if self.manager and hasattr(self.manager, 'db_conn'):
                self.manager.db_conn.disconnect()
                logger.info("Conexiones de CorreosTask cerradas")
        except Exception as e:
            logger.error(f"Error cerrando conexiones de CorreosTask: {e}")