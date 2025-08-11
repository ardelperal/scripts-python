"""Tarea orquestadora refactorizada para No Conformidades.

Responsabilidad exclusiva: decidir ejecución (planificación) y delegar la
generación/parcial de informe a un manager puro (incremental) y registrar correo.

Refactor incremental: de momento sólo se genera informe parcial (secciones migradas)
si existen datos; el resto continúa en el manager legacy hasta completar migración.
"""
from __future__ import annotations

import os

from common.db.access_connection_pool import get_nc_connection_pool
from common.base_task import TareaDiaria
from common.db.database import AccessDatabase
from common.email.registration_service import register_standard_report
from common.user_adapter import get_quality_emails_string, get_user_email
from common.base_task import register_task_completion
from email_services.email_manager import EmailManager

from .no_conformidades_manager import NoConformidadesManager


class NoConformidadesTask(TareaDiaria):
    def __init__(self):
        super().__init__(
            name="NoConformidades",
            script_filename="run_no_conformidades.py",
            task_names=["NCTecnico", "NCCalidad"],
            frequency_days=int(os.getenv("NC_FRECUENCIA_DIAS", "1") or 1),
        )
        try:
            conn_str = self.config.get_db_no_conformidades_connection_string()
            pool = get_nc_connection_pool(conn_str)
            self.db_nc = AccessDatabase(conn_str, pool=pool)
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error inicializando pool NC: {e}")
            self.db_nc = None

    def execute_specific_logic(self) -> bool:
        """Orquesta la ejecución delegando en NoConformidadesManager limpio."""
        self.logger.info("Inicio lógica específica NC", extra={"event": "nc_task_logic_start", "app": "NC"})
        if not self.db_nc:
            self.logger.warning("Sin conexión a BD NC: se omiten subtareas.")
            return False
        overall_ok = True
        try:
            manager = NoConformidadesManager()
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error inicializando manager NC: {e}")
            return False
        manager.db_nc = self.db_nc
        try:
            # Calidad
            if self.debe_ejecutar_tarea_calidad():
                try:
                    manager._generar_correo_calidad()
                except Exception as e:  # pragma: no cover
                    self.logger.error(f"Fallo generando correo calidad: {e}")
                    overall_ok = False
            # Técnica
            if self.debe_ejecutar_tarea_tecnica():
                try:
                    manager._generar_correos_tecnicos()
                except Exception as e:  # pragma: no cover
                    self.logger.error(f"Fallo generando correos técnicos: {e}")
                    overall_ok = False
        finally:
            manager.close_connections()
        self.logger.info("Fin lógica específica NC", extra={"event": "nc_task_logic_end", "success": overall_ok, "app": "NC"})
        return overall_ok

    # ---------------- Métodos de decisión ----------------
    def debe_ejecutar_tarea_calidad(self) -> bool:
        """Determina si la subtarea de calidad debe ejecutarse.

        Implementación mínima: se basa en presencia de datos relevantes.
        Puede evolucionar a comprobaciones de frecuencia específicas.
        """
        try:
            manager = NoConformidadesManager()
            manager.db_nc = self.db_nc
            datasets = [
                manager.get_ars_proximas_vencer_calidad(),
                manager.get_ncs_pendientes_eficacia(),
                manager.get_ncs_sin_acciones(),
                manager.get_ars_para_replanificar(),
            ]
            manager.close_connections()
            return any(datasets)
        except Exception:  # pragma: no cover
            # Señalizar error para que execute_specific_logic lo considere fallo
            self._calidad_error = True
            return False

    def debe_ejecutar_tarea_tecnica(self) -> bool:
        """Determina si la subtarea técnica debe ejecutarse (placeholder)."""
        try:
            tecnicos = self._get_tecnicos_con_nc_activas()
            return bool(tecnicos)
        except Exception:  # pragma: no cover
            self._tecnica_error = True
            return False

    # ---------------- Lógica de subtareas ----------------
    def ejecutar_logica_calidad(self) -> bool:
        try:
            manager = NoConformidadesManager()
            manager.db_nc = self.db_nc
            partial_html = manager.generate_nc_report_html()
            if not partial_html:
                self.logger.info("Calidad: informe vacío; se omite correo")
                manager.close_connections()
                return True
            destinatarios = (
                get_quality_emails_string(
                    app_id="8",
                    config=self.config,
                    logger=self.logger,
                    db_connection=self.db_tareas,
                )
                or ""
            )
            if not destinatarios:
                self.logger.warning("Calidad: sin destinatarios configurados")
                manager.close_connections()
                return True
            ok = register_standard_report(
                self.db_tareas,
                application="NoConformidades",
                subject="Informe Tareas No Conformidades (No Conformidades)",
                body_html=partial_html,
                recipients=destinatarios,
                admin_emails="",
                logger=self.logger,
            )
            manager.close_connections()
            if ok:
                register_task_completion(self.db_tareas, "NoConformidadesCalidad")
            return bool(ok)
        except Exception as e:  # pragma: no cover
            self.logger.exception(f"Error en ejecutar_logica_calidad: {e}")
            return False

    def ejecutar_logica_tecnica(self) -> bool:
        try:
            from .no_conformidades_manager import (
                NoConformidadesManager,  # import local para evitar ciclos en carga
            )

            manager_full = NoConformidadesManager()
            manager_full.db_nc = self.db_nc
            tecnicos = (
                manager_full._get_tecnicos_con_nc_activas()
            )  # usar lógica consolidada existente
            if not tecnicos:
                self.logger.info("Técnica: sin técnicos con NC activas")
                manager_full.close_connections()
                return True
            exitosos = 0
            total = 0
            for tecnico in tecnicos:
                data = manager_full.get_technical_report_data_for_user(tecnico)
                if not any(data.values()):
                    continue
                total += 1
                correo_tecnico = get_user_email(tecnico, self.config, self.logger)
                if not correo_tecnico:
                    continue
                cuerpo = self._render_html_tecnico(data)
                em = EmailManager("tareas")
                ok = em.register_email(
                    application="NoConformidades",
                    subject="Tareas de Acciones Correctivas a punto de caducar o caducadas (No Conformidades)",
                    body=cuerpo,
                    recipients=correo_tecnico,
                    admin_emails=self._collect_responsables_calidad(manager_full, data),
                )
                if ok:
                    exitosos += 1
            if total:
                self.logger.info(f"Técnica: notificaciones {exitosos}/{total}")
                register_task_completion(self.db_tareas, "NoConformidadesTecnica")
            manager_full.close_connections()
            return True
        except Exception as e:  # pragma: no cover
            self.logger.exception(f"Error en ejecutar_logica_tecnica: {e}")
            return False

    # -------- Helpers técnicos (simplificados) --------
    def _get_tecnicos_con_nc_activas(
        self,
    ):  # pragma: no cover - dependerá de consultas futuras
        try:
            query = (
                "SELECT DISTINCT Responsable FROM TbNCAccionesRealizadas "
                "WHERE FechaFinReal IS NULL AND Responsable IS NOT NULL"
            )
            rows = self.db_nc.execute_query(query) if self.db_nc else []
            return [r["Responsable"] for r in rows if r.get("Responsable")]
        except Exception as e:
            self.logger.error(f"Error listando técnicos NC: {e}")
            return []

    def _build_datasets_tecnico(self, manager: NoConformidadesManager, tecnico: str):
        # Reutilizamos consultas existentes de manager donde aplica; placeholders para
        # detallado por técnico
        # En refactor posterior se crearán métodos específicos filtrados por técnico
        return {"ars_8_15": [], "ars_1_7": [], "ars_vencidas": []}

    def _collect_responsables_calidad(self, manager: NoConformidadesManager, datos: dict) -> str:
        return ""

    def _render_html_tecnico(self, datos: dict) -> str:
        # Placeholder simple; futuro: plantilla HTML dedicada
        return "<html><body><p>Resumen técnico NC (refactor en progreso).</p></body></html>"

    def close_connections(self):
        try:
            if getattr(self, "db_nc", None):
                try:
                    self.db_nc.disconnect()
                except Exception as e:  # pragma: no cover
                    self.logger.warning(f"Error cerrando BD NC: {e}")
                finally:
                    self.db_nc = None
        finally:
            super().close_connections()
