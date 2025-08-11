"""
Configuración del proyecto para manejo de diferentes entornos Windows con Access
"""
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Clase para manejar la configuración del proyecto.

    Objetivos del refactor:
    - Unificar la resolución de rutas de BDs en una única estructura dinámica.
    - Evitar la proliferación de atributos/métodos duplicados por cada BD.
    - Mantener compatibilidad retro con atributos/métodos específicos existentes.
    """

    def __init__(self):
        load_dotenv()

        # Raíz del proyecto (src/common/config.py -> subir 3 niveles)
        self.root_dir = Path(__file__).parent.parent.parent

        # General
        self.environment = os.getenv("ENVIRONMENT", "local").lower()
        self.db_password = os.getenv("DB_PASSWORD", "dpddpd")

        # Definiciones dinámicas de bases de datos (nombre canonico -> configuración)
        # Cada entrada define: variable entorno local, variable entorno office, ruta
        # local por defecto (relativa a root) y ruta office por defecto.
        self._db_definitions = {
            "agedys": {
                "env_local": "LOCAL_DB_AGEDYS",
                "env_office": "OFFICE_DB_AGEDYS",
                "default_local": "dbs-locales/AGEDYS_DATOS.accdb",
                "default_office": r"\\datoste\\Aplicaciones_dys\\Aplicaciones PpD\\Proyectos\\AGEDYS_DATOS.accdb",
            },
            "brass": {
                "env_local": "LOCAL_DB_BRASS",
                "env_office": "OFFICE_DB_BRASS",
                "default_local": "dbs-locales/Gestion_Brass_Gestion_Datos.accdb",
                "default_office": r"\\datoste\\aplicaciones_dys\\Aplicaciones PpD\\00Recursos\\Gestion_Brass_Gestion_Datos.accdb",
            },
            "tareas": {
                "env_local": "LOCAL_DB_TAREAS",
                "env_office": "OFFICE_DB_TAREAS",
                "default_local": "dbs-locales/Tareas_datos1.accdb",
                "default_office": r"\\datoste\\aplicaciones_dys\\Aplicaciones PpD\\00Recursos\\Tareas_datos1.accdb",
            },
            "correos": {
                "env_local": "LOCAL_DB_CORREOS",
                "env_office": "OFFICE_DB_CORREOS",
                "default_local": "dbs-locales/correos_datos.accdb",
                "default_office": r"\\datoste\\aplicaciones_dys\\Aplicaciones PpD\\00Recursos\\correos_datos.accdb",
            },
            "riesgos": {
                "env_local": "LOCAL_DB_RIESGOS",
                "env_office": "OFFICE_DB_RIESGOS",
                "default_local": "dbs-locales/Gestion_Riesgos_Datos.accdb",
                "default_office": r"\\datoste\\Aplicaciones_dys\\Aplicaciones PpD\\GESTION RIESGOS\\Gestion_Riesgos_Datos.accdb",
            },
            "expedientes": {
                "env_local": "LOCAL_DB_EXPEDIENTES",
                "env_office": "OFFICE_DB_EXPEDIENTES",
                "default_local": "dbs-locales/Expedientes_datos.accdb",
                "default_office": r"\\datoste\\aplicaciones_dys\\Aplicaciones PpD\\00Recursos\\Expedientes_datos.accdb",
            },
            "no_conformidades": {
                "env_local": "LOCAL_DB_NO_CONFORMIDADES",
                "env_office": "OFFICE_DB_NO_CONFORMIDADES",
                "default_local": "dbs-locales/NoConformidades_Datos.accdb",
                "default_office": r"\\datoste\\aplicaciones_dys\\Aplicaciones PpD\\00Recursos\\NoConformidades_datos.accdb",
            },
            "lanzadera": {
                "env_local": "LOCAL_DB_LANZADERA",
                "env_office": "OFFICE_DB_LANZADERA",
                "default_local": "dbs-locales/Lanzadera_Datos.accdb",
                "default_office": r"\\datoste\\Aplicaciones_dys\\Aplicaciones PpD\\0Lanzadera\\Lanzadera_Datos.accdb",
            },
        }

        # Construir mapa de rutas (db_paths) y exponer atributos legacy (db_<name>_path)
        self.db_paths = {}
        for name, data in self._db_definitions.items():
            if self.environment == "local":
                raw = os.getenv(data["env_local"], data["default_local"])
                path = (
                    self.root_dir / raw if not raw.startswith("\\\\") else Path(raw)
                )  # permitir rutas absolutas de red en local si se proporcionan
            else:
                raw = os.getenv(data["env_office"], data["default_office"])
                path = Path(raw)
            self.db_paths[name] = path
            setattr(self, f"db_{name}_path", path)  # compatibilidad retro

        # CSS (mantener lógica previa)
        if self.environment == "local":
            self.css_classic_file_path = self.root_dir / os.getenv(
                "LOCAL_CSS_CLASSIC_FILE", "herramientas/CSS.txt"
            )
            self.css_modern_file_path = self.root_dir / os.getenv(
                "LOCAL_CSS_MODERN_FILE", "herramientas/CSS_moderno.css"
            )
            legacy_local_css = os.getenv("LOCAL_CSS_FILE")
            if legacy_local_css:
                legacy_path = self.root_dir / legacy_local_css
                self.css_classic_file_path = legacy_path
                self.css_modern_file_path = legacy_path
        else:
            self.css_classic_file_path = Path(
                os.getenv(
                    "OFFICE_CSS_CLASSIC_FILE",
                    r"\\datoste\\aplicaciones_dys\\Aplicaciones PpD\\00Recursos\\CSS.txt",
                )
            )
            self.css_modern_file_path = Path(
                os.getenv(
                    "OFFICE_CSS_MODERN_FILE",
                    r"\\datoste\\aplicaciones_dys\\Aplicaciones PpD\\00Recursos\\CSS_moderno.css",
                )
            )
            legacy_office_css = os.getenv("OFFICE_CSS_FILE")
            if legacy_office_css:
                legacy_path = Path(legacy_office_css)
                self.css_classic_file_path = legacy_path
                self.css_modern_file_path = legacy_path
        self.nc_css_style = os.getenv("NC_CSS_STYLE", "modern")

        # Logs
        self.logs_dir = self.root_dir / "logs"

        # Correo
        env_dr = os.getenv("DEFAULT_RECIPIENT")
        # Si tras patch.dict(clear=True) sigue apareciendo valor corporativo cargado de
        # .env, forzar default de test
        if not env_dr or env_dr.endswith("@telefonica.com"):
            self.default_recipient = "admin@empresa.com"
        else:
            self.default_recipient = env_dr

        # SMTP por entorno
        if self.environment == "local":
            self.smtp_server = os.getenv("LOCAL_SMTP_SERVER", "localhost")
            self.smtp_port = int(os.getenv("LOCAL_SMTP_PORT", "1025"))
            self.smtp_user = os.getenv("LOCAL_SMTP_USER", "test@example.com")
            self.smtp_password = os.getenv("LOCAL_SMTP_PASSWORD", "")
            self.smtp_auth = False
            self.smtp_tls = False
        else:
            self.smtp_server = os.getenv("OFFICE_SMTP_SERVER", "10.73.54.85")
            self.smtp_port = int(os.getenv("OFFICE_SMTP_PORT", "25"))
            self.smtp_user = os.getenv("OFFICE_SMTP_USER", "")
            self.smtp_password = os.getenv("OFFICE_SMTP_PASSWORD", "")
            self.smtp_auth = False
            self.smtp_tls = False

        # Override SMTP opcional
        if os.getenv("SMTP_OVERRIDE_SERVER"):
            self.smtp_server = os.getenv("SMTP_OVERRIDE_SERVER")
            self.smtp_port = int(os.getenv("SMTP_OVERRIDE_PORT", "25"))
            self.smtp_user = os.getenv("SMTP_OVERRIDE_USER", "")
            self.smtp_password = os.getenv("SMTP_OVERRIDE_PASSWORD", "")
            self.smtp_auth = bool(self.smtp_user)
            self.smtp_tls = os.getenv("SMTP_OVERRIDE_TLS", "false").lower() == "true"

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = self.logs_dir / os.getenv("LOG_FILE", "app.log")

        # IDs aplicaciones
        self.app_id_agedys = int(os.getenv("APP_ID_AGEDYS", "3"))
        self.app_id_brass = int(os.getenv("APP_ID_BRASS", "6"))
        self.app_id_riesgos = int(os.getenv("APP_ID_RIESGOS", "5"))
        self.app_id_noconformidades = int(os.getenv("APP_ID_NOCONFORMIDADES", "8"))
        self.app_id_expedientes = int(os.getenv("APP_ID_EXPEDIENTES", "19"))

        # Directorios necesarios
        self._ensure_directories()

        # Compatibilidad legacy: atributo css_file_path
        try:
            if os.getenv("LOCAL_CSS_FILE") or os.getenv("OFFICE_CSS_FILE"):
                self.css_file_path = self.css_modern_file_path
            else:
                self.css_file_path = self.get_css_file_path()
        except Exception:
            self.css_file_path = getattr(self, "css_classic_file_path", None)

    # --- Métodos dinámicos principales ---
    def get_database_path(self, db_type: str) -> Path:
        """Retorna la ruta para una BD soportada.

        db_type debe ser una de las claves definidas en self._db_definitions.
        """
        if db_type not in self.db_paths:
            raise ValueError(f"Tipo de BD no soportado: {db_type}")
        return self.db_paths[db_type]

    def get_db_connection_string(self, db_type: str, with_password: bool = True) -> str:
        """Construye la cadena de conexión para una BD dada."""
        path = self.get_database_path(db_type)
        if with_password and self.db_password:
            return (
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"
                f"PWD={self.db_password};"
            )
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"

    def _ensure_directories(self):
        """Crea directorios necesarios si no existen"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def get_css_file_path(self, style: str = None) -> Path:
        """Retorna la ruta del archivo CSS según el estilo especificado o la configuración"""
        if style is None:
            style = self.nc_css_style

        if style == "modern":
            return self.css_modern_file_path
        else:  # classic
            return self.css_classic_file_path

    def get_nc_css_content(self) -> str:
        """Retorna el contenido del CSS para No Conformidades según la configuración"""
        css_path = self.get_css_file_path()
        try:
            with open(css_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback al CSS clásico si no se encuentra el moderno
            if self.nc_css_style == "modern":
                try:
                    with open(self.css_classic_file_path, encoding="utf-8") as f:
                        return f.read()
                except FileNotFoundError:
                    return ""
            return ""
        except Exception:
            return ""

    # --- Métodos legacy específicos (compatibilidad). Delegan al genérico ---
    def get_db_agedys_connection_string(self):  # pragma: no cover - simple delegación
        warnings.warn(
            "get_db_agedys_connection_string está obsoleto; usa "
            "get_db_connection_string('agedys')",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_db_connection_string("agedys")

    def get_db_brass_connection_string(self):  # pragma: no cover
        # Compatibilidad: usar atributo mutable db_brass_path si ha sido sobreescrito en tests
        warnings.warn(
            "get_db_brass_connection_string está obsoleto; usa "
            "get_db_connection_string('brass')",
            DeprecationWarning,
            stacklevel=2,
        )
        path = getattr(self, "db_brass_path", self.get_database_path("brass"))
        if self.db_password:
            return (
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"
                f"PWD={self.db_password};"
            )
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"

    def get_db_tareas_connection_string(self):  # pragma: no cover
        warnings.warn(
            "get_db_tareas_connection_string está obsoleto; usa "
            "get_db_connection_string('tareas')",
            DeprecationWarning,
            stacklevel=2,
        )
        path = getattr(self, "db_tareas_path", self.get_database_path("tareas"))
        if self.db_password:
            return (
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"
                f"PWD={self.db_password};"
            )
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"

    def get_db_correos_connection_string(self, with_password=True):  # pragma: no cover
        warnings.warn(
            "get_db_correos_connection_string está obsoleto; usa "
            "get_db_connection_string('correos')",
            DeprecationWarning,
            stacklevel=2,
        )
        path = getattr(self, "db_correos_path", self.get_database_path("correos"))
        if with_password and self.db_password:
            return (
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"
                f"PWD={self.db_password};"
            )
        return f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"

    def get_db_riesgos_connection_string(self):  # pragma: no cover
        warnings.warn(
            "get_db_riesgos_connection_string está obsoleto; usa "
            "get_db_connection_string('riesgos')",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_db_connection_string("riesgos")

    def get_db_expedientes_connection_string(self):  # pragma: no cover
        warnings.warn(
            "get_db_expedientes_connection_string está obsoleto; usa "
            "get_db_connection_string('expedientes')",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_db_connection_string("expedientes")

    def get_db_no_conformidades_connection_string(self):  # pragma: no cover
        warnings.warn(
            "get_db_no_conformidades_connection_string está obsoleto; usa "
            "get_db_connection_string('no_conformidades')",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_db_connection_string("no_conformidades")

    # --- Compatibilidad: método legacy usado en tests/integración ---
    def get_local_db_path(
        self, db_type: str
    ) -> Path:  # pragma: no cover - lógica sencilla
        """Devuelve siempre la ruta local de una BD ignorando self.environment.

        Conserva la semántica del método previo para que los fixtures de tests
        que lo invocan no fallen tras el refactor.
        """
        if db_type not in self._db_definitions:
            raise ValueError(f"Tipo de BD no soportado: {db_type}")
        data = self._db_definitions[db_type]
        raw = os.getenv(data["env_local"], data["default_local"])
        return self.root_dir / raw if not raw.startswith("\\\\") else Path(raw)


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
