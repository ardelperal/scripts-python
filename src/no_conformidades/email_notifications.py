"""
Módulo para gestión de notificaciones de email de no conformidades
Implementa el patrón legacy de registro en base de datos
"""

import sys
import os
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.html_report_generator import HTMLReportGenerator
from common.config import Config

config = Config()
logger = logging.getLogger(__name__)


class EmailNotificationManager:
    """Manager para notificaciones de email de no conformidades"""
    
    def __init__(self):
        self.html_generator = HTMLReportGenerator()
    
    def _generar_reporte_calidad_html(self, ncs_eficacia=None, ncs_caducar=None, ncs_sin_acciones=None, 
                                     destinatarios_calidad="", destinatarios_admin="") -> str:
        """Genera el HTML para el reporte de calidad"""
        try:
            # Usar listas vacías si no se proporcionan datos
            ncs_eficacia = ncs_eficacia or []
            ncs_caducar = ncs_caducar or []
            ncs_sin_acciones = ncs_sin_acciones or []
            
            # Generar reporte completo usando HTMLReportGenerator
            html = self.html_generator.generar_reporte_completo(
                ncs_eficacia=ncs_eficacia,
                arapcs=[],  # No hay ARAPs en reporte de calidad
                ncs_caducar=ncs_caducar,
                ncs_sin_acciones=ncs_sin_acciones,
                titulo="Reporte de Calidad - No Conformidades"
            )
            
            return html
            
        except Exception as e:
            logger.error(f"Error generando HTML de reporte de calidad: {e}")
            return f"<html><body><h1>Error generando reporte</h1><p>{str(e)}</p></body></html>"
    
    def _generar_reporte_tecnico_html(self, arapcs=None, destinatarios_tecnicos="", destinatarios_admin="") -> str:
        """Genera el HTML para el reporte técnico"""
        try:
            # Usar lista vacía si no se proporcionan datos
            arapcs = arapcs or []
            
            # Generar reporte completo usando HTMLReportGenerator
            html = self.html_generator.generar_reporte_completo(
                ncs_eficacia=[],  # No hay NCs de eficacia en reporte técnico
                arapcs=arapcs,
                ncs_caducar=[],  # No hay NCs a caducar en reporte técnico
                ncs_sin_acciones=[],  # No hay NCs sin acciones en reporte técnico
                titulo="Reporte Técnico - ARAPs Próximas a Vencer"
            )
            
            return html
            
        except Exception as e:
            logger.error(f"Error generando HTML de reporte técnico: {e}")
            return f"<html><body><h1>Error generando reporte</h1><p>{str(e)}</p></body></html>"
    
    def _generar_notificacion_individual_html(self, arap, responsable_email) -> str:
        """Genera el HTML para una notificación individual de ARAP"""
        try:
            fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Calcular días restantes
            dias_restantes = 0
            if arap.get('FechaFinPrevista'):
                try:
                    if isinstance(arap['FechaFinPrevista'], str):
                        fecha_fin = datetime.strptime(arap['FechaFinPrevista'], "%Y-%m-%d")
                    else:
                        fecha_fin = arap['FechaFinPrevista']
                    dias_restantes = (fecha_fin - datetime.now()).days
                except:
                    dias_restantes = 0
            
            # Determinar estado y color
            if dias_restantes < 0:
                estado = f"VENCIDA ({abs(dias_restantes)} días)"
                color_estado = "#FF0000"
            elif dias_restantes <= 7:
                estado = f"PRÓXIMA A VENCER ({dias_restantes} días)"
                color_estado = "#FFC107"
            else:
                estado = f"{dias_restantes} días restantes"
                color_estado = "#17A2B8"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Acción Correctiva Pendiente</title>
                <style>
                    body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 10px; }}
                    .header {{ background-color: #4472C4; color: white; padding: 10px; text-align: center; font-weight: bold; }}
                    .content {{ padding: 15px; }}
                    .alert {{ background-color: #FFE6E6; border-left: 4px solid {color_estado}; padding: 10px; margin: 10px 0; }}
                    .info-table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                    .info-table th {{ background-color: #4472C4; color: white; padding: 8px; text-align: left; }}
                    .info-table td {{ padding: 8px; border: 1px solid #ccc; }}
                    .footer {{ margin-top: 20px; font-size: 10px; color: #666; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Acción Correctiva/Preventiva Pendiente</h1>
                    <p>Generado el: {fecha_actual}</p>
                </div>
                
                <div class="content">
                    <div class="alert">
                        <strong>Estado:</strong> {estado}
                    </div>
                    
                    <table class="info-table">
                        <tr>
                            <th>Código NC</th>
                            <td>{arap.get('NumeroNC', 'N/A')}</td>
                        </tr>
                        <tr>
                            <th>Descripción</th>
                            <td>{arap.get('Descripcion', 'N/A')}</td>
                        </tr>
                        <tr>
                            <th>Responsable</th>
                            <td>{arap.get('Responsable', 'N/A')}</td>
                        </tr>
                        <tr>
                            <th>Fecha Fin Prevista</th>
                            <td>{arap.get('FechaFinPrevista', 'N/A')}</td>
                        </tr>
                        <tr>
                            <th>Días Restantes</th>
                            <td style="color: {color_estado}; font-weight: bold;">{dias_restantes}</td>
                        </tr>
                    </table>
                    
                    <p><strong>Por favor, revise el estado de esta acción y actualice la información correspondiente en el sistema.</strong></p>
                </div>
                
                <div class="footer">
                    <p>Sistema de Gestión de No Conformidades - Notificación automática</p>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Error generando HTML de notificación individual: {e}")
            return f"<html><body><h1>Error generando notificación</h1><p>{str(e)}</p></body></html>"
    
    def get_admin_emails(self) -> List[str]:
        """Obtiene los emails de administradores"""
        try:
            db_path = config.get_database_path('tareas')
            connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
            db = AccessDatabase(connection_string)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT Correo 
                    FROM TbUsuarios 
                    WHERE EsAdmin = True AND Correo IS NOT NULL AND Correo <> ''
                """)
                
                result = cursor.fetchall()
                return [row[0] for row in result if row[0]]
                
        except Exception as e:
            logger.error(f"Error obteniendo emails de administradores: {e}")
            return []
    
    def get_quality_emails(self) -> List[str]:
        """Obtiene los emails del departamento de calidad"""
        try:
            db_path = config.get_database_path('tareas')
            connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
            db = AccessDatabase(connection_string)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT Correo 
                    FROM TbUsuarios 
                    WHERE Departamento = 'Calidad' AND Correo IS NOT NULL AND Correo <> ''
                """)
                
                result = cursor.fetchall()
                return [row[0] for row in result if row[0]]
                
        except Exception as e:
            logger.error(f"Error obteniendo emails de calidad: {e}")
            return []
    
    def get_technical_emails(self) -> List[str]:
        """Obtiene los emails del departamento técnico"""
        try:
            db_path = config.get_database_path('tareas')
            connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
            db = AccessDatabase(connection_string)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT Correo 
                    FROM TbUsuarios 
                    WHERE Departamento = 'Técnico' AND Correo IS NOT NULL AND Correo <> ''
                """)
                
                result = cursor.fetchall()
                return [row[0] for row in result if row[0]]
                
        except Exception as e:
            logger.error(f"Error obteniendo emails técnicos: {e}")
            return []


def _register_email_nc(application: str, subject: str, body: str, recipients: str, admin_emails: str = "") -> Optional[int]:
    """
    Registra un email en TbCorreosEnviados siguiendo el patrón legacy
    
    Args:
        application: Aplicación que envía el email
        subject: Asunto del email
        body: Cuerpo del email en HTML
        recipients: Destinatarios principales
        admin_emails: Emails de administradores (opcional)
    
    Returns:
        IDCorreo si se registra exitosamente, None en caso de error
    """
    try:
        # Obtener conexión a la base de datos de correos
        db_path = config.get_database_path('correos')
        connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
        db = AccessDatabase(connection_string)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener el siguiente IDCorreo usando la función existente
            next_id = db.get_max_id("TbCorreosEnviados", "IDCorreo") + 1
            
            # Preparar datos para inserción con formato de fecha para Access
            fecha_actual = datetime.now().strftime("#%m/%d/%Y %H:%M:%S#")
            
            # Insertar el registro
            insert_query = """
                INSERT INTO TbCorreosEnviados 
                (IDCorreo, Aplicacion, Asunto, Cuerpo, Destinatarios, DestinatariosCC, DestinatariosBCC, Fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, [
                next_id,
                application,
                subject,
                body,
                recipients,
                admin_emails,  # CC
                "",           # BCC
                fecha_actual
            ])
            
            conn.commit()
            logger.info(f"Email registrado en TbCorreosEnviados con ID: {next_id}")
            return next_id
            
    except Exception as e:
        logger.error(f"Error registrando email en base de datos: {e}")
        return None


def _register_arapc_notification(id_correo: int, arapcs_15: List[int], arapcs_7: List[int], arapcs_0: List[int]) -> bool:
    """
    Registra las notificaciones ARAPC en TbNCARAvisos siguiendo el patrón legacy
    
    Args:
        id_correo: ID del correo registrado
        arapcs_15: Lista de IDs de acciones con 15 días
        arapcs_7: Lista de IDs de acciones con 7 días  
        arapcs_0: Lista de IDs de acciones con 0 días
    
    Returns:
        True si se registra exitosamente, False en caso de error
    """
    try:
        # Obtener conexión a la base de datos de no conformidades
        db_path = config.get_database_path('no_conformidades')
        connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
        db = AccessDatabase(connection_string)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Registrar cada ARAPC notificada
            all_arapcs = [
                (arapcs_15, 15),
                (arapcs_7, 7), 
                (arapcs_0, 0)
            ]
            
            for arapc_list, dias in all_arapcs:
                for id_accion in arapc_list:
                    insert_query = """
                        INSERT INTO TbNCARAvisos (IDAccion, IDCorreo, DiasAviso, FechaAviso)
                        VALUES (?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_query, [
                        id_accion,
                        id_correo,
                        dias,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ])
            
            conn.commit()
            logger.info(f"Notificaciones ARAPC registradas para correo ID: {id_correo}")
            return True
            
    except Exception as e:
        logger.error(f"Error registrando notificaciones ARAPC: {e}")
        return False


def enviar_notificacion_calidad(datos_calidad: Dict[str, Any]) -> bool:
    """
    Registra notificación de calidad en la base de datos siguiendo el patrón legacy
    
    Args:
        datos_calidad: Diccionario con datos para generar el reporte
    
    Returns:
        True si se registra exitosamente, False en caso contrario
    """
    try:
        # Crear instancia del manager para obtener destinatarios
        manager = EmailNotificationManager()
        
        # Obtener destinatarios
        destinatarios_calidad = manager.get_quality_emails()
        destinatarios_admin = manager.get_admin_emails()
        
        # Verificar que hay destinatarios
        if not destinatarios_calidad and not destinatarios_admin:
            logger.warning("No hay destinatarios para la notificación de calidad")
            return False
        
        # Generar contenido HTML
        html_generator = HTMLReportGenerator()
        cuerpo_html = html_generator.generar_reporte_calidad(datos_calidad)
        
        # Preparar destinatarios
        todos_destinatarios = destinatarios_calidad + destinatarios_admin
        destinatarios_str = "; ".join(todos_destinatarios)
        admin_str = "; ".join(destinatarios_admin) if destinatarios_admin else ""
        
        # Registrar email en base de datos
        id_correo = _register_email_nc(
            application="NoConformidades",
            subject="Reporte de Calidad - No Conformidades",
            body=cuerpo_html,
            recipients=destinatarios_str,
            admin_emails=admin_str
        )
        
        return id_correo is not None
        
    except Exception as e:
        logger.error(f"Error enviando notificación de calidad: {e}")
        return False


def enviar_notificacion_tecnica(datos_tecnicos: Dict[str, Any]) -> bool:
    """
    Registra notificación técnica en la base de datos siguiendo el patrón legacy
    
    Args:
        datos_tecnicos: Diccionario con datos técnicos para el reporte
    
    Returns:
        True si se registra exitosamente, False en caso contrario
    """
    try:
        # Crear instancia del manager para obtener destinatarios
        manager = EmailNotificationManager()
        
        # Obtener destinatarios técnicos
        destinatarios_tecnicos = manager.get_technical_emails()
        destinatarios_admin = manager.get_admin_emails()
        
        # Verificar que hay destinatarios
        if not destinatarios_tecnicos and not destinatarios_admin:
            logger.warning("No hay destinatarios para la notificación técnica")
            return False
        
        # Generar contenido HTML
        html_generator = HTMLReportGenerator()
        cuerpo_html = html_generator.generar_reporte_tecnico(datos_tecnicos)
        
        # Preparar destinatarios
        todos_destinatarios = destinatarios_tecnicos + destinatarios_admin
        destinatarios_str = "; ".join(todos_destinatarios)
        admin_str = "; ".join(destinatarios_admin) if destinatarios_admin else ""
        
        # Registrar email en base de datos
        id_correo = _register_email_nc(
            application="NoConformidades",
            subject="Reporte Técnico - No Conformidades",
            body=cuerpo_html,
            recipients=destinatarios_str,
            admin_emails=admin_str
        )
        
        # Si hay datos de ARAPC, registrar las notificaciones
        if id_correo and 'arapcs' in datos_tecnicos:
            arapcs_data = datos_tecnicos['arapcs']
            _register_arapc_notification(
                id_correo,
                arapcs_data.get('15_dias', []),
                arapcs_data.get('7_dias', []),
                arapcs_data.get('0_dias', [])
            )
        
        return id_correo is not None
        
    except Exception as e:
        logger.error(f"Error enviando notificación técnica: {e}")
        return False


def enviar_notificacion_individual_arapc(arapc_data: Dict[str, Any], usuario_responsable: Dict[str, str]) -> bool:
    """
    Registra notificación individual ARAPC en la base de datos
    
    Args:
        arapc_data: Datos de la acción correctiva
        usuario_responsable: Datos del usuario responsable
    
    Returns:
        True si se registra exitosamente, False en caso contrario
    """
    try:
        # Generar contenido HTML
        html_generator = HTMLReportGenerator()
        cuerpo_html = html_generator.generar_notificacion_individual_arapc(arapc_data, usuario_responsable)
        
        # Preparar destinatarios
        destinatario_principal = usuario_responsable.get('correo', '')
        if not destinatario_principal:
            logger.warning("No hay correo para el usuario responsable")
            return False
        
        # Obtener emails de administradores
        manager = EmailNotificationManager()
        destinatarios_admin = manager.get_admin_emails()
        admin_str = "; ".join(destinatarios_admin) if destinatarios_admin else ""
        
        # Registrar email en base de datos
        id_correo = _register_email_nc(
            application="NoConformidades",
            subject=f"Acción Correctiva Pendiente - {arapc_data.get('codigo_nc', 'N/A')}",
            body=cuerpo_html,
            recipients=destinatario_principal,
            admin_emails=admin_str
        )
        
        # Registrar la notificación ARAPC individual
        if id_correo:
            dias_restantes = arapc_data.get('dias_restantes', 0)
            if dias_restantes <= 0:
                dias_categoria = 0
            elif dias_restantes <= 7:
                dias_categoria = 7
            else:
                dias_categoria = 15
            
            # Crear listas según la categoría
            arapcs_15 = [arapc_data['id_accion']] if dias_categoria == 15 else []
            arapcs_7 = [arapc_data['id_accion']] if dias_categoria == 7 else []
            arapcs_0 = [arapc_data['id_accion']] if dias_categoria == 0 else []
            
            _register_arapc_notification(id_correo, arapcs_15, arapcs_7, arapcs_0)
        
        return id_correo is not None
        
    except Exception as e:
        logger.error(f"Error enviando notificación individual ARAPC: {e}")
        return False


def enviar_notificaciones_individuales_arapcs(arapcs_data: List[Dict[str, Any]], usuarios_responsables: Dict[str, Dict[str, str]]) -> bool:
    """
    Registra múltiples notificaciones individuales ARAPC
    
    Args:
        arapcs_data: Lista de datos de acciones correctivas
        usuarios_responsables: Diccionario de usuarios responsables por ID
    
    Returns:
        True si todas se registran exitosamente, False en caso contrario
    """
    try:
        exito_total = True
        
        for arapc in arapcs_data:
            responsable_id = arapc.get('responsable_id')
            if responsable_id and responsable_id in usuarios_responsables:
                usuario = usuarios_responsables[responsable_id]
                exito = enviar_notificacion_individual_arapc(arapc, usuario)
                if not exito:
                    exito_total = False
                    logger.error(f"Error enviando notificación para ARAPC {arapc.get('id_accion')}")
            else:
                logger.warning(f"No se encontró usuario responsable para ARAPC {arapc.get('id_accion')}")
                exito_total = False
        
        return exito_total
        
    except Exception as e:
        logger.error(f"Error enviando notificaciones individuales ARAPC: {e}")
        return False