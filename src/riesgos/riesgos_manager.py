"""
Módulo de Gestión de Riesgos

Este módulo implementa la lógica de negocio para el proceso automatizado de Gestión de Riesgos.
Su función es supervisar digitalmente el sistema de Gestión de Riesgos, asegurando que las tareas,
revisiones y plazos clave no se pasen por alto.

Audiencias y frecuencia:
- Técnicos: Informe semanal personalizado con tareas bajo su responsabilidad
- Equipo de Calidad: Informe semanal detallado + informe mensual de alto nivel
"""

import logging
import json
import traceback
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ..common.database import AccessDatabase
from ..common.utils import (
    format_date, get_technical_users, get_quality_users, get_admin_users,
    register_email_in_database, register_task_completion, load_css_content,
    generate_html_header, get_technical_emails_string, get_quality_emails_string,
    get_admin_emails_string
)
from .table_configurations import TABLE_CONFIGURATIONS


class RiesgosManager:
    """
    Gestor principal del módulo de Gestión de Riesgos.
    
    Implementa la lógica de negocio para:
    - Informes técnicos semanales personalizados
    - Informes de calidad semanales detallados
    - Informes de calidad mensuales de alto nivel
    """
    
    def __init__(self, config, logger: logging.Logger):
        """
        Inicializa el gestor de riesgos.
        
        Args:
            config: Configuración de la aplicación
            logger: Logger para registrar eventos
        """
        self.config = config
        self.logger = logger
        self.db = None
        self.db_tareas = None
        # Usar ruta absoluta basada en el directorio del proyecto
        project_root = Path(__file__).parent.parent.parent
        self.error_log_file = project_root / "logs" / "riesgos_sql_errors.json"
        self._ensure_error_log_directory()
        
        # Cache para usuarios
        self._technical_users = None
        self._quality_users = None
        self._admin_users = None
        
        # Contadores de errores para hacer más visible cuando ocurren problemas
        self.error_count = 0
        self.warning_count = 0
        
    def _ensure_error_log_directory(self):
        """Asegura que el directorio de logs existe."""
        self.error_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _log_sql_error(self, query: str, error: Exception, context: str = ""):
        """
        Registra errores SQL en un archivo JSON para análisis posterior.
        
        Args:
            query: La consulta SQL que causó el error
            error: La excepción que se produjo
            context: Contexto adicional sobre dónde ocurrió el error
        """
        try:
            # Incrementar contador de errores
            self.error_count += 1
            
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "query": query,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            }
            
            # Leer errores existentes
            existing_errors = []
            if self.error_log_file.exists():
                try:
                    with open(self.error_log_file, 'r', encoding='utf-8') as f:
                        existing_errors = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing_errors = []
            
            # Agregar nuevo error
            existing_errors.append(error_entry)
            
            # Mantener solo los últimos 100 errores
            if len(existing_errors) > 100:
                existing_errors = existing_errors[-100:]
            
            # Guardar errores actualizados
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_errors, f, indent=2, ensure_ascii=False)
            
            # Hacer más visible el error en los logs
            self.logger.error(f"🚨 ERROR SQL #{self.error_count} - {context}")
            self.logger.error(f"   Tipo: {type(error).__name__}")
            self.logger.error(f"   Mensaje: {str(error)}")
            self.logger.error(f"   Archivo de errores: {self.error_log_file}")
            
        except Exception as log_error:
            self.logger.error(f"Error al registrar error SQL: {log_error}")
    
    def _execute_query_with_error_logging(self, query: str, params=None, context: str = ""):
        """
        Ejecuta una consulta SQL con logging automático de errores.
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            context: Contexto de la consulta para el logging
            
        Returns:
            Resultado de la consulta o None si hay error
        """
        try:
            if params:
                result = self.db.execute_query(query, params)
            else:
                result = self.db.execute_query(query)
            return result
        except Exception as e:
            self._log_sql_error(query, e, context)
            raise
        
    def connect_to_database(self):
        """Establece conexión con las bases de datos necesarias."""
        try:
            # Conexión a BD de riesgos
            self.db = AccessDatabase(self.config.get_db_riesgos_connection_string())
            self.logger.info("Conexión establecida con BD de riesgos")
            
            # Conexión a BD de tareas
            self.db_tareas = AccessDatabase(self.config.get_db_tareas_connection_string())
            self.logger.info("Conexión establecida con BD de tareas")
            
        except Exception as e:
            self.logger.error(f"Error conectando a bases de datos: {e}")
            raise
    
    def get_summary_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas de resumen de la ejecución.
        
        Returns:
            Diccionario con estadísticas de errores y warnings
        """
        return {
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'has_errors': self.error_count > 0,
            'has_warnings': self.warning_count > 0
        }
    
    def disconnect_from_database(self):
        """Cierra las conexiones a las bases de datos."""
        try:
            if self.db:
                self.db.disconnect()
                self.logger.info("Conexión cerrada con BD de riesgos")
            if self.db_tareas:
                self.db_tareas.disconnect()
                self.logger.info("Conexión cerrada con BD de tareas")
        except Exception as e:
            self.logger.error(f"Error cerrando conexiones: {e}")
    
    def _normalize_date(self, date_value) -> Optional[datetime]:
        """
        Normaliza fechas de diferentes tipos a datetime de forma consistente.
        
        Args:
            date_value: Valor de fecha que puede ser datetime, date, str o None
            
        Returns:
            datetime normalizado o None si no se puede convertir
        """
        if date_value is None:
            return None
            
        try:
            # Si ya es datetime, devolverlo tal como está
            if isinstance(date_value, datetime):
                return date_value
                
            # Si es date, convertir a datetime
            if hasattr(date_value, 'date') and callable(getattr(date_value, 'date')):
                return datetime.combine(date_value.date(), datetime.min.time())
                
            # Si es string, intentar parsearlo
            if isinstance(date_value, str):
                # Intentar diferentes formatos comunes
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%d/%m/%Y',
                    '%d/%m/%Y %H:%M:%S',
                    '%m/%d/%Y',
                    '%m/%d/%Y %H:%M:%S'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
                        
                # Si no se puede parsear con ningún formato, log warning
                self.logger.warning(f"No se pudo parsear la fecha: {date_value}")
                return None
                
            # Si no es ningún tipo reconocido, intentar convertir a string y parsear
            return self._normalize_date(str(date_value))
            
        except Exception as e:
            self.logger.warning(f"Error normalizando fecha {date_value}: {e}")
            return None
    
    def _calculate_days_difference(self, target_date, reference_date: Optional[datetime] = None) -> int:
        """
        Calcula la diferencia en días entre dos fechas de forma consistente.
        
        Args:
            target_date: Fecha objetivo (puede ser cualquier tipo)
            reference_date: Fecha de referencia (por defecto datetime.now())
            
        Returns:
            Diferencia en días (positivo si target_date es futuro, negativo si es pasado)
        """
        try:
            normalized_target = self._normalize_date(target_date)
            if normalized_target is None:
                return 0
                
            if reference_date is None:
                reference_date = datetime.now()
            else:
                reference_date = self._normalize_date(reference_date) or datetime.now()
                
            return (normalized_target - reference_date).days
            
        except Exception as e:
            self.logger.warning(f"Error calculando diferencia de días: {e}")
            return 0

    def get_last_execution_date(self, task_name: str) -> Optional[date]:
        """
        Obtiene la fecha de la última ejecución de una tarea.
        
        Args:
            task_name: Nombre de la tarea
            
        Returns:
            Fecha de última ejecución o None si no existe
        """
        try:
            query = "SELECT Fecha FROM TbTareas WHERE Tarea = ?"
            result = self.db_tareas.execute_query(query, (task_name,))
            
            if result and len(result) > 0:
                fecha = result[0]['Fecha']
                normalized_date = self._normalize_date(fecha)
                return normalized_date.date() if normalized_date else None
            
            return None
            
        except Exception as e:
            self.error_count += 1
            self._log_sql_error(query, e, f"get_last_execution_date - task: {task_name}")
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo última ejecución de {task_name}: {e}")
            return None
    
    def should_execute_technical_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea técnica (semanal, primer día laborable)
        """
        try:
            from ..common.utils import should_execute_weekly_task
            return should_execute_weekly_task(self.db_tareas, "RiesgosDiariosTecnicos", logger=self.logger)
            
        except Exception as e:
            self.logger.error("Error verificando si ejecutar tarea técnica de riesgos: {}".format(e))
            return False
    
    def should_execute_quality_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea de calidad semanal.
        Se ejecuta el primer día laborable de la semana.
        
        Returns:
            True si debe ejecutarse
        """
        try:
            from ..common.utils import get_first_workday_of_week
            
            last_execution = self.get_last_execution_date("RiesgosDiariosCalidad")
            today = date.today()
            
            # Obtener el primer día laborable de la semana actual
            first_workday_this_week = get_first_workday_of_week(today)
            
            # Si no hay ejecución previa, ejecutar si hoy es el primer día laborable
            if not last_execution:
                return today == first_workday_this_week
            
            # Si la última ejecución fue antes del primer día laborable de esta semana, ejecutar
            return last_execution < first_workday_this_week and today == first_workday_this_week
            
        except Exception as e:
            self.logger.error(f"Error verificando tarea de calidad: {e}")
            return False
    
    def should_execute_monthly_quality_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea de calidad mensual.
        Se ejecuta el primer día laborable del mes.
        
        Returns:
            True si debe ejecutarse
        """
        try:
            from ..common.utils import get_first_workday_of_month
            
            last_execution = self.get_last_execution_date("RiesgosMensualesCalidad")
            today = date.today()
            
            # Obtener el primer día laborable del mes actual
            first_workday_this_month = get_first_workday_of_month(today)
            
            # Si no hay ejecución previa, ejecutar si hoy es el primer día laborable
            if not last_execution:
                return today == first_workday_this_month
            
            # Si la última ejecución fue antes del primer día laborable de este mes, ejecutar
            return last_execution < first_workday_this_month and today == first_workday_this_month
            
        except Exception as e:
            self.logger.error(f"Error verificando tarea mensual: {e}")
            return False
    
    def _build_technical_users_query(self, query_type: str, specific_conditions: List[str] = None) -> str:
        """
        Construye dinámicamente una consulta SQL para obtener usuarios técnicos según el tipo de consulta.
        
        Args:
            query_type: Tipo de consulta a construir
            specific_conditions: Condiciones específicas adicionales para la consulta
            
        Returns:
            Consulta SQL construida
        """
        # Fecha actual y fecha límite como objetos datetime para parámetros
        current_date = datetime.now()
        future_date_15_days = datetime.now() + timedelta(days=15)
        
        # Campos SELECT comunes
        select_clause = """
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
        """
        
        # Condiciones WHERE comunes
        common_conditions = [
            "NOT (TbProyectos.ParaInformeAvisos = 'No')",
            "TbProyectos.FechaCierre IS NULL",
            "TbProyectosEdiciones.FechaPublicacion IS NULL",
            "TbExpedientesResponsables.EsJefeProyecto = 'Sí'",
            "TbExpedientesResponsables.CorreoSiempre = 'Sí'",
            "TbUsuariosAplicaciones.FechaBaja IS NULL"
        ]
        
        # Estructura FROM según el tipo de consulta
        if query_type in ["EDICIONESNECESITANPROPUESTAPUBLICACION", "EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS"]:
            from_clause = """
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            """
        elif query_type in ["RIESGOSACEPTADOSNOMOTIVADOS", "RIESGOSACEPTADOSRECHAZADOS", 
                           "RIESGOSRETIRADOSNOMOTIVADOS", "RIESGOSRETIRADOSRECHAZADOS"]:
            from_clause = """
            FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
            """
        elif query_type == "RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR":
            from_clause = """
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanMitigacionPpal
            ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) INNER JOIN TbRiesgosPlanMitigacionDetalle
            ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion
            """
        elif query_type == "RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR":
            from_clause = """
            FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanContingenciaPpal
            ON TbRiesgos.IDRiesgo = TbRiesgosPlanContingenciaPpal.IDRiesgo) INNER JOIN TbRiesgosPlanContingenciaDetalle
            ON TbRiesgosPlanContingenciaPpal.IDContingencia = TbRiesgosPlanContingenciaDetalle.IDContingencia
            """
        else:
            raise ValueError(f"Tipo de consulta no reconocido: {query_type}")
        
        # Añadir condiciones específicas según el tipo de consulta
        if specific_conditions:
            all_conditions = common_conditions + specific_conditions
        else:
            # Condiciones específicas por tipo de consulta
            if query_type == "EDICIONESNECESITANPROPUESTAPUBLICACION":
                all_conditions = common_conditions + [
                    "TbProyectos.FechaMaxProximaPublicacion <= ?",
                    "TbProyectosEdiciones.FechaPreparadaParaPublicar IS NULL"
                ]
            elif query_type == "EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS":
                all_conditions = common_conditions + [
                    "TbProyectosEdiciones.FechaPreparadaParaPublicar IS NOT NULL",
                    "TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NOT NULL"
                ]
            elif query_type == "RIESGOSACEPTADOSNOMOTIVADOS":
                all_conditions = common_conditions + [
                    "TbRiesgos.Mitigacion = 'Aceptar'",
                    "TbRiesgos.JustificacionAceptacionRiesgo IS NULL"
                ]
            elif query_type == "RIESGOSACEPTADOSRECHAZADOS":
                all_conditions = common_conditions + [
                    "TbRiesgos.Mitigacion = 'Aceptar'",
                    "TbRiesgos.FechaRechazoAceptacionPorCalidad IS NOT NULL"
                ]
            elif query_type == "RIESGOSRETIRADOSNOMOTIVADOS":
                all_conditions = common_conditions + [
                    "TbRiesgos.FechaRetirado IS NOT NULL",
                    "TbRiesgos.JustificacionRetiroRiesgo IS NULL"
                ]
            elif query_type == "RIESGOSRETIRADOSRECHAZADOS":
                all_conditions = common_conditions + [
                    "TbRiesgos.FechaRetirado IS NOT NULL",
                    "TbRiesgos.FechaRechazoRetiroPorCalidad IS NOT NULL"
                ]
            elif query_type == "RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR":
                all_conditions = common_conditions + [
                    "TbRiesgos.FechaRetirado IS NULL",
                    "NOT (TbRiesgos.Mitigacion = 'Aceptar')",
                    "TbRiesgosPlanMitigacionDetalle.FechaFinReal IS NULL",
                    "TbRiesgosPlanMitigacionDetalle.FechaFinPrevista <= ?"
                ]
            elif query_type == "RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR":
                all_conditions = common_conditions + [
                    "TbRiesgos.FechaRetirado IS NULL",
                    "NOT (TbRiesgos.Mitigacion = 'Aceptar')",
                    "TbRiesgosPlanContingenciaDetalle.FechaFinReal IS NULL",
                    "TbRiesgosPlanContingenciaDetalle.FechaFinPrevista <= ?"
                ]
        
        # Construir la cláusula WHERE
        where_clause = "WHERE " + " AND ".join(all_conditions)
        
        # Construir la consulta completa usando concatenación segura
        query = select_clause + " " + from_clause + " " + where_clause
        
        return query

    def get_distinct_technical_users(self) -> List[Dict[str, str]]:
        """
        Obtiene la lista de usuarios técnicos distintos que tienen tareas pendientes.
        Optimizada para usar una sola consulta UNION en lugar de 8 consultas separadas.
        Implementa caché para mejorar el rendimiento.
        
        Returns:
            Lista de usuarios técnicos con sus datos
        """
        # Usar caché si está disponible
        if self._technical_users is not None:
            self.logger.debug(f"Usando caché de usuarios técnicos: {len(self._technical_users)} usuarios")
            return self._technical_users
        
        try:
            self.logger.info("Obteniendo usuarios técnicos con tareas pendientes (consulta optimizada)")
            
            # Construir consulta UNION optimizada
            query = self._build_optimized_technical_users_query()
            
            # Determinar parámetros necesarios como objetos datetime
            current_date = datetime.now()
            future_date_15_days = datetime.now() + timedelta(days=15)
            
            # Los parámetros se usan en el orden: future_date_15_days, current_date, current_date
            params = (future_date_15_days, current_date, current_date)
            
            # Ejecutar la consulta optimizada
            result = self._execute_query_with_error_logging(
                query, 
                params=params,
                context="get_distinct_technical_users - optimized_union_query"
            )
            
            if result:
                # Convertir resultado a lista de diccionarios únicos
                users_collection = {}
                for row in result:
                    usuario_red = row['UsuarioRed']
                    nombre = row['Nombre']
                    correo = row['CorreoUsuario']
                    
                    if usuario_red and usuario_red not in users_collection:
                        users_collection[usuario_red] = {
                            'UsuarioRed': usuario_red, 
                            'Nombre': nombre, 
                            'CorreoUsuario': correo
                        }
                        self.logger.debug(f"Usuario añadido: {usuario_red} ({nombre})")
                
                technical_users_list = list(users_collection.values())
                
                # Guardar en caché
                self._technical_users = technical_users_list
                
                self.logger.info(f"Consulta optimizada completada. Total usuarios técnicos únicos: {len(technical_users_list)}")
                
                # Log de usuarios encontrados para debug
                if technical_users_list:
                    self.logger.info("Usuarios técnicos con tareas pendientes:")
                    for user in technical_users_list:
                        self.logger.info(f"  - {user['UsuarioRed']} ({user['Nombre']}) - {user['CorreoUsuario']}")
                
                return technical_users_list
            else:
                self.logger.info("No se encontraron usuarios técnicos con tareas pendientes")
                self._technical_users = []
                return []
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo usuarios técnicos: {e}")
            # Fallback a método original si falla la consulta optimizada
            self.logger.info("Intentando con método original como fallback...")
            return self._get_distinct_technical_users_fallback()

    def get_quality_users(self) -> List[Dict[str, str]]:
        """
        Obtiene la lista de usuarios de calidad con caché
        
        Returns:
            Lista de usuarios de calidad
        """
        if self._quality_users is not None:
            return self._quality_users
        
        try:
            from ..common.utils import get_quality_users
            self._quality_users = get_quality_users("5", self.config, self.logger)
            return self._quality_users
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo usuarios de calidad: {e}")
            self._quality_users = []
            return self._quality_users
    
    def get_admin_users(self) -> List[Dict[str, str]]:
        """
        Obtiene la lista de usuarios administradores con caché
        
        Returns:
            Lista de usuarios administradores
        """
        if self._admin_users is not None:
            return self._admin_users
        
        try:
            from ..common.utils import get_admin_users
            self._admin_users = get_admin_users(self.db_tareas)
            return self._admin_users
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo usuarios administradores: {e}")
            self._admin_users = []
            return self._admin_users

    def _build_optimized_technical_users_query(self) -> str:
        """
        Construye una consulta UNION optimizada que combina todas las consultas de usuarios técnicos.
        
        Returns:
            Consulta SQL UNION optimizada
        """
        # Campos SELECT comunes
        select_clause = """
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
        """
        
        # Condiciones WHERE comunes
        common_conditions = """
        NOT (TbProyectos.ParaInformeAvisos = 'No')
        AND TbProyectos.FechaCierre IS NULL
        AND TbProyectosEdiciones.FechaPublicacion IS NULL
        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
        AND TbUsuariosAplicaciones.FechaBaja IS NULL
        """
        
        # Consulta 1: EDICIONESNECESITANPROPUESTAPUBLICACION
        query1 = f"""
        {select_clause}
        FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
        INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
        INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
        INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
        WHERE {common_conditions}
        AND TbProyectos.FechaMaxProximaPublicacion <= ?
        AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NULL
        """
        
        # Consulta 2: EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS
        query2 = f"""
        {select_clause}
        FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
        INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
        INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
        INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
        WHERE {common_conditions}
        AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NOT NULL
        AND TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NOT NULL
        """
        
        # Consultas 3-6: Riesgos (aceptados/retirados, motivados/rechazados)
        riesgos_from = """
        FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
        INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
        INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
        INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
        ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
        """
        
        query3 = f"""
        {select_clause}
        {riesgos_from}
        WHERE {common_conditions}
        AND TbRiesgos.Mitigacion = 'Aceptar'
        AND TbRiesgos.JustificacionAceptacionRiesgo IS NULL
        """
        
        query4 = f"""
        {select_clause}
        {riesgos_from}
        WHERE {common_conditions}
        AND TbRiesgos.Mitigacion = 'Aceptar'
        AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NOT NULL
        """
        
        query5 = f"""
        {select_clause}
        {riesgos_from}
        WHERE {common_conditions}
        AND TbRiesgos.FechaRetirado IS NOT NULL
        AND TbRiesgos.JustificacionRetiroRiesgo IS NULL
        """
        
        query6 = f"""
        {select_clause}
        {riesgos_from}
        WHERE {common_conditions}
        AND TbRiesgos.FechaRetirado IS NOT NULL
        AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NOT NULL
        """
        
        # Consulta 7: RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR
        query7 = f"""
        {select_clause}
        FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
        INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
        INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
        INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
        ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanMitigacionPpal
        ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) INNER JOIN TbRiesgosPlanMitigacionDetalle
        ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion
        WHERE {common_conditions}
        AND TbRiesgos.FechaRetirado IS NULL
        AND TbRiesgos.Mitigacion <> 'Aceptar'
        AND TbRiesgosPlanMitigacionDetalle.FechaFinReal IS NULL
        AND TbRiesgosPlanMitigacionDetalle.FechaFinPrevista <= ?
        """
        
        # Consulta 8: RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR
        query8 = f"""
        {select_clause}
        FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
        INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
        INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
        INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
        ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanContingenciaPpal
        ON TbRiesgos.IDRiesgo = TbRiesgosPlanContingenciaPpal.IDRiesgo) INNER JOIN TbRiesgosPlanContingenciaDetalle
        ON TbRiesgosPlanContingenciaPpal.IDContingencia = TbRiesgosPlanContingenciaDetalle.IDContingencia
        WHERE {common_conditions}
        AND TbRiesgos.FechaRetirado IS NULL
        AND TbRiesgos.Mitigacion <> 'Aceptar'
        AND TbRiesgosPlanContingenciaDetalle.FechaFinReal IS NULL
        AND TbRiesgosPlanContingenciaDetalle.FechaFinPrevista <= ?
        """
        
        # Combinar todas las consultas con UNION
        union_query = f"""
        {query1}
        UNION
        {query2}
        UNION
        {query3}
        UNION
        {query4}
        UNION
        {query5}
        UNION
        {query6}
        UNION
        {query7}
        UNION
        {query8}
        """
        
        return union_query

    def _get_distinct_technical_users_fallback(self) -> List[Dict[str, str]]:
        """
        Método fallback que usa el enfoque original de 8 consultas separadas.
        Se usa si la consulta UNION optimizada falla.
        
        Returns:
            Lista de usuarios técnicos con sus datos
        """
        try:
            # Colección para almacenar usuarios únicos
            users_collection = {}
            
            # Definir los tipos de consultas a ejecutar
            query_types = [
                "EDICIONESNECESITANPROPUESTAPUBLICACION",
                "EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS", 
                "RIESGOSACEPTADOSNOMOTIVADOS",
                "RIESGOSACEPTADOSRECHAZADOS",
                "RIESGOSRETIRADOSNOMOTIVADOS",
                "RIESGOSRETIRADOSRECHAZADOS",
                "RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR",
                "RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR"
            ]
            
            # Ejecutar las 8 consultas una a una y añadir usuarios distintos a la colección
            for i, query_type in enumerate(query_types):
                self.logger.info(f"Ejecutando consulta fallback {i+1}/8: {query_type}")
                
                try:
                    # Construir la consulta dinámicamente
                    query = self._build_technical_users_query(query_type)
                    
                    # Determinar si la consulta necesita parámetros
                    params = None
                    if query_type in ["RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR", "RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR"]:
                        current_date = datetime.now()
                        params = (current_date,)
                    
                    # Ejecutar la consulta con logging de errores
                    result = self._execute_query_with_error_logging(
                        query, 
                        params=params,
                        context=f"get_distinct_technical_users_fallback - query_type: {query_type}"
                    )
                    if result:
                        # Añadir usuarios distintos a la colección
                        for row in result:
                            usuario_red = row['UsuarioRed']
                            nombre = row['Nombre']
                            correo = row['CorreoUsuario']
                            
                            if usuario_red and usuario_red not in users_collection:
                                users_collection[usuario_red] = {
                                    'UsuarioRed': usuario_red, 
                                    'Nombre': nombre, 
                                    'CorreoUsuario': correo
                                }
                                self.logger.debug(f"Usuario añadido: {usuario_red} ({nombre})")
                        
                        self.logger.info(f"Consulta fallback {i+1} completada: {len(result)} registros obtenidos")
                    else:
                        self.logger.info(f"Consulta fallback {i+1} completada: 0 registros")
                        
                except Exception as e:
                    self._log_sql_error(
                        query if 'query' in locals() else "Query not built", 
                        e, 
                        f"get_distinct_technical_users_fallback - query_type: {query_type}"
                    )
                    self.logger.warning(f"Error ejecutando consulta fallback {i+1} ({query_type}): {e}")
                    continue
            
            # Convertir la colección a lista
            technical_users_list = list(users_collection.values())
            
            self.logger.info(f"Método fallback completado. Total usuarios técnicos únicos: {len(technical_users_list)}")
            
            return technical_users_list
            
        except Exception as e:
            self.logger.error(f"Error en método fallback: {e}")
            return []
    
    def execute_technical_task(self) -> bool:
        """
        Ejecuta la tarea técnica semanal.
        Genera informes personalizados para cada técnico.
        
        Returns:
            True si se ejecutó correctamente
            
        Raises:
            Exception: Si ocurre algún error durante la ejecución
        """
        self.logger.info("Iniciando tarea técnica de riesgos")
        
        # Obtener usuarios técnicos con tareas pendientes
        technical_users = self.get_distinct_technical_users()
        
        if not technical_users:
            self.logger.info("No hay usuarios técnicos con tareas pendientes")
            return True
        
        # Procesar cada usuario técnico
        for user in technical_users:
            user_id = user['UsuarioRed']
            user_name = user['Nombre']
            user_email = user['CorreoUsuario']
            
            if not user_email:
                self.logger.warning(f"Usuario {user_name} no tiene email configurado")
                continue
            
            # Generar informe personalizado
            html_content = self._generate_technical_report_html(user_id, user_name)
            
            if html_content:
                # Registrar correo en BD
                subject = "Informe Tareas Para Técnicos (Gestión de Riesgos)"
                register_email_in_database(
                    self.db_tareas, "Riesgos", subject, html_content, user_email
                )
                
                self.logger.info(f"Informe técnico generado para {user_name}")
        
        # Registrar tarea como completada
        register_task_completion(self.db_tareas, "RiesgosDiariosTecnicos")
        
        return True
    
    def execute_quality_task(self) -> bool:
        """
        Ejecuta la tarea de calidad semanal.
        Envía un correo individualizado a cada miembro del equipo de calidad.
        Cada miembro recibe sus tareas primero y luego las del resto.
        
        Returns:
            True si se ejecutó correctamente
            
        Raises:
            Exception: Si ocurre algún error durante la ejecución
        """
        self.logger.info("Iniciando tarea de calidad semanal")
        
        # Obtener usuarios de calidad
        quality_users = get_quality_users("5", self.config, self.logger)  # ID 5 para Riesgos
        
        if not quality_users:
            self.logger.info("No hay usuarios de calidad configurados")
            return True
        
        # Generar las secciones HTML para cada miembro de calidad
        quality_sections = {}
        for user in quality_users:
            user_name = user.get('Nombre', 'Usuario desconocido')
            quality_sections[user_name] = self._generate_quality_member_section_html(user_name)
        
        # Enviar correo individualizado a cada miembro de calidad
        for user in quality_users:
            user_name = user.get('Nombre', 'Usuario desconocido')
            user_email = user.get('CorreoUsuario', '')
            
            if not user_email:
                self.logger.warning(f"Usuario de calidad {user_name} no tiene email configurado")
                continue
            
            # Generar HTML personalizado: sus tareas primero, luego las del resto
            html_content = self._generate_personalized_quality_report_html(
                user_name, quality_sections
            )
            
            if html_content:
                # Registrar correo en BD
                subject = "Informe Tareas Calidad (Gestión de Riesgos)"
                register_email_in_database(
                    self.db_tareas, "Riesgos", subject, html_content, user_email
                )
                
                self.logger.info(f"Informe de calidad semanal generado para {user_name}")
        
        # Registrar tarea como completada
        register_task_completion(self.db_tareas, "RiesgosDiariosCalidad")
        
        return True
    
    def execute_monthly_quality_task(self) -> bool:
        """
        Ejecuta la tarea de calidad mensual.
        Envía el mismo informe a todos los miembros de calidad.
        
        Returns:
            True si se ejecutó correctamente
            
        Raises:
            Exception: Si ocurre algún error durante la ejecución
        """
        self.logger.info("Iniciando tarea de calidad mensual")
        
        # Generar informe mensual
        html_content = self._generate_monthly_quality_report_html()
        
        if html_content:
            # Obtener usuarios de calidad
            quality_users = get_quality_users("5", self.config, self.logger)  # ID 5 para Riesgos
            
            if quality_users:
                # Obtener emails de calidad
                quality_emails = get_quality_emails_string("5", self.config, self.logger, self.db_tareas)
                
                if quality_emails:
                    # Registrar correo en BD
                    subject = "Informe Mensual Calidad (Gestión de Riesgos)"
                    register_email_in_database(
                        self.db_tareas, "Riesgos", subject, html_content, quality_emails
                    )
                    
                    self.logger.info("Informe de calidad mensual generado")
        
        # Registrar tarea como completada
        register_task_completion(self.db_tareas, "RiesgosMensualesCalidad")
        
        return True
    
    def run_daily_tasks(self, force_technical: bool = False, force_quality: bool = False, 
                       force_monthly: bool = False) -> Dict[str, bool]:
        """
        Ejecuta las tareas diarias según corresponda.
        
        Args:
            force_technical: Forzar ejecución de tarea técnica
            force_quality: Forzar ejecución de tarea de calidad
            force_monthly: Forzar ejecución de tarea mensual
            
        Returns:
            Diccionario con el resultado de cada tarea
            
        Raises:
            Exception: Si ocurre algún error durante la ejecución de las tareas.
                      La excepción se propaga para facilitar la depuración.
        """
        results = {
            'technical': False,
            'quality': False,
            'monthly': False
        }
        
        # Verificar qué tareas deben ejecutarse
        should_run_technical = force_technical or self.should_execute_technical_task()
        should_run_quality = force_quality or self.should_execute_quality_task()
        should_run_monthly = force_monthly or self.should_execute_monthly_quality_task()
        
        if not (should_run_technical or should_run_quality or should_run_monthly):
            self.logger.info("No hay tareas de riesgos para ejecutar hoy")
            return results
        
        # Ejecutar tareas según corresponda
        if should_run_technical:
            results['technical'] = self.execute_technical_task()
            
        if should_run_quality:
            results['quality'] = self.execute_quality_task()
            
        if should_run_monthly:
            results['monthly'] = self.execute_monthly_quality_task()
        
        # Log de resumen
        executed_tasks = [task for task, success in results.items() if success]
        if executed_tasks:
            self.logger.info(f"Tareas ejecutadas: {', '.join(executed_tasks)}")
        
        return results
    
    def _generate_technical_report_html(self, user_id: str, user_name: str) -> str:
        """
        Genera el reporte HTML técnico para un usuario específico.
        
        Args:
            user_id: ID del usuario
            user_name: Nombre del usuario
            
        Returns:
            Contenido HTML del reporte
            
        Raises:
            Exception: Si ocurre algún error durante la generación del reporte.
                      La excepción se propaga para facilitar la depuración.
        """
        # Cargar CSS
        css_content = self._load_css_styles()
        
        # Generar header HTML
        title = f"Informe Técnico de Riesgos - {user_name}"
        html = generate_html_header(title, css_content)
        
        # Agregar título principal
        html += f"""
        <body>
            <div class="centrado">
                <h1>INFORME TAREAS SEMANALES PARA <strong>{user_name}</strong></h1>
                <p>Fecha: {format_date(datetime.now())}</p>
            </div>
            <br>
        """
        
        # Obtener y agregar secciones del reporte
        sections_added = 0
        
        # 1. Ediciones que necesitan propuesta de publicación
        editions_data = self._get_editions_need_publication_data(user_id)
        if editions_data:
            html += self.generate_table_html(editions_data, 'editions_need_publication')
            sections_added += 1
        
        # 2. Ediciones con propuestas rechazadas
        rejected_data = self._get_editions_with_rejected_proposals_data(user_id)
        if rejected_data:
            html += self.generate_table_html(rejected_data, 'editions_with_rejected_proposals')
            sections_added += 1
        
        # 3. Riesgos aceptados sin motivar
        accepted_unmotivated_data = self._get_accepted_risks_unmotivated_data(user_id)
        if accepted_unmotivated_data:
            html += self.generate_table_html(accepted_unmotivated_data, 'accepted_risks_unmotivated')
            sections_added += 1
        
        # 4. Riesgos aceptados rechazados
        accepted_rejected_data = self._get_accepted_risks_rejected_data(user_id)
        if accepted_rejected_data:
            html += self.generate_table_html(accepted_rejected_data, 'accepted_risks_rejected')
            sections_added += 1
        
        # 5. Riesgos retirados sin motivar
        retired_unmotivated_data = self._get_retired_risks_unmotivated_data(user_id)
        if retired_unmotivated_data:
            html += self.generate_table_html(retired_unmotivated_data, 'retired_risks_unmotivated')
            sections_added += 1
        
        # 6. Riesgos retirados rechazados
        retired_rejected_data = self._get_retired_risks_rejected_data(user_id)
        if retired_rejected_data:
            html += self.generate_table_html(retired_rejected_data, 'retired_risks_rejected')
            sections_added += 1
        
        # 7. Acciones de mitigación para replanificar
        mitigation_reschedule_data = self._get_mitigation_actions_reschedule_data(user_id)
        if mitigation_reschedule_data:
            html += self.generate_table_html(mitigation_reschedule_data, 'mitigation_actions_reschedule')
            sections_added += 1
        
        # 8. Acciones de contingencia para replanificar
        contingency_reschedule_data = self._get_contingency_actions_reschedule_data(user_id)
        if contingency_reschedule_data:
            html += self.generate_table_html(contingency_reschedule_data, 'contingency_actions_reschedule')
            sections_added += 1
        
        # Si no hay secciones, no generar reporte
        if sections_added == 0:
            return ""
        
        html += """
            </body>
        </html>
        """
        
        return html
    
    def generate_table_html(self, data: List[Dict], table_type: str) -> str:
        """
        Genera tabla HTML usando la configuración predefinida.
        
        Args:
            data: Lista de diccionarios con los datos
            table_type: Tipo de tabla según TABLE_CONFIGURATIONS
            
        Returns:
            HTML de la tabla
        """
        if table_type not in TABLE_CONFIGURATIONS:
            self.logger.warning(f"Tipo de tabla no configurado: {table_type}")
            return ""
        
        config = TABLE_CONFIGURATIONS[table_type]
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_personalized_quality_report_html(self, primary_user: str, quality_sections: Dict[str, str]) -> str:
        """
        Genera el reporte HTML personalizado de calidad semanal.
        El usuario primario aparece primero, luego el resto.
        
        Args:
            primary_user: Nombre del usuario principal (sus tareas aparecen primero)
            quality_sections: Diccionario con las secciones HTML de cada usuario
            
        Returns:
            Contenido HTML del reporte personalizado
            
        Raises:
            Exception: Si ocurre algún error durante la generación del reporte.
                      La excepción se propaga para facilitar la depuración.
        """
        # Cargar CSS
        css_content = self._load_css_styles()
        
        # Generar header HTML
        title = "Informe Semanal de Calidad - Gestión de Riesgos"
        html = generate_html_header(title, css_content)
        
        html += f"""
        <body>
            <div class="centrado">
                <h1>INFORME TAREAS SEMANAL CALIDAD</h1>
                <p>Fecha: {format_date(datetime.now())}</p>
            </div>
            <br>
        """
        
        # Agregar sección del usuario principal primero
        if primary_user in quality_sections:
            html += f"""
            <div>
                {quality_sections[primary_user]}
                <hr size='2px' color='black' />
                <br>
            </div>
            """
        
        # Agregar secciones del resto de usuarios
        for user_name, section_html in quality_sections.items():
            if user_name != primary_user:
                html += f"""
                <div>
                    {section_html}
                    <hr size='2px' color='black' />
                    <br>
                </div>
                """
        
        html += """
            </body>
        </html>
        """
        
        return html
    
    def _generate_quality_member_section_html(self, member_name: str) -> str:
        """
        Genera la sección HTML para un miembro específico de calidad.
        
        Args:
            member_name: Nombre del miembro de calidad
            
        Returns:
            HTML de la sección
            
        Raises:
            Exception: Si ocurre algún error durante la generación de la sección.
                      La excepción se propaga para facilitar la depuración.
        """
        html = f"""
        <div>
            <h2>INFORME TAREAS SEMANAL CALIDAD PARA <strong>{member_name}</strong></h2>
            <br>
        """
        
        sections_added = 0
        
        # 1. Ediciones preparadas para publicar
        editions_ready_data = self._get_editions_ready_for_publication_data(member_name)
        if editions_ready_data:
            html += self.generate_table_html(editions_ready_data, 'editions_ready_for_publication')
            sections_added += 1
        
        # 2. Ediciones a punto de caducar y caducadas (combinadas en una sola tabla)
        editions_about_to_expire_data = self._get_editions_about_to_expire_data(member_name)
        expired_editions_data = self._get_expired_editions_data(member_name)
        
        # Combinar ambos conjuntos de datos si existen
        combined_expired_data = []
        if editions_about_to_expire_data:
            combined_expired_data.extend(editions_about_to_expire_data)
        if expired_editions_data:
            combined_expired_data.extend(expired_editions_data)
            
        if combined_expired_data:
            html += self.generate_table_html(combined_expired_data, 'editions_with_expired_dates')
            sections_added += 1
        
        # 4. Riesgos para retipificar
        risks_to_reclassify_data = self._get_risks_to_reclassify_data(member_name)
        if risks_to_reclassify_data:
            html += self.generate_table_html(risks_to_reclassify_data, 'risks_to_reclassify')
            sections_added += 1
        
        # 5. Riesgos aceptados por visar
        accepted_risks_to_approve_data = self._get_accepted_risks_to_approve_data(member_name)
        if accepted_risks_to_approve_data:
            html += self.generate_table_html(accepted_risks_to_approve_data, 'accepted_risks_pending_approval')
            sections_added += 1
        
        # 6. Riesgos retirados por visar
        retired_risks_to_approve_data = self._get_retired_risks_to_approve_data(member_name)
        if retired_risks_to_approve_data:
            html += self.generate_table_html(retired_risks_to_approve_data, 'retired_risks_pending_approval')
            sections_added += 1
        
        # 7. Riesgos materializados por decidir
        materialized_risks_data = self._get_materialized_risks_to_decide_data(member_name)
        if materialized_risks_data:
            html += self.generate_table_html(materialized_risks_data, 'materialized_risks_pending_decision')
            sections_added += 1
        
        if sections_added == 0:
            html += "<p>No hay tareas pendientes para este miembro de calidad.</p>"
        
        html += "</div>"
        
        return html
    
    def _generate_monthly_quality_report_html(self) -> str:
        """
        Genera el reporte HTML de calidad mensual.
        
        Returns:
            Contenido HTML del reporte
            
        Raises:
            Exception: Si ocurre algún error durante la generación del reporte.
                      La excepción se propaga para facilitar la depuración.
        """
        # Cargar CSS
        css_content = self._load_css_styles()
        
        # Generar header HTML
        title = "Informe Mensual de Calidad - Gestión de Riesgos"
        html = generate_html_header(title, css_content)
        
        html += f"""
        <body>
            <div class="centrado">
                <h1>INFORME MENSUAL PARA CALIDAD</h1>
                <p>Fecha: {format_date(datetime.now())}</p>
            </div>
            <br>
        """
        
        # 1. Riesgos aceptados pendientes de aprobación
        accepted_risks_pending_approval_data = self._get_accepted_risks_pending_approval_data()
        if accepted_risks_pending_approval_data:
            html += self.generate_table_html(
                accepted_risks_pending_approval_data, 'accepted_risks_pending_approval'
            )
        
        # 2. Riesgos retirados pendientes de aprobación
        retired_risks_pending_approval_data = self._get_retired_risks_pending_approval_data()
        if retired_risks_pending_approval_data:
            html += self.generate_table_html(
                retired_risks_pending_approval_data, 'retired_risks_pending_approval'
            )
        
        # 3. Riesgos materializados pendientes de decisión
        materialized_risks_pending_decision_data = self._get_materialized_risks_pending_decision_data()
        if materialized_risks_pending_decision_data:
            html += self.generate_table_html(
                materialized_risks_pending_decision_data, 'materialized_risks_pending_decision'
            )
        
        # 4. Ediciones preparadas para publicar (resumen general)
        editions_ready_data = self._get_all_editions_ready_for_publication_data()
        if editions_ready_data:
            html += self.generate_table_html(
                editions_ready_data, 'editions_ready_for_publication'
            )
        
        # 5. Ediciones activas
        active_editions_data = self._get_active_editions_data()
        if active_editions_data:
            html += self.generate_table_html(
                active_editions_data, 'active_editions'
            )
        
        # 6. Ediciones cerradas el último mes
        closed_editions_data = self._get_closed_editions_last_month_data()
        if closed_editions_data:
            html += self.generate_table_html(
                closed_editions_data, 'closed_editions_last_month'
            )
        
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
            
        Raises:
            Exception: Si ocurre un error al generar el HTML
        """
        if not data:
            return ""
        
        html = f"""
        <div class="section">
            <h3 class="ColespanArriba">{title} ({len(data)})</h3>
            <table>
                <thead>
                    <tr class="Cabecera">
        """
        
        # Generar cabeceras de la tabla
        if data:
            columns = list(data[0].keys())
            for col in columns:
                html += f"<th>{col}</th>"
        
        html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Generar filas de datos
        for row in data:
            html += "<tr>"
            for col in columns:
                value = row.get(col, '')
                if isinstance(value, datetime):
                    value = format_date(value)
                elif isinstance(value, date):
                    value = format_date(value)
                elif value is None:
                    value = ''
                
                # Aplicar estilo especial para campos de días
                if col.lower().startswith('dias') or col.lower().endswith('dias') or 'diasvencidos' in col.lower() or 'diaspara' in col.lower():
                    try:
                        dias = int(value)
                        dias_class = self._get_dias_class(dias)
                        html += f'<td style="text-align: center;"><span class="dias-indicador {dias_class}">{value}</span></td>'
                    except (ValueError, TypeError):
                        html += f'<td style="text-align: center;">{value}</td>'
                else:
                    html += f'<td style="text-align: center;">{value}</td>'
            html += "</tr>"
        
        html += """
                </tbody>
            </table>
        </div>
        <br>
        """
        
        return html
    
    def _load_css_styles(self) -> str:
        """
        Carga los estilos CSS para los reportes.
        
        Returns:
            Contenido CSS
            
        Raises:
            Exception: Si ocurre un error al cargar el CSS
        """
        return load_css_content(self.config.css_modern_file_path)
    
    def _get_css_class_for_days(self, dias: int) -> str:
        """
        Determina la clase CSS apropiada basada en el número de días.
        
        Args:
            dias: Número de días
            
        Returns:
            Clase CSS apropiada
        """
        if dias <= 0:
            return "negativo"
        elif dias <= 7:
            return "critico"
        else:
            return "normal"
    
    def _get_risks_data(self, query_type: str, user_id: str = None, member_name: str = None, **kwargs) -> List[Dict]:
        """
        Función genérica unificada para obtener datos de riesgos.
        
        Args:
            query_type: Tipo de consulta a ejecutar
            user_id: ID del usuario técnico (para consultas técnicas)
            member_name: Nombre del miembro de calidad (para consultas de calidad)
            **kwargs: Parámetros adicionales específicos de cada consulta
            
        Returns:
            Lista de diccionarios con los datos obtenidos
        """
        try:
            # Definir las consultas base comunes
            base_joins = {
                'technical_base': """
                    FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                            INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                            INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) 
                            INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                            ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 
                            ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
                """,
                'quality_base': """
                    FROM TbProyectos 
                    INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                """,
                'quality_risks_base': """
                    FROM TbProyectos 
                    INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                    ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                """
            }
            
            # Condiciones WHERE comunes
            common_conditions = {
                'technical_common': """
                    NOT (TbProyectos.ParaInformeAvisos = 'No')
                    AND TbProyectos.FechaCierre IS NULL
                    AND TbProyectosEdiciones.FechaPublicacion IS NULL
                    AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                    AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                    AND TbUsuariosAplicaciones.FechaBaja IS NULL
                """,
                'quality_common': """
                    NOT (TbProyectos.ParaInformeAvisos = 'No')
                    AND TbProyectos.FechaCierre IS NULL
                    AND TbProyectosEdiciones.FechaPublicacion IS NULL
                """
            }
            
            # Definir las consultas específicas
            queries = {
                'editions_need_publication': {
                    'select': """
                        SELECT TbExpedientes1.Nemotecnico, TbProyectosEdiciones.IDEdicion, TbProyectosEdiciones.Edicion,
                               TbProyectos.FechaMaxProximaPublicacion, TbProyectosEdiciones.FechaPreparadaParaPublicar,
                               TbUsuariosAplicaciones.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                        INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                        INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                        INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbProyectos.FechaMaxProximaPublicacion <= ?
                        AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NULL
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (datetime.now() + timedelta(days=15), user_id),
                    'post_process': 'calculate_days_from_fecha_max'
                },
                
                'editions_with_rejected_proposals': {
                    'select': """
                        SELECT TbExpedientes1.Nemotecnico, TbProyectosEdiciones.IDEdicion, TbProyectosEdiciones.Edicion,
                               TbProyectos.FechaMaxProximaPublicacion, TbProyectosEdiciones.FechaPreparadaParaPublicar,
                               TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha, 
                               TbProyectosEdiciones.PropuestaRechazadaPorCalidadMotivo,
                               TbUsuariosAplicaciones.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                        INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                        INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                        INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NOT NULL
                        AND TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NOT NULL
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (user_id,)
                },
                
                'accepted_risks_unmotivated': {
                    'select': """
                        SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                               TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                                INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                                ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1
                                ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbRiesgos.Mitigacion = 'Aceptar'
                        AND TbRiesgos.FechaJustificacionAceptacionRiesgo IS NULL
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (user_id,)
                },
                
                'accepted_risks_rejected': {
                    'select': """
                        SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, 
                               TbRiesgos.CausaRaiz, TbRiesgos.FechaRechazoAceptacionPorCalidad, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                                INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                                ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1
                                ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbRiesgos.Mitigacion = 'Aceptar'
                        AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NOT NULL
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (user_id,)
                },
                
                'retired_risks_unmotivated': {
                    'select': """
                        SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                               TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, TbRiesgos.FechaRetirado,
                               TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                                INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                                ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1
                                ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbRiesgos.FechaRetirado IS NOT NULL
                        AND TbRiesgos.JustificacionRetiroRiesgo IS NULL
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (user_id,)
                },
                
                'retired_risks_rejected': {
                    'select': """
                        SELECT DISTINCT TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, 
                               TbRiesgos.CausaRaiz, TbExpedientes1.Nemotecnico, TbRiesgos.FechaRetirado, 
                               TbRiesgos.FechaRechazoRetiroPorCalidad, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id)
                                INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion)
                                ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1
                                ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbRiesgos.FechaRetirado IS NOT NULL
                        AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NOT NULL
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (user_id,)
                },
                
                'mitigation_actions_reschedule': {
                    'select': """
                        SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                               TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, 
                               TbRiesgosPlanMitigacionPpal.DisparadorDelPlan, 
                               TbRiesgosPlanMitigacionDetalle.Accion,
                               TbRiesgosPlanMitigacionDetalle.FechaInicio, 
                               TbRiesgosPlanMitigacionDetalle.FechaFinPrevista,
                               TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) 
                                INNER JOIN ((TbProyectosEdiciones INNER JOIN (TbRiesgos INNER JOIN TbRiesgosPlanMitigacionPpal 
                                ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                                INNER JOIN TbRiesgosPlanMitigacionDetalle ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion) 
                                ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 
                                ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbRiesgos.FechaRetirado IS NULL
                        AND TbRiesgos.Mitigacion <> 'Aceptar'
                        AND TbRiesgosPlanMitigacionDetalle.FechaFinReal IS NULL
                        AND TbRiesgosPlanMitigacionDetalle.FechaFinPrevista <= ?
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (datetime.now(), user_id)
                },
                
                'mitigation_actions_pending': {
                    'select': """
                        SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                               TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, 
                               TbRiesgosPlanMitigacionPpal.DisparadorDelPlan, 
                               TbRiesgosPlanMitigacionDetalle.Accion,
                               TbRiesgosPlanMitigacionDetalle.FechaInicio, 
                               TbRiesgosPlanMitigacionDetalle.FechaFinPrevista,
                               TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) 
                                INNER JOIN ((TbProyectosEdiciones INNER JOIN (TbRiesgos INNER JOIN TbRiesgosPlanMitigacionPpal 
                                ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                                INNER JOIN TbRiesgosPlanMitigacionDetalle ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion) 
                                ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 
                                ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbRiesgos.FechaRetirado IS NULL
                        AND TbRiesgos.Mitigacion <> 'Aceptar'
                        AND TbRiesgosPlanMitigacionDetalle.FechaFinReal IS NULL
                        AND TbRiesgosPlanMitigacionDetalle.FechaInicio <= ?
                        AND TbRiesgosPlanMitigacionDetalle.FechaFinPrevista > ?
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (datetime.now(), datetime.now(), user_id)
                },
                
                'contingency_actions_reschedule': {
                    'select': """
                        SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                               TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, 
                               TbRiesgosPlanContingenciaPpal.DisparadorDelPlan, 
                               TbRiesgosPlanContingenciaDetalle.Accion,
                               TbRiesgosPlanContingenciaDetalle.FechaInicio, 
                               TbRiesgosPlanContingenciaDetalle.FechaFinPrevista,
                               TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                    """,
                    'from': """
                        FROM ((((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                                  INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                                  INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) 
                                  LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                                  INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                                  ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanContingenciaPpal 
                                  ON TbRiesgos.IDRiesgo = TbRiesgosPlanContingenciaPpal.IDRiesgo) INNER JOIN TbRiesgosPlanContingenciaDetalle 
                                  ON TbRiesgosPlanContingenciaPpal.IDContingencia = TbRiesgosPlanContingenciaDetalle.IDContingencia
                    """,
                    'where': """
                        WHERE TbProyectos.ParaInformeAvisos <> 'No'
                        AND TbProyectos.FechaCierre IS NULL
                        AND TbProyectosEdiciones.FechaPublicacion IS NULL
                        AND TbExpedientesResponsables.EsJefeProyecto = 'Sí'
                        AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
                        AND TbUsuariosAplicaciones.FechaBaja IS NULL
                        AND TbRiesgos.FechaRetirado IS NULL
                        AND TbRiesgos.Mitigacion <> 'Aceptar'
                        AND TbRiesgosPlanContingenciaDetalle.FechaFinReal IS NULL
                        AND TbRiesgosPlanContingenciaDetalle.FechaFinPrevista <= ?
                        AND TbUsuariosAplicaciones.UsuarioRed = ?
                    """,
                    'params': lambda: (datetime.now(), user_id)
                }
            }
            
            # Verificar que el tipo de consulta existe
            if query_type not in queries:
                self.logger.error(f"Tipo de consulta no válido: {query_type}")
                return []
            
            query_config = queries[query_type]
            
            # Construir la consulta completa
            full_query = query_config['select'] + query_config['from'] + query_config['where']
            
            # Obtener parámetros
            params = query_config['params']()
            
            # Debug logging para identificar el problema
            if query_type == 'accepted_risks_unmotivated':
                self.logger.info(f"DEBUG - Query completa para {query_type}:")
                self.logger.info(f"SELECT: {query_config['select']}")
                self.logger.info(f"FROM: {query_config['from']}")
                self.logger.info(f"WHERE: {query_config['where']}")
                self.logger.info(f"FULL QUERY: {full_query}")
                self.logger.info(f"PARAMS: {params}")
                self.logger.info(f"PARAM COUNT: {len(params) if params else 0}")
                # Contar marcadores de parámetros en la consulta
                param_count = full_query.count('?')
                self.logger.info(f"PARAMETER MARKERS COUNT: {param_count}")
                # Buscar específicamente el problema
                if param_count != len(params):
                    self.logger.error(f"MISMATCH: Query tiene {param_count} marcadores pero se pasan {len(params)} parámetros")
                    # Buscar dónde están los marcadores
                    import re
                    markers = [(m.start(), m.group()) for m in re.finditer(r'\?', full_query)]
                    self.logger.info(f"MARCADORES ENCONTRADOS: {markers}")
                    # Mostrar contexto de cada marcador
                    for i, (pos, marker) in enumerate(markers):
                        start = max(0, pos - 50)
                        end = min(len(full_query), pos + 50)
                        context = full_query[start:end]
                        self.logger.info(f"MARCADOR {i+1} en posición {pos}: ...{context}...")
            
            # Ejecutar la consulta
            result = self._execute_query_with_error_logging(
                full_query, 
                params, 
                f"_get_risks_data - query_type: {query_type}, user_id: {user_id}, member_name: {member_name}"
            ) or []
            
            # Aplicar post-procesamiento si es necesario
            if query_config.get('post_process') == 'calculate_days_from_fecha_max':
                for row in result:
                    if row.get('FechaMaxProximaPublicacion'):
                        row['Dias'] = self._calculate_days_difference(row['FechaMaxProximaPublicacion'])
                    else:
                        row['Dias'] = 0
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self._log_sql_error(
                f"Query type: {query_type}", 
                e, 
                f"_get_risks_data - query_type: {query_type}, user_id: {user_id}, member_name: {member_name}"
            )
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo datos de riesgos: {e}")
            return []
    
    # Métodos de consulta de datos (implementación básica)
    # Estos métodos deben implementarse según las consultas específicas del script VBS
    
    def _get_editions_need_publication_data(self, user_id: str) -> List[Dict]:
        """Obtiene ediciones que necesitan propuesta de publicación para un técnico."""
        return self._get_risks_data('editions_need_publication', user_id)
    
    def _get_editions_with_rejected_proposals_data(self, user_id: str) -> List[Dict]:
        """Obtiene ediciones con propuestas rechazadas para un técnico."""
        return self._get_risks_data('editions_with_rejected_proposals', user_id)
    
    def _get_accepted_risks_unmotivated_data(self, user_id: str) -> List[Dict]:
        """Obtiene riesgos aceptados sin motivar para un técnico."""
        return self._get_risks_data('accepted_risks_unmotivated', user_id)
    
    def _get_accepted_risks_rejected_data(self, user_id: str) -> List[Dict]:
        """Obtiene riesgos aceptados rechazados por calidad para un técnico."""
        return self._get_risks_data('accepted_risks_rejected', user_id)
    
    def _get_retired_risks_unmotivated_data(self, user_id: str) -> List[Dict]:
        """Obtiene riesgos retirados sin motivar para un técnico."""
        return self._get_risks_data('retired_risks_unmotivated', user_id)
    
    def _get_retired_risks_rejected_data(self, user_id: str) -> List[Dict]:
        """Obtiene riesgos retirados rechazados por calidad para un técnico."""
        return self._get_risks_data('retired_risks_rejected', user_id)
    
    def _get_mitigation_actions_reschedule_data(self, user_id: str) -> List[Dict]:
        """Obtiene acciones de mitigación que necesitan replanificación para un técnico."""
        return self._get_risks_data('mitigation_actions_reschedule', user_id)
    
    def _get_contingency_actions_reschedule_data(self, user_id: str) -> List[Dict]:
        """Obtiene acciones de contingencia que necesitan replanificación para un técnico."""
        return self._get_risks_data('contingency_actions_reschedule', user_id)
    
    # Métodos para datos de calidad
    
    def _get_editions_ready_for_publication_data(self, member_name: str) -> List[Dict]:
        """Obtiene ediciones preparadas para publicar asignadas a un miembro de calidad."""
        try:
            query = """
                SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,
                       TbProyectosEdiciones.IDEdicion, TbProyectosEdiciones.Edicion, 
                       TbProyectosEdiciones.FechaEdicion, TbProyectosEdiciones.FechaPreparadaParaPublicar
                FROM TbProyectos 
                INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                WHERE TbProyectos.NombreUsuarioCalidad = ? 
                AND TbProyectos.FechaCierre IS NULL
                AND TbProyectosEdiciones.FechaPublicacion IS NULL
                AND TbProyectosEdiciones.FechaPreparadaParaPublicar IS NOT NULL
            """
            return self._execute_query_with_error_logging(
                query, 
                params=(member_name,),
                context=f"_get_editions_ready_for_publication_data - member_name: {member_name}"
            ) or []
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo ediciones preparadas: {e}")
            return []

    def _get_editions_about_to_expire_data(self, member_name: str) -> List[Dict]:
        """Obtiene ediciones a punto de caducar asignadas a un miembro de calidad."""
        try:
            # Calcular fecha límite (15 días desde hoy) como objeto datetime para parámetro
            future_date_15_days = datetime.now() + timedelta(days=15)
            
            query = """
                SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,
                       TbProyectos.FechaPrevistaCierre, TbProyectosEdiciones.IDEdicion,
                       TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion,
                       TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad
                FROM TbProyectos 
                INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                WHERE NOT (TbProyectos.ParaInformeAvisos = 'No')
                AND TbProyectos.FechaCierre IS NULL
                AND TbProyectosEdiciones.FechaPublicacion IS NULL
                AND TbProyectosEdiciones.FechaMaxProximaPublicacion <= ?
                AND TbProyectos.NombreUsuarioCalidad = ?
            """
            
            result = self._execute_query_with_error_logging(
                query, 
                params=(future_date_15_days, member_name),
                context=f"_get_editions_about_to_expire_data - member_name: {member_name}"
            ) or []
            
            # Calcular días en Python para cada registro
            for row in result:
                if row.get('FechaMaxProximaPublicacion'):
                    row['Dias'] = self._calculate_days_difference(row['FechaMaxProximaPublicacion'])
                else:
                    row['Dias'] = 0
            
            return result
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo ediciones a punto de caducar: {e}")
            return []

    def _get_expired_editions_data(self, member_name: str) -> List[Dict]:
        """Obtiene ediciones caducadas asignadas a un miembro de calidad."""
        try:
            # Calcular fecha actual como objeto datetime para parámetro
            current_date = datetime.now()
            
            query = """
                SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,
                       TbProyectos.FechaPrevistaCierre, TbProyectosEdiciones.IDEdicion,
                       TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion,
                       TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad
                FROM TbProyectos 
                INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                WHERE NOT (TbProyectos.ParaInformeAvisos = 'No')
                AND TbProyectos.FechaCierre IS NULL
                AND TbProyectosEdiciones.FechaPublicacion IS NULL
                AND TbProyectos.NombreUsuarioCalidad = ?
                AND TbProyectosEdiciones.FechaMaxProximaPublicacion < ?
            """
            
            # Ejecutar consulta y calcular días en Python
            result = self._execute_query_with_error_logging(
                query, 
                params=(member_name, current_date),
                context=f"_get_expired_editions_data - member_name: {member_name}"
            ) or []
            
            for row in result:
                row['Dias'] = self._calculate_days_difference(row.get('FechaMaxProximaPublicacion'))
            
            return result
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo ediciones caducadas: {e}")
            return []
    
    def _get_risks_to_reclassify_data(self, member_name: str) -> List[Dict]:
        """Obtiene riesgos para retipificar asignados a un miembro de calidad."""
        try:
            query = """
                SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                       TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, TbRiesgos.FechaRiesgoParaRetipificar, 
                       TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                      LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                      INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                      ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                WHERE TbRiesgos.FechaRiesgoParaRetipificar IS NOT NULL
                      AND TbUsuariosAplicaciones_1.Nombre = ?
                      AND TbProyectos.ParaInformeAvisos <> 'No'
                      AND TbProyectos.FechaCierre IS NULL
                      AND TbProyectosEdiciones.FechaPublicacion IS NULL
                      AND TbRiesgos.Mitigacion <> 'Aceptar'
                      AND TbRiesgos.FechaRetirado IS NULL
            """
            return self._execute_query_with_error_logging(
                query, 
                params=(member_name,),
                context=f"_get_risks_to_reclassify_data - member_name: {member_name}"
            ) or []
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo riesgos para retipificar: {e}")
            return []
    
    def _get_accepted_risks_to_approve_data(self, member_name: str) -> List[Dict]:
        """Obtiene riesgos aceptados pendientes de visar por un miembro de calidad."""
        try:
            query = """
                SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                       TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, TbRiesgos.FechaJustificacionAceptacionRiesgo, 
                       TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                      LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                      INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                      ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                WHERE TbRiesgos.FechaJustificacionAceptacionRiesgo IS NOT NULL
                      AND TbUsuariosAplicaciones_1.Nombre = ?
                      AND TbProyectos.ParaInformeAvisos <> 'No'
                      AND TbProyectos.FechaCierre IS NULL
                      AND TbProyectosEdiciones.FechaPublicacion IS NULL
                      AND TbRiesgos.FechaAprobacionAceptacionPorCalidad IS NULL
                      AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NULL
            """
            return self._execute_query_with_error_logging(
                query, 
                params=(member_name,),
                context=f"_get_accepted_risks_to_approve_data - member_name: {member_name}"
            ) or []
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo riesgos aceptados por visar: {e}")
            return []
    
    def _get_retired_risks_to_approve_data(self, member_name: str) -> List[Dict]:
        """Obtiene riesgos retirados pendientes de visar por un miembro de calidad."""
        try:
            query = """
                SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                       TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, TbRiesgos.FechaJustificacionRetiroRiesgo, 
                       TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                      LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                      INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                      ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto
                WHERE TbRiesgos.FechaJustificacionRetiroRiesgo IS NOT NULL
                      AND TbUsuariosAplicaciones_1.Nombre = ?
                      AND TbProyectos.ParaInformeAvisos <> 'No'
                      AND TbProyectos.FechaCierre IS NULL
                      AND TbProyectosEdiciones.FechaPublicacion IS NULL
                      AND TbRiesgos.FechaAprobacionRetiroPorCalidad IS NULL
                      AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NULL
            """
            return self._execute_query_with_error_logging(
                query, 
                params=(member_name,),
                context=f"_get_retired_risks_to_approve_data - member_name: {member_name}"
            ) or []
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo riesgos retirados por visar: {e}")
            return []
    
    def _get_materialized_risks_to_decide_data(self, member_name: str) -> List[Dict]:
        """Obtiene riesgos materializados pendientes de decisión por un miembro de calidad."""
        try:
            query = """
                SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, 
                       TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, TbRiesgos.FechaMaterializado, 
                       TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad
                FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                       LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                       INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                       ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) 
                       INNER JOIN TbRiesgosNC ON TbRiesgos.IDRiesgo = TbRiesgosNC.IDRiesgo
                WHERE TbRiesgos.FechaMaterializado IS NOT NULL
                      AND TbUsuariosAplicaciones_1.Nombre = ?
                      AND TbProyectos.ParaInformeAvisos <> 'No'
                      AND TbProyectos.FechaCierre IS NULL
                      AND TbRiesgosNC.FechaDecison IS NULL
            """
            return self._execute_query_with_error_logging(
                query, 
                params=(member_name,),
                context=f"_get_materialized_risks_to_decide_data - member_name: {member_name}"
            ) or []
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"🚨 ERROR #{self.error_count} obteniendo riesgos materializados: {e}")
            return []
            
    def _get_accepted_risks_pending_approval_data(self) -> List[Dict]:
        """
        Obtiene todos los riesgos aceptados pendientes de aprobación por calidad.
        Esta función es similar a _get_accepted_risks_to_approve_data pero sin filtrar por miembro de calidad.
        
        Returns:
            Lista de diccionarios con los datos de los riesgos aceptados pendientes de aprobación
        """
        try:
            query = """
                SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbProyectosEdiciones.Edicion,
                       TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, 
                       TbRiesgos.FechaJustificacionAceptacionRiesgo, TbRiesgos.JustificacionAceptacionRiesgo,
                       TbUsuariosAplicaciones.Nombre AS ResponsableTecnico,
                       TbUsuariosAplicaciones_1.Nombre AS ResponsableCalidad
                FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                       LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                       INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                       ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto))
                       LEFT JOIN TbUsuariosAplicaciones ON TbRiesgos.ResponsableTecnico = TbUsuariosAplicaciones.UsuarioRed
                WHERE TbRiesgos.FechaJustificacionAceptacionRiesgo IS NOT NULL
                      AND NOT (TbProyectos.ParaInformeAvisos = 'No')
                      AND TbProyectos.FechaCierre IS NULL
                      AND TbProyectosEdiciones.FechaPublicacion IS NULL
                      AND TbRiesgos.FechaAprobacionAceptacionPorCalidad IS NULL
                      AND TbRiesgos.FechaRechazoAceptacionPorCalidad IS NULL
            """
            result = self._execute_query_with_error_logging(
                query, 
                params=(),
                context="get_accepted_risks_pending_approval_data"
            ) or []
            
            # Mapear campos para que coincidan con la configuración de tabla
            for row in result:
                row['FechaAceptacion'] = row.get('FechaJustificacionAceptacionRiesgo')
                row['UsuarioCalidad'] = row.get('ResponsableCalidad')
                # Calcular días desde la fecha de aceptación
                if row.get('FechaAceptacion'):
                    row['Dias'] = self._calculate_days_difference(row['FechaAceptacion'])
                else:
                    row['Dias'] = 0
            
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo riesgos aceptados pendientes de aprobación: {e}")
            return []
            
    def _get_retired_risks_pending_approval_data(self) -> List[Dict]:
        """
        Obtiene todos los riesgos retirados pendientes de aprobación por calidad.
        Esta función es similar a _get_retired_risks_to_approve_data pero sin filtrar por miembro de calidad.
        
        Returns:
            Lista de diccionarios con los datos de los riesgos retirados pendientes de aprobación
        """
        try:
            query = """
                SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbProyectosEdiciones.Edicion,
                       TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, 
                       TbRiesgos.FechaJustificacionRetiroRiesgo, TbRiesgos.JustificacionRetiroRiesgo,
                       TbUsuariosAplicaciones.Nombre AS ResponsableTecnico,
                       TbUsuariosAplicaciones_1.Nombre AS ResponsableCalidad
                FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                       LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                       INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                       ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto))
                       LEFT JOIN TbUsuariosAplicaciones ON TbRiesgos.ResponsableTecnico = TbUsuariosAplicaciones.UsuarioRed
                WHERE TbRiesgos.FechaJustificacionRetiroRiesgo IS NOT NULL
                      AND NOT (TbProyectos.ParaInformeAvisos = 'No')
                      AND TbProyectos.FechaCierre IS NULL
                      AND TbProyectosEdiciones.FechaPublicacion IS NULL
                      AND TbRiesgos.FechaAprobacionRetiroPorCalidad IS NULL
                      AND TbRiesgos.FechaRechazoRetiroPorCalidad IS NULL
            """
            result = self._execute_query_with_error_logging(
                query, 
                params=(),
                context="get_retired_risks_pending_approval_data"
            ) or []
            
            # Mapear campos para que coincidan con la configuración de tabla
            for row in result:
                row['FechaRetirada'] = row.get('FechaJustificacionRetiroRiesgo')
                row['UsuarioCalidad'] = row.get('ResponsableCalidad')
                # Calcular días desde la fecha de retirada
                if row.get('FechaRetirada'):
                    row['Dias'] = self._calculate_days_difference(row['FechaRetirada'])
                else:
                    row['Dias'] = 0
            
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo riesgos retirados pendientes de aprobación: {e}")
            return []
            
    def _get_materialized_risks_pending_decision_data(self) -> List[Dict]:
        """
        Obtiene todos los riesgos materializados pendientes de decisión.
        Esta función es similar a _get_materialized_risks_to_decide_data pero sin filtrar por miembro de calidad.
        
        Returns:
            Lista de diccionarios con los datos de los riesgos materializados pendientes de decisión
        """
        try:
            query = """
                SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbProyectosEdiciones.Edicion,
                       TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, 
                       TbRiesgos.FechaMaterializado AS FechaMaterializacion, TbRiesgos.DescripcionMaterializacion,
                       TbUsuariosAplicaciones.Nombre AS ResponsableTecnico,
                       TbUsuariosAplicaciones_1.Nombre AS ResponsableCalidad
                FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                       LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) 
                       INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) 
                       ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) 
                       INNER JOIN TbRiesgosNC ON TbRiesgos.IDRiesgo = TbRiesgosNC.IDRiesgo)
                       LEFT JOIN TbUsuariosAplicaciones ON TbRiesgos.ResponsableTecnico = TbUsuariosAplicaciones.UsuarioRed
                WHERE TbRiesgos.FechaMaterializado IS NOT NULL
                      AND NOT (TbProyectos.ParaInformeAvisos = 'No')
                      AND TbProyectos.FechaCierre IS NULL
                      AND TbRiesgosNC.FechaDecison IS NULL
            """
            result = self._execute_query_with_error_logging(
                query, 
                params=(),
                context="get_materialized_risks_pending_decision_data"
            ) or []
            
            # Mapear campos para que coincidan con la configuración de tabla
            for row in result:
                row['UsuarioCalidad'] = row.get('ResponsableCalidad')
                # Calcular días desde la fecha de materialización
                if row.get('FechaMaterializacion'):
                    row['Dias'] = self._calculate_days_difference(row['FechaMaterializacion'])
                else:
                    row['Dias'] = 0
            
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo riesgos materializados pendientes de decisión: {e}")
            return []
    
    # Métodos para datos mensuales
    
    def _get_all_editions_ready_for_publication_data(self) -> List[Dict]:
        """Obtiene todas las ediciones preparadas para publicar."""
        try:
            query = """
                SELECT DISTINCT TbExpedientes1.Nemotecnico, TbProyectosEdiciones.IDEdicion, 
                       TbProyectosEdiciones.Edicion, TbProyectos.FechaMaxProximaPublicacion, 
                       TbProyectosEdiciones.FechaPreparadaParaPublicar,
                       TbUsuariosAplicaciones.Nombre AS NombreUsuarioCalidad 
                FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) 
                      INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) 
                      LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
                WHERE NOT (TbProyectos.ParaInformeAvisos = 'No')
                       AND TbProyectos.FechaCierre IS NULL
                       AND TbProyectosEdiciones.FechaPublicacion IS NULL
                       AND TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha IS NULL
                ORDER BY TbProyectos.FechaMaxProximaPublicacion
            """
            
            # Ejecutar consulta y calcular días en Python
            result = self._execute_query_with_error_logging(
                query, 
                params=(),
                context="get_all_editions_ready_for_publication_data"
            ) or []
            for row in result:
                row['Dias'] = self._calculate_days_difference(row.get('FechaMaxProximaPublicacion'))
            
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo todas las ediciones preparadas: {e}")
            return []
    
    def _get_active_editions_data(self) -> List[Dict]:
        """Obtiene todas las ediciones activas."""
        try:
            query = """
                SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,
                       TbProyectos.FechaPrevistaCierre, TbProyectosEdiciones.IDEdicion,
                       TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion, 
                       TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad
                FROM TbProyectos INNER JOIN TbProyectosEdiciones 
                     ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto 
                WHERE NOT (TbProyectos.ParaInformeAvisos = 'No')
                       AND TbProyectos.FechaCierre IS NULL
                       AND TbProyectosEdiciones.FechaPublicacion IS NULL
            """
            
            # Ejecutar consulta y calcular días en Python
            result = self._execute_query_with_error_logging(
                query, 
                params=(),
                context="get_active_editions_data"
            ) or []
            for row in result:
                row['Días'] = self._calculate_days_difference(row.get('FechaMaxProximaPublicacion'))
            
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo ediciones activas: {e}")
            return []
    
    def _get_closed_editions_last_month_data(self) -> List[Dict]:
        """Obtiene ediciones cerradas en el último mes."""
        try:
            # Calcular fecha de hace 30 días
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            query = """
                SELECT TbProyectosEdiciones.IDEdicion, TbProyectos.Proyecto, TbProyectos.NombreProyecto, 
                       TbProyectos.Juridica, TbProyectos.FechaCierre, TbProyectos.NombreUsuarioCalidad 
                FROM TbProyectos INNER JOIN TbProyectosEdiciones 
                     ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto 
                WHERE NOT (TbProyectos.ParaInformeAvisos = 'No')
                       AND TbProyectos.FechaCierre IS NOT NULL
                       AND TbProyectosEdiciones.FechaPublicacion IS NULL
                       AND TbProyectos.FechaCierre >= ?
            """
            result = self._execute_query_with_error_logging(
                query, 
                params=(thirty_days_ago,),
                context="get_closed_editions_last_month_data"
            ) or []
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo ediciones cerradas en el último mes: {e}")
            return []
    
    # Métodos para informe mensual - FUNCIÓN DUPLICADA, ELIMINAR
    # Esta función está duplicada con execute_monthly_quality_task
    # Se mantiene temporalmente para compatibilidad
    
    # La función execute_monthly_report ha sido eliminada porque era una duplicación de execute_monthly_quality_task
    # y tenía llamadas a funciones con un número incorrecto de argumentos

    # ========== FUNCIONES DE GENERACIÓN DE TABLAS REFACTORIZADAS ==========
    # Las funciones hardcodeadas han sido eliminadas y reemplazadas por el sistema genérico
    # Todas las tablas ahora se generan usando self.generate_table_html(data, 'table_type')
    

    

    


    # ========== FUNCIONES FALTANTES PARA MIEMBROS DE CALIDAD ==========
    

    

    

        
    # Funciones hardcodeadas de generación de tablas HTML eliminadas
    # Ahora se utiliza el sistema genérico de generación de tablas
    
    def _generate_editions_need_publication_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para ediciones que necesitan propuesta de publicación.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('editions_need_publication')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_editions_with_rejected_proposals_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para ediciones con propuestas de publicación rechazadas.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('editions_with_rejected_proposals')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_accepted_risks_unmotivated_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para riesgos aceptados sin justificación.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('accepted_risks_unmotivated')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_accepted_risks_rejected_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para riesgos aceptados rechazados por calidad.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('accepted_risks_rejected')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_retired_risks_unmotivated_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para riesgos retirados sin justificación.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('retired_risks_unmotivated')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_retired_risks_rejected_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para riesgos retirados rechazados por calidad.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('retired_risks_rejected')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_mitigation_actions_reschedule_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para acciones de mitigación que necesitan replanificación.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('mitigation_actions_reschedule')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    def _generate_contingency_actions_reschedule_table(self, data: List[Dict]) -> str:
        """
        Genera tabla HTML para acciones de contingencia que necesitan replanificación.
        Utiliza la función genérica con configuración predefinida.
        """
        config = self._get_table_configuration('contingency_actions_reschedule')
        return self._generate_generic_table(data, config['title'], config['columns'])
    
    # La función _generate_contingency_tasks_table ha sido eliminada porque solo era utilizada por execute_monthly_report,
    # que era una duplicación de execute_monthly_quality_task
    
    # La función _generate_no_recent_review_table ha sido eliminada porque solo era utilizada por execute_monthly_report,
    # que era una duplicación de execute_monthly_quality_task
    
    def _generate_generic_table(self, data: List[Dict], title: str, columns: List[Dict[str, str]], 
                               table_class: str = "tabla", header_class: str = "cabecera") -> str:
        """
        Genera tabla HTML genérica mejorada para cualquier tipo de datos.
        
        Args:
            data: Lista de diccionarios con los datos
            title: Título de la tabla
            columns: Lista de diccionarios con información de columnas
                    Cada diccionario debe tener:
                    - 'header': Texto del encabezado
                    - 'field': Campo del diccionario de datos
                    - 'format': (opcional) 'date', 'days', 'css_days' para formatear
                    - 'css_class': (opcional) clase CSS adicional para la celda
            table_class: Clase CSS para la tabla
            header_class: Clase CSS para el encabezado
            
        Returns:
            HTML de la tabla
        """
        if not data:
            return ""
        
        html = f"""
        <div>
            <h3>{title.upper()} ({len(data)})</h3>
            <table class="{table_class}">
                <tr class="{header_class}">
        """
        
        # Generar encabezados
        for column in columns:
            html += f"<th>{column['header']}</th>"
        
        html += "</tr>"
        
        # Generar filas de datos
        for row in data:
            html += "<tr>"
            for column in columns:
                field_value = row.get(column['field'], '')
                css_class = column.get('css_class', '')
                
                # Aplicar formato según el tipo
                if column.get('format') == 'date':
                    formatted_value = format_date(field_value)
                elif column.get('format') == 'days' and str(field_value).lstrip('-').isdigit():
                    # Aplicar estilo especial para días
                    days = int(field_value)
                    if days <= 0:
                        formatted_value = f'<span style="color: red; font-weight: bold;">{field_value}</span>'
                    elif days <= 7:
                        formatted_value = f'<span style="color: orange; font-weight: bold;">{field_value}</span>'
                    else:
                        formatted_value = str(field_value)
                elif column.get('format') == 'css_days' and str(field_value).lstrip('-').isdigit():
                    # Usar la función de clase CSS para días
                    days = int(field_value)
                    css_days_class = self._get_css_class_for_days(days)
                    formatted_value = f'<span class="{css_days_class}">{field_value}</span>'
                else:
                    formatted_value = str(field_value) if field_value is not None else ''
                
                # Aplicar clase CSS adicional si se especifica
                cell_class = f' class="{css_class}"' if css_class else ''
                html += f"<td{cell_class}>{formatted_value}</td>"
            html += "</tr>"
        
        html += """
            </table>
        </div>
        <br>
        """
        
        return html
    
    def _get_table_configuration(self, table_type: str) -> Dict:
        """
        Obtiene la configuración de columnas para diferentes tipos de tablas.
        
        Args:
            table_type: Tipo de tabla
            
        Returns:
            Diccionario con título y configuración de columnas
        """
        configurations = {
            'editions_need_publication': {
                'title': 'Ediciones que necesitan propuesta de publicación',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Últ Ed', 'field': 'Edicion'},
                    {'header': 'Fecha Máx.Próx Ed.', 'field': 'FechaMaxProximaPublicacion', 'format': 'date'},
                    {'header': 'Propuesta para Publicación', 'field': 'FechaPreparadaParaPublicar', 'format': 'date'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'},
                    {'header': 'Faltan (días)', 'field': 'Dias', 'format': 'css_days'}
                ]
            },
            'editions_with_rejected_proposals': {
                'title': 'Ediciones con propuestas de publicación rechazadas',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Últ Ed', 'field': 'Edicion'},
                    {'header': 'Fecha Máx.Próx Ed.', 'field': 'FechaMaxProximaPublicacion', 'format': 'date'},
                    {'header': 'Propuesta para Publicación', 'field': 'FechaPreparadaParaPublicar', 'format': 'date'},
                    {'header': 'Fecha Rechazo', 'field': 'PropuestaRechazadaPorCalidadFecha', 'format': 'date'},
                    {'header': 'Motivo Rechazo', 'field': 'PropuestaRechazadaPorCalidadMotivo'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'}
                ]
            },
            'accepted_risks_unmotivated': {
                'title': 'Riesgos aceptados sin justificación',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Código Riesgo', 'field': 'CodigoRiesgo'},
                    {'header': 'Descripción', 'field': 'Descripcion'},
                    {'header': 'Causa Raíz', 'field': 'CausaRaiz'},
                    {'header': 'Fecha Aceptación', 'field': 'FechaAceptacion', 'format': 'date'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'}
                ]
            },
            'accepted_risks_rejected': {
                'title': 'Riesgos aceptados rechazados por calidad',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Código Riesgo', 'field': 'CodigoRiesgo'},
                    {'header': 'Descripción', 'field': 'Descripcion'},
                    {'header': 'Causa Raíz', 'field': 'CausaRaiz'},
                    {'header': 'Fecha Rechazo', 'field': 'FechaRechazoAceptacionPorCalidad', 'format': 'date'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'}
                ]
            },
            'retired_risks_unmotivated': {
                'title': 'Riesgos retirados sin justificación',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Código Riesgo', 'field': 'CodigoRiesgo'},
                    {'header': 'Descripción', 'field': 'Descripcion'},
                    {'header': 'Causa Raíz', 'field': 'CausaRaiz'},
                    {'header': 'Fecha Retirado', 'field': 'FechaRetirado', 'format': 'date'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'}
                ]
            },
            'retired_risks_rejected': {
                'title': 'Riesgos retirados rechazados por calidad',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Código Riesgo', 'field': 'CodigoRiesgo'},
                    {'header': 'Descripción', 'field': 'Descripcion'},
                    {'header': 'Causa Raíz', 'field': 'CausaRaiz'},
                    {'header': 'Fecha Retirado', 'field': 'FechaRetirado', 'format': 'date'},
                    {'header': 'Fecha Rechazo', 'field': 'FechaRechazoRetiroPorCalidad', 'format': 'date'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'}
                ]
            },
            'mitigation_actions_reschedule': {
                'title': 'Riesgos con acciones de mitigación para replanificar',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Código Riesgo', 'field': 'CodigoRiesgo'},
                    {'header': 'Descripción', 'field': 'Descripcion'},
                    {'header': 'Causa Raíz', 'field': 'CausaRaiz'},
                    {'header': 'Disparador', 'field': 'DisparadorDelPlan'},
                    {'header': 'Acción', 'field': 'Accion'},
                    {'header': 'Fecha Inicio', 'field': 'FechaInicio', 'format': 'date'},
                    {'header': 'Fecha Fin Prevista', 'field': 'FechaFinPrevista', 'format': 'date'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'}
                ]
            },
            'contingency_actions_reschedule': {
                'title': 'Riesgos con acciones de contingencia para replanificar',
                'columns': [
                    {'header': 'Proyecto', 'field': 'Nemotecnico'},
                    {'header': 'Código Riesgo', 'field': 'CodigoRiesgo'},
                    {'header': 'Descripción', 'field': 'Descripcion'},
                    {'header': 'Causa Raíz', 'field': 'CausaRaiz'},
                    {'header': 'Disparador', 'field': 'DisparadorDelPlan'},
                    {'header': 'Acción', 'field': 'Accion'},
                    {'header': 'Fecha Inicio', 'field': 'FechaInicio', 'format': 'date'},
                    {'header': 'Fecha Fin Prevista', 'field': 'FechaFinPrevista', 'format': 'date'},
                    {'header': 'Resp. Calidad', 'field': 'UsuarioCalidad'}
                ]
            }
        }
        
        return configurations.get(table_type, {
            'title': 'Tabla genérica',
            'columns': []
        })