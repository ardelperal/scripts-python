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

from .db.access_connection_pool import AccessConnectionPool, get_tareas_connection_pool
from .config import Config
from .db.database import AccessDatabase


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

# ---------------------------------------------------------------------------
# Funciones utilitarias relacionadas con tareas (movidas desde utils.py)
# ---------------------------------------------------------------------------
from datetime import datetime, date
from typing import Optional
import logging as _logging

def register_task_completion(
    db_connection, task_name: str, execution_date: Optional[date] = None
) -> bool:
    """Registra (o actualiza) la ejecución de una tarea en TbTareas.

    Estrategia:
      1. UPDATE si existe
      2. INSERT con columnas estándar; fallback a esquema alternativo si falla
    """
    try:
        if execution_date is None:
            execution_date = date.today()
        select_query = "SELECT * FROM TbTareas WHERE Tarea = ?"
        rows = db_connection.execute_query(select_query, [task_name]) if db_connection else []
        if rows:
            try:
                db_connection.execute_non_query(
                    "UPDATE TbTareas SET Realizado = 'Sí', Fecha = ? WHERE Tarea = ?",
                    [execution_date, task_name],
                )
            except Exception:
                db_connection.execute_non_query(
                    "UPDATE TbTareas SET FechaEjecucion = ? WHERE Tarea = ?",
                    [datetime.now(), task_name],
                )
        else:
            inserted = False
            try:
                db_connection.execute_non_query(
                    "INSERT INTO TbTareas (Tarea, Realizado, Fecha) VALUES (?, 'Sí', ?)",
                    [task_name, execution_date],
                )
                inserted = True
            except Exception:
                try:
                    db_connection.execute_non_query(
                        "INSERT INTO TbTareas (Tarea, FechaEjecucion) VALUES (?, ?)",
                        [task_name, datetime.now()],
                    )
                    inserted = True
                except Exception:
                    inserted = False
            if not inserted:
                return False
        return True
    except Exception as e:  # pragma: no cover - defensivo
        _logging.error(f"Error registrando finalización de tarea {task_name}: {e}")
        return False


def get_last_task_execution_date(db_connection, task_name: str) -> Optional[date]:
    """Obtiene la última fecha de ejecución de una tarea (o None)."""
    try:
        query = """
            SELECT MAX(COALESCE(FechaEjecucion, Fecha)) as UltimaFecha
            FROM TbTareas
            WHERE Tarea = ?
        """
        result = db_connection.execute_query(query, [task_name]) if db_connection else []
        if result and result[0].get("UltimaFecha"):
            fecha = result[0]["UltimaFecha"]
            if isinstance(fecha, datetime):
                return fecha.date()
            return fecha
        return None
    except Exception as e:  # pragma: no cover - defensivo
        _logging.error(
            f"Error obteniendo fecha de última ejecución para {task_name}: {e}"
        )
        return None


def should_execute_task(
    db_connection, task_name: str, frequency_days: int, logger=None
) -> bool:
    """Determina si se debe ejecutar una tarea según frecuencia en días."""
    try:
        last_execution = get_last_task_execution_date(db_connection, task_name)
        if last_execution is None:
            if logger:
                logger.info(
                    f"No hay registro previo de tarea {task_name}, se requiere ejecutar"
                )
            return True
        days_since_last = (date.today() - last_execution).days
        should = days_since_last >= frequency_days
        if logger:
            logger.info(
                f"Última ejecución tarea {task_name}: {last_execution}, días transcurridos: {days_since_last}, requiere: {should}"
            )
        return should
    except Exception as e:  # pragma: no cover - defensivo
        if logger:
            logger.error(f"Error determinando si requiere tarea {task_name}: {e}")
        else:
            _logging.error(f"Error determinando si requiere tarea {task_name}: {e}")
        return True

__all__ = [
    "BaseTask",
    "TareaDiaria",
    "TareaContinua",
    "register_task_completion",
    "get_last_task_execution_date",
    "should_execute_task",
]
