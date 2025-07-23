"""
Biblioteca común para manejo de bases de datos Access y SQLite
Integrado con el sistema de adaptadores transparente
"""
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, date

# Importar adaptadores
from .database_adapter import UnifiedDatabase, DatabaseAdapterFactory

logger = logging.getLogger(__name__)

# Mantener compatibilidad hacia atrás para imports existentes
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logger.info("pyodbc no disponible - usando solo SQLite")


class AccessDatabase:
    """
    Clase mejorada para manejar bases de datos con adaptadores transparentes
    Mantiene compatibilidad hacia atrás pero usa el nuevo sistema internamente
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._unified_db = None
        self._parse_connection_string()
    
    def _parse_connection_string(self):
        """Extrae información de la cadena de conexión para crear UnifiedDatabase"""
        # Extraer ruta de la BD de la connection string
        # Formato típico: "Driver={...};DBQ=C:\path\to\db.accdb;"
        if "DBQ=" in self.connection_string:
            db_path = self.connection_string.split("DBQ=")[1].split(";")[0]
            self.db_path = Path(db_path)
            
            # Obtener identificador base (nombre sin extensión)
            self.db_identifier = self.db_path.stem
            self.base_path = self.db_path.parent
        else:
            raise ValueError(f"No se pudo extraer ruta de DB de: {self.connection_string}")
    
    def connect(self):
        """Establece conexión usando el sistema unificado"""
        try:
            self._unified_db = UnifiedDatabase(self.db_identifier, self.base_path)
            logger.info(f"Conexión establecida con {self.db_identifier}")
            return self
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            raise
    
    def disconnect(self):
        """Cierra la conexión"""
        if self._unified_db:
            self._unified_db.close()
            self._unified_db = None
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
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta una consulta SELECT usando el adaptador unificado"""
        if not self._unified_db:
            self.connect()
        
        try:
            result = self._unified_db.query(query, params)
            logger.debug(f"Consulta ejecutada: {len(result)} filas retornadas")
            return result
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta una consulta INSERT, UPDATE o DELETE usando el adaptador unificado"""
        if not self._unified_db:
            self.connect()
        
        try:
            rows_affected = self._unified_db.execute(query, params)
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


def get_database_instance(connection_string: Optional[str] = None, db_identifier: Optional[str] = None, base_path: Optional[Path] = None):
    """
    Factory function mejorado que retorna la instancia apropiada de base de datos
    
    Args:
        connection_string: Cadena de conexión tradicional (compatibilidad hacia atrás)
        db_identifier: Identificador de BD para el sistema unificado
        base_path: Directorio base donde buscar archivos de BD
        
    Returns:
        Instancia de base de datos apropiada
    """
    # Modo demo cuando no hay parámetros
    if connection_string is None and db_identifier is None:
        return DemoDatabase()
    
    # Modo tradicional con connection string
    if connection_string:
        return AccessDatabase(connection_string)
    
    # Modo unificado directo
    if db_identifier:
        class UnifiedDatabaseWrapper:
            """Wrapper para mantener compatibilidad de interfaz"""
            def __init__(self, db_id, base_path):
                self._unified_db = UnifiedDatabase(db_id, base_path)
            
            def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
                return self._unified_db.query(query, params)
            
            def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
                return self._unified_db.execute(query, params)
            
            def get_max_id(self, table: str, id_field: str) -> int:
                result = self._unified_db.query(f"SELECT MAX({id_field}) as max_id FROM {table}")
                return result[0]['max_id'] if result and result[0]['max_id'] else 0
            
            def disconnect(self):
                self._unified_db.close()
        
        return UnifiedDatabaseWrapper(db_identifier, base_path or Path("."))
    
    # Fallback a modo demo
    return DemoDatabase()


# Función de conveniencia para migración automática
def ensure_database_available(db_identifier: str, base_path: Path) -> bool:
    """
    Asegura que la base de datos esté disponible, migrando de Access a SQLite si es necesario
    
    Args:
        db_identifier: Nombre base de la BD
        base_path: Directorio donde buscar archivos
        
    Returns:
        True si la BD está disponible
    """
    from .access_migrator import AccessToSQLiteMigrator
    
    access_file = base_path / f"{db_identifier}.accdb"
    sqlite_file = base_path / f"{db_identifier}.sqlite"
    
    # Si existe Access y estamos en entorno compatible, usar directamente
    if access_file.exists() and PYODBC_AVAILABLE:
        return True
    
    # Si existe SQLite, usar ese
    if sqlite_file.exists():
        return True
    
    # Si existe Access pero no pyodbc, migrar a SQLite
    if access_file.exists():
        logger.info(f"Migrando {access_file} a SQLite para compatibilidad...")
        migrator = AccessToSQLiteMigrator()
        return migrator.migrate_database(access_file, sqlite_file)
    
    logger.warning(f"No se encontró base de datos para {db_identifier} en {base_path}")
    return False
