"""Servicio centralizado para obtención de destinatarios de correo.

Envuelve las funciones existentes en ``src.common.utils`` para permitir
futura evolución (cache, filtros, métricas) con impacto mínimo en módulos.
"""
from __future__ import annotations

from .. import utils as _utils


class EmailRecipientsService:
    """Encapsula la lógica de obtención de emails por rol."""

    def __init__(self, db_connection, config, logger):
        self.db_connection = db_connection
        self.config = config
        self.logger = logger

    # --- Métodos por rol -------------------------------------------------
    def get_admin_emails(self) -> list[str]:
        emails_str = _utils.get_admin_emails_string(
            self.db_connection, self.config, self.logger
        )
        return self._split(emails_str)

    def get_admin_emails_string(self) -> str:  # conveniencia
        return _utils.get_admin_emails_string(
            self.db_connection, self.config, self.logger
        )

    def get_technical_emails(self) -> list[str]:
        emails_str = _utils.get_technical_emails_string(
            self.db_connection, self.config, self.logger
        )
        return self._split(emails_str)

    def get_quality_emails(self, app_id: str | None = None) -> list[str]:
        if app_id is None:
            return []
        emails_str = _utils.get_quality_emails_string(
            app_id, self.config, self.logger, self.db_connection
        )
        return self._split(emails_str)

    def get_economy_emails(self) -> list[str]:
        """Destinatarios de Economía.

        Usa utilidades existentes; si falla retorna lista vacía.
        """
        try:
            emails_str = _utils.get_economy_emails_string(self.config, self.logger)
            return self._split(emails_str)
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Error obteniendo emails economía: {e}")
            return []

    # --- Utilidades internas ---------------------------------------------
    @staticmethod
    def _split(emails_str: str) -> list[str]:
        if not emails_str:
            return []
        return [e.strip() for e in emails_str.replace(",", ";").split(";") if e.strip()]


__all__ = ["EmailRecipientsService"]
