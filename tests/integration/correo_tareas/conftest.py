"""
Configuración específica para tests de integración de Correo Tareas
"""
import pytest
import os
from pathlib import Path
from common.database import AccessDatabase
from common.config import config


@pytest.fixture
def local_db_connections():
    """
    Fixture que proporciona conexiones a bases de datos locales
    independientemente del entorno configurado en .env
    """
    # Forzar el uso de bases de datos locales
    connections = {
        'tareas': AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={config.get_local_db_path('tareas')};PWD={config.db_password};"),
        'correos': AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={config.get_local_db_path('correos')};PWD={config.db_password};")
    }
    
    return connections


@pytest.fixture
def local_correo_tareas_manager():
    """
    Fixture que proporciona una instancia de CorreoTareasManager configurada
    específicamente para usar bases de datos locales en las pruebas
    """
    # Crear una instancia personalizada que use conexiones locales
    class LocalCorreoTareasManager:
        def __init__(self):
            # Conexión forzada a base de datos local de tareas
            tareas_local_path = config.get_local_db_path('tareas')
            
            self.db_conn = AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={tareas_local_path};PWD={config.db_password};")
            
            # Configuración SMTP para tests
            self.config = config
            self.smtp_server = config.smtp_server
            self.smtp_port = config.smtp_port
            self.smtp_user = config.smtp_user
            self.smtp_password = getattr(config, 'smtp_password', None)
            self.smtp_tls = getattr(config, 'smtp_tls', False)
        
        # Importar todos los métodos de CorreoTareasManager
        def __getattr__(self, name):
            from correo_tareas.correo_tareas_manager import CorreoTareasManager
            original_manager = CorreoTareasManager()
            method = getattr(original_manager, name)
            
            # Si es un método, reemplazar la conexión de BD
            if callable(method):
                def wrapper(*args, **kwargs):
                    # Temporalmente reemplazar la conexión
                    original_db_conn = original_manager.db_conn
                    
                    original_manager.db_conn = self.db_conn
                    
                    try:
                        result = method(*args, **kwargs)
                        return result
                    finally:
                        # Restaurar conexión original
                        original_manager.db_conn = original_db_conn
                
                return wrapper
            else:
                return method
    
    return LocalCorreoTareasManager()