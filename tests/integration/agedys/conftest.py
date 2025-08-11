"""Configuración específica para tests de integración de AGEDYS
"""

import pytest

from common.config import config
from common.db.database import AccessDatabase


@pytest.fixture
def local_db_connections():
    """
    Fixture que proporciona conexiones a bases de datos locales
    independientemente del entorno configurado en .env
    """
    # Forzar el uso de bases de datos locales
    connections = {
        "agedys": AccessDatabase(
            f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
            f"DBQ={config.get_local_db_path('agedys')};PWD={config.db_password};"
        ),
        "tareas": AccessDatabase(
            f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
            f"DBQ={config.get_local_db_path('tareas')};PWD={config.db_password};"
        ),
        "correos": AccessDatabase(
            f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
            f"DBQ={config.get_local_db_path('correos')};PWD={config.db_password};"
        ),
    }

    return connections


@pytest.fixture
def local_agedys_manager():
    """
    Fixture que proporciona una instancia de AgedysManager configurada
    específicamente para usar bases de datos locales en las pruebas
    """

    # Crear una instancia personalizada que use conexiones locales
    class LocalAgedysManager:
        def __init__(self):
            # Conexiones forzadas a bases de datos locales
            agedys_local_path = config.get_local_db_path("agedys")
            tareas_local_path = config.get_local_db_path("tareas")

            self.db = AccessDatabase(
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
                f"DBQ={agedys_local_path};PWD={config.db_password};"
            )
            self.tareas_db = AccessDatabase(
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
                f"DBQ={tareas_local_path};PWD={config.db_password};"
            )

            # Cargar CSS desde archivo local
            css_local_path = config.root_dir / "herramientas" / "CSS1.css"
            try:
                with open(css_local_path, encoding="utf-8") as f:
                    self.css_content = f.read()
            except FileNotFoundError:
                self.css_content = ""

        # Importar todos los métodos de AgedysManager
        def __getattr__(self, name):
            from agedys.agedys_manager import AgedysManager

            original_manager = AgedysManager()
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

    return LocalAgedysManager()


@pytest.fixture
def real_agedys_manager():
    """
    Fixture que proporciona una instancia real de AgedysManager
    para tests de integración con bases de datos reales.
    DEPRECATED: Usar local_agedys_manager en su lugar
    """
    from agedys.agedys_manager import AgedysManager

    return AgedysManager()
