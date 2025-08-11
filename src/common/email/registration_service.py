"""Servicio de registro estándar de correos/reportes en BD.

Proporciona una función envoltorio sobre ``register_email_in_database`` que
añade manejo de errores consistente y métrica (via logger.extra).
"""
from __future__ import annotations

from .. import utils as _utils


def register_standard_report(
    db_connection,
    *,
    application: str,
    subject: str,
    body_html: str,
    recipients: str,
    admin_emails: str = "",
    logger=None,
) -> bool:
    """Registra un informe HTML como correo pendiente de envío."""
    try:
        success = _utils.register_email_in_database(
            db_connection,
            application=application,
            subject=subject,
            body=body_html,
            recipients=recipients,
            admin_emails=admin_emails,
        )
        if logger:
            if success:
                logger.info(
                    f"Correo registrado ({application})",
                    extra={
                        "metric_name": f"{application.lower()}_email_registered",
                        "metric_value": 1,
                    },
                )
            else:
                logger.error(f"Fallo registrando correo ({application})")
        return success
    except Exception as e:  # pragma: no cover
        if logger:
            logger.error(f"Excepción registrando correo estándar {application}: {e}")
        return False


__all__ = ["register_standard_report"]
