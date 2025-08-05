"""
Gestor de Tareas
Adaptación del script legacy EnviarCorreoTareas.vbs
"""
import smtplib
import logging
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional

from common.config import config
from common.database import AccessDatabase
from common.access_connection_pool import get_tareas_connection_pool

logger = logging.getLogger(__name__)


class CorreoTareasManager:
    """Gestor para el módulo de tareas"""
    
    def __init__(self):
        """Inicializar el gestor de tareas"""
        self.config = config
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.smtp_user = config.smtp_user
        self.smtp_password = getattr(config, 'smtp_password', None)
        self.smtp_tls = getattr(config, 'smtp_tls', False)
        
        # Usar pool de conexiones thread-safe para Access
        connection_string = config.get_db_connection_string('tareas')
        self.db_pool = get_tareas_connection_pool(connection_string)
        
        # Mantener compatibilidad con código existente
        self.db_conn = self.db_pool
        
        logger.info("CorreoTareasManager inicializado con pool de conexiones thread-safe")
    
    def _enviar_correo_individual(self, correo: Dict[str, Any]) -> bool:
        """
        Envía un correo individual usando los datos del registro.
        """
        try:
            msg = MIMEMultipart()
            # Construir el remitente usando el campo Aplicacion como en el legacy VBS
            aplicacion = correo.get('Aplicacion', 'Tareas')
            from_email = f"{aplicacion}.DySN@telefonica.com"
            msg['From'] = from_email
            msg['To'] = correo['Destinatarios']
            if correo.get('DestinatariosConCopia'):
                msg['Cc'] = correo['DestinatariosConCopia']
            if correo.get('DestinatariosConCopiaOculta'):
                msg['Bcc'] = correo['DestinatariosConCopiaOculta']
            
            msg['Subject'] = correo['Asunto']
            
            # Cuerpo del mensaje
            cuerpo = correo.get('Cuerpo', 'Mensaje vacío')
            if '<html>' in cuerpo.lower() or '<body>' in cuerpo.lower():
                msg.attach(MIMEText(cuerpo, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
            
            # Adjuntos si existen
            if correo.get('URLAdjunto'):
                self._agregar_adjuntos(msg, correo['URLAdjunto'])
            
            # Preparar lista de destinatarios
            destinatarios = []
            if correo['Destinatarios']:
                destinatarios.extend([email.strip() for email in correo['Destinatarios'].split(';')])
            if correo.get('DestinatariosConCopia'):
                destinatarios.extend([email.strip() for email in correo['DestinatariosConCopia'].split(';')])
            if correo.get('DestinatariosConCopiaOculta'):
                destinatarios.extend([email.strip() for email in correo['DestinatariosConCopiaOculta'].split(';')])
            
            # Enviar correo
            success = self._enviar_smtp(msg, destinatarios)
            
            if success:
                logger.info(f"Correo enviado exitosamente - ID: {correo['IDCorreo']}")
                # Marcar como enviado en la base de datos
                self._marcar_correo_enviado(correo['IDCorreo'], datetime.now())
                return True
            else:
                logger.error(f"Error enviando correo - ID: {correo['IDCorreo']}")
                return False
                
        except Exception as e:
            logger.error(f"Error en _enviar_correo_individual: {e}")
            return False
    
    def _agregar_adjuntos(self, msg: MIMEMultipart, url_adjuntos: str):
        """Agregar adjuntos al mensaje"""
        try:
            if ';' in url_adjuntos:
                # Múltiples adjuntos separados por ;
                adjuntos = url_adjuntos.split(';')
            else:
                # Un solo adjunto
                adjuntos = [url_adjuntos]
            
            for adjunto_path in adjuntos:
                adjunto_path = adjunto_path.strip()
                if adjunto_path and Path(adjunto_path).exists():
                    with open(adjunto_path, 'rb') as adjunto:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(adjunto.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {Path(adjunto_path).name}'
                        )
                        msg.attach(part)
                        logger.info(f"Adjunto agregado: {adjunto_path}")
                else:
                    logger.warning(f"Adjunto no encontrado: {adjunto_path}")
                    
        except Exception as e:
            logger.error(f"Error agregando adjuntos: {e}")
    
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
        """Marcar correo como enviado en la base de datos Access usando pool thread-safe"""
        try:
            update_data = {
                "FechaEnvio": fecha_envio
            }
            where_clause = f"IDCorreo = {id_correo}"
            
            # Usar el método thread-safe del pool
            success = self.db_pool.update_record("TbCorreosEnviados", update_data, where_clause)
            if success:
                logger.info(f"Correo ID {id_correo} marcado como enviado (thread-safe)")
            else:
                logger.error(f"Error marcando correo ID {id_correo} como enviado")
                
        except Exception as e:
            logger.error(f"Error marcando correo como enviado: {e}")
    
    def obtener_correos_pendientes(self) -> List[Dict[str, Any]]:
        """Obtener correos pendientes de envío usando pool thread-safe"""
        try:
            query = """
            SELECT TbCorreosEnviados.* 
            FROM TbCorreosEnviados 
            WHERE TbCorreosEnviados.FechaEnvio IS NULL
            ORDER BY TbCorreosEnviados.IDCorreo
            """
            
            # Usar el método thread-safe del pool
            correos = self.db_pool.execute_query(query)
            logger.info(f"Obtenidos {len(correos)} correos pendientes (thread-safe)")
            return correos
            
        except Exception as e:
            logger.error(f"Error obteniendo correos pendientes: {e}")
            return []
    
    def enviar_correos_no_enviados(self) -> int:
        """
        Enviar todos los correos pendientes de la base de datos de tareas.
        
        Returns:
            Número de correos enviados exitosamente
        """
        correos_enviados = 0
        
        try:
            logger.info("Iniciando envío de correos de tareas no enviados")
            
            # Obtener correos pendientes
            correos_pendientes = self.obtener_correos_pendientes()
            
            if not correos_pendientes:
                logger.info("No hay correos pendientes de tareas")
                return 0
            
            # Procesar cada correo
            for correo in correos_pendientes:
                try:
                    logger.info(f"Procesando correo ID: {correo['IDCorreo']}")
                    
                    if self._enviar_correo_individual(correo):
                        correos_enviados += 1
                        logger.info(f"Correo ID {correo['IDCorreo']} enviado exitosamente")
                    else:
                        logger.error(f"Error enviando correo ID {correo['IDCorreo']}")
                        
                except Exception as e:
                    logger.error(f"Error procesando correo ID {correo.get('IDCorreo', 'desconocido')}: {e}")
                    continue
            
            logger.info(f"Proceso completado. Correos enviados: {correos_enviados}/{len(correos_pendientes)}")
            return correos_enviados
            
        except Exception as e:
            logger.error(f"Error en enviar_correos_no_enviados: {e}")
            return correos_enviados
    
    def registrar_correo_enviado(self, id_correo: int) -> bool:
        """
        Registrar un correo como enviado (función auxiliar)
        
        Args:
            id_correo: ID del correo a marcar como enviado
            
        Returns:
            True si se marcó correctamente, False en caso contrario
        """
        try:
            self._marcar_correo_enviado(id_correo, datetime.now())
            return True
        except Exception as e:
            logger.error(f"Error registrando correo enviado ID {id_correo}: {e}")
            return False
    
    def execute_daily_task(self) -> bool:
        """
        Ejecutar la tarea diaria de envío de correos de tareas
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            logger.info("Iniciando tarea diaria de envío de correos de tareas")
            
            # Enviar correos pendientes
            enviados = self.enviar_correos_no_enviados()
            
            logger.info(f"Tarea diaria de tareas completada. Total de correos enviados: {enviados}")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando tarea diaria de tareas: {e}")
            return False
    
    def execute_continuous_task(self) -> bool:
        """
        Ejecutar la tarea continua de envío de correos de tareas
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            logger.info("Iniciando tarea continua de envío de correos de tareas")
            
            # Enviar correos pendientes
            enviados = self.enviar_correos_no_enviados()
            
            if enviados > 0:
                logger.info(f"Tarea continua de tareas completada. Correos enviados: {enviados}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando tarea continua de tareas: {e}")
            return False