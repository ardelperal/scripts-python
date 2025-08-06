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
from common.utils import (
    load_css_content, safe_str, generate_html_header, generate_html_footer,
    register_email_in_database, get_admin_emails_string, get_quality_emails_string,
    get_technical_emails_string, send_notification_email
)

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
        """Carga el contenido CSS según la configuración"""
        try:
            return config.get_nc_css_content()
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
    
    def get_ars_proximas_vencer_calidad(self) -> List[Dict[str, Any]]:
        """Obtiene las ARs próximas a vencer o vencidas para el equipo de calidad."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT DateDiff('d',Now(),[FPREVCIERRE]) AS DiasParaCierre, 
                    TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
                    TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE
                FROM TbNoConformidades 
                INNER JOIN (TbNCAccionCorrectivas 
                  INNER JOIN TbNCAccionesRealizadas 
                  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
                ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad 
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL AND 
                      DateDiff('d',Now(),[FPREVCIERRE]) < 16;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} ARs próximas a vencer (Calidad).")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs próximas a vencer (Calidad): {e}")
            return []
    
    def _get_modern_html_header(self) -> str:
        """Genera el header HTML moderno para los correos"""
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Informe No Conformidades</title>
            <style>
                {self.css_content}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">
                        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect width="40" height="40" rx="8" fill="white"/>
                            <path d="M20 8L32 14V26L20 32L8 26V14L20 8Z" fill="#2563eb"/>
                            <circle cx="20" cy="20" r="6" fill="white"/>
                        </svg>
                    </div>
                    <div class="header-text">
                        <h1>Informe de No Conformidades y Acciones Correctivas</h1>
                    </div>
                </div>
        """

    def _get_modern_html_footer(self) -> str:
        """Genera el footer HTML moderno para los correos"""
        return """
            </div>
            <div class="footer">
                <p>Este es un mensaje generado por el servicio automatizado del departamento.</p>
                <p>Este es un correo desatendido. No responda a este mensaje.</p>
            </div>
        </body>
        </html>
        """

    def _generate_modern_arapc_table_html(self, arapc_data: List[Dict[str, Any]]) -> str:
        """Genera tabla HTML moderna para ARAPs próximas a caducar"""
        if not arapc_data:
            return ""
        
        html = """
        <div class="section">
            <h2>Acciones Correctivas/Preventivas Próximas a Caducar</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Código NC</th>
                        <th>Nemotécnico</th>
                        <th>Descripción</th>
                        <th>Responsable Calidad</th>
                        <th>Fecha Apertura</th>
                        <th>Fecha Prevista Cierre</th>
                        <th>Días</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in arapc_data:
            dias = row.get('DiasParaCierre', 0)
            estado_class = self._get_dias_class(dias)
            
            html += f"""
                    <tr>
                        <td>{safe_str(row.get('CodigoNoConformidad', ''))}</td>
                        <td>{safe_str(row.get('Nemotecnico', ''))}</td>
                        <td>{safe_str(row.get('DESCRIPCION', ''))}</td>
                        <td>{safe_str(row.get('RESPONSABLECALIDAD', ''))}</td>
                        <td>{self._format_date_display(row.get('FECHAAPERTURA'))}</td>
                        <td>{self._format_date_display(row.get('FPREVCIERRE'))}</td>
                        <td><span class="dias-indicador {estado_class}">{dias}</span></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def _generate_modern_eficacia_table_html(self, eficacia_data: List[Dict[str, Any]]) -> str:
        """Genera tabla HTML moderna para NCs pendientes de control de eficacia"""
        if not eficacia_data:
            return ""
        
        html = """
        <div class="section">
            <h2>No Conformidades Pendientes de Control de Eficacia</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Código NC</th>
                        <th>Nemotécnico</th>
                        <th>Descripción</th>
                        <th>Responsable Calidad</th>
                        <th>Fecha Cierre</th>
                        <th>Fecha Prevista Control</th>
                        <th>Días</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in eficacia_data:
            dias = row.get('Dias', 0)
            estado_class = self._get_dias_class(dias)
            
            html += f"""
                    <tr>
                        <td>{safe_str(row.get('CodigoNoConformidad', ''))}</td>
                        <td>{safe_str(row.get('Nemotecnico', ''))}</td>
                        <td>{safe_str(row.get('DESCRIPCION', ''))}</td>
                        <td>{safe_str(row.get('RESPONSABLECALIDAD', ''))}</td>
                        <td>{self._format_date_display(row.get('FECHACIERRE'))}</td>
                        <td>{self._format_date_display(row.get('FechaPrevistaControlEficacia'))}</td>
                        <td><span class="dias-indicador {estado_class}">{dias}</span></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def _generate_modern_nc_table_html(self, nc_data: List[Dict[str, Any]]) -> str:
        """Genera tabla HTML moderna para NCs sin acciones correctivas"""
        if not nc_data:
            return ""
        
        html = """
        <div class="section">
            <h2>No Conformidades sin Acciones Correctivas</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Código NC</th>
                        <th>Nemotécnico</th>
                        <th>Descripción</th>
                        <th>Responsable Calidad</th>
                        <th>Fecha Apertura</th>
                        <th>Fecha Prevista Cierre</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in nc_data:
            html += f"""
                    <tr>
                        <td>{safe_str(row.get('CodigoNoConformidad', ''))}</td>
                        <td>{safe_str(row.get('Nemotecnico', ''))}</td>
                        <td>{safe_str(row.get('DESCRIPCION', ''))}</td>
                        <td>{safe_str(row.get('RESPONSABLECALIDAD', ''))}</td>
                        <td>{self._format_date_display(row.get('FECHAAPERTURA'))}</td>
                        <td>{self._format_date_display(row.get('FPREVCIERRE'))}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def _generate_modern_replanificar_table_html(self, replanificar_data: List[Dict[str, Any]]) -> str:
        """Genera tabla HTML moderna para ARs a replanificar"""
        if not replanificar_data:
            return ""
        
        html = """
        <div class="section">
            <h2>Acciones Realizadas para Replanificar</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Código NC</th>
                        <th>Nemotécnico</th>
                        <th>Acción Correctiva</th>
                        <th>Tarea</th>
                        <th>Técnico</th>
                        <th>Responsable Calidad</th>
                        <th>Fecha Fin Prevista</th>
                        <th>Días</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in replanificar_data:
            dias = row.get('Dias', 0)
            estado_class = self._get_dias_class(dias)
            
            html += f"""
                    <tr>
                        <td>{safe_str(row.get('CodigoNoConformidad', ''))}</td>
                        <td>{safe_str(row.get('Nemotecnico', ''))}</td>
                        <td>{safe_str(row.get('Accion', ''))}</td>
                        <td>{safe_str(row.get('Tarea', ''))}</td>
                        <td>{safe_str(row.get('Tecnico', ''))}</td>
                        <td>{safe_str(row.get('RESPONSABLECALIDAD', ''))}</td>
                        <td>{self._format_date_display(row.get('FechaFinPrevista'))}</td>
                        <td><span class="dias-indicador {estado_class}">{dias}</span></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def _generate_modern_ar_tecnico_table_html(self, ar_data: List[Dict[str, Any]], titulo: str) -> str:
        """Genera tabla HTML moderna para ARs de técnicos"""
        if not ar_data:
            return ""
        
        # Determinar el icono según el título
        icono = "🔔" if "8-15" in titulo else "⚠️" if "1-7" in titulo else "🚨"
        
        html = f"""
        <div class="section">
            <h2>{icono} {titulo}</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Código NC</th>
                        <th>Nemotécnico</th>
                        <th>Acción Correctiva</th>
                        <th>Acción Realizada</th>
                        <th>Fecha Inicio</th>
                        <th>Fecha Fin Prevista</th>
                        <th>Responsable</th>
                        <th>Días para Caducar</th>
                        <th>Correo Calidad</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in ar_data:
            dias = row.get('DiasParaCaducar', 0)
            estado_class = self._get_dias_class(dias)
            
            html += f"""
                    <tr>
                        <td>{safe_str(row.get('CodigoNoConformidad', ''))}</td>
                        <td>{safe_str(row.get('Nemotecnico', ''))}</td>
                        <td>{safe_str(row.get('AccionCorrectiva', ''))}</td>
                        <td>{safe_str(row.get('AccionRealizada', ''))}</td>
                        <td>{self._format_date_display(row.get('FechaInicio'))}</td>
                        <td>{self._format_date_display(row.get('FechaFinPrevista'))}</td>
                        <td>{safe_str(row.get('Nombre', ''))}</td>
                        <td><span class="dias-indicador {estado_class}">{dias}</span></td>
                        <td>{safe_str(row.get('CorreoCalidad', ''))}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def _get_dias_class(self, dias: int) -> str:
        """Retorna la clase CSS según los días restantes"""
        if dias <= 0:
            return "negativo"
        elif dias <= 7:
            return "critico"
        else:
            return "normal"

    def _format_date_display(self, fecha) -> str:
        """Formatea una fecha para mostrar en las tablas"""
        if fecha is None:
            return ""
        
        if isinstance(fecha, str):
            try:
                # Intentar varios formatos de fecha
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        fecha_obj = datetime.strptime(fecha, fmt)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
                return fecha  # Si no se puede parsear, devolver como está
            except:
                return fecha
        elif isinstance(fecha, (date, datetime)):
            return fecha.strftime('%d/%m/%Y')
        else:
            return str(fecha)

    def get_ncs_pendientes_eficacia(self) -> List[Dict[str, Any]]:
        """Obtiene NCs resueltas pendientes de control de eficacia."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD,  
                    TbNoConformidades.FECHACIERRE, TbNoConformidades.FechaPrevistaControlEficacia,
                    DateDiff('d',Now(),[FechaPrevistaControlEficacia]) AS Dias
                FROM TbNoConformidades
                INNER JOIN (TbNCAccionCorrectivas 
                  INNER JOIN TbNCAccionesRealizadas 
                  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
                WHERE DateDiff('d',Now(),[FechaPrevistaControlEficacia]) < 30
                  AND TbNCAccionesRealizadas.FechaFinReal IS NOT NULL
                  AND TbNoConformidades.RequiereControlEficacia = 'Sí'
                  AND TbNoConformidades.FechaControlEficacia IS NULL;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} NCs pendientes de eficacia.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs pendientes de eficacia: {e}")
            return []
    
    def get_ncs_sin_acciones(self) -> List[Dict[str, Any]]:
        """Obtiene No Conformidades sin acciones correctivas registradas."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico,
                    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
                    TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE
                FROM TbNoConformidades
                LEFT JOIN TbNCAccionCorrectivas 
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
                WHERE TbNCAccionCorrectivas.IDNoConformidad IS NULL;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} NCs sin acciones.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo NCs sin acciones: {e}")
            return []

    def get_ars_para_replanificar(self) -> List[Dict[str, Any]]:
        """Obtiene ARs que necesitan replanificación."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
                    TbNCAccionCorrectivas.AccionCorrectiva AS Accion, TbNCAccionesRealizadas.AccionRealizada AS Tarea,
                    TbUsuariosAplicaciones.Nombre AS Tecnico, TbNoConformidades.RESPONSABLECALIDAD, 
                    TbNCAccionesRealizadas.FechaFinPrevista,
                    DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) AS Dias
                FROM (TbNoConformidades 
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN TbNCAccionesRealizadas 
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbUsuariosAplicaciones 
                  ON TbNCAccionesRealizadas.Responsable = TbUsuariosAplicaciones.UsuarioRed
                WHERE DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) < 16 
                  AND TbNCAccionesRealizadas.FechaFinReal IS NULL;
            """
            result = db_nc.execute_query(query)
            self.logger.info(f"Encontradas {len(result)} ARs para replanificar.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs para replanificar: {e}")
            return []
            
        except Exception as e:
            self.logger.error("Error obteniendo ARAPs próximas a vencer: {}".format(e))
    
    def get_correo_calidad_por_nc(self, codigo_nc: str) -> Optional[str]:
        """
        Obtiene el correo del responsable de calidad para una No Conformidad específica.
        """
        try:
            db_nc = self._get_nc_connection()

            query = """
                SELECT TbUsuariosAplicaciones.CorreoUsuario 
                FROM TbNoConformidades LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.Nombre 
                WHERE (((TbNoConformidades.CodigoNoConformidad)=?));
            """
            
            result = db_nc.execute_query(query, (codigo_nc,))
            
            if result and result[0].get('CorreoUsuario'):
                return result[0]['CorreoUsuario']
            else:
                self.logger.warning(f"No se encontró correo de calidad para la NC {codigo_nc}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo correo de calidad para NC {codigo_nc}: {e}")
            return None

    def get_correo_calidad_por_arap(self, codigo_nc: str) -> Optional[str]:
        """Obtiene el correo del responsable de calidad a partir de un código de No Conformidad."""
        if not codigo_nc:
            return None
        
        # Simplemente reutiliza la función existente, ya que ahora tenemos el CodigoNC
        return self.get_correo_calidad_por_nc(codigo_nc)
    
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
            self.logger.error(f"Error obteniendo ARs para replanificar: {e}")
            return []

    def get_tecnicos_con_nc_activas(self) -> List[str]:
        """Obtiene una lista de técnicos con NC activas y ARs pendientes."""
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.RESPONSABLETELEFONICA
                FROM (TbNoConformidades
                  INNER JOIN TbNCAccionCorrectivas ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                  INNER JOIN TbNCAccionesRealizadas ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL 
                  AND TbNoConformidades.Borrado = False 
                  AND DateDiff('d', Now(), [FechaFinPrevista]) <= 15;
            """
            result = db_nc.execute_query(query)
            tecnicos = [row['RESPONSABLETELEFONICA'] for row in result if row['RESPONSABLETELEFONICA']]
            self.logger.info(f"Encontrados {len(tecnicos)} técnicos con NCs activas.")
            return tecnicos
        except Exception as e:
            self.logger.error(f"Error obteniendo técnicos con NCs activas: {e}")
            return []

    def get_ars_tecnico_por_vencer(self, tecnico: str, dias_min: int, dias_max: int, tipo_aviso: str) -> List[Dict[str, Any]]:
        """Obtiene las ARs de un técnico que están por vencer en un rango de días."""
        try:
            db_nc = self._get_nc_connection()
            query = f"""
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada,
                    TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada,
                    TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista,
                    TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar,
                    TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico
                FROM ((TbNoConformidades 
                  LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed)
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN (TbNCAccionesRealizadas 
                      LEFT JOIN TbNCARAvisos ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR)
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
                  AND DateDiff('d',Now(),[FechaFinPrevista]) BETWEEN {dias_min} AND {dias_max}
                  AND TbNCARAvisos.{tipo_aviso} IS NULL
                  AND TbNoConformidades.RESPONSABLETELEFONICA = ?;
            """
            result = db_nc.execute_query(query, (tecnico,))
            self.logger.info(f"Encontradas {len(result)} ARs para {tecnico} con vencimiento entre {dias_min} y {dias_max} días.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs para {tecnico}: {e}")
            return []

    def get_ars_tecnico_vencidas(self, tecnico: str, tipo_correo: str = "IDCorreo0") -> List[Dict[str, Any]]:
        """Obtiene las ARs vencidas de un técnico."""
        try:
            db_nc = self._get_nc_connection()
            query = f"""
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada,
                    TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada,
                    TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista,
                    TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar,
                    TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico
                FROM ((TbNoConformidades 
                  LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed)
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN (TbNCAccionesRealizadas 
                      LEFT JOIN TbNCARAvisos ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR)
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
                  AND DateDiff('d',Now(),[FechaFinPrevista]) <= 0
                  AND TbNCARAvisos.{tipo_correo} IS NULL
                  AND TbNoConformidades.RESPONSABLETELEFONICA = ?;
            """
            result = db_nc.execute_query(query, (tecnico,))
            self.logger.info(f"Encontradas {len(result)} ARs vencidas para {tecnico}.")
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs vencidas para {tecnico}: {e}")
            return []

    def registrar_aviso_ar(self, id_ar: int, id_correo: int, tipo_aviso: str):
        """Registra un aviso para una AR en la tabla TbNCARAvisos."""
        try:
            db_nc = self._get_nc_connection()
            # Verificar si ya existe un registro para este IDAR
            check_query = "SELECT IDAR FROM TbNCARAvisos WHERE IDAR = ?"
            exists = db_nc.execute_query(check_query, (id_ar,))
            
            if exists:
                # Si existe, actualizar el campo correspondiente
                update_query = f"UPDATE TbNCARAvisos SET {tipo_aviso} = ?, Fecha = Date() WHERE IDAR = ?"
                db_nc.execute_non_query(update_query, (id_correo, id_ar))
                self.logger.info(f"Actualizado aviso {tipo_aviso} para AR {id_ar} con ID de correo {id_correo}.")
            else:
                # Si no existe, insertar un nuevo registro
                # Primero obtener el próximo ID (máximo + 1)
                max_id_query = "SELECT Max(TbNCARAvisos.ID) AS Maximo FROM TbNCARAvisos"
                max_result = db_nc.execute_query(max_id_query)
                next_id = 1  # Valor por defecto si no hay registros
                if max_result and max_result[0].get('Maximo') is not None:
                    next_id = max_result[0]['Maximo'] + 1
                
                insert_query = f"INSERT INTO TbNCARAvisos (ID, IDAR, {tipo_aviso}, Fecha) VALUES (?, ?, ?, Date())"
                db_nc.execute_non_query(insert_query, (next_id, id_ar, id_correo))
                self.logger.info(f"Insertado aviso {tipo_aviso} para AR {id_ar} con ID de correo {id_correo} y ID {next_id}.")

        except Exception as e:
            self.logger.error(f"Error registrando aviso para AR {id_ar}: {e}")
    
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
    
    def get_araps_tecnicas_proximas_a_vencer(self, dias_inicio: int, dias_fin: int) -> List[Dict]:
        """
        Obtiene las ARAPs técnicas próximas a vencer en un rango de días específico.
        """
        try:
            db_nc = self._get_nc_connection()
            
            query = f"""
                SELECT ac.Nemotecnico, nc.CodigoNoConformidad, ac.Accion, ac.Tarea, 
                       ac.RESPONSABLETELEFONICA, nc.RESPONSABLECALIDAD, ac.FechaFinPrevista,
                       (ac.FechaFinPrevista - Date()) AS Dias
                FROM (TbNCAccionCorrectivas ac INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad) 
                LEFT JOIN TbUsuariosAplicaciones u ON ac.RESPONSABLETELEFONICA = u.UsuarioRed
                WHERE nc.Borrado = False 
                AND (u.Area = 'TECNICA' OR u.Area IS NULL) 
                AND ac.FechaFinReal IS NULL 
                AND ac.FechaFinPrevista IS NOT NULL
                AND (ac.FechaFinPrevista - Date()) BETWEEN {dias_inicio} AND {dias_fin}
                ORDER BY ac.FechaFinPrevista
            """
            
            return db_nc.execute_query(query)

        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPs técnicas próximas a vencer: {e}")
            return []

    def get_araps_tecnicas_vencidas(self) -> List[Dict]:
        """
        Obtiene las ARAPs técnicas vencidas.
        """
        try:
            db_nc = self._get_nc_connection()
            
            query = """
                SELECT ac.Nemotecnico, nc.CodigoNoConformidad, ac.Accion, ac.Tarea, 
                       ac.RESPONSABLETELEFONICA, nc.RESPONSABLECALIDAD, ac.FechaFinPrevista,
                       (ac.FechaFinPrevista - Date()) AS Dias
                FROM (TbNCAccionCorrectivas ac INNER JOIN TbNoConformidades nc ON ac.IDNoConformidad = nc.IDNoConformidad) 
                LEFT JOIN TbUsuariosAplicaciones u ON ac.RESPONSABLETELEFONICA = u.UsuarioRed
                WHERE nc.Borrado = False 
                AND (u.Area = 'TECNICA' OR u.Area IS NULL) 
                AND ac.FechaFinReal IS NULL 
                AND ac.FechaFinPrevista IS NOT NULL
                AND (ac.FechaFinPrevista - Date()) <= 0
                ORDER BY ac.FechaFinPrevista
            """
            
            return db_nc.execute_query(query)

        except Exception as e:
            self.logger.error(f"Error obteniendo ARAPs técnicas vencidas: {e}")
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
    
    def generar_informe_tecnico_individual_html(self, araps_8_15, araps_1_7, araps_vencidas):
        """Genera el cuerpo del email para el informe individual de un técnico."""
        html = f"""\
        <html>
        <head>{self.css}</head>
        <body>
            <h2>Informe de Acciones Correctivas Pendientes</h2>
            <p>A continuación se detallan las acciones correctivas (ARAPs) que requieren su atención.</p>
        """

        if araps_vencidas:
            html += "<h3>Acciones Correctivas Vencidas</h3>"
            html += self._generate_arapc_table_html(araps_vencidas)

        if araps_1_7:
            html += "<h3>Acciones Correctivas con Vencimiento en 1-7 días</h3>"
            html += self._generate_arapc_table_html(araps_1_7)

        if araps_8_15:
            html += "<h3>Acciones Correctivas con Vencimiento en 8-15 días</h3>"
            html += self._generate_arapc_table_html(araps_8_15)

        html += """\
            <p>Por favor, revise y actualice el estado de estas acciones en la herramienta correspondiente.</p>
        </body>
        </html>
        """
        return html
    
    def generate_quality_report_html(self, nc_pendientes_eficacia, nc_sin_acciones, ar_vencidas_calidad, ar_proximas_vencer_calidad, **kwargs):
        """Genera el cuerpo del email para el reporte de Calidad con las 4 secciones requeridas."""
        html = self._get_modern_html_header("INFORME TAREAS NO CONFORMIDADES")

        # Sección 1: ARs Próximas a Caducar o Caducadas
        if ar_proximas_vencer_calidad:
            html += '<div class="seccion">\n'
            html += '<h3>1. ARs Próximas a Caducar o Caducadas (sin fecha fin real)</h3>\n'
            html += self._generate_modern_arapc_table_html(ar_proximas_vencer_calidad)
            html += '</div>\n'

        # Sección 2: NCs Resueltas Pendientes de Control de Eficacia
        if nc_pendientes_eficacia:
            html += '<div class="seccion">\n'
            html += '<h3>2. No Conformidades Resueltas Pendientes de Control de Eficacia</h3>\n'
            html += self._generate_modern_eficacia_table_html(nc_pendientes_eficacia)
            html += '</div>\n'

        # Sección 3: NCs sin Acciones Correctivas
        if nc_sin_acciones:
            html += '<div class="seccion">\n'
            html += '<h3>3. No Conformidades sin Acciones Correctivas Registradas</h3>\n'
            html += self._generate_modern_nc_table_html(nc_sin_acciones)
            html += '</div>\n'

        # Sección 4: ARs para Replanificar
        ars_replanificar = self.get_ars_para_replanificar()
        if ars_replanificar:
            html += '<div class="seccion">\n'
            html += '<h3>4. ARs para Replanificar (fecha prevista cercana o pasada, sin fecha fin real)</h3>\n'
            html += self._generate_modern_replanificar_table_html(ars_replanificar)
            html += '</div>\n'

        html += self._get_modern_html_footer()
        return html

    def generate_technician_report_html(self, ar_15_dias, ar_7_dias, ar_vencidas, **kwargs):
        """Genera el cuerpo del email para el reporte de Técnicos con las 3 secciones requeridas."""
        html = self._get_modern_html_header("TAREAS DE ACCIONES CORRECTIVAS A PUNTO DE CADUCAR O CADUCADAS")

        # Sección 1: ARs con fecha fin prevista a 8-15 días
        if ar_15_dias:
            html += '<div class="seccion">\n'
            html += '<h3>1. Acciones Correctivas con fecha fin prevista a 8-15 días</h3>\n'
            html += self._generate_modern_ar_tecnico_table_html(ar_15_dias)
            html += '</div>\n'

        # Sección 2: ARs con fecha fin prevista a 1-7 días
        if ar_7_dias:
            html += '<div class="seccion">\n'
            html += '<h3>2. Acciones Correctivas con fecha fin prevista a 1-7 días</h3>\n'
            html += self._generate_modern_ar_tecnico_table_html(ar_7_dias)
            html += '</div>\n'

        # Sección 3: ARs con fecha fin prevista 0 o negativa (vencidas)
        if ar_vencidas:
            html += '<div class="seccion">\n'
            html += '<h3>3. Acciones Correctivas con fecha fin prevista 0 o negativa (vencidas)</h3>\n'
            html += self._generate_modern_ar_tecnico_table_html(ar_vencidas)
            html += '</div>\n'

        html += self._get_modern_html_footer()
        return html
    
    def _generate_nc_table_html(self, nc_list: List[Dict]) -> str:
        """Genera tabla HTML para No Conformidades"""
        html = f'<table>\n'
        
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
    
    def _generate_arapc_table_html(self, arapc_list: List[Dict]) -> str:
        """Genera tabla HTML para ARAPs"""
        html = f'<table>\n'
        
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

    def ejecutar_logica_especifica(self) -> bool:
        """
        Ejecuta la lógica específica de la tarea de No Conformidades
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            self.logger.info("Ejecutando lógica específica de No Conformidades")
            
            # 1. Generar correo para Miembros de Calidad
            self._generar_correo_calidad()
            
            # 2. Generar correos para Técnicos
            self._generar_correos_tecnicos()
            
            self.logger.info("Lógica específica de No Conformidades ejecutada correctamente")
            return True
            
        except Exception as e:
            self.logger.error("Error en lógica específica de No Conformidades: {}".format(e))
            return False



    def _generar_correo_calidad(self):
        """
        Genera y registra el correo para Miembros de Calidad con las 4 consultas principales
        """
        try:
            self.logger.info("Generando correo para Miembros de Calidad")
            
            # Obtener datos de las 4 consultas principales
            ars_proximas_vencer = self.get_ars_proximas_vencer_calidad()
            ncs_pendientes_eficacia = self.get_ncs_pendientes_eficacia()
            ncs_sin_acciones = self.get_ncs_sin_acciones()
            ars_para_replanificar = self.get_ars_para_replanificar()
            
            # Generar tablas HTML
            tablas_html = []
            
            if ars_proximas_vencer:
                tabla_arapc = self._generate_modern_arapc_table_html(ars_proximas_vencer)
                tablas_html.append(tabla_arapc)
                self.logger.info(f"Generada tabla ARAPC con {len(ars_proximas_vencer)} registros")
            
            if ncs_pendientes_eficacia:
                tabla_eficacia = self._generate_modern_eficacia_table_html(ncs_pendientes_eficacia)
                tablas_html.append(tabla_eficacia)
                self.logger.info(f"Generada tabla Eficacia con {len(ncs_pendientes_eficacia)} registros")
            
            if ncs_sin_acciones:
                tabla_nc = self._generate_modern_nc_table_html(ncs_sin_acciones)
                tablas_html.append(tabla_nc)
                self.logger.info(f"Generada tabla NC sin acciones con {len(ncs_sin_acciones)} registros")
            
            if ars_para_replanificar:
                tabla_replanificar = self._generate_modern_replanificar_table_html(ars_para_replanificar)
                tablas_html.append(tabla_replanificar)
                self.logger.info(f"Generada tabla Replanificar con {len(ars_para_replanificar)} registros")
            
            # Si hay al menos una tabla, generar el correo
            if tablas_html:
                header = self._get_modern_html_header()
                footer = self._get_modern_html_footer()
                cuerpo_html = header + "\n".join(tablas_html) + footer
                
                # Aquí se registraría el correo usando la función común
                self.logger.info("Correo HTML generado para Miembros de Calidad")
                self.logger.info(f"Longitud del HTML generado: {len(cuerpo_html)} caracteres")
                
                # Para debug, guardamos el HTML generado
                self._guardar_html_debug(cuerpo_html, "correo_calidad.html")
            else:
                self.logger.info("No hay datos para generar correo de Calidad")
                
        except Exception as e:
            self.logger.error(f"Error generando correo para Calidad: {e}")

    def _generar_correos_tecnicos(self):
        """
        Genera y registra correos individuales para cada técnico con ARs pendientes
        """
        try:
            self.logger.info("Generando correos para Técnicos")
            
            # Obtener técnicos con NCs activas
            tecnicos = self._get_tecnicos_con_nc_activas()
            
            for tecnico in tecnicos:
                self._generar_correo_tecnico_individual(tecnico)
                
        except Exception as e:
            self.logger.error(f"Error generando correos para técnicos: {e}")

    def _get_tecnicos_con_nc_activas(self) -> List[str]:
        """
        Obtiene la lista de técnicos que tienen al menos una NC activa con AR pendiente
        """
        try:
            db_nc = self._get_nc_connection()
            query = """
                SELECT DISTINCT TbNoConformidades.RESPONSABLETELEFONICA
                FROM (TbNoConformidades
                  INNER JOIN TbNCAccionCorrectivas ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                  INNER JOIN TbNCAccionesRealizadas ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL 
                  AND TbNoConformidades.Borrado = False 
                  AND DateDiff('d', Now(), [FechaFinPrevista]) <= 15
            """
            result = db_nc.execute_query(query)
            tecnicos = [row['RESPONSABLETELEFONICA'] for row in result if row['RESPONSABLETELEFONICA']]
            self.logger.info(f"Encontrados {len(tecnicos)} técnicos con NCs activas")
            return tecnicos
        except Exception as e:
            self.logger.error(f"Error obteniendo técnicos con NCs activas: {e}")
            return []

    def _generar_correo_tecnico_individual(self, tecnico: str):
        """
        Genera correo individual para un técnico específico
        """
        try:
            self.logger.info(f"Generando correo para técnico: {tecnico}")
            
            # Obtener ARs del técnico en las 3 categorías
            ars_15_dias = self._get_ars_tecnico_15_dias(tecnico)
            ars_7_dias = self._get_ars_tecnico_7_dias(tecnico)
            ars_vencidas = self._get_ars_tecnico_vencidas(tecnico)
            
            # Generar tablas HTML
            tablas_html = []
            
            if ars_15_dias:
                tabla_15 = self._generate_modern_ar_tecnico_table_html(ars_15_dias, "ARs próximas a vencer (8-15 días)")
                tablas_html.append(tabla_15)
                self.logger.info(f"Generada tabla 15 días para {tecnico} con {len(ars_15_dias)} registros")
            
            if ars_7_dias:
                tabla_7 = self._generate_modern_ar_tecnico_table_html(ars_7_dias, "ARs próximas a vencer (1-7 días)")
                tablas_html.append(tabla_7)
                self.logger.info(f"Generada tabla 7 días para {tecnico} con {len(ars_7_dias)} registros")
            
            if ars_vencidas:
                tabla_vencidas = self._generate_modern_ar_tecnico_table_html(ars_vencidas, "ARs vencidas")
                tablas_html.append(tabla_vencidas)
                self.logger.info(f"Generada tabla vencidas para {tecnico} con {len(ars_vencidas)} registros")
            
            # Si hay tablas, generar el correo
            if tablas_html:
                header = self._get_modern_html_header()
                footer = self._get_modern_html_footer()
                cuerpo_html = header + "\n".join(tablas_html) + footer
                
                # Aquí se registraría el correo usando la función común
                self.logger.info(f"Correo HTML generado para técnico: {tecnico}")
                
                # Para debug, guardamos el HTML generado
                self._guardar_html_debug(cuerpo_html, f"correo_tecnico_{tecnico}.html")
            else:
                self.logger.info(f"No hay datos para generar correo para técnico: {tecnico}")
                
        except Exception as e:
            self.logger.error(f"Error generando correo para técnico {tecnico}: {e}")

    def _get_ars_tecnico_15_dias(self, tecnico: str) -> List[Dict]:
        """
        Obtiene ARs del técnico con fecha fin prevista a 8-15 días
        """
        try:
            db_nc = self._get_nc_connection()
            query = f"""
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada,
                    TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada,
                    TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista,
                    TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar,
                    TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico
                FROM ((TbNoConformidades 
                  LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed)
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN (TbNCAccionesRealizadas 
                      LEFT JOIN TbNCARAvisos ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR)
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
                  AND DateDiff('d',Now(),[FechaFinPrevista]) BETWEEN 8 AND 15
                  AND TbNCARAvisos.IDCorreo15 IS NULL
                  AND TbNoConformidades.RESPONSABLETELEFONICA = '{tecnico}'
            """
            return db_nc.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs 15 días para técnico {tecnico}: {e}")
            return []

    def _get_ars_tecnico_7_dias(self, tecnico: str) -> List[Dict]:
        """
        Obtiene ARs del técnico con fecha fin prevista a 1-7 días
        """
        try:
            db_nc = self._get_nc_connection()
            query = f"""
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada,
                    TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada,
                    TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista,
                    TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar,
                    TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico
                FROM ((TbNoConformidades 
                  LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed)
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN (TbNCAccionesRealizadas 
                      LEFT JOIN TbNCARAvisos ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR)
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
                  AND DateDiff('d',Now(),[FechaFinPrevista]) > 0 AND DateDiff('d',Now(),[FechaFinPrevista]) <= 7
                  AND TbNCARAvisos.IDCorreo7 IS NULL
                  AND TbNoConformidades.RESPONSABLETELEFONICA = '{tecnico}'
            """
            return db_nc.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs 7 días para técnico {tecnico}: {e}")
            return []

    def _get_ars_tecnico_vencidas(self, tecnico: str) -> List[Dict]:
        """
        Obtiene ARs del técnico con fecha fin prevista 0 o negativa
        """
        try:
            db_nc = self._get_nc_connection()
            query = f"""
                SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada,
                    TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada,
                    TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista,
                    TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar,
                    TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico
                FROM ((TbNoConformidades 
                  LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed)
                  INNER JOIN (TbNCAccionCorrectivas 
                    INNER JOIN (TbNCAccionesRealizadas 
                      LEFT JOIN TbNCARAvisos ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR)
                    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
                  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
                LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente
                WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
                  AND DateDiff('d',Now(),[FechaFinPrevista]) <= 0
                  AND TbNCARAvisos.IDCorreo0 IS NULL
                  AND TbNoConformidades.RESPONSABLETELEFONICA = '{tecnico}'
            """
            return db_nc.execute_query(query)
        except Exception as e:
            self.logger.error(f"Error obteniendo ARs vencidas para técnico {tecnico}: {e}")
            return []

    def _guardar_html_debug(self, html_content: str, filename: str):
        """
        Guarda el HTML generado en un archivo para debug
        """
        try:
            import os
            debug_dir = os.path.join(os.path.dirname(__file__), "debug_html")
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            filepath = os.path.join(debug_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML guardado en: {filepath}")
        except Exception as e:
            self.logger.error(f"Error guardando HTML debug: {e}")


def main():
    """
    Función principal para ejecutar el manager directamente con argumentos
    """
    import sys
    import argparse
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(description='Manager de No Conformidades')
    parser.add_argument('--force-calidad', action='store_true', 
                       help='Forzar generación del correo de calidad')
    parser.add_argument('--force-tecnicos', action='store_true',
                       help='Forzar generación de correos de técnicos')
    parser.add_argument('--debug', action='store_true',
                       help='Activar modo debug')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging si debug está activado
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = None
    try:
        logger.info("=== INICIANDO MANAGER NO CONFORMIDADES ===")
        
        # Crear el manager
        manager = NoConformidadesManager()
        
        if args.force_calidad:
            logger.info("Ejecutando generación forzada del correo de calidad...")
            manager._generar_correo_calidad()
            
        if args.force_tecnicos:
            logger.info("Ejecutando generación forzada de correos de técnicos...")
            manager._generar_correos_tecnicos()
            
        if not args.force_calidad and not args.force_tecnicos:
            logger.info("Ejecutando lógica completa...")
            success = manager.ejecutar_logica_especifica()
            if not success:
                logger.error("Error en la ejecución de la lógica específica")
                return 1
        
        logger.info("=== MANAGER NO CONFORMIDADES COMPLETADO EXITOSAMENTE ===")
        return 0
        
    except Exception as e:
        logger.error(f"Error crítico en el manager: {e}")
        return 1
    finally:
        # Cerrar conexiones
        if manager:
            try:
                manager.close_connections()
                logger.info("Conexiones cerradas correctamente")
            except Exception as e:
                logger.warning(f"Error cerrando conexiones: {e}")


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)