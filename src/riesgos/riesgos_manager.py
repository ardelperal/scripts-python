"""
Módulo de gestión de riesgos.

Este módulo migra la funcionalidad del script VBScript GestionRiesgos.vbs
para gestionar tareas relacionadas con riesgos de proyectos.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..common.config import Config
from ..common.database import AccessDatabase
from ..common.utils import (
    format_date,
    get_admin_emails_string,
    get_technical_users,
    get_quality_users,
    get_user_email,
    get_technical_emails_string,
    get_quality_emails_string,
    register_email_in_database,
    register_task_completion
)


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
        self.db = AccessDatabase(config.get_db_riesgos_connection_string())
        
    def _formatear_fecha_access(self, fecha) -> str:
        """
        Formatea una fecha para uso en consultas SQL de Access
        Convierte fecha a formato #MM/dd/yyyy#
        """
        if isinstance(fecha, str):
            # Si ya es string, intentar parsearlo
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha, '%m/%d/%Y').date()
                except ValueError:
                    self.logger.error(f"Formato de fecha no reconocido: {fecha}")
                    return "#01/01/1900#"
        elif isinstance(fecha, datetime):
            fecha = fecha.date()
        elif hasattr(fecha, 'date'):
            fecha = fecha.date()
        
        # Formatear en formato Access #MM/dd/yyyy#
        return f"#{fecha.strftime('%m/%d/%Y')}#"
        
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
                SELECT FechaEjecucion 
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
        from datetime import datetime, timedelta
        
        # Calcular fecha límite (15 días desde hoy)
        fecha_hoy = datetime.now().date()
        fecha_limite = fecha_hoy + timedelta(days=15)
        fecha_limite_str = self._formatear_fecha_access(fecha_limite)
        fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
        
        return f"""
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
            AND TbProyectos.FechaMaxProximaPublicacion <= {fecha_limite_str}
            AND TbProyectos.FechaMaxProximaPublicacion > {fecha_hoy_str}
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
        from datetime import datetime
        
        # Calcular fecha actual
        fecha_hoy = datetime.now().date()
        fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
        
        return f"""
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
            AND TbRiesgosPlanMitigacionDetalle.FechaFinPrevista <= {fecha_hoy_str}
        """
    
    def _get_risks_contingency_actions_reschedule_query(self) -> str:
        """Consulta para riesgos con acciones de contingencia para replanificar."""
        from datetime import datetime
        
        # Calcular fecha actual
        fecha_hoy = datetime.now().date()
        fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
        
        return f"""
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
            AND TbRiesgosPlanContingenciaDetalle.FechaFinPrevista <= {fecha_hoy_str}
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
        Registra la ejecución de una tarea usando la función común.
        
        Args:
            task_type: Tipo de tarea ejecutada
            
        Returns:
            True si se registró correctamente, False en caso contrario
        """
        try:
            from common.utils import register_task_completion
            
            # Mapear tipos de tarea a nombres estándar
            task_names = {
                'TECNICA': 'RiesgosTecnica',
                'CALIDAD': 'RiesgosCalidad', 
                'CALIDADMENSUAL': 'RiesgosCalidadMensual'
            }
            
            task_name = task_names.get(task_type, f'Riesgos{task_type}')
            return register_task_completion(self.db, task_name)
            
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
                
                # Registrar notificación de resumen en BD
                admin_emails = get_admin_emails_string(self.db)
                if admin_emails:
                    subject = "Resumen de ejecución - Gestión de Riesgos"
                    body = f"""
                    Se han ejecutado las siguientes tareas de gestión de riesgos:
                    
                    {chr(10).join(['- ' + task for task in executed_tasks])}
                    
                    Fecha de ejecución: {format_date(datetime.now())}
                    """
                    
                    # Obtener conexión a BD de tareas para registrar correo
                    from ..common.database import AccessDatabase
                    db_tareas = AccessDatabase(self.config.get_db_tareas_connection_string())
                    register_email_in_database(db_tareas, "Riesgos", subject, body, admin_emails)
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
            
            # Obtener conexión a BD de tareas para registrar correos
            from ..common.database import AccessDatabase
            db_tareas = AccessDatabase(self.config.get_db_tareas_connection_string())
            
            for user_id, (name, email) in users.items():
                if email:
                    html_content = self._generate_technical_report_html(user_id, name)
                    
                    subject = f"Informe Semanal de Riesgos - {name}"
                    
                    # Registrar correo en BD en lugar de enviarlo
                    register_email_in_database(db_tareas, "Riesgos", subject, html_content, email)
                    
                    self.logger.info(f"Registrado informe técnico para {name} ({email})")
            
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
            
            # Registrar correo en BD en lugar de enviarlo
            admin_emails = get_admin_emails_string(self.db)
            if admin_emails:
                subject = "Informe Semanal de Calidad - Gestión de Riesgos"
                
                # Obtener conexión a BD de tareas para registrar correo
                from ..common.database import AccessDatabase
                db_tareas = AccessDatabase(self.config.get_db_tareas_connection_string())
                register_email_in_database(db_tareas, "Riesgos", subject, html_content, admin_emails)
                
                self.logger.info("Registrado informe de calidad para administradores")
            
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
            
            # Registrar correo en BD en lugar de enviarlo
            admin_emails = get_admin_emails_string(self.db)
            if admin_emails:
                subject = "Informe Mensual de Calidad - Gestión de Riesgos"
                
                # Obtener conexión a BD de tareas para registrar correo
                from ..common.database import AccessDatabase
                db_tareas = AccessDatabase(self.config.get_db_tareas_connection_string())
                register_email_in_database(db_tareas, "Riesgos", subject, html_content, admin_emails)
                
                self.logger.info("Registrado informe de calidad mensual para administradores")
            
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
            ("Ediciones con propuestas de publicación rechazadas", self._get_editions_with_rejected_proposals_data(user_id)),
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
        html = ""
        
        # Obtener datos de ediciones a punto de caducar
        editions_about_to_expire = self._get_editions_about_to_expire()
        if editions_about_to_expire:
            html += self._generate_editions_table_html(
                "EDICIONES CON FECHA DE PUBLICACIÓN A PUNTO DE SER SUPERADA",
                editions_about_to_expire
            )
        
        # Obtener datos de ediciones caducadas
        expired_editions = self._get_expired_editions()
        if expired_editions:
            html += self._generate_editions_table_html(
                "EDICIONES CON FECHA DE PUBLICACIÓN SUPERADA",
                expired_editions
            )
        
        # Obtener datos de riesgos para retipificar
        risks_to_reclassify = self._get_risks_to_reclassify()
        if risks_to_reclassify:
            html += self._generate_risks_table_html(
                "RIESGOS PARA RETIPIFICAR",
                risks_to_reclassify
            )
        
        return html if html else "<div class='section'><h3>Métricas de Calidad</h3><p>No hay elementos para mostrar.</p></div>"
    
    def _generate_monthly_metrics_html(self) -> str:
        """Genera métricas de calidad mensuales."""
        html = ""
        
        # Obtener datos de ediciones preparadas para publicar
        editions_ready = self._get_editions_ready_for_publication()
        if editions_ready:
            html += self._generate_editions_ready_table_html(
                "EDICIONES PREPARADAS PARA PUBLICAR",
                editions_ready
            )
        
        # Obtener datos de riesgos aceptados por visar
        accepted_risks = self._get_accepted_risks_pending_review()
        if accepted_risks:
            html += self._generate_risks_table_html(
                "RIESGOS ACEPTADOS POR EL TÉCNICO A FALTA DE VISADO POR CALIDAD",
                accepted_risks
            )
        
        # Obtener datos de riesgos retirados por visar
        retired_risks = self._get_retired_risks_pending_review()
        if retired_risks:
            html += self._generate_risks_table_html(
                "RIESGOS RETIRADOS POR EL TÉCNICO A FALTA DE VISADO POR CALIDAD",
                retired_risks
            )
        
        return html if html else "<div class='section'><h3>Métricas Mensuales</h3><p>No hay elementos para mostrar.</p></div>"
    
    # Métodos para obtener datos específicos
    def _get_editions_need_publication_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de ediciones que necesitan propuesta de publicación."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbProyectosEdiciones.Edicion, TbProyectosEdiciones.IDEdicion,
                   TbProyectosEdiciones.FechaMaxProximaPublicacion, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad,
                   TbProyectosEdiciones.FechaPreparadaParaPublicar, 
                   DateDiff('d', Now(), TbProyectosEdiciones.FechaMaxProximaPublicacion) AS Dias
            FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                  INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                  INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
              AND TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND DateDiff('d', Now(), TbProyectosEdiciones.FechaMaxProximaPublicacion) <= 15
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NULL
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo ediciones que necesitan propuesta de publicación: {e}")
            return []
    
    def _get_editions_with_rejected_proposals_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de ediciones con propuestas rechazadas."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbProyectosEdiciones.Edicion, TbProyectosEdiciones.IDEdicion,
                   TbProyectosEdiciones.FechaMaxProximaPublicacion, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad,
                   TbProyectosEdiciones.FechaPreparadaParaPublicar, TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha,
                   TbProyectosEdiciones.PropuestaRechazadaPorCalidadMotivo
            FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                  INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                  INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
              AND TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NOT NULL
              AND TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NOT NULL
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo ediciones con propuestas rechazadas: {e}")
            return []
    
    def _get_accepted_risks_unmotivated_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos aceptados no motivados."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion,
                   TbRiesgos.CausaRaiz, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                  INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                  INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                  ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.Mitigacion = 'Aceptar'
              AND TbRiesgos.FechaJustificacionAceptacionRiesgo IS NULL
              AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo riesgos aceptados no motivados: {e}")
            return []
    
    def _get_accepted_risks_rejected_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos aceptados rechazados."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion,
                   TbRiesgos.CausaRaiz, TbRiesgos.FechaRechazoAceptacionPorCalidad, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                  INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                  INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                  ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.Mitigacion = 'Aceptar'
              AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
              AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NOT NULL
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo riesgos aceptados rechazados: {e}")
            return []
    
    def _get_retired_risks_unmotivated_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos retirados no motivados."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion,
                   TbRiesgos.CausaRaiz, TbRiesgos.FechaRetirado, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                  INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                  INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                  ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.Mitigacion = 'Retirar'
              AND TbRiesgos.FechaJustificacionRetiroRiesgo IS NULL
              AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo riesgos retirados no motivados: {e}")
            return []
    
    def _get_retired_risks_rejected_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de riesgos retirados rechazados."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion,
                   TbRiesgos.CausaRaiz, TbRiesgos.FechaRetirado, TbRiesgos.FechaRechazoRetiroPorCalidad,
                   TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                  INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                  INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                  INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                  ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbRiesgos.Mitigacion = 'Retirar'
              AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
              AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NOT NULL
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo riesgos retirados rechazados: {e}")
            return []
    
    def _get_mitigation_actions_reschedule_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de acciones de mitigación para replanificar."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion,
                   TbRiesgos.CausaRaiz, TbAccionesMitigacion.FechaFinalizacion, TbAccionesMitigacion.Descripcion AS AccionDescripcion,
                   TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                   INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                   INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                   INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                   ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                  INNER JOIN TbAccionesMitigacion ON TbRiesgos.IDRiesgo = TbAccionesMitigacion.IDRiesgo)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbAccionesMitigacion.FechaFinalizacion < Now()
              AND TbAccionesMitigacion.FechaRealFinalizacion IS NULL
              AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo acciones de mitigación para replanificar: {e}")
            return []
    
    def _get_contingency_actions_reschedule_data(self, user_id: str) -> List[Dict]:
        """Obtiene datos de acciones de contingencia para replanificar."""
        try:
            query = f"""
            SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion,
                   TbRiesgos.CausaRaiz, TbAccionesContingencia.FechaFinalizacion, TbAccionesContingencia.Descripcion AS AccionDescripcion,
                   TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                   INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                   INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                   INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                   ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                  INNER JOIN TbAccionesContingencia ON TbRiesgos.IDRiesgo = TbAccionesContingencia.IDRiesgo)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
              AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
              AND TbUsuariosAplicaciones.FechaBaja IS NULL
              AND TbAccionesContingencia.FechaFinalizacion < Now()
              AND TbAccionesContingencia.FechaRealFinalizacion IS NULL
              AND TbUsuariosAplicaciones.UsuarioRed = '{user_id}'
            """
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo acciones de contingencia para replanificar: {e}")
            return []
    
    # Métodos auxiliares para métricas de calidad
    def _get_editions_about_to_expire(self) -> List[Dict]:
        """Obtiene ediciones a punto de caducar (próximos 15 días)."""
        try:
            from datetime import datetime, timedelta
            
            # Calcular fechas límite
            fecha_hoy = datetime.now().date()
            fecha_limite = fecha_hoy + timedelta(days=15)
            fecha_limite_str = self._formatear_fecha_access(fecha_limite)
            fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
            
            query = f"""
            SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,
                   TbProyectos.FechaPrevistaCierre, TbProyectosEdiciones.IDEdicion,
                   TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion,
                   TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad
            FROM TbProyectos INNER JOIN TbProyectosEdiciones 
                 ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbProyectosEdiciones.FechaMaxProximaPublicacion <= {fecha_limite_str}
              AND TbProyectosEdiciones.FechaMaxProximaPublicacion > {fecha_hoy_str}
            """
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_expired_editions(self) -> List[Dict]:
        """Obtiene ediciones con fecha de publicación superada."""
        try:
            from datetime import datetime
            
            # Calcular fecha actual
            fecha_hoy = datetime.now().date()
            fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
            
            query = f"""
            SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,
                   TbProyectos.FechaPrevistaCierre, TbProyectosEdiciones.IDEdicion,
                   TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion,
                   TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad
            FROM TbProyectos INNER JOIN TbProyectosEdiciones 
                 ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            WHERE TbProyectos.ParaInformeAvisos <> 'No'
              AND TbProyectos.FechaCierre IS NULL
              AND TbProyectosEdiciones.FechaPublicacion IS NULL
              AND TbProyectosEdiciones.FechaMaxProximaPublicacion < {fecha_hoy_str}
            """
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_risks_to_reclassify(self) -> List[Dict]:
        """Obtiene riesgos que necesitan retipificación."""
        try:
            query = """
            SELECT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.DescripcionRiesgo,
                   TbRiesgos.TipoRiesgo, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad,
                   TbRiesgos.FechaRiesgoParaRetipificar
            FROM (TbExpedientes1 INNER JOIN TbRiesgos ON TbExpedientes1.IDExpediente = TbRiesgos.IDExpediente)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 
                 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbRiesgos.FechaRiesgoParaRetipificar IS NOT NULL
              AND TbRiesgos.FechaRetipificacionRiesgo IS NULL
            """
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_editions_ready_for_publication(self) -> List[Dict]:
        """Obtiene ediciones preparadas para publicar."""
        try:
            query = """
            SELECT TbExpedientes1.Nemotecnico, TbProyectos.NombreProyecto, TbProyectos.Juridica,
                   TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion,
                   TbUsuariosAplicaciones.Nombre AS NombreUsuarioCalidad
            FROM ((TbExpedientes1 INNER JOIN TbProyectos ON TbExpedientes1.IDProyecto = TbProyectos.IDProyecto)
                  INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto)
                 LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones.Id
            WHERE TbProyectosEdiciones.PropuestaPublicacionFecha IS NOT NULL
              AND TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NULL
            """
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_accepted_risks_pending_review(self) -> List[Dict]:
        """Obtiene riesgos aceptados pendientes de visado por calidad."""
        try:
            query = """
            SELECT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.DescripcionRiesgo,
                   TbRiesgos.JustificacionAceptacionRiesgo, TbRiesgos.FechaJustificacionAceptacionRiesgo,
                   TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM (TbExpedientes1 INNER JOIN TbRiesgos ON TbExpedientes1.IDExpediente = TbRiesgos.IDExpediente)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 
                 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbRiesgos.FechaJustificacionAceptacionRiesgo IS NOT NULL
              AND TbRiesgos.FechaAprobacionAceptacionPorCalidad IS NULL
              AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NULL
            """
            return self.db.execute_query(query)
        except:
            return []
    
    def _get_retired_risks_pending_review(self) -> List[Dict]:
        """Obtiene riesgos retirados pendientes de visado por calidad."""
        try:
            query = """
            SELECT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.DescripcionRiesgo,
                   TbRiesgos.CausaRaiz, TbRiesgos.FechaJustificacionRetiroRiesgo,
                   TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
            FROM (TbExpedientes1 INNER JOIN TbRiesgos ON TbExpedientes1.IDExpediente = TbRiesgos.IDExpediente)
                 LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 
                 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
            WHERE TbRiesgos.FechaJustificacionRetiroRiesgo IS NOT NULL
              AND TbRiesgos.FechaAprobacionRetiroPorCalidad IS NULL
              AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NULL
            """
            return self.db.execute_query(query)
        except:
            return []
    
    def _generate_editions_table_html(self, title: str, data: List[Dict]) -> str:
        """Genera tabla HTML para ediciones."""
        if not data:
            return ""
        
        html = f"""
        <div class="section">
            <h3>{title}</h3>
            <p class="count">Total: {len(data)} elementos</p>
            <table>
                <thead>
                    <tr>
                        <th>Proyecto</th>
                        <th>Nombre</th>
                        <th>Jurídica</th>
                        <th>Últ Ed.</th>
                        <th>Fecha Últ Ed.</th>
                        <th>Fecha Prevista Cierre</th>
                        <th>Fecha Máx.Próx Ed.</th>
                        <th>Días</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in data:
            html += "<tr>"
            html += f"<td>{row.get('Proyecto', '')}</td>"
            html += f"<td>{row.get('NombreProyecto', '')}</td>"
            html += f"<td>{row.get('Juridica', '')}</td>"
            html += f"<td>{row.get('Edicion', '')}</td>"
            html += f"<td>{format_date(row.get('FechaEdicion')) if row.get('FechaEdicion') else ''}</td>"
            html += f"<td>{format_date(row.get('FechaPrevistaCierre')) if row.get('FechaPrevistaCierre') else ''}</td>"
            html += f"<td>{format_date(row.get('FechaMaxProximaPublicacion')) if row.get('FechaMaxProximaPublicacion') else ''}</td>"
            html += f"<td>{row.get('Dias', '')}</td>"
            html += f"<td>{row.get('NombreUsuarioCalidad', '')}</td>"
            html += "</tr>"
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _generate_editions_ready_table_html(self, title: str, data: List[Dict]) -> str:
        """Genera tabla HTML para ediciones preparadas para publicar."""
        if not data:
            return ""
        
        html = f"""
        <div class="section">
            <h3>{title}</h3>
            <p class="count">Total: {len(data)} elementos</p>
            <table>
                <thead>
                    <tr>
                        <th>Nemotécnico</th>
                        <th>Nombre Proyecto</th>
                        <th>Jurídica</th>
                        <th>Edición</th>
                        <th>Fecha Edición</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in data:
            html += "<tr>"
            html += f"<td>{row.get('Nemotecnico', '')}</td>"
            html += f"<td>{row.get('NombreProyecto', '')}</td>"
            html += f"<td>{row.get('Juridica', '')}</td>"
            html += f"<td>{row.get('Edicion', '')}</td>"
            html += f"<td>{format_date(row.get('FechaEdicion')) if row.get('FechaEdicion') else ''}</td>"
            html += f"<td>{row.get('NombreUsuarioCalidad', '')}</td>"
            html += "</tr>"
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _generate_risks_table_html(self, title: str, data: List[Dict]) -> str:
        """Genera tabla HTML para riesgos."""
        if not data:
            return ""
        
        html = f"""
        <div class="section">
            <h3>{title}</h3>
            <p class="count">Total: {len(data)} elementos</p>
            <table>
                <thead>
                    <tr>
                        <th>ID Riesgo</th>
                        <th>Nemotécnico</th>
                        <th>Descripción</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in data:
            html += "<tr>"
            html += f"<td>{row.get('IDRiesgo', '')}</td>"
            html += f"<td>{row.get('Nemotecnico', '')}</td>"
            html += f"<td>{row.get('DescripcionRiesgo', '')}</td>"
            html += f"<td>{row.get('UsuarioCalidad', '')}</td>"
            html += "</tr>"
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html