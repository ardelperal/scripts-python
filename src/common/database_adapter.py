"""
Adaptador de base de datos transparente para Access/SQLite
Permite usar la misma interfaz independientemente del tipo de base de datos
"""
import sqlite3
import pyodbc
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseAdapterInterface:
    """Interfaz base para adaptadores de base de datos"""
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta consulta INSERT, UPDATE, DELETE en SQLite"""
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Error ejecutando non-query SQLite: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Alias para execute_non_query para compatibilidad"""
        return self.execute_non_query(query, params)
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import os
from .config import Config

logger = logging.getLogger(__name__)

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logger.debug("pyodbc no disponible - funcionando solo con SQLite")


class DatabaseAdapter(ABC):
    """Interfaz abstracta para adaptadores de base de datos"""
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta una consulta y retorna resultados"""
        pass
    
    @abstractmethod
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta una consulta sin retorno (INSERT, UPDATE, DELETE)"""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[str]:
        """Obtiene lista de tablas disponibles"""
        pass
    
    @abstractmethod
    def close(self):
        """Cierra la conexión"""
        pass


class AccessAdapter(DatabaseAdapter):
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
            logger.info(f"Conectado a Access: {self.db_path}")
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


class SQLiteAdapter(DatabaseAdapter):
    """Adaptador para bases de datos SQLite"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establece conexión con SQLite"""
        try:
            # Crear directorio si no existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            logger.info(f"Conectado a SQLite: {self.db_path}")
        except Exception as e:
            logger.error(f"Error conectando a SQLite {self.db_path}: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta consulta SELECT en SQLite"""
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Convertir Row objects a diccionarios
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando consulta SQLite: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta consulta de modificación en SQLite"""
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Error ejecutando non-query SQLite: {e}")
            raise
    
    def get_tables(self) -> List[str]:
        """Obtiene lista de tablas en SQLite"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        except Exception as e:
            logger.error(f"Error obteniendo tablas SQLite: {e}")
            return []
    
    def close(self):
        """Cierra conexión SQLite"""
        if self.connection:
            self.connection.close()
            logger.debug(f"Conexión SQLite cerrada: {self.db_path}")

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DatabaseAdapterFactory:
    """Factory para crear adaptadores de base de datos apropiados"""
    
    @staticmethod
    def create_adapter(db_path: Union[str, Path], force_type: Optional[str] = None) -> DatabaseAdapter:
        """
        Crea adaptador apropiado basado en el archivo y entorno
        
        Args:
            db_path: Ruta a la base de datos
            force_type: Forzar tipo específico ('access', 'sqlite')
            
        Returns:
            DatabaseAdapter apropiado
        """
        db_path = Path(db_path)
        
        # Si se fuerza un tipo específico
        if force_type == 'sqlite':
            return SQLiteAdapter(db_path)
        elif force_type == 'access':
            return AccessAdapter(db_path)
        
        # Auto-detección basada en extensión y disponibilidad
        if db_path.suffix.lower() in ['.accdb', '.mdb']:
            # Archivo Access - preferir SQLite en containers
            sqlite_path = db_path.with_suffix('.sqlite')
            if sqlite_path.exists():
                logger.info(f"Usando SQLite migrado: {sqlite_path}")
                return SQLiteAdapter(sqlite_path)
            elif PYODBC_AVAILABLE and os.name == 'nt' and not Config().is_docker:
                # Windows local con pyodbc - usar Access directamente
                return AccessAdapter(db_path)
            else:
                    raise FileNotFoundError(
                        f"Base de datos Access {db_path} no puede abrirse en este entorno. "
                        f"SQLite migrado {sqlite_path} no encontrado."
                    )
        
        elif db_path.suffix.lower() in ['.sqlite', '.db']:
            # Archivo SQLite
            return SQLiteAdapter(db_path)
        
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_path}")


class UnifiedDatabase:
    """
    Interfaz unificada que maneja automáticamente Access o SQLite
    según el entorno y disponibilidad
    """
    
    def __init__(self, db_identifier: str, base_path: Optional[Path] = None):
        """
        Inicializa base de datos unificada
        
        Args:
            db_identifier: Nombre base de la BD (ej: 'Tareas_datos1')
            base_path: Directorio base donde buscar archivos
        """
        self.db_identifier = db_identifier
        self.base_path = base_path or Path(".")
        self.adapter = None
        
        self._initialize_adapter()
    
    def _initialize_adapter(self):
        """Inicializa el adaptador apropiado"""
        try:
            # Buscar archivo Access primero
            access_path = self.base_path / f"{self.db_identifier}.accdb"
            
            if access_path.exists():
                self.adapter = DatabaseAdapterFactory.create_adapter(access_path)
                logger.info(f"Usando base de datos: {access_path}")
            else:
                # Buscar SQLite como alternativa
                sqlite_path = self.base_path / f"{self.db_identifier}.sqlite"
                if sqlite_path.exists():
                    self.adapter = DatabaseAdapterFactory.create_adapter(sqlite_path)
                    logger.info(f"Usando base de datos SQLite: {sqlite_path}")
                else:
                    raise FileNotFoundError(
                        f"No se encontró base de datos para '{self.db_identifier}' "
                        f"en {self.base_path}"
                    )
                    
        except Exception as e:
            logger.error(f"Error inicializando base de datos {self.db_identifier}: {e}")
            raise
    
    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta consulta SELECT"""
        return self.adapter.execute_query(sql, params)
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        """Ejecuta consulta de modificación"""
        return self.adapter.execute_non_query(sql, params)
    
    def get_tables(self) -> List[str]:
        """Obtiene lista de tablas"""
        return self.adapter.get_tables()
    
    def close(self):
        """Cierra conexión"""
        if self.adapter:
            self.adapter.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo con base de datos unificada
    try:
        with UnifiedDatabase("Tareas_datos1", Path("dbs-locales")) as db:
            tables = db.get_tables()
            print(f"📊 Tablas disponibles: {tables}")
            
            if tables:
                # Ejemplo de consulta
                results = db.query(f"SELECT * FROM {tables[0]} LIMIT 5")
                print(f"🔍 Primeras 5 filas de {tables[0]}: {len(results)} registros")
                
    except Exception as e:
        print(f"❌ Error: {e}")
