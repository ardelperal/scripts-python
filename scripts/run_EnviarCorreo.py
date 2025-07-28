#!/usr/bin/env python3
"""
Script para enviar correos no enviados
Adaptación del script legacy EnviarCorreoNoEnviado.vbs
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from common.config import config
from common.utils import setup_logging, send_email
from common.database_adapter import DatabaseAdapter


def enviar_correos_no_enviados():
    """
    Busca y envía correos que están pendientes de envío en la base de datos.
    Equivalente a la función EnviarCorreosNoEnviados del VBS.
    """
    logger = logging.getLogger(__name__)
    db_adapter = None
    
    try:
        # Conectar a la base de datos de correos
        db_adapter = DatabaseAdapter(config.db_correos_path, config.db_password)
        
        if not db_adapter.connect():
            logger.error("No se pudo conectar a la base de datos de correos")
            return False
        
        # Buscar correos no enviados (FechaEnvio IS NULL)
        sql_query = """
            SELECT TbCorreosEnviados.*
            FROM TbCorreosEnviados
            WHERE TbCorreosEnviados.FechaEnvio IS NULL
        """
        
        correos_pendientes = db_adapter.execute_query(sql_query)
        
        if not correos_pendientes:
            logger.info("No hay correos pendientes de envío")
            return True
        
        logger.info(f"Se encontraron {len(correos_pendientes)} correos pendientes de envío")
        
        # Procesar cada correo pendiente
        for correo in correos_pendientes:
            try:
                id_correo = correo['IDCorreo']
                aplicacion = correo['Aplicacion']
                destinatarios = correo['Destinatarios']
                destinatarios_con_copia = correo['DestinatariosConCopia']
                destinatarios_con_copia_oculta = correo['DestinatariosConCopiaOculta']
                asunto = correo['Asunto']
                cuerpo = correo['Cuerpo']
                url_adjunto = correo['URLAdjunto']
                
                logger.info(f"Procesando correo ID: {id_correo}, Aplicación: {aplicacion}")
                
                # Enviar el correo
                fecha_envio = enviar_correo(
                    aplicacion=aplicacion,
                    asunto=asunto,
                    mensaje=cuerpo,
                    destinatarios=destinatarios,
                    destinatarios_con_copia=destinatarios_con_copia,
                    destinatarios_con_copia_oculta=destinatarios_con_copia_oculta,
                    url_adjuntos=url_adjunto
                )
                
                # Si el envío fue exitoso, actualizar la fecha de envío
                if fecha_envio:
                    update_sql = """
                        UPDATE TbCorreosEnviados 
                        SET FechaEnvio = ? 
                        WHERE IDCorreo = ?
                    """
                    db_adapter.execute_query(update_sql, [fecha_envio, id_correo])
                    logger.info(f"Correo ID {id_correo} enviado exitosamente")
                else:
                    logger.error(f"Error enviando correo ID {id_correo}")
                    
            except Exception as e:
                logger.error(f"Error procesando correo ID {correo.get('IDCorreo', 'desconocido')}: {e}")
                continue
        
        return True
        
    except Exception as e:
        logger.error(f"Error en enviar_correos_no_enviados: {e}")
        return False
        
    finally:
        if db_adapter:
            db_adapter.disconnect()


def enviar_correo(aplicacion, asunto, mensaje, destinatarios, 
                  destinatarios_con_copia=None, destinatarios_con_copia_oculta=None, 
                  url_adjuntos=None):
    """
    Envía un correo electrónico usando la configuración SMTP.
    Equivalente a la función EnviarCorreo del VBS.
    
    Args:
        aplicacion: Nombre de la aplicación que envía el correo
        asunto: Asunto del correo
        mensaje: Cuerpo del correo (HTML)
        destinatarios: Lista de destinatarios principales
        destinatarios_con_copia: Lista de destinatarios en copia
        destinatarios_con_copia_oculta: Lista de destinatarios en copia oculta
        url_adjuntos: Rutas de archivos adjuntos separadas por ';'
        
    Returns:
        datetime: Fecha de envío si fue exitoso, None si falló
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Preparar el remitente (equivalente al VBS: aplicacion + ".DySN@telefonica.com")
        remitente = f"{aplicacion}.DySN@telefonica.com"
        
        # Agregar destinatario en copia oculta por defecto (como en el VBS)
        if destinatarios_con_copia_oculta:
            if "Andres.RomanddelPeral@telefonica.com" not in destinatarios_con_copia_oculta:
                destinatarios_con_copia_oculta += ";Andres.RomanddelPeral@telefonica.com"
        else:
            destinatarios_con_copia_oculta = "Andres.RomanddelPeral@telefonica.com"
        
        # Preparar lista de adjuntos
        adjuntos = []
        if url_adjuntos:
            if ';' in url_adjuntos:
                adjuntos = [adj.strip() for adj in url_adjuntos.split(';') if adj.strip()]
            else:
                adjuntos = [url_adjuntos.strip()] if url_adjuntos.strip() else []
        
        # Enviar el correo usando la función común
        success = send_email(
            to_addresses=destinatarios,
            subject=asunto,
            body=mensaje,
            cc_addresses=destinatarios_con_copia,
            bcc_addresses=destinatarios_con_copia_oculta,
            attachments=adjuntos,
            from_address=remitente,
            is_html=True
        )
        
        if success:
            fecha_envio = datetime.now()
            logger.info(f"Correo enviado exitosamente desde {remitente}")
            return fecha_envio
        else:
            logger.error("Error enviando el correo")
            return None
            
    except Exception as e:
        logger.error(f"Error en enviar_correo: {e}")
        return None


def main():
    """Función principal"""
    # Configurar logging
    setup_logging(config.log_level, config.log_file)
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando script de envío de correos no enviados")
    
    try:
        # Verificar que existe la base de datos de correos
        if not Path(config.db_correos_path).exists():
            logger.error(f"No se encuentra la base de datos de correos: {config.db_correos_path}")
            return 1
        
        # Ejecutar el envío de correos pendientes
        success = enviar_correos_no_enviados()
        
        if success:
            logger.info("Script de envío de correos completado exitosamente")
            return 0
        else:
            logger.error("Error en la ejecución del script de envío de correos")
            return 1
            
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)