"""
Sincronizador bidireccional: Access ↔ SQLite con Access como fuente de verdad

- Access = Fuente de verdad para datos maestros (nuevos registros)
- SQLite = Puede hacer cambios de estado (ej: marcar correo como enviado)
- Sincronización bidireccional para evitar ciclos infinitos
"""
import logging
import sqlite3
import pyodbc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import os
import hashlib
import json

logger = logging.getLogger(__name__)

class BidirectionalSync:
    """Sincronizador bidireccional que mantiene coherencia entre Access y SQLite"""
    
    def __init__(self, config):
        self.config = config
        self.sync_rules = {
            'correos_datos': {
                'access_path': config.db_correos_path.with_suffix('.accdb'),
                'sqlite_path': config.db_correos_path.with_suffix('.sqlite'),
                'tables': {
                    'TbCorreosEnviados': {
                        'primary_key': 'IDCorreo',
                        'timestamp_fields': ['FechaCreacion', 'FechaEnvio'],
                        'master_source': 'access',  # Access crea nuevos registros
                        'update_fields': ['FechaEnvio']  # SQLite puede actualizar estos campos
                    }
                }
            },
            'brass_datos': {
                'access_path': config.db_brass_path.with_suffix('.accdb'), 
                'sqlite_path': config.db_brass_path.with_suffix('.sqlite'),
                'tables': {
                    'equipos': {
                        'primary_key': 'id',
                        'timestamp_fields': ['fecha_ultima_calibracion'],
                        'master_source': 'access',
                        'update_fields': ['fecha_ultima_calibracion', 'estado']
                    }
                }
            },
            'tareas_datos': {
                'access_path': config.db_tareas_path.with_suffix('.accdb'),
                'sqlite_path': config.db_tareas_path.with_suffix('.sqlite'),
                'tables': {
                    'tareas': {
                        'primary_key': 'id', 
                        'timestamp_fields': ['fecha_creacion', 'fecha_completado'],
                        'master_source': 'access',
                        'update_fields': ['estado', 'fecha_completado']
                    }
                }
            }
        }
    
    def sync_all_databases(self) -> Dict[str, Dict[str, Any]]:
        """
        Sincroniza todas las bases de datos de forma bidireccional
        Retorna estado detallado de cada sincronización
        """
        results = {}
        
        logger.info("🔄 Iniciando sincronización bidireccional: Access ↔ SQLite")
        
        for db_name, db_config in self.sync_rules.items():
            try:
                if self._access_file_exists(db_config['access_path']):
                    result = self._sync_database_bidirectional(db_name, db_config)
                    results[db_name] = result
                    
                    if result['success']:
                        logger.info(f"✅ {db_name}: Sincronización exitosa")
                        logger.info(f"   📥 Access → SQLite: {result['access_to_sqlite']['affected_rows']} filas")
                        logger.info(f"   📤 SQLite → Access: {result['sqlite_to_access']['affected_rows']} filas")
                    else:
                        logger.error(f"❌ {db_name}: Error en sincronización")
                else:
                    logger.warning(f"⚠️  {db_name}: Archivo Access no encontrado: {db_config['access_path']}")
                    results[db_name] = {'success': False, 'error': 'Access file not found'}
                    
            except Exception as e:
                logger.error(f"❌ {db_name}: Error general: {e}")
                results[db_name] = {'success': False, 'error': str(e)}
        
        return results
    
    def _access_file_exists(self, access_path: Path) -> bool:
        """Verifica si el archivo Access existe y es accesible"""
        return access_path.exists() and access_path.is_file()
    
    def _sync_database_bidirectional(self, db_name: str, db_config: Dict) -> Dict[str, Any]:
        """
        Sincroniza una base de datos de forma bidireccional
        
        Proceso:
        1. Obtener datos de ambas fuentes
        2. Detectar diferencias
        3. Aplicar cambios según reglas definidas
        4. Evitar sobrescribir cambios locales importantes
        """
        result = {
            'success': False,
            'access_to_sqlite': {'affected_rows': 0, 'operations': []},
            'sqlite_to_access': {'affected_rows': 0, 'operations': []},
            'conflicts': [],
            'error': None
        }
        
        try:
            logger.info(f"🔄 Sincronización bidireccional: {db_name}")
            
            # Conectar a ambas bases
            access_conn = self._connect_access(db_config['access_path'])
            if not access_conn:
                result['error'] = 'Cannot connect to Access'
                return result
            
            sqlite_conn = self._connect_sqlite(db_config['sqlite_path'])
            
            # Procesar cada tabla según sus reglas
            for table_name, table_rules in db_config['tables'].items():
                logger.info(f"  📋 Procesando tabla: {table_name}")
                
                # Obtener datos de ambas fuentes
                access_data = self._get_table_data(access_conn, table_name, 'access')
                sqlite_data = self._get_table_data(sqlite_conn, table_name, 'sqlite')
                
                # Sincronizar según reglas
                sync_result = self._sync_table_bidirectional(
                    access_conn, sqlite_conn, table_name, table_rules,
                    access_data, sqlite_data
                )
                
                # Acumular resultados
                result['access_to_sqlite']['affected_rows'] += sync_result['access_to_sqlite']['affected_rows']
                result['sqlite_to_access']['affected_rows'] += sync_result['sqlite_to_access']['affected_rows']
                result['access_to_sqlite']['operations'].extend(sync_result['access_to_sqlite']['operations'])
                result['sqlite_to_access']['operations'].extend(sync_result['sqlite_to_access']['operations'])
                result['conflicts'].extend(sync_result['conflicts'])
            
            # Guardar metadatos
            self._save_sync_metadata(sqlite_conn, db_name, 'BIDIRECTIONAL')
            
            access_conn.close()
            sqlite_conn.close()
            
            result['success'] = True
            logger.info(f"✅ {db_name}: Sincronización bidireccional completada")
            
        except Exception as e:
            logger.error(f"Error en sincronización bidireccional {db_name}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _sync_table_bidirectional(self, access_conn, sqlite_conn, table_name: str, 
                                 table_rules: Dict, access_data: List[Dict], 
                                 sqlite_data: List[Dict]) -> Dict[str, Any]:
        """
        Sincroniza una tabla específica de forma bidireccional
        """
        result = {
            'access_to_sqlite': {'affected_rows': 0, 'operations': []},
            'sqlite_to_access': {'affected_rows': 0, 'operations': []},
            'conflicts': []
        }
        
        primary_key = table_rules['primary_key']
        update_fields = table_rules.get('update_fields', [])
        
        # Crear diccionarios indexados por clave primaria
        access_dict = {row[primary_key]: row for row in access_data}
        sqlite_dict = {row[primary_key]: row for row in sqlite_data}
        
        all_keys = set(access_dict.keys()) | set(sqlite_dict.keys())
        
        for key in all_keys:
            access_row = access_dict.get(key)
            sqlite_row = sqlite_dict.get(key)
            
            if access_row and not sqlite_row:
                # Registro existe solo en Access → Crear en SQLite
                self._insert_row_sqlite(sqlite_conn, table_name, access_row)
                result['access_to_sqlite']['affected_rows'] += 1
                result['access_to_sqlite']['operations'].append(f"INSERT {key}")
                
            elif sqlite_row and not access_row:
                # Registro existe solo en SQLite → Crear en Access (si es permitido)
                if table_rules.get('master_source') != 'access':
                    self._insert_row_access(access_conn, table_name, sqlite_row)
                    result['sqlite_to_access']['affected_rows'] += 1
                    result['sqlite_to_access']['operations'].append(f"INSERT {key}")
                else:
                    # SQLite tiene registro que Access no conoce - posible conflicto
                    result['conflicts'].append(f"Registro {key} solo en SQLite pero Access es master")
                
            elif access_row and sqlite_row:
                # Registro existe en ambos → Detectar diferencias
                changes = self._detect_changes(access_row, sqlite_row, update_fields)
                
                if changes:
                    # Aplicar cambios según reglas de precedencia
                    if self._should_update_access(changes, table_rules):
                        self._update_row_access(access_conn, table_name, primary_key, key, changes, 'sqlite_to_access')
                        result['sqlite_to_access']['affected_rows'] += 1
                        result['sqlite_to_access']['operations'].append(f"UPDATE {key}: {list(changes.keys())}")
                    
                    if self._should_update_sqlite(changes, table_rules):
                        self._update_row_sqlite(sqlite_conn, table_name, primary_key, key, changes, 'access_to_sqlite')
                        result['access_to_sqlite']['affected_rows'] += 1
                        result['access_to_sqlite']['operations'].append(f"UPDATE {key}: {list(changes.keys())}")
        
        return result
    
    def _detect_changes(self, access_row: Dict, sqlite_row: Dict, update_fields: List[str]) -> Dict[str, Tuple]:
        """
        Detecta diferencias entre registros de Access y SQLite
        Retorna dict con cambios: {campo: (valor_access, valor_sqlite)}
        """
        changes = {}
        
        # Comparar todos los campos comunes
        common_fields = set(access_row.keys()) & set(sqlite_row.keys())
        
        for field in common_fields:
            access_val = access_row.get(field)
            sqlite_val = sqlite_row.get(field)
            
            # Normalizar valores para comparación
            access_norm = self._normalize_value(access_val)
            sqlite_norm = self._normalize_value(sqlite_val)
            
            if access_norm != sqlite_norm:
                changes[field] = (access_val, sqlite_val)
        
        return changes
    
    def _normalize_value(self, value):
        """Normaliza valores para comparación (maneja None, fechas, etc.)"""
        if value is None:
            return None
        if isinstance(value, (int, float, str, bool)):
            return value
        if hasattr(value, 'isoformat'):  # datetime objects
            return value.isoformat() if value else None
        return str(value)
    
    def _should_update_access(self, changes: Dict, table_rules: Dict) -> bool:
        """
        Determina si Access debe ser actualizado con cambios de SQLite
        Solo para campos que SQLite tiene permitido modificar
        """
        update_fields = table_rules.get('update_fields', [])
        
        # Solo actualizar Access si el cambio es en un campo permitido para SQLite
        for field in changes.keys():
            if field in update_fields:
                return True
        return False
    
    def _should_update_sqlite(self, changes: Dict, table_rules: Dict) -> bool:
        """
        Determina si SQLite debe ser actualizado con cambios de Access
        Access siempre tiene precedencia excepto en campos específicos de SQLite
        """
        update_fields = table_rules.get('update_fields', [])
        
        # Actualizar SQLite para campos donde Access tiene precedencia
        for field in changes.keys():
            if field not in update_fields:
                return True
        return False
    
    def _get_table_data(self, conn, table_name: str, db_type: str) -> List[Dict]:
        """Obtiene todos los datos de una tabla"""
        try:
            if db_type == 'access':
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:  # sqlite
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo datos de {table_name} ({db_type}): {e}")
            return []
    
    def _insert_row_sqlite(self, conn: sqlite3.Connection, table_name: str, row_data: Dict):
        """Inserta una fila en SQLite"""
        try:
            columns = list(row_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = [row_data[col] for col in columns]
            
            sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
        except Exception as e:
            logger.error(f"Error insertando en SQLite {table_name}: {e}")
    
    def _insert_row_access(self, conn: pyodbc.Connection, table_name: str, row_data: Dict):
        """Inserta una fila en Access"""
        try:
            columns = list(row_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = [row_data[col] for col in columns]
            
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
        except Exception as e:
            logger.error(f"Error insertando en Access {table_name}: {e}")
    
    def _update_row_sqlite(self, conn: sqlite3.Connection, table_name: str, 
                          primary_key: str, key_value: Any, changes: Dict, direction: str):
        """Actualiza una fila en SQLite"""
        try:
            # Solo actualizar con valores de Access si es la dirección correcta
            if direction == 'access_to_sqlite':
                set_clauses = []
                values = []
                for field, (access_val, sqlite_val) in changes.items():
                    set_clauses.append(f"{field} = ?")
                    values.append(access_val)  # Usar valor de Access
                
                values.append(key_value)  # Para WHERE
                sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {primary_key} = ?"
                
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
        except Exception as e:
            logger.error(f"Error actualizando SQLite {table_name}: {e}")
    
    def _update_row_access(self, conn: pyodbc.Connection, table_name: str,
                          primary_key: str, key_value: Any, changes: Dict, direction: str):
        """Actualiza una fila en Access"""
        try:
            # Solo actualizar con valores de SQLite si es la dirección correcta  
            if direction == 'sqlite_to_access':
                set_clauses = []
                values = []
                for field, (access_val, sqlite_val) in changes.items():
                    set_clauses.append(f"{field} = ?")
                    values.append(sqlite_val)  # Usar valor de SQLite
                
                values.append(key_value)  # Para WHERE
                sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {primary_key} = ?"
                
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
        except Exception as e:
            logger.error(f"Error actualizando Access {table_name}: {e}")
    
    def _connect_access(self, access_path: Path) -> Optional[pyodbc.Connection]:
        """Conecta a base de datos Access con contraseña desde configuración"""
        try:
            password = self.config.db_password
            logger.info(f"🔐 Intentando conectar a Access con contraseña configurada")
            logger.info(f"📁 Archivo: {access_path}")
            
            # Diferentes drivers de Access y configuraciones
            connection_configs = [
                {
                    'driver': "Microsoft Access Driver (*.mdb, *.accdb)",
                    'conn_str': f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_path.absolute()};PWD={password}"
                },
                {
                    'driver': "Microsoft Access Driver (*.mdb, *.accdb)",
                    'conn_str': f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_path.absolute()};PWD={password};"
                },
                {
                    'driver': "Microsoft Access Driver (*.mdb, *.accdb)",
                    'conn_str': f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_path.absolute()};Pwd={password}"
                }
            ]
            
            for config in connection_configs:
                try:
                    logger.debug(f"🔄 Probando: {config['driver']}")
                    conn = pyodbc.connect(config['conn_str'])
                    
                    # Probar que la conexión funciona
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM TbCorreosEnviados")
                    count = cursor.fetchone()[0]
                    
                    logger.info(f"✅ Conectado exitosamente a Access: {count} registros encontrados")
                    return conn
                    
                except pyodbc.Error as e:
                    error_msg = str(e)
                    if "contraseña" in error_msg.lower() or "password" in error_msg.lower():
                        logger.warning(f"⚠️  Error de contraseña con {config['driver']}: {error_msg}")
                    else:
                        logger.debug(f"❌ Error con {config['driver']}: {error_msg}")
                    continue
                except Exception as e:
                    logger.debug(f"❌ Error general con {config['driver']}: {e}")
                    continue
            
            logger.error(f"❌ No se pudo conectar a Access con ninguna configuración")
            logger.error(f"💡 Verifica que:")
            logger.error(f"   - El archivo existe: {access_path.exists()}")
            logger.error(f"   - La contraseña es correcta: {password}")
            logger.error(f"   - El driver está instalado")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error general conectando Access {access_path}: {e}")
            return None
    
    def _connect_sqlite(self, sqlite_path: Path) -> sqlite3.Connection:
        """Conecta/crea base de datos SQLite"""
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(sqlite_path))
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _extract_from_access(self, access_conn: pyodbc.Connection, table_names: List[str]) -> Dict:
        """Extrae estructura y datos desde Access"""
        tables_data = {}
        
        for table_name in table_names:
            try:
                cursor = access_conn.cursor()
                
                # Obtener estructura de tabla
                columns = []
                try:
                    for column in cursor.columns(table_name):
                        columns.append({
                            'name': column.column_name,
                            'type': self._map_access_type_to_sqlite(column.type_name),
                            'nullable': column.nullable
                        })
                except:
                    # Si no podemos obtener estructura, usar consulta básica
                    cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
                    columns = [{'name': desc[0], 'type': 'TEXT', 'nullable': True} 
                              for desc in cursor.description]
                
                # Obtener datos
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # Convertir a diccionarios
                data = []
                column_names = [col['name'] for col in columns]
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(column_names):
                            row_dict[column_names[i]] = value
                    data.append(row_dict)
                
                tables_data[table_name] = {
                    'columns': columns,
                    'data': data,
                    'row_count': len(data)
                }
                
                logger.debug(f"Extraído {table_name}: {len(data)} registros")
                
            except Exception as e:
                logger.error(f"Error extrayendo tabla {table_name}: {e}")
                tables_data[table_name] = {'columns': [], 'data': [], 'row_count': 0}
        
        return tables_data
    
    def _map_access_type_to_sqlite(self, access_type: str) -> str:
        """Mapea tipos de datos Access a SQLite"""
        type_mapping = {
            'COUNTER': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'LONGBINARY': 'BLOB',
            'CURRENCY': 'DECIMAL',
            'DATETIME': 'DATETIME',
            'SINGLE': 'REAL',
            'DOUBLE': 'REAL',
            'INTEGER': 'INTEGER',
            'LONG': 'INTEGER',
            'SHORT': 'INTEGER',
            'VARCHAR': 'TEXT',
            'MEMO': 'TEXT',
            'BIT': 'BOOLEAN'
        }
        return type_mapping.get(access_type.upper(), 'TEXT')
    
    def _recreate_sqlite_structure(self, sqlite_conn: sqlite3.Connection, tables_data: Dict):
        """Recrea la estructura completa en SQLite"""
        cursor = sqlite_conn.cursor()
        
        for table_name, table_info in tables_data.items():
            try:
                # Eliminar tabla si existe
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                
                # Crear tabla nueva
                columns_def = []
                for col in table_info['columns']:
                    null_constraint = "NOT NULL" if not col['nullable'] else ""
                    columns_def.append(f"{col['name']} {col['type']} {null_constraint}")
                
                if columns_def:
                    create_sql = f"CREATE TABLE {table_name} ({', '.join(columns_def)})"
                    cursor.execute(create_sql)
                    logger.debug(f"Tabla {table_name} recreada en SQLite")
                
            except Exception as e:
                logger.error(f"Error recreando tabla {table_name}: {e}")
        
        sqlite_conn.commit()
    
    def _insert_data_to_sqlite(self, sqlite_conn: sqlite3.Connection, tables_data: Dict):
        """Inserta todos los datos desde Access a SQLite"""
        cursor = sqlite_conn.cursor()
        
        for table_name, table_info in tables_data.items():
            try:
                if table_info['data']:
                    column_names = [col['name'] for col in table_info['columns']]
                    placeholders = ', '.join(['?' for _ in column_names])
                    
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                    
                    for row_dict in table_info['data']:
                        values = [row_dict.get(col, None) for col in column_names]
                        cursor.execute(insert_sql, values)
                    
                    logger.debug(f"Insertados {len(table_info['data'])} registros en {table_name}")
                
            except Exception as e:
                logger.error(f"Error insertando datos en {table_name}: {e}")
        
        sqlite_conn.commit()
    
    def _save_sync_metadata(self, sqlite_conn: sqlite3.Connection, db_name: str, sync_type: str = 'ACCESS_TO_SQLITE'):
        """Guarda metadatos de sincronización"""
        cursor = sqlite_conn.cursor()
        
        # Crear tabla de metadatos si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _sync_metadata (
                id INTEGER PRIMARY KEY,
                database_name TEXT,
                last_sync_timestamp TEXT,
                sync_direction TEXT,
                sync_status TEXT
            )
        """)
        
        # Insertar registro de sincronización
        cursor.execute("""
            INSERT OR REPLACE INTO _sync_metadata 
            (id, database_name, last_sync_timestamp, sync_direction, sync_status)
            VALUES (1, ?, ?, ?, 'SUCCESS')
        """, (db_name, datetime.now().isoformat(), sync_type))
        
        sqlite_conn.commit()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Obtiene estado de sincronización de todas las bases"""
        status = {}
        
        for db_name, db_config in self.sync_rules.items():
            sqlite_path = db_config['sqlite_path']
            
            if sqlite_path.exists():
                try:
                    conn = sqlite3.connect(str(sqlite_path))
                    cursor = conn.cursor()
                    
                    # Verificar metadatos
                    cursor.execute("SELECT last_sync_timestamp FROM _sync_metadata WHERE id = 1")
                    result = cursor.fetchone()
                    
                    if result:
                        status[db_name] = {
                            'sqlite_exists': True,
                            'last_sync': result[0],
                            'access_path': str(db_config['access_path']),
                            'access_exists': db_config['access_path'].exists()
                        }
                    else:
                        status[db_name] = {
                            'sqlite_exists': True,
                            'last_sync': 'Unknown',
                            'access_path': str(db_config['access_path']),
                            'access_exists': db_config['access_path'].exists()
                        }
                    
                    conn.close()
                    
                except Exception as e:
                    status[db_name] = {
                        'sqlite_exists': True,
                        'error': str(e),
                        'access_path': str(db_config['access_path']),
                        'access_exists': db_config['access_path'].exists()
                    }
            else:
                status[db_name] = {
                    'sqlite_exists': False,
                    'access_path': str(db_config['access_path']),
                    'access_exists': db_config['access_path'].exists()
                }
        
        return status


