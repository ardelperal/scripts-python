"""Utilidades comunes para el proyecto
"""
import logging
import holidays
import os
import re
from datetime import date, datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Importa los componentes de la librería correcta: python-logging-loki
try:  # Hacer opcional la dependencia de logging_loki
    from logging_loki import LokiQueueHandler  # type: ignore
except ImportError:  # pragma: no cover - entorno sin logging_loki
    LokiQueueHandler = None  # fallback para entornos donde no está instalada
from queue import Queue

# Importar config para funciones que lo necesitan
from .config import config


def hide_password_in_connection_string(connection_string: str) -> str:
    """
    Oculta la contraseña en una cadena de conexión para logging seguro

    Args:
        connection_string: Cadena de conexión que puede contener contraseña

    Returns:
        Cadena de conexión con contraseña oculta
    """
    # Patrón para encontrar PWD=valor; o Password=valor;
    pattern = r"(PWD|Password)=([^;]+);"
    return re.sub(pattern, r"\1=***;", connection_string, flags=re.IGNORECASE)


def setup_logging(log_file: Path, level=logging.INFO):
    """Configura logging (archivo + consola + Loki opcional) limpiando handlers previos.

    Mantiene compatibilidad con tests que validan:
    - Limpieza de handlers existentes (logger.hasHandlers())
    - Creación de directorio/archivo
    - Mensajes informativos específicos en ausencia / error de Loki
    - Creación de LokiQueueHandler si procede
    """
    logger = logging.getLogger()
    if logger.hasHandlers():  # tests esperan clear()
        try:
            logger.handlers.clear()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            # fallback manual
            for h in list(logger.handlers):
                logger.removeHandler(h)

    logger.setLevel(level)
    if not isinstance(log_file, Path):  # defensive
        log_file = Path(str(log_file))
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    loki_url = os.getenv("LOKI_URL")
    if loki_url and LokiQueueHandler is not None:
        try:
            q = Queue()
            full_url = f"{loki_url.rstrip('/')}/loki/api/v1/push"
            loki_handler = LokiQueueHandler(
                queue=q,
                url=full_url,
                tags={
                    "application": "scripts_python",
                    "environment": os.getenv("ENVIRONMENT", "development"),
                },
                version="1",
            )
            loki_handler.setFormatter(formatter)
            logger.addHandler(loki_handler)
        except Exception as e:  # pragma: no cover
            logging.warning(
                f"No se pudo configurar Loki handler: {e}. Continuando solo con archivo y consola."
            )
    elif loki_url and LokiQueueHandler is None:
        # Loki no instalado
        logging.info(
            "LOKI_URL configurada pero módulo logging_loki no instalado; continuando sin Loki."
        )
    else:
        logging.info(
            "LOKI_URL no configurada. Logging configurado solo para archivo y consola."
        )
    return logger


# Inicializa el objeto una sola vez a nivel de módulo para mayor eficiencia
# 'M' es el código para la Comunidad de Madrid
try:
    festivos_madrid = holidays.ES(prov='M')
    HOLIDAYS_LIB_AVAILABLE = True
except Exception:
    festivos_madrid = None
    HOLIDAYS_LIB_AVAILABLE = False
    logging.warning("No se pudo inicializar la librería 'holidays'. Se usará el archivo local como fallback.")

def es_laborable(fecha: date = None, festivos_file_path: Path = None) -> bool:
    """
    Determina si una fecha es día laborable en Madrid.
    Un día es laborable si no es fin de semana y no es festivo.
    Primero intenta usar la librería 'holidays' y, si falla, usa 'Festivos.txt'.
    festivos_file_path: solo para tests, permite inyectar la ruta del archivo de festivos.
    """
    if fecha is None:
        fecha = date.today()

    # 1. Comprueba si es fin de semana (lunes=0, ..., domingo=6)
    if fecha.weekday() >= 5:
        return False

    # 2. Intenta usar la librería 'holidays' (método principal)
    if HOLIDAYS_LIB_AVAILABLE and festivos_madrid:
        try:
            if fecha in festivos_madrid:
                return False
            else:
                return True # No es festivo según la librería
        except Exception as e:
            logging.warning(f"Fallo al consultar la librería 'holidays': {e}. Usando fallback a Festivos.txt.")

    # 3. Si la librería falla o no está disponible, usa el archivo local (método de respaldo)
    try:
        if festivos_file_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            festivos_file_path = project_root / "herramientas" / "Festivos.txt"
        if festivos_file_path.exists():
            with open(festivos_file_path, 'r', encoding='utf-8') as f:
                festivos_locales = f.read().splitlines()
            if fecha.strftime("%d/%m/%Y") in festivos_locales:
                return False
    except Exception as e:
        logging.error(f"No se pudo leer el archivo de festivos local: {e}")

    # Si no es fin de semana ni se encontró como festivo, es laborable
    return True
