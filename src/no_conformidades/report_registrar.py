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
    
    # Legacy generator methods eliminados (_generar_reporte_*, _generar_notificacion_individual_html)
    
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
        except Exception as e:  # pragma: no cover - acceso BD auxiliar
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
        except Exception as e:  # pragma: no cover - acceso BD auxiliar
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
        except Exception as e:  # pragma: no cover - generación HTML fallback
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
        except Exception as e:  # pragma: no cover - acceso BD auxiliar
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
            
    except Exception as e:  # pragma: no cover - registro email
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
            
    except Exception as e:  # pragma: no cover - registro avisos ARAPC
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
        # Adaptación a estructura moderna: esperados keys similares
        cuerpo_html = html_generator.generar_reporte_calidad_moderno(
            datos_calidad.get('ars_proximas_vencer', []),
            datos_calidad.get('ncs_pendientes_eficacia', []),
            datos_calidad.get('ncs_sin_acciones', []),
            datos_calidad.get('ars_para_replanificar', [])
        )
        
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
        
    except Exception as e:  # pragma: no cover - error envío calidad
        logger.error(f"Error enviando notificación de calidad: {e}")
        return False




def enviar_notificacion_tecnico_individual(tecnico: str, datos_tecnico: Dict[str, Any]) -> bool:
    """Genera y registra una notificación individual para un técnico.

    Args:
        tecnico: Identificador / nombre del técnico (RESPONSABLETELEFONICA).
        datos_tecnico: Dict con listas 'ars_15_dias', 'ars_7_dias', 'ars_vencidas'.

    Returns:
        True si se registró un correo (o no había contenido y se omite sin error), False en fallo.
    """
    try:
        html_generator = HTMLReportGenerator()
        cuerpo_html = html_generator.generar_reporte_tecnico_moderno(
            datos_tecnico.get('ars_15_dias', []),
            datos_tecnico.get('ars_7_dias', []),
            datos_tecnico.get('ars_vencidas', []),
        )

        if not cuerpo_html.strip():
            logger.info(f"Sin contenido para correo técnico {tecnico}; se omite.")
            return True  # No es error: simplemente nada que enviar

        # Obtener email del técnico: heurística simple (buscar en TbUsuariosAplicaciones)
        email_tecnico = _obtener_email_tecnico(tecnico) or ""
        if not email_tecnico:
            logger.warning(f"No se encontró email para técnico {tecnico}; se aborta notificación.")
            return False

        admin_emails = ReportRegistrar().get_admin_emails()
        admin_str = "; ".join(admin_emails) if admin_emails else ""

        id_correo = _register_email_nc(
            application="NoConformidades",
            subject=f"Acciones de Resolución Pendientes ({tecnico})",
            body=cuerpo_html,
            recipients=email_tecnico,
            admin_emails=admin_str,
        )

        if id_correo:
            # Extraer IDs para registrar avisos y evitar repetición
            ids_15 = [ar.get('IDAccionRealizada') or ar.get('IDAccion') for ar in datos_tecnico.get('ars_15_dias', []) if ar]
            ids_7 = [ar.get('IDAccionRealizada') or ar.get('IDAccion') for ar in datos_tecnico.get('ars_7_dias', []) if ar]
            ids_0 = [ar.get('IDAccionRealizada') or ar.get('IDAccion') for ar in datos_tecnico.get('ars_vencidas', []) if ar]
            _register_arapc_notification(id_correo, ids_15, ids_7, ids_0)

        return id_correo is not None
    except Exception as e:  # pragma: no cover - error notificación técnica individual
        logger.error(f"Error enviando notificación técnica individual {tecnico}: {e}")
        return False


def _obtener_email_tecnico(tecnico: str) -> Optional[str]:
    """Intenta recuperar el email del técnico desde la base de datos de tareas.

    Se mantiene aquí una implementación liviana para evitar dependencias circulares.
    """
    try:
        db_path = config.get_database_path('tareas')
        connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
        db = AccessDatabase(connection_string)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT TOP 1 Correo FROM TbUsuarios WHERE UsuarioRed = ? AND Correo IS NOT NULL AND Correo <> ''",
                (tecnico,),
            )
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception as e:  # pragma: no cover - camino de error no crítico
        logger.debug(f"No se pudo obtener email para técnico {tecnico}: {e}")
    return None