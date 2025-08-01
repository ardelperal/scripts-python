#!/usr/bin/env python3
"""
Gestor AGEDYS - Gestión de facturas pendientes de visado técnico
Adaptación del script legacy AGEDYS.VBS a Python
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from common import config
from common.database import AccessDatabase
from common.utils import (
    generate_html_header, generate_html_footer, format_date, load_css_content,
    get_quality_emails_string, get_technical_emails_string, get_admin_emails_string,
    register_task_completion, should_execute_task, is_task_completed_today,
    send_notification_email, register_email_in_database
)

# Configuración
APP_ID = 3  # ID de aplicación AGEDYS según .env
TASK_FREQUENCY = 'daily'  # Frecuencia de ejecución

logger = logging.getLogger(__name__)

class LoggingHelper:
    """Helper para logging estructurado y consistente"""
    
    @staticmethod
    def log_phase_start(phase_name: str, details: str = ""):
        """Log del inicio de una fase del proceso"""
        separator = "=" * 60
        logger.info(f"\n{separator}")
        logger.info(f"🚀 INICIANDO: {phase_name.upper()}")
        if details:
            logger.info(f"   {details}")
        logger.info(f"{separator}")
    
    @staticmethod
    def log_phase_end(phase_name: str, success: bool = True, count: int = None):
        """Log del final de una fase del proceso"""
        status = "✅ COMPLETADO" if success else "❌ FALLIDO"
        count_info = f" ({count} elementos procesados)" if count is not None else ""
        logger.info(f"🏁 {status}: {phase_name.upper()}{count_info}")
    
    @staticmethod
    def log_query_execution(query_name: str, success: bool, result_count: int = None, error: str = None):
        """Log de ejecución de consultas SQL"""
        if success:
            count_info = f" - {result_count} registros" if result_count is not None else ""
            logger.debug(f"📊 Query '{query_name}' ejecutada exitosamente{count_info}")
        else:
            logger.warning(f"⚠️  Query '{query_name}' falló: {error}")
    
    @staticmethod
    def log_user_processing(operation_or_usuario: str, details_or_email: str = "", item_count: int = None, item_type: str = ""):
        """Log de procesamiento de usuario - compatible con múltiples firmas"""
        if item_count is not None and item_type:
            # Formato: usuario, email, count, type
            logger.info(f"👤 Procesando {operation_or_usuario} ({details_or_email}) - {item_count} {item_type}")
        else:
            # Formato: usuario, detalles
            logger.info(f"👤 {operation_or_usuario}: {details_or_email}")
    
    @staticmethod
    def log_email_action(operation: str, usuario: str, email: str, action_or_count: str, details: str = "", dry_run: bool = False):
        """Log de acciones de email - compatible con múltiples firmas"""
        if isinstance(action_or_count, int):
            # Formato antiguo: action, usuario, email, count, item_type, dry_run
            mode = "🧪 DRY-RUN" if dry_run else "📧 EMAIL"
            action_text = "registrado" if operation == "register" else operation
            logger.info(f"{mode}: {action_text.capitalize()} para {usuario} ({email}) - {action_or_count} {details}")
        else:
            # Formato nuevo: operation, usuario, email, action, details
            action_icon = "🧪" if action_or_count == "DRY-RUN" else "📧"
            details_info = f" - {details}" if details else ""
            logger.info(f"{action_icon} {operation}: {action_or_count} para {usuario} ({email}){details_info}")
    
    @staticmethod
    def log_database_error(operation: str, context: str, error: str):
        """Log de errores de base de datos"""
        logger.error(f"🔴 Error BD en {operation} ({context}): {error}")
    
    @staticmethod
    def log_fallback_action(reason: str, action: str):
        """Log de acciones de respaldo"""
        logger.warning(f"🔄 Fallback activado - {reason}. Acción: {action}")
    
    @staticmethod
    def log_skip_action(reason: str, context: str = ""):
        """Log de acciones omitidas"""
        context_info = f" ({context})" if context else ""
        logger.info(f"⏭️  Omitiendo{context_info}: {reason}")
    
    @staticmethod
    def log_skipped_action(operation: str, context: str, reason: str):
        """Log de acciones omitidas con más detalle"""
        logger.info(f"⏭️  {operation} omitido ({context}): {reason}")
    
    @staticmethod
    def log_system_status(component: str, status: str, details: str = ""):
        """Log de estado del sistema"""
        status_icon = "🟢" if "exitosamente" in status or "completado" in status else "🟡" if "DRY-RUN" in status else "🔴"
        details_info = f" - {details}" if details else ""
        logger.info(f"{status_icon} {component}: {status}{details_info}")


class AgedysManager:
    """Gestor principal para las tareas de AGEDYS"""
    
    def __init__(self):
        # Obtener la cadena de conexión para AGEDYS desde config
        agedys_connection_string = config.get_db_agedys_connection_string()
        self.db = AccessDatabase(agedys_connection_string)
        
        # Conexión a la base de datos de tareas para consultas de usuarios y registro de correos
        tareas_connection_string = config.get_db_tareas_connection_string()
        self.tareas_db = AccessDatabase(tareas_connection_string)
        
        # Para AGEDYS, usar la base de datos de tareas para registrar correos (como otros run_ scripts)
        self.correos_db = self.tareas_db
        
        self.css_content = load_css_content(config.css_file_path)
        
    def get_usuarios_facturas_pendientes_visado_tecnico(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con facturas pendientes de visado técnico"""
        LoggingHelper.log_phase_start("Obtención de usuarios con facturas pendientes", 
                                    "Ejecutando 4 consultas principales + fallback si es necesario")
        
        usuarios_dict = {}
        
        # Definir las consultas con nombres descriptivos - USANDO ACENTOS COMO EN EL LEGACY VBS
        queries = {
            "peticionarios_con_visado": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM ((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle INNER JOIN TbVisadoFacturas_Nueva 
                ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
                INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
                INNER JOIN TbUsuariosAplicaciones ON TbProyectos.PETICIONARIO = TbUsuariosAplicaciones.Nombre 
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
                AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL 
                AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL 
                AND TbExpedientes.AGEDYSGenerico = 'Sí' 
                AND TbExpedientes.AGEDYSAplica = 'Sí'
            """,
            "responsables_sin_visado_generico_si": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle 
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
                INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
                LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
                INNER JOIN TbExpedientesResponsables ON TbExpedientes.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id 
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
                AND TbVisadoFacturas_Nueva.IDFactura IS NULL 
                AND TbExpedientes.AGEDYSGenerico = 'Sí' 
                AND TbExpedientes.AGEDYSAplica = 'Sí' 
                AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            """,
            "responsables_con_visado_generico_no": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM (((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle 
                INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
                INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
                INNER JOIN TbExpedientesResponsables ON TbExpedientes.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id 
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
                AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL 
                AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL 
                AND TbExpedientes.AGEDYSGenerico = 'No' 
                AND TbExpedientes.AGEDYSAplica = 'Sí' 
                AND TbExpedientesResponsables.CorreoSiempre = 'Sí'
            """,
            "responsables_sin_visado_generico_no": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle 
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
                INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
                INNER JOIN TbExpedientesResponsables ON TbExpedientes.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id 
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
                AND TbVisadoFacturas_Nueva.IDFactura IS NULL 
                AND TbExpedientes.AGEDYSGenerico = 'No' 
                AND TbExpedientes.AGEDYSAplica = 'Sí'
            """
        }
        
        query_fallback = """
            SELECT DISTINCT TbProyectos.PETICIONARIO as UsuarioRed 
            FROM ((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle 
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
            INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
            LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura 
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
            AND TbVisadoFacturas_Nueva.IDFactura IS NULL 
            AND TbExpedientes.AGEDYSGenerico = 'Sí' 
            AND TbExpedientes.AGEDYSAplica = 'Sí'
        """
        
        try:
            # Ejecutar las consultas principales
            for query_name, query_sql in queries.items():
                try:
                    usuarios = self.db.execute_query(query_sql)
                    LoggingHelper.log_query_execution(query_name, True, len(usuarios))
                    
                    for usuario in usuarios:
                        usuario_red = usuario['UsuarioRed']
                        correo_usuario = usuario.get('CorreoUsuario')
                        if usuario_red not in usuarios_dict and correo_usuario:
                            usuarios_dict[usuario_red] = {
                                'UsuarioRed': usuario_red,
                                'CorreoUsuario': correo_usuario
                            }
                except Exception as e:
                    LoggingHelper.log_query_execution(query_name, False, error=str(e))
                    
            # Si no se obtuvieron usuarios, usar query alternativa
            if not usuarios_dict:
                LoggingHelper.log_fallback_action(
                    "No se obtuvieron usuarios con TbUsuariosAplicaciones", 
                    "Usando query alternativa"
                )
                try:
                    usuarios = self.db.execute_query(query_fallback)
                    LoggingHelper.log_query_execution("fallback_peticionarios", True, len(usuarios))
                    
                    for usuario in usuarios:
                        usuario_red = usuario['UsuarioRed']
                        if usuario_red not in usuarios_dict:
                            # Para el fallback, necesitamos obtener el correo de TbUsuariosAplicaciones
                            try:
                                correo_query = f"SELECT CorreoUsuario FROM TbUsuariosAplicaciones WHERE Nombre = '{usuario_red}'"
                                correo_result = self.db.execute_query(correo_query)
                                if correo_result and correo_result[0].get('CorreoUsuario'):
                                    usuarios_dict[usuario_red] = {
                                        'UsuarioRed': usuario_red,
                                        'CorreoUsuario': correo_result[0]['CorreoUsuario']
                                    }
                            except Exception as correo_error:
                                LoggingHelper.log_query_execution(f"correo_lookup_{usuario_red}", False, error=str(correo_error))
                except Exception as e2:
                    LoggingHelper.log_database_error("query_fallback", "usuarios_facturas_pendientes", str(e2))
                    
            LoggingHelper.log_phase_end("Obtención de usuarios con facturas pendientes", True, len(usuarios_dict))
            return list(usuarios_dict.values())
            
        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_facturas_pendientes", "proceso_completo", str(e))
            LoggingHelper.log_phase_end("Obtención de usuarios con facturas pendientes", False)
            return []
    
    def get_facturas_pendientes_visado_tecnico(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene facturas pendientes de visado técnico para un usuario"""
        LoggingHelper.log_user_processing(usuario, "Iniciando obtención de facturas pendientes")
        
        # Primero obtener el ID del usuario
        try:
            user_query = f"SELECT Id FROM TbUsuariosAplicaciones WHERE UsuarioRed = '{usuario}'"
            user_result = self.db.execute_query(user_query)
            if not user_result:
                LoggingHelper.log_skipped_action(f"Usuario {usuario} no encontrado en TbUsuariosAplicaciones", 
                                               "Solo se ejecutarán queries 3 y 4")
                user_id = None
            else:
                user_id = user_result[0]['Id']
        except Exception as e:
            LoggingHelper.log_database_error("user_lookup", usuario, str(e))
            user_id = None
        
        # Definir las consultas con nombres descriptivos - USANDO ACENTOS COMO EN EL LEGACY VBS
        queries = {}
        
        if user_id is not None:
            queries["responsable_con_visado_generico_no"] = f"""
                SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, 
                       TbExpedientes.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, 
                       TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO 
                FROM (((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle 
                INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
                INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
                INNER JOIN TbExpedientesResponsables ON TbExpedientes.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
                AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL 
                AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL 
                AND TbExpedientes.AGEDYSGenerico = 'No' 
                AND TbExpedientes.AGEDYSAplica = 'Sí' 
                AND TbExpedientesResponsables.CorreoSiempre = 'Sí' 
                AND TbExpedientesResponsables.IdUsuario = {user_id}
            """
            
            queries["responsable_sin_visado_generico_no"] = f"""
                SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, 
                       TbExpedientes.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, 
                       TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO 
                FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle 
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
                INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
                INNER JOIN TbExpedientesResponsables ON TbExpedientes.IDExpediente = TbExpedientesResponsables.IdExpediente) 
                LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
                INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
                AND TbVisadoFacturas_Nueva.IDFactura IS NULL 
                AND TbExpedientes.AGEDYSGenerico = 'No' 
                AND TbExpedientes.AGEDYSAplica = 'Sí' 
                AND TbExpedientesResponsables.CorreoSiempre = 'Sí' 
                AND TbExpedientesResponsables.IdUsuario = {user_id}
            """
        
        # Estas queries siempre se ejecutan - USANDO ACENTOS COMO EN EL LEGACY VBS
        queries["peticionario_con_visado_generico_si"] = f"""
            SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, 
                   TbExpedientes.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, 
                   TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO 
            FROM ((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle 
            INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
            INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
            INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
            AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL 
            AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL 
            AND TbExpedientes.AGEDYSGenerico = 'Sí' 
            AND TbExpedientes.AGEDYSAplica = 'Sí' 
            AND TbProyectos.PETICIONARIO = '{usuario}'
        """
        
        queries["peticionario_sin_visado_generico_si"] = f"""
            SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, 
                   TbExpedientes.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, 
                   TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO 
            FROM (((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle 
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
            INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IDExpediente) 
            LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) 
            INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL 
            AND TbVisadoFacturas_Nueva.IDFactura IS NULL 
            AND TbExpedientes.AGEDYSGenerico = 'Sí' 
            AND TbExpedientes.AGEDYSAplica = 'Sí' 
            AND TbProyectos.PETICIONARIO = '{usuario}'
        """
        
        facturas_list = []
        
        try:
            for query_name, query_sql in queries.items():
                try:
                    facturas = self.db.execute_query(query_sql)
                    LoggingHelper.log_query_execution(f"{query_name}_{usuario}", True, len(facturas))
                    facturas_list.extend(facturas)
                except Exception as e:
                    LoggingHelper.log_query_execution(f"{query_name}_{usuario}", False, error=str(e))
            
            # Eliminar duplicados basándose en NFactura
            facturas_unicas = {}
            for factura in facturas_list:
                key = factura.get('NFactura', '')
                if key not in facturas_unicas:
                    facturas_unicas[key] = factura
            
            facturas_result = list(facturas_unicas.values())
            LoggingHelper.log_user_processing(usuario, f"Facturas obtenidas: {len(facturas_result)}")
            return facturas_result
            
        except Exception as e:
            LoggingHelper.log_database_error("get_facturas_pendientes", usuario, str(e))
            return []
    
    def get_usuarios_dpds_sin_visado(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con DPDs sin visado"""
        LoggingHelper.log_phase_start("Obtención de usuarios con DPDs sin visado")
        
        usuarios_dict = {}        
        # Query principal - Sin acentos para evitar problemas de codificación
        query_responsables = """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
            FROM ((((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) 
            INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) INNER JOIN TbExpedientesResponsables 
            ON TbExpedientes.IdExpediente = TbExpedientesResponsables.IdExpediente) INNER JOIN TbUsuariosAplicaciones 
            ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) LEFT JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
            WHERE TbProyectos.ELIMINADO = False 
            AND TbSolicitudesOfertasPrevias.DPD IS NULL 
            AND TbExpedientes.AGEDYSGenerico <> 'Si' 
            AND TbExpedientes.AGEDYSAplica = 'Si' 
            AND TbProyectos.CODCONTRATOGTV IS NULL 
            AND TbSuministradoresSAP.IDSuministrador IS NULL
        """
        
        # Query fallback - Sin acentos para evitar problemas de codificación
        query_peticionarios = """
            SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
            FROM (((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) 
            INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) LEFT JOIN TbSuministradoresSAP 
            ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) INNER JOIN TbUsuariosAplicaciones ON TbProyectos.PETICIONARIO = TbUsuariosAplicaciones.Nombre 
            WHERE TbProyectos.ELIMINADO = False 
            AND TbSolicitudesOfertasPrevias.DPD IS NULL 
            AND TbExpedientes.AGEDYSGenerico <> 'Si' 
            AND TbProyectos.CODCONTRATOGTV IS NULL 
            AND TbSuministradoresSAP.IDSuministrador IS NULL
        """
        
        try:
            # Ejecutar query de responsables
            try:
                usuarios = self.db.execute_query(query_responsables)
                LoggingHelper.log_query_execution("responsables_dpds_sin_visado", True, len(usuarios))
                
                for usuario in usuarios:
                    usuario_red = usuario['UsuarioRed']
                    correo_usuario = usuario.get('CorreoUsuario')
                    if usuario_red not in usuarios_dict and correo_usuario:
                        usuarios_dict[usuario_red] = {
                            'UsuarioRed': usuario_red,
                            'CorreoUsuario': correo_usuario
                        }
            except Exception as e:
                LoggingHelper.log_query_execution("responsables_dpds_sin_visado", False, error=str(e))
            
            # Ejecutar query de peticionarios
            try:
                usuarios = self.db.execute_query(query_peticionarios)
                LoggingHelper.log_query_execution("peticionarios_dpds_sin_visado", True, len(usuarios))
                
                for usuario in usuarios:
                    usuario_red = usuario['UsuarioRed']
                    correo_usuario = usuario.get('CorreoUsuario')
                    if usuario_red not in usuarios_dict and correo_usuario:
                        usuarios_dict[usuario_red] = {
                            'UsuarioRed': usuario_red,
                            'CorreoUsuario': correo_usuario
                        }
            except Exception as e:
                LoggingHelper.log_query_execution("peticionarios_dpds_sin_visado", False, error=str(e))
                
            LoggingHelper.log_phase_end("Obtención de usuarios con DPDs sin visado", True, len(usuarios_dict))
            return list(usuarios_dict.values())
            
        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_dpds_sin_visado", "proceso_completo", str(e))
            LoggingHelper.log_phase_end("Obtención de usuarios con DPDs sin visado", False)
            return []
    
    def get_dpds_sin_visado(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene DPDs sin visado para un usuario"""
        LoggingHelper.log_user_processing(usuario, "Iniciando obtención de DPDs sin visado")
        
        # Primero obtener el ID del usuario
        try:
            user_query = f"SELECT Id FROM TbUsuariosAplicaciones WHERE UsuarioRed = '{usuario}'"
            user_result = self.db.execute_query(user_query)
            if not user_result:
                LoggingHelper.log_skipped_action(f"Usuario {usuario} no encontrado en TbUsuariosAplicaciones", 
                                               "Solo se ejecutará query de peticionario")
                user_id = None
            else:
                user_id = user_result[0]['Id']
        except Exception as e:
            LoggingHelper.log_database_error("user_lookup", usuario, str(e))
            user_id = None
        
        dpds_list = []
        
        # Query para responsables (si tenemos ID) - Sin acentos para evitar problemas de codificación
        if user_id is not None:
            query_responsable = f"""
                SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes.CodExp, 
                       TbProyectos.DESCRIPCION, TbProyectos.IMPORTEADJUDICADO 
                FROM ((((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) 
                INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) INNER JOIN TbExpedientesResponsables 
                ON TbExpedientes.IdExpediente = TbExpedientesResponsables.IdExpediente) INNER JOIN TbUsuariosAplicaciones 
                ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) LEFT JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
                WHERE TbProyectos.ELIMINADO = False 
                AND TbSolicitudesOfertasPrevias.DPD IS NULL 
                AND TbExpedientes.AGEDYSGenerico <> 'Si' 
                AND TbExpedientes.AGEDYSAplica = 'Si' 
                AND TbProyectos.CODCONTRATOGTV IS NULL 
                AND TbSuministradoresSAP.IDSuministrador IS NULL 
                AND TbExpedientesResponsables.IdUsuario = {user_id}
            """
            
            try:
                dpds = self.db.execute_query(query_responsable)
                LoggingHelper.log_query_execution(f"responsable_dpds_{usuario}", True, len(dpds))
                dpds_list.extend(dpds)
            except Exception as e:
                LoggingHelper.log_query_execution(f"responsable_dpds_{usuario}", False, error=str(e))
        
        # Query para peticionarios - USANDO ACENTOS COMO EN EL LEGACY VBS
        query_peticionario = f"""
            SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes.CodExp, 
                   TbProyectos.DESCRIPCION, TbProyectos.IMPORTEADJUDICADO 
            FROM (((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) 
            INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) LEFT JOIN TbSuministradoresSAP 
            ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) INNER JOIN TbUsuariosAplicaciones ON TbProyectos.PETICIONARIO = TbUsuariosAplicaciones.Nombre 
            WHERE TbProyectos.ELIMINADO = False 
            AND TbSolicitudesOfertasPrevias.DPD IS NULL 
            AND TbExpedientes.AGEDYSGenerico <> 'Sí' 
            AND TbProyectos.CODCONTRATOGTV IS NULL 
            AND TbSuministradoresSAP.IDSuministrador IS NULL 
            AND TbProyectos.PETICIONARIO = '{usuario}'
        """
        
        try:
            dpds = self.db.execute_query(query_peticionario)
            LoggingHelper.log_query_execution(f"peticionario_dpds_{usuario}", True, len(dpds))
            dpds_list.extend(dpds)
        except Exception as e:
            LoggingHelper.log_query_execution(f"peticionario_dpds_{usuario}", False, error=str(e))
        
        # Eliminar duplicados basándose en CODPROYECTOS
        dpds_unicos = {}
        for dpd in dpds_list:
            key = dpd.get('CODPROYECTOS', '')
            if key not in dpds_unicos:
                dpds_unicos[key] = dpd
        
        dpds_result = list(dpds_unicos.values())
        LoggingHelper.log_user_processing(usuario, f"DPDs obtenidos: {len(dpds_result)}")
        return dpds_result
    
    def get_usuarios_economia(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios de economía usando la función común"""
        LoggingHelper.log_phase_start("Obtención de usuarios de economía")
        
        try:
            from common.utils import get_economy_users
            from common.config import config
            
            usuarios = get_economy_users(config, LoggingHelper.logger)
            LoggingHelper.log_query_execution("usuarios_economia", True, len(usuarios))
            LoggingHelper.log_phase_end("Obtención de usuarios de economía", True, len(usuarios))
            return usuarios
            
        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_economia", "proceso_completo", str(e))
            LoggingHelper.log_phase_end("Obtención de usuarios de economía", False)
            raise  # Re-lanzar la excepción para que se propague
    
    def get_dpds_sin_pedido(self) -> List[Dict[str, Any]]:
        """Obtiene DPDs sin pedido para economía"""
        LoggingHelper.log_phase_start("Obtención de DPDs sin pedido para economía")
        
        try:
            # Query para obtener DPDs sin pedido - USANDO ACENTOS COMO EN EL LEGACY VBS
            query = """
                SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes.CodExp, 
                       TbProyectos.DESCRIPCION, TbProyectos.IMPORTEADJUDICADO, TbSuministradoresSAP.Suministrador 
                FROM ((TbProyectos INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) 
                LEFT JOIN TbNPedido ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) 
                LEFT JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP 
                WHERE TbProyectos.ELIMINADO = False 
                AND TbNPedido.CODPPD IS NULL 
                AND TbExpedientes.AGEDYSAplica = 'Sí' 
                AND TbProyectos.CODCONTRATOGTV IS NULL 
                AND TbSuministradoresSAP.IDSuministrador IS NOT NULL
            """
            
            dpds = self.db.execute_query(query)
            LoggingHelper.log_query_execution("dpds_sin_pedido", True, len(dpds))
            LoggingHelper.log_phase_end("Obtención de DPDs sin pedido para economía", True, len(dpds))
            return dpds
            
        except Exception as e:
            LoggingHelper.log_database_error("get_dpds_sin_pedido", "proceso_completo", str(e))
            LoggingHelper.log_phase_end("Obtención de DPDs sin pedido para economía", False)
            raise  # Re-lanzar la excepción para que se propague
    
    def generate_html_table_facturas(self, facturas: List[Dict[str, Any]], titulo: str) -> str:
        """Genera tabla HTML para facturas"""
        if not facturas:
            return ""
        
        html = f"""
        <table>
            <tr>
                <td class="ColespanArriba" colspan="9">{titulo}</td>
            </tr>
            <tr>
                <td class="Cabecera">NFactura</td>
                <td class="Cabecera">NDOCUMENTO</td>
                <td class="Cabecera">DPD</td>
                <td class="Cabecera">PETICIONARIO</td>
                <td class="Cabecera">EXPEDIENTE</td>
                <td class="Cabecera">DESCRIPCIÓN</td>
                <td class="Cabecera">IMPORTE PEDIDO</td>
                <td class="Cabecera">SUMINISTRADOR</td>
                <td class="Cabecera">IMPORTE FACTURA</td>
            </tr>
        """
        
        for factura in facturas:
            importe_pedido = factura.get('IMPORTEADJUDICADO', '')
            if isinstance(importe_pedido, (int, float)):
                importe_pedido = f"{importe_pedido:.2f}€"
            
            importe_factura = factura.get('ImporteFactura', '')
            if isinstance(importe_factura, (int, float)):
                importe_factura = f"{importe_factura:.2f}€"
            
            html += f"""
            <tr>
                <td>{factura.get('NFactura', '')}</td>
                <td>{factura.get('NDOCUMENTO', '')}</td>
                <td>{factura.get('CODPROYECTOS', '')}</td>
                <td>{factura.get('PETICIONARIO', '')}</td>
                <td>{factura.get('CodExp', '')}</td>
                <td>{factura.get('DESCRIPCION', '')}</td>
                <td>{importe_pedido}</td>
                <td>{factura.get('Suministrador', '')}</td>
                <td>{importe_factura}</td>
            </tr>
            """
        
        html += "</table>\n"
        return html
    
    def generate_html_table_dpds(self, dpds: List[Dict[str, Any]], titulo: str) -> str:
        """Genera tabla HTML para DPDs"""
        if not dpds:
            return ""
        
        html = f"""
        <table>
            <tr>
                <td class="ColespanArriba" colspan="6">{titulo}</td>
            </tr>
            <tr>
                <td class="Cabecera">DPD</td>
                <td class="Cabecera">PETICIONARIO</td>
                <td class="Cabecera">EXPEDIENTE</td>
                <td class="Cabecera">DESCRIPCIÓN</td>
                <td class="Cabecera">IMPORTE ADJUDICADO</td>
                <td class="Cabecera">SUMINISTRADOR</td>
            </tr>
        """
        
        for dpd in dpds:
            importe = dpd.get('IMPORTEADJUDICADO', '')
            if isinstance(importe, (int, float)):
                importe = f"{importe:.2f}€"
            
            html += f"""
            <tr>
                <td>{dpd.get('CODPROYECTOS', '')}</td>
                <td>{dpd.get('PETICIONARIO', '')}</td>
                <td>{dpd.get('CodExp', '')}</td>
                <td>{dpd.get('DESCRIPCION', '')}</td>
                <td>{importe}</td>
                <td>{dpd.get('Suministrador', '')}</td>
            </tr>
            """
        
        html += "</table>\n"
        return html
    
    def send_facturas_pendientes_email(self, usuario: str, correo: str, facturas: List[Dict[str, Any]], dry_run: bool = False):
        """Envía email de facturas pendientes de visado técnico"""
        if not facturas:
            LoggingHelper.log_skipped_action("send_facturas_pendientes_email", usuario, "No hay facturas pendientes")
            return
        
        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_facturas(facturas, "Facturas Pendientes de Visado Técnico (AGEDYS)")
            
            html_content = f"""
            {generate_html_header(self.css_content)}
            <h2>Facturas Pendientes de Visado Técnico</h2>
            <p>Estimado/a {usuario},</p>
            <p>Le informamos que tiene facturas pendientes de visado técnico:</p>
            {tabla_html}
            <p>Por favor, proceda con el visado correspondiente.</p>
            {generate_html_footer()}
            """
            
            subject = f"AGEDYS - Facturas Pendientes de Visado Técnico ({len(facturas)} facturas)"
            
            if dry_run:
                LoggingHelper.log_email_action("send", usuario, correo, "DRY-RUN", f"{len(facturas)} facturas")
            else:
                # Enviar email
                send_notification_email(
                    to_email=correo,
                    subject=subject,
                    html_content=html_content,
                    app_id=APP_ID
                )
                
                # Registrar en base de datos
                register_email_in_database(
                    self.correos_db,
                    usuario_red=usuario,
                    correo_usuario=correo,
                    asunto=subject,
                    cuerpo_html=html_content,
                    app_id=APP_ID
                )
                
                LoggingHelper.log_email_action("send", usuario, correo, "ENVIADO", f"{len(facturas)} facturas")
                
        except Exception as e:
            LoggingHelper.log_database_error("send_facturas_pendientes_email", usuario, str(e))
    
    def send_dpds_sin_visado_email(self, usuario: str, correo: str, dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Envía email de DPDs sin visado"""
        if not dpds:
            LoggingHelper.log_skipped_action("send_dpds_sin_visado_email", usuario, "No hay DPDs sin visado")
            return
        
        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_dpds(dpds, "DPDs sin Solicitud de Oferta al Suministrador (AGEDYS)")
            
            html_content = f"""
            {generate_html_header(self.css_content)}
            <h2>DPDs sin Solicitud de Oferta al Suministrador</h2>
            <p>Estimado/a {usuario},</p>
            <p>Le informamos que tiene DPDs sin solicitud de oferta al suministrador:</p>
            {tabla_html}
            <p>Por favor, proceda con la solicitud correspondiente.</p>
            {generate_html_footer()}
            """
            
            subject = f"AGEDYS - DPDs sin Solicitud de Oferta ({len(dpds)} DPDs)"
            
            if dry_run:
                LoggingHelper.log_email_action("send", usuario, correo, "DRY-RUN", f"{len(dpds)} DPDs")
            else:
                # Enviar email
                send_notification_email(
                    to_email=correo,
                    subject=subject,
                    html_content=html_content,
                    app_id=APP_ID
                )
                
                # Registrar en base de datos
                register_email_in_database(
                    self.correos_db,
                    usuario_red=usuario,
                    correo_usuario=correo,
                    asunto=subject,
                    cuerpo_html=html_content,
                    app_id=APP_ID
                )
                
                LoggingHelper.log_email_action("send", usuario, correo, "ENVIADO", f"{len(dpds)} DPDs")
                
        except Exception as e:
            LoggingHelper.log_database_error("send_dpds_sin_visado_email", usuario, str(e))
    
    def send_dpds_rechazados_email(self, usuario: str, correo: str, dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Envía email de DPDs rechazados"""
        # Esta funcionalidad no está implementada en el legacy, se deja como placeholder
        LoggingHelper.log_skipped_action("send_dpds_rechazados_email", usuario, "Funcionalidad no implementada en legacy")
    
    def register_economia_email(self, usuarios: List[Dict[str, Any]], dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Registra correos de DPDs sin pedido para usuarios de economía"""
        if not dpds:
            LoggingHelper.log_skipped_action("register_economia_email", "economia", "No hay DPDs sin pedido")
            return
        
        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_dpds(dpds, "DPDs sin Pedido (AGEDYS)")
            
            html_content = f"""
            {generate_html_header(self.css_content)}
            <h2>DPDs sin Pedido</h2>
            <p>Estimados compañeros de Economía,</p>
            <p>Les informamos de los siguientes DPDs sin pedido:</p>
            {tabla_html}
            <p>Por favor, procedan con la gestión correspondiente.</p>
            {generate_html_footer()}
            """
            
            subject = f"AGEDYS - DPDs sin Pedido ({len(dpds)} DPDs)"
            
            for usuario_data in usuarios:
                usuario = usuario_data['UsuarioRed']
                correo = usuario_data['CorreoUsuario']
                
                if dry_run:
                    LoggingHelper.log_email_action("send", usuario, correo, "DRY-RUN", f"{len(dpds)} DPDs")
                else:
                    # Enviar email
                    send_notification_email(
                        to_email=correo,
                        subject=subject,
                        html_content=html_content,
                        app_id=APP_ID
                    )
                    
                    # Registrar en base de datos
                    register_email_in_database(
                        self.correos_db,
                        usuario_red=usuario,
                        correo_usuario=correo,
                        asunto=subject,
                        cuerpo_html=html_content,
                        app_id=APP_ID
                    )
                    
                    LoggingHelper.log_email_action("send", usuario, correo, "ENVIADO", f"{len(dpds)} DPDs")
                    
        except Exception as e:
            LoggingHelper.log_database_error("register_economia_email", "economia", str(e))
    
    def send_dpds_sin_pedido_email(self, usuarios: List[Dict[str, Any]], dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Alias para register_economia_email para mantener compatibilidad"""
        self.register_economia_email(usuarios, dpds, dry_run)
    
    def execute_task(self, dry_run: bool = False, force: bool = False) -> bool:
        """Ejecuta la tarea principal de AGEDYS"""
        has_errors = False
        
        try:
            LoggingHelper.log_phase_start("Ejecución de tarea AGEDYS", 
                                        f"Modo: {'DRY-RUN' if dry_run else 'PRODUCCIÓN'}")
            
            # Verificar si la tarea debe ejecutarse
            if not force and is_task_completed_today(self.tareas_db, "AGEDYSDiario"):
                LoggingHelper.log_skipped_action("execute_task", "AGEDYS", "Tarea ya completada hoy")
                return True
            
            if not force and not should_execute_task(TASK_FREQUENCY):
                LoggingHelper.log_skipped_action("execute_task", "AGEDYS", "No es momento de ejecutar según frecuencia")
                return True
            
            # Fase 1: Facturas pendientes de visado técnico
            LoggingHelper.log_phase_start("Fase 1", "Procesamiento de facturas pendientes de visado técnico")
            try:
                usuarios_facturas = self.get_usuarios_facturas_pendientes_visado_tecnico()
                
                facturas_enviadas = 0
                for usuario_data in usuarios_facturas:
                    usuario = usuario_data['UsuarioRed']
                    correo = usuario_data['CorreoUsuario']
                    
                    try:
                        facturas = self.get_facturas_pendientes_visado_tecnico(usuario)
                        if facturas:
                            self.send_facturas_pendientes_email(usuario, correo, facturas, dry_run)
                            facturas_enviadas += 1
                    except Exception as e:
                        LoggingHelper.log_database_error("get_facturas_pendientes_visado_tecnico", usuario, str(e))
                        has_errors = True
                
                LoggingHelper.log_phase_end("Fase 1", not has_errors, facturas_enviadas)
            except Exception as e:
                LoggingHelper.log_database_error("get_usuarios_facturas_pendientes_visado_tecnico", "fase_1", str(e))
                has_errors = True
                LoggingHelper.log_phase_end("Fase 1", False, 0)
            
            # Fase 2: DPDs sin visado
            LoggingHelper.log_phase_start("Fase 2", "Procesamiento de DPDs sin visado")
            try:
                usuarios_dpds = self.get_usuarios_dpds_sin_visado()
                
                dpds_enviados = 0
                for usuario_data in usuarios_dpds:
                    usuario = usuario_data['UsuarioRed']
                    correo = usuario_data['CorreoUsuario']
                    
                    try:
                        dpds = self.get_dpds_sin_visado(usuario)
                        if dpds:
                            self.send_dpds_sin_visado_email(usuario, correo, dpds, dry_run)
                            dpds_enviados += 1
                    except Exception as e:
                        LoggingHelper.log_database_error("get_dpds_sin_visado", usuario, str(e))
                        has_errors = True
                
                LoggingHelper.log_phase_end("Fase 2", not has_errors, dpds_enviados)
            except Exception as e:
                LoggingHelper.log_database_error("get_usuarios_dpds_sin_visado", "fase_2", str(e))
                has_errors = True
                LoggingHelper.log_phase_end("Fase 2", False, 0)
            
            # Fase 3: DPDs rechazados (placeholder)
            LoggingHelper.log_phase_start("Fase 3", "Procesamiento de DPDs rechazados")
            LoggingHelper.log_skipped_action("Fase 3", "DPDs rechazados", "No implementado en legacy")
            LoggingHelper.log_phase_end("Fase 3", True, 0)
            
            # Fase 4: Economía - DPDs sin pedido
            LoggingHelper.log_phase_start("Fase 4", "Procesamiento de DPDs sin pedido para economía")
            try:
                usuarios_economia = self.get_usuarios_economia()
                dpds_sin_pedido = self.get_dpds_sin_pedido()
                
                if usuarios_economia and dpds_sin_pedido:
                    self.register_economia_email(usuarios_economia, dpds_sin_pedido, dry_run)
                    economia_enviados = len(usuarios_economia)
                else:
                    economia_enviados = 0
                
                LoggingHelper.log_phase_end("Fase 4", not has_errors, economia_enviados)
            except Exception as e:
                LoggingHelper.log_database_error("get_usuarios_economia", "fase_4", str(e))
                has_errors = True
                LoggingHelper.log_phase_end("Fase 4", False, 0)
            
            # Solo registrar completación si no hubo errores
            if not has_errors and not dry_run:
                register_task_completion(self.tareas_db, "AGEDYSDiario")
            
            success = not has_errors
            LoggingHelper.log_phase_end("Ejecución de tarea AGEDYS", success)
            return success
            
        except Exception as e:
            LoggingHelper.log_database_error("execute_task", "proceso_principal", str(e))
            LoggingHelper.log_phase_end("Ejecución de tarea AGEDYS", False)
            return False
    
    def has_emails_sent_today(self) -> bool:
        """Verifica si se han enviado emails hoy para AGEDYS"""
        try:
            from datetime import date
            today = date.today()
            
            # Usar formato de fecha de Access #mm/dd/yyyy#
            fecha_access = f"#{today.strftime('%m/%d/%Y')}#"
            
            query = f"""
                SELECT COUNT(*) as Count 
                FROM TbCorreosEnviados 
                WHERE Aplicacion = 'AGEDYS' 
                AND DateValue(FechaGrabacion) = {fecha_access}
            """
            
            result = self.correos_db.execute_query(query)
            
            if result and len(result) > 0:
                return result[0]['Count'] > 0
            
            return False
            
        except Exception as e:
            LoggingHelper.log_database_error("has_emails_sent_today", "verificacion", str(e))
            return False

    @staticmethod
    def run(dry_run: bool = False, force: bool = False) -> bool:
        """Método estático para ejecutar AGEDYS"""
        print("🔄 Iniciando procesamiento de AGEDYS...")
        print(f"📋 Modo: {'DRY-RUN (simulación)' if dry_run else 'PRODUCCIÓN'}")
        print(f"⚡ Forzado: {'SÍ' if force else 'NO'}")
        print("🔗 Conectando a base de datos...")
        
        try:
            manager = AgedysManager()
            print("✅ Conexión establecida correctamente")
            print("📊 Analizando facturas pendientes y DPDs...")
            
            success = manager.execute_task(dry_run=dry_run, force=force)
            
            if success:
                print("✅ PROCESO COMPLETADO EXITOSAMENTE")
                # Solo mostrar mensaje de emails procesados si realmente se enviaron emails
                if not dry_run and manager.has_emails_sent_today():
                    print("📧 Todos los emails han sido procesados correctamente")
            else:
                print("❌ PROCESO COMPLETADO CON ERRORES")
                print("⚠️  Revisar logs para más detalles")
            
            return success
            
        except Exception as e:
            print(f"💥 Error durante el procesamiento: {e}")
            LoggingHelper.log_database_error("proceso_principal_agedys", "sistema", str(e))
            return False