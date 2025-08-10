"""
Tarea de Correo Tareas
Adaptación del script original EnviarCorreoTareas.vbs
"""
import logging
from common.base_task import TareaContinua
from .correo_tareas_manager import CorreoTareasManager

logger = logging.getLogger(__name__)


class CorreoTareasTask(TareaContinua):
    """Tarea continua para notificaciones de tareas pendientes."""

    def __init__(self, manager_cls=CorreoTareasManager):
        super().__init__(
            name="CorreoTareas",
            script_filename="run_correo_tareas.py"
        )
        self.manager_cls = manager_cls
        self.manager = None

    def initialize(self):  # pragma: no cover - simple
        try:
            logger.debug("Inicializando CorreoTareasTask")
            self.manager = self.manager_cls()
            return True
        except Exception as e:  # pragma: no cover
            logger.error(f"Error inicializando CorreoTareasTask: {e}")
            return False

    def execute_specific_logic(self) -> bool:
        try:
            if not self.manager:
                self.manager = self.manager_cls()
            enviados = self.manager.process_pending_emails()
            if enviados < 0:
                logger.error("Error ejecutando envío de correos de tareas")
                return False
            return True
        except Exception as e:
            logger.error(f"Error en execute_specific_logic CorreoTareasTask: {e}")
            return False

    def execute(self) -> bool:  # pragma: no cover - alias retrocompatibilidad
        return self.execute_specific_logic()

    def close_connections(self):  # pragma: no cover - defensivo
        try:
            if self.manager and hasattr(self.manager, 'db_pool'):
                try:
                    self.manager.db_pool.close_all_connections()
                except Exception:
                    pass
        finally:
            self.manager = None