"""
Configuración del proyecto para manejo de diferentes entornos
"""
import os
import platform
from pathlib import Path
from dotenv import load_dotenv


class Config:
    def get_db_correos_connection_string(self, with_password=True) -> str:
        """Retorna la cadena de conexión para la base de datos de Correos"""
        if with_password and self.db_password:
            return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_correos_path};PWD={self.db_password};"
        else:
            return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_correos_path};"
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
        self.database_mode = os.getenv('DATABASE_MODE', 'auto')  # auto, access, sqlite
        
        # Configuración de rutas según el entorno y modo de BD
        if self.database_mode == 'sqlite':
            # Forzar uso de SQLite
            self.db_brass_path = self.root_dir / 'dbs-sqlite/Gestion_Brass_Gestion_Datos.sqlite'
            self.db_tareas_path = self.root_dir / 'dbs-sqlite/Tareas_datos1.sqlite'
            self.db_correos_path = self.root_dir / 'dbs-sqlite/correos_datos.sqlite'
            self.css_file_path = self.root_dir / os.getenv('LOCAL_CSS_FILE', 'herramientas/CSS.txt')
        elif self.environment == 'local':
            self.db_brass_path = self.root_dir / os.getenv('LOCAL_DB_BRASS', 'dbs-locales/Gestion_Brass_Gestion_Datos.accdb')
            self.db_tareas_path = self.root_dir / os.getenv('LOCAL_DB_TAREAS', 'dbs-locales/Tareas_datos1.accdb')
            self.db_correos_path = self.root_dir / os.getenv('LOCAL_DB_CORREOS', 'dbs-locales/correos_datos.accdb')
            self.css_file_path = self.root_dir / os.getenv('LOCAL_CSS_FILE', 'herramientas/CSS.txt')
        else:  # oficina
            self.db_brass_path = Path(os.getenv('OFFICE_DB_BRASS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Gestion_Brass_Gestion_Datos.accdb'))
            self.db_tareas_path = Path(os.getenv('OFFICE_DB_TAREAS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb'))
            self.db_correos_path = Path(os.getenv('OFFICE_DB_CORREOS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb'))
            self.css_file_path = Path(os.getenv('OFFICE_CSS_FILE', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\CSS.txt'))
        
        # Directorios para el nuevo sistema
        self.sqlite_dir = self.root_dir / 'dbs-sqlite'
        self.logs_dir = self.root_dir / 'logs'
        
        # Configuración de correo
        self.default_recipient = os.getenv('DEFAULT_RECIPIENT', 'admin@empresa.com')
        self.smtp_use_local = os.getenv('SMTP_USE_LOCAL', 'false').lower() == 'true'
        self.smtp_user = os.getenv('SMTP_USER', 'noreply@empresa.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        # Configurar servidor SMTP según entorno
        if self.smtp_use_local or self.environment == 'local':
            # Servidor SMTP local para desarrollo
            self.smtp_server = os.getenv('SMTP_SERVER', 'localhost')
            self.smtp_port = int(os.getenv('SMTP_PORT', '1025'))
            self.smtp_auth = False
            self.smtp_tls = False
        else:
            # Servidor SMTP de oficina
            self.smtp_server = os.getenv('SMTP_SERVER', '10.73.54.85')
            self.smtp_port = int(os.getenv('SMTP_PORT', '25'))
            self.smtp_auth = False
            self.smtp_tls = False
        
        # Configuración de logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = self.logs_dir / os.getenv('LOG_FILE', 'app.log')
        
        # Crear directorios necesarios
        self._ensure_directories()
        
    def _is_running_in_docker(self) -> bool:
        """Detecta si la aplicación está ejecutándose en Docker"""
        return (
            os.path.exists('/.dockerenv') or 
            os.getenv('DOCKER_CONTAINER') == 'true' or
            os.path.exists('/app')  # Directorio típico en Linux containers
        )
    
    def _ensure_directories(self):
        """Crea directorios necesarios si no existen"""
        for directory in [self.sqlite_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
    def is_demo_mode(self) -> bool:
        """Retorna True si estamos en modo demo (Docker sin Access)"""
        return self.is_docker or self.database_mode == 'sqlite'
    
    def get_database_path(self, db_type: str) -> Path:
        """Retorna la ruta apropiada según el tipo de BD y entorno"""
        if db_type == 'brass':
            return self.db_brass_path
        elif db_type == 'tareas':
            return self.db_tareas_path
        elif db_type == 'correos':
            return self.db_correos_path
        else:
            raise ValueError(f"Tipo de BD no soportado: {db_type}")
        
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
