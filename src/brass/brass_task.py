"""Tarea BRASS orquestadora siguiendo patrón ExpedientesTask."""
import os

from common.db.access_connection_pool import get_brass_connection_pool
from common.base_task import TareaDiaria
from common.db.database import AccessDatabase
from common.email.recipients_service import EmailRecipientsService
from common.email.registration_service import register_standard_report
from common.user_adapter import get_admin_emails_string

from .brass_manager import BrassManager


class BrassTask(TareaDiaria):
    """Orquesta obtención de equipos fuera de calibración y registro de correo."""

    def __init__(self, recipients_service_class=EmailRecipientsService):
        super().__init__(
            name="BRASS",
            script_filename="run_brass.py",
            task_names=["BRASSDiario"],
            frequency_days=int(os.getenv("BRASS_FRECUENCIA_DIAS", "1") or 1),
        )
        # Permite inyección en tests o futuras extensiones (DI)
        self.recipients_service_class = recipients_service_class
        try:
            conn_str = self.config.get_db_brass_connection_string()
            pool = get_brass_connection_pool(conn_str)
            self.db_brass = AccessDatabase(conn_str, pool=pool)
            self.logger.debug("Pool BRASS inicializado")
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error inicializando pool BRASS: {e}")
            self.db_brass = None

    def execute_specific_logic(self) -> bool:
        """Genera informe y registra correo si hay equipos fuera de calibración."""
        self.logger.info(
            "Inicio lógica específica BRASS",
            extra={"event": "brass_task_logic_start", "app": "BRASS"},
        )
        try:
            if not self.db_brass:
                self.logger.warning("Sin conexión BD BRASS; se omite informe")
                return True

            manager = BrassManager(self.db_brass, self.db_tareas, logger=self.logger)
            html = manager.generate_brass_report_html()
            if not html:
                self.logger.info("Informe BRASS vacío: no se registra correo")
                return True

            # Recipients service con fallback
            try:
                recipients_service = self.recipients_service_class(
                    self.db_tareas, self.config, self.logger
                )
                recipients = recipients_service.get_admin_emails_string() or "ADMIN"
            except Exception:  # pragma: no cover
                recipients = (
                    get_admin_emails_string(self.db_tareas, self.config, self.logger)
                    or "ADMIN"
                )

            subject = "Informe Equipos de Medida fuera de calibración (BRASS)"
            ok = register_standard_report(
                self.db_tareas,
                application="BRASS",
                subject=subject,
                body_html=html,
                recipients=recipients,
                admin_emails="",
                logger=self.logger,
            )
            self.logger.info(
                "Fin lógica específica BRASS",
                extra={
                    "event": "brass_task_logic_end",
                    "success": bool(ok),
                    "app": "BRASS",
                },
            )
            return bool(ok)
        except Exception as e:
            self.logger.error(
                f"Error en execute_specific_logic BRASS: {e}",
                extra={"context": "execute_specific_logic_brass"},
            )
            return False

    def close_connections(self):
        try:
            if getattr(self, "db_brass", None):
                try:
                    self.db_brass.disconnect()
                except Exception as e:  # pragma: no cover
                    self.logger.warning(f"Error cerrando BD BRASS: {e}")
                finally:
                    self.db_brass = None
        finally:
            super().close_connections()
