"""
Biblioteca común para manejo de bases de datos Access
"""
import pyodbc
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, date

logger = logging.getLogger(__name__)


class AccessDatabase:
    """Clase para manejar conexiones a bases de datos Access"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None
    
    def connect(self) -> pyodbc.Connection:
        """Establece conexión con la base de datos"""
        try:
            self._connection = pyodbc.connect(self.connection_string)
            logger.info("Conexión establecida con la base de datos")
            return self._connection
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            raise
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Conexión cerrada")
    
    @contextmanager
    def get_connection(self):
        """Context manager para manejo seguro de conexiones"""
        connection = None
        try:
            connection = self.connect()
            yield connection
        except Exception as e:
            logger.error(f"Error en conexión: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                self.disconnect()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta una consulta SELECT y retorna los resultados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Obtener nombres de columnas
                columns = [column[0] for column in cursor.description]
                
                # Obtener filas y convertir a diccionarios
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    result.append(dict(zip(columns, row)))
                
                logger.debug(f"Consulta ejecutada: {len(result)} filas retornadas")
                return result
                
            except Exception as e:
                logger.error(f"Error ejecutando consulta: {e}")
                raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta una consulta INSERT, UPDATE o DELETE"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                rows_affected = cursor.rowcount
                logger.debug(f"Consulta ejecutada: {rows_affected} filas afectadas")
                return rows_affected
                
            except Exception as e:
                logger.error(f"Error ejecutando consulta: {e}")
                conn.rollback()
                raise
    
    def get_max_id(self, table: str, id_field: str) -> int:
        """Obtiene el ID máximo de una tabla"""
        query = f"SELECT MAX({id_field}) as MaxID FROM {table}"
        result = self.execute_query(query)
        
        if result and result[0]['MaxID'] is not None:
            return result[0]['MaxID']
        return 0
    
    def insert_record(self, table: str, data: Dict[str, Any]) -> bool:
        """Inserta un registro en la tabla especificada"""
        try:
            fields = list(data.keys())
            placeholders = ['?' for _ in fields]
            values = list(data.values())
            
            query = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            
            self.execute_non_query(query, tuple(values))
            logger.info(f"Registro insertado en {table}")
            return True
            
        except Exception as e:
            logger.error(f"Error insertando registro en {table}: {e}")
            return False
    
    def update_record(self, table: str, data: Dict[str, Any], where_condition: str, where_params: Optional[tuple] = None) -> bool:
        """Actualiza registros en la tabla especificada"""
        try:
            set_clauses = [f"{field} = ?" for field in data.keys()]
            values = list(data.values())
            
            query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {where_condition}"
            
            params = tuple(values)
            if where_params:
                params += where_params
            
            rows_affected = self.execute_non_query(query, params)
            logger.info(f"Actualizado {rows_affected} registros en {table}")
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error actualizando registro en {table}: {e}")
            return False


class DemoDatabase:
    """Clase de demostración que simula una base de datos Access para Docker"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        logger.info("Modo DEMO: Simulando base de datos Access")
        
        # Datos de demo para BRASS
        self.demo_brass_data = {
            'ultima_ejecucion': datetime.now().date(),
            'equipos_descalibrados': []
        }
        
        # Datos de demo para Tareas
        self.demo_tareas_data = {
            'max_id': 1000
        }
    
    def connect(self):
        """Simula conexión exitosa"""
        logger.info("DEMO: Conexión simulada establecida")
        return self
    
    def disconnect(self):
        """Simula desconexión"""
        logger.info("DEMO: Conexión simulada cerrada")
    
    @contextmanager
    def get_connection(self):
        """Context manager simulado"""
        try:
            yield self
        except Exception as e:
            logger.error(f"Error en modo demo: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Simula ejecución de consultas SELECT"""
        logger.info(f"DEMO: Ejecutando consulta simulada: {query[:50]}...")
        
        # Simular consultas específicas de BRASS
        if "ultima_ejecucion" in query.lower():
            return [{'ultima_ejecucion': self.demo_brass_data['ultima_ejecucion']}]
        
        if "equipos" in query.lower() and "calibracion" in query.lower():
            return self.demo_brass_data['equipos_descalibrados']
        
        # Simular consultas de Tareas
        if "max(" in query.lower():
            return [{'MaxID': self.demo_tareas_data['max_id']}]
        
        # Por defecto, retornar lista vacía
        return []
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Simula ejecución de consultas INSERT, UPDATE, DELETE"""
        logger.info(f"DEMO: Ejecutando consulta no-SELECT simulada: {query[:50]}...")
        
        if "insert" in query.lower():
            # Simular inserción exitosa
            if "tareas" in query.lower():
                self.demo_tareas_data['max_id'] += 1
            return 1
        
        if "update" in query.lower():
            # Simular actualización exitosa
            return 1
        
        return 0
    
    def get_max_id(self, table: str, id_field: str) -> int:
        """Simula obtención de ID máximo"""
        logger.info(f"DEMO: Obteniendo ID máximo simulado para {table}.{id_field}")
        return self.demo_tareas_data['max_id']
    
    def insert_record(self, table: str, data: Dict[str, Any]) -> bool:
        """Simula inserción de registro"""
        logger.info(f"DEMO: Insertando registro simulado en {table}")
        if "tareas" in table.lower():
            self.demo_tareas_data['max_id'] += 1
        return True
    
    def update_record(self, table: str, data: Dict[str, Any], where_condition: str, where_params: Optional[tuple] = None) -> bool:
        """Simula actualización de registro"""
        logger.info(f"DEMO: Actualizando registro simulado en {table}")
        return True


def get_database_instance(connection_string: Optional[str]) -> AccessDatabase:
    """Factory function que retorna la instancia apropiada de base de datos"""
    if connection_string is None:
        return DemoDatabase()
    else:
        return AccessDatabase(connection_string)
