"""
Utilidades comunes para el proyecto
"""
import os
import logging
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional


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
    """Configura el sistema de logging y devuelve un logger"""
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
    
    # Devolver un logger configurado
    logger = logging.getLogger(__name__)
    return logger


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
                return str(date_value)  # Si no se puede parsear, devolver como string
        except Exception:
            return str(date_value)
    
    if isinstance(date_value, (datetime, date)):
        return date_value.strftime(format_str)
    
    return str(date_value)


def send_email(to_address: str, subject: str, body: str, is_html: bool = True, 
               cc_address: str = None, bcc_address: str = None, 
               attachment_path: str = None, config=None, logger=None) -> bool:
    """
    Envía un email usando la configuración SMTP del proyecto.
    
    Args:
        to_address: Dirección(es) de destino (separadas por ; si son múltiples)
        subject: Asunto del email
        body: Cuerpo del email
        is_html: Si el cuerpo es HTML (default: True)
        cc_address: Dirección(es) con copia (separadas por ; si son múltiples)
        bcc_address: Dirección(es) con copia oculta (separadas por ; si son múltiples)
        attachment_path: Ruta del archivo adjunto (opcional)
        config: Objeto de configuración (si no se proporciona, se usa el global)
        logger: Logger (si no se proporciona, se usa el del módulo)
        
    Returns:
        True si se envió correctamente, False en caso contrario
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    from pathlib import Path
    
    if config is None:
        from .config import config
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = config.smtp_user or config.default_recipient
        msg['To'] = to_address
        msg['Subject'] = subject
        
        # Agregar destinatarios con copia si se especifican
        if cc_address:
            msg['Cc'] = cc_address
        if bcc_address:
            msg['Bcc'] = bcc_address
        
        # Agregar cuerpo del mensaje
        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Agregar archivo adjunto si se especifica
        if attachment_path and Path(attachment_path).exists():
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {Path(attachment_path).name}'
                    )
                    msg.attach(part)
                logger.debug(f"Archivo adjunto agregado: {attachment_path}")
            except Exception as e:
                logger.warning(f"No se pudo agregar el archivo adjunto {attachment_path}: {e}")
        
        # Preparar lista de destinatarios
        recipients = []
        if to_address:
            recipients.extend([addr.strip() for addr in to_address.split(';') if addr.strip()])
        if cc_address:
            recipients.extend([addr.strip() for addr in cc_address.split(';') if addr.strip()])
        if bcc_address:
            recipients.extend([addr.strip() for addr in bcc_address.split(';') if addr.strip()])
        
        if not recipients:
            logger.error("No se especificaron destinatarios válidos")
            return False
        
        # Enviar email
        logger.debug(f"Conectando a servidor SMTP: {config.smtp_server}:{config.smtp_port}")
        
        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            # Configurar TLS si está habilitado
            if getattr(config, 'smtp_tls', False):
                server.starttls()
                logger.debug("TLS habilitado")
            
            # Autenticación si está configurada
            if (getattr(config, 'smtp_auth', False) and 
                getattr(config, 'smtp_user', None) and 
                getattr(config, 'smtp_password', None)):
                server.login(config.smtp_user, config.smtp_password)
                logger.debug("Autenticación SMTP exitosa")
            
            # Enviar mensaje
            server.sendmail(msg['From'], recipients, msg.as_string())
            
        logger.info(f"Email enviado exitosamente a: {to_address}")
        if cc_address:
            logger.info(f"Con copia a: {cc_address}")
        if bcc_address:
            logger.info(f"Con copia oculta a: {bcc_address}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email a {to_address}: {e}")
        return False


def get_admin_emails_string(config=None, logger=None) -> str:
    """
    Obtiene una cadena con los correos de administradores separados por punto y coma.
    
    Args:
        config: Objeto de configuración (opcional)
        logger: Logger (opcional)
        
    Returns:
        String con correos separados por ; o cadena vacía si no hay administradores
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        admin_users = get_admin_users(config, logger)
        emails = [user.get('CorreoUsuario') for user in admin_users if user.get('CorreoUsuario')]
        return ";".join(emails)
    except Exception as e:
        logger.error(f"Error obteniendo cadena de correos administradores: {e}")
        return ""


def get_quality_emails_string(application_id: int, config=None, logger=None) -> str:
    """
    Obtiene una cadena con los correos de usuarios de calidad separados por punto y coma.
    
    Args:
        application_id: ID de la aplicación
        config: Objeto de configuración (opcional)
        logger: Logger (opcional)
        
    Returns:
        String con correos separados por ; o cadena vacía si no hay usuarios de calidad
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        quality_users = get_quality_users(application_id, config, logger)
        emails = [user.get('CorreoUsuario') for user in quality_users if user.get('CorreoUsuario')]
        return ";".join(emails)
    except Exception as e:
        logger.error(f"Error obteniendo cadena de correos de calidad: {e}")
        return ""


def get_technical_emails_string(application_id: int, config=None, logger=None) -> str:
    """
    Obtiene una cadena con los correos de usuarios técnicos separados por punto y coma.
    
    Args:
        application_id: ID de la aplicación
        config: Objeto de configuración (opcional)
        logger: Logger (opcional)
        
    Returns:
        String con correos separados por ; o cadena vacía si no hay usuarios técnicos
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        technical_users = get_technical_users(application_id, config, logger)
        emails = [user.get('CorreoUsuario') for user in technical_users if user.get('CorreoUsuario')]
        return ";".join(emails)
    except Exception as e:
        logger.error(f"Error obteniendo cadena de correos técnicos: {e}")
        return ""


