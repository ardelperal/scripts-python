"""Abstracción unificada para acceso a Microsoft Access.

Refactor:
 - Se elimina `database_adapter.py` (AccessAdapter) y `DemoDatabase`.
 - `AccessDatabase` se convierte en la única interfaz pública.
 - Internamente usa siempre (si disponible) un `AccessConnectionPool` para operaciones
     thread-safe; si no se pasa pool, mantiene modo legacy de conexión única.
 - Para tests se recomienda usar mocks sobre `AccessDatabase`.
"""
import logging
from typing import Optional, List, Dict, Any

from .utils import hide_password_in_connection_string
from .access_connection_pool import AccessConnectionPool

logger = logging.getLogger(__name__)

# Mantener compatibilidad hacia atrás para imports existentes
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logger.error("pyodbc no disponible - requerido para conexiones Access")


class AccessDatabase:
    """Interfaz principal para ejecutar operaciones sobre Access.

    Diseño:
        - Si se provee un `AccessConnectionPool` se usarán conexiones del pool.
        - Si no, se abre una conexión única (modo legacy) bajo demanda.
    """

    def __init__(self, connection_string: str, pool: Optional[AccessConnectionPool] = None):
        self.connection_string = connection_string
        self.pool = pool
        self._connection = None  # solo en modo legacy
    
    def connect(self):
        """Establece conexión legacy si no hay pool. Con pool, se obtiene conexión temporal."""
        if self.pool:
            # Para compatibilidad, devolvemos un objeto conexión del pool (context-managed en uso real)
            if not PYODBC_AVAILABLE:
                raise ImportError("pyodbc es requerido para conexiones Access")
            # No almacenamos; cada operación debe pedir su propia conexión via pool
            safe_conn_str = hide_password_in_connection_string(self.connection_string)
            logger.debug(f"AccessDatabase (pool) usando connection string: {safe_conn_str}")
            return None
        try:
            if not PYODBC_AVAILABLE:
                raise ImportError("pyodbc es requerido para conexiones Access")
            self._connection = pyodbc.connect(self.connection_string)
            safe_conn_str = hide_password_in_connection_string(self.connection_string)
            logger.info(f"Conexión establecida con Access: {safe_conn_str}")
            return self._connection
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            raise
    
    def disconnect(self):
        """Cierra la conexión legacy. Con pool no hace nada (pool maneja)."""
        if self.pool:
            return
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Conexión cerrada")
    
    def get_connection(self):
        """Context manager compatible.

        - Sin pool: abre/cierra conexión única.
        - Con pool: obtiene conexión del pool y la devuelve automáticamente.
        """
        if not self.pool:
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
        else:
            # Reutilizar get_connection del pool directamente
            return self.pool.get_connection()
    
    def get_cursor(self):  # pragma: no cover - legacy
        if self.pool:
            raise RuntimeError("get_cursor() no soportado directamente cuando se usa pool")
        if not self._connection:
            self.connect()
        return self._connection.cursor()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        if self.pool:
            return self.pool.execute_query(query, params)
        if not self._connection:
            self.connect()
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        if self.pool:
            return self.pool.execute_non_query(query, params)
        if not self._connection:
            self.connect()
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.rowcount
            self._connection.commit()
            return rows
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            raise
    
    def get_max_id(self, table: str, id_field: str) -> int:
        if self.pool:
            return self.pool.get_max_id(table, id_field)
        query = f"SELECT MAX({id_field}) as MaxID FROM {table}"
        result = self.execute_query(query)
        if result and result[0].get('MaxID') is not None:
            return result[0]['MaxID']
        return 0
    
    def insert_record(self, table: str, data: Dict[str, Any]) -> bool:
        if self.pool:
            return self.pool.insert_record(table, data)
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
    
    def update_record(self, table: str, data: Dict[str, Any], where_condition: str, where_params: Optional[List] = None) -> bool:
        if self.pool:
            return self.pool.update_record(table, data, where_condition, where_params)
        try:
            set_clauses = [f"{field} = ?" for field in data.keys()]
            values = list(data.values())
            query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {where_condition}"
            params = tuple(values)
            if where_params:
                params = params + tuple(where_params)
            rows_affected = self.execute_non_query(query, params)
            logger.info(f"Actualizado {rows_affected} registros en {table}")
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error actualizando registro en {table}: {e}")
            return False


__all__ = ["AccessDatabase"]
