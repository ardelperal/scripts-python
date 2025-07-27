"""
Módulo de gestión de riesgos.

Este módulo migra la funcionalidad del script VBScript GestionRiesgos.vbs
para gestionar tareas relacionadas con riesgos de proyectos.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..common.config import Config
from ..common.database import AccessDatabase
from ..common.utils import format_date, send_notification_email, get_admin_emails_string


class RiesgosManager:
    """
    Gestor de riesgos que maneja las tareas técnicas y de calidad.
    
    Funcionalidades principales:
    - Tareas técnicas semanales para jefes de proyecto
    - Tareas de calidad semanales
    - Tareas de calidad mensuales
    - Generación de reportes HTML
    - Envío automático de correos
    """
    
    def __init__(self, config: Config):
        """
        Inicializa el gestor de riesgos.
        
        Args:
            config: Configuración de la aplicación
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db = AccessDatabase(config.database_path)
        
    def connect(self) -> bool:
        """
        Establece conexión con la base de datos.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            return self.db.connect()
        except Exception as e:
            self.logger.error(f"Error conectando a la base de datos: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos."""
        self.db.disconnect()
    
    def get_last_execution(self, task_type: str) -> Optional[datetime]:
        """
        Obtiene la fecha de la última ejecución de una tarea.
        
        Args:
            task_type: Tipo de tarea ('TECNICA', 'CALIDAD', 'CALIDADMENSUAL')
            
        Returns:
            Fecha de última ejecución o None si no existe
        """
        try:
            query = """
                SELECT TOP 1 FechaEjecucion 
                FROM TbTareasEjecutadas 
                WHERE TipoTarea = ? 
                ORDER BY FechaEjecucion DESC
            """
            result = self.db.execute_query(query, [task_type])
            
            if result and len(result) > 0:
                return result[0]['FechaEjecucion']
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo última ejecución para {task_type}: {e}")
            return None
    
    def should_execute_technical_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea técnica.
        
        Returns:
            True si debe ejecutarse, False en caso contrario
        """
        try:
            last_execution = self.get_last_execution('TECNICA')
            
            if last_execution is None:
                return True
            
            # Ejecutar si han pasado más de 7 días
            days_since_last = (datetime.now() - last_execution).days
            return days_since_last >= 7
            
        except Exception as e:
            self.logger.error(f"Error verificando tarea técnica: {e}")
            return False
    
    def should_execute_quality_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea de calidad.
        
        Returns:
            True si debe ejecutarse, False en caso contrario
        """
        try:
            last_execution = self.get_last_execution('CALIDAD')
            
            if last_execution is None:
                return True
            
            # Ejecutar si han pasado más de 7 días
            days_since_last = (datetime.now() - last_execution).days
            return days_since_last >= 7
            
        except Exception as e:
            self.logger.error(f"Error verificando tarea de calidad: {e}")
            return False
    
    def should_execute_monthly_quality_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea de calidad mensual.
        
        Returns:
            True si debe ejecutarse, False en caso contrario
        """
        try:
            last_execution = self.get_last_execution('CALIDADMENSUAL')
            
            if last_execution is None:
                return True
            
            # Ejecutar si han pasado más de 30 días
            days_since_last = (datetime.now() - last_execution).days
            return days_since_last >= 30
            
        except Exception as e:
            self.logger.error(f"Error verificando tarea de calidad mensual: {e}")
            return False
    
    def get_distinct_users(self) -> Dict[str, Tuple[str, str]]:
        """
        Obtiene usuarios distintos que requieren notificaciones.
        
        Returns:
            Diccionario con usuario_red como clave y (nombre, correo) como valor
        """
        users = {}
        
        # Lista de consultas para diferentes tipos de riesgos
        queries = [
            self._get_editions_need_publication_proposal_query(),
            self._get_editions_with_rejected_proposals_query(),
            self._get_accepted_risks_unmotivated_query(),
            self._get_accepted_risks_rejected_query(),
            self._get_retired_risks_unmotivated_query(),
            self._get_retired_risks_rejected_query(),
            self._get_risks_mitigation_actions_reschedule_query(),
            self._get_risks_contingency_actions_reschedule_query()
        ]
        
        for query in queries:
            try:
                results = self.db.execute_query(query)
                for row in results:
                    user_id = row['UsuarioRed']
                    if user_id not in users:
                        users[user_id] = (row['Nombre'], row['CorreoUsuario'])
            except Exception as e:
                self.logger.error(f"Error ejecutando consulta de usuarios: {e}")
        
        return users
    
    def _get_editions_need_publication_proposal_query(self) -> str:
        """Consulta para ediciones que necesitan propuesta de publicación."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND DATEDIFF('d', NOW(), TbProyectos.FechaMaxProximaPublicacion) <= 15
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NULL
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
        """
    
    def _get_editions_with_rejected_proposals_query(self) -> str:
        """Consulta para ediciones con propuestas de publicación rechazadas."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NOT NULL
            AND TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NOT NULL
        """
    
    def _get_accepted_risks_unmotivated_query(self) -> str:
        """Consulta para riesgos aceptados no motivados."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbRiesgos.FechaRetirado IS NOT NULL
            AND TbRiesgos.JustificacionRetiroRiesgo IS NULL
        """
    
    def _get_accepted_risks_rejected_query(self) -> str:
        """Consulta para riesgos aceptados rechazados."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbRiesgos.Mitigacion = 'Aceptar'
            AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NOT NULL
        """
    
    def _get_retired_risks_unmotivated_query(self) -> str:
        """Consulta para riesgos retirados no motivados."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbRiesgos.FechaRetirado IS NOT NULL
            AND TbRiesgos.JustificacionRetiroRiesgo IS NULL
        """
    
    def _get_retired_risks_rejected_query(self) -> str:
        """Consulta para riesgos retirados rechazados."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbRiesgos.FechaRetirado IS NOT NULL
            AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NOT NULL
        """
    
    def _get_risks_mitigation_actions_reschedule_query(self) -> str:
        """Consulta para riesgos con acciones de mitigación para replanificar."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanMitigacionPpal
            ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) INNER JOIN TbRiesgosPlanMitigacionDetalle
            ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbRiesgos.FechaRetirado IS NULL
            AND TbRiesgos.Mitigacion <> 'Aceptar'
            AND TbRiesgosPlanMitigacionDetalle.FechaFinReal IS NULL
            AND TbRiesgosPlanMitigacionDetalle.FechaFinPrevista <= DATE()
        """
    
    def _get_risks_contingency_actions_reschedule_query(self) -> str:
        """Consulta para riesgos con acciones de contingencia para replanificar."""
        return """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, 
                   TbUsuariosAplicaciones.Nombre, 
                   TbUsuariosAplicaciones.CorreoUsuario
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanContingenciaPpal
            ON TbRiesgos.IDRiesgo = TbRiesgosPlanContingenciaPpal.IDRiesgo) INNER JOIN TbRiesgosPlanContingenciaDetalle
            ON TbRiesgosPlanContingenciaPpal.IDContingencia = TbRiesgosPlanContingenciaDetalle.IDContingencia
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
            AND TbProyectos.FechaCierre IS NULL
            AND TbProyectosEdiciones.FechaPublicacion IS NULL
            AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
            AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            AND TbUsuariosAplicaciones.FechaBaja IS NULL
            AND TbRiesgos.FechaRetirado IS NULL
            AND TbRiesgos.Mitigacion <> 'Aceptar'
            AND TbRiesgosPlanContingenciaDetalle.FechaFinReal IS NULL
            AND TbRiesgosPlanContingenciaDetalle.FechaFinPrevista <= DATE()
        """
    
    def get_css_styles(self) -> str:
        """
        Obtiene los estilos CSS para los reportes HTML.
        
        Returns:
            String con los estilos CSS
        """
        return """
        <style type="text/css">
        body { font-family: Arial, sans-serif; font-size: 12px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        .header { background-color: #4CAF50; color: white; padding: 10px; text-align: center; }
        .section { margin-bottom: 30px; }
        .count { font-weight: bold; color: #d9534f; }
        </style>
        """
    
    def record_task_execution(self, task_type: str) -> bool:
        """
        Registra la ejecución de una tarea.
        
        Args:
            task_type: Tipo de tarea ejecutada
            
        Returns:
            True si se registró correctamente, False en caso contrario
        """
        try:
            query = """
                INSERT INTO TbTareasEjecutadas (TipoTarea, FechaEjecucion)
                VALUES (?, ?)
            """
            self.db.execute_query(query, [task_type, datetime.now()])
            return True
            
        except Exception as e:
            self.logger.error(f"Error registrando ejecución de tarea {task_type}: {e}")
            return False
    
    def execute_daily_task(self) -> bool:
        """
        Ejecuta las tareas diarias de gestión de riesgos.
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            if not self.connect():
                self.logger.error("No se pudo conectar a la base de datos")
                return False
            
            executed_tasks = []
            
            # Verificar y ejecutar tarea técnica
            if self.should_execute_technical_task():
                if self.execute_technical_task():
                    executed_tasks.append("Tarea técnica")
                    self.record_task_execution('TECNICA')
            
            # Verificar y ejecutar tarea de calidad
            if self.should_execute_quality_task():
                if self.execute_quality_task():
                    executed_tasks.append("Tarea de calidad")
                    self.record_task_execution('CALIDAD')
            
            # Verificar y ejecutar tarea de calidad mensual
            if self.should_execute_monthly_quality_task():
                if self.execute_monthly_quality_task():
                    executed_tasks.append("Tarea de calidad mensual")
                    self.record_task_execution('CALIDADMENSUAL')
            
            if executed_tasks:
                self.logger.info(f"Tareas ejecutadas: {', '.join(executed_tasks)}")
                
                # Enviar notificación de resumen
                admin_emails = get_admin_emails_string()
                if admin_emails:
                    subject = "Resumen de ejecución - Gestión de Riesgos"
                    body = f"""
                    Se han ejecutado las siguientes tareas de gestión de riesgos:
                    
                    {chr(10).join(['- ' + task for task in executed_tasks])}
                    
                    Fecha de ejecución: {format_date(datetime.now())}
                    """
                    
                    send_notification_email(admin_emails, subject, body)
            else:
                self.logger.info("No hay tareas pendientes de ejecución")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tareas diarias: {e}")
            return False
        finally:
            self.disconnect()
    
    def execute_technical_task(self) -> bool:
        """
        Ejecuta la tarea técnica semanal.
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            self.logger.info("Ejecutando tarea técnica semanal")
            
            # Obtener usuarios distintos que requieren notificaciones
            users = self.get_distinct_users()
            
            for user_id, (name, email) in users.items():
                if email:
                    html_content = self._generate_technical_report_html(user_id, name)
                    
                    subject = f"Informe Semanal de Riesgos - {name}"
                    
                    send_notification_email(
                        email,
                        subject,
                        html_content,
                        is_html=True
                    )
                    
                    self.logger.info(f"Enviado informe técnico a {name} ({email})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea técnica: {e}")
            return False
    
    def execute_quality_task(self) -> bool:
        """
        Ejecuta la tarea de calidad semanal.
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            self.logger.info("Ejecutando tarea de calidad semanal")
            
            # Generar reporte de calidad
            html_content = self._generate_quality_report_html()
            
            # Enviar a administradores
            admin_emails = get_admin_emails_string()
            if admin_emails:
                subject = "Informe Semanal de Calidad - Gestión de Riesgos"
                
                send_notification_email(
                    admin_emails,
                    subject,
                    html_content,
                    is_html=True
                )
                
                self.logger.info("Enviado informe de calidad a administradores")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea de calidad: {e}")
            return False
    
    def execute_monthly_quality_task(self) -> bool:
        """
        Ejecuta la tarea de calidad mensual.
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            self.logger.info("Ejecutando tarea de calidad mensual")
            
            # Generar reporte de calidad mensual
            html_content = self._generate_monthly_quality_report_html()
            
            # Enviar a administradores
            admin_emails = get_admin_emails_string()
            if admin_emails:
                subject = "Informe Mensual de Calidad - Gestión de Riesgos"
                
                send_notification_email(
                    admin_emails,
                    subject,
                    html_content,
                    is_html=True
                )
                
                self.logger.info("Enviado informe de calidad mensual a administradores")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea de calidad mensual: {e}")
            return False
    
    def _generate_technical_report_html(self, user_id: str, user_name: str) -> str:
        """
        Genera el reporte HTML técnico para un usuario específico.
        
        Args:
            user_id: ID del usuario
            user_name: Nombre del usuario
            
        Returns:
            Contenido HTML del reporte
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Informe Técnico de Riesgos - {user_name}</title>
            {self.get_css_styles()}
        </head>
        <body>
            <div class="header">
                <h1>Informe Técnico de Riesgos</h1>
                <h2>{user_name}</h2>
                <p>Fecha: {format_date(datetime.now())}</p>
            </div>
        """
        
        # Agregar secciones del reporte
        sections = [
            ("Ediciones que necesitan propuesta de publicación", self._get_editions_need_publication_data(user_id)),
            ("Ediciones con propuestas de publicación rechazadas", self._get_editions_rejected_proposals_data(user_id)),
            ("Riesgos aceptados no motivados", self._get_accepted_risks_unmotivated_data(user_id)),
            ("Riesgos aceptados rechazados", self._get_accepted_risks_rejected_data(user_id)),
            ("Riesgos retirados no motivados", self._get_retired_risks_unmotivated_data(user_id)),
            ("Riesgos retirados rechazados", self._get_retired_risks_rejected_data(user_id)),
            ("Riesgos con acciones de mitigación para replanificar", self._get_mitigation_actions_reschedule_data(user_id)),
            ("Riesgos con acciones de contingencia para replanificar", self._get_contingency_actions_reschedule_data(user_id))
        ]
        
        for title, data in sections:
            html += self._generate_section_html(title, data)
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_quality_report_html(self) -> str:
        """
        Genera el reporte HTML de calidad semanal.
        
        Returns:
            Contenido HTML del reporte
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Informe Semanal de Calidad - Gestión de Riesgos</title>
            {self.get_css_styles()}
        </head>
        <body>
            <div class="header">
                <h1>Informe Semanal de Calidad</h1>
                <h2>Gestión de Riesgos</h2>
                <p>Fecha: {format_date(datetime.now())}</p>
            </div>
        """
        
        # Agregar métricas de calidad
        html += self._generate_quality_metrics_html()
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_monthly_quality_report_html(self) -> str:
        """
        Genera el reporte HTML de calidad mensual.
        
        Returns:
            Contenido HTML del reporte
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Informe Mensual de Calidad - Gestión de Riesgos</title>
            {self.get_css_styles()}
        </head>
        <body>
            <div class="header">
                <h1>Informe Mensual de Calidad</h1>
                <h2>Gestión de Riesgos</h2>
                <p>Fecha: {format_date(datetime.now())}</p>
            </div>
        """
        
        # Agregar métricas mensuales
        html += self._generate_monthly_metrics_html()
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_section_html(self, title: str, data: List[Dict]) -> str:
        """
        Genera HTML para una sección del reporte.
        
        Args:
            title: Título de la sección
            data: Datos de la sección
            
        Returns:
            HTML de la sección
        """
        html = f"""
        <div class="section">
            <h3>{title}</h3>
            <p class="count">Total: {len(data)} elementos</p>
        """
        
        if data:
            # Obtener columnas de la primera fila
            columns = list(data[0].keys())
            
            html += "<table><thead><tr>"
            for col in columns:
                html += f"<th>{col}</th>"
            html += "</tr></thead><tbody>"
            
            for row in data:
                html += "<tr>"
                for col in columns:
                    value = row.get(col, '')
                    if isinstance(value, datetime):
                        value = format_date(value)
                    html += f"<td>{value}</td>"
                html += "</tr>"
            
            html += "</tbody></table>"
        else:
            html += "<p>No hay elementos para mostrar.</p>"
        
        html += "</div>"
        return html
    
    def _generate_quality_metrics_html(self) -> str:
        """Genera métricas de calidad semanales."""
        # Implementar métricas específicas de calidad
        return "<div class='section'><h3>Métricas de Calidad</h3><p>Implementar métricas específicas</p></div>"
    
    def _generate_monthly_metrics_html(self) -> str:
        """Genera métricas de calidad mensuales."""
        # Implementar métricas específicas mensuales
        return "<div class='section'><h3>Métricas Mensuales</h3><p>Implementar métricas específicas</p></div>"
    
    # Métodos para obtener datos específicos (implementar según necesidades)
    def _get_editions_need_publication_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de ediciones que necesitan propuesta de publicación."""
        try:
            query = self._get_editions_need_publication_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_editions_rejected_proposals_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de ediciones con propuestas rechazadas."""
        try:
            query = self._get_editions_with_rejected_proposals_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_accepted_risks_unmotivated_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos aceptados no motivados."""
        try:
            query = self._get_accepted_risks_unmotivated_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_accepted_risks_rejected_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos aceptados rechazados."""
        try:
            query = self._get_accepted_risks_rejected_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_retired_risks_unmotivated_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos retirados no motivados."""
        try:
            query = self._get_retired_risks_unmotivated_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_retired_risks_rejected_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos retirados rechazados."""
        try:
            query = self._get_retired_risks_rejected_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_mitigation_actions_reschedule_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de acciones de mitigación para replanificar."""
        try:
            query = self._get_risks_mitigation_actions_reschedule_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_contingency_actions_reschedule_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de acciones de contingencia para replanificar."""
        try:
            query = self._get_risks_contingency_actions_reschedule_query() + f" AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'"
            return self.db.execute_query(query)
        except:
            return []