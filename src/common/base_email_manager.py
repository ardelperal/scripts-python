"""
Clase base para gestores de notificaciones por email
Proporciona funcionalidad común que puede ser extendida por módulos específicos
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime

# Obsoleto: HTMLReportGenerator movido a common.reporting.html_report_generator (archivo legacy)
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

    def send_simple_notification(
        self, to_addresses: list[str], subject: str, body: str, is_html: bool = False
    ) -> bool:
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
                to_address=";".join(to_addresses),
                subject=subject,
                body=body,
                is_html=is_html,
                from_app=self.module_name,
            )

            if resultado:
                self.logger.info(
                    f"Notificación enviada exitosamente a {len(to_addresses)} destinatarios"
                )
            else:
                self.logger.error("Error enviando notificación")

            return resultado

        except Exception as e:
            """Archivo legacy (BaseEmailNotificationManager) deprecado.

            Con la introducción de EmailManager y EmailServicesTask este archivo se mantiene
            solo para evitar errores de import en código antiguo. No usar en nuevo código.
            """

            class BaseEmailNotificationManager:  # pragma: no cover - legacy stub
                pass