def main():
    """Función principal para ejecutar sincronización"""
    import sys
    from pathlib import Path
    
    # Añadir path para config
    sys.path.append(str(Path(__file__).parent / 'src' / 'common'))
    
    try:
        from config import Config
        config = Config()
    except ImportError:
        # Fallback configuration si no existe el módulo
        logger.error("No se pudo importar configuración, usando valores por defecto")
        
        # Crear configuración básica
        class FallbackConfig:
            def __init__(self):
                from dotenv import load_dotenv  # Import local
                load_dotenv()  # Cargar variables de .env
                self.db_password = os.getenv('DB_PASSWORD', 'dpddpd')
                self.root_dir = Path(__file__).parent
                # Usar rutas correctas de Access en dbs-locales
                self.db_correos_path = self.root_dir / 'dbs-locales' / 'correos_datos.accdb'
                self.db_brass_path = self.root_dir / 'dbs-locales' / 'Gestion_Brass_Gestion_Datos.accdb'  
                self.db_tareas_path = self.root_dir / 'dbs-locales' / 'Tareas_datos1.accdb'
                self.logs_dir = self.root_dir / 'logs'
                self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        config = FallbackConfig()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.logs_dir / 'access_sync.log'),
            logging.StreamHandler()
        ]
    )
    
    logger.info("=" * 60)
    logger.info("🎯 SINCRONIZACIÓN BIDIRECCIONAL: ACCESS ↔ SQLite")
    logger.info("=" * 60)
    
    syncer = BidirectionalSync(config)
    
    # Mostrar estado actual
    status = syncer.get_sync_status()
    logger.info("📊 Estado actual:")
    for db_name, db_status in status.items():
        logger.info(f"  {db_name}: SQLite={db_status.get('sqlite_exists', False)}, "
                   f"Access={db_status.get('access_exists', False)}")
    
    # Ejecutar sincronización bidireccional
    results = syncer.sync_all_databases()
    
    # Mostrar resultados
    logger.info("=" * 60)
    logger.info("📋 RESULTADO DE SINCRONIZACIÓN:")
    for db_name, result in results.items():
        if isinstance(result, dict) and result.get('success'):
            status_icon = "✅"
            logger.info(f"  {status_icon} {db_name}")
            logger.info(f"     📥 Access → SQLite: {result['access_to_sqlite']['affected_rows']} filas")
            logger.info(f"     📤 SQLite → Access: {result['sqlite_to_access']['affected_rows']} filas")
        else:
            status_icon = "❌"
            logger.info(f"  {status_icon} {db_name}")
            if isinstance(result, dict):
                logger.error(f"     Error: {result.get('error', 'Unknown')}")
    
    successful = sum(1 for result in results.values() 
                    if isinstance(result, dict) and result.get('success'))
    total = len(results)
    logger.info(f"📊 Total: {successful}/{total} bases sincronizadas")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
