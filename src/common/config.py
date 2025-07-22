"""
Configuración del proyecto para manejo de diferentes entornos
"""
import os
import platform
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Clase para manejar la configuración del proyecto"""
    
    def __init__(self):
        # Cargar variables de entorno desde .env
        load_dotenv()
        
        # Directorio raíz del proyecto (dos niveles arriba desde src/common/)
        self.root_dir = Path(__file__).parent.parent.parent
        
        # Detectar si estamos en Docker
        self.is_docker = self._is_running_in_docker()
        
        # Configuración general
        self.environment = os.getenv('ENVIRONMENT', 'local')
        self.db_password = os.getenv('DB_PASSWORD', 'dpddpd')
        
        # Configuración de rutas según el entorno
        if self.environment == 'local':
            self.db_brass_path = self.root_dir / os.getenv('LOCAL_DB_BRASS')
            self.db_tareas_path = self.root_dir / os.getenv('LOCAL_DB_TAREAS')
            self.css_file_path = self.root_dir / os.getenv('LOCAL_CSS_FILE')
        else:  # oficina
            self.db_brass_path = Path(os.getenv('OFFICE_DB_BRASS'))
            self.db_tareas_path = Path(os.getenv('OFFICE_DB_TAREAS'))
            self.css_file_path = Path(os.getenv('OFFICE_CSS_FILE'))
        
        # Configuración de correo
        self.default_recipient = os.getenv('DEFAULT_RECIPIENT')
        
        # Configuración de logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = self.root_dir / os.getenv('LOG_FILE', 'logs/brass.log')
        
    def _is_running_in_docker(self) -> bool:
        """Detecta si la aplicación está ejecutándose en Docker"""
        return (
            os.path.exists('/.dockerenv') or 
            os.getenv('DOCKER_CONTAINER') == 'true' or
            os.path.exists('C:\\app')  # Directorio típico en Windows containers
        )
        
    def is_demo_mode(self) -> bool:
        """Retorna True si estamos en modo demo (Docker)"""
        return self.environment == 'docker_demo'
        
    def get_db_brass_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos BRASS"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_brass_path};PWD={self.db_password};"
    
    def get_db_tareas_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos de Tareas"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_tareas_path};PWD={self.db_password};"


# Instancia global de configuración
config = Config()

def reload_config():
    """Recargar la configuración desde las variables de entorno"""
    global config
    
    # Recargar variables de entorno desde .env
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    # Crear nueva instancia de configuración
    config = Config()
    
    return config
