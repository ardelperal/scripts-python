"""
Configuración específica para tests de integración de Expedientes
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
        'expedientes': AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={config.get_local_db_path('expedientes')};PWD={config.db_password};"),
        'tareas': AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={config.get_local_db_path('tareas')};PWD={config.db_password};"),
        'correos': AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={config.get_local_db_path('correos')};PWD={config.db_password};")
    }
    
    return connections


@pytest.fixture
def local_expedientes_manager():
    """
    Fixture que proporciona una instancia de ExpedientesManager configurada
    específicamente para usar bases de datos locales en las pruebas
    """
    # Crear una instancia personalizada que use conexiones locales
    class LocalExpedientesManager:
        def __init__(self):
            # Conexiones forzadas a bases de datos locales
            expedientes_local_path = config.get_local_db_path('expedientes')
            tareas_local_path = config.get_local_db_path('tareas')
            
            self.db = AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={expedientes_local_path};PWD={config.db_password};")
            self.tareas_db = AccessDatabase(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={tareas_local_path};PWD={config.db_password};")
            
            # Cargar CSS desde archivo local
            css_local_path = config.root_dir / 'herramientas' / 'CSS1.css'
            try:
                with open(css_local_path, 'r', encoding='utf-8') as f:
                    self.css_content = f.read()
            except FileNotFoundError:
                self.css_content = ""
        
        # Importar todos los métodos de ExpedientesManager
        def __getattr__(self, name):
            from expedientes.expedientes_manager import ExpedientesManager
            original_manager = ExpedientesManager()
            method = getattr(original_manager, name)
            
            # Si es un método, reemplazar las conexiones de BD
            if callable(method):
                def wrapper(*args, **kwargs):
                    # Temporalmente reemplazar las conexiones
                    original_db = original_manager.db
                    original_tareas_db = original_manager.tareas_db
                    
                    original_manager.db = self.db
                    original_manager.tareas_db = self.tareas_db
                    
                    try:
                        result = method(*args, **kwargs)
                        return result
                    finally:
                        # Restaurar conexiones originales
                        original_manager.db = original_db
                        original_manager.tareas_db = original_tareas_db
                
                return wrapper
            else:
                return method
    
    return LocalExpedientesManager()