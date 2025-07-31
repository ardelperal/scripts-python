"""
Clase base para gestores de notificaciones por email
Proporciona funcionalidad común que puede ser extendida por módulos específicos
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime

from .html_report_generator import HTMLReportGenerator
from .utils import send_email, setup_logging


class BaseEmailNotificationManager(ABC):
    """
    Clase base para gestores de notificaciones por email.
    
    Proporciona funcionalidad común para el envío de notificaciones
    y puede ser extendida por módulos específicos.
    """
    
    def __init__(self, module_name: str):
        """
        Inicializa el gestor base de notificaciones.
        
        Args:
            module_name: Nombre del módulo que usa este gestor
        """
        self.module_name = module_name
        setup_logging()
        self.logger = logging.getLogger(f"{module_name}_email_notifications")
        self.html_generator = HTMLReportGenerator()
    
    def send_simple_notification(self, 
                                to_addresses: List[str], 
                                subject: str, 
                                body: str, 
                                is_html: bool = False) -> bool:
        """
        Envía una notificación simple.
        
        Args:
            to_addresses: Lista de direcciones de email
            subject: Asunto del email
            body: Cuerpo del email
            is_html: Si el cuerpo es HTML
            
        Returns:
            True si se envió correctamente
        """
        try:
            if not to_addresses:
                self.logger.warning("No hay destinatarios para la notificación")
                return False
            
            resultado = send_email(
                to_address=';'.join(to_addresses),
                subject=subject,
                body=body,
                is_html=is_html
            )
            
            if resultado:
                self.logger.info(f"Notificación enviada exitosamente a {len(to_addresses)} destinatarios")
            else:
                self.logger.error("Error enviando notificación")
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación simple: {e}")
            return False
    
    def send_html_report(self, 
                        to_addresses: List[str], 
                        subject: str, 
                        html_content: str) -> bool:
        """
        Envía un reporte HTML.
        
        Args:
            to_addresses: Lista de direcciones de email
            subject: Asunto del email
            html_content: Contenido HTML del reporte
            
        Returns:
            True si se envió correctamente
        """
        return self.send_simple_notification(
            to_addresses=to_addresses,
            subject=subject,
            body=html_content,
            is_html=True
        )
    
    def send_error_notification(self, error_message: str, admin_emails: List[str]) -> bool:
        """
        Envía una notificación de error a los administradores.
        
        Args:
            error_message: Mensaje de error
            admin_emails: Lista de emails de administradores
            
        Returns:
            True si se envió correctamente
        """
        subject = f"Error en {self.module_name}"
        body = f"""
        <h2>Error en {self.module_name}</h2>
        <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Error:</strong> {error_message}</p>
        <p>Por favor, revise el sistema lo antes posible.</p>
        """
        
        return self.send_html_report(
            to_addresses=admin_emails,
            subject=subject,
            html_content=body
        )
    
    def send_success_notification(self, message: str, admin_emails: List[str]) -> bool:
        """
        Envía una notificación de éxito a los administradores.
        
        Args:
            message: Mensaje de éxito
            admin_emails: Lista de emails de administradores
            
        Returns:
            True si se envió correctamente
        """
        subject = f"Operación completada en {self.module_name}"
        body = f"""
        <h2>Operación Completada - {self.module_name}</h2>
        <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Resultado:</strong> {message}</p>
        <p>La operación se completó exitosamente.</p>
        """
        
        return self.send_html_report(
            to_addresses=admin_emails,
            subject=subject,
            html_content=body
        )
    
    @abstractmethod
    def get_admin_emails(self) -> List[str]:
        """
        Obtiene la lista de emails de administradores.
        Debe ser implementado por cada módulo específico.
        
        Returns:
            Lista de emails de administradores
        """
        raise NotImplementedError("Subclases deben implementar get_admin_emails()")
    
    @abstractmethod
    def generate_module_report(self, **kwargs) -> str:
        """
        Genera un reporte específico del módulo.
        Debe ser implementado por cada módulo específico.
        
        Returns:
            Contenido HTML del reporte
        """
        raise NotImplementedError("Subclases deben implementar generate_module_report()")
    
    def log_email_sent(self, to_addresses: List[str], subject: str, success: bool):
        """
        Registra el envío de un email en los logs.
        
        Args:
            to_addresses: Destinatarios del email
            subject: Asunto del email
            success: Si el envío fue exitoso
        """
        status = "exitosamente" if success else "con error"
        recipients_str = ", ".join(to_addresses)
        self.logger.info(f"Email '{subject}' enviado {status} a: {recipients_str}")