"""Email unified service module.

EmailManager unifica la lógica de envío de correos de los módulos
'correos' y 'correo_tareas' usando pools de conexión thread-safe.
"""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from typing import List, Dict, Any

from common.config import config
from common.access_connection_pool import (
    get_correos_connection_pool,
    get_tareas_connection_pool,
)

logger = logging.getLogger(__name__)


class TransientEmailSendError(Exception):
    """Error transitorio (p.ej. fallo de conexión SMTP) que NO debe marcar el correo como no enviado aún."""
    pass


class EmailManager:
    """Gestor unificado para envío de correos pendientes.

    Parametros:
        email_source: 'correos' o 'tareas'. Determina la BD origen.
    """

    def __init__(self, email_source: str):
        source = email_source.lower().strip()
        if source not in {"correos", "tareas"}:
            raise ValueError("email_source debe ser 'correos' o 'tareas'")
        self.email_source = source

        # Config SMTP
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.smtp_user = config.smtp_user
        self.smtp_password = getattr(config, 'smtp_password', None)
        self.smtp_tls = getattr(config, 'smtp_tls', False)

        # Pool conexión adecuado
        if self.email_source == 'correos':
            conn_str = config.get_db_correos_connection_string()
            self.db_pool = get_correos_connection_pool(conn_str)
        else:  # tareas
            conn_str = config.get_db_connection_string('tareas')
            self.db_pool = get_tareas_connection_pool(conn_str)

    # ---------------------- API pública ----------------------
    def process_pending_emails(self) -> int:
        """Procesa correos pendientes (FechaEnvio IS NULL) enviándolos y marcándolos.

        Retorna el número de correos enviados.
        """
        enviados = 0
        try:
            query = "SELECT * FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
            rows = self.db_pool.execute_query(query)
            if not rows:
                logger.info("No hay correos pendientes (%s)", self.email_source)
                return 0
            logger.info("%s correos pendientes (%s)", len(rows), self.email_source)
            for correo in rows:
                try:
                    resultado = self._enviar_correo_individual(correo)
                    if resultado is True:
                        self._marcar_correo_enviado(correo['IDCorreo'], datetime.now())
                        enviados += 1
                    elif resultado is False:
                        # Fallo definitivo en construcción o envío (no transitorio)
                        self._marcar_correo_no_enviado(correo['IDCorreo'], 'Error envío')
                except TransientEmailSendError as e:  # fallo transitorio -> reintentar en ciclo futuro
                    logger.warning(
                        "Fallo transitorio SMTP para correo ID %s: %s (se reintentará sin marcar)",
                        correo.get('IDCorreo'), e
                    )
                except Exception as e:  # pragma: no cover - path de error inesperado
                    logger.error("Error procesando correo ID %s: %s", correo.get('IDCorreo'), e)
                    self._marcar_correo_no_enviado(correo.get('IDCorreo', -1), str(e))
            return enviados
        except Exception as e:
            logger.error("Error general en process_pending_emails (%s): %s", self.email_source, e)
            return enviados

    # ------------------ Lógica interna ------------------
    def _enviar_correo_individual(self, correo: Dict[str, Any]) -> bool:
        """Devuelve True si enviado, False si fallo definitivo, o levanta TransientEmailSendError."""
        try:
            msg = MIMEMultipart()
            aplicacion = correo.get('Aplicacion', 'Sistema')
            msg['From'] = f"{aplicacion}.DySN@telefonica.com"
            msg['To'] = correo.get('Destinatarios', '')
            if correo.get('DestinatariosConCopia'):
                msg['Cc'] = correo['DestinatariosConCopia']
            if correo.get('DestinatariosConCopiaOculta'):
                msg['Bcc'] = correo['DestinatariosConCopiaOculta']
            msg['Subject'] = correo.get('Asunto', '(Sin asunto)')

            cuerpo = correo.get('Cuerpo', 'Mensaje vacío')
            if '<html>' in cuerpo.lower() or '<body>' in cuerpo.lower():
                msg.attach(MIMEText(cuerpo, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

            if correo.get('URLAdjunto'):
                self._agregar_adjuntos(msg, correo['URLAdjunto'])

            destinatarios = self._build_recipient_list(correo)
            if not destinatarios:
                logger.warning("Correo ID %s sin destinatarios", correo.get('IDCorreo'))
                return False
            return self._enviar_smtp(msg, destinatarios)
        except TransientEmailSendError:
            raise
        except Exception as e:
            logger.error("Error en _enviar_correo_individual: %s", e)
            return False

    def _build_recipient_list(self, correo: Dict[str, Any]) -> List[str]:
        lst: List[str] = []
        for key in ('Destinatarios', 'DestinatariosConCopia', 'DestinatariosConCopiaOculta'):
            val = correo.get(key)
            if val:
                # Permitir múltiples separados por ';'
                parts = [p.strip() for p in val.split(';') if p.strip()]
                lst.extend(parts)
        # Eliminar duplicados preservando orden
        seen = set()
        result = []
        for d in lst:
            if d not in seen:
                seen.add(d)
                result.append(d)
        return result

    def _agregar_adjuntos(self, msg: MIMEMultipart, url_adjuntos: str):
        try:
            if ';' in url_adjuntos:
                items = [p.strip() for p in url_adjuntos.split(';') if p.strip()]
            else:
                items = [url_adjuntos.strip()]
            for p in items:
                if not p:
                    continue
                path = Path(p)
                if not path.exists():
                    logger.warning("Adjunto no encontrado: %s", p)
                    continue
                with open(path, 'rb') as fh:
                    # Usar MIMEBase genérico para máxima compatibilidad
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(fh.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{path.name}"')
                    msg.attach(part)
        except Exception as e:  # pragma: no cover
            logger.error("Error agregando adjuntos: %s", e)

    def _enviar_smtp(self, msg: MIMEMultipart, destinatarios: List[str]) -> bool:
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as servidor:
                if self.smtp_tls:
                    servidor.starttls()
                if self.smtp_user and self.smtp_password:
                    servidor.login(self.smtp_user, self.smtp_password)
                servidor.sendmail(self.smtp_user, destinatarios, msg.as_string())
            return True
        except (ConnectionRefusedError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            logger.error("Fallo conexión SMTP: %s", e)
            raise TransientEmailSendError(str(e))
        except Exception as e:
            logger.error("Error enviando correo SMTP: %s", e)
            return False

    def _marcar_correo_enviado(self, id_correo: int, fecha_envio: datetime):
        try:
            update_data = {"FechaEnvio": fecha_envio}
            where_clause = f"IDCorreo = {id_correo}"
            self.db_pool.update_record("TbCorreosEnviados", update_data, where_clause)
        except Exception as e:  # pragma: no cover
            logger.error("Error marcando correo enviado: %s", e)

    def _marcar_correo_no_enviado(self, id_correo: int, motivo: str):
        try:
            update_data = {"Notas": f"Fallo envío: {motivo}", "Enviado": False}
            where_clause = f"IDCorreo = {id_correo}"
            self.db_pool.update_record("TbCorreosEnviados", update_data, where_clause)
        except Exception as e:  # pragma: no cover
            logger.error("Error marcando correo no enviado: %s", e)
