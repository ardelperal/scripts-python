"""
Módulo No Conformidades - Gestión de no conformidades y ARAPs
Nueva versión usando la arquitectura de tareas base
"""
import logging
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in os.sys.path:
    os.sys.path.insert(0, src_dir)

from common.base_task import TareaDiaria
from common.config import config
from common.database import AccessDatabase
from src.common.utils import load_css_content, safe_str, generate_html_header, generate_html_footer
from src.common.utils import register_email_in_database

logger = logging.getLogger(__name__)


class NoConformidadesManager(TareaDiaria):
    """Manager de No Conformidades usando la nueva arquitectura"""
    
    def __init__(self):
        # Inicializar con los parámetros requeridos por TareaDiaria
        super().__init__(
            name="NoConformidades",
            script_filename="run_no_conformidades.py",
            task_names=["NCTecnico", "NCCalidad"],  # Nombres de las tareas en la BD
            frequency_days=int(os.getenv('NC_FRECUENCIA_DIAS', '1'))
        )
        
        # Configuración específica
        self.dias_alerta_arapc = int(os.getenv('NC_DIAS_ALERTA_ARAPC', '15'))
        self.dias_alerta_nc = int(os.getenv('NC_DIAS_ALERTA_NC', '16'))
        self.id_aplicacion = int(os.getenv('NC_ID_APLICACION', '3'))
        
        # Conexiones a bases de datos
        self.db_nc = None
        # db_tareas ya se inicializa en BaseTask, no lo sobrescribimos
        
        # Cache para usuarios
        self._admin_users = None
        self._admin_emails = None
        self._quality_users = None
        self._quality_emails = None
        self._technical_users = None
        
        # CSS
        self.css_content = self._load_css_content()
    
    def _load_css_content(self) -> str:
        """Carga el contenido CSS"""
        try:
            return load_css_content(config.css_file_path)
        except Exception as e:
            self.logger.error("Error cargando CSS: {}".format(e))
            return "/* CSS no disponible */"
    
    def _get_nc_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de No Conformidades"""
        if self.db_nc is None:
            connection_string = config.get_db_no_conformidades_connection_string()
            self.db_nc = AccessDatabase(connection_string)
        return self.db_nc
    
    def _get_tareas_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de Tareas"""
        # Usar la conexión ya inicializada en BaseTask
        return self.db_tareas
    
    def close_connections(self):
        """Cierra las conexiones a las bases de datos"""
        super().close_connections()
        if self.db_nc:
            try:
                self.db_nc.disconnect()
                self.db_nc = None
            except Exception as e:
                self.logger.warning("Error cerrando conexión NC: {}".format(e))
    
    def _format_date_for_access(self, fecha) -> str:
        """Formatea una fecha para uso en consultas SQL de Access"""
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha, '%m/%d/%Y').date()
                except ValueError:
                    self.logger.error("Formato de fecha no reconocido: {}".format(fecha))
                    return "#01/01/1900#"
        elif isinstance(fecha, datetime):
            fecha = fecha.date()
        elif hasattr(fecha, 'date'):
            fecha = fecha.date()
        
        return f"#{fecha.strftime('%m/%d/%Y')}#"
    
    def get_nc_proximas_caducar(self) -> List[Dict[str, Any]]:
        """
        Obtiene las No Conformidades próximas a caducar (entre 1 y 15 días)
        Basado en la consulta del archivo legacy NoConformidades.vbs
        """
        try:
            db_nc = self._get_nc_connection()
            
            # Consulta basada en el legacy: NCs con acciones sin finalizar y próximas a caducar
            query = """
                SELECT DISTINCT DateDiff('d',Now(),[FPREVCIERRE]) AS DiasParaCierre, 
                       TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                       TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
                       TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE 
                FROM TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas 
                     ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
                     ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad 
                WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) 
                       AND ((DateDiff('d',Now(),[FPREVCIERRE])) > 0 AND (DateDiff('d',Now(),[FPREVCIERRE])) < 16)
                       AND ((TbNoConformidades.Borrado) = False))
                ORDER BY TbNoConformidades.FPREVCIERRE
            """
            
            result = db_nc.execute_query(query)
            self.logger.info("Encontradas {} NCs próximas a caducar".format(len(result)))
            return result
            
        except Exception as e:
            self.logger.error("Error obteniendo NCs próximas a caducar: {}".format(e))
            return []
    
    def get_nc_caducadas(self) -> List[Dict[str, Any]]:
        """
        Obtiene las No Conformidades ya caducadas
        Basado en la consulta del archivo legacy NoConformidades.vbs
        """
        try:
            db_nc = self._get_nc_connection()
            
            # Consulta basada en el legacy: NCs caducadas sin cerrar
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico,
                       TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
                       TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE,
                       DateDiff('d', TbNoConformidades.FPREVCIERRE, Now()) AS DiasVencidas
                FROM TbNoConformidades 
                WHERE (((TbNoConformidades.FECHACIERRE) Is Null) 
                       AND ((DateDiff('d',Now(),[FPREVCIERRE])) < 0) 
                       AND ((TbNoConformidades.Borrado) = False))
                ORDER BY TbNoConformidades.FPREVCIERRE
            """
            
            result = db_nc.execute_query(query)
            self.logger.info("Encontradas {} NCs caducadas".format(len(result)))
            return result
            
        except Exception as e:
            self.logger.error("Error obteniendo NCs caducadas: {}".format(e))
            return []
    
    def get_arapcs_proximas_vencer(self) -> List[Dict[str, Any]]:
        """
        Obtiene las ARAPs próximas a vencer (entre 8 y 15 días)
        Basado en la consulta del archivo legacy NoConformidades.vbs
        """
        try:
            db_nc = self._get_nc_connection()
            
            # Consulta basada en el legacy para ARAPs próximas a vencer
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada, 
                       TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada, 
                       TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista, 
                       TbUsuariosAplicaciones.Nombre AS RESPONSABLECALIDAD, 
                       DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaVencer, 
                       TbExpedientes.Nemotecnico 
                FROM ((TbNoConformidades LEFT JOIN TbUsuariosAplicaciones 
                       ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed) 
                       INNER JOIN (TbNCAccionCorrectivas INNER JOIN (TbNCAccionesRealizadas LEFT JOIN TbNCARAvisos 
                       ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR) 
                       ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
                       ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad) 
                       LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente 
                WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) 
                       AND ((DateDiff('d',Now(),[FechaFinPrevista])) >= 8 AND (DateDiff('d',Now(),[FechaFinPrevista])) <= 15) 
                       AND ((TbNCARAvisos.IDCorreo15) Is Null))
                ORDER BY TbNCAccionesRealizadas.FechaFinPrevista
            """
            
            result = db_nc.execute_query(query)
            self.logger.info("Encontradas {} ARAPs próximas a vencer".format(len(result)))
            return result
            
        except Exception as e:
            self.logger.error("Error obteniendo ARAPs próximas a vencer: {}".format(e))
            return []
    
    def get_arapcs_vencidas(self) -> List[Dict[str, Any]]:
        """
        Obtiene las ARAPs ya vencidas (0 días o menos)
        Basado en la consulta del archivo legacy NoConformidades.vbs
        """
        try:
            db_nc = self._get_nc_connection()
            
            # Consulta basada en el legacy para ARAPs vencidas
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada, 
                       TbNCAccionCorrectivas.AccionCorrectiva AS Accion, TbNCAccionesRealizadas.AccionRealizada AS Tarea, 
                       TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista, 
                       TbUsuariosAplicaciones.Nombre AS RESPONSABLECALIDAD, 
                       DateDiff('d',Now(),[FechaFinPrevista]) AS DiasVencidas, 
                       TbExpedientes.Nemotecnico,
                       TbNoConformidades.RESPONSABLETELEFONICA
                FROM ((TbNoConformidades LEFT JOIN TbUsuariosAplicaciones 
                       ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed) 
                       INNER JOIN (TbNCAccionCorrectivas INNER JOIN (TbNCAccionesRealizadas LEFT JOIN TbNCARAvisos 
                       ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR) 
                       ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
                       ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad) 
                       LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente 
                WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) 
                       AND ((DateDiff('d',Now(),[FechaFinPrevista])) <= 0) 
                       AND ((TbNCARAvisos.IDCorreo0) Is Null))
                ORDER BY TbNCAccionesRealizadas.FechaFinPrevista
            """
            
            result = db_nc.execute_query(query)
            self.logger.info("Encontradas {} ARAPs vencidas".format(len(result)))
            return result
            
        except Exception as e:
            self.logger.error("Error obteniendo ARAPs vencidas: {}".format(e))
            return []
    
    def get_nc_pendientes_eficacia(self) -> List[Dict[str, Any]]:
        """
        Obtiene las NCs pendientes de control de eficacia
        Basado en la consulta del archivo legacy NoConformidades.vbs
        """
        try:
            db_nc = self._get_nc_connection()
            
            # Consulta basada en el legacy para NCs pendientes de control de eficacia
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                       TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
                       TbNoConformidades.FECHACIERRE, TbNoConformidades.FechaPrevistaControlEficacia, 
                       DateDiff('d',Now(),[FechaPrevistaControlEficacia]) AS Dias 
                FROM TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas 
                     ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
                     ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad 
                WHERE (((DateDiff('d',Now(),[FechaPrevistaControlEficacia])) < 30) 
                       AND (Not (TbNCAccionesRealizadas.FechaFinReal) Is Null) 
                       AND ((TbNoConformidades.RequiereControlEficacia) = 'Sí') 
                       AND ((TbNoConformidades.FechaControlEficacia) Is Null))
                ORDER BY TbNoConformidades.FechaPrevistaControlEficacia
            """
            
            result = db_nc.execute_query(query)
            self.logger.info("Encontradas {} NCs pendientes de control de eficacia".format(len(result)))
            return result
            
        except Exception as e:
            self.logger.error("Error obteniendo NCs pendientes de eficacia: {}".format(e))
            return []
    
    def get_arapcs_para_replanificar(self) -> List[Dict[str, Any]]:
        """
        Obtiene las ARAPs que requieren replanificación
        Basado en la consulta del archivo legacy NoConformidades.vbs
        """
        try:
            db_nc = self._get_nc_connection()
            
            # Consulta basada en el legacy para ARAPs que requieren replanificación
            query = """
                SELECT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                       TbNCAccionCorrectivas.AccionCorrectiva AS Accion, 
                       TbNCAccionesRealizadas.AccionRealizada AS Tarea, 
                       TbUsuariosAplicaciones.Nombre AS RESPONSABLETELEFONICA, 
                       TbNoConformidades.RESPONSABLECALIDAD, 
                       TbNCAccionesRealizadas.FechaFinPrevista,  
                       DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) AS Dias 
                FROM (TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas 
                      ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
                      ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad) 
                      LEFT JOIN TbUsuariosAplicaciones ON TbNCAccionesRealizadas.Responsable = TbUsuariosAplicaciones.UsuarioRed 
                WHERE (((DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista])) < 16) 
                       AND ((TbNCAccionesRealizadas.FechaFinReal) Is Null))
                ORDER BY TbNCAccionesRealizadas.FechaFinPrevista
            """
            
            result = db_nc.execute_query(query)
            self.logger.info("Encontradas {} ARAPs para replanificar".format(len(result)))
            return result
            
        except Exception as e:
            self.logger.error("Error obteniendo ARAPs para replanificar: {}".format(e))
            return []
    
    def get_technical_users(self) -> List[Dict[str, Any]]:
        """
        Obtiene los usuarios técnicos usando las funciones comunes
        """
        try:
            return get_users_with_fallback(
                db_connection=self._get_nc_connection(),
                id_aplicacion=self.id_aplicacion_nc,
                tipo_usuario='Técnico',
                logger=self.logger
            )
        except Exception as e:
            self.logger.error("Error obteniendo usuarios técnicos: {}".format(e))
            return []
    
    def get_quality_users(self) -> List[Dict[str, Any]]:
        """
        Obtiene los usuarios de calidad usando las funciones comunes
        """
        try:
            return get_users_with_fallback(
                db_connection=self._get_nc_connection(),
                id_aplicacion=self.id_aplicacion_nc,
                tipo_usuario='Calidad',
                logger=self.logger
            )
        except Exception as e:
            self.logger.error("Error obteniendo usuarios de calidad: {}".format(e))
            return []
    
    def get_admin_users(self) -> List[Dict[str, Any]]:
        """
        Obtiene los usuarios administradores usando las funciones comunes
        """
        try:
            return get_users_with_fallback(
                db_connection=self._get_nc_connection(),
                id_aplicacion=self.id_aplicacion_nc,
                tipo_usuario='Administrador',
                logger=self.logger
            )
        except Exception as e:
            self.logger.error("Error obteniendo usuarios administradores: {}".format(e))
            return []
    
    def get_admin_emails_string(self) -> str:
        """
        Obtiene la cadena de correos de administradores separados por ;
        """
        if self._admin_emails is not None:
            return self._admin_emails
        
        admin_users = self.get_admin_users()
        emails = [user['CorreoUsuario'] for user in admin_users if user['CorreoUsuario']]
        self._admin_emails = ';'.join(emails)
        return self._admin_emails
    
    def get_quality_emails_string(self) -> str:
        """
        Obtiene la cadena de correos de calidad separados por ;
        """
        if self._quality_emails is not None:
            return self._quality_emails
        
        quality_users = self.get_quality_users()
        emails = [user['CorreoUsuario'] for user in quality_users if user['CorreoUsuario']]
        self._quality_emails = ';'.join(emails)
        return self._quality_emails
    
    def generate_technical_report_html(self, nc_proximas: List[Dict], nc_caducadas: List[Dict], 
                                     arapcs_proximas: List[Dict], arapcs_vencidas: List[Dict]) -> str:
        """
        Genera el reporte HTML para técnicos
        """
        title = "INFORME DE NO CONFORMIDADES Y ARAPCS - TÉCNICOS"
        html_content = generate_html_header(title, self.css_content)
        
        html_content += f"<h1>{title}</h1>\n"
        html_content += "<br><br>\n"
        
        # Sección de NCs próximas a caducar
        if nc_proximas:
            html_content += self._generate_nc_table_html(nc_proximas, "NO CONFORMIDADES PRÓXIMAS A CADUCAR")
        
        # Sección de NCs caducadas
        if nc_caducadas:
            html_content += self._generate_nc_table_html(nc_caducadas, "NO CONFORMIDADES CADUCADAS")
        
        # Sección de ARAPs próximas a vencer
        if arapcs_proximas:
            html_content += self._generate_arapc_table_html(arapcs_proximas, "ARAPCS PRÓXIMAS A VENCER")
        
        # Sección de ARAPs vencidas
        if arapcs_vencidas:
            html_content += self._generate_arapc_table_html(arapcs_vencidas, "ARAPCS VENCIDAS")
        
        html_content += generate_html_footer()
        return html_content
    
    def generate_quality_report_html(self, nc_eficacia: List[Dict]) -> str:
        """
        Genera el reporte HTML para calidad
        """
        title = "INFORME DE NO CONFORMIDADES PENDIENTES DE CONTROL DE EFICACIA"
        html_content = generate_html_header(title, self.css_content)
        
        html_content += f"<h1>{title}</h1>\n"
        html_content += "<br><br>\n"
        
        if nc_eficacia:
            html_content += self._generate_eficacia_table_html(nc_eficacia)
        
        html_content += generate_html_footer()
        return html_content
    
    def _generate_nc_table_html(self, nc_list: List[Dict], title: str) -> str:
        """Genera tabla HTML para No Conformidades"""
        html = f'<table>\n'
        html += f'<tr>\n<td colspan="7" class="ColespanArriba">{title}</td>\n</tr>\n'
        
        # Encabezados
        html += '<tr>\n'
        html += '<td class="centrado"><strong>NEMOTÉCNICO</strong></td>\n'
        html += '<td class="centrado"><strong>CÓDIGO</strong></td>\n'
        html += '<td class="centrado"><strong>DESCRIPCIÓN</strong></td>\n'
        html += '<td class="centrado"><strong>RESPONSABLE CALIDAD</strong></td>\n'
        html += '<td class="centrado"><strong>FECHA APERTURA</strong></td>\n'
        html += '<td class="centrado"><strong>FECHA PREV. CIERRE</strong></td>\n'
        html += '<td class="centrado"><strong>DÍAS</strong></td>\n'
        html += '</tr>\n'
        
        # Filas de datos
        for nc in nc_list:
            html += '<tr>\n'
            html += f'<td>{safe_str(nc.get("Nemotecnico"))}</td>\n'
            html += f'<td>{safe_str(nc.get("CodigoNoConformidad"))}</td>\n'
            html += f'<td>{safe_str(nc.get("DESCRIPCION"))}</td>\n'
            html += f'<td>{safe_str(nc.get("RESPONSABLECALIDAD"))}</td>\n'
            html += f'<td>{safe_str(nc.get("FECHAAPERTURA"))}</td>\n'
            html += f'<td>{safe_str(nc.get("FPREVCIERRE"))}</td>\n'
            html += f'<td>{safe_str(nc.get("DiasParaCierre", nc.get("DiasVencidas")))}</td>\n'
            html += '</tr>\n'
        
        html += '</table>\n<br><br>\n'
        return html
    
    def _generate_arapc_table_html(self, arapc_list: List[Dict], title: str) -> str:
        """Genera tabla HTML para ARAPs"""
        html = f'<table>\n'
        html += f'<tr>\n<td colspan="8" class="ColespanArriba">{title}</td>\n</tr>\n'
        
        # Encabezados
        html += '<tr>\n'
        html += '<td class="centrado"><strong>NEMOTÉCNICO</strong></td>\n'
        html += '<td class="centrado"><strong>CÓDIGO</strong></td>\n'
        html += '<td class="centrado"><strong>ACCIÓN</strong></td>\n'
        html += '<td class="centrado"><strong>TAREA</strong></td>\n'
        html += '<td class="centrado"><strong>RESPONSABLE TELEFÓNICA</strong></td>\n'
        html += '<td class="centrado"><strong>RESPONSABLE CALIDAD</strong></td>\n'
        html += '<td class="centrado"><strong>FECHA FIN PREVISTA</strong></td>\n'
        html += '<td class="centrado"><strong>DÍAS</strong></td>\n'
        html += '</tr>\n'
        
        # Filas de datos
        for arapc in arapc_list:
            html += '<tr>\n'
            html += f'<td>{safe_str(arapc.get("Nemotecnico"))}</td>\n'
            html += f'<td>{safe_str(arapc.get("CodigoNoConformidad"))}</td>\n'
            html += f'<td>{safe_str(arapc.get("Accion"))}</td>\n'
            html += f'<td>{safe_str(arapc.get("Tarea"))}</td>\n'
            html += f'<td>{safe_str(arapc.get("RESPONSABLETELEFONICA"))}</td>\n'
            html += f'<td>{safe_str(arapc.get("RESPONSABLECALIDAD"))}</td>\n'
            html += f'<td>{safe_str(arapc.get("FechaFinPrevista"))}</td>\n'
            html += f'<td>{safe_str(arapc.get("DiasParaVencer", arapc.get("DiasVencidas", arapc.get("Dias"))))}</td>\n'
            html += '</tr>\n'
        
        html += '</table>\n<br><br>\n'
        return html
    
    def _generate_eficacia_table_html(self, eficacia_list: List[Dict]) -> str:
        """Genera tabla HTML para control de eficacia"""
        html = f'<table>\n'
        html += f'<tr>\n<td colspan="8" class="ColespanArriba">NO CONFORMIDADES PENDIENTES DE CONTROL DE EFICACIA</td>\n</tr>\n'
        
        # Encabezados
        html += '<tr>\n'
        html += '<td class="centrado"><strong>NEMOTÉCNICO</strong></td>\n'
        html += '<td class="centrado"><strong>CÓDIGO</strong></td>\n'
        html += '<td class="centrado"><strong>DESCRIPCIÓN</strong></td>\n'
        html += '<td class="centrado"><strong>FECHA APERTURA</strong></td>\n'
        html += '<td class="centrado"><strong>ACCIÓN</strong></td>\n'
        html += '<td class="centrado"><strong>FECHA FIN ACCIÓN</strong></td>\n'
        html += '<td class="centrado"><strong>RESPONSABLE</strong></td>\n'
        html += '<td class="centrado"><strong>DÍAS TRANSCURRIDOS</strong></td>\n'
        html += '</tr>\n'
        
        # Filas de datos
        for item in eficacia_list:
            html += '<tr>\n'
            html += f'<td>{safe_str(item.get("Nemotecnico"))}</td>\n'
            html += f'<td>{safe_str(item.get("CodigoNoConformidad"))}</td>\n'
            html += f'<td>{safe_str(item.get("DESCRIPCION"))}</td>\n'
            html += f'<td>{safe_str(item.get("FECHAAPERTURA"))}</td>\n'
            html += f'<td>{safe_str(item.get("Accion"))}</td>\n'
            html += f'<td>{safe_str(item.get("FechaFinReal"))}</td>\n'
            html += f'<td>{safe_str(item.get("RESPONSABLETELEFONICA"))}</td>\n'
            html += f'<td>{safe_str(item.get("DiasTranscurridos"))}</td>\n'
            html += '</tr>\n'
        
        html += '</table>\n<br><br>\n'
        return html
    
    def should_execute_technical_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea técnica
        """
        try:
            # Verificar última ejecución de NCTecnico
            last_execution = self.get_last_execution_date("NCTecnico")
            if last_execution and last_execution.date() == date.today():
                return False
            
            # Verificar si hay datos para procesar
            nc_proximas = self.get_nc_proximas_caducar()
            nc_caducadas = self.get_nc_caducadas()
            arapcs_proximas = self.get_arapcs_proximas_vencer()
            arapcs_vencidas = self.get_arapcs_vencidas()
            
            return len(nc_proximas) > 0 or len(nc_caducadas) > 0 or len(arapcs_proximas) > 0 or len(arapcs_vencidas) > 0
            
        except Exception as e:
            self.logger.error("Error verificando si ejecutar tarea técnica: {}".format(e))
            return False

    def run(self) -> bool:
        """
        Método principal para ejecutar la tarea de No Conformidades
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            self.logger.info("Ejecutando tarea de No Conformidades")
            
            # Verificar si debe ejecutarse
            if not self.debe_ejecutarse():
                self.logger.info("La tarea de No Conformidades no debe ejecutarse hoy")
                return True
            
            # Ejecutar la lógica específica
            success = self.ejecutar_logica_especifica()
            
            if success:
                # Marcar como completada
                self.marcar_como_completada()
                self.logger.info("Tarea de No Conformidades completada exitosamente")
            
            return success
            
        except Exception as e:
            self.logger.error("Error ejecutando tarea de No Conformidades: {}".format(e))
            return False

    # Métodos alias para compatibilidad con el script run_no_conformidades.py
    def obtener_nc_resueltas_pendientes_eficacia(self) -> List[Dict[str, Any]]:
        """Alias para get_nc_pendientes_eficacia para compatibilidad con el script"""
        return self.get_nc_pendientes_eficacia()
    
    def obtener_nc_proximas_caducar(self) -> List[Dict[str, Any]]:
        """Alias para get_nc_proximas_caducar para compatibilidad con el script"""
        return self.get_nc_proximas_caducar()
    
    def obtener_nc_registradas_sin_acciones(self) -> List[Dict[str, Any]]:
        """Obtiene las NCs registradas sin acciones correctivas"""
        try:
            db_nc = self._get_nc_connection()
            
            query = """
                SELECT nc.CodigoNoConformidad, nc.Nemotecnico, nc.DESCRIPCION,
                       nc.RESPONSABLECALIDAD, nc.FECHAAPERTURA
                FROM TbNoConformidades nc
                LEFT JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
                WHERE nc.FECHACIERRE IS NULL 
                AND nc.Borrado = False
                AND ac.IDAccionCorrectiva IS NULL
                ORDER BY nc.FECHAAPERTURA
            """
            
            result = db_nc.execute_query(query)
            self.logger.info("Encontradas {} NCs sin acciones correctivas".format(len(result)))
            return result
            
        except Exception as e:
            self.logger.error("Error obteniendo NCs sin acciones: {}".format(e))
            return []
    
    def obtener_arapc_proximas_vencer(self) -> List[Dict[str, Any]]:
        """Alias para get_arapcs_proximas_vencer para compatibilidad con el script"""
        return self.get_arapcs_proximas_vencer()
    
    def get_nc_registradas_sin_acciones(self) -> List[Dict[str, Any]]:
        """Obtiene las NCs registradas sin acciones correctivas"""
        return self.obtener_nc_registradas_sin_acciones()


