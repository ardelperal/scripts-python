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


class AgedysManager:
    """Gestor principal para las tareas de AGEDYS"""
    
    def __init__(self):
        # Obtener la cadena de conexión para AGEDYS desde config
        agedys_connection_string = config.get_db_agedys_connection_string()
        self.db = AccessDatabase(agedys_connection_string)
        
        # Conexión a la base de datos de tareas para consultas de usuarios
        tareas_connection_string = config.get_db_tareas_connection_string()
        self.tareas_db = AccessDatabase(tareas_connection_string)
        
        # Conexión a la base de datos de correos
        self.correos_db = AccessDatabase(config.get_db_correos_connection_string())
        
        self.css_content = load_css_content(config.css_file_path)
        
    def get_usuarios_facturas_pendientes_visado_tecnico(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con facturas pendientes de visado técnico"""
        # Basado exactamente en getColUsuariosFacturasPendientesVisadoTecnico del VBS
        
        # Query principal con TbUsuariosAplicaciones (exactamente como en el VBS)
        query_with_usuarios_aplicaciones = """
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed
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
        
        UNION
        
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed 
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
        
        UNION
        
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed 
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
        
        UNION
        
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed 
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
        
        # Query alternativa para bases de datos locales sin TbUsuariosAplicaciones
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
            # Intentar primero con la query completa
            usuarios = self.db.execute_query(query_with_usuarios_aplicaciones)
            # Convertir a formato esperado con CorreoUsuario
            result = []
            for usuario in usuarios:
                result.append({
                    'UsuarioRed': usuario['UsuarioRed'],
                    'CorreoUsuario': f"{usuario['UsuarioRed']}@telefonica.com"
                })
            return result
        except Exception as e:
            logger.warning(f"Error con TbUsuariosAplicaciones, usando query alternativa: {e}")
            try:
                # Si falla, usar la query alternativa
                usuarios = self.db.execute_query(query_fallback)
                result = []
                for usuario in usuarios:
                    result.append({
                        'UsuarioRed': usuario['UsuarioRed'],
                        'CorreoUsuario': f"{usuario['UsuarioRed']}@telefonica.com"
                    })
                return result
            except Exception as e2:
                logger.error(f"Error obteniendo usuarios facturas pendientes: {e2}")
                return []
    
    def get_facturas_pendientes_visado_tecnico(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene facturas pendientes de visado técnico para un usuario"""
        # Basado exactamente en getFacturasPendientesVisadoTecnico del VBS
        
        # Primera query: facturas donde el usuario es responsable con CorreoSiempre='Sí'
        query1 = """
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
        AND TbExpedientesResponsables.IdUsuario = (SELECT Id FROM TbUsuariosAplicaciones WHERE UsuarioRed = ?)
        """
        
        # Segunda query: facturas sin visado donde el usuario es responsable con CorreoSiempre='Sí'
        query2 = """
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
        AND TbExpedientesResponsables.IdUsuario = (SELECT Id FROM TbUsuariosAplicaciones WHERE UsuarioRed = ?)
        """
        
        # Tercera query: facturas donde el usuario es PETICIONARIO (AGEDYSGenerico='Sí')
        query3 = """
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
        AND TbProyectos.PETICIONARIO = ?
        """
        
        # Cuarta query: facturas sin visado donde el usuario es PETICIONARIO (AGEDYSGenerico='Sí')
        query4 = """
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
        AND TbProyectos.PETICIONARIO = ?
        """
        
        try:
            facturas = []
            
            # Ejecutar las 4 queries como en el VBS
            try:
                facturas.extend(self.db.execute_query(query1, (usuario,)))
            except:
                pass  # Si falla por TbUsuariosAplicaciones, continuar
                
            try:
                facturas.extend(self.db.execute_query(query2, (usuario,)))
            except:
                pass  # Si falla por TbUsuariosAplicaciones, continuar
                
            facturas.extend(self.db.execute_query(query3, (usuario,)))
            facturas.extend(self.db.execute_query(query4, (usuario,)))
            
            # Eliminar duplicados basándose en NFactura
            facturas_unicas = {}
            for factura in facturas:
                key = factura.get('NFactura', '')
                if key not in facturas_unicas:
                    facturas_unicas[key] = factura
            
            return list(facturas_unicas.values())
            
        except Exception as e:
            logger.error(f"Error obteniendo facturas pendientes para {usuario}: {e}")
            return []
    
    def get_usuarios_dpds_sin_visado_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con DPDs sin visado por calidad"""
        # Basado en getColUsuariosDPDsSinVisadoPorCalidad del VBS
        query = """
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
        FROM (((TbProyectos INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) 
        INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD) 
        INNER JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) 
        LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
        WHERE TbExpedientes.Pecal <> 'No' 
        AND TbVisadosGenerales.ROFechaRealiza IS NOT NULL 
        AND TbVisadosGenerales.ROFechaVisado IS NULL 
        AND TbVisadosGenerales.ROFechaRechazo IS NULL 
        AND TbProyectos.FechaFinAgendaTecnica IS NULL
        """
        
        try:
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo usuarios DPDs sin visado calidad: {e}")
            return []
    
    def get_dpds_sin_visado_calidad(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene DPDs sin visado por calidad para un usuario"""
        # Basado en getDPDsSinVisadoPorCalidad del VBS
        query = """
        SELECT TbProyectos.CODPROYECTOS, TbProyectos.DESCRIPCION, TbProyectos.PETICIONARIO, 
               TbProyectos.FECHAPETICION, TbExpedientes.CodExp, TbUsuariosAplicaciones.Nombre AS ResponsableCalidad 
        FROM (((TbProyectos INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) 
        INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD) 
        INNER JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) 
        LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
        WHERE TbExpedientes.Pecal <> 'No' 
        AND TbVisadosGenerales.ROFechaRealiza IS NOT NULL 
        AND TbVisadosGenerales.ROFechaVisado IS NULL 
        AND TbVisadosGenerales.ROFechaRechazo IS NULL 
        AND TbProyectos.FechaFinAgendaTecnica IS NULL
        AND TbUsuariosAplicaciones.UsuarioRed = ?
        """
        
        try:
            return self.db.execute_query(query, (usuario,))
        except Exception as e:
            logger.error(f"Error obteniendo DPDs sin visado calidad para {usuario}: {e}")
            return []
    
    def get_usuarios_dpds_rechazados_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con DPDs rechazados por calidad"""
        # Basado en getColUsuariosDPDsRechazadosPorCalidad del VBS
        query = """
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
        FROM (((TbProyectos INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) 
        INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD) 
        INNER JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) 
        LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableTecnico = TbUsuariosAplicaciones.Id 
        WHERE TbExpedientes.Pecal <> 'No' 
        AND TbVisadosGenerales.ROFechaRealiza IS NOT NULL 
        AND TbVisadosGenerales.ROFechaRechazo IS NOT NULL 
        AND TbProyectos.FechaFinAgendaTecnica IS NULL
        """
        
        try:
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo usuarios DPDs rechazados calidad: {e}")
            return []
    
    def get_dpds_rechazados_calidad(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene DPDs rechazados por calidad para un usuario"""
        # Basado en getDPDsRechazadosPorCalidad del VBS
        query = """
        SELECT TbProyectos.CODPROYECTOS, TbProyectos.DESCRIPCION, TbProyectos.PETICIONARIO, 
               TbProyectos.FECHAPETICION, TbExpedientes.CodExp, TbUsuariosAplicaciones.Nombre AS ResponsableTecnico,
               TbVisadosGenerales.ROObservaciones
        FROM (((TbProyectos INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) 
        INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD) 
        INNER JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) 
        LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableTecnico = TbUsuariosAplicaciones.Id 
        WHERE TbExpedientes.Pecal <> 'No' 
        AND TbVisadosGenerales.ROFechaRealiza IS NOT NULL 
        AND TbVisadosGenerales.ROFechaRechazo IS NOT NULL 
        AND TbProyectos.FechaFinAgendaTecnica IS NULL
        AND TbUsuariosAplicaciones.UsuarioRed = ?
        """
        
        try:
            return self.db.execute_query(query, (usuario,))
        except Exception as e:
            logger.error(f"Error obteniendo DPDs rechazados calidad para {usuario}: {e}")
            return []
    
    def get_usuarios_dpds_pendientes_recepcion_economica(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios con DPDs pendientes de recepción económica"""
        # Basado en getColUsuariosDPDsPendientesRecepcionEconomica del VBS
        query = """
        SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.CorreoUsuario
        FROM (((TbProyectos INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) 
        INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD) 
        INNER JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) 
        LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableEconomico = TbUsuariosAplicaciones.Id 
        WHERE TbExpedientes.Pecal <> 'No' 
        AND TbVisadosGenerales.ROFechaRealiza IS NOT NULL 
        AND TbVisadosGenerales.ROFechaVisado IS NOT NULL 
        AND TbVisadosGenerales.REFechaRealiza IS NULL 
        AND TbProyectos.FechaFinAgendaTecnica IS NULL
        """
        
        try:
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo usuarios DPDs pendientes recepción económica: {e}")
            return []
    
    def get_dpds_pendientes_recepcion_economica(self, usuario: str) -> List[Dict[str, Any]]:
        """Obtiene DPDs pendientes de recepción económica para un usuario"""
        # Basado en getDPDsPendientesRecepcionEconomica del VBS
        query = """
        SELECT TbProyectos.CODPROYECTOS, TbProyectos.DESCRIPCION, TbProyectos.PETICIONARIO, 
               TbProyectos.FECHAPETICION, TbExpedientes.CodExp, TbUsuariosAplicaciones.Nombre AS ResponsableEconomico 
        FROM (((TbProyectos INNER JOIN TbExpedientes ON TbProyectos.IDExpediente = TbExpedientes.IdExpediente) 
        INNER JOIN TbVisadosGenerales ON TbProyectos.CODPROYECTOS = TbVisadosGenerales.NDPD) 
        INNER JOIN TbSuministradoresSAP ON TbProyectos.NAcreedorSAP = TbSuministradoresSAP.AcreedorSAP) 
        LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableEconomico = TbUsuariosAplicaciones.Id 
        WHERE TbExpedientes.Pecal <> 'No' 
        AND TbVisadosGenerales.ROFechaRealiza IS NOT NULL 
        AND TbVisadosGenerales.ROFechaVisado IS NOT NULL 
        AND TbVisadosGenerales.REFechaRealiza IS NULL 
        AND TbProyectos.FechaFinAgendaTecnica IS NULL
        AND TbUsuariosAplicaciones.UsuarioRed = ?
        """
        
        try:
            return self.db.execute_query(query, (usuario,))
        except Exception as e:
            logger.error(f"Error obteniendo DPDs pendientes recepción económica para {usuario}: {e}")
            return []
    
    def get_usuarios_economia(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios del departamento de economía"""
        # Basado en getColusuariosTareas("Economía") del VBS de BRASS
        # Usa el mismo patrón que get_quality_users en utils.py
        query = """
        SELECT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
        FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesTareas ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesTareas.CorreoUsuario
        WHERE TbUsuariosAplicaciones.ParaTareasProgramadas = True
        AND TbUsuariosAplicaciones.FechaBaja IS NULL
        AND TbUsuariosAplicacionesTareas.EsEconomia = 'Sí'
        """
        
        try:
            # Usar la conexión de tareas en lugar de la conexión AGEDYS
            return self.tareas_db.execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo usuarios economía: {e}")
            return []
    
    def get_dpds_fin_agenda_tecnica_por_recepcionar(self) -> List[Dict[str, Any]]:
        """Obtiene DPDs con fin de agenda técnica pendientes de recepción por economía"""
        # Basado en getDPDsConFinAgendaTecnicaPorRecepcionaEconomia del VBS
        query = """
        SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbProyectos.FECHAPETICION, 
               TbProyectos.EXPEDIENTE, TbProyectos.DESCRIPCION
        FROM TbProyectos
        WHERE TbProyectos.ELIMINADO = False 
        AND TbProyectos.FECHARECEPCIONECONOMICA IS NULL
        AND TbProyectos.FechaFinAgendaTecnica IS NOT NULL
        """
        
        try:
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo DPDs fin agenda técnica: {e}")
            return []
    
    def get_usuarios_tareas(self) -> List[Dict[str, Any]]:
        """Obtiene usuarios responsables de tareas (técnicos)"""
        # Basado en getColusuariosTareas("Técnico") del VBS de BRASS
        # Usa el mismo patrón que get_technical_users en utils.py
        query = """
        SELECT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario
        FROM TbUsuariosAplicaciones LEFT JOIN TbUsuariosAplicacionesTareas ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesTareas.CorreoUsuario
        WHERE TbUsuariosAplicaciones.ParaTareasProgramadas = True
        AND TbUsuariosAplicaciones.FechaBaja IS NULL
        AND TbUsuariosAplicacionesTareas.CorreoUsuario IS NULL
        """
        
        try:
            # Usar la conexión de tareas en lugar de la conexión AGEDYS
            return self.tareas_db.execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo usuarios tareas: {e}")
            return []
    
    def get_dpds_sin_pedido(self) -> List[Dict[str, Any]]:
        """Obtiene DPDs sin pedido"""
        # Basado en getDPDsSinPedido del VBS
        query = """
        SELECT TbProyectos.CODPROYECTOS, TbProyectos.PETICIONARIO, TbProyectos.FECHAPETICION, 
               TbProyectos.EXPEDIENTE, TbProyectos.DESCRIPCION
        FROM TbProyectos INNER JOIN TbNPedido ON TbProyectos.CODPROYECTOS = TbNPedido.CODPPD
        WHERE TbProyectos.ELIMINADO = False 
        AND TbNPedido.NPEDIDO IS NULL
        """
        
        try:
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo DPDs sin pedido: {e}")
            return []
    
    def generate_facturas_html_table(self, facturas: List[Dict[str, Any]]) -> str:
        """Genera tabla HTML para facturas pendientes"""
        if not facturas:
            return "<p>No hay facturas pendientes de visado técnico.</p>"
        
        html = """
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <thead style="background-color: #f0f0f0;">
                <tr>
                    <th>Número Factura</th>
                    <th>Proveedor</th>
                    <th>Importe</th>
                    <th>Fecha Recepción</th>
                    <th>Expediente</th>
                    <th>Descripción</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for factura in facturas:
            html += f"""
                <tr>
                    <td>{factura.get('NFactura', factura.get('NumeroFactura', ''))}</td>
                    <td>{factura.get('Suministrador', factura.get('Proveedor', ''))}</td>
                    <td>{factura.get('ImporteFactura', factura.get('Importe', ''))}</td>
                    <td>{format_date(factura.get('FechaRecepcion', factura.get('FechaFactura')))}</td>
                    <td>{factura.get('CodExp', factura.get('Expediente', ''))}</td>
                    <td>{factura.get('DESCRIPCION', factura.get('Descripcion', ''))}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generate_dpds_html_table(self, dpds: List[Dict[str, Any]], tipo: str = 'general') -> str:
        """Genera tabla HTML para DPDs según el tipo"""
        if not dpds:
            return f"<p>No hay DPDs {tipo}.</p>"
        
        if tipo == 'sin_visado_calidad':
            headers = ['Número DPD', 'Descripción', 'Fecha Finalización', 'Responsable Técnico', 'Expediente']
            fields = ['NumeroDPD', 'Descripcion', 'FechaFinalizacion', 'ResponsableTecnico', 'Expediente']
        elif tipo == 'rechazados_calidad':
            headers = ['Número DPD', 'Descripción', 'Fecha Rechazo', 'Motivo Rechazo', 'Responsable Calidad', 'Expediente']
            fields = ['NumeroDPD', 'Descripcion', 'FechaRechazo', 'MotivoRechazo', 'ResponsableCalidad', 'Expediente']
        elif tipo == 'fin_agenda_tecnica':
            headers = ['Número DPD', 'Descripción', 'Fecha Fin Agenda', 'Responsable Técnico', 'Expediente', 'Importe Estimado']
            fields = ['NumeroDPD', 'Descripcion', 'FechaFinAgendaTecnica', 'ResponsableTecnico', 'Expediente', 'ImporteEstimado']
        elif tipo == 'sin_pedido':
            headers = ['Número DPD', 'Descripción', 'Fecha Aprobación', 'Responsable Calidad', 'Expediente', 'Importe Estimado']
            fields = ['NumeroDPD', 'Descripcion', 'FechaAprobacionCalidad', 'ResponsableCalidad', 'Expediente', 'ImporteEstimado']
        else:
            headers = ['Número DPD', 'Descripción', 'Expediente']
            fields = ['NumeroDPD', 'Descripcion', 'Expediente']
        
        html = f"""
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <thead style="background-color: #f0f0f0;">
                <tr>
                    {''.join(f'<th>{header}</th>' for header in headers)}
                </tr>
            </thead>
            <tbody>
        """
        
        for dpd in dpds:
            html += "<tr>"
            for field in fields:
                value = dpd.get(field, '')
                if 'Fecha' in field and value:
                    value = format_date(value)
                html += f"<td>{value}</td>"
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def send_facturas_pendientes_email(self, usuario: str, email: str, facturas: List[Dict[str, Any]], dry_run=False):
        """Registra email con facturas pendientes de visado técnico en la base de datos"""
        if not facturas:
            return
        
        subject = f"AGEDYS - Facturas Pendientes de Visado Técnico - {usuario}"
        
        html_content = generate_html_header("Facturas Pendientes de Visado Técnico", self.css_content)
        html_content += f"<h2>Usuario: {usuario}</h2>"
        html_content += f"<p>Tienes {len(facturas)} factura(s) pendiente(s) de visado técnico:</p>"
        html_content += self.generate_facturas_html_table(facturas)
        html_content += generate_html_footer()
        
        try:
            if dry_run:
                logger.info(f"DRY-RUN: Se habría registrado email para {usuario} ({email}) - {len(facturas)} facturas pendientes")
            else:
                # Solo registrar en la base de datos, no enviar email real
                register_email_in_database(self.correos_db, 'AGEDYS', subject, html_content, email)
                logger.info(f"Email registrado para {usuario} ({email}) - {len(facturas)} facturas pendientes")
        except Exception as e:
            logger.error(f"Error registrando email para {usuario}: {e}")
    
    def send_dpds_sin_visado_email(self, usuario: str, email: str, dpds: List[Dict[str, Any]], dry_run=False):
        """Registra email con DPDs sin visado de calidad en la base de datos"""
        if not dpds:
            return
        
        subject = f"AGEDYS - DPDs Sin Visado de Calidad - {usuario}"
        
        html_content = generate_html_header("DPDs Sin Visado de Calidad", self.css_content)
        html_content += f"<h2>Usuario: {usuario}</h2>"
        html_content += f"<p>Tienes {len(dpds)} DPD(s) pendiente(s) de visado de calidad:</p>"
        html_content += self.generate_dpds_html_table(dpds, 'sin_visado_calidad')
        html_content += generate_html_footer()
        
        try:
            if dry_run:
                logger.info(f"DRY-RUN: Se habría registrado email para {usuario} ({email}) - {len(dpds)} DPDs sin visado")
            else:
                # Solo registrar en la base de datos, no enviar email real
                register_email_in_database(self.correos_db, 'AGEDYS', subject, html_content, email)
                logger.info(f"Email registrado para {usuario} ({email}) - {len(dpds)} DPDs sin visado")
        except Exception as e:
            logger.error(f"Error registrando email para {usuario}: {e}")
    
    def send_dpds_rechazados_email(self, usuario: str, email: str, dpds: List[Dict[str, Any]], dry_run=False):
        """Registra email con DPDs rechazados por calidad en la base de datos"""
        if not dpds:
            return
        
        subject = f"AGEDYS - DPDs Rechazados por Calidad - {usuario}"
        
        html_content = generate_html_header("DPDs Rechazados por Calidad", self.css_content)
        html_content += f"<h2>Usuario: {usuario}</h2>"
        html_content += f"<p>Tienes {len(dpds)} DPD(s) rechazado(s) por calidad en los últimos 7 días:</p>"
        html_content += self.generate_dpds_html_table(dpds, 'rechazados_calidad')
        html_content += generate_html_footer()
        
        try:
            if dry_run:
                logger.info(f"DRY-RUN: Se habría registrado email para {usuario} ({email}) - {len(dpds)} DPDs rechazados")
            else:
                # Solo registrar en la base de datos, no enviar email real
                register_email_in_database(self.correos_db, 'AGEDYS', subject, html_content, email)
                logger.info(f"Email registrado para {usuario} ({email}) - {len(dpds)} DPDs rechazados")
        except Exception as e:
            logger.error(f"Error registrando email para {usuario}: {e}")
    
    def send_economia_email(self, usuarios_economia: List[Dict[str, Any]], dpds: List[Dict[str, Any]], dry_run=False):
        """Registra email con DPDs pendientes de recepción en la base de datos"""
        if not dpds or not usuarios_economia:
            return
        
        subject = "AGEDYS - DPDs con Fin de Agenda Técnica Pendientes de Recepción"
        
        html_content = generate_html_header("DPDs Pendientes de Recepción por Economía", self.css_content)
        html_content += f"<p>Hay {len(dpds)} DPD(s) con fin de agenda técnica pendiente(s) de recepción:</p>"
        html_content += self.generate_dpds_html_table(dpds, 'fin_agenda_tecnica')
        html_content += generate_html_footer()
        
        for usuario_economia in usuarios_economia:
            email = usuario_economia.get('CorreoUsuario')  
            usuario = usuario_economia.get('UsuarioRed')   # Cambiar de 'Nombre' a 'UsuarioRed'
            
            if email:
                try:
                    if dry_run:
                        logger.info(f"DRY-RUN: Se habría registrado email para economía {usuario} ({email}) - {len(dpds)} DPDs pendientes")
                    else:
                        # Solo registrar en la base de datos, no enviar email real
                        register_email_in_database(self.correos_db, 'AGEDYS', subject, html_content, email)
                        logger.info(f"Email registrado para economía {usuario} ({email}) - {len(dpds)} DPDs pendientes")
                except Exception as e:
                    logger.error(f"Error registrando email para economía {usuario}: {e}")
    
    def send_dpds_sin_pedido_email(self, usuario: str, email: str, dpds: List[Dict[str, Any]], dry_run=False):
        """Registra email con DPDs sin pedido en la base de datos"""
        if not dpds:
            return
        
        subject = f"AGEDYS - DPDs Sin Pedido - {usuario}"
        
        html_content = generate_html_header("DPDs Sin Pedido", self.css_content)
        html_content += f"<h2>Usuario: {usuario}</h2>"
        html_content += f"<p>Tienes {len(dpds)} DPD(s) aprobado(s) por calidad sin pedido:</p>"
        html_content += self.generate_dpds_html_table(dpds, 'sin_pedido')
        html_content += generate_html_footer()
        
        try:
            if dry_run:
                logger.info(f"DRY-RUN: Se habría registrado email para {usuario} ({email}) - {len(dpds)} DPDs sin pedido")
            else:
                # Solo registrar en la base de datos, no enviar email real
                register_email_in_database(self.correos_db, 'AGEDYS', subject, html_content, email)
                logger.info(f"Email registrado para {usuario} ({email}) - {len(dpds)} DPDs sin pedido")
        except Exception as e:
            logger.error(f"Error registrando email para {usuario}: {e}")
    
    def execute_task(self, force=False, dry_run=False):
        """Ejecuta las tareas de AGEDYS con control de frecuencia"""
        try:
            # Obtener conexión a la base de datos de tareas
            from common.database import AccessDatabase
            tareas_db = AccessDatabase(config.get_db_tareas_connection_string())
            
            # Verificar si debe ejecutarse (a menos que sea forzado)
            if not force:
                # Convertir frecuencia a días
                frequency_days = 1 if TASK_FREQUENCY == 'daily' else 7 if TASK_FREQUENCY == 'weekly' else 30
                
                if not should_execute_task(tareas_db, f"AGEDYS_{APP_ID}", frequency_days, logger):
                    logger.info("AGEDYS no necesita ejecutarse según su frecuencia. Use --force para forzar ejecución.")
                    return True
            
            # Ejecutar proceso principal
            success = self.run(dry_run=dry_run)
            
            if success and not dry_run:
                # Registrar ejecución exitosa
                register_task_completion(tareas_db, f"AGEDYS_{APP_ID}")
                logger.info("AGEDYS ejecutado exitosamente")
            elif dry_run:
                logger.info("DRY-RUN: Se habría registrado la ejecución exitosa")
            else:
                register_task_completion(tareas_db, f"AGEDYS_{APP_ID}")
                logger.error("AGEDYS completado con errores")
            
            return success
            
        except Exception as e:
            logger.error(f"Error crítico en AGEDYS: {e}")
            if not dry_run:
                # Obtener conexión a la base de datos de tareas para registrar error
                from common.database import AccessDatabase
                tareas_db = AccessDatabase(config.get_db_tareas_connection_string())
                register_task_completion(tareas_db, f"AGEDYS_{APP_ID}")
            return False
    
    def run(self, dry_run=False):
        """Ejecuta el proceso principal de AGEDYS"""
        logger.info("Iniciando proceso AGEDYS")
        
        try:
            # 1. Facturas pendientes de visado técnico
            logger.info("Procesando facturas pendientes de visado técnico...")
            usuarios_facturas = self.get_usuarios_facturas_pendientes_visado_tecnico()
            
            for usuario_data in usuarios_facturas:
                usuario = usuario_data.get('UsuarioRed')    # Usar UsuarioRed que es lo que devuelve la consulta
                email = usuario_data.get('CorreoUsuario')   
                
                if usuario and email:
                    facturas = self.get_facturas_pendientes_visado_tecnico(usuario)
                    self.send_facturas_pendientes_email(usuario, email, facturas, dry_run)
            
            # 2. DPDs sin visado de calidad
            logger.info("Procesando DPDs sin visado de calidad...")
            usuarios_dpds_calidad = self.get_usuarios_dpds_sin_visado_calidad()
            
            for usuario_data in usuarios_dpds_calidad:
                usuario = usuario_data.get('UsuarioRed')    # Usar UsuarioRed que es lo que devuelve la consulta
                email = usuario_data.get('CorreoUsuario')   
                
                if usuario and email:
                    dpds = self.get_dpds_sin_visado_calidad(usuario)
                    self.send_dpds_sin_visado_email(usuario, email, dpds, dry_run)
            
            # 3. DPDs rechazados por calidad
            logger.info("Procesando DPDs rechazados por calidad...")
            usuarios_dpds_rechazados = self.get_usuarios_dpds_rechazados_calidad()
            
            for usuario_data in usuarios_dpds_rechazados:
                usuario = usuario_data.get('UsuarioRed')    # Usar UsuarioRed que es lo que devuelve la consulta
                email = usuario_data.get('CorreoUsuario')   
                
                if usuario and email:
                    dpds = self.get_dpds_rechazados_calidad(usuario)
                    self.send_dpds_rechazados_email(usuario, email, dpds, dry_run)
            
            # 4. DPDs con fin de agenda técnica para economía
            logger.info("Procesando DPDs para economía...")
            usuarios_economia = self.get_usuarios_economia()
            dpds_economia = self.get_dpds_fin_agenda_tecnica_por_recepcionar()
            
            if dpds_economia:
                self.send_economia_email(usuarios_economia, dpds_economia, dry_run)
            
            # 5. DPDs sin pedido
            logger.info("Procesando DPDs sin pedido...")
            dpds_sin_pedido = self.get_dpds_sin_pedido()
            
            # Agrupar DPDs por usuario (PETICIONARIO)
            dpds_por_usuario = {}
            for dpd in dpds_sin_pedido:
                peticionario = dpd.get('PETICIONARIO')
                if peticionario:
                    if peticionario not in dpds_por_usuario:
                        dpds_por_usuario[peticionario] = []
                    dpds_por_usuario[peticionario].append(dpd)
            
            # Obtener usuarios técnicos para enviar emails
            usuarios_tareas = self.get_usuarios_tareas()
            usuarios_dict = {u.get('UsuarioRed'): u for u in usuarios_tareas}
            
            # Enviar emails a cada usuario con sus DPDs
            for peticionario, dpds in dpds_por_usuario.items():
                if peticionario in usuarios_dict:
                    usuario_data = usuarios_dict[peticionario]
                    email = usuario_data.get('CorreoUsuario')
                    if email:
                        self.send_dpds_sin_pedido_email(peticionario, email, dpds, dry_run)
            
            logger.info("Proceso AGEDYS completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error en proceso AGEDYS: {e}")
            return False