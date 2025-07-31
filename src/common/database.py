"""
Biblioteca común para manejo de bases de datos Access
Integrado con el sistema de adaptadores transparente
"""
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, date

# Importar adaptadores
from .database_adapter import AccessAdapter
from .utils import hide_password_in_connection_string

logger = logging.getLogger(__name__)

# Mantener compatibilidad hacia atrás para imports existentes
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logger.error("pyodbc no disponible - requerido para conexiones Access")


class AccessDatabase:
    """
    Clase mejorada para manejar bases de datos con adaptadores transparentes
    Mantiene compatibilidad hacia atrás pero usa el nuevo sistema internamente
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None
    
    def connect(self):
        """Establece conexión con Access usando pyodbc"""
        try:
            if not PYODBC_AVAILABLE:
                raise ImportError("pyodbc es requerido para conexiones Access")
            
            self._connection = pyodbc.connect(self.connection_string)
            # Usar función para ocultar contraseña en logs
            safe_conn_str = hide_password_in_connection_string(self.connection_string)
            logger.info(f"Conexión establecida con Access: {safe_conn_str}")
            return self._connection
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            raise
    
    def disconnect(self):
        """Cierra la conexión"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Conexión cerrada")
    
    def get_connection(self):
        """Context manager para manejo seguro de conexiones"""
        class ConnectionManager:
            def __init__(self, access_db):
                self.access_db = access_db
                self.connection = None
            
            def __enter__(self):
                self.connection = self.access_db.connect()
                return self.connection
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    logger.error(f"Error en conexión: {exc_val}")
                self.access_db.disconnect()
        
        return ConnectionManager(self)
    
    def get_cursor(self):
        """Obtiene un cursor para ejecutar consultas directamente"""
        if not self._connection:
            self.connect()
        return self._connection.cursor()
    
    def get_cursor(self):
        """Simula obtención de cursor"""
        class DemoCursor:
            def __init__(self, demo_db):
                self.demo_db = demo_db
                self.description = None
                
            def execute(self, query, params=None):
                """Simula ejecución de consulta"""
                logger.info(f"DEMO: Cursor ejecutando: {query[:50]}...")
                # Simular descripción de columnas
                if "expediente" in query.lower():
                    self.description = [
                        ('Expediente',), ('FechaFinalizacion',), ('Estado',), 
                        ('Responsable',), ('Descripcion',)
                    ]
                elif "hito" in query.lower():
                    self.description = [
                        ('IdHito',), ('Expediente',), ('Descripcion',), 
                        ('FechaLimite',), ('Estado',), ('Responsable',)
                    ]
                elif "tsol" in query.lower() or "cods4h" in query.lower():
                    self.description = [
                        ('Expediente',), ('FechaAdjudicacion',), ('Importe',), 
                        ('Proveedor',), ('Estado',)
                    ]
                elif "oferta" in query.lower():
                    self.description = [
                        ('Expediente',), ('FechaInicioOferta',), ('Estado',), 
                        ('Responsable',), ('Descripcion',)
                    ]
                    
            def fetchall(self):
                """Simula obtención de todos los resultados"""
                # Retornar datos de prueba vacíos por defecto
                return []
                
        return DemoCursor(self)
    
    def get_cursor(self):
        """Obtiene un cursor para ejecución directa de consultas"""
        if not self._connection:
            self.connect()
        return self._connection.cursor()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta una consulta SELECT usando pyodbc"""
        if not self._connection:
            self.connect()
        
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Convertir resultados a lista de diccionarios
            columns = [column[0] for column in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            logger.debug(f"Consulta ejecutada: {len(result)} filas retornadas")
            return result
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta una consulta INSERT, UPDATE o DELETE usando pyodbc"""
        if not self._connection:
            self.connect()
        
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows_affected = cursor.rowcount
            self._connection.commit()
            
            logger.debug(f"Consulta ejecutada: {rows_affected} filas afectadas")
            return rows_affected
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
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
    
    def get_connection(self):
        """Context manager simulado"""
        class DemoConnectionManager:
            def __init__(self, demo_db):
                self.demo_db = demo_db
            
            def __enter__(self):
                return self.demo_db
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    logger.error(f"Error en modo demo: {exc_val}")
        
        return DemoConnectionManager(self)
    
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


def get_database_instance(connection_string: Optional[str] = None):
    """
    Factory function que retorna la instancia apropiada de base de datos
    
    Args:
        connection_string: Cadena de conexión para Access
        
    Returns:
        Instancia de base de datos apropiada
    """
    # Modo demo cuando no hay connection string
    if connection_string is None:
        return DemoDatabase()
    
    # Modo Access con connection string
    return AccessDatabase(connection_string)
