"""
Script Python equivalente a EnviarCorreoNoEnviado.vbs
Funciona con SQLite en Docker y sincroniza con Access cuando está disponible
"""
import smtplib
import logging
import time
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Any, Dict, List

# Añadir path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from common.config import reload_config, config

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, config):
        self.config = config
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.smtp_user = config.smtp_user
        self.smtp_password = getattr(config, 'smtp_password', None)
        self.smtp_tls = getattr(config, 'smtp_tls', False)

    def _enviar_correo_individual(self, correo: Dict[str, Any]) -> bool:
        """
        Envía un correo individual usando los datos del registro.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = correo['Destinatarios']
            if correo.get('DestinatariosConCopia'):
                msg['Cc'] = correo['DestinatariosConCopia']
            if correo.get('DestinatariosConCopiaOculta'):
                msg['Bcc'] = correo['DestinatariosConCopiaOculta']
            msg['Subject'] = correo['Asunto']
            msg.attach(MIMEText(correo['Cuerpo'], 'html'))
            # Adjuntar archivo si existe
            if correo.get('URLAdjunto'):
                archivo_path = Path(correo['URLAdjunto'])
                if archivo_path.exists():
                    self._adjuntar_archivo(msg, archivo_path)
            # Configurar SMTP
            # self.smtp_server = config.smtp_server # This line is removed as per the new_code
            # self.smtp_port = config.smtp_port # This line is removed as per the new_code
            # self.smtp_user = config.smtp_user # This line is removed as per the new_code
            # self.smtp_password = config.smtp_password # This line is removed as per the new_code
            # self.smtp_tls = getattr(config, 'smtp_tls', False) # This line is removed as per the new_code
            # Destinatarios
            destinatarios = [correo['Destinatarios']]
            if correo.get('DestinatariosConCopia'):
                destinatarios += [correo['DestinatariosConCopia']]
            if correo.get('DestinatariosConCopiaOculta'):
                destinatarios += [correo['DestinatariosConCopiaOculta']]
            # Enviar
            return self._enviar_smtp(msg, destinatarios)
        except Exception as e:
            logger.error(f"Error en _enviar_correo_individual: {e}")
            return False
    """Clase para envío de correos equivalente al script VBS"""
    
    def enviar_correos_no_enviados(self) -> int:
        """
        Función principal equivalente a EnviarCorreosNoEnviados del VBS
        Retorna número de correos enviados
        """
        correos_enviados = 0
        try:
            print(f"[INFO] Ruta de base de datos usada: {self._get_db_path()}")
            logger.info(f"Ruta de base de datos usada: {self._get_db_path()}")
            conn = sqlite3.connect(self._get_db_path())
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM TbCorreosEnviados WHERE FechaEnvio IS NULL")
            rows = cursor.fetchall()
            correos_pendientes = [dict(row) for row in rows]
            if not correos_pendientes:
                print("[INFO] No hay correos pendientes de envío")
                logger.info("No hay correos pendientes de envío")
                return 0
            print(f"[INFO] Encontrados {len(correos_pendientes)} correos pendientes")
            for correo in correos_pendientes:
                print(f"[INFO] Procesando correo ID {correo['IDCorreo']} - Asunto: {correo['Asunto']}")
                try:
                    if self._enviar_correo_individual(correo):
                        self._marcar_correo_enviado(conn, correo['IDCorreo'], datetime.now())
                        correos_enviados += 1
                        print(f"[OK] Correo enviado: ID {correo['IDCorreo']} - {correo['Asunto']}")
                        logger.info(f"[OK] Correo enviado: ID {correo['IDCorreo']} - {correo['Asunto']}")
                    else:
                        print(f"[ERROR] Error enviando correo ID {correo['IDCorreo']}")
                        logger.error(f"[ERROR] Error enviando correo ID {correo['IDCorreo']}")
                except Exception as e:
                    print(f"[ERROR] Error procesando correo {correo.get('IDCorreo', 'N/A')}: {e}")
            return correos_enviados
        except Exception as e:
            logger.error(f"Error en enviar_correos_no_enviados: {e}")
            return 0

    def _get_db_path(self):
        # Usar siempre la base de datos SQLite para las consultas y envío
        return str(self.config.sqlite_dir / 'correos_datos.sqlite')
    
    def _adjuntar_archivo(self, msg: MIMEMultipart, archivo_path: Path):
        try:
            with open(archivo_path, 'rb') as archivo:
                adjunto = MIMEApplication(archivo.read(), Name=archivo_path.name)
                adjunto['Content-Disposition'] = f'attachment; filename="{archivo_path.name}"'
                msg.attach(adjunto)
        except Exception as e:
            logger.error(f"Error adjuntando archivo {archivo_path}: {e}")
    
    def _enviar_smtp(self, msg: MIMEMultipart, destinatarios: List[str]) -> bool:
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as servidor:
                if getattr(self, 'smtp_tls', False):
                    servidor.starttls()
                if getattr(self, 'smtp_user', None) and getattr(self, 'smtp_password', None):
                    servidor.login(self.smtp_user, self.smtp_password)
                servidor.sendmail(self.smtp_user, destinatarios, msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Error enviando correo por SMTP: {e}")
            return False


def main():
    print("[INFO] Iniciando envío de correos no enviados...")
    reload_config()
    print(f"[DEBUG] ENVIRONMENT: {config.environment}")
    print(f"[DEBUG] Ruta correos: {config.db_correos_path}")
    from common.database_sync import sync_database_from_access, sync_database_to_access
    access_path = config.db_correos_path
    sqlite_path = config.sqlite_dir / 'correos_datos.sqlite'
    print(f"[INFO] Sincronizando Access → SQLite: {access_path} → {sqlite_path}")
    try:
        sync_database_from_access(access_path, sqlite_path, tables=['TbCorreosEnviados'])
    except Exception as e:
        print(f"[WARN] Error con contraseña: {e}. Probando sin contraseña...")
        from common.config import config as config_mod
        config_mod.db_password = ''
        from common.database_sync import sync_database_from_access as sync_no_pwd
        sync_no_pwd(access_path, sqlite_path, tables=['TbCorreosEnviados'])
    sender = EmailSender(config)
    enviados = sender.enviar_correos_no_enviados()
    print(f"[INFO] Total de correos enviados: {enviados}")
    print(f"[INFO] Sincronizando SQLite → Access: {sqlite_path} → {access_path}")
    sync_database_to_access(sqlite_path, access_path, tables=['TbCorreosEnviados'])

if __name__ == "__main__":
    main()
