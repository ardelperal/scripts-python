#!/usr/bin/env python3
"""
Script para preparar el entorno local:
1. Copia bases de datos desde ubicaciones remotas (oficina) a ubicaciones locales
2. Actualiza vínculos de tablas vinculadas para que apunten a bases de datos locales

Autor: Sistema de Gestión
Fecha: 2024
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import win32com.client
import pythoncom
from dotenv import load_dotenv
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_local_environment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LocalEnvironmentSetup:
    """Clase para configurar el entorno local de desarrollo"""
    
    def __init__(self):
        """Inicializar configuración"""
        # Inicializar logger
        self.logger = logging.getLogger(__name__)
        
        load_dotenv()
        self.project_root = Path(__file__).parent
        self.db_password = os.getenv('DB_PASSWORD', '')
        
        # Descubrir automáticamente las bases de datos desde el .env
        self.databases = self._discover_databases_from_env()
        
        # Crear directorio local si no existe
        self._ensure_local_directories()
    
    def _discover_databases_from_env(self) -> Dict[str, Tuple[str, str, str]]:
        """
        Descubre automáticamente las bases de datos desde las variables de entorno
        
        Returns:
            Dict con mapeo de bases de datos: {nombre: (office_var, local_var, filename)}
        """
        databases = {}
        
        # Obtener todas las variables de entorno
        env_vars = dict(os.environ)
        
        # Buscar pares OFFICE_DB_* y LOCAL_DB_*
        office_vars = {k: v for k, v in env_vars.items() if k.startswith('OFFICE_DB_')}
        local_vars = {k: v for k, v in env_vars.items() if k.startswith('LOCAL_DB_')}
        
        for office_var, office_path in office_vars.items():
            # Extraer nombre de la base de datos (ej: OFFICE_DB_BRASS -> BRASS)
            db_name = office_var.replace('OFFICE_DB_', '')
            local_var = f'LOCAL_DB_{db_name}'
            
            if local_var in local_vars:
                local_path = local_vars[local_var]
                filename = os.path.basename(office_path)
                
                databases[db_name] = (office_var, local_var, filename)
                self.logger.debug(f"Base de datos descubierta: {db_name}")
                self.logger.debug(f"  Oficina: {office_var} = {office_path}")
                self.logger.debug(f"  Local: {local_var} = {local_path}")
                self.logger.debug(f"  Archivo: {filename}")
        
        self.logger.info(f"Descubiertas {len(databases)} bases de datos desde .env")
        return databases
    
    def _check_network_accessibility(self) -> bool:
        """Verifica si la ubicación de red de oficina es accesible"""
        # Extraer la ubicación de red común de las rutas de oficina
        network_locations = set()
        
        for db_name, (office_var, local_var, filename) in self.databases.items():
            office_path = os.getenv(office_var)
            if office_path and office_path.startswith('\\\\'):
                # Extraer la parte del servidor de red (ej: \\datoste\Aplicaciones_dys)
                parts = office_path.split('\\')
                if len(parts) >= 4:  # ['', '', 'servidor', 'recurso', ...]
                    network_root = f"\\\\{parts[2]}\\{parts[3]}"
                    network_locations.add(network_root)
        
        if not network_locations:
            self.logger.info("No se encontraron ubicaciones de red para verificar")
            return True
        
        self.logger.info("[NET] Verificando accesibilidad de ubicaciones de red...")
        
        all_accessible = True
        for network_location in network_locations:
            try:
                # Intentar acceder a la ubicación de red
                if os.path.exists(network_location):
                    self.logger.info(f"  [OK] {network_location} - Accesible")
                else:
                    self.logger.error(f"  [X] {network_location} - No accesible")
                    all_accessible = False
            except Exception as e:
                self.logger.error(f"  [X] {network_location} - Error: {e}")
                all_accessible = False
        
        if not all_accessible:
            self.logger.error("[!] Algunas ubicaciones de red no son accesibles")
            self.logger.error("   Verifica tu conexión a la red de oficina")
            self.logger.error("   O ejecuta el script desde la red de oficina")
        
        return all_accessible
    
    def show_configuration(self):
        """Muestra la configuración descubierta desde el .env"""
        self.logger.info("=== CONFIGURACIÓN DESCUBIERTA DESDE .ENV ===")
        
        if not self.databases:
            self.logger.warning("No se encontraron bases de datos configuradas")
            return
        
        for db_name, (office_var, local_var, filename) in self.databases.items():
            office_path = os.getenv(office_var, 'NO CONFIGURADO')
            local_path = os.getenv(local_var, 'NO CONFIGURADO')
            
            self.logger.info(f"\n[FOLDER] {db_name}:")
            self.logger.info(f"  Archivo: {filename}")
            self.logger.info(f"  Oficina ({office_var}): {office_path}")
            self.logger.info(f"  Local ({local_var}): {local_path}")
            
            # Verificar existencia
            if office_path != 'NO CONFIGURADO':
                exists_office = "[OK]" if os.path.exists(office_path) else "[X]"
                self.logger.info(f"  Estado oficina: {exists_office}")
            
            if local_path != 'NO CONFIGURADO':
                if not os.path.isabs(local_path):
                    local_path = str(self.project_root / local_path)
                exists_local = "[OK]" if os.path.exists(local_path) else "[X]"
                self.logger.info(f"  Estado local: {exists_local}")
        
        self.logger.info("=" * 50)
    
    def _ensure_local_directories(self):
        """Crear directorios locales necesarios"""
        for db_name, (office_var, local_var, filename) in self.databases.items():
            local_path = os.getenv(local_var)
            if local_path:
                # Convertir a ruta absoluta si es relativa
                if not os.path.isabs(local_path):
                    local_path = self.project_root / local_path
                
                # Crear directorio padre si no existe
                local_dir = os.path.dirname(local_path)
                os.makedirs(local_dir, exist_ok=True)
                self.logger.debug(f"Directorio asegurado: {local_dir}")
        
    def _setup_correos_database_light(self, office_path: str, local_path: str) -> bool:
        """
        Configura la base de datos de correos en modo ligero (solo últimos 5 registros)
        Crea la base desde cero con contraseña y estructura idéntica a la remota
        
        Args:
            office_path: Ruta de la base de datos en oficina
            local_path: Ruta de la base de datos local
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            office_name = os.path.basename(office_path)
            local_name = os.path.basename(local_path)
            
            self.logger.info(f"[EMAIL] Configurando base de datos de correos (creación desde cero)...")
            self.logger.info(f"  [FOLDER] Origen: {office_name}")
            self.logger.info(f"  [FOLDER] Destino: {local_name}")
            
            # Asegurar que el directorio local existe
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Si la base local existe, eliminarla para recrearla
            if os.path.exists(local_path):
                self.logger.info(f"  [DELETE] Eliminando base local existente {local_name}...")
                try:
                    os.remove(local_path)
                    self.logger.info(f"  [OK] Base local eliminada")
                except Exception as e:
                    self.logger.error(f"  [X] Error eliminando base local: {e}")
                    return False
            
            # Crear la base de datos desde cero
            if not self._create_correos_database_from_scratch(office_path, local_path):
                return False
            
            # Llenar con los últimos 5 registros
            return self._fill_correos_with_latest_records(office_path, local_path)
                
        except Exception as e:
            self.logger.error(f"  [X] Error configurando base de correos: {e}")
            return False

    def _create_correos_database_from_scratch(self, office_path: str, local_path: str) -> bool:
        """
        Crea una base de datos Access desde cero con contraseña y estructura idéntica a la remota
        
        Args:
            office_path: Ruta de la base de datos en oficina (para analizar estructura)
            local_path: Ruta de la base de datos local a crear
            
        Returns:
            bool: True si la creación fue exitosa
        """
        import win32com.client
        import pyodbc
        
        try:
            local_name = os.path.basename(local_path)
            
            self.logger.info(f"  [BUILD] Creando base de datos {local_name} desde cero...")
            
            # Asegurar que el directorio existe y usar ruta absoluta
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)
            local_path_abs = os.path.abspath(local_path)
            
            self.logger.info(f"  [PIN] Ruta absoluta: {local_path_abs}")
            
            # Paso 1: Crear base de datos vacía
            self.logger.info(f"  [ACTIONS] Creando archivo de base de datos...")
            access = win32com.client.Dispatch("Access.Application")
            access.Visible = False  # Asegurar que Access no sea visible
            access.NewCurrentDatabase(local_path_abs)
            access.Quit()
            access = None  # Liberar referencia COM
            
            # Verificar que el archivo se creó
            if not os.path.exists(local_path_abs):
                self.logger.error(f"  [X] El archivo de base de datos no se creó: {local_path_abs}")
                return False
            
            # Paso 2: Aplicar contraseña
            self.logger.info(f"  [LOCK] Aplicando contraseña a la base de datos...")
            access = win32com.client.Dispatch("Access.Application")
            access.Visible = False
            
            # Abrir en modo exclusivo para poder establecer contraseña
            access.OpenCurrentDatabase(local_path_abs, True)  # True = modo exclusivo
            
            # Establecer contraseña usando NewPassword (contraseña_actual, contraseña_nueva)
            access.CurrentDb().NewPassword("", self.db_password)  # "" = sin contraseña previa
            
            access.CloseCurrentDatabase()
            access.Quit()
            access = None  # Liberar referencia COM
            
            # Paso 3: Analizar estructura de la base remota
            self.logger.info(f"  [SEARCH] Analizando estructura de la base remota...")
            table_structure = self._analyze_remote_table_structure(office_path)
            
            if not table_structure:
                self.logger.error(f"  [X] No se pudo analizar la estructura de la base remota")
                return False
            
            # Paso 4: Crear tabla con la estructura analizada
            self.logger.info(f"  [BUILD] Creando tabla {table_structure['name']} con estructura idéntica...")
            if not self._create_table_with_structure(local_path_abs, table_structure):
                return False
            
            self.logger.info(f"  [OK] Base de datos {local_name} creada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error creando base de datos desde cero: {e}")
            return False

    def _analyze_remote_table_structure(self, office_path: str) -> dict:
        """
        Analiza la estructura de la tabla principal en la base remota
        
        Args:
            office_path: Ruta de la base de datos remota
            
        Returns:
            dict: Información de la estructura de la tabla o None si hay error
        """
        import pyodbc
        
        try:
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
            conn_str = f'DRIVER={driver};DBQ={office_path};PWD={self.db_password};'
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Encontrar la tabla principal (primera que no sea del sistema)
            main_table_name = None
            tables = cursor.tables(tableType='TABLE')
            
            for table in tables:
                table_name = table.table_name
                if (not table_name.startswith('MSys') and 
                    not table_name.startswith('~')):
                    main_table_name = table_name
                    break
            
            if not main_table_name:
                self.logger.error(f"  [X] No se encontró tabla principal en la base remota")
                conn.close()
                return None
            
            # Obtener información detallada de las columnas
            columns_info = []
            columns = cursor.columns(table=main_table_name)
            
            for col in columns:
                column_info = {
                    'name': col.column_name,
                    'type': col.type_name,
                    'size': col.column_size if hasattr(col, 'column_size') else None,
                    'nullable': col.nullable == 1 if hasattr(col, 'nullable') else True,
                    'default': col.column_def if hasattr(col, 'column_def') else None
                }
                columns_info.append(column_info)
            
            conn.close()
            
            structure = {
                'name': main_table_name,
                'columns': columns_info
            }
            
            self.logger.info(f"  [OK] Estructura analizada: tabla '{main_table_name}' con {len(columns_info)} columnas")
            return structure
            
        except Exception as e:
            self.logger.error(f"  [X] Error analizando estructura remota: {e}")
            return None

    def _create_table_with_structure(self, local_path: str, table_structure: dict) -> bool:
        """
        Crea una tabla en la base local con la estructura especificada
        
        Args:
            local_path: Ruta de la base de datos local
            table_structure: Diccionario con la estructura de la tabla
            
        Returns:
            bool: True si la creación fue exitosa
        """
        import pyodbc
        
        try:
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
            conn_str = f'DRIVER={driver};DBQ={local_path};PWD={self.db_password};'
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            table_name = table_structure['name']
            columns = table_structure['columns']
            
            # Construir la sentencia CREATE TABLE
            column_definitions = []
            
            for col in columns:
                col_def = f"[{col['name']}]"
                
                # Mapear tipos de datos de ODBC a Access SQL
                access_type = self._map_odbc_type_to_access(col['type'], col.get('size'))
                col_def += f" {access_type}"
                
                # Agregar restricciones
                if not col.get('nullable', True):
                    col_def += " NOT NULL"
                
                if col.get('default'):
                    col_def += f" DEFAULT {col['default']}"
                
                column_definitions.append(col_def)
            
            # Crear la tabla
            create_sql = f"CREATE TABLE [{table_name}] ({', '.join(column_definitions)})"
            
            self.logger.debug(f"  [ACTIONS] SQL: {create_sql}")
            cursor.execute(create_sql)
            conn.commit()
            conn.close()
            
            self.logger.info(f"  [OK] Tabla {table_name} creada con {len(columns)} columnas")
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error creando tabla: {e}")
            return False

    def _map_odbc_type_to_access(self, odbc_type: str, size: int = None) -> str:
        """
        Mapea tipos de datos ODBC a tipos de Access SQL
        
        Args:
            odbc_type: Tipo de dato ODBC
            size: Tamaño del campo (opcional)
            
        Returns:
            str: Tipo de dato compatible con Access SQL
        """
        # Mapeo de tipos comunes
        type_mapping = {
            'COUNTER': 'AUTOINCREMENT',
            'INTEGER': 'INTEGER',
            'LONG': 'LONG',
            'SINGLE': 'SINGLE',
            'DOUBLE': 'DOUBLE',
            'CURRENCY': 'CURRENCY',
            'DATETIME': 'DATETIME',
            'BIT': 'YESNO',
            'BYTE': 'BYTE',
            'LONGBINARY': 'LONGBINARY',
            'LONGTEXT': 'MEMO'
        }
        
        # Tipos de texto con tamaño
        if odbc_type in ['VARCHAR', 'CHAR', 'TEXT']:
            if size and size > 0:
                return f"TEXT({size})"
            else:
                return "TEXT(255)"
        
        # Buscar en el mapeo
        mapped_type = type_mapping.get(odbc_type.upper())
        if mapped_type:
            return mapped_type
        
        # Por defecto, usar TEXT
        self.logger.debug(f"  [!] Tipo desconocido {odbc_type}, usando TEXT por defecto")
        return "TEXT(255)"

    def _fill_correos_with_latest_records(self, office_path: str, local_path: str) -> bool:
        """
        Llena la base local con los últimos 5 registros de la base remota
        
        Args:
            office_path: Ruta de la base de datos en oficina
            local_path: Ruta de la base de datos local
            
        Returns:
            bool: True si la operación fue exitosa
        """
        import pyodbc
        
        try:
            office_name = os.path.basename(office_path)
            local_name = os.path.basename(local_path)
            
            self.logger.info(f"  📥 Obteniendo últimos 5 registros de {office_name}...")
            
            # Configurar cadena de conexión para Access
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
            
            # Conectar a la base de oficina
            office_conn_str = f'DRIVER={driver};DBQ={office_path};PWD={self.db_password};'
            office_conn = pyodbc.connect(office_conn_str)
            office_cursor = office_conn.cursor()
            
            # Obtener la tabla principal
            main_table_name = None
            tables = office_cursor.tables(tableType='TABLE')
            
            for table in tables:
                table_name = table.table_name
                if (not table_name.startswith('MSys') and 
                    not table_name.startswith('~')):
                    main_table_name = table_name
                    break
            
            if not main_table_name:
                self.logger.warning(f"  [!] No se encontró tabla principal en {office_name}")
                office_conn.close()
                return True
            
            # Obtener información de columnas
            columns_info = office_cursor.columns(table=main_table_name)
            column_names = [col.column_name for col in columns_info]
            
            # Intentar obtener los últimos 5 registros con diferentes campos de ordenación
            order_fields = ['ID', 'Id', 'id', 'Fecha', 'fecha', 'FechaCreacion', 'Timestamp']
            records_obtained = False
            records = []
            
            for field in order_fields:
                if field in column_names:
                    try:
                        query_sql = f"SELECT TOP 5 * FROM [{main_table_name}] ORDER BY [{field}] DESC"
                        office_cursor.execute(query_sql)
                        records = office_cursor.fetchall()
                        self.logger.info(f"  [OK] Obtenidos últimos 5 registros usando campo {field}")
                        records_obtained = True
                        break
                    except Exception as e:
                        self.logger.debug(f"  [!] No se pudo ordenar por {field}: {e}")
                        continue
            
            if not records_obtained:
                # Si no se pudo ordenar, obtener los primeros 5 registros
                try:
                    query_sql = f"SELECT TOP 5 * FROM [{main_table_name}]"
                    office_cursor.execute(query_sql)
                    records = office_cursor.fetchall()
                    self.logger.info(f"  [OK] Obtenidos primeros 5 registros (sin ordenación específica)")
                    records_obtained = True
                except Exception as e:
                    self.logger.error(f"  [X] Error obteniendo registros: {e}")
                    office_conn.close()
                    return False
            
            office_conn.close()
            
            if not records or len(records) == 0:
                self.logger.warning(f"  [!] No se encontraron registros en {office_name}")
                return True
            
            # Insertar los registros en la base local
            self.logger.info(f"  [SAVE] Insertando {len(records)} registros en {local_name}...")
            
            local_conn_str = f'DRIVER={driver};DBQ={local_path};PWD={self.db_password};'
            local_conn = pyodbc.connect(local_conn_str)
            local_cursor = local_conn.cursor()
            
            # Construir la consulta INSERT
            placeholders = ','.join(['?' for _ in column_names])
            insert_sql = f"INSERT INTO [{main_table_name}] ({','.join([f'[{col}]' for col in column_names])}) VALUES ({placeholders})"
            
            try:
                for record in records:
                    local_cursor.execute(insert_sql, record)
                local_conn.commit()
                self.logger.info(f"  [OK] {len(records)} registros insertados correctamente")
            except Exception as e:
                self.logger.error(f"  [X] Error insertando registros: {e}")
                local_conn.rollback()
                local_conn.close()
                return False
            
            local_conn.close()
            
            # Verificar el tamaño final
            size_mb = os.path.getsize(local_path) / (1024 * 1024)
            self.logger.info(f"  🎉 Base {local_name} completada con últimos registros ({size_mb:.1f} MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error llenando base con últimos registros: {e}")
            return False

    def _clean_and_fill_correos_sql(self, office_path: str, local_path: str) -> bool:
        """
        Limpia la base de datos local y la rellena con los últimos 5 registros usando pyodbc
        
        Args:
            office_path: Ruta de la base de datos en oficina
            local_path: Ruta de la base de datos local
            
        Returns:
            bool: True si la operación fue exitosa
        """
        import pyodbc
        
        try:
            office_name = os.path.basename(office_path)
            local_name = os.path.basename(local_path)
            
            # Limpiar archivos de bloqueo antes de empezar
            self._clean_lock_files(local_path)
            
            # Configurar cadena de conexión para Access
            driver = '{Microsoft Access Driver (*.mdb, *.accdb)}'
            
            # Primero limpiar la base local
            self.logger.info(f"  🧹 Vaciando contenido de {local_name}...")
            
            local_conn_str = f'DRIVER={driver};DBQ={local_path};PWD={self.db_password};'
            local_conn = pyodbc.connect(local_conn_str)
            local_cursor = local_conn.cursor()
            
            # Obtener la tabla principal (primera tabla que no sea del sistema)
            main_table_name = None
            tables = local_cursor.tables(tableType='TABLE')
            
            for table in tables:
                table_name = table.table_name
                if (not table_name.startswith('MSys') and 
                    not table_name.startswith('~')):
                    main_table_name = table_name
                    break
            
            if not main_table_name:
                self.logger.warning(f"  [!] No se encontró tabla principal en {local_name}")
                local_conn.close()
                return True
            
            # Eliminar todos los registros de la tabla local
            try:
                local_cursor.execute(f"DELETE FROM [{main_table_name}]")
                local_conn.commit()
                self.logger.info(f"  [OK] Tabla {main_table_name} vaciada")
            except Exception as e:
                self.logger.error(f"  [X] Error vaciando tabla {main_table_name}: {e}")
                local_conn.close()
                return False
            
            # Cerrar conexión local
            local_conn.close()
            
            # Ahora conectar a la base de oficina para obtener los últimos 5 registros
            self.logger.info(f"  📥 Obteniendo últimos 5 registros de {office_name}...")
            
            office_conn_str = f'DRIVER={driver};DBQ={office_path};PWD={self.db_password};'
            office_conn = pyodbc.connect(office_conn_str)
            office_cursor = office_conn.cursor()
            
            # Verificar que la tabla existe en la base de oficina
            office_tables = [table.table_name for table in office_cursor.tables(tableType='TABLE')]
            
            if main_table_name not in office_tables:
                self.logger.error(f"  [X] Tabla {main_table_name} no existe en {office_name}")
                office_conn.close()
                return False
            
            # Obtener información de columnas para construir el INSERT
            columns_info = office_cursor.columns(table=main_table_name)
            column_names = [col.column_name for col in columns_info]
            
            # Intentar obtener los últimos 5 registros con diferentes campos de ordenación
            order_fields = ['ID', 'Id', 'id', 'Fecha', 'fecha', 'FechaCreacion', 'Timestamp']
            records_obtained = False
            records = []
            
            for field in order_fields:
                if field in column_names:
                    try:
                        query_sql = f"SELECT TOP 5 * FROM [{main_table_name}] ORDER BY [{field}] DESC"
                        office_cursor.execute(query_sql)
                        records = office_cursor.fetchall()
                        self.logger.info(f"  [OK] Obtenidos últimos 5 registros usando campo {field}")
                        records_obtained = True
                        break
                    except Exception as e:
                        self.logger.debug(f"  [!] No se pudo ordenar por {field}: {e}")
                        continue
            
            if not records_obtained:
                # Si no se pudo ordenar, obtener los primeros 5 registros
                try:
                    query_sql = f"SELECT TOP 5 * FROM [{main_table_name}]"
                    office_cursor.execute(query_sql)
                    records = office_cursor.fetchall()
                    self.logger.info(f"  [OK] Obtenidos primeros 5 registros (sin ordenación específica)")
                    records_obtained = True
                except Exception as e:
                    self.logger.error(f"  [X] Error obteniendo registros: {e}")
                    office_conn.close()
                    return False
            
            office_conn.close()
            
            if not records or len(records) == 0:
                self.logger.warning(f"  [!] No se encontraron registros en {office_name}")
                return True
            
            # Insertar los registros en la base local
            self.logger.info(f"  [SAVE] Insertando {len(records)} registros en {local_name}...")
            
            local_conn = pyodbc.connect(local_conn_str)
            local_cursor = local_conn.cursor()
            
            # Construir la consulta INSERT
            placeholders = ','.join(['?' for _ in column_names])
            insert_sql = f"INSERT INTO [{main_table_name}] ({','.join([f'[{col}]' for col in column_names])}) VALUES ({placeholders})"
            
            try:
                for record in records:
                    local_cursor.execute(insert_sql, record)
                local_conn.commit()
                self.logger.info(f"  [OK] {len(records)} registros insertados correctamente")
            except Exception as e:
                self.logger.error(f"  [X] Error insertando registros: {e}")
                local_conn.rollback()
                local_conn.close()
                return False
            
            local_conn.close()
            
            # Verificar el tamaño final
            size_mb = os.path.getsize(local_path) / (1024 * 1024)
            self.logger.info(f"  🎉 Base {local_name} actualizada con últimos registros ({size_mb:.1f} MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"  [X] Error en limpieza y llenado con pyodbc: {e}")
            return False
            
        finally:
            # Limpiar archivos de bloqueo al final
            self._clean_lock_files(local_path)

    def _clean_lock_files(self, db_path: str):
        """
        Limpia archivos de bloqueo (.ldb, .laccdb) asociados a una base de datos
        
        Args:
            db_path: Ruta de la base de datos
        """
        try:
            # Archivos de bloqueo posibles
            lock_extensions = ['.ldb', '.laccdb']
            base_path = os.path.splitext(db_path)[0]
            
            for ext in lock_extensions:
                lock_file = base_path + ext
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                        self.logger.debug(f"  🧹 Archivo de bloqueo eliminado: {os.path.basename(lock_file)}")
                    except Exception as e:
                        self.logger.debug(f"  [!] No se pudo eliminar archivo de bloqueo {os.path.basename(lock_file)}: {e}")
        except Exception as e:
            self.logger.debug(f"  [!] Error limpiando archivos de bloqueo: {e}")



    def copy_databases(self) -> bool:
        """
        Copia todas las bases de datos desde ubicaciones remotas a locales
        
        Returns:
            bool: True si todas las copias fueron exitosas
        """
        self.logger.info("=== Iniciando copia de bases de datos ===")
        success_count = 0
        total_count = len(self.databases)
        
        for db_name, (office_var, local_var, filename) in self.databases.items():
            try:
                # Obtener rutas desde variables de entorno
                office_path = os.getenv(office_var)
                local_path = os.getenv(local_var)
                
                if not office_path or not local_path:
                    self.logger.error(f"Variables de entorno no encontradas para {db_name}")
                    continue
                
                # Convertir rutas relativas a absolutas
                if not os.path.isabs(local_path):
                    local_path = self.project_root / local_path
                
                self.logger.info(f"Copiando {db_name}...")
                self.logger.info(f"  Origen: {office_path}")
                self.logger.info(f"  Destino: {local_path}")
                
                # Verificar que el archivo origen existe
                if not os.path.exists(office_path):
                    self.logger.error(f"Archivo origen no encontrado: {office_path}")
                    continue
                
                # Crear directorio destino si no existe
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Manejo especial para base de datos de correos
                if db_name == 'CORREOS' or 'correos' in filename.lower():
                    if self._setup_correos_database_light(office_path, local_path):
                        self.logger.info(f"✓ {db_name} configurada exitosamente (modo ligero)")
                        success_count += 1
                    else:
                        self.logger.error(f"✗ Error configurando {db_name} en modo ligero")
                else:
                    # Copia normal para otras bases de datos
                    shutil.copy2(office_path, local_path)
                    
                    # Verificar que la copia fue exitosa
                    if os.path.exists(local_path):
                        size_origin = os.path.getsize(office_path)
                        size_dest = os.path.getsize(local_path)
                        
                        if size_origin == size_dest:
                            self.logger.info(f"✓ {db_name} copiada exitosamente ({size_dest:,} bytes)")
                            success_count += 1
                        else:
                            self.logger.error(f"✗ Error en copia de {db_name}: tamaños diferentes")
                    else:
                        self.logger.error(f"✗ Error en copia de {db_name}: archivo destino no creado")
                    
            except Exception as e:
                self.logger.error(f"✗ Error copiando {db_name}: {e}")
        
        self.logger.info(f"=== Copia completada: {success_count}/{total_count} exitosas ===")
        return success_count == total_count
    
    def get_linked_tables(self, db_path: str) -> List[Tuple[str, str]]:
        """
        Obtener lista de tablas vinculadas en una base de datos Access.
        
        Args:
            db_path: Ruta a la base de datos Access
            
        Returns:
            Lista de tuplas (nombre_tabla, ruta_vinculada)
        """
        linked_tables = []
        access_app = None
        db = None
        
        try:
            # Inicializar COM
            pythoncom.CoInitialize()
            
            # Crear aplicación Access en modo completamente silencioso
            access_app = win32com.client.Dispatch("Access.Application")
            access_app.Visible = False
            access_app.UserControl = False
            
            # Abrir base de datos con contraseña de forma silenciosa
            if self.db_password:
                # Usar método que no muestra diálogos
                access_app.OpenCurrentDatabase(db_path, False, self.db_password)
            else:
                access_app.OpenCurrentDatabase(db_path, False)
            
            # Suprimir todos los mensajes y diálogos después de abrir la BD
            access_app.DoCmd.SetWarnings(False)
            
            # Obtener referencia a la base de datos actual
            db = access_app.CurrentDb()
            
            # Iterar sobre todas las tablas
            for i in range(db.TableDefs.Count):
                table_def = db.TableDefs(i)
                table_name = table_def.Name
                
                # Verificar si es una tabla vinculada (tiene Connect property)
                if hasattr(table_def, 'Connect') and table_def.Connect:
                    connect_string = table_def.Connect
                    
                    # Extraer la ruta del archivo de la cadena de conexión
                    if 'DATABASE=' in connect_string:
                        db_path_part = connect_string.split('DATABASE=')[1]
                        # Remover cualquier parámetro adicional después del path
                        if ';' in db_path_part:
                            db_path_part = db_path_part.split(';')[0]
                        
                        linked_tables.append((table_name, db_path_part))
                        self.logger.debug(f"Tabla vinculada encontrada: {table_name} -> {db_path_part}")
            
            self.logger.info(f"Encontradas {len(linked_tables)} tablas vinculadas en {db_path}")
            
        except Exception as e:
            self.logger.error(f"Error al obtener tablas vinculadas de {db_path}: {e}")
            
        finally:
            # Cerrar base de datos y aplicación de forma silenciosa
            try:
                if access_app:
                    # Restaurar advertencias antes de cerrar
                    access_app.DoCmd.SetWarnings(True)
                    access_app.CloseCurrentDatabase()
                    access_app.Quit()
            except Exception:
                # Ignorar errores al cerrar la aplicación Access
                pass
            
            # Limpiar COM
            try:
                pythoncom.CoUninitialize()
            except Exception:
                # Ignorar errores al limpiar COM
                pass
        
        return linked_tables
    
    def update_linked_table(self, db_path: str, table_name: str, old_path: str, new_path: str) -> bool:
        """
        Actualiza el vínculo de una tabla específica
        
        Args:
            db_path: Ruta a la base de datos
            table_name: Nombre de la tabla vinculada
            old_path: Ruta antigua de la base de datos vinculada
            new_path: Nueva ruta de la base de datos vinculada
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        access_app = None
        
        try:
            # Inicializar COM
            pythoncom.CoInitialize()
            
            # Crear aplicación Access en modo completamente silencioso
            access_app = win32com.client.Dispatch("Access.Application")
            access_app.Visible = False
            access_app.UserControl = False
            
            # Abrir base de datos con contraseña de forma silenciosa
            if self.db_password:
                # Usar método que no muestra diálogos
                access_app.OpenCurrentDatabase(db_path, False, self.db_password)
            else:
                access_app.OpenCurrentDatabase(db_path, False)
            
            # Suprimir todos los mensajes y diálogos después de abrir la BD
            access_app.DoCmd.SetWarnings(False)
            
            # Obtener referencia a la tabla
            table_def = access_app.CurrentDb().TableDefs(table_name)
            
            # Construir nueva cadena de conexión
            old_connect = table_def.Connect
            new_connect = old_connect.replace(old_path, new_path)
            
            # Actualizar conexión
            table_def.Connect = new_connect
            table_def.RefreshLink()
            
            self.logger.info(f"✓ Vínculo actualizado para tabla '{table_name}'")
            self.logger.debug(f"  Anterior: {old_path}")
            self.logger.debug(f"  Nueva: {new_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error actualizando vínculo de tabla '{table_name}': {e}")
            return False
        finally:
            # Cerrar base de datos y aplicación de forma silenciosa
            try:
                if access_app:
                    # Restaurar advertencias antes de cerrar
                    access_app.DoCmd.SetWarnings(True)
                    access_app.CloseCurrentDatabase()
                    access_app.Quit()
            except Exception:
                # Ignorar errores al cerrar la aplicación Access
                pass
            
            # Limpiar COM
            try:
                pythoncom.CoUninitialize()
            except Exception:
                # Ignorar errores al limpiar COM
                pass
    
    def update_database_links(self, db_path: str) -> tuple[bool, list[str], list[dict]]:
        """
        Actualiza todos los vínculos de una base de datos para que apunten a ubicaciones locales
        Usa el enfoque mejorado con COM para analizar y revincular tablas
        
        Args:
            db_path: Ruta a la base de datos local
            
        Returns:
            tuple: (success, missing_databases, failed_links)
                - success: True si todas las actualizaciones fueron exitosas
                - missing_databases: Lista de nombres de bases de datos faltantes
                - failed_links: Lista de diccionarios con detalles de vínculos fallidos
        """
        self.logger.info(f"Actualizando vínculos en: {os.path.basename(db_path)}")
        
        access_app = None
        success_count = 0
        total_linked_tables = 0
        missing_databases = set()  # Usar set para evitar duplicados
        failed_links = []  # Lista detallada de vínculos fallidos
        
        try:
            # Inicializar COM
            pythoncom.CoInitialize()
            
            # Crear aplicación Access en modo completamente silencioso
            access_app = win32com.client.Dispatch("Access.Application")
            access_app.Visible = False
            access_app.UserControl = False
            
            # Abrir base de datos en modo exclusivo con contraseña
            if self.db_password:
                access_app.OpenCurrentDatabase(db_path, True, self.db_password)
            else:
                access_app.OpenCurrentDatabase(db_path, True)
            
            # Suprimir todos los mensajes y diálogos
            access_app.DoCmd.SetWarnings(False)
            
            # Obtener referencia a la base de datos actual
            db = access_app.CurrentDb()
            
            self.logger.info(f"  Analizando tablas vinculadas...")
            
            # Iterar sobre todas las definiciones de tabla
            for i in range(db.TableDefs.Count):
                table_def = db.TableDefs(i)
                table_name = table_def.Name
                
                # Solo procesar tablas vinculadas (que tienen Connect property)
                if hasattr(table_def, 'Connect') and table_def.Connect:
                    connect_string = table_def.Connect
                    
                    # Verificar si es un enlace a otra base Access
                    if connect_string.startswith("MS Access;"):
                        total_linked_tables += 1
                        
                        # Extraer la ruta actual de la cadena de conexión
                        if 'DATABASE=' in connect_string:
                            current_db_path = connect_string.split('DATABASE=')[1]
                            if ';' in current_db_path:
                                current_db_path = current_db_path.split(';')[0]
                            
                            self.logger.debug(f"    Tabla vinculada: {table_name}")
                            self.logger.debug(f"      Ruta actual: {current_db_path}")
                            
                            # Determinar nueva ruta local
                            new_local_path = self._convert_to_local_path(current_db_path)
                            
                            if new_local_path and new_local_path != current_db_path:
                                # Verificar que la base de datos local existe
                                if os.path.exists(new_local_path):
                                    try:
                                        # Construir nueva cadena de conexión con contraseña si es necesario
                                        if new_local_path.endswith('.accdb') and hasattr(self, 'db_password'):
                                            new_connect = f"MS Access;DATABASE={new_local_path};PWD={self.db_password}"
                                        else:
                                            new_connect = f"MS Access;DATABASE={new_local_path}"
                                        
                                        # Actualizar la conexión
                                        table_def.Connect = new_connect
                                        table_def.RefreshLink()
                                        
                                        self.logger.info(f"    [OK] Revinculada: {table_name} -> {os.path.basename(new_local_path)}")
                                        success_count += 1
                                        
                                    except Exception as e:
                                        self.logger.error(f"    [X] Error revinculando {table_name}: {e}")
                                        failed_links.append({
                                            'table_name': table_name,
                                            'current_path': current_db_path,
                                            'target_path': new_local_path,
                                            'error': str(e),
                                            'reason': 'relink_error'
                                        })
                                else:
                                    missing_db_name = os.path.basename(current_db_path)
                                    missing_databases.add(missing_db_name)
                                    self.logger.warning(f"    [X] Base local no existe: {new_local_path}")
                                    failed_links.append({
                                        'table_name': table_name,
                                        'current_path': current_db_path,
                                        'target_path': new_local_path,
                                        'error': 'Base de datos local no encontrada',
                                        'reason': 'missing_database'
                                    })
                            else:
                                if not new_local_path:
                                    # No se pudo convertir la ruta
                                    failed_links.append({
                                        'table_name': table_name,
                                        'current_path': current_db_path,
                                        'target_path': '',
                                        'error': 'No se pudo determinar ruta local equivalente',
                                        'reason': 'path_conversion_failed'
                                    })
                                else:
                                    self.logger.debug(f"    [INFO] No requiere cambio: {table_name}")
            
            if total_linked_tables == 0:
                self.logger.info("  [INFO] No se encontraron tablas vinculadas a bases Access")
                return True, [], []
            
            self.logger.info(f"  [INFO] Vínculos procesados: {success_count}/{total_linked_tables} exitosos")
            
            return success_count == total_linked_tables, list(missing_databases), failed_links
            
        except Exception as e:
            self.logger.error(f"  [X] Error actualizando vínculos: {e}")
            return False, list(missing_databases), failed_links
            
        finally:
            # Cerrar base de datos y aplicación de forma silenciosa
            try:
                if access_app:
                    access_app.DoCmd.SetWarnings(True)
                    access_app.CloseCurrentDatabase()
                    access_app.Quit()
            except Exception:
                # Ignorar errores al cerrar la aplicación Access
                pass
            
            # Limpiar COM
            try:
                pythoncom.CoUninitialize()
            except Exception:
                # Ignorar errores al limpiar COM
                pass
    
    def _convert_to_local_path(self, remote_path: str) -> str:
        """
        Convierte una ruta remota a su equivalente local usando las variables del .env
        
        Args:
            remote_path: Ruta remota (de oficina)
            
        Returns:
            str: Ruta local equivalente o cadena vacía si no se puede convertir
        """
        # Normalizar ruta
        remote_path = remote_path.replace('/', '\\').strip()
        
        # Buscar coincidencia exacta con rutas de oficina conocidas
        for db_name, (office_var, local_var, filename) in self.databases.items():
            office_path = os.getenv(office_var, '').replace('/', '\\').strip()
            
            if office_path and remote_path.lower() == office_path.lower():
                local_path = os.getenv(local_var)
                if local_path:
                    if not os.path.isabs(local_path):
                        local_path = str(self.project_root / local_path)
                    return local_path.replace('/', '\\')
        
        # Si no se encuentra coincidencia exacta, intentar por nombre de archivo
        remote_filename = os.path.basename(remote_path)
        for db_name, (office_var, local_var, expected_filename) in self.databases.items():
            if remote_filename.lower() == expected_filename.lower():
                local_path = os.getenv(local_var)
                if local_path:
                    if not os.path.isabs(local_path):
                        local_path = str(self.project_root / local_path)
                    return local_path.replace('/', '\\')
        
        # Intentar buscar por coincidencia parcial en el nombre del archivo
        for db_name, (office_var, local_var, expected_filename) in self.databases.items():
            # Extraer nombre base sin extensión
            remote_base = os.path.splitext(remote_filename)[0].lower()
            expected_base = os.path.splitext(expected_filename)[0].lower()
            
            if remote_base in expected_base or expected_base in remote_base:
                local_path = os.getenv(local_var)
                if local_path:
                    if not os.path.isabs(local_path):
                        local_path = str(self.project_root / local_path)
                    self.logger.info(f"Coincidencia parcial encontrada: {remote_filename} -> {expected_filename}")
                    return local_path.replace('/', '\\')
        
        self.logger.warning(f"No se pudo convertir ruta remota a local: {remote_path}")
        return ""
    
    def update_all_database_links(self) -> bool:
        """
        Actualiza vínculos en todas las bases de datos locales
        
        Returns:
            bool: True si todas las actualizaciones fueron exitosas
        """
        self.logger.info("=== Iniciando actualización de vínculos ===")
        success_count = 0
        total_count = 0
        all_missing_databases = set()
        all_failed_links = []
        
        for db_name, (office_var, local_var, filename) in self.databases.items():
            local_path = os.getenv(local_var)
            
            if not local_path:
                self.logger.warning(f"Variable local no encontrada para {db_name}")
                continue
            
            # Convertir a ruta absoluta
            if not os.path.isabs(local_path):
                local_path = str(self.project_root / local_path)
            
            if not os.path.exists(local_path):
                self.logger.warning(f"Base de datos local no encontrada: {local_path}")
                continue
            
            total_count += 1
            
            try:
                success, missing_dbs, failed_links = self.update_database_links(local_path)
                if success:
                    success_count += 1
                
                # Agregar bases de datos faltantes al conjunto global
                all_missing_databases.update(missing_dbs)
                
                # Agregar vínculos fallidos a la lista global
                for failed_link in failed_links:
                    failed_link['source_database'] = db_name
                    all_failed_links.append(failed_link)
                
            except Exception as e:
                self.logger.error(f"Error actualizando vínculos en {db_name}: {e}")
        
        # Mostrar resumen final
        self.logger.info(f"=== Actualización de vínculos completada: {success_count}/{total_count} exitosas ===")
        
        # Mostrar resumen detallado de problemas
        if all_failed_links or all_missing_databases:
            self._show_detailed_link_summary(all_failed_links, all_missing_databases)
        
        return success_count == total_count
    
    def _show_detailed_link_summary(self, failed_links: list[dict], missing_databases: set[str]):
        """
        Muestra un resumen detallado de los vínculos que fallaron y las bases de datos faltantes
        
        Args:
            failed_links: Lista de vínculos fallidos con detalles
            missing_databases: Conjunto de nombres de bases de datos faltantes
        """
        self.logger.warning("")
        self.logger.warning("=" * 80)
        self.logger.warning("[RESUMEN] RESUMEN DETALLADO DE PROBLEMAS DE VINCULACION")
        self.logger.warning("=" * 80)
        
        if missing_databases:
            self.logger.warning("")
            self.logger.warning("[DB] BASES DE DATOS FALTANTES:")
            self.logger.warning("Las siguientes bases de datos no se encontraron localmente:")
            for missing_db in sorted(missing_databases):
                self.logger.warning(f"   [X] {missing_db}")
            self.logger.warning("")
            self.logger.warning("[!] ACCION REQUERIDA: Copie estas bases de datos desde la oficina")
            self.logger.warning("   al directorio 'dbs-locales' para completar la revinculacion.")
        
        if failed_links:
            self.logger.warning("")
            self.logger.warning("[LINK] VINCULOS FALLIDOS DETALLADOS:")
            
            # Agrupar por razón del fallo
            grouped_failures = {}
            for link in failed_links:
                reason = link['reason']
                if reason not in grouped_failures:
                    grouped_failures[reason] = []
                grouped_failures[reason].append(link)
            
            for reason, links in grouped_failures.items():
                if reason == 'missing_database':
                    self.logger.warning("")
                    self.logger.warning("   [FOLDER] TABLAS QUE REQUIEREN BASES DE DATOS FALTANTES:")
                    for link in links:
                        self.logger.warning(f"      * Tabla: {link['table_name']}")
                        self.logger.warning(f"        Base origen: {link['source_database']}")
                        self.logger.warning(f"        Ruta remota: {link['current_path']}")
                        self.logger.warning(f"        Ruta local esperada: {link['target_path']}")
                        self.logger.warning("")
                
                elif reason == 'path_conversion_failed':
                    self.logger.warning("")
                    self.logger.warning("   [SEARCH] TABLAS CON RUTAS NO RECONOCIDAS:")
                    for link in links:
                        self.logger.warning(f"      * Tabla: {link['table_name']}")
                        self.logger.warning(f"        Base origen: {link['source_database']}")
                        self.logger.warning(f"        Ruta remota: {link['current_path']}")
                        self.logger.warning(f"        Problema: {link['error']}")
                        self.logger.warning("")
                    self.logger.warning("   [!] ACCION REQUERIDA: Agregue estas bases de datos al archivo .env")
                
                elif reason == 'relink_error':
                    self.logger.warning("")
                    self.logger.warning("   [WARNING] ERRORES DE REVINCULACION:")
                    for link in links:
                        self.logger.warning(f"      * Tabla: {link['table_name']}")
                        self.logger.warning(f"        Base origen: {link['source_database']}")
                        self.logger.warning(f"        Ruta remota: {link['current_path']}")
                        self.logger.warning(f"        Ruta local: {link['target_path']}")
                        self.logger.warning(f"        Error: {link['error']}")
                        self.logger.warning("")
        
        # Resumen de acciones
        self.logger.warning("")
        self.logger.warning("[ACTIONS] RESUMEN DE ACCIONES REQUERIDAS:")
        
        if missing_databases:
            self.logger.warning("   1. Copiar las siguientes bases de datos desde la oficina:")
            for missing_db in sorted(missing_databases):
                # Buscar la ruta de oficina correspondiente
                office_path = self._find_office_path_for_database(missing_db)
                if office_path:
                    self.logger.warning(f"      * {missing_db}")
                    self.logger.warning(f"        Desde: {office_path}")
                    self.logger.warning(f"        Hacia: dbs-locales/{missing_db}")
                else:
                    self.logger.warning(f"      * {missing_db} (ruta de oficina no encontrada)")
        
        unrecognized_paths = [link['current_path'] for link in failed_links if link['reason'] == 'path_conversion_failed']
        if unrecognized_paths:
            self.logger.warning("   2. Agregar al archivo .env las siguientes bases de datos:")
            for path in set(unrecognized_paths):
                db_name = os.path.basename(path)
                suggested_name = os.path.splitext(db_name)[0].upper()
                self.logger.warning(f"      * OFFICE_DB_{suggested_name}={path}")
                self.logger.warning(f"      * LOCAL_DB_{suggested_name}=dbs-locales/{db_name}")
        
        self.logger.warning("")
        self.logger.warning("=" * 80)
    
    def _find_office_path_for_database(self, database_filename: str) -> str:
        """
        Busca la ruta de oficina para un nombre de archivo de base de datos
        
        Args:
            database_filename: Nombre del archivo de base de datos
            
        Returns:
            str: Ruta de oficina si se encuentra, cadena vacía si no
        """
        for db_name, (office_var, local_var, filename) in self.databases.items():
            if filename.lower() == database_filename.lower():
                return os.getenv(office_var, '')
        return ''

    def setup_environment(self, force_links_only: bool = False) -> bool:
        """
        Ejecuta el proceso completo de configuración del entorno local
        
        Args:
            force_links_only: Si es True, solo actualiza vínculos sin copiar bases de datos
        
        Returns:
            bool: True si todo el proceso fue exitoso
        """
        self.logger.info("[START] Iniciando configuracion del entorno local")
        
        try:
            # Mostrar configuración descubierta
            self.show_configuration()
            
            # Verificar accesibilidad de red ANTES de proceder (solo si no es modo force_links_only)
            if not force_links_only:
                if not self._check_network_accessibility():
                    self.logger.error("[X] No se puede acceder a las ubicaciones de red de oficina")
                    self.logger.warning("   Opciones disponibles:")
                    self.logger.warning("   1. Ejecutar desde la red de oficina")
                    self.logger.warning("   2. Usar modo 'solo vinculos' si ya tienes las bases de datos locales")
                    self.logger.warning("   3. Verificar conectividad de red")
                    return False
                
                self.logger.info("[OK] Ubicaciones de red accesibles, continuando...")
                
                # Paso 1: Copiar bases de datos
                copy_success = self.copy_databases()
                
                if not copy_success:
                    self.logger.warning("[!] Algunas copias fallaron, continuando con actualizacion de vinculos...")
            else:
                self.logger.info("[LINK] Modo 'solo vinculos' activado - saltando copia de bases de datos")
                copy_success = True
            
            # Paso 2: Actualizar vínculos
            links_success = self.update_all_database_links()
            
            # Resultado final
            if copy_success and links_success:
                self.logger.info("[OK] Configuracion del entorno local completada exitosamente")
                return True
            else:
                self.logger.warning("[!] Configuracion completada con algunos errores")
                return False
                
        except Exception as e:
            self.logger.error(f"[X] Error en configuracion del entorno: {e}")
            return False

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Configuración del entorno local - Copia bases de datos y actualiza vínculos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python setup_local_environment.py                    # Proceso completo
  python setup_local_environment.py --links-only       # Solo actualizar vínculos
  python setup_local_environment.py --check-network    # Solo verificar red
        """
    )
    
    parser.add_argument(
        '--links-only', 
        action='store_true',
        help='Solo actualizar vínculos de tablas (no copiar bases de datos)'
    )
    
    parser.add_argument(
        '--check-network', 
        action='store_true',
        help='Solo verificar accesibilidad de red y mostrar configuración'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CONFIGURACIÓN DEL ENTORNO LOCAL")
    print("=" * 60)
    print()
    
    try:
        setup = LocalEnvironmentSetup()
        
        if args.check_network:
            # Solo verificar red y mostrar configuración
            setup.show_configuration()
            network_ok = setup._check_network_accessibility()
            
            print()
            print("=" * 80)
            if network_ok:
                print("[OK] VERIFICACION DE RED EXITOSA")
                print("Las ubicaciones de red son accesibles")
            else:
                print("[X] PROBLEMAS DE CONECTIVIDAD DE RED")
                print("Algunas ubicaciones no son accesibles")
            print("=" * 80)
            
            return 0 if network_ok else 1
        
        # Ejecutar configuración completa o solo vínculos
        success = setup.setup_environment(force_links_only=args.links_only)
        
        print()
        print("=" * 60)
        if success:
            print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
            if args.links_only:
                print("Los vinculos de tablas han sido actualizados")
            else:
                print("El entorno local esta listo para usar")
        else:
            print("[!] PROCESO COMPLETADO CON ERRORES")
            print("Revisa el log para mas detalles")
        print("=" * 60)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n[X] Proceso cancelado por el usuario")
        return 1
    except Exception as e:
        print(f"\n[X] Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit(main())