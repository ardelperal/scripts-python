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
    
<<<<<<< Updated upstream
    def get_quality_emails_string(self) -> str:
=======
    def desconectar_bases_datos(self):
        """Desconecta de las bases de datos"""
        try:
            if self.db_nc:
                self.db_nc.disconnect()
            if self.db_tareas:
                self.db_tareas.disconnect()
            self.logger.info("Conexiones a bases de datos cerradas")
        except Exception as e:
            self.logger.error(f"Error cerrando conexiones: {e}")
    
    def __enter__(self):
        """Context manager entry - conecta a las bases de datos"""
        self.conectar_bases_datos()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - desconecta de las bases de datos"""
        self.desconectar_bases_datos()
        if exc_type:
            self.logger.error(f"Error en context manager: {exc_val}")
    

    
    def obtener_nc_resueltas_pendientes_eficacia(self) -> List[NoConformidad]:
        """Obtiene NCs resueltas pendientes de control de eficacia"""
        try:
            # Calcular la fecha límite (30 días atrás desde hoy)
            from datetime import datetime, timedelta
            fecha_limite = datetime.now() - timedelta(days=30)
            fecha_limite_str = self._formatear_fecha_access(fecha_limite)
            
            sql = f"""
                SELECT DISTINCT nc.CodigoNoConformidad, nc.Nemotecnico, nc.DESCRIPCION,
                       nc.RESPONSABLECALIDAD, nc.FECHAAPERTURA, nc.FPREVCIERRE
                FROM (TbNoConformidades nc
                INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad)
                INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
                WHERE ar.FechaFinReal IS NOT NULL 
                AND nc.ControlEficacia IS NULL
                AND ar.FechaFinReal <= {fecha_limite_str}
            """
            
            records = self.db_nc.execute_query(sql)
            ncs = []
            
            for record in records:
                nc = NoConformidad(
                    codigo=record['CodigoNoConformidad'] or "",
                    nemotecnico=record['Nemotecnico'] or "",
                    descripcion=record['DESCRIPCION'] or "",
                    responsable_calidad=record['RESPONSABLECALIDAD'] or "",
                    fecha_apertura=record['FECHAAPERTURA'] if record['FECHAAPERTURA'] else datetime.now(),
                    fecha_prev_cierre=record['FPREVCIERRE'] if record['FPREVCIERRE'] else datetime.now()
                )
                ncs.append(nc)
            
            self.logger.info(f"Encontradas {len(ncs)} NCs pendientes de control de eficacia")
            return ncs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs pendientes de eficacia: {e}", exc_info=True)
            return []
    
    def obtener_arapc_proximas_vencer(self) -> List[ARAPC]:
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
            # Verificar última ejecución de NCTecnico
            last_execution = self.get_last_execution_date("NCTecnico")
            if last_execution and last_execution.date() == date.today():
=======
            # Obtener el valor de días de alerta desde la configuración
            import os
            from datetime import datetime, timedelta
            dias_alerta_arapc = int(os.getenv('DIAS_ALERTA_ARAPC', '7'))
            self.logger.info(f"Buscando ARAPs próximas a vencer en {dias_alerta_arapc} días")
            
            # Calcular fechas límite
            fecha_hoy = datetime.now().date()
            fecha_limite_superior = fecha_hoy + timedelta(days=dias_alerta_arapc)
            
            fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
            fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.DESCRIPCION,
                nc.FECHAAPERTURA,
                ac.IDAccionCorrectiva,
                ac.AccionCorrectiva,
                ar.FechaFinPrevista,
                ac.Responsable
            FROM (TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad)
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
                AND ar.FechaFinPrevista >= {fecha_hoy_str}
                AND ar.FechaFinPrevista <= {fecha_limite_superior_str}
            ORDER BY ar.FechaFinPrevista ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos ARAPC y calcular días para vencer
            arapcs = []
            for row in resultados:
                fecha_fin = row['FechaFinPrevista']
                if fecha_fin:
                    if isinstance(fecha_fin, str):
                        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin = fecha_fin.date()
                    
                    dias_para_vencer = (fecha_fin - fecha_hoy).days
                else:
                    dias_para_vencer = 0
                
                arapc = ARAPC(
                    id_accion=row['IDAccionCorrectiva'],
                    codigo_nc=row['CodigoNoConformidad'] or "",
                    descripcion=row['AccionCorrectiva'] or "",
                    responsable=row['Responsable'] or "",
                    fecha_fin_prevista=row['FechaFinPrevista'] if row['FechaFinPrevista'] else datetime.now(),
                    dias_para_vencer=dias_para_vencer
                )
                arapcs.append(arapc)
            
            self.logger.info(f"ARAPs próximas a vencer encontradas: {len(arapcs)}")
            return arapcs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPs próximas a vencer: {e}", exc_info=True)
            return []
    
    def obtener_nc_proximas_caducar(self) -> List[NoConformidad]:
        """
        Obtiene las No Conformidades próximas a caducar por eficacia
        Equivalente a la función ObtenerNCProximasCaducar del VBS original
        """
        try:
            from datetime import datetime, timedelta
            self.logger.info("Buscando NCs próximas a caducar por eficacia")
            
            # Calcular fechas límite (entre 30 y 365 días desde la fecha final)
            fecha_hoy = datetime.now().date()
            fecha_limite_inferior = fecha_hoy - timedelta(days=365)  # Hace 365 días
            fecha_limite_superior = fecha_hoy - timedelta(days=30)   # Hace 30 días
            
            fecha_limite_inferior_str = self._formatear_fecha_access(fecha_limite_inferior)
            fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.DESCRIPCION,
                nc.FECHAAPERTURA,
                ac.IDAccionCorrectiva,
                ac.AccionCorrectiva AS DescripcionAccion,
                ar.FechaFinPrevista,
                ac.Responsable
            FROM (TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad)
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
                AND ar.FechaFinPrevista >= {fecha_limite_inferior_str}
                AND ar.FechaFinPrevista <= {fecha_limite_superior_str}
            ORDER BY ar.FechaFinPrevista ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos NoConformidad y calcular días transcurridos
            ncs_proximas = []
            for row in resultados:
                fecha_fin = row['FechaFinPrevista']
                if fecha_fin:
                    if isinstance(fecha_fin, str):
                        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin = fecha_fin.date()
                    
                    dias_transcurridos = (fecha_hoy - fecha_fin).days
                else:
                    dias_transcurridos = 0
                
                nc = NoConformidad(
                    codigo=row['CodigoNoConformidad'] or "",
                    nemotecnico="",
                    descripcion=row['DESCRIPCION'] or "",
                    responsable_calidad=row['Responsable'] or "",
                    fecha_apertura=row['FECHAAPERTURA'] if row['FECHAAPERTURA'] else datetime.now(),
                    fecha_prev_cierre=row['FechaFinPrevista'] if row['FechaFinPrevista'] else datetime.now(),
                    dias_para_cierre=dias_transcurridos
                )
                ncs_proximas.append(nc)
            
            self.logger.info(f"NCs próximas a caducar encontradas: {len(ncs_proximas)}")
            return ncs_proximas
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs próximas a caducar: {e}", exc_info=True)
            return []
    
    def obtener_nc_registradas_sin_acciones(self) -> List[NoConformidad]:
        """
        Obtiene las No Conformidades registradas sin acciones correctivas
        Equivalente a la función ObtenerNCRegistradasSinAcciones del VBS original
        """
        try:
            from datetime import datetime, timedelta
            self.logger.info("Buscando NCs registradas sin acciones correctivas")
            
            # Calcular fecha límite basada en días de alerta
            fecha_hoy = datetime.now().date()
            fecha_limite = fecha_hoy + timedelta(days=self.dias_alerta_nc)
            fecha_limite_str = self._formatear_fecha_access(fecha_limite)
            
            # Query SQL sin DATEDIFF - usando nombres correctos de columnas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.Nemotecnico,
                nc.DESCRIPCION,
                nc.RESPONSABLECALIDAD,
                nc.FECHAAPERTURA,
                nc.FPREVCIERRE
            FROM TbNoConformidades nc
            LEFT JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            WHERE ac.IDAccionCorrectiva IS NULL
                AND nc.FPREVCIERRE IS NOT NULL
                AND nc.FPREVCIERRE <= {fecha_limite_str}
            ORDER BY nc.FECHAAPERTURA ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos NoConformidad y calcular días para cierre
            ncs_sin_acciones = []
            for row in resultados:
                fecha_prev_cierre = row['FPREVCIERRE']
                if fecha_prev_cierre:
                    if isinstance(fecha_prev_cierre, str):
                        fecha_prev_cierre = datetime.strptime(fecha_prev_cierre, '%Y-%m-%d').date()
                    elif hasattr(fecha_prev_cierre, 'date'):
                        fecha_prev_cierre = fecha_prev_cierre.date()
                    
                    dias_para_cierre = (fecha_prev_cierre - fecha_hoy).days
                else:
                    dias_para_cierre = 0
                
                nc = NoConformidad(
                    codigo=row['CodigoNoConformidad'] or "",
                    nemotecnico=row['Nemotecnico'] or "",
                    descripcion=row['DESCRIPCION'] or "",
                    responsable_calidad=row['RESPONSABLECALIDAD'] or "",
                    fecha_apertura=row['FECHAAPERTURA'] if row['FECHAAPERTURA'] else datetime.now(),
                    fecha_prev_cierre=row['FPREVCIERRE'] if row['FPREVCIERRE'] else datetime.now(),
                    dias_para_cierre=dias_para_cierre
                )
                ncs_sin_acciones.append(nc)
            
            self.logger.info(f"NCs registradas sin acciones encontradas: {len(ncs_sin_acciones)}")
            return ncs_sin_acciones
            
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs registradas sin acciones: {e}")
            return []
    
    def obtener_usuarios_arapc_por_caducar(self) -> List[UsuarioARAPCPorCaducar]:
        """
        Obtiene los usuarios con ARAPs por caducar agrupados
        Equivalente a la función ObtenerUsuariosARAPCPorCaducar del VBS original
        """
        try:
            from datetime import datetime, timedelta
            import os
            self.logger.info("Obteniendo usuarios con ARAPs por caducar")
            
            # Obtener el valor de días de alerta desde la configuración
            dias_alerta_arapc = int(os.getenv('DIAS_ALERTA_ARAPC', '7'))
            
            # Calcular fechas límite
            fecha_hoy = datetime.now().date()
            fecha_limite_superior = fecha_hoy + timedelta(days=dias_alerta_arapc)
            
            fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
            fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.RESPONSABLETELEFONICA,
                COUNT(*) AS CantidadARAPs
            FROM TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
                AND ar.FechaFinPrevista >= {fecha_hoy_str}
                AND ar.FechaFinPrevista <= {fecha_limite_superior_str}
                AND nc.RESPONSABLETELEFONICA IS NOT NULL
                AND nc.RESPONSABLETELEFONICA <> ''
            GROUP BY nc.RESPONSABLETELEFONICA
            ORDER BY CantidadARAPs DESC, nc.RESPONSABLETELEFONICA ASC
            """
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a objetos UsuarioARAPCPorCaducar
            usuarios_arapc = []
            for row in resultados:
                usuario = UsuarioARAPCPorCaducar(
                    responsable=row['RESPONSABLETELEFONICA'] or "",
                    cantidad_arapcs=row['CantidadARAPs'] if row['CantidadARAPs'] is not None else 0
                )
                usuarios_arapc.append(usuario)
            
            self.logger.info(f"Usuarios con ARAPs por caducar encontrados: {len(usuarios_arapc)}")
            return usuarios_arapc
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios con ARAPs por caducar: {e}")
            return []
    
    def obtener_arapc_usuario_por_tipo(self, usuario: str, tipo_alerta: str) -> List[Dict]:
        """
        Obtiene las ARAPs de un usuario específico por tipo de alerta
        Equivalente a la función ObtenerARAPCUsuarioPorTipo del VBS original
        """
        try:
            from datetime import datetime, timedelta
            self.logger.info(f"Obteniendo ARAPs para usuario {usuario} con tipo de alerta {tipo_alerta}")
            
            # Calcular fechas límite según el tipo de alerta
            fecha_hoy = datetime.now().date()
            
            # Query SQL siguiendo la lógica del VBScript legacy - INNER JOIN con TbNCAccionesRealizadas
            sql_query = f"""
            SELECT 
                nc.IDNoConformidad,
                nc.CodigoNoConformidad,
                nc.DESCRIPCION,
                ac.IDAccionCorrectiva,
                ac.AccionCorrectiva,
                ar.FechaFinPrevista,
                ac.Responsable
            FROM TbNoConformidades nc
            INNER JOIN TbNCAccionCorrectivas ac ON nc.IDNoConformidad = ac.IDNoConformidad
            INNER JOIN TbNCAccionesRealizadas ar ON ac.IDAccionCorrectiva = ar.IDAccionCorrectiva
            WHERE ac.Responsable = '{usuario}'
                AND ar.FechaFinReal IS NULL
                AND ar.FechaFinPrevista IS NOT NULL
            """
            
            # Agregar filtros según el tipo de alerta
            if tipo_alerta == '15':
                fecha_limite_inferior = fecha_hoy + timedelta(days=8)
                fecha_limite_superior = fecha_hoy + timedelta(days=15)
                fecha_limite_inferior_str = self._formatear_fecha_access(fecha_limite_inferior)
                fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
                sql_query += f" AND ar.FechaFinPrevista >= {fecha_limite_inferior_str} AND ar.FechaFinPrevista <= {fecha_limite_superior_str}"
            elif tipo_alerta == '7':
                fecha_limite_inferior = fecha_hoy + timedelta(days=1)
                fecha_limite_superior = fecha_hoy + timedelta(days=7)
                fecha_limite_inferior_str = self._formatear_fecha_access(fecha_limite_inferior)
                fecha_limite_superior_str = self._formatear_fecha_access(fecha_limite_superior)
                sql_query += f" AND ar.FechaFinPrevista >= {fecha_limite_inferior_str} AND ar.FechaFinPrevista <= {fecha_limite_superior_str}"
            elif tipo_alerta == '0':
                fecha_hoy_str = self._formatear_fecha_access(fecha_hoy)
                sql_query += f" AND ar.FechaFinPrevista <= {fecha_hoy_str}"
            
            sql_query += " ORDER BY ar.FechaFinPrevista ASC"
            
            # Ejecutar la consulta
            resultados = self.db_nc.execute_query(sql_query)
            
            # Convertir resultados a diccionarios y calcular días para vencer
            arapcs = []
            for row in resultados:
                fecha_fin = row['FechaFinPrevista']
                if fecha_fin:
                    if isinstance(fecha_fin, str):
                        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin = fecha_fin.date()
                    
                    dias_para_vencer = (fecha_fin - fecha_hoy).days
                else:
                    dias_para_vencer = 0
                
                arapc = {
                    'id_nc': row['IDNoConformidad'],
                    'codigo_nc': row['CodigoNoConformidad'] or "",
                    'descripcion_nc': row['DESCRIPCION'] or "",
                    'id_accion': row['IDAccionCorrectiva'],
                    'descripcion_accion': row['AccionCorrectiva'] or "",
                    'fecha_fin_prevista': row['FechaFinPrevista'],
                    'responsable': row['Responsable'] or "",
                    'dias_para_vencer': dias_para_vencer
                }
                arapcs.append(arapc)
            
            self.logger.info(f"ARAPs encontradas para usuario {usuario}: {len(arapcs)}")
            return arapcs
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPs para usuario {usuario}: {e}")
            return []

    def obtener_correo_usuario(self, usuario_red: str) -> str:
        """Obtiene el correo electrónico de un usuario"""
        try:
            sql = """
                SELECT CorreoUsuario
                FROM TbUsuariosAplicaciones
                WHERE UsuarioRed = ?
            """
            
            if records and records[0] and records[0]['CorreoUsuario']:
                return records[0]['CorreoUsuario']
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correo del usuario {usuario_red}: {e}")
            return ""
    
    def obtener_correo_calidad_nc(self, codigo_nc: str) -> str:
        """Obtiene el correo del responsable de calidad de una NC"""
        try:
            sql = """
                SELECT u.CorreoUsuario
                FROM TbNoConformidades nc
                LEFT JOIN TbUsuariosAplicaciones u ON nc.RESPONSABLECALIDAD = u.UsuarioRed
                WHERE nc.CodigoNoConformidad = ?
            """
            
            if records and records[0] and records[0]['CorreoUsuario']:
                return records[0]['CorreoUsuario']
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correo de calidad para NC {codigo_nc}: {e}")
            return ""
    
    def obtener_correos_calidad_multiples(self, arapcs_15: List[Dict], arapcs_0: List[Dict]) -> str:
        """Obtiene los correos de calidad únicos de múltiples ARAPs"""
        try:
            correos_unicos = set()
            
            # Procesar ARAPs de 15 días
            for arapc in arapcs_15:
                correo = self.obtener_correo_calidad_nc(arapc.get('codigo_nc', ''))
                if correo:
                    correos_unicos.add(correo)
            
            # Procesar ARAPs vencidas
            for arapc in arapcs_0:
                correo = self.obtener_correo_calidad_nc(arapc.get('codigo_nc', ''))
                if correo:
                    correos_unicos.add(correo)
            
            return ";".join(correos_unicos) if correos_unicos else ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correos de calidad múltiples: {e}")
            return ""
    
    def marcar_aviso_arapc_enviado(self, id_accion_realizada: int, tipo_alerta: str, id_correo: int):
        """Marca un aviso ARAPC como enviado"""
        try:
            # Verificar si ya existe el registro
            sql_check = "SELECT ID FROM TbNCARAvisos WHERE IDAR = ?"
            records = self.db_nc.execute_query(sql_check, [id_accion_realizada])
            
            if records:
                # Actualizar registro existente
                if tipo_alerta == "15":
                    sql_update = "UPDATE TbNCARAvisos SET IDCorreo15 = ? WHERE IDAR = ?"
                elif tipo_alerta == "7":
                    sql_update = "UPDATE TbNCARAvisos SET IDCorreo7 = ? WHERE IDAR = ?"
                elif tipo_alerta == "0":
                    sql_update = "UPDATE TbNCARAvisos SET IDCorreo0 = ? WHERE IDAR = ?"
                else:
                    return
                
                self.db_nc.execute_query(sql_update, [id_correo, id_accion_realizada])
            else:
                # Crear nuevo registro
                nuevo_id = self.obtener_siguiente_id_avisos()
                sql_insert = "INSERT INTO TbNCARAvisos (ID, IDAR"
                values = [nuevo_id, id_accion_realizada]
                
                if tipo_alerta == "15":
                    sql_insert += ", IDCorreo15"
                    values.append(id_correo)
                elif tipo_alerta == "7":
                    sql_insert += ", IDCorreo7"
                    values.append(id_correo)
                elif tipo_alerta == "0":
                    sql_insert += ", IDCorreo0"
                    values.append(id_correo)
                
                sql_insert += ") VALUES (" + ",".join(["?"] * len(values)) + ")"
                self.db_nc.execute_query(sql_insert, values)
            
            self.logger.info(f"Aviso ARAPC marcado como enviado: ID={id_accion_realizada}, Tipo={tipo_alerta}")
            
        except Exception as e:
            self.logger.error(f"Error marcando aviso ARAPC como enviado: {e}")
    
    def obtener_siguiente_id_correo(self) -> int:
        """Obtiene el siguiente ID disponible para correos"""
        try:
            sql = "SELECT MAX(IDCorreo) AS Maximo FROM TbCorreosEnviados"
            records = self.db_tareas.execute_query(sql)
            
            if records and records[0] and records[0][0] is not None:
                return records[0][0] + 1
            
            return 1
            
        except Exception as e:
            self.logger.error(f"Error obteniendo siguiente ID de correo: {e}")
            return 1
    
    def obtener_siguiente_id_avisos(self) -> int:
        """Obtiene el siguiente ID disponible para avisos"""
        try:
            sql = "SELECT MAX(ID) AS Maximo FROM TbNCARAvisos"
            records = self.db_nc.execute_query(sql)
            
            if records and records[0] and records[0][0] is not None:
                return records[0][0] + 1
            
            return 1
            
        except Exception as e:
            self.logger.error(f"Error obteniendo siguiente ID de avisos: {e}")
            return 1
    
    def registrar_correo_enviado(self, asunto: str, cuerpo: str, destinatarios: str, 
                                correo_calidad: str = "") -> int:
        """Registra un correo como enviado en la base de datos"""
        try:
            id_correo = self.obtener_siguiente_id_correo()
            
            sql = """
                INSERT INTO TbCorreosEnviados 
                (IDCorreo, Aplicacion, Asunto, Cuerpo, Destinatarios, DestinatariosConCopiaOculta, FechaGrabacion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            admin_emails = get_admin_emails_string()
            
            self.db_tareas.execute_query(sql, [
                id_correo,
                "NC",
                asunto,
                cuerpo,
                destinatarios if "@" in destinatarios else "",
                admin_emails,
                datetime.now()
            ])
            
            self.logger.info(f"Correo registrado con ID: {id_correo}")
            return id_correo
            
        except Exception as e:
            self.logger.error(f"Error registrando correo enviado: {e}")
            return 0
    
    def es_dia_entre_semana(self) -> bool:
        """Verifica si hoy es día entre semana (lunes a viernes)"""
        hoy = datetime.now().weekday()  # 0=lunes, 6=domingo
        return 0 <= hoy <= 4  # lunes a viernes
    
    def requiere_tarea_calidad(self) -> bool:
        """Determina si se requiere ejecutar la tarea de calidad (lunes)"""
        try:
            hoy = datetime.now()
            
            # Verificar si es lunes (weekday 0)
            if hoy.weekday() != 0:
>>>>>>> Stashed changes
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