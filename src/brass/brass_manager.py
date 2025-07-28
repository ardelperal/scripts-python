"""
Módulo BRASS - Gestión de equipos de medida y calibraciones
Adaptación del sistema legacy VBS a Python
"""
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path

from common import (
    config,
    AccessDatabase,
    load_css_content,
    generate_html_header,
    generate_html_footer,
    safe_str
)

logger = logging.getLogger(__name__)


class BrassManager:
    """Gestor principal del módulo BRASS"""
    
    def __init__(self):
        # Inicializar conexiones a bases de datos
        self.db_brass = AccessDatabase(config.get_db_brass_connection_string())
        self.db_tareas = AccessDatabase(config.get_db_tareas_connection_string())
        
        # Cargar contenido CSS
        self.css_content = load_css_content(config.css_file_path)
        
        # Cache para usuarios administradores
        self._admin_users = None
        self._admin_emails = None
    
    def get_last_execution_date(self) -> Optional[date]:
        """
        Obtiene la fecha de la última ejecución de la tarea BRASS
        
        Returns:
            Fecha de última ejecución o None si no existe
        """
        try:
            query = """
                SELECT MAX(Fecha) as Ultima 
                FROM TbTareas 
                WHERE Tarea = 'BRASSDiario' AND Realizado = 'Sí'
            """
            
            result = self.db_tareas.execute_query(query)
            
            if result and result[0]['Ultima']:
                fecha = result[0]['Ultima']
                # Convertir a date si es datetime
                if isinstance(fecha, datetime):
                    return fecha.date()
                elif isinstance(fecha, date):
                    return fecha
                
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo fecha de última ejecución: {e}")
            return None
    
    def is_task_completed_today(self) -> bool:
        """
        Verifica si la tarea ya se ejecutó hoy
        
        Returns:
            True si ya se ejecutó hoy, False en caso contrario
        """
        last_execution = self.get_last_execution_date()
        today = date.today()
        
        if last_execution is None:
            return False
        
        return last_execution == today
    
    def get_equipment_out_of_calibration(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de equipos de medida que están fuera de calibración
        
        Returns:
            Lista de equipos fuera de calibración
        """
        try:
            # Primero obtener todos los equipos activos
            query_equipos = """
                SELECT IDEquipoMedida, NOMBRE, NS, PN, MARCA, MODELO
                FROM TbEquiposMedida 
                WHERE FechaFinServicio IS NULL
            """
            
            equipos = self.db_brass.execute_query(query_equipos)
            equipos_sin_calibracion = []
            
            for equipo in equipos:
                if not self._is_calibration_valid(equipo['IDEquipoMedida']):
                    equipos_sin_calibracion.append(equipo)
            
            logger.info(f"Encontrados {len(equipos_sin_calibracion)} equipos fuera de calibración")
            return equipos_sin_calibracion
            
        except Exception as e:
            logger.error(f"Error obteniendo equipos fuera de calibración: {e}")
            return []
    
    def _is_calibration_valid(self, equipment_id: int) -> bool:
        """
        Verifica si la calibración de un equipo está vigente
        
        Args:
            equipment_id: ID del equipo de medida
            
        Returns:
            True si la calibración está vigente
        """
        try:
            query = """
                SELECT FechaFinCalibracion 
                FROM TbEquiposMedidaCalibraciones 
                WHERE IDEquipoMedida = ? 
                ORDER BY IDCalibracion DESC
            """
            
            result = self.db_brass.execute_query(query, (equipment_id,))
            
            if not result:
                return False
            
            fecha_fin = result[0]['FechaFinCalibracion']
            if not fecha_fin:
                return False
            
            # Convertir a date si es necesario
            if isinstance(fecha_fin, datetime):
                fecha_fin = fecha_fin.date()
            
            return date.today() < fecha_fin
            
        except Exception as e:
            logger.error(f"Error verificando calibración del equipo {equipment_id}: {e}")
            return False
    
    def generate_html_report(self, equipment_list: List[Dict[str, Any]]) -> str:
        """
        Genera el reporte HTML de equipos fuera de calibración
        
        Args:
            equipment_list: Lista de equipos fuera de calibración
            
        Returns:
            HTML del reporte
        """
        if not equipment_list:
            return ""
        
        title = "INFORME DE AVISOS DE EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN"
        html_content = generate_html_header(title, self.css_content)
        
        html_content += f"<h1>{title}</h1>\n"
        html_content += "<br><br>\n"
        
        # Tabla de equipos
        html_content += "<table>\n"
        html_content += "<tr>\n"
        html_content += '<td colspan="5" class="ColespanArriba">EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN</td>\n'
        html_content += "</tr>\n"
        
        # Encabezados
        html_content += "<tr>\n"
        html_content += '<td class="centrado"><strong>NOMBRE</strong></td>\n'
        html_content += '<td class="centrado"><strong>NS</strong></td>\n'
        html_content += '<td class="centrado"><strong>PN</strong></td>\n'
        html_content += '<td class="centrado"><strong>MARCA</strong></td>\n'
        html_content += '<td class="centrado"><strong>MODELO</strong></td>\n'
        html_content += "</tr>\n"
        
        # Filas de datos
        for equipo in equipment_list:
            html_content += "<tr>\n"
            html_content += f"<td>{safe_str(equipo.get('NOMBRE'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('NS'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('PN'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('MARCA'))}</td>\n"
            html_content += f"<td>{safe_str(equipo.get('MODELO'))}</td>\n"
            html_content += "</tr>\n"
        
        html_content += "</table>\n"
        html_content += generate_html_footer()
        
        return html_content
    
    def get_admin_users(self) -> List[Dict[str, str]]:
        """
        Obtiene la lista de usuarios administradores
        
        Returns:
            Lista de usuarios administradores
        """
        if self._admin_users is not None:
            return self._admin_users
        
        try:
            query = """
                SELECT ua.UsuarioRed, ua.Nombre, ua.CorreoUsuario 
                FROM TbUsuariosAplicaciones ua 
                INNER JOIN TbUsuariosAplicacionesTareas uat ON ua.CorreoUsuario = uat.CorreoUsuario 
                WHERE ua.ParaTareasProgramadas = True 
                AND ua.FechaBaja IS NULL 
                AND uat.EsAdministrador = 'Sí'
            """
            
            result = self.db_tareas.execute_query(query)
            self._admin_users = result
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios administradores: {e}")
            return []
    
    def get_admin_emails_string(self) -> str:
        """
        Obtiene la cadena de correos de administradores separados por ;
        
        Returns:
            String con correos separados por ;
        """
        if self._admin_emails is not None:
            return self._admin_emails
        
        admin_users = self.get_admin_users()
        emails = [user['CorreoUsuario'] for user in admin_users if user['CorreoUsuario']]
        self._admin_emails = ';'.join(emails)
        return self._admin_emails
    
    def register_email(self, subject: str, body: str, recipients: str) -> bool:
        """
        Registra un correo en la base de datos de tareas
        
        Args:
            subject: Asunto del correo
            body: Cuerpo del correo
            recipients: Destinatarios del correo
            
        Returns:
            True si se registró correctamente
        """
        try:
            # Obtener próximo ID
            next_id = self.db_tareas.get_max_id("TbCorreosEnviados", "IDCorreo") + 1
            
            # Preparar datos del correo
            email_data = {
                "IDCorreo": next_id,
                "Aplicacion": "BRASS",
                "Asunto": subject,
                "Cuerpo": body,
                "Destinatarios": recipients if "@" in recipients else "",
                "DestinatariosConCopiaOculta": self.get_admin_emails_string(),
                "FechaGrabacion": datetime.now()
            }
            
            success = self.db_tareas.insert_record("TbCorreosEnviados", email_data)
            
            if success:
                logger.info("Correo registrado correctamente")
            else:
                logger.error("Error registrando correo")
            
            return success
            
        except Exception as e:
            logger.error(f"Error registrando correo: {e}")
            return False
    
    def register_task_completion(self) -> bool:
        """
        Registra la finalización de la tarea BRASS usando la función común
        
        Returns:
            True si se registró correctamente
        """
        try:
            from common.utils import register_task_completion
            return register_task_completion(self.db_tareas, "BRASSDiario")
            
        except Exception as e:
            logger.error(f"Error registrando tarea: {e}")
            return False
    
    def execute_task(self, force: bool = False) -> bool:
        """
        Ejecuta la tarea principal del módulo BRASS
        
        Args:
            force: Si es True, ejecuta la tarea aunque ya se haya ejecutado hoy
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            logger.info("Iniciando tarea BRASS")
            
            # Verificar si ya se ejecutó hoy (solo si no es modo forzado)
            if not force and self.is_task_completed_today():
                logger.info("La tarea ya se ejecutó hoy")
                return True
            
            if force:
                logger.info("Ejecutando en modo forzado")
            
            # Obtener equipos fuera de calibración
            equipment_list = self.get_equipment_out_of_calibration()
            
            # Si no hay equipos fuera de calibración, solo registrar la tarea
            if not equipment_list:
                logger.info("No hay equipos fuera de calibración")
                return self.register_task_completion()
            
            # Generar reporte HTML
            html_report = self.generate_html_report(equipment_list)
            
            # Registrar correo
            subject = "Informe Equipos de Medida fuera de calibración (BRASS)"
            success = self.register_email(
                subject=subject,
                body=html_report,
                recipients=config.default_recipient
            )
            
            if success:
                # Registrar tarea como completada
                self.register_task_completion()
                logger.info("Tarea BRASS completada exitosamente")
                return True
            else:
                logger.error("Error en la ejecución de la tarea BRASS")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando tarea BRASS: {e}")
            return False