def is_workday(check_date: date, holidays_file: Optional[Path] = None) -> bool:
    """
    Verifica si una fecha es día laborable

    Args:
        check_date: Fecha a verificar
        holidays_file: Archivo con días festivos

    Returns:
        True si es día laborable, False en caso contrario
    """
    # Verificar si es fin de semana (lunes=0, domingo=6)
    if check_date.weekday() >= 5:  # sábado=5, domingo=6
        return False

    # Verificar si es día festivo
    if holidays_file and holidays_file.exists():
        try:
            with open(holidays_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and str(check_date) in line:
                        return False
        except Exception as e:
            logging.warning(f"Error leyendo archivo de festivos: {e}")

    return True


def get_next_workday_from_preferred(
    preferred_weekday: int = 0, holidays_file: Optional[Path] = None
) -> date:
    """
    Obtiene el próximo día laborable a partir del día de la semana preferido

    Args:
        preferred_weekday: Día de la semana preferido (0=lunes, 1=martes, ..., 6=domingo)
        holidays_file: Archivo con días festivos

    Returns:
        Fecha del próximo día laborable
    """
    _today = date.today()

    # Calcular días hasta el día preferido de esta semana
    _days_until_preferred = (preferred_weekday - _today.weekday()) % 7

    # Si es 0, significa que hoy es el día preferido
    if _days_until_preferred == 0:
        candidate_date = _today
    else:
        candidate_date = _today + timedelta(days=_days_until_preferred)

    # Buscar el próximo día laborable desde el día preferido
    max_attempts = 7  # Máximo una semana de búsqueda
    attempts = 0

    while attempts < max_attempts:
        if es_laborable(candidate_date):
            return candidate_date

        # Si no es laborable, probar el siguiente día
        candidate_date += timedelta(days=1)
        attempts += 1

    # Si no encontramos un día laborable en una semana, devolver el lunes original
    # (situación excepcional)
    return candidate_date


def is_night_time(current_time: Optional[datetime] = None) -> bool:
    """Indica si la hora está dentro del tramo nocturno (20:00 - 07:00)."""
    if current_time is None:
        current_time = datetime.now()
    hour = current_time.hour
    return hour >= 20 or hour < 7


def load_css_content(css_file_path: Path) -> str:
    """
    Carga el contenido CSS desde un archivo con soporte para múltiples encodings

    Args:
        css_file_path: Ruta al archivo CSS

    Returns:
        Contenido CSS como string
    """
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            with open(css_file_path, encoding=encoding) as f:
                content = f.read()
                logging.info(
                    f"Archivo CSS cargado exitosamente con encoding {encoding}"
                )
                return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logging.error(f"Error leyendo archivo CSS {css_file_path}: {e}")
            break

    logging.warning(
        f"No se pudo cargar el archivo CSS {css_file_path} con ningún encoding, "
        "usando CSS por defecto"
    )
    # CSS básico por defecto
    return """
    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
    .centrado { text-align: center; }
    .ColespanArriba { background-color: #4CAF50; color: white; font-weight: bold; text-align: center; }
    .Cabecera { background-color: #f2f2f2; font-weight: bold; text-align: center; border: 1px solid #ddd; }
    table { border-collapse: collapse; width: 100%; }
    td, th { border: 1px solid #ddd; padding: 8px; }
    strong { font-weight: bold; }
    """


## Eliminados definitivamente generate_html_header / generate_html_footer (wrappers legacy)
## Usar directamente HTMLReportGenerator en nuevo código.


def safe_str(value, default: str = "&nbsp;") -> str:
    """
    Convierte un valor a string de forma segura para HTML

    Args:
        value: Valor a convertir
        default: Valor por defecto si es None o vacío

    Returns:
        String seguro para HTML
    """
    if value is None or value == "":
        return default
    return str(value)


def format_date(date_value, format_str: str = "%d/%m/%Y") -> str:
    """
    Formatea una fecha a string

    Args:
        date_value: Fecha a formatear (datetime, date o string)
        format_str: Formato de salida

    Returns:
        Fecha formateada como string
    """
    if date_value is None:
        return ""

    if isinstance(date_value, str):
        try:
            # Intentar parsear diferentes formatos de fecha
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                try:
                    date_value = datetime.strptime(date_value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return str(date_value)
        except Exception:
            return str(date_value)

    if isinstance(date_value, (datetime, date)):
        return date_value.strftime(format_str)

    return str(date_value)


def get_admin_users(db_connection) -> list[dict[str, str]]:
    """
    Obtiene la lista de usuarios administradores desde la base de datos

    Args:
        db_connection: Conexión a la base de datos de tareas

    Returns:
        Lista de usuarios administradores
    """
    try:
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario
            FROM TbUsuariosAplicaciones ua
            INNER JOIN TbUsuariosAplicacionesTareas uat ON ua.CorreoUsuario = uat.CorreoUsuario
            WHERE ua.ParaTareasProgramadas = True
            AND ua.FechaBaja IS NULL
            AND uat.EsAdministrador = 'Sí'
        """

        result = db_connection.execute_query(query)
        return result

    except Exception as e:
        logging.error(f"Error obteniendo usuarios administradores: {e}")
        return []


def get_technical_emails_string(app_id: str, config, logger) -> str:
    """
    Obtiene la cadena de correos de usuarios técnicos separados por ;

    Args:
        app_id: ID de la aplicación
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        String con correos separados por ;
    """
    try:
        technical_users = get_technical_users(app_id, config, logger)
        emails = [
            user["CorreoUsuario"] for user in technical_users if user["CorreoUsuario"]
        ]
        return ";".join(emails)
    except Exception as e:
        logger.error(f"Error obteniendo emails técnicos para {app_id}: {e}")
        return ""


def get_quality_emails_string(app_id, config, logger, db_connection) -> str:
    """
    Devuelve emails de usuarios de Calidad.

    app_id debe ser numérico (IDAplicacion en permisos). Antes se pasaba la cadena
    "AGEDYS" provocando error de tipo en Access. Esta función acepta str/int pero
    se normaliza a entero en user_adapter.
    """
    try:
        from .user_adapter import get_users_with_fallback

        quality_users = get_users_with_fallback(
            user_type="quality",
            db_connection=db_connection,
            config=config,
            logger=logger,
            app_id=app_id,
        )
        return "; ".join(
            [
                user["CorreoUsuario"]
                for user in quality_users
                if user.get("CorreoUsuario")
            ]
        )
    except Exception as e:
        logging.error(f"Error obteniendo emails de calidad: {e}")
        return ""


def get_admin_emails_string(db_connection, config, logger) -> str:
    """
    Obtiene una cadena con los emails de los administradores separados por punto y coma

    Args:
        db_connection: Conexión a la base de datos de tareas
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        Cadena de emails
    """
    # Por ahora, los administradores son los mismos que los técnicos
    return get_technical_emails_string("admin", config, logger)


def get_quality_users(app_id, config, logger) -> list[dict[str, str]]:  # retrocompat
    try:
        from .user_adapter import get_users_with_fallback

        return get_users_with_fallback(
            user_type="quality",
            db_connection=None,
            config=config,
            logger=logger,
            app_id=app_id,
        )
    except Exception as e:  # pragma: no cover
        if logger:
            logger.debug(f"Fallback get_quality_users: {e}")
        return []


def get_economy_emails_string(app_id, config, logger, db_connection=None) -> str:  # retrocompat
    try:
        users = get_economy_users(config, logger)
        return ";".join(u.get("CorreoUsuario") for u in users if u.get("CorreoUsuario"))
    except Exception as e:  # pragma: no cover
        if logger:
            logger.debug(f"Fallback get_economy_emails_string: {e}")
        return ""


def send_email(
    to_address: str,
    subject: str,
    body: str,
    is_html: bool = True,
    from_app: str = "Sistema",
    attachments: list[str] = None,
) -> bool:
    """
    Envía un email usando SMTP (implementación real basada en script original VBS)

    Args:
        to_address: Dirección de destino
        subject: Asunto del email
        body: Cuerpo del email
        is_html: Si el cuerpo es HTML
        from_app: Aplicación que envía el correo
        attachments: Lista de rutas de archivos adjuntos

    Returns:
        True si se envió correctamente, False en caso contrario
    """
    try:
        import smtplib
        from email.mime.application import MIMEApplication
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from pathlib import Path

        # Configuración SMTP basada en script original VBS
        smtp_server = config.smtp_server
        smtp_port = config.smtp_port

        # Crear mensaje
        msg = MIMEMultipart()
        msg["From"] = f"{from_app}.DySN@telefonica.com"
        msg["To"] = to_address
        msg["Subject"] = subject

        # Añadir BCC para administrador (como en el script original VBS)
        admin_email = "Andres.RomandelPeral@telefonica.com"
        if admin_email not in to_address:
            msg["Bcc"] = admin_email

        # Añadir cuerpo del mensaje
        if is_html:
            msg.attach(MIMEText(body, "html", "utf-8"))
        else:
            msg.attach(MIMEText(body, "plain", "utf-8"))

        # Añadir archivos adjuntos si existen
        if attachments:
            for attachment_path in attachments:
                if Path(attachment_path).exists():
                    with open(attachment_path, "rb") as f:
                        attach = MIMEApplication(f.read())
                        attach.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=Path(attachment_path).name,
                        )
                        msg.attach(attach)

        # Enviar email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Sin autenticación como en el script original VBS
            server.sendmail(msg["From"], [to_address, admin_email], msg.as_string())

        logging.info(f"Email enviado exitosamente a {to_address} con asunto: {subject}")
        return True

    except Exception as e:
        logging.error(f"Error enviando email a {to_address}: {e}")
        return False


# Función send_notification_email eliminada - solo se registran correos en BD


def register_email_in_database(
    db_connection,
    application: str,
    subject: str,
    body: str,
    recipients: str,
    admin_emails: str = "",
) -> bool:
    """
    Registra un correo en la base de datos de tareas

    Args:
        db_connection: Conexión a la base de datos de tareas
        application: Nombre de la aplicación (BRASS, Expedientes, Riesgos, etc.)
        subject: Asunto del correo
        body: Cuerpo del correo
        recipients: Destinatarios del correo
        admin_emails: Emails de administradores para copia oculta

    Returns:
        True si se registró correctamente
    """
    try:
        # Obtener próximo ID
        next_id = db_connection.get_max_id("TbCorreosEnviados", "IDCorreo") + 1

        # Preparar datos del correo
        email_data = {
            "IDCorreo": next_id,
            "Aplicacion": application,
            "Asunto": subject,
            "Cuerpo": body,
            "Destinatarios": recipients if "@" in recipients else "",
            "DestinatariosConCopiaOculta": admin_emails,
            "FechaGrabacion": datetime.now(),
        }

        success = db_connection.insert_record("TbCorreosEnviados", email_data)

        if success:
            logging.info(f"Correo registrado correctamente para {application}")
        else:
            logging.error(f"Error registrando correo para {application}")

        return success

    except Exception as e:
        logging.error(f"Error registrando correo en base de datos: {e}")
        return False


def register_task_completion(
    db_connection, task_name: str, execution_date: Optional[date] = None
) -> bool:
    """
    Registra la finalización de una tarea en la base de datos
    Solo debe haber un registro por nombre de tarea.
    Si no existe se crea, si existe se actualiza la fecha.

    Args:
        db_connection: Conexión a la base de datos de tareas
        task_name: Nombre de la tarea
        execution_date: Fecha de ejecución (por defecto hoy)

    Returns:
        True si se registró correctamente
    """
    try:
        if execution_date is None:
            execution_date = date.today()

        # Verificar si ya existe la tarea
        select_query = "SELECT * FROM TbTareas WHERE Tarea = ?"
        rows = db_connection.execute_query(select_query, [task_name])

        if rows:
            # Actualizar registro existente
            try:
                db_connection.execute_non_query(
                    "UPDATE TbTareas SET Realizado = 'Sí', Fecha = ? WHERE Tarea = ?",
                    [execution_date, task_name],
                )
            except Exception:
                # Fallback si columnas difieren
                db_connection.execute_non_query(
                    "UPDATE TbTareas SET FechaEjecucion = ? WHERE Tarea = ?",
                    [datetime.now(), task_name],
                )
        else:
            # Insertar nuevo registro (probar con esquema estándar primero)
            inserted = False
            try:
                db_connection.execute_non_query(
                    "INSERT INTO TbTareas (Tarea, Realizado, Fecha) VALUES (?, 'Sí', ?)",
                    [task_name, execution_date],
                )
                inserted = True
            except Exception:
                try:
                    db_connection.execute_non_query(
                        "INSERT INTO TbTareas (Tarea, FechaEjecucion) VALUES (?, ?)",
                        [task_name, datetime.now()],
                    )
                    inserted = True
                except Exception:
                    inserted = False
            if not inserted:
                return False
        return True
    except Exception as e:
        logging.error(f"Error registrando finalización de tarea {task_name}: {e}")
        return False


def get_technical_users(app_id: str | int, config, logger) -> list[dict[str, str]]:
    """Obtiene usuarios técnicos.

    Usa adaptador si disponible; si falla retorna lista vacía.
    """
    try:
        from .user_adapter import get_users_with_fallback

        return get_users_with_fallback(
            user_type="technical",
            db_connection=None,
            config=config,
            logger=logger,
            app_id=app_id,
        )
    except Exception as e:  # pragma: no cover - defensivo
        if logger:
            logger.debug(f"Fallback usuarios técnicos: {e}")
        return []


def get_economy_users(config, logger) -> list[dict[str, str]]:
    """
    Obtiene la lista de usuarios de economía desde la base de datos
    Basado en el script original VBS: usa TbUsuariosAplicacionesTareas con EsEconomia

    Args:
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        Lista de usuarios de economía
    """
    try:
        from .database import AccessDatabase

        # Usar la conexión de tareas para obtener usuarios (como en el script original)
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())

        query = """
            SELECT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre,
            TbUsuariosAplicaciones.CorreoUsuario
            FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesTareas ON
            TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesTareas.CorreoUsuario
            WHERE TbUsuariosAplicaciones.ParaTareasProgramadas = True
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbUsuariosAplicacionesTareas.EsEconomia = 'Sí'
        """

        result = db_connection.execute_query(query)
        return result

    except Exception as e:
        logger.error(f"Error obteniendo usuarios de economía: {e}")
        return []


def get_user_email(username: str, config, logger=None) -> str:
    """
    Obtiene el correo electrónico de un usuario específico
    Basado en el script original VBS: busca en TbUsuariosAplicaciones por UsuarioRed

    Args:
        usuario_red: Nombre de usuario de red
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        Correo electrónico del usuario o None si no se encuentra
    """
    try:
        from .database import AccessDatabase

        # Usar la conexión de tareas para obtener el email
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())

        # Query simplificada que coincide exactamente con el VBS original
        query = """
            SELECT CorreoUsuario
            FROM TbUsuariosAplicaciones
            WHERE UsuarioRed = ?
        """

        result = db_connection.execute_query(query, [username])

        if result and len(result) > 0:
            email = result[0].get("CorreoUsuario", "")
            return email if email else ""

        return ""

    except Exception as e:
        if logger:
            logger.error(f"Error obteniendo email para usuario {username}: {e}")
        else:
            logging.error(f"Error obteniendo email para usuario {username}: {e}")
        return ""


def get_technical_emails_string(app_id: str, config, logger) -> str:
    """
    Obtiene la cadena de correos de usuarios técnicos separados por ;

    Args:
        app_id: ID de la aplicación
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        String con correos separados por ;
    """
    try:
        technical_users = get_technical_users(app_id, config, logger)
        emails = [
            user["CorreoUsuario"] for user in technical_users if user["CorreoUsuario"]
        ]
        return ";".join(emails)
    except Exception as e:
        logger.error(f"Error obteniendo emails técnicos para {app_id}: {e}")
        return ""


def get_economy_emails_string(config, logger) -> str:
    """
    Obtiene la cadena de correos de usuarios de economía separados por ;

    Args:
        config: Configuración de la aplicación
        logger: Logger para registrar eventos

    Returns:
        String con correos separados por ;
    """
    try:
        economy_users = get_economy_users(config, logger)
        emails = [
            user["CorreoUsuario"] for user in economy_users if user["CorreoUsuario"]
        ]
        return ";".join(emails)
    except Exception as e:
        logger.error(f"Error obteniendo emails de economía: {e}")
        return ""


def get_last_task_execution_date(db_connection, task_name: str) -> Optional[date]:
    """
    Obtiene la fecha de la última ejecución de una tarea

    Args:
        db_connection: Conexión a la base de datos de tareas
        task_name: Nombre de la tarea

    Returns:
        Fecha de la última ejecución o None si no existe
    """
    try:
        query = """
            SELECT MAX(Fecha) as UltimaFecha
            FROM TbTareas
            WHERE Tarea = ?
        """

        result = db_connection.execute_query(query, [task_name])

        if result and result[0]["UltimaFecha"]:
            fecha = result[0]["UltimaFecha"]
            # Convertir a date si es datetime
            if isinstance(fecha, datetime):
                return fecha.date()
            return fecha

        return None

    except Exception as e:
        logging.error(
            f"Error obteniendo fecha de última ejecución para {task_name}: {e}"
        )
        return None


def is_task_completed_today(db_connection, task_name: str) -> bool:
    """
    Verifica si una tarea ya se ejecutó hoy

    Args:
        db_connection: Conexión a la base de datos de tareas
        task_name: Nombre de la tarea

    Returns:
        True si ya se ejecutó hoy, False en caso contrario
    """
    last_execution = get_last_task_execution_date(db_connection, task_name)
    today = date.today()

    if last_execution is None:
        return False

    return last_execution == today


def execute_task_with_standard_boilerplate(
    task_name: str,
    task_obj=None,
    *,
    force: bool = False,
    dry_run: bool = False,
    log_level: int = logging.INFO,
    log_file: Path | None = None,
    logger: logging.Logger | None = None,
):
    """Ejecuta una tarea (objeto con métodos) con patrón estándar.

    Compatibilidad con tests existentes que esperan:
    - Selección de método: execute_specific_logic / execute_logic / execute
    - Uso de debe_ejecutarse() salvo --force o dry_run
    - Llamada a marcar_como_completada() tras éxito (cuando no force)
    """
    from pathlib import Path as _Path

    upper = task_name.upper()
    root = logging.getLogger()
    if not root.handlers:  # ejecución aislada
        setup_logging(log_file or _Path('logs') / 'app.log')  # type: ignore[arg-type]
    task_logger = logger or logging.getLogger(f"tasks.{upper}")
    task_logger.setLevel(log_level)
    task_logger.propagate = True

    def _select_method(obj):
        for attr in ("execute_specific_logic", "execute_logic", "execute"):
            if hasattr(obj, attr) and callable(getattr(obj, attr)):
                return getattr(obj, attr)
        raise AttributeError("No se encontró método de ejecución en la tarea")

    exit_code = 0
    task_logger.info(f"=== INICIO TAREA {upper} ===")
    try:
        if task_obj is None:
            raise ValueError("task_obj requerido")

        if dry_run:
            # Sólo comprobar planificación
            should = True
            if hasattr(task_obj, 'debe_ejecutarse'):
                try:
                    should = task_obj.debe_ejecutarse()
                except Exception as e:  # pragma: no cover
                    task_logger.warning("Error evaluando planificación: %s", e)
                    should = False
            task_logger.info("Planificación: %s", "EJECUTAR" if should else "OMITIR")
            return 0

        if not force and hasattr(task_obj, 'debe_ejecutarse'):
            try:
                if not task_obj.debe_ejecutarse():
                    task_logger.info(f"La tarea {upper} no requiere ejecución hoy.")
                    return 0
            except Exception as e:  # pragma: no cover
                task_logger.warning("Fallo en debe_ejecutarse(): %s (se continúa)", e)

        method = _select_method(task_obj)
        try:
            result = method()
            if result is False:
                task_logger.error("La lógica específica devolvió False")
                exit_code = 1
            else:
                if not force and hasattr(task_obj, 'marcar_como_completada'):
                    try:
                        task_obj.marcar_como_completada()
                    except Exception as e:  # pragma: no cover
                        task_logger.warning("No se pudo marcar completada: %s", e)
        except Exception as e:  # pragma: no cover
            task_logger.exception("Excepción ejecutando lógica: %s", e)
            exit_code = 1
        if force:
            task_logger.info("Ejecución forzada (--force)")
    except Exception as e:  # pragma: no cover
        task_logger.exception("Error en tarea %s: %s", upper, e)
        exit_code = 1
    finally:
        task_logger.info(
            f"=== FIN TAREA {upper} ===",
            extra={"event": "task_end", "task": upper, "exit_code": exit_code},
        )
    return exit_code


def should_execute_task(
    db_connection, task_name: str, frequency_days: int, logger=None
) -> bool:
    """
    Determina si se debe ejecutar una tarea basándose en su frecuencia

    Args:
        db_connection: Conexión a la base de datos de tareas
        task_name: Nombre de la tarea
        frequency_days: Frecuencia en días para ejecutar la tarea
        logger: Logger para registrar eventos (opcional)

    Returns:
        True si se debe ejecutar la tarea
    """
    try:
        last_execution = get_last_task_execution_date(db_connection, task_name)

        if last_execution is None:
            # Si no hay registro previo, ejecutar
            if logger:
                logger.info(
                    f"No hay registro previo de tarea {task_name}, se requiere ejecutar"
                )
            return True

        days_since_last = (date.today() - last_execution).days
        should_execute = days_since_last >= frequency_days

        if logger:
            logger.info(
                f"Última ejecución tarea {task_name}: {last_execution}, "
                f"días transcurridos: {days_since_last}, requiere: {should_execute}"
            )

        return should_execute

    except Exception as e:
        if logger:
            logger.error(f"Error determinando si requiere tarea {task_name}: {e}")
        else:
            logging.error(f"Error determinando si requiere tarea {task_name}: {e}")
        return True


## (Definición anterior de execute_task_with_standard_boilerplate eliminada y reemplazada por versión centralizada más arriba)


def ensure_project_root_in_path():
    """
    Garantiza que la ruta raíz del proyecto (que contiene 'src') esté en sys.path.

    Idempotente: sólo inserta si no existe ya. No lanza excepciones al fallar.
    """
    try:
        import sys as _sys
        from pathlib import Path as _Path

        current_file = _Path(__file__).resolve()
        # Estructura esperada: <root>/src/common/utils.py -> root = parent.parent.parent
        project_root = current_file.parent.parent.parent
        if str(project_root / "src") not in _sys.path:
            _sys.path.insert(0, str(project_root / "src"))
    except Exception:  # pragma: no cover
        # Silencioso: evitar romper importaciones si algo inesperado ocurre
        pass


def get_first_workday_of_week(
    reference_date: Optional[date] = None, holidays_file: Optional[Path] = None
) -> date:
    """
    Obtiene el primer día laborable de la semana

    Args:
        reference_date: Fecha de referencia (si no se proporciona, usa la actual)
        holidays_file: Archivo con días festivos

    Returns:
        Fecha del primer día laborable de la semana
    """
    if reference_date is None:
        reference_date = date.today()

    # Obtener el lunes de la semana actual
    monday = reference_date - timedelta(days=reference_date.weekday())

    # Buscar el primer día laborable desde el lunes
    candidate_date = monday
    max_attempts = 7  # Máximo una semana de búsqueda
    attempts = 0

    while attempts < max_attempts:
        if is_workday(candidate_date, holidays_file):
            return candidate_date

        # Si no es laborable, probar el siguiente día
        candidate_date += timedelta(days=1)
        attempts += 1

    # Si no encontramos uno (caso excepcional), devolver el último candidato evaluado
    return candidate_date


def get_first_workday_of_month(
    reference_date: Optional[date] = None, holidays_file: Optional[Path] = None
) -> date:
    """
    Obtiene el primer día laborable del mes

    Args:
        reference_date: Fecha de referencia (si no se proporciona, usa la actual)
        holidays_file: Archivo con días festivos

    Returns:
        Fecha del primer día laborable del mes
    """
    if reference_date is None:
        reference_date = date.today()

    # Obtener el primer día del mes
    first_day = reference_date.replace(day=1)

    # Buscar el primer día laborable desde el primer día del mes
    candidate_date = first_day
    max_attempts = 31  # Máximo un mes de búsqueda
    attempts = 0

    while attempts < max_attempts:
        if is_workday(candidate_date, holidays_file):
            return candidate_date

        candidate_date += timedelta(days=1)
        attempts += 1

    # Si no encontramos un día laborable en el mes, devolver el primer día
    return first_day


def should_execute_weekly_task(
    db_connection, task_name: str, holidays_file: Optional[Path] = None, logger=None
) -> bool:
    """
    Determina si se debe ejecutar una tarea semanal en el primer día laborable de la semana

    Args:
        db_connection: Conexión a la base de datos de tareas
        task_name: Nombre de la tarea
        holidays_file: Archivo con días festivos
        logger: Logger para registrar eventos (opcional)

    Returns:
        True si se debe ejecutar la tarea
    """
    try:
        today = date.today()
        last_execution = get_last_task_execution_date(db_connection, task_name)

        if logger:
            logger.info(
                f"Verificando tarea semanal {task_name} - Última ejecución: "
                f"{last_execution}"
            )

        # Obtener el primer día laborable de esta semana
        first_workday_this_week = get_first_workday_of_week(today, holidays_file)

        if logger:
            logger.info(
                f"Primer día laborable de esta semana: {first_workday_this_week}"
            )

        # Si hoy no es el primer día laborable de la semana, no ejecutar
        if today != first_workday_this_week:
            if logger:
                logger.info(
                    f"Hoy ({today}) no es el primer día laborable de la semana "
                    f"({first_workday_this_week})"
                )
            return False

        # Si no hay registro previo, ejecutar
        if last_execution is None:
            if logger:
                logger.info(
                    f"No hay registro previo de tarea {task_name}, se requiere ejecutar"
                )
            return True

        # Si hoy es el primer día laborable de la semana y han pasado al menos 7 días
        # desde la última ejecución
        days_since_last = (today - last_execution).days
        should_execute = days_since_last >= 7  # Mínimo una semana

        if logger:
            logger.info(
                f"Hoy es el primer día laborable de la semana. Días desde última "
                f"ejecución: {days_since_last}, requiere: {should_execute}"
            )

        return should_execute

    except Exception as e:
        if logger:
            logger.error(
                f"Error determinando si requiere tarea semanal {task_name}: {e}"
            )
        else:
            logging.error(
                f"Error determinando si requiere tarea semanal {task_name}: {e}"
            )
        return True


def should_execute_monthly_task(
    db_connection, task_name: str, holidays_file: Optional[Path] = None, logger=None
) -> bool:
    """
    Determina si se debe ejecutar una tarea mensual en el primer día laborable del mes

    Args:
        db_connection: Conexión a la base de datos de tareas
        task_name: Nombre de la tarea
        holidays_file: Archivo con días festivos
        logger: Logger para registrar eventos (opcional)

    Returns:
        True si se debe ejecutar la tarea
    """
    try:
        today = date.today()
        last_execution = get_last_task_execution_date(db_connection, task_name)

        if logger:
            logger.info(
                f"Verificando tarea mensual {task_name} - Última ejecución: "
                f"{last_execution}"
            )

        # Obtener el primer día laborable de este mes
        first_workday_this_month = get_first_workday_of_month(today, holidays_file)

        if logger:
            logger.info(f"Primer día laborable de este mes: {first_workday_this_month}")

        # Si hoy no es el primer día laborable del mes, no ejecutar
        if today != first_workday_this_month:
            if logger:
                logger.info(
                    f"Hoy ({today}) no es el primer día laborable del mes "
                    f"({first_workday_this_month})"
                )
            return False

        # Si no hay registro previo, ejecutar
        if last_execution is None:
            if logger:
                logger.info(
                    f"No hay registro previo de tarea {task_name}, se requiere ejecutar"
                )
            return True

        # Si hoy es el primer día laborable del mes y han pasado al menos 30 días
        # desde la última ejecución
        days_since_last = (today - last_execution).days
        should_execute = days_since_last >= 30  # Mínimo un mes

        if logger:
            logger.info(
                f"Hoy es el primer día laborable del mes. Días desde última ejecución: "
                f"{days_since_last}, requiere: {should_execute}"
            )

        return should_execute

    except Exception as e:
        if logger:
            logger.error(
                f"Error determinando si requiere tarea mensual {task_name}: {e}"
            )
        else:
            logging.error(
                f"Error determinando si requiere tarea mensual {task_name}: {e}"
            )
        return True


def should_execute_quality_task(
    db_connection,
    task_name: str,
    preferred_weekday: int = 0,
    holidays_file: Optional[Path] = None,
    logger=None,
) -> bool:
    """Determina si se debe ejecutar una tarea de calidad semanal en el día laborable preferido.

    Reglas (según tests):
    - Si no hay ejecución previa y hoy es el día laborable preferido -> True
    - Si hoy NO es el día laborable preferido -> False (aunque haya pasado el intervalo)
    - Si existe ejecución previa, se ejecuta cuando han pasado >=7 días y hoy es el
      día laborable preferido.
    """
    try:
        today = date.today()
        # Hallar el próximo día laborable que cae en el preferred_weekday (esta semana)
        # Si hoy es ese día laborable preferido, candidate = today
        # De lo contrario, no es día de ejecución
        if today.weekday() != preferred_weekday or not is_workday(
            today, holidays_file
        ):
            return False

        last_execution = get_last_task_execution_date(db_connection, task_name)
        if last_execution is None:
            return True
        days_since = (today - last_execution).days
        return days_since >= 7
    except Exception as e:  # pragma: no cover
        if logger:
            logger.error(
                f"Error determinando si requiere tarea calidad {task_name}: {e}"
            )
        else:
            logging.error(
                f"Error determinando si requiere tarea calidad {task_name}: {e}"
            )
        return True