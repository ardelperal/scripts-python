"""
Utilidades comunes para el proyecto
"""
import os
import logging
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict

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
    pattern = r'(PWD|Password)=([^;]+);'
    return re.sub(pattern, r'\1=***;', connection_string, flags=re.IGNORECASE)


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None):
    """Configura el sistema de logging"""
    # Crear directorio de logs si no existe
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configurar logging
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Formato de log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para archivo
    handlers = []
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Configurar logging básico
    logging.basicConfig(
        level=level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


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
            with open(holidays_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and str(check_date) in line:
                        return False
        except Exception as e:
            logging.warning(f"Error leyendo archivo de festivos: {e}")
    
    return True


def is_night_time(current_time: Optional[datetime] = None) -> bool:
    """
    Verifica si es horario nocturno (20:00 - 07:00)
    
    Args:
        current_time: Hora actual (si no se proporciona, usa la actual)
        
    Returns:
        True si es horario nocturno
    """
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
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(css_file_path, 'r', encoding=encoding) as f:
                content = f.read()
                logging.info(f"Archivo CSS cargado exitosamente con encoding {encoding}")
                return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logging.error(f"Error leyendo archivo CSS {css_file_path}: {e}")
            break
    
    logging.warning(f"No se pudo cargar el archivo CSS {css_file_path} con ningún encoding, usando CSS por defecto")
    # CSS básico por defecto
    return """
    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
    .centrado { text-align: center; }
    .ColespanArriba { background-color: #4CAF50; color: white; font-weight: bold; text-align: center; }
    table { border-collapse: collapse; width: 100%; }
    td, th { border: 1px solid #ddd; padding: 8px; }
    strong { font-weight: bold; }
    """


def generate_html_header(title: str, css_content: str) -> str:
    """
    Genera el header HTML con CSS incorporado
    
    Args:
        title: Título de la página
        css_content: Contenido CSS
        
    Returns:
        Header HTML como string
    """
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <title>{title}</title>
    <meta charset="UTF-8" />
    <style type="text/css">
        {css_content}
    </style>
</head>
<body>
"""


def generate_html_footer() -> str:
    """Genera el footer HTML"""
    return """
</body>
</html>
"""


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


def get_admin_users(db_connection) -> List[Dict[str, str]]:
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


def get_admin_emails_string(db_connection) -> str:
    """
    Obtiene la cadena de correos de administradores separados por ;
    
    Args:
        db_connection: Conexión a la base de datos de tareas
        
    Returns:
        String con correos separados por ;
    """
    try:
        admin_users = get_admin_users(db_connection)
        emails = [user['CorreoUsuario'] for user in admin_users if user['CorreoUsuario']]
        return ';'.join(emails)
    except Exception as e:
        logging.error(f"Error obteniendo emails de administradores: {e}")
        return ""


def send_email(to_address: str, subject: str, body: str, is_html: bool = True, 
               from_app: str = "Sistema", attachments: List[str] = None) -> bool:
    """
    Envía un email usando SMTP (implementación real basada en legacy VBS)
    
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
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        from pathlib import Path
        
        # Configuración SMTP basada en legacy VBS
        smtp_server = config.smtp_server
        smtp_port = config.smtp_port
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = f"{from_app}.DySN@telefonica.com"
        msg['To'] = to_address
        msg['Subject'] = subject
        
        # Añadir BCC para administrador (como en VBS legacy)
        admin_email = "Andres.RomandelPeral@telefonica.com"
        if admin_email not in to_address:
            msg['Bcc'] = admin_email
        
        # Añadir cuerpo del mensaje
        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Añadir archivos adjuntos si existen
        if attachments:
            for attachment_path in attachments:
                if Path(attachment_path).exists():
                    with open(attachment_path, 'rb') as f:
                        attach = MIMEApplication(f.read())
                        attach.add_header('Content-Disposition', 'attachment', 
                                        filename=Path(attachment_path).name)
                        msg.attach(attach)
        
        # Enviar email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Sin autenticación como en VBS legacy
            server.sendmail(msg['From'], [to_address, admin_email], msg.as_string())
        
        logging.info(f"Email enviado exitosamente a {to_address} con asunto: {subject}")
        return True
        
    except Exception as e:
        logging.error(f"Error enviando email a {to_address}: {e}")
        return False


def send_notification_email(to_address: str, subject: str, body: str, is_html: bool = True, 
                           from_app: str = "Sistema", attachments: List[str] = None) -> bool:
    """
    Envía un email de notificación (función mejorada de send_email)
    
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
        logging.info(f"Enviando notificación a {to_address} con asunto: {subject}")
        return send_email(to_address, subject, body, is_html, from_app, attachments)
    except Exception as e:
        logging.error(f"Error enviando notificación: {e}")
        return False


def register_email_in_database(db_connection, application: str, subject: str, body: str, 
                              recipients: str, admin_emails: str = "") -> bool:
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
            "FechaGrabacion": datetime.now()
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


def register_task_completion(db_connection, task_name: str, execution_date: Optional[date] = None) -> bool:
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
        
        # Verificar si ya existe registro para la tarea (sin importar la fecha)
        query_check = """
            SELECT COUNT(*) as Count 
            FROM TbTareas 
            WHERE Tarea = ?
        """
        
        result = db_connection.execute_query(query_check, (task_name,))
        
        if result and result[0]['Count'] > 0:
            # Actualizar registro existente - solo cambiar la fecha
            task_data = {
                "Fecha": execution_date,
                "Realizado": "Sí"
            }
            success = db_connection.update_record(
                "TbTareas", 
                task_data, 
                "Tarea = ?", 
                (task_name,)
            )
            logging.info(f"Tarea {task_name} actualizada con fecha {execution_date}")
        else:
            # Insertar nuevo registro
            task_data = {
                "Tarea": task_name,
                "Fecha": execution_date,
                "Realizado": "Sí"
            }
            success = db_connection.insert_record("TbTareas", task_data)
            logging.info(f"Tarea {task_name} creada con fecha {execution_date}")
        
        if success:
            logging.info(f"Tarea {task_name} registrada como completada")
        else:
            logging.error(f"Error registrando tarea {task_name}")
        
        return success
        
    except Exception as e:
        logging.error(f"Error registrando finalización de tarea: {e}")
        return False


def get_technical_users(app_id: str, config, logger) -> List[Dict[str, str]]:
    """
    Obtiene la lista de usuarios técnicos desde la base de datos
    
    Args:
        app_id: ID de la aplicación
        config: Configuración de la aplicación
        logger: Logger para registrar eventos
        
    Returns:
        Lista de usuarios técnicos
    """
    try:
        from .database import AccessDatabase
        
        # Usar la conexión de tareas para obtener usuarios
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())
        
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario 
            FROM TbUsuariosAplicaciones ua 
            INNER JOIN TbUsuariosAplicacionesTareas uat ON ua.CorreoUsuario = uat.CorreoUsuario 
            WHERE ua.ParaTareasProgramadas = True 
            AND ua.FechaBaja IS NULL 
            AND uat.EsTecnico = 'Sí'
            AND uat.Aplicacion = ?
        """
        
        result = db_connection.execute_query(query, (app_id,))
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios técnicos para {app_id}: {e}")
        return []


def get_quality_users(app_id: str, config, logger) -> List[Dict[str, str]]:
    """
    Obtiene la lista de usuarios de calidad desde la base de datos
    
    Args:
        app_id: ID de la aplicación
        config: Configuración de la aplicación
        logger: Logger para registrar eventos
        
    Returns:
        Lista de usuarios de calidad
    """
    try:
        from .database import AccessDatabase
        
        # Usar la conexión de tareas para obtener usuarios
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())
        
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario 
            FROM TbUsuariosAplicaciones ua 
            INNER JOIN TbUsuariosAplicacionesTareas uat ON ua.CorreoUsuario = uat.CorreoUsuario 
            WHERE ua.ParaTareasProgramadas = True 
            AND ua.FechaBaja IS NULL 
            AND uat.EsCalidad = 'Sí'
            AND uat.Aplicacion = ?
        """
        
        result = db_connection.execute_query(query, (app_id,))
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios de calidad para {app_id}: {e}")
        return []


def get_economy_users(config, logger) -> List[Dict[str, str]]:
    """
    Obtiene la lista de usuarios de economía desde la base de datos
    
    Args:
        config: Configuración de la aplicación
        logger: Logger para registrar eventos
        
    Returns:
        Lista de usuarios de economía
    """
    try:
        from .database import AccessDatabase
        
        # Usar la conexión de tareas para obtener usuarios
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())
        
        query = """
            SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario 
            FROM TbUsuariosAplicaciones ua 
            INNER JOIN TbUsuariosAplicacionesTareas uat ON ua.CorreoUsuario = uat.CorreoUsuario 
            WHERE ua.ParaTareasProgramadas = True 
            AND ua.FechaBaja IS NULL 
            AND uat.EsEconomia = 'Sí'
            AND uat.IDAplicacion = ?
        """
        
        result = db_connection.execute_query(query, (config.app_id_agedys,))
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios de economía: {e}")
        return []


def get_user_email(username: str, config, logger=None) -> str:
    """
    Obtiene el email de un usuario específico desde la base de datos
    
    Args:
        username: Nombre de usuario (UsuarioRed)
        config: Configuración de la aplicación
        logger: Logger para registrar eventos (opcional)
        
    Returns:
        Email del usuario o cadena vacía si no se encuentra
    """
    try:
        from .database import AccessDatabase
        
        # Usar la conexión de tareas para obtener el email
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())
        
        query = """
            SELECT CorreoUsuario 
            FROM TbUsuariosAplicaciones 
            WHERE UsuarioRed = ? 
            AND ParaTareasProgramadas = True 
            AND FechaBaja IS NULL
        """
        
        result = db_connection.execute_query(query, (username,))
        
        if result and len(result) > 0:
            return result[0].get('CorreoUsuario', '')
        
        return ""
        
    except Exception as e:
        if logger:
            logger.error(f"Error obteniendo email para usuario {username}: {e}")
        else:
            logging.error(f"Error obteniendo email para usuario {username}: {e}")
        return ""


def get_quality_emails_string(app_id: str, config, logger) -> str:
    """
    Obtiene la cadena de correos de usuarios de calidad separados por ;
    
    Args:
        app_id: ID de la aplicación
        config: Configuración de la aplicación
        logger: Logger para registrar eventos
        
    Returns:
        String con correos separados por ;
    """
    try:
        quality_users = get_quality_users(app_id, config, logger)
        emails = [user['CorreoUsuario'] for user in quality_users if user['CorreoUsuario']]
        return ';'.join(emails)
    except Exception as e:
        logger.error(f"Error obteniendo emails de calidad para {app_id}: {e}")
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
        emails = [user['CorreoUsuario'] for user in technical_users if user['CorreoUsuario']]
        return ';'.join(emails)
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
        emails = [user['CorreoUsuario'] for user in economy_users if user['CorreoUsuario']]
        return ';'.join(emails)
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
        
        result = db_connection.execute_query(query, (task_name,))
        
        if result and result[0]['UltimaFecha']:
            fecha = result[0]['UltimaFecha']
            # Convertir a date si es datetime
            if isinstance(fecha, datetime):
                return fecha.date()
            return fecha
            
        return None
        
    except Exception as e:
        logging.error(f"Error obteniendo fecha de última ejecución para {task_name}: {e}")
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


def should_execute_task(db_connection, task_name: str, frequency_days: int, logger=None) -> bool:
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
                logger.info(f"No hay registro previo de tarea {task_name}, se requiere ejecutar")
            return True
        
        days_since_last = (date.today() - last_execution).days
        should_execute = days_since_last >= frequency_days
        
        if logger:
            logger.info(f"Última ejecución tarea {task_name}: {last_execution}, "
                       f"días transcurridos: {days_since_last}, requiere: {should_execute}")
        
        return should_execute
        
    except Exception as e:
        if logger:
            logger.error(f"Error determinando si requiere tarea {task_name}: {e}")
        else:
            logging.error(f"Error determinando si requiere tarea {task_name}: {e}")
        return True
