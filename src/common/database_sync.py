"""
Sistema de sincronización bidireccional Access ↔ SQLite
Para mantener coherencia de datos entre oficina y Docker
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import time

logger = logging.getLogger(__name__)

class DatabaseSynchronizer:
    """Sincronizador bidireccional de bases de datos"""
    
    def __init__(self, access_path: Path, sqlite_path: Path, access_password: Optional[str] = None):
        self.access_path = access_path
        self.sqlite_path = sqlite_path
        self.sync_log_path = sqlite_path.parent / f"{sqlite_path.stem}_sync.log"
        self.access_password = access_password
        
    def sync_access_to_sqlite(self, tables: List[str] = None) -> bool:
        """Sincroniza datos desde Access hacia SQLite"""
        if not self.access_path.exists():
            logger.warning(f"Access DB no existe: {self.access_path}")
            return False
        
        try:
            from .database_adapter import AccessAdapter, SQLiteAdapter
            
            with AccessAdapter(self.access_path, self.access_password) as access_db, \
                 SQLiteAdapter(self.sqlite_path) as sqlite_db:
                
                if not tables:
                    tables = access_db.get_tables()
                
                for table in tables:
                    logger.info(f"Sincronizando tabla {table}: Access → SQLite")
                    
                    # Leer datos de Access
                    data = access_db.execute_query(f"SELECT * FROM {table}")
                    
                    if data:
                        # Crear tabla en SQLite si no existe
                        self._create_sqlite_table_from_data(sqlite_db, table, data[0])
                        
                        # Limpiar y insertar datos
                        sqlite_db.execute_non_query(f"DELETE FROM {table}")
                        
                        for row in data:
                            columns = list(row.keys())
                            placeholders = ','.join(['?' for _ in columns])
                            values = list(row.values())
                            
                            insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                            sqlite_db.execute_non_query(insert_sql, tuple(values))
                        
                        logger.info(f"Sincronizados {len(data)} registros en {table}")
            
            self._log_sync("access_to_sqlite", True)
            return True
            
        except Exception as e:
            logger.error(f"Error sincronizando Access → SQLite: {e}")
            self._log_sync("access_to_sqlite", False, str(e))
            return False
    
    def sync_sqlite_to_access(self, tables: List[str] = None, 
                            update_only: bool = True) -> bool:
        """Sincroniza cambios desde SQLite hacia Access"""
        if not self.access_path.exists():
            logger.warning(f"Access DB no existe para sincronizar: {self.access_path}")
            return False
        
        try:
            from .database_adapter import AccessAdapter, SQLiteAdapter
            
            with AccessAdapter(self.access_path, self.access_password) as access_db, \
                 SQLiteAdapter(self.sqlite_path) as sqlite_db:
                
                if not tables:
                    tables = sqlite_db.get_tables()
                
                for table in tables:
                    if update_only:
                        # Solo sincronizar registros modificados
                        self._sync_modified_records(access_db, sqlite_db, table)
                    else:
                        # Sincronización completa
                        logger.info(f"Sincronizando tabla {table}: SQLite → Access")
                        
                        data = sqlite_db.execute_query(f"SELECT * FROM {table}")
                        
                        # Limpiar y recrear en Access
                        access_db.execute_non_query(f"DELETE FROM {table}")
                        
                        for row in data:
                            columns = list(row.keys())
                            placeholders = ','.join(['?' for _ in columns])
                            values = list(row.values())
                            
                            insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                            access_db.execute_non_query(insert_sql, tuple(values))
            
            self._log_sync("sqlite_to_access", True)
            return True
            
        except Exception as e:
            logger.error(f"Error sincronizando SQLite → Access: {e}")
            self._log_sync("sqlite_to_access", False, str(e))
            return False
    
    def _sync_modified_records(self, access_db, sqlite_db, table: str):
        """Sincroniza solo registros que fueron modificados en SQLite"""
        try:
            # Esta lógica depende de tener timestamps o campos de control
            # Por ejemplo, para TbCorreosEnviados:
            
            if table.lower() == 'tbcorreosenviados':
                # Buscar correos que fueron marcados como enviados en SQLite
                sqlite_sent = sqlite_db.execute_query(
                    "SELECT * FROM TbCorreosEnviados WHERE FechaEnvio IS NOT NULL"
                )
                
                for record in sqlite_sent:
                    # Actualizar en Access
                    access_db.execute_non_query(
                        "UPDATE TbCorreosEnviados SET FechaEnvio = ? WHERE IDCorreo = ?",
                        (record['FechaEnvio'], record['IDCorreo'])
                    )
                
                logger.info(f"Actualizados {len(sqlite_sent)} correos enviados en Access")
        
        except Exception as e:
            logger.error(f"Error sincronizando registros modificados en {table}: {e}")
    
    def _create_sqlite_table_from_data(self, sqlite_db, table_name: str, sample_row: Dict[str, Any]):
        """Crea tabla SQLite basada en datos de ejemplo"""
        columns = []
        
        for column, value in sample_row.items():
            if isinstance(value, int):
                col_type = "INTEGER"
            elif isinstance(value, float):
                col_type = "REAL"
            elif isinstance(value, datetime):
                col_type = "DATETIME"
            else:
                col_type = "TEXT"
            
            columns.append(f"{column} {col_type}")
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        sqlite_db.execute_non_query(create_sql)
    
    def _log_sync(self, operation: str, success: bool, error: str = None):
        """Registra operación de sincronización"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'success': success,
            'error': error,
            'access_path': str(self.access_path),
            'sqlite_path': str(self.sqlite_path)
        }
        
        try:
            with open(self.sync_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error escribiendo log de sync: {e}")


class OfflineQueueManager:
    """Gestiona cola de operaciones para sincronizar cuando Access esté disponible"""
    
    def __init__(self, queue_path: Path):
        self.queue_path = queue_path
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
    
    def add_operation(self, table: str, operation: str, data: Dict[str, Any], key_field: str = 'id'):
        """Añade operación a la cola"""
        op = {
            'timestamp': datetime.now().isoformat(),
            'table': table,
            'operation': operation,  # 'insert', 'update', 'delete'
            'data': data,
            'key_field': key_field
        }
        
        try:
            with open(self.queue_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(op) + '\n')
            logger.info(f"Operación añadida a cola: {operation} en {table}")
        except Exception as e:
            logger.error(f"Error añadiendo operación a cola: {e}")
    
    def process_queue(self, access_db) -> int:
        """Procesa todas las operaciones de la cola contra Access"""
        if not self.queue_path.exists():
            return 0
        
        processed = 0
        failed_ops = []
        
        try:
            with open(self.queue_path, 'r', encoding='utf-8') as f:
                operations = [json.loads(line.strip()) for line in f if line.strip()]
            
            for op in operations:
                try:
                    if op['operation'] == 'update':
                        # Construir SQL de actualización
                        set_clause = ', '.join([f"{k} = ?" for k in op['data'].keys() if k != op['key_field']])
                        sql = f"UPDATE {op['table']} SET {set_clause} WHERE {op['key_field']} = ?"
                        
                        values = [v for k, v in op['data'].items() if k != op['key_field']]
                        values.append(op['data'][op['key_field']])
                        
                        access_db.execute_non_query(sql, tuple(values))
                        processed += 1
                        
                    elif op['operation'] == 'insert':
                        columns = list(op['data'].keys())
                        placeholders = ','.join(['?' for _ in columns])
                        sql = f"INSERT INTO {op['table']} ({','.join(columns)}) VALUES ({placeholders})"
                        
                        access_db.execute_non_query(sql, tuple(op['data'].values()))
                        processed += 1
                    
                    logger.debug(f"Operación procesada: {op['operation']} en {op['table']}")
                    
                except Exception as e:
                    logger.error(f"Error procesando operación {op}: {e}")
                    failed_ops.append(op)
            
            # Reescribir archivo solo con operaciones fallidas
            if failed_ops:
                with open(self.queue_path, 'w', encoding='utf-8') as f:
                    for op in failed_ops:
                        f.write(json.dumps(op) + '\n')
            else:
                # Limpiar cola si todo se procesó
                self.queue_path.unlink()
            
            logger.info(f"Cola procesada: {processed} exitosos, {len(failed_ops)} fallidos")
            return processed
            
        except Exception as e:
            logger.error(f"Error procesando cola: {e}")
            return 0


# Funciones de conveniencia
def sync_database_from_access(access_path: Path, sqlite_path: Path, 
                            tables: List[str] = None) -> bool:
    """Sincroniza datos desde Access hacia SQLite"""
    from .config import config
    sync = DatabaseSynchronizer(access_path, sqlite_path, access_password=getattr(config, 'db_password', None))
    return sync.sync_access_to_sqlite(tables)

def sync_database_to_access(sqlite_path: Path, access_path: Path, 
                          tables: List[str] = None) -> bool:
    """Sincroniza cambios desde SQLite hacia Access"""
    from .config import config
    sync = DatabaseSynchronizer(access_path, sqlite_path, access_password=getattr(config, 'db_password', None))
    return sync.sync_sqlite_to_access(tables)
