"""Manager de Expedientes simplificado integrado con framework común.

Responsabilidades:
 - Obtener datos de expedientes mediante conexiones inyectadas
 - Generar un informe HTML (sin envío ni scheduling)
"""

from typing import Dict, List
import logging
import json
from datetime import datetime

from src.common.database import AccessDatabase
from src.common.html_report_generator import HTMLReportGenerator
from src.common.reporting.table_builder import build_table_html


def safe_str(value) -> str:
    """Convierte un valor a string de forma segura"""
    if value is None:
        return '&nbsp;'
    return str(value)


class ExpedientesManager:
    """Manager independiente (sin herencia) centrado sólo en lógica de expedientes."""

    def __init__(self, db_expedientes: AccessDatabase, db_tareas: AccessDatabase, logger: logging.Logger | None = None):
        self.db_expedientes = db_expedientes
        self.db_tareas = db_tareas
        self.logger = logger or logging.getLogger(__name__)
        self.html_generator = HTMLReportGenerator()
    from src.common.reporting.table_builder import build_table_html

    def get_expedientes_tsol_sin_cod_s4h(self) -> List[Dict]:
        """Obtiene expedientes TSOL adjudicados sin código S4H"""
        try:
            db_expedientes = self.db_expedientes
            query = """
                SELECT TbExpedientes.IDExpediente, TbExpedientes.CodExp, TbExpedientes.Nemotecnico, 
                       TbExpedientes.Titulo, TbUsuariosAplicaciones.Nombre, CadenaJuridicas, 
                       TbExpedientes.FECHAADJUDICACION, TbExpedientes.CodS4H 
                FROM (TbExpedientes LEFT JOIN TbExpedientesConEntidades 
                      ON TbExpedientes.IDExpediente = TbExpedientesConEntidades.IDExpediente) 
                     LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
                WHERE (((TbExpedientesConEntidades.CadenaJuridicas)='TSOL') 
                       AND ((TbExpedientes.Adjudicado)='Sí')  
                       AND ((TbExpedientes.CodS4H) Is Null) 
                       AND ((TbExpedientes.AplicaTareaS4H) <>'No'))
            """
            result = db_expedientes.execute_query(query)
            
            expedientes = []
            for row in result:
                expedientes.append({
                    'IDExpediente': row.get('IDExpediente'),
                    'CodExp': row.get('CodExp', ''),
                    'Nemotecnico': row.get('Nemotecnico', ''),
                    'Titulo': row.get('Titulo', ''),
                    'ResponsableCalidad': row.get('Nombre', ''),
                    'CadenaJuridicas': row.get('CadenaJuridicas', ''),
                    'FechaAdjudicacion': row.get('FECHAADJUDICACION'),
                    'CodS4H': row.get('CodS4H', '')
                })
            
            return expedientes
        except Exception as e:
            self.logger.error(
                f"Error obteniendo expedientes TSOL sin código S4H: {e}",
                extra={'context': 'get_expedientes_tsol_sin_cod_s4h'}
            )
            return []

    def get_expedientes_a_punto_finalizar(self) -> List[Dict]:
        """Obtiene expedientes a punto de recepcionar/finalizar"""
        try:
            db_expedientes = self.db_expedientes
            query = """
                SELECT IDExpediente, CodExp, Nemotecnico, Titulo, FechaInicioContrato, 
                       FechaFinContrato, DateDiff('d',Date(),[FechaFinContrato]) AS Dias,
                       FECHACERTIFICACION, GARANTIAMESES, FechaFinGarantia, Nombre 
                FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones 
                     ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
                WHERE (((DateDiff('d',Date(),[FechaFinContrato]))>-1 
                        And (DateDiff('d',Date(),[FechaFinContrato]))<15) 
                       AND ((TbExpedientes.EsBasado)='Sí')) 
                      OR (((DateDiff('d',Date(),[FechaFinContrato]))>-1 
                           And (DateDiff('d',Date(),[FechaFinContrato]))<15) 
                          AND ((TbExpedientes.EsExpediente)='Sí'))
            """
            result = db_expedientes.execute_query(query)
            
            expedientes = []
            for row in result:
                expedientes.append({
                    'IDExpediente': row.get('IDExpediente'),
                    'CodExp': row.get('CodExp', ''),
                    'Nemotecnico': row.get('Nemotecnico', ''),
                    'Titulo': row.get('Titulo', ''),
                    'FechaInicioContrato': row.get('FechaInicioContrato'),
                    'FechaFinContrato': row.get('FechaFinContrato'),
                    'DiasParaFin': row.get('Dias'),
                    'FechaCertificacion': row.get('FECHACERTIFICACION'),
                    'GarantiaMeses': row.get('GARANTIAMESES'),
                    'FechaFinGarantia': row.get('FechaFinGarantia'),
                    'ResponsableCalidad': row.get('Nombre', '')
                })
            
            return expedientes
        except Exception as e:
            self.logger.error(
                f"Error obteniendo expedientes a punto de finalizar: {e}",
                extra={'context': 'get_expedientes_a_punto_finalizar'}
            )
            return []

    def get_hitos_a_punto_finalizar(self) -> List[Dict]:
        """Obtiene hitos de expedientes a punto de recepcionar"""
        try:
            db_expedientes = self.db_expedientes
            query = """
                SELECT TbExpedientesHitos.IDExpediente, CodExp, Nemotecnico, Titulo, 
                       TbExpedientesHitos.Descripcion, FechaHito, 
                       DateDiff('d',Date(),[FechaHito]) AS Dias, Nombre 
                FROM (TbExpedientesHitos INNER JOIN TbExpedientes 
                      ON TbExpedientesHitos.IDExpediente = TbExpedientes.IDExpediente) 
                     LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
                WHERE (((DateDiff('d',Date(),[FechaHito]))>-1 And (DateDiff('d',Date(),[FechaHito]))<15))
            """
            result = db_expedientes.execute_query(query)
            
            hitos = []
            for row in result:
                hitos.append({
                    'IDExpediente': row.get('IDExpediente'),
                    'CodExp': row.get('CodExp', ''),
                    'Nemotecnico': row.get('Nemotecnico', ''),
                    'Titulo': row.get('Titulo', ''),
                    'Descripcion': row.get('Descripcion', ''),
                    'FechaHito': row.get('FechaHito'),
                    'DiasParaFin': row.get('Dias'),
                    'ResponsableCalidad': row.get('Nombre', '')
                })
            
            return hitos
        except Exception as e:
            self.logger.error(
                f"Error obteniendo hitos a punto de finalizar: {e}",
                extra={'context': 'get_hitos_a_punto_finalizar'}
            )
            return []

    def get_expedientes_estado_desconocido(self) -> List[Dict]:
        """Obtiene expedientes con estado desconocido"""
        try:
            db_expedientes = self.db_expedientes
            query = """
                SELECT IDExpediente, CodExp, Nemotecnico, Titulo, FechaInicioContrato, 
                       FechaFinContrato, GARANTIAMESES, Estado, Nombre 
                FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones 
                     ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
                WHERE Estado='Desconocido'
            """
            result = db_expedientes.execute_query(query)
            
            expedientes = []
            for row in result:
                expedientes.append({
                    'IDExpediente': row.get('IDExpediente'),
                    'CodExp': row.get('CodExp', ''),
                    'Nemotecnico': row.get('Nemotecnico', ''),
                    'Titulo': row.get('Titulo', ''),
                    'FechaInicioContrato': row.get('FechaInicioContrato'),
                    'FechaFinContrato': row.get('FechaFinContrato'),
                    'GarantiaMeses': row.get('GARANTIAMESES'),
                    'Estado': row.get('Estado', ''),
                    'ResponsableCalidad': row.get('Nombre', '')
                })
            
            return expedientes
        except Exception as e:
            self.logger.error(
                f"Error obteniendo expedientes con estado desconocido: {e}",
                extra={'context': 'get_expedientes_estado_desconocido'}
            )
            return []

    def get_expedientes_adjudicados_sin_contrato(self) -> List[Dict]:
        """
        Obtiene expedientes adjudicados sin datos de contrato
        Basado en la función getColAdjudicadosSinContrato() del script original TareaExpedientes.vbs
        """
        try:
            db_expedientes = self.db_expedientes
            # Query exacta del script original con todas las condiciones
            query = """
                SELECT IDExpediente, CodExp, Nemotecnico, Titulo, FechaInicioContrato, 
                       FechaFinContrato, FECHAADJUDICACION, GARANTIAMESES, Nombre 
                FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones 
                     ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
                WHERE FechaInicioContrato Is Null 
                      AND GARANTIAMESES Is Null 
                      AND FechaFinContrato Is Null 
                      AND Not FECHAADJUDICACION Is Null 
                      AND APLICAESTADO<>'No'
            """
            result = db_expedientes.execute_query(query)
            
            expedientes = []
            for row in result:
                expedientes.append({
                    'IDExpediente': row.get('IDExpediente'),
                    'CodExp': row.get('CodExp', ''),
                    'Nemotecnico': row.get('Nemotecnico', ''),
                    'Titulo': row.get('Titulo', ''),
                    'FechaInicioContrato': row.get('FechaInicioContrato'),
                    'FechaFinContrato': row.get('FechaFinContrato'),
                    'FechaAdjudicacion': row.get('FECHAADJUDICACION'),
                    'GarantiaMeses': row.get('GARANTIAMESES'),
                    'ResponsableCalidad': row.get('Nombre', '')
                })
            
            return expedientes
        except Exception as e:
            self.logger.error(
                f"Error obteniendo expedientes adjudicados sin contrato: {e}",
                extra={'context': 'get_expedientes_adjudicados_sin_contrato'}
            )
            return []

    def get_expedientes_fase_oferta_mucho_tiempo(self) -> List[Dict]:
        """Obtiene expedientes en fase de oferta sin resolución en más de 45 días"""
        try:
            db_expedientes = self.db_expedientes
            query = """
                SELECT TbExpedientes.IDExpediente, TbExpedientes.CodExp, TbExpedientes.Nemotecnico, 
                       TbExpedientes.Titulo, TbExpedientes.FechaInicioContrato, TbExpedientes.FECHAOFERTA, 
                       TbUsuariosAplicaciones.Nombre 
                FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones 
                     ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id 
                WHERE ((Not (TbExpedientes.FECHAOFERTA) Is Null) 
                       AND ((DateDiff('d',[FECHAOFERTA],Date()))>=45) 
                       AND ((TbExpedientes.FECHAPERDIDA) Is Null) 
                       AND ((TbExpedientes.FECHAADJUDICACION) Is Null) 
                       AND ((TbExpedientes.FECHADESESTIMADA) Is Null))
            """
            result = db_expedientes.execute_query(query)
            
            expedientes = []
            for row in result:
                expedientes.append({
                    'IDExpediente': row.get('IDExpediente'),
                    'CodExp': row.get('CodExp', ''),
                    'Nemotecnico': row.get('Nemotecnico', ''),
                    'Titulo': row.get('Titulo', ''),
                    'FechaInicioContrato': row.get('FechaInicioContrato'),
                    'FechaOferta': row.get('FECHAOFERTA'),
                    'ResponsableCalidad': row.get('Nombre', '')
                })
            
            return expedientes
        except Exception as e:
            self.logger.error(
                f"Error obteniendo expedientes en fase de oferta por mucho tiempo: {e}",
                extra={'context': 'get_expedientes_fase_oferta_mucho_tiempo'}
            )
            return []

    # Métodos de emails / scheduling eliminados según refactor solicitado.

    # _get_tramitadores_emails eliminado

    def _guardar_html_debug(self, html_content: str, filename: str):
        """Guarda el HTML generado en un archivo para debug"""
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
            self.logger.error(
                f"Error guardando HTML debug: {e}",
                extra={'context': '_guardar_html_debug'}
            )

    # _build_table_html eliminado en favor de build_table_html común (common.reporting.table_builder)

    def generate_expedientes_report_html(self) -> str:
        """Genera el reporte HTML completo de Expedientes y registra métricas detalladas.

        Logging estructurado para Grafana/Loki:
          - event: 'expedientes_report_start' / 'expedientes_report_empty' / 'expedientes_report_section' / 'expedientes_report_summary'
          - metric_name / metric_value: pares genéricos ya utilizados en el ecosistema
          - section: slug de la sección (sin espacios ni acentos) para facilitar agregaciones
        """
        try:
            self.logger.info(
                "Inicio generación reporte Expedientes",
                extra={'event': 'expedientes_report_start', 'app': 'EXPEDIENTES'}
            )
            sections = [
                ("Expedientes TSOL adjudicados sin código S4H", self.get_expedientes_tsol_sin_cod_s4h()),
                ("Expedientes a punto de finalizar", self.get_expedientes_a_punto_finalizar()),
                ("Hitos a punto de finalizar", self.get_hitos_a_punto_finalizar()),
                ("Expedientes con estado desconocido", self.get_expedientes_estado_desconocido()),
                ("Expedientes adjudicados sin contrato", self.get_expedientes_adjudicados_sin_contrato()),
                ("Expedientes en fase oferta > 45 días", self.get_expedientes_fase_oferta_mucho_tiempo()),
            ]
            non_empty = [s for s in sections if s[1]]
            if not non_empty:
                self.logger.info(
                    "Sin datos para generar reporte de expedientes",
                    extra={
                        'event': 'expedientes_report_empty',
                        'metric_name': 'expedientes_report_sections',
                        'metric_value': 0,
                        'app': 'EXPEDIENTES'
                    }
                )
                return ""

            def _slug(title: str) -> str:
                import unicodedata, re
                norm = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
                norm = norm.lower()
                norm = re.sub(r'[^a-z0-9]+', '_', norm).strip('_')
                return norm[:60]
            parts = [self.html_generator.generar_header_moderno("INFORME DE AVISOS DE EXPEDIENTES")]
            total_rows = 0
            for title, data in non_empty:
                parts.append(build_table_html(title, data, sort_headers=True))
                row_count = len(data)
                total_rows += row_count
                self.logger.info(
                    f"Sección '{title}' generada con {row_count} filas",
                    extra={
                        'event': 'expedientes_report_section',
                        'section': _slug(title),
                        'metric_name': 'expedientes_section_rows',
                        'metric_value': row_count,
                        'app': 'EXPEDIENTES'
                    }
                )
            parts.append(self.html_generator.generar_footer_moderno())
            html = ''.join(parts)
            self.logger.info(
                "Resumen reporte expedientes",
                extra={
                    'event': 'expedientes_report_summary',
                    'metric_name': 'expedientes_report_sections',
                    'metric_value': len(non_empty),
                    'total_rows': total_rows,
                    'html_length': len(html),
                    'app': 'EXPEDIENTES'
                }
            )
            return html
        except Exception as e:
            self.logger.error(
                f"Error generando reporte de expedientes: {e}",
                extra={'context': 'generate_expedientes_report_html'}
            )
            return ""

    # generate_email_body eliminado en favor de generate_expedientes_report_html

    # Métodos de registro / scheduling eliminados; orchestration externa deberá usarlos si aplica.

    # ejecutar_logica_especifica / run / execute eliminados: orquestación externa se encargará.

    def close_connections(self):
        """Cierra las conexiones a las bases de datos"""
        try:
            if self.db_expedientes:
                try:
                    self.db_expedientes.disconnect()
                    self.db_expedientes = None
                except Exception as e:
                    self.logger.warning(f"Error cerrando conexión Expedientes: {e}")
            
            if self.db_tareas:
                try:
                    self.db_tareas.disconnect()
                    self.db_tareas = None
                except Exception as e:
                    self.logger.warning(f"Error cerrando conexión Tareas: {e}")
        except Exception as e:
            self.logger.error(
                f"Error cerrando conexiones: {e}",
                extra={'context': 'close_connections'}
            )


