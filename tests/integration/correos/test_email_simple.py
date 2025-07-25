"""
Script Python simplificado para envío de correos - Solo para pruebas
"""
import smtplib
import logging
import pyodbc
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import sys
import os

# Añadir path para importar config
sys.path.append(str(Path(__file__).parent.parent))
from common.config import config

logger = logging.getLogger(__name__)

def enviar_correos():
    """Función simplificada para enviar correos"""
    correos_enviados = 0
    
    try:
        # Conectar a Access
        conn = pyodbc.connect(config.get_db_correos_connection_string())
        cursor = conn.cursor()
        
        # Buscar correos pendientes
        sql = """
        SELECT IDCorreo, Aplicacion, Destinatarios, Asunto, Cuerpo
        FROM TbCorreosEnviados 
        WHERE FechaEnvio IS NULL
        """
        
        cursor.execute(sql)
        correos_pendientes = cursor.fetchall()
        
        if not correos_pendientes:
            logger.info("No hay correos pendientes")
            return 0
            
        logger.info(f"Encontrados {len(correos_pendientes)} correos pendientes")
        
        # Configurar SMTP
        if config.environment == 'local':
            smtp_server = 'localhost'
            smtp_port = 1025
        else:
            smtp_server = '10.73.54.85'
            smtp_port = 25
            
        logger.info(f"Configuración SMTP: {smtp_server}:{smtp_port}")
        
        # Enviar correos
        for correo in correos_pendientes:
            try:
                # Crear mensaje
                msg = MIMEMultipart()
                msg['Subject'] = correo.Asunto or 'Sin asunto'
                msg['From'] = config.default_recipient
                msg['To'] = correo.Destinatarios or config.default_recipient
                
                # Cuerpo
                cuerpo = correo.Cuerpo or 'Mensaje vacío'
                if '<html>' in cuerpo.lower():
                    msg.attach(MIMEText(cuerpo, 'html', 'utf-8'))
                else:
                    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
                
                # Enviar
                with smtplib.SMTP(smtp_server, smtp_port) as servidor:
                    servidor.send_message(msg)
                
                # Marcar como enviado
                cursor.execute(
                    "UPDATE TbCorreosEnviados SET FechaEnvio = ? WHERE IDCorreo = ?",
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), correo.IDCorreo)
                )
                conn.commit()
                
                correos_enviados += 1
                logger.info(f"[OK] Correo enviado: ID {correo.IDCorreo} - {correo.Asunto}")
                
            except Exception as e:
                logger.error(f"Error enviando correo {correo.IDCorreo}: {e}")
                continue
        
        conn.close()
        logger.info(f"Proceso completado: {correos_enviados} correos enviados")
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        
    return correos_enviados

def main():
    """Función principal"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    logger.info("Iniciando envío de correos...")
    
    try:
        correos_enviados = enviar_correos()
        if correos_enviados > 0:
            logger.info(f"Correos enviados: {correos_enviados}")
        else:
            logger.info("No hay correos pendientes")
    except Exception as e:
        logger.error(f"Error en main: {e}")

if __name__ == "__main__":
    main()
