"""
Script independiente para probar el sistema de correos con MailHog
"""
import smtplib
import logging
import sqlite3
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# Configuración simplificada
DB_PATH = "dbs-sqlite/correos_datos.sqlite"
SMTP_SERVER = "localhost"
SMTP_PORT = 1025
DEFAULT_EMAIL = "admin@empresa.com"

def main():
    """Función principal"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=== PRUEBA DE SISTEMA DE CORREOS CON MAILHOG ===")
    
    correos_enviados = 0
    
    try:
        # Conectar a SQLite
        logger.info(f"Conectando a base de datos: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
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
            return
            
        logger.info(f"Encontrados {len(correos_pendientes)} correos pendientes")
        logger.info(f"Configuración SMTP: {SMTP_SERVER}:{SMTP_PORT}")
        
        # Enviar correos
        for correo in correos_pendientes:
            try:
                # Crear mensaje
                msg = MIMEMultipart()
                msg['Subject'] = correo['Asunto'] or 'Sin asunto'
                msg['From'] = DEFAULT_EMAIL
                
                # Procesar destinatarios (separados por ; o ,)
                destinatarios_raw = correo['Destinatarios'] or DEFAULT_EMAIL
                if ';' in destinatarios_raw:
                    destinatarios_lista = [d.strip() for d in destinatarios_raw.split(';') if d.strip()]
                elif ',' in destinatarios_raw:
                    destinatarios_lista = [d.strip() for d in destinatarios_raw.split(',') if d.strip()]
                else:
                    destinatarios_lista = [destinatarios_raw.strip()]
                
                # Filtrar destinatarios vacíos
                destinatarios_validos = [d for d in destinatarios_lista if d and '@' in d]
                if not destinatarios_validos:
                    destinatarios_validos = [DEFAULT_EMAIL]
                
                msg['To'] = ', '.join(destinatarios_validos)
                logger.info(f"Correo ID {correo['IDCorreo']}: Destinatarios: {destinatarios_validos}")
                
                # Cuerpo - mejorar detección de HTML y crear documento completo
                cuerpo = correo['Cuerpo'] or 'Mensaje vacío'
                
                # Detectar si es HTML (buscar tags HTML comunes)
                html_tags = ['<h1>', '<h2>', '<h3>', '<p>', '<div>', '<ul>', '<ol>', '<li>', '<br>', '<strong>', '<b>', '<i>', '<em>']
                es_html = any(tag in cuerpo.lower() for tag in html_tags)
                
                if es_html:
                    # Crear documento HTML completo
                    html_completo = f"""
                    <!DOCTYPE html>
                    <html lang="es">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>{correo['Asunto'] or 'Correo del Sistema'}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                            h1, h2, h3 {{ color: #2c3e50; }}
                            ul {{ padding-left: 20px; }}
                            li {{ margin: 5px 0; }}
                            .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                            .content {{ background-color: #ffffff; }}
                            .footer {{ margin-top: 30px; padding: 15px; background-color: #e9ecef; border-radius: 5px; font-size: 0.9em; color: #6c757d; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>📧 {correo['Aplicacion'] or 'Sistema'}</h1>
                        </div>
                        <div class="content">
                            {cuerpo}
                        </div>
                        <div class="footer">
                            <p><strong>Enviado por:</strong> Sistema Automatizado de Correos</p>
                            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                        </div>
                    </body>
                    </html>
                    """
                    msg.attach(MIMEText(html_completo, 'html', 'utf-8'))
                    logger.info(f"Correo ID {correo['IDCorreo']}: Enviado como HTML")
                else:
                    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
                    logger.info(f"Correo ID {correo['IDCorreo']}: Enviado como texto plano")
                
                # Enviar por SMTP
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
                    servidor.send_message(msg, to_addrs=destinatarios_validos)
                
                # Marcar como enviado
                cursor.execute(
                    "UPDATE TbCorreosEnviados SET FechaEnvio = ? WHERE IDCorreo = ?",
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), correo['IDCorreo'])
                )
                conn.commit()
                
                correos_enviados += 1
                logger.info(f"[OK] Correo enviado: ID {correo['IDCorreo']} - {correo['Asunto']}")
                
            except Exception as e:
                logger.error(f"[ERROR] Error enviando correo ID {correo['IDCorreo']}: {e}")
                continue
        
        conn.close()
        
        logger.info("=" * 50)
        logger.info(f"RESULTADO: {correos_enviados} correos enviados exitosamente")
        logger.info("Ver correos en MailHog: http://localhost:8025")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error general: {e}")

if __name__ == "__main__":
    main()
