"""
Tarea de No Conformidades
Implementa la tarea diaria para gestión de no conformidades y ARAPs
"""
import logging
import os

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in os.sys.path:
    os.sys.path.insert(0, src_dir)

from common.base_task import TareaDiaria
from no_conformidades.no_conformidades_manager import NoConformidadesManager

logger = logging.getLogger(__name__)


class NoConformidadesTask(TareaDiaria):
    """
    Tarea para la gestión de No Conformidades y ARAPs
    """
    
    def __init__(self):
        super().__init__(
            name="NoConformidades",
            script_filename="run_no_conformidades.py",
            task_names=["NCTecnico", "NCCalidad"],
            frequency_days=int(os.getenv('NC_FRECUENCIA_DIAS', '1'))
        )
        self.manager = None
    
    def execute(self) -> bool:
        """
        Ejecuta la tarea de No Conformidades
        """
        try:
            self.logger.info("Iniciando ejecución de tarea No Conformidades")
            
            # Crear el manager
            self.manager = NoConformidadesManager()
            
            # Ejecutar la tarea
            success = self.manager.run()
            
            if success:
                self.logger.info("Tarea No Conformidades completada exitosamente")
            else:
                self.logger.error("Error en la ejecución de la tarea No Conformidades")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea No Conformidades: {e}")
            return False
        finally:
            # Cerrar conexiones
            if self.manager:
                try:
                    self.manager.close_connections()
                except Exception as e:
                    self.logger.warning(f"Error cerrando conexiones: {e}")
    
    def close_connections(self):
        """
        Cierra las conexiones de la tarea
        """
        super().close_connections()
        if self.manager:
            try:
                self.manager.close_connections()
            except Exception as e:
                self.logger.warning(f"Error cerrando conexiones del manager: {e}")