def register_email_in_database(recipients: str, subject: str, body: str, 
                              application: str = None, config=None, logger=None) -> bool:
    """
    Registra un correo en la base de datos de correos para envío posterior.
    
    Args:
        recipients: Destinatarios del correo (separados por ;)
        subject: Asunto del correo
        body: Cuerpo del correo
        application: Nombre de la aplicación que registra el correo
        config: Objeto de configuración (opcional)
        logger: Logger (opcional)
        
    Returns:
        True si se registró correctamente, False en caso contrario
    """
    from .database import AccessDatabase
    from datetime import datetime
    
    if config is None:
        from .config import config
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Conectar a la base de datos de correos
        connection_string = config.get_db_correos_connection_string()
        db = AccessDatabase(connection_string)
        db.connect()
        
        # Obtener el próximo ID
        max_id_result = db.execute_query("SELECT MAX(IDCorreo) as MaxID FROM TbCorreosEnviados")
        next_id = 1
        if max_id_result and max_id_result[0].get('MaxID'):
            next_id = max_id_result[0]['MaxID'] + 1
        
        # Preparar datos del correo
        email_data = {
            "IDCorreo": next_id,
            "Aplicacion": application or "Sistema",
            "Destinatarios": recipients,
            "Asunto": subject,
            "Cuerpo": body,
            "FechaCreacion": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "FechaEnvio": None  # NULL para indicar que no se ha enviado
        }
        
        # Insertar el registro
        success = db.insert_record("TbCorreosEnviados", email_data)
        db.disconnect()
        
        if success:
            logger.info(f"Correo registrado correctamente en BD con ID {next_id}")
            return True
        else:
            logger.error("Error registrando correo en BD")
            return False
            
    except Exception as e:
        logger.error(f"Error registrando correo en BD: {e}")
        return False


