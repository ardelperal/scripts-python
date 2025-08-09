"""Tarea diaria que orquesta la generación y registro del informe de expedientes."""

from src.common.base_task import TareaDiaria
from src.common.database import AccessDatabase
from src.common.utils import register_email_in_database, get_admin_emails_string
from src.common.email.recipients_service import EmailRecipientsService
from src.common.email.registration_service import register_standard_report
from .expedientes_manager import ExpedientesManager


class ExpedientesTask(TareaDiaria):
    """Orquesta la lógica de la tarea de expedientes (consulta + registro correo)."""

    def __init__(self):
        super().__init__(
            name="EXPEDIENTES",
            script_filename="run_expedientes.py",
            task_names=["ExpedientesDiario"],
            frequency_days=1
        )
        # Conexión específica expedientes
        try:
            self.db_expedientes = AccessDatabase(self.config.get_db_expedientes_connection_string())
            self.logger.debug("Conexión BD Expedientes inicializada")
        except Exception as e:
            self.logger.error(f"Error inicializando BD Expedientes: {e}")
            self.db_expedientes = None

    def execute_specific_logic(self) -> bool:
        """Ejecuta la lógica principal: genera informe y registra email si aplica."""
        try:
            if not self.db_expedientes:
                self.logger.warning("Sin conexión a BD Expedientes; se omite informe")
                return True

            manager = ExpedientesManager(self.db_expedientes, self.db_tareas, logger=self.logger)
            html = manager.generate_expedientes_report_html()
            if not html:
                self.logger.info("Informe vacío: no se registra correo")
                return True

            # Servicio centralizado (fallback a función legacy)
            try:
                recipients_service = EmailRecipientsService(self.db_tareas, self.config, self.logger)
                recipients = recipients_service.get_admin_emails_string() or "ADMIN"
            except Exception:  # pragma: no cover
                recipients = get_admin_emails_string(self.db_tareas, self.config, self.logger) or "ADMIN"
            subject = "Informe Diario de Expedientes"
            return register_standard_report(
                self.db_tareas,
                application="EXPEDIENTES",
                subject=subject,
                body_html=html,
                recipients=recipients,
                admin_emails="",
                logger=self.logger
            )
        except Exception as e:
            self.logger.error(f"Error en execute_specific_logic Expedientes: {e}", extra={'context': 'execute_specific_logic'})
            return False

    def close_connections(self):
        """Cierra conexiones propias y de la superclase."""
        try:
            if getattr(self, 'db_expedientes', None):
                try:
                    self.db_expedientes.disconnect()
                except Exception as e:
                    self.logger.warning(f"Error cerrando BD Expedientes: {e}")
                finally:
                    self.db_expedientes = None
        finally:
            super().close_connections()