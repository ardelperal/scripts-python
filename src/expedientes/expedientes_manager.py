"""
Manager de Expedientes - Migración del sistema original con mejoras del módulo de No Conformidades
"""

from datetime import datetime, date
from typing import Dict, List, Optional
import logging

from src.common.base_task import TareaDiaria
from src.common.config import Config
from src.common.database import AccessDatabase


def safe_str(value) -> str:
    """Convierte un valor a string de forma segura"""
    if value is None:
        return '&nbsp;'
    return str(value)


class ExpedientesManager(TareaDiaria):
    """Manager para el sistema de Expedientes con mejoras del módulo de No Conformidades"""
    
    def __init__(self):
        super().__init__(
            name="EXPEDIENTES",
            script_filename="run_expedientes.py",
            task_names=["ExpedientesDiario"],
            frequency_days=1
        )
        
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Conexiones a bases de datos
        self.db_expedientes = None
        self.db_tareas = None
        
        # CSS para el formato HTML
        self.css_content = self._load_css_content()
    
    def _get_expedientes_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de expedientes"""
        if self.db_expedientes is None:
            connection_string = self.config.get_db_expedientes_connection_string()
            self.db_expedientes = AccessDatabase(connection_string)
        return self.db_expedientes
    
    def _get_tareas_connection(self) -> AccessDatabase:
        """Obtiene la conexión a la base de datos de tareas"""
        if self.db_tareas is None:
            connection_string = self.config.get_db_tareas_connection_string()
            self.db_tareas = AccessDatabase(connection_string)
        return self.db_tareas
    
    def _load_css_content(self) -> str:
        """Carga el contenido CSS desde el archivo"""
        from ..common.utils import load_css_content
        return load_css_content(self.config.css_modern_file_path)
    
    def _format_date_display(self, date_value) -> str:
        """Formatea una fecha para mostrar en HTML"""
        if not date_value:
            return '&nbsp;'
        
        if isinstance(date_value, str):
            try:
                # Intentar parsear diferentes formatos de fecha
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        date_obj = datetime.strptime(date_value, fmt)
                        return date_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
                return date_value
            except:
                return date_value
        elif hasattr(date_value, 'strftime'):
            return date_value.strftime('%d/%m/%Y')
        else:
            return str(date_value)
    
    def _get_dias_class(self, dias: int) -> str:
        """Obtiene la clase CSS según los días restantes"""
        if dias <= 0:
            return 'dias-vencido'
        elif dias <= 7:
            return 'dias-critico'
        elif dias <= 15:
            return 'dias-alerta'
        else:
            return 'dias-normal'
    
    def _get_modern_html_header(self) -> str:
        """Genera la cabecera HTML moderna"""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INFORME DE AVISOS DE EXPEDIENTES</title>
    <style type="text/css">
        {self.css_content}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📋 INFORME DE AVISOS DE NO EXPEDIENTES</h1>
        <p class="fecha">Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
    </div>
"""
    
    def _get_modern_html_footer(self) -> str:
        """Genera el pie HTML moderno"""
        return """
    <div class="footer">
        <p>Este es un informe automático del sistema de gestión de expedientes.</p>
        <p>Para más información, contacte con el equipo de TI.</p>
    </div>
</div>
</body>
</html>
        """

    def get_expedientes_tsol_sin_cod_s4h(self) -> List[Dict]:
        """Obtiene expedientes TSOL adjudicados sin código S4H"""
        try:
            db_expedientes = self._get_expedientes_connection()
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
            self.logger.error(f"Error obteniendo expedientes TSOL sin código S4H: {e}")
            return []

    def get_expedientes_a_punto_finalizar(self) -> List[Dict]:
        """Obtiene expedientes a punto de recepcionar/finalizar"""
        try:
            db_expedientes = self._get_expedientes_connection()
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
            self.logger.error(f"Error obteniendo expedientes a punto de finalizar: {e}")
            return []

    def get_hitos_a_punto_finalizar(self) -> List[Dict]:
        """Obtiene hitos de expedientes a punto de recepcionar"""
        try:
            db_expedientes = self._get_expedientes_connection()
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
            self.logger.error(f"Error obteniendo hitos a punto de finalizar: {e}")
            return []

    def get_expedientes_estado_desconocido(self) -> List[Dict]:
        """Obtiene expedientes con estado desconocido"""
        try:
            db_expedientes = self._get_expedientes_connection()
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
            self.logger.error(f"Error obteniendo expedientes con estado desconocido: {e}")
            return []

    def get_expedientes_adjudicados_sin_contrato(self) -> List[Dict]:
        """
        Obtiene expedientes adjudicados sin datos de contrato
        Basado en la función getColAdjudicadosSinContrato() del script original TareaExpedientes.vbs
        """
        try:
            db_expedientes = self._get_expedientes_connection()
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
            self.logger.error(f"Error obteniendo expedientes adjudicados sin contrato: {e}")
            return []

    def get_expedientes_fase_oferta_mucho_tiempo(self) -> List[Dict]:
        """Obtiene expedientes en fase de oferta sin resolución en más de 45 días"""
        try:
            db_expedientes = self._get_expedientes_connection()
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
            self.logger.error(f"Error obteniendo expedientes en fase de oferta por mucho tiempo: {e}")
            return []

    # Funciones modernas de generación de HTML

    def _generate_modern_tsol_table_html(self, expedientes: List[Dict]) -> str:
        """Genera tabla HTML moderna para expedientes TSOL sin código S4H"""
        if not expedientes:
            return ""
        
        html = f"""
    <div class="section">
        <h2>🏢 Expedientes TSOL Adjudicados sin Código S4H</h2>
        <div class="table-container">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Código</th>
                        <th>Nemotécnico</th>
                        <th>Título</th>
                        <th>Resp. Calidad</th>
                        <th>Jurídica</th>
                        <th>F. Adjudicación</th>
                        <th>Cod S4H</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for exp in expedientes:
            fecha_adj = self._format_date_display(exp.get('FechaAdjudicacion'))
            html += f"""
                    <tr>
                        <td>{safe_str(exp.get('IDExpediente'))}</td>
                        <td>{safe_str(exp.get('CodExp'))}</td>
                        <td>{safe_str(exp.get('Nemotecnico'))}</td>
                        <td class="titulo-cell">{safe_str(exp.get('Titulo'))}</td>
                        <td>{safe_str(exp.get('ResponsableCalidad'))}</td>
                        <td>{safe_str(exp.get('CadenaJuridicas'))}</td>
                        <td>{fecha_adj}</td>
                        <td>{safe_str(exp.get('CodS4H'))}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        return html

    def _generate_modern_finalizar_table_html(self, expedientes: List[Dict]) -> str:
        """Genera tabla HTML moderna para expedientes a punto de finalizar"""
        if not expedientes:
            return ""
        
        html = f"""
    <div class="section">
        <h2>⏰ Expedientes a Punto de Finalizar</h2>
        <div class="table-container">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Código</th>
                        <th>Nemotécnico</th>
                        <th>Título</th>
                        <th>F. Inicio</th>
                        <th>F. Fin</th>
                        <th>Días</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for exp in expedientes:
            dias = exp.get('DiasParaFin', 0)
            dias_class = self._get_dias_class(dias)
            fecha_inicio = self._format_date_display(exp.get('FechaInicioContrato'))
            fecha_fin = self._format_date_display(exp.get('FechaFinContrato'))
            
            html += f"""
                    <tr>
                        <td>{safe_str(exp.get('IDExpediente'))}</td>
                        <td>{safe_str(exp.get('CodExp'))}</td>
                        <td>{safe_str(exp.get('Nemotecnico'))}</td>
                        <td class="titulo-cell">{safe_str(exp.get('Titulo'))}</td>
                        <td>{fecha_inicio}</td>
                        <td>{fecha_fin}</td>
                        <td class="{dias_class}">{safe_str(dias)}</td>
                        <td>{safe_str(exp.get('ResponsableCalidad'))}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        return html

    def _generate_modern_hitos_table_html(self, hitos: List[Dict]) -> str:
        """Genera tabla HTML moderna para hitos a punto de finalizar"""
        if not hitos:
            return ""
        
        html = f"""
    <div class="section">
        <h2>🎯 Hitos a Punto de Finalizar</h2>
        <div class="table-container">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Código</th>
                        <th>Nemotécnico</th>
                        <th>Título</th>
                        <th>Descripción Hito</th>
                        <th>F. Hito</th>
                        <th>Días</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for hito in hitos:
            dias = hito.get('DiasParaFin', 0)
            dias_class = self._get_dias_class(dias)
            fecha_hito = self._format_date_display(hito.get('FechaHito'))
            
            html += f"""
                    <tr>
                        <td>{safe_str(hito.get('IDExpediente'))}</td>
                        <td>{safe_str(hito.get('CodExp'))}</td>
                        <td>{safe_str(hito.get('Nemotecnico'))}</td>
                        <td class="titulo-cell">{safe_str(hito.get('Titulo'))}</td>
                        <td>{safe_str(hito.get('Descripcion'))}</td>
                        <td>{fecha_hito}</td>
                        <td class="{dias_class}">{safe_str(dias)}</td>
                        <td>{safe_str(hito.get('ResponsableCalidad'))}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        return html

    def _generate_modern_desconocido_table_html(self, expedientes: List[Dict]) -> str:
        """Genera tabla HTML moderna para expedientes con estado desconocido"""
        if not expedientes:
            return ""
        
        html = f"""
    <div class="section">
        <h2>❓ Expedientes con Estado Desconocido</h2>
        <div class="table-container">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Código</th>
                        <th>Nemotécnico</th>
                        <th>Título</th>
                        <th>F. Inicio</th>
                        <th>F. Fin</th>
                        <th>Garantía (meses)</th>
                        <th>Estado</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for exp in expedientes:
            fecha_inicio = self._format_date_display(exp.get('FechaInicioContrato'))
            fecha_fin = self._format_date_display(exp.get('FechaFinContrato'))
            
            html += f"""
                    <tr>
                        <td>{safe_str(exp.get('IDExpediente'))}</td>
                        <td>{safe_str(exp.get('CodExp'))}</td>
                        <td>{safe_str(exp.get('Nemotecnico'))}</td>
                        <td class="titulo-cell">{safe_str(exp.get('Titulo'))}</td>
                        <td>{fecha_inicio}</td>
                        <td>{fecha_fin}</td>
                        <td>{safe_str(exp.get('GarantiaMeses'))}</td>
                        <td class="estado-desconocido">{safe_str(exp.get('Estado'))}</td>
                        <td>{safe_str(exp.get('ResponsableCalidad'))}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        return html

    def _generate_modern_sin_contrato_table_html(self, expedientes: List[Dict]) -> str:
        """Genera tabla HTML moderna para expedientes adjudicados sin contrato"""
        if not expedientes:
            return ""
        
        html = f"""
    <div class="section">
        <h2>📋 Expedientes Adjudicados sin Datos de Contrato</h2>
        <div class="table-container">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Código</th>
                        <th>Nemotécnico</th>
                        <th>Título</th>
                        <th>F. Inicio</th>
                        <th>F. Fin</th>
                        <th>F. Adjudicación</th>
                        <th>Garantía (meses)</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for exp in expedientes:
            fecha_inicio = self._format_date_display(exp.get('FechaInicioContrato'))
            fecha_fin = self._format_date_display(exp.get('FechaFinContrato'))
            fecha_adj = self._format_date_display(exp.get('FechaAdjudicacion'))
            
            html += f"""
                    <tr>
                        <td>{safe_str(exp.get('IDExpediente'))}</td>
                        <td>{safe_str(exp.get('CodExp'))}</td>
                        <td>{safe_str(exp.get('Nemotecnico'))}</td>
                        <td class="titulo-cell">{safe_str(exp.get('Titulo'))}</td>
                        <td>{fecha_inicio}</td>
                        <td>{fecha_fin}</td>
                        <td>{fecha_adj}</td>
                        <td>{safe_str(exp.get('GarantiaMeses'))}</td>
                        <td>{safe_str(exp.get('ResponsableCalidad'))}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        return html

    def _generate_modern_oferta_tiempo_table_html(self, expedientes: List[Dict]) -> str:
        """Genera tabla HTML moderna para expedientes en fase de oferta por mucho tiempo"""
        if not expedientes:
            return ""
        
        html = f"""
    <div class="section">
        <h2>⏳ Expedientes en Fase de Oferta por Mucho Tiempo</h2>
        <div class="table-container">
            <table class="modern-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Código</th>
                        <th>Nemotécnico</th>
                        <th>Título</th>
                        <th>F. Inicio</th>
                        <th>F. Oferta</th>
                        <th>Resp. Calidad</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for exp in expedientes:
            fecha_inicio = self._format_date_display(exp.get('FechaInicioContrato'))
            fecha_oferta = self._format_date_display(exp.get('FechaOferta'))
            
            html += f"""
                    <tr>
                        <td>{safe_str(exp.get('IDExpediente'))}</td>
                        <td>{safe_str(exp.get('CodExp'))}</td>
                        <td>{safe_str(exp.get('Nemotecnico'))}</td>
                        <td class="titulo-cell">{safe_str(exp.get('Titulo'))}</td>
                        <td>{fecha_inicio}</td>
                        <td>{fecha_oferta}</td>
                        <td>{safe_str(exp.get('ResponsableCalidad'))}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        return html

    def get_admin_emails(self) -> List[str]:
        """Obtiene los correos de los administradores usando el módulo común"""
        try:
            from ..common.user_adapter import get_users_with_fallback
            
            db_tareas = self._get_tareas_connection()
            
            admin_users = get_users_with_fallback(
                user_type='admin',
                config=self.config,
                logger=self.logger,
                db_connection=db_tareas
            )
            
            if admin_users:
                return [user.get('CorreoUsuario', '') for user in admin_users if user.get('CorreoUsuario') and '@' in user.get('CorreoUsuario', '')]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error obteniendo emails de administradores: {e}")
            return []

    def _get_tramitadores_emails(self) -> List[str]:
        """
        Obtiene los correos de los tramitadores de expedientes (administradores de la aplicación)
        Basado en la función getCadenaCorreoTareas() del script original TareaExpedientes.vbs
        """
        try:
            db_tareas = self._get_tareas_connection()
            
            # SQL específico para obtener administradores de la aplicación de expedientes
            query = """
                SELECT TbUsuariosAplicaciones.CorreoUsuario 
                FROM TbUsuariosAplicaciones 
                INNER JOIN TbUsuariosAplicacionesPermisos 
                ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario 
                WHERE IDAplicacion = ? 
                AND EsUsuarioAdministrador = 'Sí'
            """
            
            # Usar el ID de aplicación desde config
            app_id = self.config.app_id_expedientes
            self.logger.debug(f"Consultando administradores para IDAplicacion={app_id}")
            
            results = db_tareas.execute_query(query, (app_id,))
            
            if results:
                emails = [row.get('CorreoUsuario', '') for row in results 
                         if row.get('CorreoUsuario') and '@' in row.get('CorreoUsuario', '')]
                self.logger.info(f"Obtenidos {len(emails)} correos de tramitadores de expedientes: {emails}")
                return emails
            else:
                self.logger.warning("No se encontraron tramitadores de expedientes")
                return []
                
        except Exception as e:
            self.logger.error(f"Error obteniendo emails de tramitadores: {e}")
            return []

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
            self.logger.error(f"Error guardando HTML debug: {e}")

    def generate_email_body(self) -> str:
        """Genera el cuerpo del correo HTML con todas las secciones usando el estilo moderno"""
        try:
            # Obtener datos
            expedientes_tsol = self.get_expedientes_tsol_sin_cod_s4h()
            expedientes_finalizar = self.get_expedientes_a_punto_finalizar()
            hitos_finalizar = self.get_hitos_a_punto_finalizar()
            expedientes_desconocido = self.get_expedientes_estado_desconocido()
            expedientes_sin_contrato = self.get_expedientes_adjudicados_sin_contrato()
            expedientes_oferta_tiempo = self.get_expedientes_fase_oferta_mucho_tiempo()
            
            # Generar tablas HTML modernas
            tablas_html = []
            
            if expedientes_tsol:
                tabla_tsol = self._generate_modern_tsol_table_html(expedientes_tsol)
                tablas_html.append(tabla_tsol)
                self.logger.info(f"Generada tabla TSOL con {len(expedientes_tsol)} registros")
            
            if expedientes_finalizar:
                tabla_finalizar = self._generate_modern_finalizar_table_html(expedientes_finalizar)
                tablas_html.append(tabla_finalizar)
                self.logger.info(f"Generada tabla Finalizar con {len(expedientes_finalizar)} registros")
            
            if hitos_finalizar:
                tabla_hitos = self._generate_modern_hitos_table_html(hitos_finalizar)
                tablas_html.append(tabla_hitos)
                self.logger.info(f"Generada tabla Hitos con {len(hitos_finalizar)} registros")
            
            if expedientes_desconocido:
                tabla_desconocido = self._generate_modern_desconocido_table_html(expedientes_desconocido)
                tablas_html.append(tabla_desconocido)
                self.logger.info(f"Generada tabla Estado Desconocido con {len(expedientes_desconocido)} registros")
            
            if expedientes_sin_contrato:
                tabla_sin_contrato = self._generate_modern_sin_contrato_table_html(expedientes_sin_contrato)
                tablas_html.append(tabla_sin_contrato)
                self.logger.info(f"Generada tabla Sin Contrato con {len(expedientes_sin_contrato)} registros")
            
            if expedientes_oferta_tiempo:
                tabla_oferta = self._generate_modern_oferta_tiempo_table_html(expedientes_oferta_tiempo)
                tablas_html.append(tabla_oferta)
                self.logger.info(f"Generada tabla Oferta Tiempo con {len(expedientes_oferta_tiempo)} registros")
            
            # Si hay al menos una tabla, generar el correo
            if tablas_html:
                header = self._get_modern_html_header()
                footer = self._get_modern_html_footer()
                cuerpo_html = header + "\n".join(tablas_html) + footer
                
                self.logger.info("Correo HTML generado para Expedientes")
                self.logger.info(f"Longitud del HTML generado: {len(cuerpo_html)} caracteres")
                
                # Para debug, guardamos el HTML generado
                self._guardar_html_debug(cuerpo_html, "correo_expedientes.html")
                
                return cuerpo_html
            else:
                self.logger.info("No hay datos para generar correo de Expedientes")
                return ""
            
        except Exception as e:
            self.logger.error(f"Error generando cuerpo del correo: {e}")
            return ""

    def register_email(self, subject: str, body: str, recipients: List[str], bcc_recipients: List[str] = None) -> bool:
        """Registra el correo en la base de datos usando el módulo común"""
        try:
            from ..common.utils import register_email_in_database
            
            db_tareas = self._get_tareas_connection()
            
            recipients_str = ';'.join(recipients) if recipients else ''
            bcc_str = ';'.join(bcc_recipients) if bcc_recipients else ''
            
            return register_email_in_database(
                db_tareas,
                "EXPEDIENTES",
                subject,
                body,
                recipients_str,
                bcc_str
            )
                
        except Exception as e:
            self.logger.error(f"Error registrando correo: {e}")
            return False

    def register_task(self) -> bool:
        """Registra la tarea como completada usando el módulo común"""
        try:
            from ..common.utils import register_task_completion
            
            db_tareas = self._get_tareas_connection()
            
            return register_task_completion(
                db_tareas,
                'ExpedientesDiario',
                self.logger
            )
                
        except Exception as e:
            self.logger.error(f"Error registrando tarea: {e}")
            return False

    def should_execute_task(self) -> bool:
        """
        Determina si debe ejecutarse la tarea de expedientes (diaria, primer día laborable)
        """
        try:
            from src.common.utils import should_execute_weekly_task
            return should_execute_weekly_task(self.db_tareas, "Expedientes", logger=self.logger)
            
        except Exception as e:
            self.logger.error("Error verificando si ejecutar tarea de expedientes: {}".format(e))
            return False

    def run(self) -> bool:
        """
        Método principal para ejecutar la tarea de Expedientes
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            self.logger.info("Ejecutando tarea de Expedientes")
            
            # Verificar si debe ejecutarse
            if not self.debe_ejecutarse():
                self.logger.info("La tarea de Expedientes no debe ejecutarse hoy")
                return True
            
            # Ejecutar la lógica específica
            success = self.ejecutar_logica_especifica()
            
            if success:
                # Marcar como completada
                self.marcar_como_completada()
                self.logger.info("Tarea de Expedientes completada exitosamente")
            
            return success
            
        except Exception as e:
            self.logger.error("Error ejecutando tarea de Expedientes: {}".format(e))
            return False

    def ejecutar_logica_especifica(self) -> bool:
        """
        Ejecuta la lógica específica de la tarea de Expedientes
        
        Returns:
            True si se ejecutó correctamente
        """
        try:
            self.logger.info("Ejecutando lógica específica de Expedientes")
            
            # Obtener correos
            admin_emails = self.get_admin_emails()
            task_emails = self._get_tramitadores_emails()
            
            if not task_emails:
                self.logger.warning("No se encontraron correos de tramitadores")
                return False
            
            # Generar cuerpo del correo
            email_body = self.generate_email_body()
            if not email_body:
                self.logger.info("No hay datos para generar correo de Expedientes")
                return True  # No es un error, simplemente no hay datos
            
            # Registrar correo
            subject = "Informe Tareas De Expedientes (Expedientes)"
            if not self.register_email(subject, email_body, task_emails, admin_emails):
                self.logger.error("No se pudo registrar el correo")
                return False
            
            self.logger.info("Lógica específica de Expedientes ejecutada correctamente")
            return True
            
        except Exception as e:
            self.logger.error("Error en lógica específica de Expedientes: {}".format(e))
            return False

    def execute(self) -> bool:
        """Ejecuta la lógica principal de Expedientes (método de compatibilidad)"""
        return self.run()

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
            self.logger.error(f"Error cerrando conexiones: {e}")


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
    parser = argparse.ArgumentParser(description='Manager de Expedientes')
    parser.add_argument('--debug', action='store_true',
                       help='Activar modo debug')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging si debug está activado
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = None
    try:
        logger = logging.getLogger(__name__)
        logger.info("=== INICIANDO MANAGER EXPEDIENTES ===")
        
        # Crear el manager
        manager = ExpedientesManager()
        
        logger.info("Ejecutando lógica completa...")
        success = manager.ejecutar_logica_especifica()
        if not success:
            logger.error("Error en la ejecución de la lógica específica")
            return 1
        
        logger.info("=== MANAGER EXPEDIENTES COMPLETADO EXITOSAMENTE ===")
        return 0
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error crítico en el manager: {e}")
        return 1
    finally:
        # Cerrar conexiones
        if manager:
            try:
                manager.close_connections()
                logger = logging.getLogger(__name__)
                logger.info("Conexiones cerradas correctamente")
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Error cerrando conexiones: {e}")


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)