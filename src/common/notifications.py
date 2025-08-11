"""
Módulo de notificaciones para el sistema.

Este módulo proporciona funcionalidades para enviar notificaciones
por email y otros medios de comunicación.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationManager:
    """Gestor de notificaciones del sistema."""

    def __init__(self):
        """Inicializar el gestor de notificaciones."""
        # Configuración desde variables de entorno
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_from = os.getenv("SMTP_FROM", "noreply@example.com")
        # Valor por defecto alineado con los tests unitarios
        self.default_recipient = os.getenv("DEFAULT_RECIPIENT", "admin@example.com")

        # Configuración opcional de autenticación
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

    def send_email(
        self, to: list[str], subject: str, body: str, html_body: Optional[str] = None
    ) -> bool:
        """
        Envía un email de notificación.

        Args:
            to: Lista de destinatarios
            subject: Asunto del email
            body: Cuerpo del email en texto plano
            html_body: Cuerpo del email en HTML (opcional)

        Returns:
            bool: True si el email se envió correctamente
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = ", ".join(to)

            # Agregar parte de texto plano
            text_part = MIMEText(body, "plain", "utf-8")
            msg.attach(text_part)

            # Agregar parte HTML si se proporciona
            if html_body:
                html_part = MIMEText(html_body, "html", "utf-8")
                msg.attach(html_part)

            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.send_message(msg)

            logger.info(f"Email enviado exitosamente a {', '.join(to)}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            return False

    def send_error_notification(
        self, error_message: str, module: str = "Sistema"
    ) -> bool:
        """
        Envía una notificación de error al administrador.

        Args:
            error_message: Mensaje de error
            module: Módulo donde ocurrió el error

        Returns:
            bool: True si la notificación se envió correctamente
        """
        subject = f"Error en {module}"
        body = f"""
Se ha producido un error en el sistema:

Módulo: {module}
Error: {error_message}

Por favor, revise los logs para más detalles.
        """

        return self.send_email([self.default_recipient], subject, body.strip())

    def send_success_notification(self, message: str, module: str = "Sistema") -> bool:
        """
        Envía una notificación de éxito.

        Args:
            message: Mensaje de éxito
            module: Módulo que completó la operación

        Returns:
            bool: True si la notificación se envió correctamente
        """
        subject = f"Operación completada en {module}"
        body = f"""
Operación completada exitosamente:

Módulo: {module}
Resultado: {message}
        """

        return self.send_email([self.default_recipient], subject, body.strip())


def send_notification(message: str, notification_type: str = "info") -> bool:
    """
    Función de conveniencia para enviar notificaciones rápidas.

    Args:
        message: Mensaje a enviar
        notification_type: Tipo de notificación ('info', 'error', 'success')

    Returns:
        bool: True si la notificación se envió correctamente
    """
    manager = NotificationManager()

    if notification_type == "error":
        return manager.send_error_notification(message)
    elif notification_type == "success":
        return manager.send_success_notification(message)
    else:
        return manager.send_email(
            [manager.default_recipient], "Notificación del Sistema", message
        )


# Instancia global para uso directo
notification_manager = NotificationManager()