def send_notification_email(to_users: str, subject: str, body_html: str, 
                           email_type: str = None, config=None, logger=None) -> bool:
    """
    Función de alto nivel para enviar correos de notificación.
    Combina el envío directo con el registro en base de datos.
    
    Args:
        to_users: Destinatarios (separados por ;)
        subject: Asunto del correo
        body_html: Cuerpo del correo en HTML
        email_type: Tipo de correo para logging
        config: Objeto de configuración (opcional)
        logger: Logger (opcional)
        
    Returns:
        True si se envió correctamente, False en caso contrario
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Intentar envío directo primero
        success = send_email(
            to_address=to_users,
            subject=subject,
            body=body_html,
            is_html=True,
            config=config,
            logger=logger
        )
        
        if success:
            logger.info(f"Correo enviado directamente - Tipo: {email_type}, Destinatarios: {to_users}")
        else:
            # Si falla el envío directo, registrar en BD para envío posterior
            logger.warning(f"Envío directo falló, registrando en BD para envío posterior")
            register_success = register_email_in_database(
                recipients=to_users,
                subject=subject,
                body=body_html,
                application=email_type,
                config=config,
                logger=logger
            )
            
            if register_success:
                logger.info(f"Correo registrado en BD para envío posterior - Tipo: {email_type}")
                return True
            else:
                logger.error(f"Error tanto en envío directo como en registro en BD")
                return False
        
        return success
        
    except Exception as e:
        logger.error(f"Error en send_notification_email: {e}")
        return False


def get_application_users(application_id: int, user_type: str, config, logger=None):
    """
    Obtiene usuarios de una aplicación específica según el tipo solicitado.
    
    Args:
        application_id: ID de la aplicación (expedientes=19, brass=6, noconformidades=8, agedys=3)
        user_type: Tipo de usuario ('quality', 'technical', 'admin')
        config: Objeto de configuración
        logger: Logger opcional
        
    Returns:
        Lista de usuarios que cumplen los criterios
    """
    from .database import AccessDatabase
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Obtener la cadena de conexión a la base de datos de lanzadera
        connection_string = config.get_db_lanzadera_connection_string()
        
        # Crear conexión
        db = AccessDatabase(connection_string)
        db.connect()
        
        # Construir la consulta según el tipo de usuario
        if user_type.lower() == 'admin':
            query = """
                SELECT TbUsuariosAplicaciones.* 
                FROM TbUsuariosAplicaciones 
                WHERE (((TbUsuariosAplicaciones.EsAdministrador)='Sí'));
            """
            params = ()
        elif user_type.lower() == 'quality':
            query = """
                SELECT TbUsuariosAplicaciones.* 
                FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesPermisos ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario 
                WHERE (((TbUsuariosAplicacionesPermisos.IDAplicacion)=?) AND ((TbUsuariosAplicacionesPermisos.EsUsuarioCalidad)='Sí'));
            """
            params = (application_id,)
        elif user_type.lower() == 'technical':
            query = """
                SELECT TbUsuariosAplicaciones.* 
                FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesPermisos ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario 
                WHERE (((TbUsuariosAplicacionesPermisos.IDAplicacion)=?) AND ((TbUsuariosAplicacionesPermisos.EsUsuarioTecnico)='Sí'));
            """
            params = (application_id,)
        else:
            raise ValueError(f"Tipo de usuario no válido: {user_type}. Debe ser 'quality', 'technical' o 'admin'")
        
        logger.info(f"Obteniendo usuarios de tipo '{user_type}' para aplicación {application_id}")
        
        # Ejecutar consulta
        result = db.execute_query(query, params)
        usuarios = result if isinstance(result, list) else []
        
        logger.info(f"Encontrados {len(usuarios)} usuarios de tipo '{user_type}'")
        
        # Cerrar conexión
        db.disconnect()
        
        return usuarios
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios de tipo '{user_type}': {e}")
        return []


# Las constantes ahora se obtienen de la configuración, pero mantenemos estas como fallback
APPLICATION_IDS = {
    'expedientes': 19,
    'brass': 6,
    'noconformidades': 8,
    'agedys': 3
}


def get_quality_users(application_id: int, config, logger=None):
    """
    Obtiene usuarios de calidad para una aplicación específica.
    
    Args:
        application_id: ID de la aplicación
        config: Objeto de configuración
        logger: Logger opcional
        
    Returns:
        Lista de usuarios de calidad
    """
    return get_application_users(application_id, 'quality', config, logger)


def get_technical_users(application_id: int, config, logger=None):
    """
    Obtiene usuarios técnicos para una aplicación específica.
    
    Args:
        application_id: ID de la aplicación
        config: Objeto de configuración
        logger: Logger opcional
        
    Returns:
        Lista de usuarios técnicos
    """
    return get_application_users(application_id, 'technical', config, logger)


def get_admin_users(config, logger=None):
    """
    Obtiene usuarios administradores (no depende de aplicación específica).
    
    Args:
        config: Objeto de configuración
        logger: Logger opcional
        
    Returns:
        Lista de usuarios administradores
    """
    return get_application_users(0, 'admin', config, logger)  # ID 0 porque no se usa para administradores


def get_user_email(username: str, application_id: int, config, logger=None):
    """
    Obtiene el correo electrónico de un usuario específico para una aplicación.
    
    Args:
        username: Nombre de usuario
        application_id: ID de la aplicación
        config: Objeto de configuración
        logger: Logger opcional
        
    Returns:
        Correo electrónico del usuario o None si no se encuentra
    """
    from .database import AccessDatabase
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Obtener la cadena de conexión a la base de datos de lanzadera
        connection_string = config.get_db_lanzadera_connection_string()
        
        # Crear conexión
        db = AccessDatabase(connection_string)
        db.connect()
        
        # Consulta para obtener el correo del usuario
        query = """
            SELECT Correo 
            FROM TbUsuariosAplicaciones 
            WHERE Usuario = ? AND IDAplicacion = ?
        """
        
        logger.debug(f"Obteniendo correo para usuario '{username}' en aplicación {application_id}")
        
        # Ejecutar consulta
        result = db.execute_query(query, (username, application_id))
        
        # Cerrar conexión
        db.disconnect()
        
        if result and len(result) > 0:
            email = result[0].get('Correo')
            logger.debug(f"Correo encontrado para usuario '{username}': {email}")
            return email
        else:
            logger.warning(f"No se encontró correo para usuario '{username}' en aplicación {application_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error obteniendo correo para usuario '{username}': {e}")
        return None


def get_user_by_email(email: str, config, logger=None):
    """
    Obtiene información de un usuario por su correo electrónico.
    
    Args:
        email: Correo electrónico del usuario
        config: Objeto de configuración
        logger: Logger opcional
        
    Returns:
        Información del usuario o None si no se encuentra
    """
    from .database import AccessDatabase
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Obtener la cadena de conexión a la base de datos de lanzadera
        connection_string = config.get_db_lanzadera_connection_string()
        
        # Crear conexión
        db = AccessDatabase(connection_string)
        db.connect()
        
        # Consulta para obtener información del usuario
        query = """
            SELECT * 
            FROM TbUsuariosAplicaciones 
            WHERE Correo = ?
        """
        
        logger.debug(f"Obteniendo información para correo '{email}'")
        
        # Ejecutar consulta
        result = db.execute_query(query, (email,))
        
        # Cerrar conexión
        db.disconnect()
        
        if result and len(result) > 0:
            user_info = result[0]
            logger.debug(f"Usuario encontrado para correo '{email}': {user_info.get('Usuario', 'N/A')}")
            return user_info
        else:
            logger.warning(f"No se encontró usuario para correo '{email}'")
            return None
            
    except Exception as e:
        logger.error(f"Error obteniendo usuario para correo '{email}': {e}")
        return None
