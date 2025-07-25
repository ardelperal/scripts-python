"""
Utilidades comunes para el proyecto
"""
import os
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional


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
                return str(date_value)  # Si no se puede parsear, devolver como string
        except Exception:
            return str(date_value)
    
    if isinstance(date_value, (datetime, date)):
        return date_value.strftime(format_str)
    
    return str(date_value)


def send_email(to_address: str, subject: str, body: str, is_html: bool = True) -> bool:
    """
    Envía un email (función placeholder)
    
    Args:
        to_address: Dirección de destino
        subject: Asunto del email
        body: Cuerpo del email
        is_html: Si el cuerpo es HTML
        
    Returns:
        True si se envió correctamente, False en caso contrario
    """
    # Esta es una función placeholder
    # En un entorno real, aquí iría la lógica de envío de email
    logging.info(f"Email enviado a {to_address} con asunto: {subject}")
    return True