# Clases de datos para No Conformidades
class NoConformidad:
    """Clase de datos para representar una No Conformidad"""
    
    def __init__(self, codigo: str, nemotecnico: str, descripcion: str, 
                 responsable_calidad: str, fecha_apertura: datetime, 
                 fecha_prev_cierre: datetime, dias_para_cierre: int = 0,
                 fecha_cierre: Optional[datetime] = None):
        self.codigo = codigo
        self.nemotecnico = nemotecnico
        self.descripcion = descripcion
        self.responsable_calidad = responsable_calidad
        self.fecha_apertura = fecha_apertura
        self.fecha_prev_cierre = fecha_prev_cierre
        self.fecha_cierre = fecha_cierre
        self.dias_para_cierre = dias_para_cierre
    
    def __str__(self):
        return f"NC-{self.codigo}: {self.nemotecnico}"
    
    def __repr__(self):
        return f"NoConformidad(codigo='{self.codigo}', nemotecnico='{self.nemotecnico}')"


class ARAPC:
    """Clase de datos para representar una ARAPC (Acción de Respuesta a Auditorías, Procesos y Controles)"""
    
    def __init__(self, id_accion: int, codigo_nc: str, descripcion: str,
                 responsable: str, fecha_fin_prevista: datetime,
                 fecha_fin_real: Optional[datetime] = None):
        self.id_accion = id_accion
        self.codigo_nc = codigo_nc
        self.descripcion = descripcion
        self.responsable = responsable
        self.fecha_fin_prevista = fecha_fin_prevista
        self.fecha_fin_real = fecha_fin_real
    
    def __str__(self):
        return f"ARAPC-{self.id_accion}: {self.codigo_nc}"
    
    def __repr__(self):
        return f"ARAPC(id_accion={self.id_accion}, codigo_nc='{self.codigo_nc}')"


class Usuario:
    """Clase de datos para representar un Usuario"""
    
    def __init__(self, usuario_red: str, nombre: str, correo: str):
        self.usuario_red = usuario_red
        self.nombre = nombre
        self.correo = correo
    
    def __str__(self):
        return f"{self.nombre} ({self.usuario_red})"

    def __repr__(self):
        return f"Usuario(usuario_red='{self.usuario_red}', nombre='{self.nombre}', correo='{self.correo}')"