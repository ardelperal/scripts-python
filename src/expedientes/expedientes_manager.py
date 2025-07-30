"""
Gestor de Expedientes
Adaptación del script legacy Expedientes.vbs
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ..common import config
from ..common.database import AccessDatabase
from ..common.utils import (
    format_date, 
    send_email,
    register_email_in_database,
    generate_html_header,
    generate_html_footer,
    load_css_content,
    safe_str,
    send_notification_email,
    get_admin_emails_string
)

logger = logging.getLogger(__name__)


class ExpedientesManager:
    """Gestor para el módulo de expedientes"""
    
    def __init__(self):
        """Inicializar el gestor de expedientes"""
        self.expedientes_conn = None
        self.correos_conn = None
        self.tareas_conn = None
        
        # Inicializar conexiones
        self._init_connections()
    
    def _formatear_fecha_access(self, fecha):
        """
        Formatear fecha para consultas de Access
        
        Args:
            fecha: Fecha a formatear (datetime.date, datetime.datetime o string)
            
        Returns:
            str: Fecha formateada como #MM/dd/yyyy# para Access
        """
        from datetime import datetime, date
        
        if fecha is None:
            return None
            
        # Si es string, intentar parsearlo
        if isinstance(fecha, str):
            try:
                # Intentar formato YYYY-MM-DD
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                try:
                    # Intentar formato MM/DD/YYYY
                    fecha_obj = datetime.strptime(fecha, '%m/%d/%Y').date()
                except ValueError:
                    logger.error(f"No se pudo parsear la fecha: {fecha}")
                    return None
        elif isinstance(fecha, datetime):
            fecha_obj = fecha.date()
        elif isinstance(fecha, date):
            fecha_obj = fecha
        else:
            logger.error(f"Tipo de fecha no soportado: {type(fecha)}")
            return None
        
        # Formatear para Access: #MM/dd/yyyy#
        return f"#{fecha_obj.strftime('%m/%d/%Y')}#"

    def _init_connections(self):
        """Inicializar conexiones a las bases de datos"""
        try:
            # Conexión a base de datos de expedientes
            self.expedientes_conn = AccessDatabase(config.get_db_expedientes_connection_string())
            logger.info("Conectado a base de datos Access de expedientes")
            
            # Conexión a base de datos de correos
            self.correos_conn = AccessDatabase(config.get_db_correos_connection_string())
            
            # Conexión a base de datos de tareas
            self.tareas_conn = AccessDatabase(config.get_db_tareas_connection_string())
            
        except Exception as e:
            logger.error(f"Error inicializando conexiones: {e}")
            raise
    
    def close_connections(self):
        """Cerrar todas las conexiones"""
        try:
            if self.expedientes_conn:
                if hasattr(self.expedientes_conn, 'close'):
                    self.expedientes_conn.close()
            if self.correos_conn:
                if hasattr(self.correos_conn, 'close'):
                    self.correos_conn.close()
            if self.tareas_conn:
                if hasattr(self.tareas_conn, 'close'):
                    self.tareas_conn.close()
            logger.info("Conexiones cerradas correctamente")
        except Exception as e:
            logger.error(f"Error cerrando conexiones: {e}")
    
    def get_expedientes_about_to_finish(self, days_threshold: int = 15) -> List[Dict]:
        """
        Obtener expedientes que están próximos a finalizar
        
        Args:
            days_threshold: Días de umbral para considerar próximo a finalizar
            
        Returns:
            Lista de expedientes próximos a finalizar
        """
        try:
            query = """
            SELECT IDExpediente, CodExp, Nemotecnico, Titulo, FechaInicioContrato, 
                   FechaFinContrato, FECHACERTIFICACION, GARANTIAMESES, FechaFinGarantia, Nombre
            FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones 
            ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id
            WHERE ((TbExpedientes.EsBasado = 'Sí') OR (TbExpedientes.EsExpediente = 'Sí'))
            AND TbExpedientes.FechaFinContrato IS NOT NULL
            """
            
            cursor = self.expedientes_conn.cursor()
            cursor.execute(query)
            
            expedientes = []
            today = datetime.now().date()
            
            for row in cursor.fetchall():
                fecha_fin = row[5]  # FechaFinContrato
                if fecha_fin:
                    if isinstance(fecha_fin, str):
                        try:
                            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                fecha_fin = datetime.strptime(fecha_fin, '%d/%m/%Y').date()
                            except ValueError:
                                continue
                    elif hasattr(fecha_fin, 'date'):
                        fecha_fin = fecha_fin.date()
                    
                    dias_para_fin = (fecha_fin - today).days
                    
                    # Solo incluir si está dentro del umbral y no ha pasado más de 1 día
                    if -1 <= dias_para_fin < days_threshold:
                        expedientes.append({
                            'id_expediente': row[0],
                            'codigo_exp': row[1] if row[1] else "&nbsp;",
                            'nemotecnico': row[2] if row[2] else "&nbsp;",
                            'titulo': row[3] if row[3] else "&nbsp;",
                            'fecha_inicio': format_date(row[4]) if row[4] else "&nbsp;",
                            'fecha_fin': format_date(row[5]) if row[5] else "&nbsp;",
                            'fecha_certificacion': format_date(row[6]) if row[6] else "&nbsp;",
                            'garantia_meses': row[7] if row[7] and str(row[7]).isdigit() else "&nbsp;",
                            'fecha_fin_garantia': format_date(row[8]) if row[8] else "&nbsp;",
                            'responsable': row[9] if row[9] else "&nbsp;",
                            'dias_para_fin': dias_para_fin
                        })
            
            logger.info(f"Encontrados {len(expedientes)} expedientes próximos a finalizar")
            return expedientes
            
        except Exception as e:
            logger.error(f"Error obteniendo expedientes próximos a finalizar: {e}")
            return []
    
    def get_hitos_about_to_finish(self, days_threshold: int = 15) -> List[Dict]:
        """
        Obtener hitos que están próximos a finalizar
        
        Args:
            days_threshold: Días de umbral para considerar próximo a finalizar
            
        Returns:
            Lista de hitos próximos a finalizar
        """
        try:
            query = """
            SELECT TbExpedientes.IDExpediente, TbExpedientes.CodExp, TbExpedientes.Nemotecnico,
                   TbExpedientes.Titulo, TbUsuariosAplicaciones.Nombre, TbHitos.FechaHito,
                   TbHitos.Descripcion
            FROM (TbExpedientes LEFT JOIN TbHitos ON TbExpedientes.IDExpediente = TbHitos.IDExpediente)
            LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id
            WHERE TbHitos.FechaHito IS NOT NULL
            ORDER BY TbHitos.FechaHito
            """
            
            cursor = self.expedientes_conn.cursor()
            cursor.execute(query)
            
            hitos = []
            today = datetime.now().date()
            
            for row in cursor.fetchall():
                fecha_hito = row[5]  # FechaHito
                if fecha_hito:
                    if isinstance(fecha_hito, str):
                        try:
                            fecha_hito = datetime.strptime(fecha_hito, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                fecha_hito = datetime.strptime(fecha_hito, '%d/%m/%Y').date()
                            except ValueError:
                                continue
                    elif hasattr(fecha_hito, 'date'):
                        fecha_hito = fecha_hito.date()
                    
                    dias_para_fin = (fecha_hito - today).days
                    
                    # Solo incluir si está dentro del umbral y no ha pasado
                    if 0 <= dias_para_fin <= days_threshold:
                        hitos.append({
                            'id_expediente': row[0],
                            'codigo_exp': row[1] if row[1] else "&nbsp;",
                            'nemotecnico': row[2] if row[2] else "&nbsp;",
                            'titulo': row[3] if row[3] else "&nbsp;",
                            'responsable': row[4] if row[4] else "&nbsp;",
                            'fecha_hito': format_date(fecha_hito),
                            'descripcion': row[6] if row[6] else "&nbsp;",
                            'dias_para_fin': dias_para_fin
                        })
            
            logger.info(f"Encontrados {len(hitos)} hitos próximos a finalizar")
            return hitos
            
        except Exception as e:
            logger.error(f"Error obteniendo hitos próximos a finalizar: {e}")
            return []
    
    def get_expedientes_sin_cods4h(self) -> List[Dict]:
        """
        Obtener expedientes adjudicados TSOL sin CodS4H
        
        Returns:
            Lista de expedientes sin CodS4H
        """
        try:
            query = """
            SELECT TbExpedientes.IDExpediente, TbExpedientes.CodExp, TbExpedientes.Nemotecnico,
                   TbExpedientes.Titulo, TbUsuariosAplicaciones.Nombre, 
                   TbExpedientesConEntidades.CadenaJuridicas, TbExpedientes.FECHAADJUDICACION,
                   TbExpedientes.CodS4H
            FROM (TbExpedientes LEFT JOIN TbExpedientesConEntidades 
                  ON TbExpedientes.IDExpediente = TbExpedientesConEntidades.IDExpediente)
            LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id
            WHERE TbExpedientesConEntidades.CadenaJuridicas = 'TSOL'
            AND TbExpedientes.Adjudicado = 'Sí'
            AND TbExpedientes.CodS4H IS NULL
            AND TbExpedientes.AplicaTareaS4H <> 'No'
            """
            
            cursor = self.expedientes_conn.cursor()
            cursor.execute(query)
            
            expedientes = []
            for row in cursor.fetchall():
                expedientes.append({
                    'id_expediente': row[0],
                    'codigo_exp': row[1] if row[1] else "&nbsp;",
                    'nemotecnico': row[2] if row[2] else "&nbsp;",
                    'titulo': row[3] if row[3] else "&nbsp;",
                    'responsable': row[4] if row[4] else "&nbsp;",
                    'juridica': row[5] if row[5] else "&nbsp;",
                    'fecha_adjudicacion': format_date(row[6]) if row[6] else "&nbsp;",
                    'cod_s4h': row[7] if row[7] else "&nbsp;"
                })
            
            logger.info(f"Encontrados {len(expedientes)} expedientes TSOL sin CodS4H")
            return expedientes
            
        except Exception as e:
            logger.error(f"Error obteniendo expedientes sin CodS4H: {e}")
            return []
    
    def get_expedientes_fase_oferta_largo_tiempo(self, days_threshold: int = 45) -> List[Dict]:
        """
        Obtener expedientes en fase de oferta por mucho tiempo
        Replica la lógica del VBS legacy: expedientes con FECHAOFERTA >= days_threshold días atrás
        y que no tengan FECHAPERDIDA, FECHAADJUDICACION ni FECHADESESTIMADA
        
        Args:
            days_threshold: Días de umbral para considerar mucho tiempo (por defecto 45)
            
        Returns:
            Lista de expedientes en fase de oferta por mucho tiempo
        """
        try:
            # Replicamos exactamente la consulta del VBS legacy
            query = """
            SELECT TbExpedientes.IDExpediente, TbExpedientes.CodExp, TbExpedientes.Nemotecnico,
                   TbExpedientes.Titulo, TbExpedientes.FechaInicioContrato, TbExpedientes.FECHAOFERTA,
                   TbUsuariosAplicaciones.Nombre
            FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones
            ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id
            WHERE TbExpedientes.FECHAOFERTA IS NOT NULL
            AND TbExpedientes.FECHAPERDIDA IS NULL
            AND TbExpedientes.FECHAADJUDICACION IS NULL
            AND TbExpedientes.FECHADESESTIMADA IS NULL
            """
            
            cursor = self.expedientes_conn.cursor()
            cursor.execute(query)
            
            expedientes = []
            today = datetime.now().date()
            
            for row in cursor.fetchall():
                fecha_oferta = row[5]  # FECHAOFERTA
                if fecha_oferta:
                    # Parsear fecha de oferta
                    if isinstance(fecha_oferta, str):
                        try:
                            fecha_oferta = datetime.strptime(fecha_oferta, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                fecha_oferta = datetime.strptime(fecha_oferta, '%d/%m/%Y').date()
                            except ValueError:
                                continue
                    elif hasattr(fecha_oferta, 'date'):
                        fecha_oferta = fecha_oferta.date()
                    
                    # Calcular días desde la oferta (equivalente a DateDiff('d',[FECHAOFERTA],Date()) en VBS)
                    dias_desde_oferta = (today - fecha_oferta).days
                    
                    # Solo incluir si ha pasado el umbral de días (>=45 en el VBS original)
                    if dias_desde_oferta >= days_threshold:
                        expedientes.append({
                            'id_expediente': row[0],
                            'codigo_exp': row[1] if row[1] else "&nbsp;",
                            'nemotecnico': row[2] if row[2] else "&nbsp;",
                            'titulo': row[3] if row[3] else "&nbsp;",
                            'fecha_inicio_contrato': format_date(row[4]) if row[4] else "&nbsp;",
                            'fecha_oferta': format_date(fecha_oferta),
                            'responsable': row[6] if row[6] else "&nbsp;",
                            'dias_desde_oferta': dias_desde_oferta
                        })
            
            logger.info(f"Encontrados {len(expedientes)} expedientes en fase de oferta por mucho tiempo")
            return expedientes
            
        except Exception as e:
            logger.error(f"Error obteniendo expedientes en fase de oferta: {e}")
            return []
    
    def generate_html_report(self) -> str:
        """
        Generar reporte HTML con todos los datos
        
        Returns:
            Contenido HTML del reporte
        """
        try:
            # Obtener datos
            expedientes_proximos = self.get_expedientes_about_to_finish()
            hitos_proximos = self.get_hitos_about_to_finish()
            expedientes_sin_cods4h = self.get_expedientes_sin_cods4h()
            expedientes_oferta_largo = self.get_expedientes_fase_oferta_largo_tiempo()
            
            # Generar HTML
            title = f"Reporte Diario de Expedientes - {format_date(datetime.now())}"
            css_path = Path(__file__).parent.parent.parent / "herramientas" / "CSS1.css"
            html_content = generate_html_header(title, load_css_content(css_path))
            html_content += f"<h1>Reporte Diario de Expedientes</h1>\n<p>Fecha: {format_date(datetime.now())}</p>\n"
            
            # Sección de expedientes próximos a finalizar
            if expedientes_proximos:
                html_content += self._generate_expedientes_proximos_section(expedientes_proximos)
            
            # Sección de hitos próximos a finalizar
            if hitos_proximos:
                html_content += self._generate_hitos_proximos_section(hitos_proximos)
            
            # Sección de expedientes sin CodS4H
            if expedientes_sin_cods4h:
                html_content += self._generate_sin_cods4h_section(expedientes_sin_cods4h)
            
            # Sección de expedientes en oferta por mucho tiempo
            if expedientes_oferta_largo:
                html_content += self._generate_oferta_largo_section(expedientes_oferta_largo)
            
            html_content += generate_html_footer()
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generando reporte HTML: {e}")
            return ""
    
    def _generate_html_header(self) -> str:
        """
        Generar cabecera HTML (wrapper de la función común)
        
        Returns:
            Cabecera HTML como string
        """
        title = f"Reporte Diario de Expedientes - {format_date(datetime.now())}"
        css_path = Path(__file__).parent.parent.parent / "herramientas" / "CSS1.css"
        return generate_html_header(title, load_css_content(css_path))
    
    def _generate_html_footer(self) -> str:
        """
        Generar pie HTML (wrapper de la función común)
        
        Returns:
            Pie HTML como string
        """
        return generate_html_footer()
    
    def _generate_expedientes_proximos_section(self, expedientes: List[Dict]) -> str:
        """Generar sección de expedientes próximos a finalizar"""
        html = """
        <h2>Expedientes Próximos a Finalizar</h2>
        <table>
            <tr>
                <th>Expediente</th>
                <th>Fecha Finalización</th>
                <th>Estado</th>
                <th>Responsable</th>
                <th>Descripción</th>
            </tr>
        """
        
        for exp in expedientes:
            html += f"""
            <tr class="warning">
                <td>{safe_str(exp['expediente'])}</td>
                <td>{safe_str(exp['fecha_finalizacion'])}</td>
                <td>{safe_str(exp['estado'])}</td>
                <td>{safe_str(exp['responsable'])}</td>
                <td>{safe_str(exp['descripcion'])}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def _generate_hitos_proximos_section(self, hitos: List[Dict]) -> str:
        """Generar sección de hitos próximos a finalizar"""
        html = """
        <h2>Hitos Próximos a Finalizar</h2>
        <table>
            <tr>
                <th>ID Hito</th>
                <th>Expediente</th>
                <th>Descripción</th>
                <th>Fecha Límite</th>
                <th>Estado</th>
                <th>Responsable</th>
            </tr>
        """
        
        for hito in hitos:
            html += f"""
            <tr class="warning">
                <td>{safe_str(hito['id_hito'])}</td>
                <td>{safe_str(hito['expediente'])}</td>
                <td>{safe_str(hito['descripcion'])}</td>
                <td>{safe_str(hito['fecha_limite'])}</td>
                <td>{safe_str(hito['estado'])}</td>
                <td>{safe_str(hito['responsable'])}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def _generate_sin_cods4h_section(self, expedientes: List[Dict]) -> str:
        """Generar sección de expedientes sin CodS4H"""
        html = """
        <h2>Expedientes TSOL Adjudicados sin CodS4H</h2>
        <table>
            <tr>
                <th>Expediente</th>
                <th>Fecha Adjudicación</th>
                <th>Importe</th>
                <th>Proveedor</th>
                <th>Estado</th>
            </tr>
        """
        
        for exp in expedientes:
            html += f"""
            <tr class="danger">
                <td>{safe_str(exp['expediente'])}</td>
                <td>{safe_str(exp['fecha_adjudicacion'])}</td>
                <td>{safe_str(exp['importe'])}</td>
                <td>{safe_str(exp['proveedor'])}</td>
                <td>{safe_str(exp['estado'])}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def _generate_oferta_largo_section(self, expedientes: List[Dict]) -> str:
        """Generar sección de expedientes en oferta por mucho tiempo"""
        html = """
        <h2>Expedientes en Fase de Oferta por Mucho Tiempo</h2>
        <table>
            <tr>
                <th>Expediente</th>
                <th>Fecha Inicio Oferta</th>
                <th>Estado</th>
                <th>Responsable</th>
                <th>Descripción</th>
            </tr>
        """
        
        for exp in expedientes:
            html += f"""
            <tr class="warning">
                <td>{safe_str(exp['expediente'])}</td>
                <td>{safe_str(exp['fecha_inicio_oferta'])}</td>
                <td>{safe_str(exp['estado'])}</td>
                <td>{safe_str(exp['responsable'])}</td>
                <td>{safe_str(exp['descripcion'])}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def register_email_sent(self, to_email: str, subject: str, body: str) -> bool:
        """
        Registrar email enviado en la base de datos
        
        Args:
            to_email: Email de destino
            subject: Asunto del email
            body: Cuerpo del email
            
        Returns:
            True si se registró correctamente, False en caso contrario
        """
        try:
            from common.utils import register_email_in_database
            
            # Usar la función común para registrar el email
            success = register_email_in_database(
                db_connection=self.correos_conn,
                application="Expedientes",
                subject=subject,
                body=body,
                recipients=to_email
            )
            
            if success:
                logger.info(f"Email registrado correctamente para {to_email}")
            else:
                logger.error(f"Error registrando email para {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error registrando email enviado: {e}")
            return False
    
    def execute_daily_task(self) -> bool:
        """
        Ejecutar la tarea diaria de expedientes
        
        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            logger.info("Iniciando tarea diaria de expedientes")
            
            # Generar reporte HTML
            html_report = self.generate_html_report()
            
            if not html_report:
                logger.warning("No se pudo generar el reporte HTML")
                # Aún así registrar la tarea como completada
                from common.utils import register_task_completion
                return register_task_completion(self.tareas_conn, "ExpedientesDiario")
            
            # Enviar correo con el reporte
            subject = f"Reporte Diario de Expedientes - {format_date(datetime.now())}"
            to_address = config.default_recipient
            
            success = send_email(
                to_address=to_address,
                subject=subject,
                body=html_report,
                is_html=True
            )
            
            if success:
                # Registrar envío usando el método de la clase
                self.register_email_sent(
                    to_email=to_address,
                    subject=subject,
                    body=html_report
                )
                logger.info("Tarea diaria de expedientes completada exitosamente")
            else:
                logger.error("Error enviando correo del reporte")
            
            # Registrar la tarea como completada usando la función común
            from common.utils import register_task_completion
            task_registered = register_task_completion(self.tareas_conn, "ExpedientesDiario")
            
            if not task_registered:
                logger.warning("Error registrando la tarea, pero la ejecución fue exitosa")
            
            return success
                
        except Exception as e:
            logger.error(f"Error ejecutando tarea diaria de expedientes: {e}")
            return False
