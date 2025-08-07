"""
Módulo para gestión de notificaciones de email de no conformidades
Implementa el patrón de registro en base de datos
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
from common.database import AccessDatabase

config = Config()
logger = logging.getLogger(__name__)


class ReportRegistrar:
    """Manager para el registro de reportes de no conformidades"""
    
    def __init__(self):
        self.html_generator = HTMLReportGenerator()
    
    def _generar_reporte_calidad_html(self, ars_proximas_vencer=None, ncs_pendientes_eficacia=None, 
                                     ncs_sin_acciones=None, ars_para_replanificar=None, 
                                     destinatarios_calidad="", destinatarios_admin="") -> str:
        """Genera el HTML para el reporte de calidad"""
        try:
            # Usar listas vacías si no se proporcionan datos
            ars_proximas_vencer = ars_proximas_vencer or []
            ncs_pendientes_eficacia = ncs_pendientes_eficacia or []
            ncs_sin_acciones = ncs_sin_acciones or []
            ars_para_replanificar = ars_para_replanificar or []
            
            # Generar reporte completo usando HTMLReportGenerator
            html = self.html_generator.generar_reporte_completo(
                ncs_eficacia=ncs_pendientes_eficacia,
                arapcs=[],  # No hay ARAPs en reporte de calidad
                ncs_caducar=ars_proximas_vencer,
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
            logger.debug(f"Generando reporte técnico con {len(arapcs) if arapcs else 0} ARAPs.")
            # Usar lista vacía si no se proporcionan datos
            arapcs = arapcs or []
            
            # Generar reporte completo usando HTMLReportGenerator
            html = self.html_generator.generar_reporte_completo(
                ncs_eficacia=[],
                arapcs=arapcs,
                ncs_caducar=[],
                ncs_sin_acciones=[],
                titulo="Reporte Técnico - Tareas de Acciones Correctivas a punto de caducar o caducadas"
            )
            
            logger.debug("HTML de reporte técnico generado correctamente.")
            return html
            
        except Exception as e:
            logger.error(f"Error generando HTML de reporte técnico: {e}", exc_info=True)
            return f"<html><body><h1>Error generando reporte</h1><p>{str(e)}</p></body></html>"
    
    def _generar_notificacion_individual_html(self, arap: Dict[str, Any], responsable_email: str = "") -> str:
        """Genera el HTML para una notificación individual de ARAP"""
        try:
            fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Calcular días restantes
            dias_restantes = 0
            fecha_fin_prevista = arap.get('FechaFinPrevista')
            if fecha_fin_prevista:
                try:
                    if isinstance(fecha_fin_prevista, str):
                        fecha_fin = datetime.strptime(fecha_fin_prevista, "%Y-%m-%d")
                    else:
                        fecha_fin = fecha_fin_prevista
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
            
            css_styles = self.html_generator.get_css_styles()
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="ISO-8859-1">
    <title>Acción Correctiva Próxima a Vencer</title>
    <style>{css_styles}</style>
</head>
<body>
    <table>
        <tr>
            <td colspan='2' class='ColespanArriba'>Acción Correctiva/Preventiva Próxima a Vencer</td>
        </tr>
        <tr>
            <td class='Cabecera'>Código NC</td>
            <td>{arap.get('CodigoNoConformidad', 'N/A')}</td>
        </tr>
        <tr>
            <td class='Cabecera'>Descripción de la Acción</td>
            <td>{arap.get('AccionRealizada', 'N/A')}</td>
        </tr>
        <tr>
            <td class='Cabecera'>Responsable</td>
            <td>{responsable_email if responsable_email else arap.get('Responsable', 'N/A')}</td>
        </tr>
        <tr>
            <td class='Cabecera'>Fecha Fin Prevista</td>
            <td>{arap.get('FechaFinPrevista').strftime('%d/%m/%Y') if arap.get('FechaFinPrevista') else 'N/A'}</td>
        </tr>
        <tr>
            <td class='Cabecera'>Estado</td>
            <td style="color: {color_estado}; font-weight: bold;">{estado}</td>
        </tr>
    </table>
    <p><strong>Por favor, revise el estado de esta acción y actualice la información correspondiente en el sistema.</strong></p>
    <p>Sistema de Gestión de No Conformidades - Notificación automática</p>
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
                    FROM TbUsuariosAplicacionesAplicaciones 
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
    


    def generate_technical_report_html(self, ars_proximas_vencer_8_15=None, ars_proximas_vencer_1_7=None, 
                                      ars_vencidas=None) -> str:
        """Genera el HTML para el reporte técnico individual"""
        try:
            # Usar listas vacías si no se proporcionan datos
            ars_proximas_vencer_8_15 = ars_proximas_vencer_8_15 or []
            ars_proximas_vencer_1_7 = ars_proximas_vencer_1_7 or []
            ars_vencidas = ars_vencidas or []
            
            css_styles = self.html_generator.get_css_styles()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Aviso de Acciones de Resolución</title>
    <style>{css_styles}</style>
</head>
<body>
    <h2>Aviso de Acciones de Resolución Próximas a Vencer o Vencidas</h2>
    <p>Este es un resumen de las Acciones de Resolución asignadas que requieren su atención.</p>
"""

            if ars_proximas_vencer_8_15:
                html += "<h3>Acciones Próximas a Vencer (8-15 días)</h3>"
                html += self.html_generator.generate_table(ars_proximas_vencer_8_15, 
                    ["Código NC", "Nemotécnico", "Acción Correctiva", "Acción Realizada", "Fecha Fin Prevista", "Días"])

            if ars_proximas_vencer_1_7:
                html += "<h3>Acciones Próximas a Vencer (1-7 días)</h3>"
                html += self.html_generator.generate_table(ars_proximas_vencer_1_7, 
                    ["Código NC", "Nemotécnico", "Acción Correctiva", "Acción Realizada", "Fecha Fin Prevista", "Días"])

            if ars_vencidas:
                html += "<h3>Acciones Vencidas</h3>"
                html += self.html_generator.generate_table(ars_vencidas, 
                    ["Código NC", "Nemotécnico", "Acción Correctiva", "Acción Realizada", "Fecha Fin Prevista", "Días"])

            html += """
                <hr>
                <div style="text-align: center; margin-top: 20px;">
                    <p><strong>Por favor, revise el estado de estas acciones y actualice la información correspondiente en el sistema.</strong></p>
                    <p>Sistema de Gestión de No Conformidades - Notificación automática</p>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Error generando HTML de reporte técnico: {e}")
            return f"<html><body><h1>Error generando reporte</h1><p>{str(e)}</p></body></html>"

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
    Registra un email en TbCorreosEnviados
    
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
        # Obtener conexión a la base de datos de tareas (no correos)
        connection_string = config.get_db_tareas_connection_string()
        db = AccessDatabase(connection_string)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener el siguiente IDCorreo usando la función existente
            next_id = db.get_max_id("TbCorreosEnviados", "IDCorreo") + 1
            
            # Preparar datos para inserción con formato de fecha para Access
            fecha_actual = datetime.now()
            
            # Insertar el registro usando los nombres de columnas correctos
            insert_query = """
                INSERT INTO TbCorreosEnviados 
                (IDCorreo, Aplicacion, Asunto, Cuerpo, Destinatarios, DestinatariosConCopia, DestinatariosConCopiaOculta, FechaGrabacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, [
                next_id,
                application,
                subject,
                body.strip(),  # Aplicar trim para eliminar espacios en blanco al inicio y final
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
    Registra las notificaciones ARAPC en TbNCARAvisos
    
    Args:
        id_correo: ID del correo registrado
        arapcs_15: Lista de IDs de acciones con 15 días
        arapcs_7: Lista de IDs de acciones con 7 días  
        arapcs_0: Lista de IDs de acciones con 0 días
    
    Returns:
        True si se registra exitosamente, False en caso de error
    """
    try:
        # Obtener conexión a la base de datos de no conformidades (donde está TbNCARAvisos)
        db_path = config.get_database_path('no_conformidades')
        connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD=dpddpd;"
        db = AccessDatabase(connection_string)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Función auxiliar para obtener el próximo ID
            def get_next_id():
                try:
                    cursor.execute("SELECT Max(TbNCARAvisos.ID) AS Maximo FROM TbNCARAvisos")
                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        return result[0] + 1
                    return 1
                except:
                    # Si la tabla no existe, crear el primer registro
                    return 1
            
            # Registrar avisos de 15 días
            for id_accion in arapcs_15:
                next_id = get_next_id()
                insert_query = """
                    INSERT INTO TbNCARAvisos (ID, IDAR, IDCorreo15, Fecha)
                    VALUES (?, ?, ?, ?)
                """
                cursor.execute(insert_query, [next_id, id_accion, id_correo, datetime.now()])
            
            # Registrar avisos de 7 días
            for id_accion in arapcs_7:
                next_id = get_next_id()
                insert_query = """
                    INSERT INTO TbNCARAvisos (ID, IDAR, IDCorreo7, Fecha)
                    VALUES (?, ?, ?, ?)
                """
                cursor.execute(insert_query, [next_id, id_accion, id_correo, datetime.now()])
            
            # Registrar avisos de 0 días
            for id_accion in arapcs_0:
                next_id = get_next_id()
                insert_query = """
                    INSERT INTO TbNCARAvisos (ID, IDAR, IDCorreo0, Fecha)
                    VALUES (?, ?, ?, ?)
                """
                cursor.execute(insert_query, [next_id, id_accion, id_correo, datetime.now()])
            
            conn.commit()
            logger.info(f"Notificaciones ARAPC registradas para correo ID: {id_correo}")
            return True
            
    except Exception as e:
        logger.error(f"Error registrando notificaciones ARAPC: {e}")
        return False


def enviar_notificacion_calidad(datos_calidad: Dict[str, Any]) -> bool:
    """
    Registra notificación de calidad en la base de datos
    
    Args:
        datos_calidad: Diccionario con datos para generar el reporte
    
    Returns:
        True si se registra exitosamente, False en caso contrario
    """
    try:
        # Crear instancia del manager para obtener destinatarios
        manager = ReportRegistrar()
        
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
            subject="Listado de No Conformidades Pendientes",
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
    Registra notificación técnica en la base de datos
    
    Args:
        datos_tecnicos: Diccionario con datos técnicos para el reporte
    
    Returns:
        True si se registra exitosamente, False en caso contrario
    """
    try:
        # Crear instancia del manager para obtener destinatarios
        manager = ReportRegistrar()
        
        # Obtener destinatarios técnicos
        destinatarios_tecnicos = manager.get_quality_emails()  # Usar quality_emails ya que no existe get_technical_emails
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
        manager = ReportRegistrar()
        destinatarios_admin = manager.get_admin_emails()
        admin_str = "; ".join(destinatarios_admin) if destinatarios_admin else ""
        
        # Registrar email en base de datos
        id_correo = _register_email_nc(
            application="NoConformidades",
            subject="Aviso de Accion Correctiva/Preventiva proxima a su vencimiento",
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