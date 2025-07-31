"""
Adaptador de base de datos para Microsoft Access
Simplificado para trabajar únicamente con Access en Windows
"""
import pyodbc
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from .utils import hide_password_in_connection_string

logger = logging.getLogger(__name__)

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logger.error("pyodbc no está disponible - requerido para conexiones Access")
    raise ImportError("pyodbc es requerido para trabajar con bases de datos Access")


class AccessAdapter:
    """Adaptador para bases de datos Microsoft Access"""
    
    def __init__(self, db_path: Path, password: str = None):
        if not PYODBC_AVAILABLE:
            raise ImportError("pyodbc no está disponible para conexiones Access")
        
        if not db_path.exists():
            raise FileNotFoundError(f"Base de datos Access no encontrada: {db_path}")
        
        self.db_path = db_path
        self.password = password
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establece conexión con Access"""
        try:
            conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_path};"
            if self.password:
                conn_str += f"PWD={self.password};"
            self.connection = pyodbc.connect(conn_str)
            # Usar función para ocultar contraseña en logs
            safe_conn_str = hide_password_in_connection_string(conn_str)
            logger.info(f"Conectado a Access: {safe_conn_str}")
        except Exception as e:
            logger.error(f"Error conectando a Access {self.db_path}: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta consulta SELECT en Access"""
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Obtener nombres de columnas
            columns = [column[0] for column in cursor.description]
            
            # Convertir filas a diccionarios
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando consulta Access: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta consulta de modificación en Access"""
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Error ejecutando non-query Access: {e}")
            raise
    
    def get_tables(self) -> List[str]:
        """Obtiene lista de tablas en Access"""
        try:
            cursor = self.connection.cursor()
            tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
            return tables
        except Exception as e:
            logger.error(f"Error obteniendo tablas Access: {e}")
            return []
    
    def close(self):
        """Cierra conexión Access"""
        if self.connection:
            self.connection.close()
            logger.debug(f"Conexión Access cerrada: {self.db_path}")

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo con base de datos Access
    try:
        db_path = Path("dbs-locales/Tareas_datos1.accdb")
        with AccessAdapter(db_path) as db:
            tables = db.get_tables()
            logger.info(f"Tablas disponibles: {tables}")
            
            if tables:
                # Ejemplo de consulta
                results = db.execute_query(f"SELECT TOP 5 * FROM {tables[0]}")
                logger.info(f"Primeras 5 filas de {tables[0]}: {len(results)} registros")
                
    except Exception as e:
        logger.error(f"Error en ejemplo: {e}")
