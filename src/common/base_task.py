"""
Clases base para el sistema de tareas
Proporciona funcionalidad común para tareas diarias y continuas
"""

import logging
import subprocess
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any

from .access_connection_pool import AccessConnectionPool, get_tareas_connection_pool
from .config import Config
from .database import AccessDatabase
from .utils import register_task_completion, should_execute_task


class BaseTask(ABC):
    """
    Clase base abstracta para todas las tareas del sistema
    """

    def __init__(self, name: str, script_filename: str):
        """
        Inicializa la tarea base

        Args:
            name: Nombre descriptivo de la tarea
            script_filename: Nombre del archivo de script a ejecutar
        """
        self.name = name
        self.script_filename = script_filename
        self.logger = logging.getLogger(f"Task.{name}")

        # Configuración
        self.config = Config()

        # Conexión a base de datos de tareas
        self.db_tareas = None
        self._init_database_connection()

        # Ruta del script
        self.project_root = Path(__file__).parent.parent.parent
        self.scripts_dir = self.project_root / "scripts"
        self.script_path = self.scripts_dir / script_filename

        if not self.script_path.exists():
            raise FileNotFoundError(f"Script no encontrado: {self.script_path}")

    def _init_database_connection(self):
        """Inicializa la conexión a la base de datos de tareas usando pool global."""
        try:
            conn_str = self.config.get_db_tareas_connection_string()
            pool: AccessConnectionPool = get_tareas_connection_pool(conn_str)
            # Crear wrapper AccessDatabase que delega en pool
            self.db_tareas = AccessDatabase(conn_str, pool=pool)
            self.logger.debug(f"Pool de BD tareas inicializado para {self.name}")
        except Exception as e:
            self.logger.error(
                f"Error inicializando pool BD tareas para {self.name}: {e}"
            )
            self.db_tareas = None

    @abstractmethod
    def debe_ejecutarse(self) -> bool:
        """
        Determina si la tarea debe ejecutarse

        Returns:
            True si debe ejecutarse, False en caso contrario
        """
        pass

    def ejecutar(self) -> dict[str, Any]:
        """
        Ejecuta el script asociado a la tarea

        Returns:
            Diccionario con el resultado de la ejecución
        """
        try:
            self.logger.info(f"🚀 Iniciando ejecución de {self.name}")

            # Ejecutar el script
            date.today()
            result = subprocess.run(
                ["python", str(self.script_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutos timeout
            )

            success = result.returncode == 0

            resultado = {
                "success": success,
                "return_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr,
                "duration": 0,  # Se podría calcular si es necesario
            }

            if success:
                self.logger.info(f"✅ {self.name} ejecutado exitosamente")
            else:
                self.logger.error(f"❌ Error en {self.name}: {result.stderr}")

            return resultado

        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ Timeout en {self.name} después de 30 minutos")
            return {
                "success": False,
                "return_code": -1,
                "output": "",
                "error": "Timeout después de 30 minutos",
                "duration": 1800,
            }
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando {self.name}: {e}")
            return {
                "success": False,
                "return_code": -2,
                "output": "",
                "error": str(e),
                "duration": 0,
            }

    @abstractmethod
    def marcar_como_completada(self):
        """
        Marca la tarea como completada
        """
        pass

    def close_connections(self):
        """Cierra las conexiones de la tarea"""
        if hasattr(self, "db_tareas") and self.db_tareas is not None:
            try:  # Con pool no se requiere disconnect; se deja por compatibilidad
                self.db_tareas.disconnect()
            except Exception:
                pass
            finally:
                self.db_tareas = None


class TareaDiaria(BaseTask):
    """
    Clase base para tareas que se ejecutan en días laborables con frecuencia específica
    """

    def __init__(
        self,
        name: str,
        script_filename: str,
        task_names: list[str],
        frequency_days: int = 1,
    ):
        """
        Inicializa una tarea diaria

        Args:
            name: Nombre descriptivo de la tarea
            script_filename: Nombre del archivo de script
            task_names: Lista de nombres de tareas en la BD (puede ser una sola)
            frequency_days: Frecuencia en días para ejecutar la tarea
        """
        super().__init__(name, script_filename)
        self.task_names = task_names if isinstance(task_names, list) else [task_names]
        self.frequency_days = frequency_days

    def __enter__(self):
        """Entrada del context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager - cierra conexiones"""
        self.close_connections()
        return False  # No suprimir excepciones

    def debe_ejecutarse(self) -> bool:
        """
        Verifica si alguna de las tareas asociadas debe ejecutarse
        """
        if not self.db_tareas:
            self.logger.warning(
                f"⚠️  No hay conexión a BD, no se puede verificar {self.name}"
            )
            return False

        try:
            # Verificar si alguna de las tareas debe ejecutarse
            for task_name in self.task_names:
                if should_execute_task(
                    self.db_tareas, task_name, self.frequency_days, self.logger
                ):
                    self.logger.info(f"📅 {task_name} debe ejecutarse")
                    return True

            self.logger.info(f"✅ {self.name} no necesita ejecutarse aún")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error verificando {self.name}: {e}")
            return False

    def marcar_como_completada(self):
        """
        Registra todas las tareas asociadas como completadas
        """
        if not self.db_tareas:
            self.logger.warning(
                f"⚠️  No hay conexión a BD, no se puede registrar {self.name}"
            )
            return

        try:
            for task_name in self.task_names:
                success = register_task_completion(self.db_tareas, task_name)
                if success:
                    self.logger.info(f"✅ Tarea {task_name} registrada como completada")
                else:
                    self.logger.error(f"❌ Error registrando tarea {task_name}")
        except Exception as e:
            self.logger.error(f"❌ Error registrando finalización de {self.name}: {e}")


class TareaContinua(BaseTask):
    """
    Clase base para tareas que se ejecutan continuamente (correos, notificaciones)
    """

    def __init__(self, name: str, script_filename: str):
        """
        Inicializa una tarea continua

        Args:
            name: Nombre descriptivo de la tarea
            script_filename: Nombre del archivo de script
        """
        super().__init__(name, script_filename)

    def debe_ejecutarse(self) -> bool:
        """
        Las tareas continuas siempre se ejecutan
        """
        return True

    def marcar_como_completada(self):
        """
        Las tareas continuas no se marcan como completadas
        porque deben ejecutarse en cada ciclo
        """
        pass
