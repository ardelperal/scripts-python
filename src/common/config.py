"""
Configuración del proyecto para manejo de diferentes entornos Windows con Access
"""
import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Clase para manejar la configuración del proyecto"""
    
    def __init__(self):
        # Cargar variables de entorno desde .env
        load_dotenv()
        
        # Directorio raíz del proyecto (dos niveles arriba desde src/common/)
        self.root_dir = Path(__file__).parent.parent.parent
        
        # Configuración general
        self.environment = os.getenv('ENVIRONMENT', 'local')
        self.db_password = os.getenv('DB_PASSWORD', 'dpddpd')
        
        # Configuración de bases de datos
        self.db_paths = {
            'correos': self._get_db_path('CORREOS_DB_PATH', 'Correos_datos.accdb'),
            'brass': self._get_db_path('BRASS_DB_PATH', 'Brass_datos.accdb'),
            'expedientes': self._get_db_path('EXPEDIENTES_DB_PATH', 'Expedientes_datos.accdb'),
            'riesgos': self._get_db_path('RIESGOS_DB_PATH', 'Riesgos_datos.accdb'),
            'no_conformidades': self._get_db_path('NO_CONFORMIDADES_DB_PATH', 'NoConformidades_Datos.accdb'),
            'agedys': self._get_db_path('AGEDYS_DB_PATH', 'Agedys_datos.accdb'),
            'tareas': self._get_db_path('TAREAS_DB_PATH', 'Tareas_datos1.accdb')
        }
        
        # Configuración de rutas según el entorno
        if self.environment == 'local':
            self.db_agedys_path = self.root_dir / os.getenv('LOCAL_DB_AGEDYS', 'dbs-locales/AGEDYS_DATOS.accdb')
            self.db_brass_path = self.root_dir / os.getenv('LOCAL_DB_BRASS', 'dbs-locales/Gestion_Brass_Gestion_Datos.accdb')
            self.db_tareas_path = self.root_dir / os.getenv('LOCAL_DB_TAREAS', 'dbs-locales/Tareas_datos1.accdb')
            self.db_correos_path = self.root_dir / os.getenv('LOCAL_DB_CORREOS', 'dbs-locales/correos_datos.accdb')
            self.db_riesgos_path = self.root_dir / os.getenv('LOCAL_DB_RIESGOS', 'dbs-locales/Gestion_Riesgos_Datos.accdb')
            self.db_expedientes_path = self.root_dir / os.getenv('LOCAL_DB_EXPEDIENTES', 'dbs-locales/Expedientes_datos.accdb')
            self.db_no_conformidades_path = self.root_dir / os.getenv('LOCAL_DB_NO_CONFORMIDADES', 'dbs-locales/NoConformidades_Datos.accdb')
            self.db_lanzadera_path = self.root_dir / os.getenv('LOCAL_DB_LANZADERA', 'dbs-locales/Lanzadera_Datos.accdb')
            # Configuración de CSS
            self.css_classic_file_path = self.root_dir / os.getenv('LOCAL_CSS_CLASSIC_FILE', 'herramientas/CSS.txt')
            self.css_modern_file_path = self.root_dir / os.getenv('LOCAL_CSS_MODERN_FILE', 'herramientas/CSS_moderno.css')
            self.nc_css_style = os.getenv('NC_CSS_STYLE', 'modern')  # 'classic' o 'modern'
        else:  # oficina
            self.db_agedys_path = Path(os.getenv('OFFICE_DB_AGEDYS', r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\Proyectos\AGEDYS_DATOS.accdb'))
            self.db_brass_path = Path(os.getenv('OFFICE_DB_BRASS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Gestion_Brass_Gestion_Datos.accdb'))
            self.db_tareas_path = Path(os.getenv('OFFICE_DB_TAREAS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb'))
            self.db_correos_path = Path(os.getenv('OFFICE_DB_CORREOS', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb'))
            self.db_riesgos_path = Path(os.getenv('OFFICE_DB_RIESGOS', r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\GESTION RIESGOS\Gestion_Riesgos_Datos.accdb'))
            self.db_expedientes_path = Path(os.getenv('OFFICE_DB_EXPEDIENTES', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Expedientes_datos.accdb'))
            self.db_no_conformidades_path = Path(os.getenv('OFFICE_DB_NO_CONFORMIDADES', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\NoConformidades_datos.accdb'))
            self.db_lanzadera_path = Path(os.getenv('OFFICE_DB_LANZADERA', r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\0Lanzadera\Lanzadera_Datos.accdb'))
            # Configuración de CSS
            self.css_classic_file_path = Path(os.getenv('OFFICE_CSS_CLASSIC_FILE', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\CSS.txt'))
            self.css_modern_file_path = Path(os.getenv('OFFICE_CSS_MODERN_FILE', r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\CSS_moderno.css'))
            self.nc_css_style = os.getenv('NC_CSS_STYLE', 'modern')  # 'classic' o 'modern'
        
        # Directorio para logs
        self.logs_dir = self.root_dir / 'logs'
        
        # Configuración de correo
        self.default_recipient = os.getenv('DEFAULT_RECIPIENT', 'admin@empresa.com')
        
        # Configurar servidor SMTP según entorno
        if self.environment == 'local':
            # Servidor SMTP local para desarrollo
            self.smtp_server = os.getenv('LOCAL_SMTP_SERVER', 'localhost')
            self.smtp_port = int(os.getenv('LOCAL_SMTP_PORT', '1025'))
            self.smtp_user = os.getenv('LOCAL_SMTP_USER', 'test@example.com')
            self.smtp_password = os.getenv('LOCAL_SMTP_PASSWORD', '')
            self.smtp_auth = False
            self.smtp_tls = False
        else:
            # Servidor SMTP de oficina
            self.smtp_server = os.getenv('OFFICE_SMTP_SERVER', '10.73.54.85')
            self.smtp_port = int(os.getenv('OFFICE_SMTP_PORT', '25'))
            self.smtp_user = os.getenv('OFFICE_SMTP_USER', '')
            self.smtp_password = os.getenv('OFFICE_SMTP_PASSWORD', '')
            self.smtp_auth = False
            self.smtp_tls = False
        
        # Aplicar sobrescritura de SMTP si está configurada
        # Esto permite usar un servidor alternativo cuando no se puede acceder al de oficina
        if os.getenv('SMTP_OVERRIDE_SERVER'):
            self.smtp_server = os.getenv('SMTP_OVERRIDE_SERVER')
            self.smtp_port = int(os.getenv('SMTP_OVERRIDE_PORT', '25'))
            self.smtp_user = os.getenv('SMTP_OVERRIDE_USER', '')
            self.smtp_password = os.getenv('SMTP_OVERRIDE_PASSWORD', '')
            self.smtp_auth = bool(self.smtp_user)  # Activar auth si hay usuario
            self.smtp_tls = os.getenv('SMTP_OVERRIDE_TLS', 'false').lower() == 'true'
        
        # Configuración de logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = self.logs_dir / os.getenv('LOG_FILE', 'app.log')
        
        # IDs de Aplicaciones
        self.app_id_agedys = int(os.getenv('APP_ID_AGEDYS', '3'))
        self.app_id_brass = int(os.getenv('APP_ID_BRASS', '6'))
        self.app_id_riesgos = int(os.getenv('APP_ID_RIESGOS', '5'))
        self.app_id_noconformidades = int(os.getenv('APP_ID_NOCONFORMIDADES', '8'))
        self.app_id_expedientes = int(os.getenv('APP_ID_EXPEDIENTES', '19'))
        
        # Crear directorios necesarios
        self._ensure_directories()
        
    def _get_db_path(self, env_var: str, default_filename: str) -> Path:
        """Obtiene la ruta de la base de datos según el entorno"""
        if self.environment == 'local':
            return self.root_dir / 'dbs-locales' / default_filename
        else:
            # Para oficina, usar la ruta específica de cada BD
            office_paths = {
                'CORREOS_DB_PATH': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb',
                'BRASS_DB_PATH': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Gestion_Brass_Gestion_Datos.accdb',
                'EXPEDIENTES_DB_PATH': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Expedientes_datos.accdb',
                'RIESGOS_DB_PATH': r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\GESTION RIESGOS\Gestion_Riesgos_Datos.accdb',
                'NO_CONFORMIDADES_DB_PATH': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\NoConformidades_datos.accdb',
                'AGEDYS_DB_PATH': r'\\datoste\Aplicaciones_dys\Aplicaciones PpD\Proyectos\AGEDYS_DATOS.accdb',
                'TAREAS_DB_PATH': r'\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb'
            }
            return Path(os.getenv(env_var, office_paths.get(env_var, default_filename)))

    def get_db_connection_string(self, db_type: str) -> str:
        """Retorna la cadena de conexión para cualquier base de datos"""
        if db_type not in self.db_paths:
            raise ValueError(f"Tipo de BD no soportado: {db_type}")
        
        db_path = self.db_paths[db_type]
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD={self.db_password};"
        
    def _ensure_directories(self):
        """Crea directorios necesarios si no existen"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def get_css_file_path(self, style: str = None) -> Path:
        """Retorna la ruta del archivo CSS según el estilo especificado o la configuración"""
        if style is None:
            style = self.nc_css_style
        
        if style == 'modern':
            return self.css_modern_file_path
        else:  # classic
            return self.css_classic_file_path
    
    def get_nc_css_content(self) -> str:
        """Retorna el contenido del CSS para No Conformidades según la configuración"""
        css_path = self.get_css_file_path()
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback al CSS clásico si no se encuentra el moderno
            if self.nc_css_style == 'modern':
                try:
                    with open(self.css_classic_file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except FileNotFoundError:
                    return ""
            return ""
        except Exception:
            return ""

    def get_local_db_path(self, db_type: str) -> Path:
        """Retorna siempre la ruta local de la base de datos, independientemente del entorno"""
        if db_type == 'agedys':
            return self.root_dir / os.getenv('LOCAL_DB_AGEDYS', 'dbs-locales/AGEDYS_DATOS.accdb')
        elif db_type == 'brass':
            return self.root_dir / os.getenv('LOCAL_DB_BRASS', 'dbs-locales/Gestion_Brass_Gestion_Datos.accdb')
        elif db_type == 'tareas':
            return self.root_dir / os.getenv('LOCAL_DB_TAREAS', 'dbs-locales/Tareas_datos1.accdb')
        elif db_type == 'correos':
            return self.root_dir / os.getenv('LOCAL_DB_CORREOS', 'dbs-locales/correos_datos.accdb')
        elif db_type == 'riesgos':
            return self.root_dir / os.getenv('LOCAL_DB_RIESGOS', 'dbs-locales/Gestion_Riesgos_Datos.accdb')
        elif db_type == 'expedientes':
            return self.root_dir / os.getenv('LOCAL_DB_EXPEDIENTES', 'dbs-locales/Expedientes_datos.accdb')
        elif db_type == 'no_conformidades':
            return self.root_dir / os.getenv('LOCAL_DB_NO_CONFORMIDADES', 'dbs-locales/NoConformidades_Datos.accdb')
        else:
            raise ValueError(f"Tipo de BD no soportado: {db_type}")
    
    def get_database_path(self, db_type: str) -> Path:
        """Retorna la ruta apropiada según el tipo de BD"""
        if db_type == 'agedys':
            return self.db_agedys_path
        elif db_type == 'brass':
            return self.db_brass_path
        elif db_type == 'tareas':
            return self.db_tareas_path
        elif db_type == 'correos':
            return self.db_correos_path
        elif db_type == 'riesgos':
            return self.db_riesgos_path
        elif db_type == 'expedientes':
            return self.db_expedientes_path
        elif db_type == 'no_conformidades':
            return self.db_no_conformidades_path
        else:
            raise ValueError(f"Tipo de BD no soportado: {db_type}")
        
    def get_db_agedys_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos AGEDYS"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_agedys_path};PWD={self.db_password};"
        
    def get_db_brass_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos BRASS"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_brass_path};PWD={self.db_password};"
    
    def get_db_tareas_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos de Tareas"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_tareas_path};PWD={self.db_password};"

    def get_db_correos_connection_string(self, with_password=True) -> str:
        """Retorna la cadena de conexión para la base de datos de Correos"""
        if with_password and self.db_password:
            return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_correos_path};PWD={self.db_password};"
        else:
            return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_correos_path};"

    def get_db_riesgos_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos de Riesgos"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_riesgos_path};PWD={self.db_password};"

    def get_db_expedientes_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos de Expedientes"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_expedientes_path};PWD={self.db_password};"

    def get_db_no_conformidades_connection_string(self) -> str:
        """Retorna la cadena de conexión para la base de datos de No Conformidades"""
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_no_conformidades_path};PWD={self.db_password};"


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