class JsonFormatter(logging.Formatter):
    """Formatter que convierte los registros a JSON con campos estándar y extras."""
    def format(self, record: logging.LogRecord) -> str:
        base = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'logger': record.name
        }
        # Incluir extras (metric/context) excluyendo claves estándar
        standard = set(['name','msg','args','levelname','levelno','pathname','filename','module','exc_info','exc_text','stack_info','lineno','funcName','created','msecs','relativeCreated','thread','threadName','processName','process'])
        for k, v in record.__dict__.items():
            if k not in standard and k not in base:
                base[k] = v
        return json.dumps(base, ensure_ascii=False)


def main():
    """Entrada CLI mínima para depuración manual.

    Nota: El manager requiere instancias de AccessDatabase inyectadas. Aquí sólo se
    muestran placeholders; en un entorno real se deben construir con cadenas de conexión
    válidas o reemplazarse por mocks para pruebas manuales.
    """
    import sys
    import argparse
    
    # Configurar logging con JsonFormatter
    root = logging.getLogger()
    root.handlers = []
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(description='Manager de Expedientes')
    parser.add_argument('--debug', action='store_true',
                       help='Activar modo debug')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging si debug está activado
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = None
    logger = logging.getLogger(__name__)
    try:
        logger.info("=== INICIANDO MANAGER EXPEDIENTES (modo standalone) ===")
        logger.warning("Instancias reales de AccessDatabase no configuradas; usando None (sólo HTML vacío)")
        # Placeholders: en uso real proporcionar AccessDatabase(...)
        db_exp = None  # type: ignore
        db_tareas = None  # type: ignore
        manager = ExpedientesManager(db_exp, db_tareas, logger=logger)  # type: ignore
        html = manager.generate_expedientes_report_html()
        if html:
            logger.info("Reporte generado (longitud=%d)", len(html))
        else:
            logger.info("Sin datos para generar reporte")
        return 0
    except Exception as e:
        logger.error(f"Error crítico en el manager: {e}", extra={'context': 'main'})
        return 1
    finally:
        if manager:
            try:
                manager.close_connections()
                logger.info("Conexiones cerradas correctamente")
            except Exception as e:
                logger.warning(f"Error cerrando conexiones: {e}", extra={'context': 'main_close'})


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)