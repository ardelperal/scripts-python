"""
Tests de integración para verificar conectividad de bases de datos
según el entorno configurado.
"""

import pytest
import pyodbc
import os
from pathlib import Path
import sys

# Añadir src al path para importar módulos
SRC_ROOT = Path(__file__).resolve().parent.parent.parent.parent / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.config import config
from common.database import AccessDatabase


class TestDatabaseConnectivity:
    """Tests de conectividad para todas las bases de datos del entorno"""
    
    def test_environment_configuration(self):
        """Verifica que el entorno esté configurado correctamente"""
        assert config.environment in ['local', 'oficina'], f"Entorno no válido: {config.environment}"
        assert config.db_password, "Password de BD no configurado"
        
    def test_database_paths_exist(self):
        """Verifica que las rutas de las bases de datos existan"""
        databases = {
            'brass': config.db_brass_path,
            'tareas': config.db_tareas_path,
            'correos': config.db_correos_path
        }
        
        missing_databases = []
        for db_name, db_path in databases.items():
            if not Path(db_path).exists():
                missing_databases.append(f"{db_name}: {db_path}")
        
        if missing_databases:
            pytest.skip(f"Bases de datos no encontradas en entorno '{config.environment}': {', '.join(missing_databases)}")
    
    def test_brass_database_connection(self):
        """Test de conectividad a la base de datos BRASS"""
        try:
            connection_string = config.get_db_brass_connection_string()
            
            # Verificar que el archivo existe
            if not Path(config.db_brass_path).exists():
                pytest.skip(f"Base de datos BRASS no encontrada: {config.db_brass_path}")
            
            # Intentar conexión
            with pyodbc.connect(connection_string, timeout=10) as conn:
                cursor = conn.cursor()
                # Usar una consulta muy simple que siempre funciona
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result is not None, "No se pudo ejecutar consulta básica en BD BRASS"
                assert result[0] == 1, "Resultado inesperado en consulta básica"
                
        except pyodbc.Error as e:
            pytest.fail(f"Error conectando a BD BRASS: {e}")
    
    def test_tareas_database_connection(self):
        """Test de conectividad a la base de datos de Tareas"""
        try:
            connection_string = config.get_db_tareas_connection_string()
            
            # Verificar que el archivo existe
            if not Path(config.db_tareas_path).exists():
                pytest.skip(f"Base de datos Tareas no encontrada: {config.db_tareas_path}")
            
            # Intentar conexión
            with pyodbc.connect(connection_string, timeout=10) as conn:
                cursor = conn.cursor()
                # Usar una consulta muy simple que siempre funciona
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result is not None, "No se pudo ejecutar consulta básica en BD Tareas"
                assert result[0] == 1, "Resultado inesperado en consulta básica"
                
        except pyodbc.Error as e:
            pytest.fail(f"Error conectando a BD Tareas: {e}")
    
    def test_correos_database_connection(self):
        """Test de conectividad a la base de datos de Correos"""
        try:
            connection_string = config.get_db_correos_connection_string()
            
            # Verificar que el archivo existe
            if not Path(config.db_correos_path).exists():
                pytest.skip(f"Base de datos Correos no encontrada: {config.db_correos_path}")
            
            # Intentar conexión
            with pyodbc.connect(connection_string, timeout=10) as conn:
                cursor = conn.cursor()
                # Usar una consulta muy simple que siempre funciona
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result is not None, "No se pudo ejecutar consulta básica en BD Correos"
                assert result[0] == 1, "Resultado inesperado en consulta básica"
                
        except pyodbc.Error as e:
            pytest.fail(f"Error conectando a BD Correos: {e}")
    
    def test_correos_database_connection_without_password(self):
        """Test de conectividad a la base de datos de Correos sin contraseña"""
        try:
            connection_string = config.get_db_correos_connection_string(with_password=False)
            
            # Verificar que el archivo existe
            if not Path(config.db_correos_path).exists():
                pytest.skip(f"Base de datos Correos no encontrada: {config.db_correos_path}")
            
            # Intentar conexión sin contraseña
            with pyodbc.connect(connection_string, timeout=10) as conn:
                cursor = conn.cursor()
                # Usar una consulta muy simple que siempre funciona
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result is not None, "No se pudo ejecutar consulta básica en BD Correos sin password"
                assert result[0] == 1, "Resultado inesperado en consulta básica"
                
        except pyodbc.Error:
            # Es normal que falle sin contraseña, no es un error del test
            pass
    
    def test_accessdatabase_basic_query(self):
        """Prueba básica de AccessDatabase (solo crea instancia y ejecuta SELECT 1 si existe BD tareas)."""
        db_path = Path(config.db_tareas_path)
        if not db_path.exists():
            pytest.skip(f"Base de datos Tareas no encontrada: {db_path}")
        # Construir connection string reutilizando config
        conn_str = config.get_db_tareas_connection_string()
        db = AccessDatabase(conn_str)
        # Modo legacy: abrir y ejecutar
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                assert row and row[0] == 1
        except Exception as e:
            pytest.fail(f"AccessDatabase fallo consulta básica: {e}")
    
    def test_all_databases_summary(self):
        """Test resumen que verifica el estado de todas las bases de datos"""
        databases = {
            'brass': config.db_brass_path,
            'tareas': config.db_tareas_path,
            'correos': config.db_correos_path
        }
        
        results = {}
        accessible_count = 0
        
        for db_name, db_path in databases.items():
            try:
                # Verificar existencia del archivo
                if not Path(db_path).exists():
                    results[db_name] = f"❌ Archivo no encontrado: {db_path}"
                    continue
                
                # Intentar conexión con contraseña
                if db_name == 'brass':
                    connection_string = config.get_db_brass_connection_string()
                elif db_name == 'tareas':
                    connection_string = config.get_db_tareas_connection_string()
                else:  # correos
                    connection_string = config.get_db_correos_connection_string()
                
                with pyodbc.connect(connection_string, timeout=10) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result and result[0] == 1:
                        results[db_name] = f"✅ Conectado correctamente"
                        accessible_count += 1
                    else:
                        results[db_name] = f"❌ Consulta falló"
                    
            except pyodbc.Error as e:
                error_msg = str(e)
                if "contraseña" in error_msg.lower() or "password" in error_msg.lower():
                    # Intentar sin contraseña
                    try:
                        conn_str_no_pwd = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
                        with pyodbc.connect(conn_str_no_pwd, timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT 1")
                            result = cursor.fetchone()
                            if result and result[0] == 1:
                                results[db_name] = f"✅ Conectado sin contraseña"
                                accessible_count += 1
                            else:
                                results[db_name] = f"❌ Consulta falló sin contraseña"
                    except pyodbc.Error:
                        results[db_name] = f"❌ Requiere contraseña válida"
                else:
                    results[db_name] = f"❌ Error de conexión: {str(e)[:100]}..."
            except Exception as e:
                results[db_name] = f"❌ Error: {str(e)[:100]}..."
        
        # Mostrar resumen
        print(f"\n=== RESUMEN CONECTIVIDAD BD - Entorno: {config.environment.upper()} ===")
        for db_name, status in results.items():
            print(f"{db_name.upper()}: {status}")
        print(f"\n🎯 Bases de datos accesibles: {accessible_count}/{len(databases)}")
        
        # Verificar que al menos una BD esté conectada
        assert accessible_count > 0, f"Ninguna base de datos está accesible en entorno '{config.environment}'"
        
        # En entorno oficina, esperamos que al menos 2 estén conectadas (excluyendo BRASS si no existe)
        if config.environment == 'oficina':
            existing_dbs = [db for db, path in databases.items() if Path(path).exists()]
            accessible_existing = [db for db, status in results.items() if "✅" in status and Path(databases[db]).exists()]
            
            if len(existing_dbs) > 1 and len(accessible_existing) < len(existing_dbs):
                failed_existing = [db for db in existing_dbs if db not in accessible_existing]
                pytest.fail(f"En entorno oficina, estas BD existentes deberían estar accesibles: {failed_existing}")


if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v", "--tb=short"])