"""Tarea orquestadora refactorizada para No Conformidades.

Responsabilidad exclusiva: decidir ejecución (planificación) y delegar la
generación/parcial de informe a un manager puro (incremental) y registrar correo.

Refactor incremental: de momento sólo se genera informe parcial (secciones migradas)
si existen datos; el resto continúa en el manager legacy hasta completar migración.
"""
from __future__ import annotations

import os
import logging
from common.base_task import TareaDiaria
from common.database import AccessDatabase
from common.access_connection_pool import get_nc_connection_pool
from common.email.recipients_service import EmailRecipientsService
from common.email.registration_service import register_standard_report
from common.utils import get_admin_emails_string
from .nc_pure_manager import NoConformidadesManagerPure


class NoConformidadesTask(TareaDiaria):
    def __init__(self):
        super().__init__(
            name="NoConformidades",
            script_filename="run_no_conformidades.py",
            task_names=["NCTecnico", "NCCalidad"],
            frequency_days=int(os.getenv('NC_FRECUENCIA_DIAS', '1') or 1)
        )
        try:
            conn_str = self.config.get_db_no_conformidades_connection_string()
            pool = get_nc_connection_pool(conn_str)
            self.db_nc = AccessDatabase(conn_str, pool=pool)
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error inicializando pool NC: {e}")
            self.db_nc = None

    def execute_specific_logic(self) -> bool:
        self.logger.info(
            "Inicio lógica específica NC (parcial)",
            extra={'event': 'nc_task_logic_start', 'app': 'NC'}
        )
        try:
            if not self.db_nc:
                self.logger.warning("Sin conexión BD NC; se omite informe")
                return True

            manager = NoConformidadesManagerPure(self.db_nc, logger=self.logger)
            html = manager.generate_nc_report_html()
            if not html:
                self.logger.info("Informe NC parcial vacío: no se registra correo")
                return True

            # Recipients (administradores NC)
            try:
                recipients_service = EmailRecipientsService(self.db_tareas, self.config, self.logger)
                recipients = recipients_service.get_admin_emails_string() or "ADMIN"
            except Exception:  # pragma: no cover
                recipients = get_admin_emails_string(self.db_tareas, self.config, self.logger) or "ADMIN"

            subject = "Informe Parcial No Conformidades (NC)"
            ok = register_standard_report(
                self.db_tareas,
                application="NC",
                subject=subject,
                body_html=html,
                recipients=recipients,
                admin_emails="",
                logger=self.logger
            )
            self.logger.info(
                "Fin lógica específica NC (parcial)",
                extra={'event': 'nc_task_logic_end', 'success': bool(ok), 'app': 'NC'}
            )
            return bool(ok)
        except Exception as e:
            self.logger.error(f"Error en execute_specific_logic NC: {e}", extra={'context': 'execute_specific_logic_nc'})
            return False

    def close_connections(self):
        try:
            if getattr(self, 'db_nc', None):
                try:
                    self.db_nc.disconnect()
                except Exception as e:  # pragma: no cover
                    self.logger.warning(f"Error cerrando BD NC: {e}")
                finally:
                    self.db_nc = None
        finally:
            super().close_connections()