"""
Generador de reportes HTML para No Conformidades
Convierte los datos de no conformidades en reportes HTML formateados
"""

import os
import logging
from datetime import datetime
from typing import List, Dict
from no_conformidades.no_conformidades_manager import NoConformidad, ARAPC, Usuario


logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generador de reportes HTML para No Conformidades"""
    
    def __init__(self):
        self.css_styles = self.get_css_styles()
    
    def generate_table(self, data: list, headers: list) -> str:
        """Genera una tabla HTML a partir de una lista de diccionarios y una lista de cabeceras."""
        if not data:
            return "<p>No hay datos para mostrar.</p>"

        # Mapeo de headers a campos de la base de datos
        field_mapping = {
            "Código": "CodigoNoConformidad",
            "Descripción": "DESCRIPCION", 
            "Responsable Calidad": "RESPONSABLECALIDAD",
            "Fecha Cierre": "FECHACIERRE",
            "Fecha Prevista Control Eficacia": "FechaPrevistaControlEficacia",
            "Días Restantes": "Dias",
            "Fecha Límite": "FPREVCIERRE",
            "Fecha Registro": "FECHAAPERTURA",
            "Código NC": "CodigoNoConformidad",
            "Fecha Fin Prevista": "FechaFinPrevista",
            "Días Vencidos": "Dias"
        }

        html = "<table class='table'>\n"
        html += "  <tr>\n"
        for header in headers:
            html += f"    <th class='Cabecera'>{header}</th>\n"
        html += "  </tr>\n"

        for row in data:
            html += "  <tr>\n"
            for header in headers:
                # Usar el mapeo para obtener el campo correcto
                field_name = field_mapping.get(header, header)
                cell_value = row.get(field_name, 'N/A')
                
                # Formatear fechas si es necesario
                if isinstance(cell_value, datetime):
                    cell_value = cell_value.strftime('%d/%m/%Y')
                elif cell_value is None:
                    cell_value = 'N/A'
                    
                html += f"    <td>{cell_value}</td>\n"
            html += "  </tr>\n"

        html += "</table>"
        return html

    def get_css_styles(self) -> str:
        """Lee y devuelve los estilos CSS desde el archivo."""
        try:
            css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'herramientas', 'CSS.txt')
            with open(css_path, 'r', encoding='utf-8') as f:
                return f.read()  # Solo devolver el contenido CSS sin las etiquetas <style>
        except Exception as e:
            logger.error(f"Error al leer el archivo CSS: {e}")
            return ""  # Devuelve CSS vacío en caso de error
    
    def generar_header_html(self, titulo: str) -> str:
        """Genera el header HTML del reporte"""
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        {self.css_styles}
    </style>
</head>
<body>
    <table border="0" width="100%">
        <tr>
            <td width="50%" class="Cabecera">{titulo}</td>
            <td width="50%" align="right" class="Cabecera">Fecha: {fecha_actual}</td>
        </tr>
    </table>
    <hr>
"""
    
    def generar_footer_html(self) -> str:
        """Genera el footer HTML del reporte"""
        return """
            <div class="footer">
                <p>Sistema de Gestión de No Conformidades - Generado automáticamente</p>
            </div>
        </body>
        </html>
        """
    
    def generar_tabla_nc_eficacia(self, ncs: List[Dict]) -> str:
        """Genera tabla HTML para NCs pendientes de control de eficacia"""
        if not ncs:
            return '<p class="info">No hay No Conformidades pendientes de control de eficacia.</p>'
        
        html = """
        <p class="Cabecera">No Conformidades Resueltas Pendientes de Control de Eficacia</p>
        <table class="table">
            <thead>
                <tr class="Cabecera">
                    <th>Código NC</th>
                    <th>Nemotécnico</th>
                    <th>Descripción</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Apertura</th>
                    <th>Fecha Prev. Cierre</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for nc in ncs:
            fecha_apertura = nc.get('FECHAAPERTURA').strftime("%d/%m/%Y") if nc.get('FECHAAPERTURA') else ""
            fecha_cierre = nc.get('FPREVCIERRE').strftime("%d/%m/%Y") if nc.get('FPREVCIERRE') else ""
            
            html += f"""
                <tr>
                    <td>{nc.get('CodigoNoConformidad', '')}</td>
                    <td>{nc.get('Nemotecnico', '')}</td>
                    <td>{nc.get('DESCRIPCION', '')}</td>
                    <td>{nc.get('RESPONSABLECALIDAD', '')}</td>
                    <td>{fecha_apertura}</td>
                    <td>{fecha_cierre}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generar_tabla_arapc(self, arapcs: List[Dict]) -> str:
        """Genera tabla HTML para ARAPs próximas a vencer"""
        if not arapcs:
            return '<p class="info">No hay Acciones Correctivas/Preventivas próximas a vencer.</p>'
        
        html = """
        <p class="Cabecera">Acciones Correctivas/Preventivas Próximas a Vencer</p>
        <table class="table">
            <thead>
                <tr class="Cabecera">
                    <th>ID Acción</th>
                    <th>Código NC</th>
                    <th>Descripción</th>
                    <th>Responsable</th>
                    <th>Fecha Fin Prevista</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for arapc in arapcs:
            fecha_fin_prevista = arapc.get('FechaFinPrevista')
            fecha_fin = fecha_fin_prevista.strftime("%d/%m/%Y") if fecha_fin_prevista else ""
            
            # Determinar estado y clase CSS
            dias_restantes = (fecha_fin_prevista - datetime.now()).days if fecha_fin_prevista else 0
            if dias_restantes < 0:
                estado = f"VENCIDA ({abs(dias_restantes)} días)"
                clase_css = "Error"
            elif dias_restantes <= 7:
                estado = f"PRÓXIMA A VENCER ({dias_restantes} días)"
                clase_css = "Alert"
            else:
                estado = f"{dias_restantes} días restantes"
                clase_css = ""
            
            html += f"""
                <tr class="{clase_css}">
                    <td>{arapc.get('IDAccionRealizada', '')}</td>
                    <td>{arapc.get('CodigoNoConformidad', '')}</td>
                    <td>{arapc.get('AccionRealizada', '')}</td>
                    <td>{arapc.get('Responsable', '')}</td>
                    <td>{fecha_fin}</td>
                    <td>{estado}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generar_tabla_nc_caducar(self, ncs: List[Dict]) -> str:
        """Genera tabla HTML para NCs próximas a caducar"""
        if not ncs:
            return '<p class="info">No hay No Conformidades próximas a caducar.</p>'
        
        html = """
        <p class="Cabecera">No Conformidades Próximas a Caducar</p>
        <table class="table">
            <thead>
                <tr class="Cabecera">
                    <th>Código NC</th>
                    <th>Nemotécnico</th>
                    <th>Descripción</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Apertura</th>
                    <th>Fecha Prev. Cierre</th>
                    <th>Días para Cierre</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for nc in ncs:
            fecha_apertura = nc.get('FECHAAPERTURA').strftime("%d/%m/%Y") if nc.get('FECHAAPERTURA') else ""
            fecha_cierre = nc.get('FPREVCIERRE').strftime("%d/%m/%Y") if nc.get('FPREVCIERRE') else ""
            dias_para_cierre = nc.get('DiasParaCierre', 0)
            
            # Determinar clase CSS según días restantes
            if dias_para_cierre < 0:
                clase_css = "Error"
                estado_dias = f"CADUCADA ({abs(dias_para_cierre)} días)"
            elif dias_para_cierre <= 7:
                clase_css = "Alert"
                estado_dias = f"{dias_para_cierre} días"
            else:
                clase_css = ""
                estado_dias = f"{dias_para_cierre} días"
            
            html += f"""
                <tr class="{clase_css}">
                    <td>{nc.get('CodigoNoConformidad', '')}</td>
                    <td>{nc.get('Nemotecnico', '')}</td>
                    <td>{nc.get('DESCRIPCION', '')}</td>
                    <td>{nc.get('RESPONSABLECALIDAD', '')}</td>
                    <td>{fecha_apertura}</td>
                    <td>{fecha_cierre}</td>
                    <td>{estado_dias}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generar_tabla_nc_sin_acciones(self, ncs: List[NoConformidad]) -> str:
        """Genera tabla HTML para NCs sin acciones definidas"""
        if not ncs:
            return '<p class="info">No hay No Conformidades sin acciones definidas.</p>'
        
        html = """
        <p class="Cabecera">No Conformidades Registradas Sin Acciones Definidas</p>
        <table class="table">
            <tr class="Alert">
                <td colspan="6">
                    <strong>Atención:</strong> Las siguientes No Conformidades requieren que se definan acciones correctivas/preventivas.
                </td>
            </tr>
            <thead>
                <tr class="Cabecera">
                    <th>Código NC</th>
                    <th>Nemotécnico</th>
                    <th>Descripción</th>
                    <th>Responsable Calidad</th>
                    <th>Fecha Apertura</th>
                    <th>Fecha Prev. Cierre</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for nc in ncs:
            fecha_apertura = nc.get('FechaApertura').strftime("%d/%m/%Y") if nc.get('FechaApertura') else ""
            fecha_cierre = nc.get('FechaPrevistaCierre').strftime("%d/%m/%Y") if nc.get('FechaPrevistaCierre') else ""
            
            html += f"""
                <tr>
                    <td>{nc.get('CodigoNoConformidad', '')}</td>
                    <td>{nc.get('Nemotecnico', '')}</td>
                    <td>{nc.get('DESCRIPCION', '')}</td>
                    <td>{nc.get('RESPONSABLECALIDAD', '')}</td>
                    <td>{fecha_apertura}</td>
                    <td>{fecha_cierre}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generar_resumen_estadisticas(self, ncs_eficacia: List[NoConformidad], 
                                   arapcs: List[ARAPC], 
                                   ncs_caducar: List[NoConformidad],
                                   ncs_sin_acciones: List[NoConformidad]) -> str:
        """Genera un resumen con estadísticas generales"""
        total_ncs_eficacia = len(ncs_eficacia)
        total_arapcs = len(arapcs)
        total_ncs_caducar = len(ncs_caducar)
        total_ncs_sin_acciones = len(ncs_sin_acciones)
        
        # Contar ARAPs vencidas
        arapcs_vencidas = sum(1 for arapc in arapcs 
                             if arapc.get('FechaFinPrevista') and 
                             (arapc.get('FechaFinPrevista') - datetime.now()).days < 0)
        
        # Contar NCs caducadas
        ncs_caducadas = sum(1 for nc in ncs_caducar if nc.get('dias_para_cierre', 1) < 0)
        
        html = f"""
        <p class="Cabecera">Resumen Ejecutivo</p>
        <table class="table">
            <thead>
                <tr class="Cabecera">
                    <th>Categoría</th>
                    <th>Total</th>
                    <th>Críticos</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>NCs Pendientes Control Eficacia</td>
                    <td>{total_ncs_eficacia}</td>
                    <td>-</td>
                    <td class="{'Alert' if total_ncs_eficacia > 0 else ''}">{'Requiere Atención' if total_ncs_eficacia > 0 else 'OK'}</td>
                </tr>
                <tr>
                    <td>Acciones Correctivas/Preventivas</td>
                    <td>{total_arapcs}</td>
                    <td>{arapcs_vencidas} vencidas</td>
                    <td class="{'Error' if arapcs_vencidas > 0 else 'Alert' if total_arapcs > 0 else ''}">{'Crítico' if arapcs_vencidas > 0 else 'Requiere Seguimiento' if total_arapcs > 0 else 'OK'}</td>
                </tr>
                <tr>
                    <td>NCs Próximas a Caducar</td>
                    <td>{total_ncs_caducar}</td>
                    <td>{ncs_caducadas} caducadas</td>
                    <td class="{'Error' if ncs_caducadas > 0 else 'Alert' if total_ncs_caducar > 0 else ''}">{'Crítico' if ncs_caducadas > 0 else 'Requiere Seguimiento' if total_ncs_caducar > 0 else 'OK'}</td>
                </tr>
                <tr>
                    <td>NCs Sin Acciones Definidas</td>
                    <td>{total_ncs_sin_acciones}</td>
                    <td>-</td>
                    <td class="{'Alert' if total_ncs_sin_acciones > 0 else ''}">{'Requiere Definición' if total_ncs_sin_acciones > 0 else 'OK'}</td>
                </tr>
            </tbody>
        </table>
        """
        
        return html
    
    def generar_reporte_completo(self, ncs_eficacia: List[NoConformidad], 
                               arapcs: List[ARAPC], 
                               ncs_caducar: List[NoConformidad],
                               ncs_sin_acciones: List[NoConformidad],
                               titulo: str = "Reporte de No Conformidades") -> str:
        """Genera un reporte HTML completo"""
        
        html = self.generar_header_html(titulo)
        html += self.generar_resumen_estadisticas(ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones)
        html += self.generar_tabla_nc_sin_acciones(ncs_sin_acciones)
        html += self.generar_tabla_arapc(arapcs)
        html += self.generar_tabla_nc_caducar(ncs_caducar)
        html += self.generar_tabla_nc_eficacia(ncs_eficacia)
        html += self.generar_footer_html()
        
        return html