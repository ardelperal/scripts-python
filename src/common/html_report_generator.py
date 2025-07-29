"""
Generador de reportes HTML para No Conformidades
Convierte los datos de no conformidades en reportes HTML formateados
"""

from datetime import datetime
from typing import List, Dict
from no_conformidades.no_conformidades_manager import NoConformidad, ARAPC, Usuario


class HTMLReportGenerator:
    """Generador de reportes HTML para No Conformidades"""
    
    def __init__(self):
        self.css_styles = self._get_css_styles()
    
    def _get_css_styles(self) -> str:
        """Obtiene los estilos CSS para los reportes"""
        return """
        <style type="text/css">
        body { font-family: Arial, sans-serif; font-size: 12px; margin: 10px; }
        .header { background-color: #4472C4; color: white; padding: 10px; text-align: center; font-weight: bold; }
        .section-title { background-color: #D9E1F2; padding: 8px; font-weight: bold; margin-top: 15px; }
        .table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        .table th { background-color: #4472C4; color: white; padding: 8px; text-align: left; border: 1px solid #ccc; }
        .table td { padding: 6px; border: 1px solid #ccc; }
        .table tr:nth-child(even) { background-color: #f9f9f9; }
        .alert { background-color: #FFE6E6; border-left: 4px solid #FF0000; padding: 10px; margin: 10px 0; }
        .warning { background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 10px; margin: 10px 0; }
        .info { background-color: #D1ECF1; border-left: 4px solid #17A2B8; padding: 10px; margin: 10px 0; }
        .footer { margin-top: 20px; font-size: 10px; color: #666; text-align: center; }
        .overdue { background-color: #FFCDD2; }
        .near-due { background-color: #FFF9C4; }
        </style>
        """
    
    def generar_header_html(self, titulo: str) -> str:
        """Genera el header HTML del reporte"""
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{titulo}</title>
            {self.css_styles}
        </head>
        <body>
            <div class="header">
                <h1>{titulo}</h1>
                <p>Generado el: {fecha_actual}</p>
            </div>
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
    
    def generar_tabla_nc_eficacia(self, ncs: List[NoConformidad]) -> str:
        """Genera tabla HTML para NCs pendientes de control de eficacia"""
        if not ncs:
            return '<div class="info">No hay No Conformidades pendientes de control de eficacia.</div>'
        
        html = """
        <div class="section-title">No Conformidades Resueltas Pendientes de Control de Eficacia</div>
        <table class="table">
            <thead>
                <tr>
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
            fecha_apertura = nc.fecha_apertura.strftime("%d/%m/%Y") if nc.fecha_apertura else ""
            fecha_cierre = nc.fecha_prev_cierre.strftime("%d/%m/%Y") if nc.fecha_prev_cierre else ""
            
            html += f"""
                <tr>
                    <td>{nc.codigo}</td>
                    <td>{nc.nemotecnico}</td>
                    <td>{nc.descripcion}</td>
                    <td>{nc.responsable_calidad}</td>
                    <td>{fecha_apertura}</td>
                    <td>{fecha_cierre}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generar_tabla_arapc(self, arapcs: List[ARAPC]) -> str:
        """Genera tabla HTML para ARAPs próximas a vencer"""
        if not arapcs:
            return '<div class="info">No hay Acciones Correctivas/Preventivas próximas a vencer.</div>'
        
        html = """
        <div class="section-title">Acciones Correctivas/Preventivas Próximas a Vencer</div>
        <table class="table">
            <thead>
                <tr>
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
            fecha_fin = arapc.fecha_fin_prevista.strftime("%d/%m/%Y") if arapc.fecha_fin_prevista else ""
            
            # Determinar estado y clase CSS
            dias_restantes = (arapc.fecha_fin_prevista - datetime.now()).days if arapc.fecha_fin_prevista else 0
            if dias_restantes < 0:
                estado = f"VENCIDA ({abs(dias_restantes)} días)"
                clase_css = "overdue"
            elif dias_restantes <= 7:
                estado = f"PRÓXIMA A VENCER ({dias_restantes} días)"
                clase_css = "near-due"
            else:
                estado = f"{dias_restantes} días restantes"
                clase_css = ""
            
            html += f"""
                <tr class="{clase_css}">
                    <td>{arapc.id_accion}</td>
                    <td>{arapc.codigo_nc}</td>
                    <td>{arapc.descripcion}</td>
                    <td>{arapc.responsable}</td>
                    <td>{fecha_fin}</td>
                    <td>{estado}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generar_tabla_nc_caducar(self, ncs: List[NoConformidad]) -> str:
        """Genera tabla HTML para NCs próximas a caducar"""
        if not ncs:
            return '<div class="info">No hay No Conformidades próximas a caducar.</div>'
        
        html = """
        <div class="section-title">No Conformidades Próximas a Caducar</div>
        <table class="table">
            <thead>
                <tr>
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
            fecha_apertura = nc.fecha_apertura.strftime("%d/%m/%Y") if nc.fecha_apertura else ""
            fecha_cierre = nc.fecha_prev_cierre.strftime("%d/%m/%Y") if nc.fecha_prev_cierre else ""
            
            # Determinar clase CSS según días restantes
            if nc.dias_para_cierre < 0:
                clase_css = "overdue"
                estado_dias = f"CADUCADA ({abs(nc.dias_para_cierre)} días)"
            elif nc.dias_para_cierre <= 7:
                clase_css = "near-due"
                estado_dias = f"{nc.dias_para_cierre} días"
            else:
                clase_css = ""
                estado_dias = f"{nc.dias_para_cierre} días"
            
            html += f"""
                <tr class="{clase_css}">
                    <td>{nc.codigo}</td>
                    <td>{nc.nemotecnico}</td>
                    <td>{nc.descripcion}</td>
                    <td>{nc.responsable_calidad}</td>
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
            return '<div class="info">No hay No Conformidades sin acciones definidas.</div>'
        
        html = """
        <div class="section-title">No Conformidades Registradas Sin Acciones Definidas</div>
        <div class="alert">
            <strong>Atención:</strong> Las siguientes No Conformidades requieren que se definan acciones correctivas/preventivas.
        </div>
        <table class="table">
            <thead>
                <tr>
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
            fecha_apertura = nc.fecha_apertura.strftime("%d/%m/%Y") if nc.fecha_apertura else ""
            fecha_cierre = nc.fecha_prev_cierre.strftime("%d/%m/%Y") if nc.fecha_prev_cierre else ""
            
            html += f"""
                <tr>
                    <td>{nc.codigo}</td>
                    <td>{nc.nemotecnico}</td>
                    <td>{nc.descripcion}</td>
                    <td>{nc.responsable_calidad}</td>
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
                             if arapc.fecha_fin_prevista and 
                             (arapc.fecha_fin_prevista - datetime.now()).days < 0)
        
        # Contar NCs caducadas
        ncs_caducadas = sum(1 for nc in ncs_caducar if nc.dias_para_cierre < 0)
        
        html = f"""
        <div class="section-title">Resumen Ejecutivo</div>
        <table class="table">
            <thead>
                <tr>
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
                    <td>{'⚠️ Requiere Atención' if total_ncs_eficacia > 0 else '✅ OK'}</td>
                </tr>
                <tr>
                    <td>Acciones Correctivas/Preventivas</td>
                    <td>{total_arapcs}</td>
                    <td>{arapcs_vencidas} vencidas</td>
                    <td>{'🔴 Crítico' if arapcs_vencidas > 0 else '⚠️ Requiere Seguimiento' if total_arapcs > 0 else '✅ OK'}</td>
                </tr>
                <tr>
                    <td>NCs Próximas a Caducar</td>
                    <td>{total_ncs_caducar}</td>
                    <td>{ncs_caducadas} caducadas</td>
                    <td>{'🔴 Crítico' if ncs_caducadas > 0 else '⚠️ Requiere Seguimiento' if total_ncs_caducar > 0 else '✅ OK'}</td>
                </tr>
                <tr>
                    <td>NCs Sin Acciones Definidas</td>
                    <td>{total_ncs_sin_acciones}</td>
                    <td>-</td>
                    <td>{'⚠️ Requiere Definición' if total_ncs_sin_acciones > 0 else '✅ OK'}</td>
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
        html += self.generar_tabla_nc_eficacia(ncs_eficacia)
        html += self.generar_tabla_arapc(arapcs)
        html += self.generar_tabla_nc_caducar(ncs_caducar)
        html += self.generar_tabla_nc_sin_acciones(ncs_sin_acciones)
        html += self.generar_footer_html()
        
        return html