"""
Gestor de Correos
Adaptación del script legacy EnviarCorreoNoEnviado.vbs
"""
import smtplib
import logging
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
        
        # Conexión a base de datos Access
        self.db_conn = AccessDatabase(config.get_db_correos_connection_string())

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
            self.db_conn.connect()
            logger.info("Conectado a base de datos Access de correos")
            
            # Obtener correos pendientes
            query = "SELECT * FROM TbCorreosEnviados WHERE FechaEnvio IS NULL"
            correos_pendientes = self.db_conn.execute_query(query)
            
            if not correos_pendientes:
                logger.info("📭 No hay correos pendientes de envío")
                return 0
            
            logger.info(f"📬 Encontrados {len(correos_pendientes)} correos pendientes para envío")
            
            for correo in correos_pendientes:
                logger.info(f"📧 Procesando correo ID: {correo['IDCorreo']} | Asunto: '{correo['Asunto']}'")
                try:
                    if self._enviar_correo_individual(correo):
                        self._marcar_correo_enviado(correo['IDCorreo'], datetime.now())
                        correos_enviados += 1
                        logger.info(f"✅ Correo enviado exitosamente | ID: {correo['IDCorreo']} | Asunto: '{correo['Asunto']}'")
                    else:
                        logger.error(f"❌ Error enviando correo | ID: {correo['IDCorreo']} | Asunto: '{correo['Asunto']}'")
                except Exception as e:
                    logger.error(f"💥 Error procesando correo ID {correo.get('IDCorreo', 'N/A')}: {e}")
            
            self.db_conn.disconnect()
            return correos_enviados
            
        except Exception as e:
            logger.error(f"Error en enviar_correos_no_enviados: {e}")
            return 0
    
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

    def _marcar_correo_enviado(self, id_correo: int, fecha_envio: datetime):
        """Marcar correo como enviado en la base de datos Access"""
        try:
            update_data = {
                "FechaEnvio": fecha_envio
            }
            where_clause = f"IDCorreo = {id_correo}"
            
            success = self.db_conn.update_record("TbCorreosEnviados", update_data, where_clause)
            if success:
                logger.info(f"✅ Correo ID {id_correo} marcado como enviado correctamente")
            else:
                logger.error(f"❌ Error marcando correo ID {id_correo} como enviado")
                
        except Exception as e:
            logger.error(f"Error marcando correo como enviado: {e}")

    def insertar_correo(self, aplicacion: str, asunto: str, cuerpo: str, 
                       destinatarios: str, destinatarios_cc: str = None, 
                       destinatarios_bcc: str = None, url_adjunto: str = None) -> int:
        """
        Inserta un nuevo correo en la base de datos usando la regla del máximo + 1
        
        Args:
            aplicacion: Nombre de la aplicación
            asunto: Asunto del correo
            cuerpo: Cuerpo del correo
            destinatarios: Destinatarios principales
            destinatarios_cc: Destinatarios con copia (opcional)
            destinatarios_bcc: Destinatarios con copia oculta (opcional)
            url_adjunto: Ruta del archivo adjunto (opcional)
            
        Returns:
            ID del correo insertado o 0 si hubo error
        """
        try:
            self.db_conn.connect()
            
            # Obtener próximo ID usando la regla del máximo + 1
            next_id = self.db_conn.get_max_id("TbCorreosEnviados", "IDCorreo") + 1
            
            # Preparar datos del correo
            email_data = {
                "IDCorreo": next_id,
                "Aplicacion": aplicacion,
                "Asunto": asunto,
                "Cuerpo": cuerpo,
                "Destinatarios": destinatarios,
                "DestinatariosConCopia": destinatarios_cc,
                "DestinatariosConCopiaOculta": destinatarios_bcc,
                "URLAdjunto": url_adjunto,
                "FechaGrabacion": datetime.now(),
                "CuerpoHTML": True if "<" in cuerpo and ">" in cuerpo else False
            }
            
            success = self.db_conn.insert_record("TbCorreosEnviados", email_data)
            
            if success:
                logger.info(f"📧 Correo insertado correctamente | ID: {next_id} | Asunto: '{asunto}'")
                return next_id
            else:
                logger.error(f"❌ Error insertando correo | Asunto: '{asunto}'")
                return 0
                
        except Exception as e:
            logger.error(f"Error insertando correo: {e}")
            return 0
        finally:
            self.db_conn.disconnect()

    def execute_daily_task(self) -> bool:
        """
        Ejecutar la tarea diaria de envío de correos
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            logger.info("🚀 Iniciando tarea diaria de envío de correos")
            
            # Enviar correos pendientes
            enviados = self.enviar_correos_no_enviados()
            
            logger.info(f"✅ Tarea diaria completada exitosamente | Total de correos enviados: {enviados}")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando tarea diaria de correos: {e}")
            return False