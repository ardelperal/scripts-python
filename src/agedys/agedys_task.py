"""AgedysTask refactorizada: usa AgedysManager y patrón execute_specific_logic.

Responsabilidad: decidir ejecución (frecuencia) y registrar correo estándar si hay contenido.
"""
import os
from common.base_task import TareaDiaria
from common.database import AccessDatabase
from common.access_connection_pool import get_agedys_connection_pool
from common.email.recipients_service import EmailRecipientsService
from common.email.registration_service import register_standard_report  # fallback temporal
from .agedys_manager import AgedysManager


class AgedysTask(TareaDiaria):
    def __init__(self):
        super().__init__(
            name="AGEDYS",
            script_filename="run_agedys.py",
            task_names=["AGEDYSDiario"],
            frequency_days=int(os.getenv('AGEDYS_FRECUENCIA_DIAS', '1') or 1)
        )
        try:
            conn_str = self.config.get_db_agedys_connection_string()
            pool = get_agedys_connection_pool(conn_str)
            self.db_agedys = AccessDatabase(conn_str, pool=pool)
            self.logger.debug("Pool AGEDYS inicializado")
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error inicializando pool AGEDYS: {e}")
            self.db_agedys = None

    def execute_specific_logic(self) -> bool:
        """Orquesta la generación y registro de múltiples informes AGEDYS.

        Flujo:
          1. Informes técnicos individuales (por cada usuario con tareas)
          2. Informe grupal de Calidad
          3. Informe grupal de Economía
        Usa servicios centralizados: EmailRecipientsService y register_standard_report.
        """
        self.logger.info(
            "Inicio lógica específica AGEDYS (multi-informes)",
            extra={'event': 'agedys_task_logic_start', 'app': 'AGEDYS'}
        )
        if not self.db_agedys:
            self.logger.warning("Sin conexión BD AGEDYS; se omite ejecución")
            return True
        try:
            manager = AgedysManager(self.db_agedys, logger=self.logger)
            recipients_service = EmailRecipientsService(self.db_tareas, self.config, self.logger)

            total_registered = 0

            # ---- Sub-funciones internas ---------------------------------
            def _handle_technical_reports():
                count = 0
                usuarios = manager.get_usuarios_con_tareas_pendientes() or []
                self.logger.info(
                    "Usuarios con tareas pendientes recuperados",
                    extra={'event': 'agedys_users_pending_fetch', 'users': len(usuarios)}
                )
                for u in usuarios:
                    user_id = u.get('UserId') or u.get('user_id')
                    user_name = u.get('UserName') or u.get('user_name') or u.get('Nombre') or ''
                    user_email = u.get('UserEmail') or u.get('user_email') or u.get('CorreoUsuario') or ''
                    if user_id is None or not user_email:
                        self.logger.debug(
                            "Usuario omitido (datos incompletos)",
                            extra={'event': 'agedys_user_skipped', 'reason': 'missing_id_or_email', 'user_id': user_id, 'user_email': user_email}
                        )
                        continue
                    try:
                        html = manager.generate_technical_user_report_html(user_id, user_name, user_email)
                    except Exception as ex:  # pragma: no cover
                        self.logger.error(
                            f"Error generando informe técnico usuario {user_id}",
                            extra={'event': 'agedys_user_report_error', 'user_id': user_id, 'error': str(ex)}
                        )
                        continue
                    if not html:
                        self.logger.debug(
                            "Informe técnico vacío para usuario",
                            extra={'event': 'agedys_user_report_empty', 'user_id': user_id}
                        )
                        continue
                    subject = f"Informe Tareas Pendientes (AGEDYS) - {user_name}".strip()
                    try:
                        if register_standard_report(
                            self.db_tareas,
                            application="AGEDYS",
                            subject=subject,
                            body_html=html,
                            recipients=user_email,
                            admin_emails="",
                            logger=self.logger
                        ):
                            count += 1
                    except Exception as ex:  # pragma: no cover
                        self.logger.error(
                            f"Error registrando informe técnico usuario {user_id}",
                            extra={'event': 'agedys_user_report_register_error', 'user_id': user_id, 'error': str(ex)}
                        )
                self.logger.info(
                    "Informes técnicos procesados",
                    extra={'event': 'agedys_technical_reports_done', 'registered': count}
                )
                return count

            def _handle_quality_report():
                html = manager.generate_quality_report_html()
                if not html:
                    self.logger.info("Sin contenido informe Calidad")
                    return 0
                # Obtener destinatarios de calidad usando el ID numérico de la aplicación.
                # Antes se pasaba la cadena "AGEDYS" provocando mismatch de tipos (texto vs entero) en Access.
                app_id_num = self.config.app_id_agedys  # entero (ej. 3)
                self.logger.info(
                    "DEBUG_MARKER_PRE_QUALITY_RECIPIENTS",
                    extra={'event': 'agedys_quality_debug_marker', 'app_id': app_id_num}
                )
                quality_emails = recipients_service.get_quality_emails(app_id=app_id_num)
                if not quality_emails:
                    # Log detallado para diagnósticos posteriores si vuelve a fallar
                    self.logger.warning(
                        "Sin usuarios de calidad recuperados",
                        extra={
                            'event': 'agedys_quality_recipients_empty',
                            'passed_app_id': app_id_num,
                            'app_id_type': type(app_id_num).__name__
                        }
                    )
                recipients = ';'.join(quality_emails) if quality_emails else ''
                if not recipients:
                    self.logger.warning("Sin destinatarios calidad; se omite envío")
                    return 0
                if register_standard_report(
                    self.db_tareas,
                    application="AGEDYS",
                    subject="Informe AGEDYS - Calidad",
                    body_html=html,
                    recipients=recipients,
                    admin_emails="",
                    logger=self.logger
                ):
                    return 1
                return 0

            def _handle_economy_report():
                html = manager.generate_economy_report_html()
                if not html:
                    self.logger.info("Sin contenido informe Economía")
                    return 0
                economy_emails = recipients_service.get_economy_emails()
                if not economy_emails:
                    # fallback admin
                    self.logger.warning("Sin emails economía; usando admin como fallback")
                    economy_emails = recipients_service.get_admin_emails()
                recipients = ';'.join(economy_emails) if economy_emails else ''
                if not recipients:
                    self.logger.warning("Sin destinatarios economía tras fallback; se omite envío")
                    return 0
                if register_standard_report(
                    self.db_tareas,
                    application="AGEDYS",
                    subject="Informe AGEDYS - Economía",
                    body_html=html,
                    recipients=recipients,
                    admin_emails="",
                    logger=self.logger
                ):
                    return 1
                return 0

            # ---- Ejecución ordenada ------------------------------------
            total_registered += _handle_technical_reports()
            total_registered += _handle_quality_report()
            total_registered += _handle_economy_report()

            self.logger.info(
                "Fin lógica específica AGEDYS",
                extra={'event': 'agedys_task_logic_end', 'success': True, 'registered_reports': total_registered, 'app': 'AGEDYS'}
            )
            return True
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error en execute_specific_logic AGEDYS: {e}", extra={'context': 'execute_specific_logic_agedys'})
            return False

    def close_connections(self):
        try:
            if getattr(self, 'db_agedys', None):
                try:
                    self.db_agedys.disconnect()
                except Exception as e:  # pragma: no cover
                    self.logger.warning(f"Error cerrando BD AGEDYS: {e}")
                finally:
                    self.db_agedys = None
        finally:
            super().close_connections()