"""EmailServicesTask

Tarea continua que procesa correos pendientes tanto del origen 'correos'
como del origen 'tareas' usando EmailManager unificado.
"""
from __future__ import annotations

import logging

from common.base_task import TareaContinua

from .email_manager import EmailManager

logger = logging.getLogger(__name__)


class EmailServicesTask(TareaContinua):
    """Tarea continua para unificar el procesamiento de correos."""

    def __init__(
        self,
        name: str = "EmailServicesTask",
        script_filename: str = "run_email_services.py",
    ):
        # Usar el nombre real del runner para que BaseTask valide correctamente la ruta
        super().__init__(name=name, script_filename=script_filename)
        self._manager_correos: EmailManager | None = None
        self._manager_tareas: EmailManager | None = None

    def execute_specific_logic(self) -> bool:  # type: ignore[override]
        """Ejecuta la lógica específica de la tarea.

        1. Procesa correos generales (tabla correos).
        2. Procesa correos de tareas.
        Devuelve True si ambos pasos se ejecutan sin excepciones graves.
        """
        try:
            self.logger.info(
                "Iniciando procesamiento de correos generales",
                extra={
                    "event": "email_processing_start",
                    "source": "correos",
                    "task": self.name,
                },
            )
            self._manager_correos = EmailManager(email_source="correos")
            enviados_correos = self._manager_correos.process_pending_emails()
            self.logger.info(
                "Procesamiento de correos generales finalizado",
                extra={
                    "event": "email_processing_end",
                    "source": "correos",
                    "sent_count": enviados_correos,
                    "task": self.name,
                },
            )
        except Exception as e:
            self.logger.error(
                "Error procesando correos generales",
                extra={
                    "event": "email_processing_error",
                    "source": "correos",
                    "error": str(e),
                    "task": self.name,
                },
            )
            return False

        try:
            self.logger.info(
                "Iniciando procesamiento de correos de tareas",
                extra={
                    "event": "email_processing_start",
                    "source": "tareas",
                    "task": self.name,
                },
            )
            self._manager_tareas = EmailManager(email_source="tareas")
            enviados_tareas = self._manager_tareas.process_pending_emails()
            self.logger.info(
                "Procesamiento de correos de tareas finalizado",
                extra={
                    "event": "email_processing_end",
                    "source": "tareas",
                    "sent_count": enviados_tareas,
                    "task": self.name,
                },
            )
        except Exception as e:
            self.logger.error(
                "Error procesando correos de tareas",
                extra={
                    "event": "email_processing_error",
                    "source": "tareas",
                    "error": str(e),
                    "task": self.name,
                },
            )
            return False

        return True

    def close_connections(self):  # type: ignore[override]
        """Cierra/limpia referencias a managers (los pools se mantienen singleton)."""
        self._manager_correos = None
        self._manager_tareas = None
        self.logger.debug(
            "Managers liberados",
            extra={"event": "email_task_cleanup", "task": self.name},
        )
