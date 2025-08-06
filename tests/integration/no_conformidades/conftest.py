"""Configuración de fixtures para tests de integración de No Conformidades."""
import pytest
import os
from src.no_conformidades.no_conformidades_manager import NoConformidadesManager
from src.common.database import AccessDatabase
from src.common.config import Config

config = Config()


@pytest.fixture(scope="class")
def verify_local_environment():
    """Verificar que las bases de datos locales están disponibles"""
    # Forzar el uso de bases de datos locales independientemente del entorno
    # Las pruebas siempre deben usar las bases de datos locales
    required_dbs = {
        'no_conformidades': config.get_local_db_path('no_conformidades'),
        'tareas': config.get_local_db_path('tareas'),
        'correos': config.get_local_db_path('correos')
    }
    
    missing_dbs = []
    for db_name, db_path in required_dbs.items():
        if not os.path.exists(db_path):
            missing_dbs.append(f"{db_name}: {db_path}")
    
    if missing_dbs:
        pytest.skip(f"Bases de datos locales no encontradas: {', '.join(missing_dbs)}")
    
    return required_dbs


@pytest.fixture(scope="class")
def no_conformidades_manager(verify_local_environment):
    """Crear instancia de NoConformidadesManager configurada para usar bases de datos locales"""
    # Forzar el uso de bases de datos locales para las pruebas
    # Temporalmente sobrescribir las rutas de configuración
    original_paths = {
        'no_conformidades': config.db_no_conformidades_path,
        'tareas': config.db_tareas_path,
        'correos': config.db_correos_path
    }
    
    # Usar las rutas locales
    local_paths = verify_local_environment
    config.db_no_conformidades_path = local_paths['no_conformidades']
    config.db_tareas_path = local_paths['tareas']
    config.db_correos_path = local_paths['correos']
    
    try:
        manager = NoConformidadesManager()
        yield manager
    finally:
        # Restaurar las rutas originales
        config.db_no_conformidades_path = original_paths['no_conformidades']
        config.db_tareas_path = original_paths['tareas']
        config.db_correos_path = original_paths['correos']


@pytest.fixture(scope="class")
def db_connections(verify_local_environment):
    """Crear conexiones directas a las bases de datos locales para verificación"""
    local_paths = verify_local_environment
    connections = {}
    
    try:
        # Crear conexiones usando las rutas locales
        # Usar el método de config para obtener las cadenas de conexión
        connections['no_conformidades'] = AccessDatabase(config.get_db_connection_string('no_conformidades'))
        connections['tareas'] = AccessDatabase(config.get_db_connection_string('tareas'))
        connections['correos'] = AccessDatabase(config.get_db_connection_string('correos'))
        
        yield connections
    finally:
        # Cerrar todas las conexiones
        for conn in connections.values():
            try:
                conn.disconnect()
            except Exception:
                # Ignorar errores al cerrar conexiones
                continue


@pytest.fixture
def real_no_conformidades_manager():
    """
    Fixture que proporciona una instancia real de NoConformidadesManager
    para tests de integración con bases de datos reales.
    """
    return NoConformidadesManager()

@pytest.fixture
def setup_test_database_for_no_conformidades(db_connections):
    """
    Prepara la base de datos de No Conformidades para las pruebas de notificación.
    Limpia las tablas relevantes e inserta datos de prueba.
    """
    nc_db = db_connections['no_conformidades']
    
    # Limpiar tablas
    nc_db.execute_non_query("DELETE FROM TbNCAccionesRealizadas")
    nc_db.execute_non_query("DELETE FROM TbNCAccionCorrectivas")
    nc_db.execute_non_query("DELETE FROM TbNoConformidades")

    # Insertar datos de prueba
    # (Los datos se insertarán en las pruebas específicas)
    
    yield nc_db
    
    # Limpieza después de la prueba
    nc_db.execute_non_query("DELETE FROM TbNCAccionesRealizadas")
    nc_db.execute_non_query("DELETE FROM TbNCAccionCorrectivas")
    nc_db.execute_non_query("DELETE FROM TbNoConformidades")