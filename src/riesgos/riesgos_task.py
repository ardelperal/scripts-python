"""Tarea orquestadora para Gestión de Riesgos.

Responsabilidad: decidir qué subtareas (técnica, calidad semanal, calidad mensual)
se ejecutan y delegar la generación/envío en un `RiesgosManager` (que mantiene la
lógica de negocio y generación de informes).

Objetivo refactor incremental: mover la orquestación fuera de `RiesgosManager`
sin romper los tests existentes que todavía invocan métodos del manager
(`run_daily_tasks`, `should_execute_*`). Para mantener compatibilidad, esos
métodos permanecen en el manager pero ahora delegan (o podrán delegar) en esta
clase. Una vez actualizados los tests se podrán eliminar los wrappers legacy.
"""
from __future__ import annotations

from typing import Optional, Dict

from common.base_task import TareaDiaria


class RiesgosTask(TareaDiaria):
    """Task diaria para Riesgos.

    Nota: Usa un `RiesgosManager` externo (inyectado) para reutilizar conexiones
    y mantener compatibilidad de tests que acceden a atributos internos del
    manager. Si no se proporciona, la tarea creará y gestionará su propio
    manager temporal.
    """

    def __init__(self, manager: Optional["RiesgosManager"] = None):  # type: ignore[name-defined]
        # Mantener nomenclatura alineada con otras tasks; el script se crea como stub.
        super().__init__(
            name="Riesgos",
            script_filename="run_riesgos.py",
            task_names=[
                "RiesgosDiariosTecnicos",
                "RiesgosDiariosCalidad",
                "RiesgosMensualesCalidad",
            ],
            frequency_days=1,
        )
        self.manager = manager  # Puede ser None (se creará on-demand)

    # ---------------- Orquestación principal -----------------
    def execute_specific_logic(
        self,
        force_technical: bool = False,
        force_quality: bool = False,
        force_monthly: bool = False,
    ) -> bool:
        """Ejecuta la lógica específica de la tarea.

        Devuelve True si al menos una subtarea se ejecutó exitosamente.
        """
        results = self.run_tasks(force_technical, force_quality, force_monthly)
        # Marcar completadas sólo si al menos una subtarea se ejecutó
        if any(results.values()):
            self.marcar_como_completada()  # registra las tareas asociadas
        return any(results.values())

    # API interna usada por el wrapper de RiesgosManager
    def run_tasks(
        self,
        force_technical: bool = False,
        force_quality: bool = False,
        force_monthly: bool = False,
    ) -> Dict[str, bool]:
        """Ejecuta las subtareas de Riesgos y devuelve dict de resultados.

        Se intenta reutilizar un manager inyectado; si no se proporciona se
        crea uno temporal y se cierran sus conexiones al final.
        """
        created_manager = False
        if self.manager is None:
            from .riesgos_manager import RiesgosManager  # import diferido

            self.manager = RiesgosManager(self.config, self.logger)
            try:
                self.manager.connect_to_database()
            except Exception:  # pragma: no cover
                self.logger.warning("No se pudo conectar a BD de riesgos")
            created_manager = True

        mgr = self.manager
        results = {"technical": False, "quality": False, "monthly": False}

        try:
            # Decisiones (se reutiliza la lógica existente del manager para compatibilidad)
            should_run_technical = force_technical or mgr.should_execute_technical_task()
            should_run_quality = force_quality or mgr.should_execute_quality_task()
            should_run_monthly = force_monthly or mgr.should_execute_monthly_quality_task()

            if not (should_run_technical or should_run_quality or should_run_monthly):
                self.logger.info("RiesgosTask: no hay subtareas para ejecutar hoy")
                return results

            if should_run_technical:
                results["technical"] = bool(mgr.execute_technical_task())
            if should_run_quality:
                results["quality"] = bool(mgr.execute_quality_task())
            if should_run_monthly:
                results["monthly"] = bool(mgr.execute_monthly_quality_task())

            executed = [k for k, v in results.items() if v]
            if executed:
                self.logger.info(
                    f"RiesgosTask: subtareas ejecutadas: {', '.join(executed)}"
                )
            return results
        finally:
            if created_manager:
                try:
                    mgr.disconnect_from_database()
                except Exception:  # pragma: no cover
                    pass


__all__ = ["RiesgosTask"]
