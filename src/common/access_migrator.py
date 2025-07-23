"""
Migrador de bases de datos Access (.accdb) a SQLite para uso en Docker
Permite mantener funcionalidad completa sin usar Windows containers pesados
"""
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import os
import tempfile

logger = logging.getLogger(__name__)


class AccessToSQLiteMigrator:
    """Migra bases de datos Access a SQLite para compatibilidad con Docker Linux"""
    
    def __init__(self):
        self.temp_dir = None
        
    def migrate_database(self, access_file: Path, sqlite_file: Path) -> bool:
        """
        Migra una base de datos Access completa a SQLite
        
        Args:
            access_file: Ruta al archivo .accdb
            sqlite_file: Ruta de destino para SQLite
            
        Returns:
            bool: True si la migración fue exitosa
        """
        try:
            if not access_file.exists():
                logger.warning(f"Archivo Access no encontrado: {access_file}")
                return False
                
            logger.info(f"Iniciando migración: {access_file} → {sqlite_file}")
            
            # Crear directorio de destino si no existe
            sqlite_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Intentar diferentes métodos de migración
            success = (
                self._migrate_with_pandas_access(access_file, sqlite_file) or
                self._migrate_with_mdbtools(access_file, sqlite_file) or
                self._migrate_with_pyodbc_fallback(access_file, sqlite_file)
            )
            
            if success:
                logger.info(f"Migración completada exitosamente: {sqlite_file}")
                self._verify_migration(sqlite_file)
            else:
                logger.error(f"Falló la migración de {access_file}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error durante migración: {e}")
            return False
    
    def _migrate_with_pandas_access(self, access_file: Path, sqlite_file: Path) -> bool:
        """Migración usando pandas y pyodbc (Windows) o pandas-access"""
        try:
            import pandas as pd
            
            # En Windows, usar pyodbc
            if os.name == 'nt':
                return self._migrate_with_pyodbc(access_file, sqlite_file)
            
            # En Linux, intentar con pandas-access si está disponible
            try:
                import pandas_access
                logger.info("Usando pandas-access para migración")
                
                # Leer todas las tablas del Access
                tables = self._get_access_tables_with_pandas_access(access_file)
                
                with sqlite3.connect(sqlite_file) as conn:
                    for table_name in tables:
                        df = pandas_access.read_table(str(access_file), table_name)
                        df.to_sql(table_name, conn, if_exists='replace', index=False)
                        logger.info(f"Tabla migrada: {table_name} ({len(df)} filas)")
                
                return True
                
            except ImportError:
                logger.debug("pandas-access no disponible")
                return False
                
        except Exception as e:
            logger.debug(f"Migración con pandas falló: {e}")
            return False
    
    def _migrate_with_mdbtools(self, access_file: Path, sqlite_file: Path) -> bool:
        """Migración usando mdbtools (Linux)"""
        try:
            # Verificar si mdbtools está disponible
            subprocess.run(['mdb-tables', '--help'], 
                          capture_output=True, check=True)
            
            logger.info("Usando mdbtools para migración")
            
            # Obtener lista de tablas
            result = subprocess.run(['mdb-tables', str(access_file)], 
                                  capture_output=True, text=True, check=True)
            
            tables = result.stdout.strip().split()
            
            with sqlite3.connect(sqlite_file) as conn:
                for table_name in tables:
                    # Exportar tabla como CSV
                    csv_result = subprocess.run([
                        'mdb-export', str(access_file), table_name
                    ], capture_output=True, text=True, check=True)
                    
                    # Importar CSV a SQLite usando pandas
                    from io import StringIO
                    df = pd.read_csv(StringIO(csv_result.stdout))
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    logger.info(f"Tabla migrada: {table_name} ({len(df)} filas)")
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"mdbtools no disponible o falló: {e}")
            return False
    
    def _migrate_with_pyodbc_fallback(self, access_file: Path, sqlite_file: Path) -> bool:
        """Migración fallback usando pyodbc (solo Windows)"""
        if os.name != 'nt':
            return False
            
        try:
            import pyodbc
            
            # Intentar conexión directa a Access
            conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_file};"
            
            with pyodbc.connect(conn_str) as access_conn:
                cursor = access_conn.cursor()
                
                # Obtener lista de tablas
                tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
                
                with sqlite3.connect(sqlite_file) as sqlite_conn:
                    for table_name in tables:
                        # Leer tabla completa
                        df = pd.read_sql(f"SELECT * FROM [{table_name}]", access_conn)
                        df.to_sql(table_name, sqlite_conn, if_exists='replace', index=False)
                        logger.info(f"Tabla migrada: {table_name} ({len(df)} filas)")
            
            return True
            
        except Exception as e:
            logger.debug(f"Migración con pyodbc falló: {e}")
            return False
    
    def _get_access_tables_with_pandas_access(self, access_file: Path) -> List[str]:
        """Obtiene lista de tablas usando pandas-access"""
        try:
            import pandas_access
            return pandas_access.list_tables(str(access_file))
        except:
            return []
    
    def _verify_migration(self, sqlite_file: Path) -> bool:
        """Verifica que la migración fue exitosa"""
        try:
            with sqlite3.connect(sqlite_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                logger.info(f"Migración verificada: {len(tables)} tablas en SQLite")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    logger.debug(f"  - {table[0]}: {count} filas")
                
                return len(tables) > 0
                
        except Exception as e:
            logger.error(f"Error verificando migración: {e}")
            return False


def migrate_all_access_databases(source_dir: Path, target_dir: Path) -> Dict[str, bool]:
    """
    Migra todas las bases de datos Access de un directorio
    
    Args:
        source_dir: Directorio con archivos .accdb
        target_dir: Directorio destino para archivos .sqlite
        
    Returns:
        Dict con resultados de migración por archivo
    """
    migrator = AccessToSQLiteMigrator()
    results = {}
    
    # Buscar archivos .accdb
    access_files = list(source_dir.glob('*.accdb'))
    
    if not access_files:
        logger.warning(f"No se encontraron archivos .accdb en {source_dir}")
        return results
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for access_file in access_files:
        sqlite_file = target_dir / f"{access_file.stem}.sqlite"
        success = migrator.migrate_database(access_file, sqlite_file)
        results[access_file.name] = success
    
    return results


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Migrar bases de datos de prueba
    source_dir = Path("dbs-locales")
    target_dir = Path("dbs-sqlite")
    
    results = migrate_all_access_databases(source_dir, target_dir)
    
    print("\n🔄 Resultados de migración:")
    for file, success in results.items():
        status = "✅ Éxito" if success else "❌ Falló"
        print(f"  {file} → {status}")
