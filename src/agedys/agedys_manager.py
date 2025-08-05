#!/usr/bin/env python3
"""
Gestor AGEDYS - Gestión de facturas pendientes de visado técnico
Adaptación del script legacy AGEDYS.VBS a Python
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from common import config
from common.database import AccessDatabase
from common.utils import (
    generate_html_header, generate_html_footer, format_date, load_css_content,
    get_quality_emails_string, get_technical_emails_string, get_admin_emails_string,
    register_task_completion, should_execute_task, is_task_completed_today,
    get_quality_users, get_economy_users
)
from common import utils

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
    def log_database_query(operation: str, description: str):
        """Log de consultas de base de datos"""
        logger.debug(f"📊 {operation}: {description}")

    @staticmethod
    def log_database_result(operation: str, count: int):
        """Log de resultados de base de datos"""
        logger.debug(f"📊 {operation}: {count} registros obtenidos")

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
        
        # Configuración y logger
        self.config = config
        self.logger = logger

        self.css_content = load_css_content(config.css_file_path)

    def get_usuarios_facturas_pendientes_visado_tecnico(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con facturas pendientes de visado técnico"""
        LoggingHelper.log_phase_start("Obtención de usuarios con facturas pendientes",
                                    "Ejecutando 4 consultas principales + fallback si es necesario")

        usuarios_dict = {}

        # Definir las consultas EXACTAMENTE como en el VBS legacy - Corregidas para TbExpedientes1
        queries = {
            "peticionarios_con_visado": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM ((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle
                INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
                INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                INNER JOIN TbUsuariosAplicaciones ON TbProyectos.PETICIONARIO = TbUsuariosAplicaciones.Nombre
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL
                AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL
                AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL
                AND TbExpedientes1.AGEDYSGenerico = 'Sí'
                AND TbExpedientes1.AGEDYSAplica = 'Sí'
            """,
            "responsables_sin_visado_generico_si": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
                INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL
                AND TbVisadoFacturas_Nueva.IDFactura IS NULL
                AND TbExpedientes1.AGEDYSGenerico = 'Sí'
                AND TbExpedientes1.AGEDYSAplica = 'Sí'
                AND TbExpedientesResponsables.CorreoSiempre <> 'No'
            """,
            "responsables_con_visado_generico_no": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM (((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle
                INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
                INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL
                AND TbVisadoFacturas_Nueva.FRECHAZOTECNICO IS NULL
                AND TbVisadoFacturas_Nueva.FVISADOTECNICO IS NULL
                AND TbExpedientes1.AGEDYSGenerico = 'No'
                AND TbExpedientes1.AGEDYSAplica = 'Sí'
                AND TbExpedientesResponsables.CorreoSiempre <> 'No'
            """,
            "responsables_sin_visado_generico_no": """
                SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
                FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle
                ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
                INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
                INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente)
                LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura)
                INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id
                WHERE TbFacturasDetalle.FechaAceptacion IS NULL
                AND TbVisadoFacturas_Nueva.IDFactura IS NULL
                AND TbExpedientes1.AGEDYSGenerico = 'No'
                AND TbExpedientes1.AGEDYSAplica = 'Sí'
            """
        }

        query_fallback = """
            SELECT DISTINCT TbProyectos.PETICIONARIO as UsuarioRed
            FROM ((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle
            ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD)
            INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente)
            LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura
            WHERE TbFacturasDetalle.FechaAceptacion IS NULL
            AND TbVisadoFacturas_Nueva.IDFactura IS NULL
            AND TbExpedientes1.AGEDYSGenerico <> 'No'
            AND TbExpedientes1.AGEDYSAplica = 'Sí'
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
                                correo_query = "SELECT CorreoUsuario FROM TbUsuariosAplicaciones WHERE Nombre = '" + usuario_red + "'"
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

        # Primero obtener el ID y nombre completo del usuario
        try:
            user_query = "SELECT Id, Nombre FROM TbUsuariosAplicaciones WHERE UsuarioRed = '" + usuario + "'"
            user_result = self.db.execute_query(user_query)
            if not user_result:
                LoggingHelper.log_skipped_action(f"Usuario {usuario} no encontrado en TbUsuariosAplicaciones",
                                               "No se ejecutarán consultas")
                return []
            else:
                user_id = user_result[0]['Id']
                user_nombre = user_result[0]['Nombre']
        except Exception as e:
            LoggingHelper.log_database_error("user_lookup", usuario, str(e))
            return []

        # Definir las consultas usando concatenación directa sin parámetros
        queries_with_params = {}
        
        # Query para responsables con visado genérico = 'No' (usando ID de usuario) - Corregida para TbExpedientes1
        sql_responsable_con_visado = "SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes1.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO FROM (((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP WHERE ((TbFacturasDetalle.FechaAceptacion) IS NULL) AND ((TbVisadoFacturas_Nueva.FRECHAZOTECNICO) IS NULL) AND ((TbVisadoFacturas_Nueva.FVISADOTECNICO) IS NULL) AND ((TbExpedientes1.AGEDYSGenerico) = 'No') AND ((TbExpedientes1.AGEDYSAplica) = 'Sí') AND ((TbExpedientesResponsables.CorreoSiempre) = 'Sí') AND ((TbExpedientesResponsables.IdUsuario) = " + str(user_id) + ")"
        
        # Query para responsables sin visado genérico = 'No' (usando ID de usuario) - Corregida para TbExpedientes1
        sql_responsable_sin_visado = "SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes1.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO FROM ((((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP WHERE ((TbFacturasDetalle.FechaAceptacion) IS NULL) AND ((TbVisadoFacturas_Nueva.IDFactura) IS NULL) AND ((TbExpedientes1.AGEDYSGenerico) = 'No') AND ((TbExpedientes1.AGEDYSAplica) = 'Sí') AND ((TbExpedientesResponsables.CorreoSiempre) = 'Sí') AND ((TbExpedientesResponsables.IdUsuario) = " + str(user_id) + ")"
        
        queries_with_params["responsable_con_visado_generico_no"] = sql_responsable_con_visado
        queries_with_params["responsable_sin_visado_generico_no"] = sql_responsable_sin_visado

        # Consulta para peticionarios CON visado genérico = 'Sí' (usando nombre completo) - Corregida para TbExpedientes1
        sql_con_visado = "SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes1.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO FROM ((TbProyectos INNER JOIN (TbNPedido INNER JOIN (TbFacturasDetalle INNER JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP WHERE ((TbFacturasDetalle.FechaAceptacion) IS NULL) AND ((TbVisadoFacturas_Nueva.FRECHAZOTECNICO) IS NULL) AND ((TbVisadoFacturas_Nueva.FVISADOTECNICO) IS NULL) AND ((TbExpedientes1.AGEDYSGenerico) = 'Sí') AND ((TbExpedientes1.AGEDYSAplica) = 'Sí') AND ((TbProyectos.PETICIONARIO) = '" + user_nombre + "')"
        
        # Consulta para peticionarios SIN visado genérico = 'Sí' (usando nombre completo) - Corregida para TbExpedientes1
        sql_sin_visado = "SELECT TbFacturasDetalle.NFactura, TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes1.CodExp, TbProyectos.DESCRIPCION, TbNPedido.IMPORTEADJUDICADO, TbSuministradoresSAP.Suministrador, TbFacturasDetalle.ImporteFactura, TbFacturasDetalle.NDOCUMENTO FROM (((TbProyectos INNER JOIN (TbNPedido INNER JOIN TbFacturasDetalle ON TbNPedido.NPEDIDO = TbFacturasDetalle.NPEDIDO) ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) LEFT JOIN TbVisadoFacturas_Nueva ON TbFacturasDetalle.IDFactura = TbVisadoFacturas_Nueva.IDFactura) INNER JOIN TbSuministradoresSAP ON TbNPedido.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP WHERE ((TbFacturasDetalle.FechaAceptacion) IS NULL) AND ((TbVisadoFacturas_Nueva.IDFactura) IS NULL) AND ((TbExpedientes1.AGEDYSGenerico) = 'Sí') AND ((TbExpedientes1.AGEDYSAplica) = 'Sí') AND ((TbProyectos.PETICIONARIO) = '" + user_nombre + "')"
        
        queries_with_params["peticionario_con_visado_generico_si"] = sql_con_visado
        queries_with_params["peticionario_sin_visado_generico_si"] = sql_sin_visado

        facturas_list = []

        try:
            for query_name, query_info in queries_with_params.items():
                try:
                    # Todas las consultas ahora usan concatenación directa sin parámetros
                    facturas = self.db.execute_query(query_info)
                    LoggingHelper.log_query_execution(query_name, True, len(facturas))
                    facturas_list.extend(facturas)
                except Exception as e:
                    LoggingHelper.log_query_execution(query_name, False, error=str(e))

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
        # Query principal - EXACTA del VBS legacy - Corregida para TbExpedientes1
        query_responsables = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario FROM ((((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IdExpediente) INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IdExpediente = TbExpedientesResponsables.IdExpediente) INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) LEFT JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP WHERE (((TbProyectos.ELIMINADO)=False) AND ((TbSolicitudesOfertasPrevias.DPD) Is Null) AND ((TbExpedientes1.AGEDYSGenerico)<>'Sí') AND ((TbExpedientes1.AGEDYSAplica)='Sí') AND ((TbProyectos.CODCONTRATOGTV) Is Null) AND ((TbSuministradoresSAP.IDSuministrador) Is Null))"

        # Query fallback - EXACTA del VBS legacy - Corregida para TbExpedientes1
        query_peticionarios = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario FROM (((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IdExpediente) LEFT JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) INNER JOIN TbUsuariosAplicaciones ON TbProyectos.PETICIONARIO = TbUsuariosAplicaciones.Nombre WHERE (((TbProyectos.ELIMINADO)=False) AND ((TbSolicitudesOfertasPrevias.DPD) Is Null) AND ((TbExpedientes1.AGEDYSGenerico)<>'Sí') AND ((TbProyectos.CODCONTRATOGTV) Is Null) AND ((TbSuministradoresSAP.IDSuministrador) Is Null))"

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
            user_query = "SELECT Id FROM TbUsuariosAplicaciones WHERE UsuarioRed = '" + usuario + "'"
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

        # Query para responsables (si tenemos ID) - Con acentos correctos
        if user_id is not None:
            query_responsable = "SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes1.CodExp, TbProyectos.DESCRIPCION, TbProyectos.IMPORTEADJUDICADO FROM ((((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IdExpediente) INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IdExpediente = TbExpedientesResponsables.IdExpediente) INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) LEFT JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP WHERE (((TbProyectos.ELIMINADO)=False) AND ((TbSolicitudesOfertasPrevias.DPD) Is Null) AND ((TbExpedientes1.AGEDYSGenerico)<>'Sí') AND ((TbExpedientes1.AGEDYSAplica)='Sí') AND ((TbProyectos.CODCONTRATOGTV) Is Null) AND ((TbSuministradoresSAP.IDSuministrador) Is Null) AND ((TbExpedientesResponsables.IdUsuario) = " + str(user_id) + "))"

            try:
                dpds = self.db.execute_query(query_responsable)
                LoggingHelper.log_query_execution(f"responsable_dpds_{usuario}", True, len(dpds))
                dpds_list.extend(dpds)
            except Exception as e:
                LoggingHelper.log_query_execution(f"responsable_dpds_{usuario}", False, error=str(e))

        # Query para peticionarios - Con acentos correctos
        query_peticionario = "SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbExpedientes1.CodExp, TbProyectos.DESCRIPCION, TbProyectos.IMPORTEADJUDICADO FROM (((TbProyectos LEFT JOIN TbSolicitudesOfertasPrevias ON TbProyectos.CODPROYECTOS = TbSolicitudesOfertasPrevias.DPD) INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IdExpediente) LEFT JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) INNER JOIN TbUsuariosAplicaciones ON TbProyectos.PETICIONARIO = TbUsuariosAplicaciones.Nombre WHERE (((TbProyectos.ELIMINADO)=False) AND ((TbSolicitudesOfertasPrevias.DPD) Is Null) AND ((TbExpedientes1.AGEDYSGenerico)<>'Sí') AND ((TbProyectos.CODCONTRATOGTV) Is Null) AND ((TbSuministradoresSAP.IDSuministrador) Is Null) AND ((TbUsuariosAplicaciones.UsuarioRed) = '" + usuario + "'))"

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

    def get_usuarios_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios de calidad usando la función común"""
        try:
            from common.utils import get_quality_users
            return get_quality_users("3", self.config, self.logger) or []
        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_calidad", "calidad", str(e))
            return []

    def get_usuarios_tecnicos(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios técnicos usando la función común"""
        try:
            from common.utils import get_technical_users
            return get_technical_users("3", self.config, self.logger) or []
        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_tecnicos", "tecnicos", str(e))
            return []

    def get_all_dpds_sin_visado_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene todos los DPDs sin visado de calidad"""
        try:
            query = """
                SELECT TbProyectos.CODPROYECTOS, TbProyectos.DESCRIPCION, TbProyectos.PETICIONARIO,
                       TbProyectos.FREGISTRO, TbProyectos.IMPORTESINIVA
                FROM TbProyectos
                INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD
                WHERE TbVisadosGenerales.ROFechaRechazo IS NULL
                AND TbVisadosGenerales.ROFechaVisado IS NULL
                AND TbProyectos.FechaFinAgendaTecnica IS NULL
                ORDER BY TbProyectos.FREGISTRO
            """
            return self.db.execute_query(query) or []
        except Exception as e:
            LoggingHelper.log_database_error("get_all_dpds_sin_visado_calidad", "calidad", str(e))
            return []

    def get_all_dpds_rechazados_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene todos los DPDs rechazados por calidad"""
        try:
            query = """
                SELECT TbProyectos.CODPROYECTOS, TbProyectos.DESCRIPCION, TbProyectos.PETICIONARIO,
                       TbProyectos.FREGISTRO, TbProyectos.IMPORTESINIVA
                FROM TbProyectos
                INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD
                WHERE TbVisadosGenerales.ROFechaRechazo IS NOT NULL
                ORDER BY TbProyectos.FREGISTRO
            """
            return self.db.execute_query(query) or []
        except Exception as e:
            LoggingHelper.log_database_error("get_all_dpds_rechazados_calidad", "calidad", str(e))
            return []

    def get_dpds_sin_pedido_for_user(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene DPDs sin pedido para un usuario específico"""
        try:
            dpds_sin_pedido = self.get_dpds_sin_pedido()
            return [dpd for dpd in dpds_sin_pedido if dpd.get('PETICIONARIO') == usuario]
        except Exception as e:
            LoggingHelper.log_database_error("get_dpds_sin_pedido_for_user", usuario, str(e))
            return []

    def get_usuarios_economia(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios de economía usando la función común"""
        LoggingHelper.log_phase_start("Obtención de usuarios de economía")

        try:
            usuarios = get_economy_users(self.config, self.logger)
            LoggingHelper.log_query_execution("usuarios_economia", True, len(usuarios))
            LoggingHelper.log_phase_end("Obtención de usuarios de economía", True, len(usuarios))
            return usuarios

        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_economia", "proceso_completo", str(e))
            LoggingHelper.log_phase_end("Obtención de usuarios de economía", False)
            raise  # Re-lanzar la excepción para que se propague

    def get_usuarios_dpds_pendientes_recepcion_economica(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con DPDs pendientes de recepción económica"""
        try:
            LoggingHelper.log_database_query("get_usuarios_dpds_pendientes_recepcion_economica", "Obteniendo usuarios con DPDs pendientes de recepción económica")

            query = """
                SELECT DISTINCT u.UsuarioRed, u.CorreoUsuario
                FROM TbUsuarios u
                INNER JOIN TbProyectos p ON u.UsuarioRed = p.PETICIONARIO
                WHERE p.ESTADODPD = 'Fin Agenda Técnica'
                AND u.CorreoUsuario IS NOT NULL
                AND u.CorreoUsuario <> ''
                ORDER BY u.UsuarioRed
            """

            result = self.db.execute_query(query)
            LoggingHelper.log_database_result("get_usuarios_dpds_pendientes_recepcion_economica", len(result))
            return result

        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_dpds_pendientes_recepcion_economica", "consulta", str(e))
            return []

    def get_dpds_pendientes_recepcion_economica(self, usuario: str = None) -> List[Dict[str, Any]]:
        """Obtiene DPDs pendientes de recepción económica para un usuario específico o todos"""
        try:
            LoggingHelper.log_database_query("get_dpds_pendientes_recepcion_economica", f"Obteniendo DPDs pendientes de recepción económica para {usuario or 'todos'}")

            if usuario:
                query = "SELECT CODPROYECTOS, DESCRIPCION, PETICIONARIO, CodExp, IMPORTEADJUDICADO, Suministrador FROM TbProyectos WHERE ESTADODPD = 'Fin Agenda Técnica' AND PETICIONARIO = '" + usuario + "' ORDER BY CODPROYECTOS"
            else:
                query = "SELECT CODPROYECTOS, DESCRIPCION, PETICIONARIO, CodExp, IMPORTEADJUDICADO, Suministrador FROM TbProyectos WHERE ESTADODPD = 'Fin Agenda Técnica' ORDER BY CODPROYECTOS"

            result = self.db.execute_query(query)
            LoggingHelper.log_database_result("get_dpds_pendientes_recepcion_economica", len(result))
            return result

        except Exception as e:
            LoggingHelper.log_database_error("get_dpds_pendientes_recepcion_economica", usuario or "todos", str(e))
            return []

    def get_usuarios_dpds_sin_visado_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con DPDs sin visado de calidad"""
        try:
            LoggingHelper.log_database_query("get_usuarios_dpds_sin_visado_calidad", "Obteniendo usuarios con DPDs sin visado de calidad")

            # Usar la función común para obtener usuarios de calidad
            usuarios = get_quality_users("3", self.config, self.logger)

            LoggingHelper.log_database_result("get_usuarios_dpds_sin_visado_calidad", len(usuarios))
            return usuarios

        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_dpds_sin_visado_calidad", "consulta", str(e))
            return []

    def get_dpds_sin_visado_calidad(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene DPDs sin visado de calidad para un usuario específico"""
        try:
            LoggingHelper.log_database_query("get_dpds_sin_visado_calidad", f"Obteniendo DPDs sin visado de calidad para {usuario}")

            query = "SELECT DISTINCT p.CODPROYECTOS as NumeroDPD, p.DESCRIPCION as Descripcion, p.PETICIONARIO, p.FECHAPETICION, p.CodExp, p.ResponsableTecnico, p.ROObservaciones FROM TbProyectos p LEFT JOIN TbVisadosGenerales vg ON p.CODPROYECTOS = vg.CODPROYECTOS AND vg.TipoVisado = 'CALIDAD' WHERE p.PETICIONARIO = '" + usuario + "' AND vg.CODPROYECTOS IS NULL AND p.Estado = 'ACTIVO' ORDER BY p.FECHAPETICION DESC"

            result = self.db.execute_query(query)
            LoggingHelper.log_database_result("get_dpds_sin_visado_calidad", len(result))
            return result

        except Exception as e:
            LoggingHelper.log_database_error("get_dpds_sin_visado_calidad", usuario, str(e))
            return []

    def get_usuarios_dpds_rechazados_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con DPDs rechazados por calidad"""
        try:
            LoggingHelper.log_database_query("get_usuarios_dpds_rechazados_calidad", "Obteniendo usuarios con DPDs rechazados por calidad")

            # Usar la función común para obtener usuarios de calidad
            usuarios = get_quality_users("3", self.config, self.logger)

            LoggingHelper.log_database_result("get_usuarios_dpds_rechazados_calidad", len(usuarios))
            return usuarios

        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_dpds_rechazados_calidad", "consulta", str(e))
            return []

    def get_dpds_rechazados_calidad(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene DPDs rechazados por calidad para un usuario específico"""
        try:
            LoggingHelper.log_database_query("get_dpds_rechazados_calidad", f"Obteniendo DPDs rechazados por calidad para {usuario}")

            query = "SELECT DISTINCT p.CODPROYECTOS as NumeroDPD, p.DESCRIPCION as Descripcion, p.PETICIONARIO, p.FECHAPETICION, p.CodExp, p.ResponsableTecnico, p.ROObservaciones, vg.FechaVisado as FechaRechazo, vg.Observaciones FROM TbProyectos p INNER JOIN TbVisadosGenerales vg ON p.CODPROYECTOS = vg.CODPROYECTOS AND vg.TipoVisado = 'CALIDAD' WHERE p.PETICIONARIO = '" + usuario + "' AND vg.EstadoVisado = 'RECHAZADO' AND p.Estado = 'ACTIVO' ORDER BY vg.FechaVisado DESC"

            result = self.db.execute_query(query)
            LoggingHelper.log_database_result("get_dpds_rechazados_calidad", len(result))
            return result

        except Exception as e:
            LoggingHelper.log_database_error("get_dpds_rechazados_calidad", usuario, str(e))
            return []

    def get_dpds_fin_agenda_tecnica_por_recepcionar(self) -> List[Dict[str, Any]]:
        """Obtiene DPDs con fin de agenda técnica por recepcionar - basado en VBS original"""
        try:
            LoggingHelper.log_database_query("get_dpds_fin_agenda_tecnica_por_recepcionar", "Obteniendo DPDs con fin de agenda técnica por recepcionar")

            # Consulta basada en el VBS original: getDPDsConFinAgendaTecnicaPorRecepcionaEconomia
            query = """
                SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbProyectos.FECHAPETICION, 
                       TbProyectos.EXPEDIENTE, TbProyectos.DESCRIPCION
                FROM TbProyectos
                WHERE TbProyectos.ELIMINADO = False 
                AND TbProyectos.FECHARECEPCIONECONOMICA IS NULL 
                AND TbProyectos.FechaFinAgendaTecnica IS NOT NULL
            """

            result = self.db.execute_query(query)
            LoggingHelper.log_database_result("get_dpds_fin_agenda_tecnica_por_recepcionar", len(result))
            return result

        except Exception as e:
            LoggingHelper.log_database_error("get_dpds_fin_agenda_tecnica_por_recepcionar", "consulta", str(e))
            return []

    def get_usuarios_tareas(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios de tareas - basado en el legacy VBS"""
        try:
            LoggingHelper.log_database_query("get_usuarios_tareas", "Obteniendo usuarios de tareas")

            # SQL simplificada según especificación del usuario
            # Usa la base de datos Lanzadera (tareas_db) como en el VBS
            query = """
                SELECT 
                    TbUsuariosAplicaciones.UsuarioRed, 
                    TbUsuariosAplicaciones.Nombre, 
                    TbUsuariosAplicaciones.CorreoUsuario 
                FROM 
                    TbUsuariosAplicaciones 
                WHERE 
                    TbUsuariosAplicaciones.ParaTareasProgramadas = True 
                    AND TbUsuariosAplicaciones.FechaBaja IS NULL
            """

            result = self.tareas_db.execute_query(query)
            LoggingHelper.log_database_result("get_usuarios_tareas", len(result))
            return result

        except Exception as e:
            LoggingHelper.log_database_error("get_usuarios_tareas", "consulta", str(e))
            return []

    def get_dpds_sin_pedido(self) -> List[Dict[str, Any]]:
        """Obtiene DPDs sin pedido para economía - basado en VBS original"""
        LoggingHelper.log_phase_start("Obtención de DPDs sin pedido para economía")

        try:
            # Query basada en el VBS original getDPDsSinPedido
            query = """
                SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbProyectos.FECHAPETICION, 
                       TbProyectos.EXPEDIENTE, TbProyectos.DESCRIPCION
                FROM TbProyectos INNER JOIN TbNPedido ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD
                WHERE TbProyectos.ELIMINADO = False 
                AND TbNPedido.NPEDIDO IS NULL
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

    def generate_dpds_html_table(self, dpds: List[Dict[str, Any]], tipo: str) -> str:
        """Genera tabla HTML para DPDs con tipo específico"""
        if not dpds:
            return f"<p>No hay DPDs {tipo}.</p>"

        return self.generate_html_table_dpds(dpds, f"DPDs {tipo}")

    def generate_facturas_html_table(self, facturas: List[Dict[str, Any]]) -> str:
        """Genera tabla HTML para facturas"""
        if not facturas:
            return "<p>No hay facturas pendientes de visado técnico.</p>"

        return self.generate_html_table_facturas(facturas, "Facturas Pendientes de Visado Técnico")

    def register_facturas_pendientes_notification(self, usuario: str, correo: str, facturas: List[Dict[str, Any]], dry_run: bool = False) -> bool:
        """Registra notificación de facturas pendientes de visado técnico"""
        if not facturas:
            LoggingHelper.log_skipped_action("register_facturas_pendientes_notification", usuario, "No hay facturas pendientes")
            return True

        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_facturas(facturas, "Facturas Pendientes de Visado Técnico (AGEDYS)")

            html_content = f"""
            {generate_html_header("Facturas Pendientes de Visado Técnico", self.css_content)}
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
                # Solo registrar en base de datos (no enviar por SMTP)
                utils.register_email_in_database(
                    self.correos_db,
                    "AGEDYS",
                    subject,
                    html_content,
                    correo,
                    ""  # admin_emails vacío
                )

                LoggingHelper.log_email_action("send", usuario, correo, "REGISTRADO", f"{len(facturas)} facturas")

            return True

        except Exception as e:
            LoggingHelper.log_database_error("register_facturas_pendientes_notification", usuario, str(e))
            return False

    def register_dpds_sin_visado_notification(self, usuario: str, correo: str, dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Registra notificación de DPDs sin visado"""
        if not dpds:
            LoggingHelper.log_skipped_action("register_dpds_sin_visado_notification", usuario, "No hay DPDs sin visado")
            return

        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_dpds(dpds, "DPDs sin Solicitud de Oferta al Suministrador (AGEDYS)")

            html_content = f"""
            {generate_html_header("DPDs sin Solicitud de Oferta", self.css_content)}
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
                # Solo registrar en base de datos (no enviar por SMTP)
                utils.register_email_in_database(
                    self.correos_db,
                    "AGEDYS",
                    subject,
                    html_content,
                    correo,
                    ""  # admin_emails vacío
                )

                LoggingHelper.log_email_action("send", usuario, correo, "REGISTRADO", f"{len(dpds)} DPDs")

        except Exception as e:
            LoggingHelper.log_database_error("register_dpds_sin_visado_notification", usuario, str(e))

    def register_dpds_rechazados_notification(self, usuario: str, correo: str, dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Registra notificación de DPDs rechazados"""
        if not dpds:
            LoggingHelper.log_skipped_action("register_dpds_rechazados_notification", usuario, "No hay DPDs rechazados")
            return

        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_dpds(dpds, "DPDs Rechazados de Calidad (AGEDYS)")

            html_content = f"""
            {generate_html_header("DPDs Rechazados de Calidad", self.css_content)}
            <h2>DPDs Rechazados de Calidad</h2>
            <p>Estimado/a {usuario},</p>
            <p>Le informamos que tiene DPDs rechazados de calidad:</p>
            {tabla_html}
            <p>Por favor, proceda con las correcciones correspondientes.</p>
            {generate_html_footer()}
            """

            subject = f"AGEDYS - DPDs Rechazados de Calidad ({len(dpds)} DPDs)"

            if dry_run:
                LoggingHelper.log_email_action("send", usuario, correo, "DRY-RUN", f"{len(dpds)} DPDs")
            else:
                # Solo registrar en base de datos (no enviar por SMTP)
                utils.register_email_in_database(
                    self.correos_db,
                    "AGEDYS",
                    subject,
                    html_content,
                    correo,
                    ""  # admin_emails vacío
                )

                LoggingHelper.log_email_action("send", usuario, correo, "REGISTRADO", f"{len(dpds)} DPDs")

        except Exception as e:
            LoggingHelper.log_database_error("register_dpds_rechazados_notification", usuario, str(e))

    def register_economia_notification_data(self, usuarios: List[Dict[str, Any]], dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Registra notificaciones de DPDs sin pedido para usuarios de economía"""
        if not dpds:
            LoggingHelper.log_skipped_action("register_economia_notification_data", "economia", "No hay DPDs sin pedido")
            return

        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_dpds(dpds, "DPDs sin Pedido (AGEDYS)")

            html_content = f"""
            {generate_html_header("DPDs sin Pedido", self.css_content)}
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
                    # Solo registrar en base de datos (no enviar por SMTP)
                    utils.register_email_in_database(
                        self.correos_db,
                        "AGEDYS",
                        subject,
                        html_content,
                        correo,
                        ""  # admin_emails vacío
                    )

                    LoggingHelper.log_email_action("send", usuario, correo, "REGISTRADO", f"{len(dpds)} DPDs")

        except Exception as e:
            LoggingHelper.log_database_error("register_economia_notification_data", "economia", str(e))

    def register_dpds_sin_pedido_notification(self, usuario: str, correo: str, dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Registra notificación de DPDs sin pedido a un usuario específico"""
        if not dpds:
            LoggingHelper.log_skipped_action("register_dpds_sin_pedido_notification", usuario, "No hay DPDs sin pedido")
            return

        try:
            # Generar contenido HTML
            tabla_html = self.generate_html_table_dpds(dpds, "DPDs sin Pedido (AGEDYS)")

            html_content = f"""
            {generate_html_header("DPDs sin Pedido", self.css_content)}
            <h2>DPDs sin Pedido</h2>
            <p>Estimado/a {usuario},</p>
            <p>Le informamos que tiene DPDs sin pedido:</p>
            {tabla_html}
            <p>Por favor, proceda con la gestión correspondiente.</p>
            {generate_html_footer()}
            """

            subject = f"AGEDYS - DPDs sin Pedido ({len(dpds)} DPDs)"

            if dry_run:
                LoggingHelper.log_email_action("send", usuario, correo, "DRY-RUN", f"{len(dpds)} DPDs")
            else:
                # Solo registrar en base de datos (no enviar por SMTP)
                utils.register_email_in_database(
                    self.correos_db,
                    "AGEDYS",
                    subject,
                    html_content,
                    correo,
                    ""  # admin_emails vacío
                )

                LoggingHelper.log_email_action("send", usuario, correo, "REGISTRADO", f"{len(dpds)} DPDs")

        except Exception as e:
            LoggingHelper.log_database_error("register_dpds_sin_pedido_notification", usuario, str(e))

    def register_economia_notification(self, usuarios: List[Dict[str, Any]], dpds: List[Dict[str, Any]], dry_run: bool = False):
        """Registra notificación para economía - alias para mantener compatibilidad con tests"""
        self.register_economia_notification_data(usuarios, dpds, dry_run)

    def process_calidad_tasks(self, dry_run: bool = False):
        """Procesa todas las tareas de calidad y envía un solo email agrupado"""
        try:
            # Obtener usuarios de calidad
            usuarios_calidad = self.get_usuarios_calidad()
            if not usuarios_calidad:
                LoggingHelper.log_skip_action("No hay usuarios de calidad configurados", "process_calidad_tasks")
                return

            # Obtener todas las tareas de calidad
            dpds_sin_visado = self.get_all_dpds_sin_visado_calidad()
            dpds_rechazados = self.get_all_dpds_rechazados_calidad()

            # Si no hay tareas, no enviar email
            if not dpds_sin_visado and not dpds_rechazados:
                LoggingHelper.log_skip_action("No hay tareas pendientes para calidad", "process_calidad_tasks")
                return

            # Construir HTML agrupado
            html_content = self.build_calidad_html(dpds_sin_visado, dpds_rechazados)
            
            # Enviar a todos los usuarios de calidad
            for usuario_data in usuarios_calidad:
                correo = usuario_data['CorreoUsuario']
                self.register_grouped_notification(
                    correo, 
                    "Tareas Diarias Calidad", 
                    html_content, 
                    dry_run
                )

        except Exception as e:
            LoggingHelper.log_database_error("process_calidad_tasks", "calidad", str(e))        # Re-lanzar la excepción para que sea capturada por el método run
            raise

    def process_economia_tasks(self, dry_run: bool = False):
        """Procesa todas las tareas de economía y envía un solo email agrupado"""
        try:
            # Obtener usuarios de economía
            usuarios_economia = self.get_usuarios_economia()
            if not usuarios_economia:
                LoggingHelper.log_skip_action("No hay usuarios de economía configurados", "process_economia_tasks")
                return

            # Obtener DPDs sin pedido para economía
            dpds_sin_pedido = self.get_dpds_fin_agenda_tecnica_por_recepcionar()
            
            if not dpds_sin_pedido:
                LoggingHelper.log_skip_action("No hay DPDs sin pedido para economía", "process_economia_tasks")
                return

            # Construir HTML
            html_content = self.build_economia_html(dpds_sin_pedido)
            
            # Enviar a todos los usuarios de economía
            for usuario_data in usuarios_economia:
                correo = usuario_data['CorreoUsuario']
                self.register_grouped_notification(
                    correo, 
                    "Tareas Diarias Economía", 
                    html_content, 
                    dry_run
                )

        except Exception as e:
            LoggingHelper.log_database_error("process_economia_tasks", "economia", str(e))
            # Re-lanzar la excepción para que sea capturada por el método run
            raise

    def build_calidad_html(self, dpds_sin_visado: List[Dict], dpds_rechazados: List[Dict]) -> str:
        """Construye HTML agrupado para tareas de calidad como en el VBS legacy"""
        try:
            html_content = generate_html_header("Tareas Diarias Calidad", self.css_content)
            
            # Agregar DPDs sin visado si existen
            if dpds_sin_visado:
                tabla_sin_visado = self.generate_html_table_dpds(dpds_sin_visado, "DPDs Pendientes de Visado de Calidad")
                html_content += f"<h3>DPDs Pendientes de Visado de Calidad ({len(dpds_sin_visado)})</h3>\n{tabla_sin_visado}\n"
            
            # Agregar DPDs rechazados si existen
            if dpds_rechazados:
                tabla_rechazados = self.generate_html_table_dpds(dpds_rechazados, "DPDs Rechazados por Calidad")
                html_content += f"<h3>DPDs Rechazados por Calidad ({len(dpds_rechazados)})</h3>\n{tabla_rechazados}\n"
            
            html_content += generate_html_footer()
            return html_content
            
        except Exception as e:
            LoggingHelper.log_database_error("build_calidad_html", "construccion_html", str(e))
            raise

    def build_economia_html(self, dpds_sin_pedido: List[Dict]) -> str:
        """Construye HTML para tareas de economía como en el VBS legacy"""
        try:
            html_content = generate_html_header("Tareas Diarias Economía", self.css_content)
            
            if dpds_sin_pedido:
                tabla_html = self.generate_html_table_dpds(dpds_sin_pedido, "DPDs Fin Agenda Técnica por Recepcionar")
                html_content += f"<h3>DPDs Fin Agenda Técnica por Recepcionar ({len(dpds_sin_pedido)})</h3>\n{tabla_html}\n"
            
            html_content += generate_html_footer()
            return html_content
            
        except Exception as e:
            LoggingHelper.log_database_error("build_economia_html", "construccion_html", str(e))
            raise

    def build_tecnico_html(self, usuario: str, facturas: List[Dict], dpds_sin_pedido: List[Dict]) -> str:
        """Construye HTML agrupado para un técnico específico como en el VBS legacy"""
        try:
            html_content = generate_html_header(f"Tareas Diarias Técnico - {usuario}", self.css_content)
            
            # Agregar facturas pendientes si existen
            if facturas:
                tabla_facturas = self.generate_html_table_facturas(facturas, "Facturas Pendientes de Visado Técnico")
                html_content += f"<h3>Facturas Pendientes de Visado Técnico ({len(facturas)})</h3>\n{tabla_facturas}\n"
            
            # Agregar DPDs sin pedido si existen
            if dpds_sin_pedido:
                tabla_dpds = self.generate_html_table_dpds(dpds_sin_pedido, "DPDs sin Pedido")
                html_content += f"<h3>DPDs sin Pedido ({len(dpds_sin_pedido)})</h3>\n{tabla_dpds}\n"
            
            html_content += generate_html_footer()
            return html_content
            
        except Exception as e:
            LoggingHelper.log_database_error("build_tecnico_html", usuario, str(e))
            raise

    def register_grouped_notification(self, correo: str, subject: str, html_content: str, dry_run: bool = False):
        """Registra notificación agrupada en la base de datos (sin envío real, como en BRASS)"""
        try:
            if dry_run:
                LoggingHelper.log_email_action("register", "agrupado", correo, "DRY-RUN", subject)
                return

            # Solo registrar en base de datos (sin envío real) usando función común
            if correo and "@" in correo:
                LoggingHelper.log_email_action("register", "agrupado", correo, "REGISTRADO", subject)

                # Usar la función común register_email_in_database con Aplicacion="Tareas"
                utils.register_email_in_database(
                    self.correos_db,
                    "Tareas",  # Usar "Tareas" como especificado
                    subject,
                    html_content,
                    correo,
                    ""  # admin_emails vacío
                )

        except Exception as e:
            LoggingHelper.log_database_error("register_grouped_notification", correo, str(e))
            raise

    def process_tecnicos_tasks(self, dry_run: bool = False) -> int:
        """Procesa todas las tareas técnicas y envía un email agrupado por técnico"""
        tecnicos_enviados = 0
        has_errors = False
        
        try:
            # Obtener todos los usuarios técnicos
            usuarios_tecnicos = self.get_usuarios_tecnicos()
            if not usuarios_tecnicos:
                LoggingHelper.log_skip_action("No hay usuarios técnicos configurados", "process_tecnicos_tasks")
                return 0

            for usuario_data in usuarios_tecnicos:
                usuario = usuario_data['UsuarioRed']
                correo = usuario_data['CorreoUsuario']
                
                try:
                    # Obtener todas las tareas para este técnico
                    facturas = self.get_facturas_pendientes_visado_tecnico(usuario)
                    dpds_sin_pedido = self.get_dpds_sin_pedido_for_user(usuario)
                    
                    # Si no hay tareas para este técnico, continuar
                    if not facturas and not dpds_sin_pedido:
                        continue
                    
                    # Construir HTML agrupado para este técnico
                    html_content = self.build_tecnico_html(usuario, facturas, dpds_sin_pedido)
                    
                    # Enviar email agrupado
                    self.register_grouped_notification(
                        correo, 
                        f"Tareas Diarias Técnico - {usuario}", 
                        html_content, 
                        dry_run
                    )
                    
                    tecnicos_enviados += 1
                    
                except Exception as e:
                    LoggingHelper.log_database_error("process_tecnicos_tasks", usuario, str(e))
                    has_errors = True
                    continue
                    
            # Si hubo errores, lanzar excepción para que sea capturada por el método run
            if has_errors:
                raise Exception("Errores durante el procesamiento de técnicos")
                    
            return tecnicos_enviados
            
        except Exception as e:
            LoggingHelper.log_database_error("process_tecnicos_tasks", "general", str(e))
            # Re-lanzar la excepción para que sea capturada por el método run
            raise

    def execute_task(self, dry_run: bool = False, force: bool = False) -> bool:
        """Ejecuta la tarea principal de AGEDYS"""
        try:
            LoggingHelper.log_phase_start("Ejecución de tarea AGEDYS",
                                        f"Modo: {'DRY-RUN' if dry_run else 'PRODUCCIÓN'}")

            # Verificar si la tarea debe ejecutarse
            if not force and is_task_completed_today(self.tareas_db, "AGEDYSDiario"):
                LoggingHelper.log_skipped_action("execute_task", "AGEDYS", "Tarea ya completada hoy")
                return True

            if not force and not should_execute_task(self.tareas_db, f"AGEDYS_{APP_ID}", 1):
                LoggingHelper.log_skipped_action("execute_task", "AGEDYS", "No es momento de ejecutar según frecuencia")
                return True

            # Ejecutar el proceso principal
            success = self.run(dry_run=dry_run)

            # Registrar completación de la tarea solo cuando no es dry_run
            if not dry_run:
                register_task_completion(self.tareas_db, "AGEDYSDiario")

            LoggingHelper.log_phase_end("Ejecución de tarea AGEDYS", success)
            return success

        except Exception as e:
            LoggingHelper.log_database_error("execute_task", "proceso_principal", str(e))
            LoggingHelper.log_phase_end("Ejecución de tarea AGEDYS", False)
            # Registrar fallo en caso de excepción solo cuando no es dry_run
            if not dry_run:
                register_task_completion(self.tareas_db, "AGEDYSDiario")
            return False

    def run(self, dry_run: bool = False) -> bool:
        """Ejecuta el proceso principal de AGEDYS replicando la lógica del VBS legacy"""
        has_errors = False

        try:
            LoggingHelper.log_phase_start("AGEDYS", "Iniciando procesamiento completo como en legacy VBS")

            # FASE CALIDAD: Un solo email con todas las tareas de calidad
            LoggingHelper.log_phase_start("Calidad", "Procesamiento de tareas para usuarios de calidad")
            try:
                self.process_calidad_tasks(dry_run)
                LoggingHelper.log_phase_end("Calidad", True, 1)
            except Exception as e:
                LoggingHelper.log_database_error("process_calidad_tasks", "calidad", str(e))
                has_errors = True
                LoggingHelper.log_phase_end("Calidad", False, 0)

            # FASE ECONOMÍA: Un solo email con todas las tareas de economía
            LoggingHelper.log_phase_start("Economía", "Procesamiento de tareas para usuarios de economía")
            try:
                self.process_economia_tasks(dry_run)
                LoggingHelper.log_phase_end("Economía", True, 1)
            except Exception as e:
                LoggingHelper.log_database_error("process_economia_tasks", "economia", str(e))
                has_errors = True
                LoggingHelper.log_phase_end("Economía", False, 0)

            # FASE TÉCNICOS: Un solo email por técnico con todas sus tareas agrupadas
            LoggingHelper.log_phase_start("Técnicos", "Procesamiento de tareas para usuarios técnicos")
            try:
                tecnicos_enviados = self.process_tecnicos_tasks(dry_run)
                LoggingHelper.log_phase_end("Técnicos", True, tecnicos_enviados)
            except Exception as e:
                LoggingHelper.log_database_error("process_tecnicos_tasks", "tecnicos", str(e))
                has_errors = True
                LoggingHelper.log_phase_end("Técnicos", False, 0)

            # Si hubo errores, devolver False
            if has_errors:
                LoggingHelper.log_phase_end("AGEDYS", False)
                return False

            LoggingHelper.log_phase_end("AGEDYS", True)
            return True

        except Exception as e:
            LoggingHelper.log_database_error("run", "proceso_principal", str(e))
            LoggingHelper.log_phase_end("AGEDYS", False)
            return False

    def has_emails_sent_today(self) -> bool:
        """Verifica si se han registrado emails hoy para AGEDYS (aplicación Tareas)"""
        try:
            from datetime import date
            today = date.today()

            # Usar formato de fecha de Access #mm/dd/yyyy#
            fecha_access = f"#{today.strftime('%m/%d/%Y')}#"

            query = f"""
                SELECT COUNT(*) as Count
                FROM TbCorreosEnviados
                WHERE Aplicacion = 'Tareas'
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
    def run_static(dry_run: bool = False, force: bool = False) -> bool:
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
