"""
Gestor de Expedientes
Adaptación del script legacy Expedientes.vbs
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from common import config
from common.database import AccessDatabase
from common.utils import (
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
    
    def get_expedientes_about_to_finish(self, days_threshold: int = 30) -> List[Dict]:
        """
        Obtener expedientes que están próximos a finalizar
        
        Args:
            days_threshold: Días de umbral para considerar próximo a finalizar
            
        Returns:
            Lista de expedientes próximos a finalizar
        """
        try:
            # Fecha límite
            limit_date = datetime.now() + timedelta(days=days_threshold)
            
            query = """
                SELECT 
                    Expediente,
                    FechaFinalizacion,
                    Estado,
                    Responsable,
                    Descripcion
                FROM Expedientes 
                WHERE FechaFinalizacion <= ? 
                AND Estado NOT IN ('Finalizado', 'Cancelado')
                ORDER BY FechaFinalizacion ASC
            """
            
            cursor = self.expedientes_conn.get_cursor()
            cursor.execute(query, [limit_date.strftime('%Y-%m-%d')])
            results = cursor.fetchall()
            
            expedientes = []
            for row in results:
                expedientes.append({
                    'expediente': row[0],
                    'fecha_finalizacion': row[1],
                    'estado': row[2],
                    'responsable': row[3],
                    'descripcion': row[4]
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
            # Fecha límite
            limit_date = datetime.now() + timedelta(days=days_threshold)
            
            query = """
                SELECT 
                    h.IdHito,
                    h.Expediente,
                    h.Descripcion,
                    h.FechaLimite,
                    h.Estado,
                    e.Responsable
                FROM Hitos h
                INNER JOIN Expedientes e ON h.Expediente = e.Expediente
                WHERE h.FechaLimite <= ? 
                AND h.Estado NOT IN ('Completado', 'Cancelado')
                ORDER BY h.FechaLimite ASC
            """
            
            cursor = self.expedientes_conn.get_cursor()
            cursor.execute(query, [limit_date.strftime('%Y-%m-%d')])
            results = cursor.fetchall()
            
            hitos = []
            for row in results:
                hitos.append({
                    'id_hito': row[0],
                    'expediente': row[1],
                    'descripcion': row[2],
                    'fecha_limite': row[3],
                    'estado': row[4],
                    'responsable': row[5]
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
                SELECT 
                    Expediente,
                    FechaAdjudicacion,
                    Importe,
                    Proveedor,
                    Estado
                FROM Expedientes 
                WHERE TipoExpediente = 'TSOL'
                AND Estado = 'Adjudicado'
                AND (CodS4H IS NULL OR CodS4H = '')
                ORDER BY FechaAdjudicacion DESC
            """
            
            cursor = self.expedientes_conn.get_cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            expedientes = []
            for row in results:
                expedientes.append({
                    'expediente': row[0],
                    'fecha_adjudicacion': row[1],
                    'importe': row[2],
                    'proveedor': row[3],
                    'estado': row[4]
                })
            
            logger.info(f"Encontrados {len(expedientes)} expedientes TSOL sin CodS4H")
            return expedientes
            
        except Exception as e:
            logger.error(f"Error obteniendo expedientes sin CodS4H: {e}")
            return []
    
    def get_expedientes_fase_oferta_largo_tiempo(self, days_threshold: int = 60) -> List[Dict]:
        """
        Obtener expedientes en fase de oferta por mucho tiempo
        
        Args:
            days_threshold: Días de umbral para considerar mucho tiempo
            
        Returns:
            Lista de expedientes en fase de oferta por mucho tiempo
        """
        try:
            # Fecha límite
            limit_date = datetime.now() - timedelta(days=days_threshold)
            
            query = """
                SELECT 
                    Expediente,
                    FechaInicioOferta,
                    Estado,
                    Responsable,
                    Descripcion
                FROM Expedientes 
                WHERE Estado = 'En Oferta'
                AND FechaInicioOferta <= ?
                ORDER BY FechaInicioOferta ASC
            """
            
            cursor = self.expedientes_conn.get_cursor()
            cursor.execute(query, [limit_date.strftime('%Y-%m-%d')])
            results = cursor.fetchall()
            
            expedientes = []
            for row in results:
                expedientes.append({
                    'expediente': row[0],
                    'fecha_inicio_oferta': row[1],
                    'estado': row[2],
                    'responsable': row[3],
                    'descripcion': row[4]
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
