"""Tarea continua de envío de correos pendientes integrada con framework de tareas.

Refactor: adopta el patrón execute_specific_logic utilizado por execute_task_with_standard_boilerplate
para unificar el flujo (banners, planificación, etc.). Al ser TareaContinua no se marca
como completada en BD.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from common.base_task import TareaContinua  # type: ignore
from common.config import config  # type: ignore
from .correos_manager import CorreosManager  # type: ignore

logger = logging.getLogger(__name__)


class CorreosTask(TareaContinua):
    """Tarea continua que envía todos los correos pendientes."""

    def __init__(self, manager_cls=CorreosManager):
        super().__init__(
            name="Correos",
            script_filename="run_correos.py",
        )
        self.manager_cls = manager_cls
        self.manager: Optional[CorreosManager] = None

    def initialize(self):  # pragma: no cover - simple
        try:
            logger.debug("Inicializando CorreosTask")
            self.manager = self.manager_cls()
            return True
        except Exception as e:  # pragma: no cover
            logger.error(f"Error inicializando CorreosTask: {e}")
            return False

    def execute_specific_logic(self) -> bool:
        try:
            if not Path(config.db_correos_path).exists():
                logger.error(f"BD de correos inexistente: {config.db_correos_path}")
                return False
            if not self.manager:
                self.manager = self.manager_cls()
            enviados = self.manager.process_pending_emails()
            logger.info(f"Correos enviados: {enviados}")
            return True
        except Exception as e:
            logger.error(f"Error en execute_specific_logic CorreosTask: {e}")
            return False

    def execute(self) -> bool:  # pragma: no cover - alias retrocompatibilidad
        return self.execute_specific_logic()

    def close_connections(self):  # pragma: no cover - defensivo
        try:
            if self.manager and getattr(self.manager, 'db_conn', None):
                try:
                    self.manager.db_conn.disconnect()
                except Exception:
                    pass
        finally:
            self.manager = None