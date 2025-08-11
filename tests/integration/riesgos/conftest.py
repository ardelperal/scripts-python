"""Configuración específica para tests de integración de Riesgos
"""

import pytest

from common.config import config
from common.database import AccessDatabase


@pytest.fixture
def local_db_connections():
    """
    Fixture que proporciona conexiones a bases de datos locales
    independientemente del entorno configurado en .env
    """
    # Forzar el uso de bases de datos locales
    connections = {
        "riesgos": AccessDatabase(
            f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
            f"DBQ={config.get_local_db_path('riesgos')};PWD={config.db_password};"
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
def local_riesgos_manager():
    """
    Fixture que proporciona una instancia de RiesgosManager configurada
    específicamente para usar bases de datos locales en las pruebas
    """

    # Crear una instancia personalizada que use conexiones locales
    class LocalRiesgosManager:
        def __init__(self):
            # Conexiones forzadas a bases de datos locales
            riesgos_local_path = config.get_local_db_path("riesgos")
            tareas_local_path = config.get_local_db_path("tareas")

            self.db = AccessDatabase(
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
                f"DBQ={riesgos_local_path};PWD={config.db_password};"
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

        # Importar todos los métodos de RiesgosManager
        def __getattr__(self, name):
            from riesgos.riesgos_manager import RiesgosManager

            original_manager = RiesgosManager()
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

    return LocalRiesgosManager()
