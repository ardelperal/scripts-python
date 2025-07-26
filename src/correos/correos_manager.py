"""
Gestor de Correos
Adaptación del script legacy EnviarCorreoNoEnviado.vbs
"""
import smtplib
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Any, Dict, List

from ..common import config
from ..common.database import AccessDatabase

logger = logging.getLogger(__name__)


class CorreosManager:
    """Gestor para el módulo de correos"""
    
    def __init__(self):
        """Inicializar el gestor de correos"""
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
    
    def enviar_correos_no_enviados(self) -> int:
        """
        Función principal equivalente a EnviarCorreosNoEnviados del VBS
        Retorna número de correos enviados
        """
        correos_enviados = 0
        try:
            db_path = self._get_db_path()
            logger.info(f"Ruta de base de datos usada: {db_path}")
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM TbCorreosEnviados WHERE FechaEnvio IS NULL")
            rows = cursor.fetchall()
            correos_pendientes = [dict(row) for row in rows]
            
            if not correos_pendientes:
                logger.info("No hay correos pendientes de envío")
                return 0
            
            logger.info(f"Encontrados {len(correos_pendientes)} correos pendientes")
            
            for correo in correos_pendientes:
                logger.info(f"Procesando correo ID {correo['IDCorreo']} - Asunto: {correo['Asunto']}")
                try:
                    if self._enviar_correo_individual(correo):
                        self._marcar_correo_enviado(conn, correo['IDCorreo'], datetime.now())
                        correos_enviados += 1
                        logger.info(f"Correo enviado: ID {correo['IDCorreo']} - {correo['Asunto']}")
                    else:
                        logger.error(f"Error enviando correo ID {correo['IDCorreo']}")
                except Exception as e:
                    logger.error(f"Error procesando correo {correo.get('IDCorreo', 'N/A')}: {e}")
            
            conn.close()
            return correos_enviados
            
        except Exception as e:
            logger.error(f"Error en enviar_correos_no_enviados: {e}")
            return 0

    def _get_db_path(self):
        """Obtener la ruta de la base de datos SQLite"""
        return str(self.config.sqlite_dir / 'correos_datos.sqlite')
    
    def _adjuntar_archivo(self, msg: MIMEMultipart, archivo_path: Path):
        """Adjuntar archivo al mensaje de correo"""
        try:
            with open(archivo_path, 'rb') as archivo:
                adjunto = MIMEApplication(archivo.read(), Name=archivo_path.name)
                adjunto['Content-Disposition'] = f'attachment; filename="{archivo_path.name}"'
                msg.attach(adjunto)
        except Exception as e:
            logger.error(f"Error adjuntando archivo {archivo_path}: {e}")
    
    def _enviar_smtp(self, msg: MIMEMultipart, destinatarios: List[str]) -> bool:
        """Enviar correo por SMTP"""
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

    def _marcar_correo_enviado(self, conn: sqlite3.Connection, id_correo: int, fecha_envio: datetime):
        """Marcar correo como enviado en la base de datos"""
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE TbCorreosEnviados SET FechaEnvio = ? WHERE IDCorreo = ?",
                (fecha_envio.strftime('%Y-%m-%d %H:%M:%S'), id_correo)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error marcando correo como enviado: {e}")

    def sync_databases(self):
        """Sincronizar bases de datos Access y SQLite (placeholder)"""
        try:
            logger.info("Sincronización de bases de datos no disponible en modo Access-only")
            # En modo Access-only, no hay sincronización
            return True
                
        except Exception as e:
            logger.error(f"Error sincronizando bases de datos: {e}")
            return False

    def sync_back_to_access(self):
        """Sincronizar cambios de vuelta a Access (placeholder)"""
        try:
            logger.info("Sincronización de vuelta a Access no necesaria en modo Access-only")
            # En modo Access-only, no hay sincronización
            return True
            
        except Exception as e:
            logger.error(f"Error sincronizando de vuelta a Access: {e}")
            return False

    def execute_daily_task(self) -> bool:
        """
        Ejecutar la tarea diaria de envío de correos
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            logger.info("Iniciando tarea diaria de envío de correos")
            
            # Sincronizar desde Access
            self.sync_databases()
            
            # Enviar correos pendientes
            enviados = self.enviar_correos_no_enviados()
            
            # Sincronizar de vuelta a Access
            if enviados > 0:
                self.sync_back_to_access()
            
            logger.info(f"Tarea diaria completada. Total de correos enviados: {enviados}")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando tarea diaria de correos: {e}")
            return False