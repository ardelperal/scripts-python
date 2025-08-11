"""Registro de reportes AGEDYS (patrón similar a no_conformidades/report_registrar.py)

Responsabilidad: encapsular la inserción en TbCorreosEnviados para informes AGEDYS.
"""
from __future__ import annotations

import logging
from datetime import datetime

from common.config import Config
from common.database import AccessDatabase

config = Config()
logger = logging.getLogger(__name__)


def register_agedys_report(
    subject: str, body_html: str, recipients: str, admin_emails: str = ""
) -> int | None:
    """Inserta un correo de informe AGEDYS en TbCorreosEnviados.

    Args:
        subject: Asunto del correo
        body_html: Cuerpo HTML (ya completo)
        recipients: Destinatarios principales (string separado por ';')
        admin_emails: CC administradores (opcional)
    Returns:
        IDCorreo insertado o None si error.
    """
    try:  # pragma: no cover - acceso real
        connection_string = config.get_db_tareas_connection_string()
        db = AccessDatabase(connection_string)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            next_id = db.get_max_id("TbCorreosEnviados", "IDCorreo") + 1
            now = datetime.now()
            insert = (
                "INSERT INTO TbCorreosEnviados (IDCorreo, Aplicacion, Asunto, Cuerpo, "
                "Destinatarios, DestinatariosConCopia, DestinatariosConCopiaOculta, "
                "FechaGrabacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            )
            cursor.execute(
                insert,
                [
                    next_id,
                    "AGEDYS",
                    subject,
                    body_html.strip(),
                    recipients,
                    admin_emails,
                    "",  # BCC
                    now,
                ],
            )
            conn.commit()
            logger.info(
                "Correo AGEDYS registrado",
                extra={
                    "event": "agedys_report_registered",
                    "metric_name": "agedys_report_registered",
                    "metric_value": 1,
                    "id_correo": next_id,
                },
            )
            return next_id
    except Exception as e:  # pragma: no cover
        logger.error(f"Error registrando correo AGEDYS: {e}")
        return None
