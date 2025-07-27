"""Módulo para gestión centralizada de tareas en la tabla TbTareas
"""

from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
import logging

from .database import AccessDatabase
from .config import Config


class TaskManager:
    """
    Gestor centralizado para operaciones con la tabla TbTareas
    """
    
    def __init__(self, config: Config, logger: logging.Logger):
        """
        Inicializa el gestor de tareas
        
        Args:
            config: Configuración de la aplicación
            logger: Logger para registrar eventos
        """
        self.config = config
        self.logger = logger
        self.db_tareas = None
    
    def _get_db_tareas(self) -> AccessDatabase:
        """
        Obtiene la instancia de base de datos de tareas
        
        Returns:
            Instancia de AccessDatabase para tareas
        """
        if self.db_tareas is None:
            self.db_tareas = AccessDatabase(
                self.config.get_db_tareas_connection_string()
            )
            self.db_tareas.connect()
        return self.db_tareas
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.db_tareas:
            try:
                self.db_tareas.disconnect()
            except Exception as e:
                self.logger.error(f"Error cerrando conexión db_tareas: {e}")
            finally:
                self.db_tareas = None
    
    def get_last_execution_date(self, task_name: str) -> Optional[date]:
        """
        Obtiene la fecha de la última ejecución exitosa de una tarea
        
        Args:
            task_name: Nombre de la tarea
            
        Returns:
            Fecha de última ejecución o None si no existe
        """
        try:
            db = self._get_db_tareas()
            query = """
                SELECT MAX(Fecha) as UltimaFecha
                FROM TbTareas 
                WHERE Tarea = ? AND Realizado = 'Sí'
            """
            
            result = db.execute_query(query, (task_name,))
            
            if result and result[0]['UltimaFecha']:
                fecha = result[0]['UltimaFecha']
                if isinstance(fecha, str):
                    return datetime.strptime(fecha, '%Y-%m-%d').date()
                elif isinstance(fecha, datetime):
                    return fecha.date()
                return fecha
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo última ejecución de {task_name}: {e}")
            return None
    
    def is_task_completed_today(self, task_name: str) -> bool:
        """
        Verifica si una tarea se completó hoy
        
        Args:
            task_name: Nombre de la tarea
            
        Returns:
            True si la tarea se completó hoy
        """
        try:
            db = self._get_db_tareas()
            today = date.today()
            
            query = """
                SELECT COUNT(*) as Count
                FROM TbTareas 
                WHERE Tarea = ? AND Fecha = ? AND Realizado = 'Sí'
            """
            
            result = db.execute_query(query, (task_name, today))
            return result and result[0]['Count'] > 0
            
        except Exception as e:
            self.logger.error(f"Error verificando si {task_name} se completó hoy: {e}")
            return False
    
    def register_task_completion(self, task_name: str, execution_date: Optional[date] = None) -> bool:
        """
        Registra la finalización exitosa de una tarea
        
        Args:
            task_name: Nombre de la tarea
            execution_date: Fecha de ejecución (por defecto hoy)
            
        Returns:
            True si se registró correctamente
        """
        try:
            db = self._get_db_tareas()
            exec_date = execution_date or date.today()
            
            # Verificar si ya existe registro para esta fecha
            query_check = """
                SELECT COUNT(*) as Count 
                FROM TbTareas 
                WHERE Tarea = ? AND Fecha = ?
            """
            
            result = db.execute_query(query_check, (task_name, exec_date))
            
            if result and result[0]['Count'] > 0:
                # Actualizar registro existente
                task_data = {
                    "Fecha": exec_date,
                    "Realizado": "Sí"
                }
                success = db.update_record(
                    "TbTareas", 
                    task_data, 
                    "Tarea = ? AND Fecha = ?", 
                    (task_name, exec_date)
                )
            else:
                # Insertar nuevo registro
                task_data = {
                    "Tarea": task_name,
                    "Fecha": exec_date,
                    "Realizado": "Sí"
                }
                success = db.insert_record("TbTareas", task_data)
            
            if success:
                self.logger.info(f"Tarea {task_name} registrada como completada para {exec_date}")
            else:
                self.logger.error(f"Error registrando tarea {task_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error registrando tarea {task_name}: {e}")
            return False
    
    def days_since_last_execution(self, task_name: str) -> Optional[int]:
        """
        Calcula los días transcurridos desde la última ejecución exitosa
        
        Args:
            task_name: Nombre de la tarea
            
        Returns:
            Número de días transcurridos o None si no hay ejecuciones previas
        """
        last_date = self.get_last_execution_date(task_name)
        if last_date is None:
            return None
        
        return (date.today() - last_date).days
    
    def requires_execution(self, task_name: str, frequency_days: int) -> bool:
        """
        Determina si una tarea requiere ejecución basada en su frecuencia
        
        Args:
            task_name: Nombre de la tarea
            frequency_days: Frecuencia en días (1 = diario, 7 = semanal, etc.)
            
        Returns:
            True si la tarea requiere ejecución
        """
        days_since = self.days_since_last_execution(task_name)
        
        # Si nunca se ha ejecutado, requiere ejecución
        if days_since is None:
            return True
        
        # Si han pasado suficientes días según la frecuencia
        return days_since >= frequency_days
    
    def mark_task_failed(self, task_name: str, execution_date: Optional[date] = None) -> bool:
        """
        Marca una tarea como fallida
        
        Args:
            task_name: Nombre de la tarea
            execution_date: Fecha de ejecución (por defecto hoy)
            
        Returns:
            True si se registró correctamente
        """
        try:
            db = self._get_db_tareas()
            exec_date = execution_date or date.today()
            
            # Verificar si ya existe registro para esta fecha
            query_check = """
                SELECT COUNT(*) as Count 
                FROM TbTareas 
                WHERE Tarea = ? AND Fecha = ?
            """
            
            result = db.execute_query(query_check, (task_name, exec_date))
            
            if result and result[0]['Count'] > 0:
                # Actualizar registro existente
                task_data = {
                    "Fecha": exec_date,
                    "Realizado": "No"
                }
                success = db.update_record(
                    "TbTareas", 
                    task_data, 
                    "Tarea = ? AND Fecha = ?", 
                    (task_name, exec_date)
                )
            else:
                # Insertar nuevo registro
                task_data = {
                    "Tarea": task_name,
                    "Fecha": exec_date,
                    "Realizado": "No"
                }
                success = db.insert_record("TbTareas", task_data)
            
            if success:
                self.logger.warning(f"Tarea {task_name} marcada como fallida para {exec_date}")
            else:
                self.logger.error(f"Error marcando tarea {task_name} como fallida")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error marcando tarea {task_name} como fallida: {e}")
            return False
    
    def get_task_history(self, task_name: str, days: int = 30) -> list:
        """
        Obtiene el historial de ejecuciones de una tarea
        
        Args:
            task_name: Nombre de la tarea
            days: Número de días hacia atrás a consultar
            
        Returns:
            Lista de registros de ejecución
        """
        try:
            db = self._get_db_tareas()
            start_date = date.today() - timedelta(days=days)
            
            query = """
                SELECT Fecha, Realizado
                FROM TbTareas 
                WHERE Tarea = ? AND Fecha >= ?
                ORDER BY Fecha DESC
            """
            
            result = db.execute_query(query, (task_name, start_date))
            return result or []
            
        except Exception as e:
            self.logger.error(f"Error obteniendo historial de {task_name}: {e}")
            return []


def create_task_manager(config: Config, logger: logging.Logger) -> TaskManager:
    """
    Función de conveniencia para crear un TaskManager
    
    Args:
        config: Configuración de la aplicación
        logger: Logger para registrar eventos
        
    Returns:
        Instancia de TaskManager
    """
    return TaskManager(config, logger)