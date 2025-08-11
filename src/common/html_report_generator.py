"""Generador de reportes HTML para No Conformidades
Convierte los datos de no conformidades en reportes HTML formateados
"""

import logging
import os
import textwrap
from datetime import datetime

# Clases de datos eliminadas - ya no se necesitan


logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generador de reportes HTML unificado (solo modo moderno)."""

    theme = "modern"

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
            "Días Vencidos": "Dias",
            # Mapeos adicionales para correos técnicos
            "Acción Correctiva": "AccionCorrectiva",
            "Acción Realizada": "AccionRealizada",
            "Nemotécnico": "Nemotecnico",
            "Días para Caducar": "DiasParaCaducar",
            "Días": "DiasParaCaducar",  # Nuevo mapeo para "Días"
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
                cell_value = row.get(field_name, "N/A")

                # Formatear fechas si es necesario
                if isinstance(cell_value, datetime):
                    cell_value = cell_value.strftime("%d/%m/%Y")
                elif cell_value is None:
                    cell_value = "N/A"
                elif header in ["Días para Caducar", "Días"] and isinstance(
                    cell_value, (int, float)
                ):
                    # Formatear días para caducar con colores como en el correo de calidad
                    if cell_value < 0:
                        # Días vencidos - color rojo
                        cell_value = f'<span class="dias-indicador negativo">{cell_value}</span>'
                    elif cell_value == 0:
                        # Vence hoy - color naranja
                        cell_value = '<span class="dias-indicador critico">0</span>'
                    elif cell_value <= 7:
                        # Próximo a vencer - color naranja
                        cell_value = f'<span class="dias-indicador critico">{cell_value}</span>'
                    else:
                        # Normal - color verde
                        cell_value = f'<span class="dias-indicador normal">{cell_value}</span>'

                # Aplicar centrado a ciertas columnas
                if header in [
                    "Código NC",
                    "Nemotécnico",
                    "Fecha Fin Prevista",
                    "Días",
                    "Días para Caducar",
                ]:
                    html += f"    <td class='centrado'>{cell_value}</td>\n"
                else:
                    html += f"    <td>{cell_value}</td>\n"
            html += "  </tr>\n"

        html += "</table>"
        return html

    def get_css_styles(self) -> str:
        """Lee y devuelve los estilos CSS desde el archivo."""
        try:
            css_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "herramientas", "CSS_moderno.css"
            )
            with open(css_path, encoding="utf-8") as f:
                return (
                    f.read()
                )  # Solo devolver el contenido CSS sin las etiquetas <style>
        except Exception as e:
            logger.error(f"Error al leer el archivo CSS: {e}")
            return ""  # Devuelve CSS vacío en caso de error

    # Eliminados header/footer legacy: usar generar_header_moderno / generar_footer_moderno

    # ==== NUEVO BLOQUE: HEADER/FOOTER MODERNO UNIFICADO ====
    def generar_header_moderno(self, titulo: str) -> str:
        """Header alternativo con maquetación moderna (sin indentación inicial)."""
        raw = f"""<!DOCTYPE html>
<html lang=\"es\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>{titulo}</title>
<style>
{self.css_styles}
</style>
</head>
<body>
<div class=\"container\">
<div class=\"header\">
<div class=\"logo\">
<svg width=\"40\" height=\"40\" viewBox=\"0 0 40 40\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n<rect width=\"40\" height=\"40\" rx=\"8\" fill=\"white"/>\n<path d=\"M20 8L32 14V26L20 32L8 26V14L20 8Z\" fill=\"#2563eb"/>\n<circle cx=\"20\" cy=\"20\" r=\"6\" fill=\"white"/>\n</svg>
</div>
<div class=\"header-text\"><h1>{titulo}</h1></div>
</div>
"""
        return textwrap.dedent(raw)

    def generar_footer_moderno(self) -> str:
        """Footer moderno sin indentación inicial."""
        raw = """</div>
<div class=\"footer\">
<p>Este es un mensaje generado por el servicio automatizado del departamento.</p>
<p>Correo desatendido - no responda a este mensaje.</p>
</div>
</body>
</html>
"""
        return textwrap.dedent(raw)

    # ==== NUEVOS HELPERS MODERNOS ====
    def _dias_class(self, dias: int) -> str:
        if dias is None:
            return "normal"
        if dias <= 0:
            return "negativo"
        if dias <= 7:
            return "critico"
        return "normal"

    def _fmt_fecha(self, fecha) -> str:
        from datetime import date
        from datetime import datetime as _dt

        if not fecha:
            return ""
        if isinstance(fecha, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    return _dt.strptime(fecha, fmt).strftime("%d/%m/%Y")
                except ValueError:
                    continue
            return fecha
        if isinstance(fecha, (date, _dt)):
            return fecha.strftime("%d/%m/%Y")
        return str(fecha)

    # ==== TABLAS MODERNAS UNIFICADAS ====
    def tabla_arapc_proximas(self, arapc_data: list[dict]) -> str:
        if not arapc_data:
            return ""
        html = [
            """
        <div class=\"section\">
            <h2>Acciones Correctivas/Preventivas Próximas a Caducar</h2>
            <table class=\"data-table\">
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
                <tbody>"""
        ]
        for r in arapc_data:
            dias = r.get("DiasParaCierre", r.get("Dias", 0))
            html.append(
                f"""
                <tr>
                    <td>{r.get('CodigoNoConformidad','')}</td>
                    <td>{r.get('Nemotecnico','')}</td>
                    <td>{r.get('DESCRIPCION','')}</td>
                    <td>{r.get('RESPONSABLECALIDAD','')}</td>
                    <td>{self._fmt_fecha(r.get('FECHAAPERTURA'))}</td>
                    <td>{self._fmt_fecha(r.get('FPREVCIERRE'))}</td>
                    <td><span class=\"dias-indicador {self._dias_class(dias)}\">{dias}</span></td>
                </tr>"""
            )  # end append row
        html.append(
            """
                </tbody>
            </table>
        </div>"""
        )
        return "".join(html)

    def tabla_nc_pendientes_eficacia(self, eficacia_data: list[dict]) -> str:
        if not eficacia_data:
            return ""
        html = [
            """
        <div class=\"section\">
            <h2>No Conformidades Pendientes de Control de Eficacia</h2>
            <table class=\"data-table\">
                <thead><tr>
                    <th>Código NC</th><th>Nemotécnico</th><th>Descripción</th>
                    <th>Responsable Calidad</th><th>Fecha Cierre</th><th>Fecha Prevista Control</th><th>Días</th>
                </tr></thead><tbody>"""
        ]
        for r in eficacia_data:
            dias = r.get("Dias", 0)
            html.append(
                f"""
                <tr>
                    <td>{r.get('CodigoNoConformidad','')}</td>
                    <td>{r.get('Nemotecnico','')}</td>
                    <td>{r.get('DESCRIPCION','')}</td>
                    <td>{r.get('RESPONSABLECALIDAD','')}</td>
                    <td>{self._fmt_fecha(r.get('FECHACIERRE'))}</td>
                    <td>{self._fmt_fecha(r.get('FechaPrevistaControlEficacia'))}</td>
                    <td><span class=\"dias-indicador {self._dias_class(dias)}\">{dias}</span></td>
                </tr>"""
            )  # end append row
        html.append("""</tbody></table></div>"""
        )
        return "".join(html)

    def tabla_nc_sin_acciones(self, nc_data: list[dict]) -> str:
        if not nc_data:
            return ""
        html = [
            """
        <div class=\"section\">
            <h2>No Conformidades sin Acciones Correctivas</h2>
            <table class=\"data-table"><thead><tr>
                <th>Código NC</th><th>Nemotécnico</th><th>Descripción</th>
                <th>Responsable Calidad</th><th>Fecha Apertura</th><th>Fecha Prevista Cierre</th>
            </tr></thead><tbody>"""
        ]
        for r in nc_data:
            html.append(
                f"""
                <tr>
                    <td>{r.get('CodigoNoConformidad','')}</td>
                    <td>{r.get('Nemotecnico','')}</td>
                    <td>{r.get('DESCRIPCION','')}</td>
                    <td>{r.get('RESPONSABLECALIDAD','')}</td>
                    <td>{self._fmt_fecha(r.get('FECHAAPERTURA'))}</td>
                    <td>{self._fmt_fecha(r.get('FPREVCIERRE'))}</td>
                </tr>"""
            )  # end append row
        html.append("""</tbody></table></div>"""
        )
        return "".join(html)

    def tabla_ars_replanificar(self, replanificar_data: list[dict]) -> str:
        if not replanificar_data:
            return ""
        html = [
            """
        <div class=\"section\">
            <h2>Acciones Realizadas para Replanificar</h2>
            <table class=\"data-table"><thead><tr>
                <th>Código NC</th><th>Nemotécnico</th><th>Acción Correctiva</th>
                <th>Tarea</th><th>Técnico</th><th>Responsable Calidad</th>
                <th>Fecha Fin Prevista</th><th>Días</th>
            </tr></thead><tbody>"""
        ]
        for r in replanificar_data:
            dias = r.get("Dias", 0)
            html.append(
                f"""
                <tr>
                    <td>{r.get('CodigoNoConformidad','')}</td>
                    <td>{r.get('Nemotecnico','')}</td>
                    <td>{r.get('Accion','')}</td>
                    <td>{r.get('Tarea','')}</td>
                    <td>{r.get('Tecnico','')}</td>
                    <td>{r.get('RESPONSABLECALIDAD','')}</td>
                    <td>{self._fmt_fecha(r.get('FechaFinPrevista'))}</td>
                    <td><span class=\"dias-indicador {self._dias_class(dias)}\">{dias}</span></td>
                </tr>"""
            )  # end append row
        html.append("""</tbody></table></div>"""
        )
        return "".join(html)

    def tabla_ar_tecnico(self, ar_data: list[dict], titulo: str) -> str:
        if not ar_data:
            return ""
        # Selección de icono simple según título
        icono = "🔔" if "8-15" in titulo else ("⚠️" if "1-7" in titulo else "🚨")
        html = [
            f"""
        <div class=\"section\">
            <h2>{icono} {titulo}</h2>
            <table class=\"data-table"><thead><tr>
                <th>Código NC</th><th>Nemotécnico</th><th>Acción Correctiva</th>
                <th>Acción Realizada</th><th>Fecha Inicio</th><th>Fecha Fin Prevista</th>
                <th>Responsable</th><th>Días para Caducar</th><th>Correo Calidad</th>
            </tr></thead><tbody>"""
        ]
        for r in ar_data:
            dias = r.get("DiasParaCaducar", 0)
            html.append(
                f"""
                <tr>
                    <td>{r.get('CodigoNoConformidad','')}</td>
                    <td>{r.get('Nemotecnico','')}</td>
                    <td>{r.get('AccionCorrectiva','')}</td>
                    <td>{r.get('AccionRealizada','')}</td>
                    <td>{self._fmt_fecha(r.get('FechaInicio'))}</td>
                    <td>{self._fmt_fecha(r.get('FechaFinPrevista'))}</td>
                    <td>{r.get('Nombre','')}</td>
                    <td><span class=\"dias-indicador {self._dias_class(dias)}\">{dias}</span></td>
                    <td>{r.get('CorreoCalidad','')}</td>
                </tr>"""
            )  # end append row
        html.append("""</tbody></table></div>"""
        )
        return "".join(html)

    # ==== REPORTES COMPUESTOS MODERNOS ====
    def generar_reporte_calidad_moderno(
        self,
        ars_proximas_vencer,
        ncs_pendientes_eficacia,
        ncs_sin_acciones,
        ars_replanificar,
    ) -> str:
        partes = [self.generar_header_moderno("Informe de No Conformidades - Calidad")]
        partes.append(self.tabla_arapc_proximas(ars_proximas_vencer))
        partes.append(self.tabla_nc_pendientes_eficacia(ncs_pendientes_eficacia))
        partes.append(self.tabla_nc_sin_acciones(ncs_sin_acciones))
        partes.append(self.tabla_ars_replanificar(ars_replanificar))
        partes.append(self.generar_footer_moderno())
        return "".join([p for p in partes if p])

    def generar_reporte_tecnico_moderno(self, ars_15, ars_7, ars_vencidas) -> str:
        partes = [
            self.generar_header_moderno("Informe de Acciones Correctivas - Técnicos")
        ]
        partes.append(
            self.tabla_ar_tecnico(
                ars_15, "Acciones Correctivas con fecha fin prevista a 8-15 días"
            )
        )
        partes.append(
            self.tabla_ar_tecnico(
                ars_7, "Acciones Correctivas con fecha fin prevista a 1-7 días"
            )
        )
        partes.append(
            self.tabla_ar_tecnico(ars_vencidas, "Acciones Correctivas vencidas")
        )
        partes.append(self.generar_footer_moderno())
        return "".join([p for p in partes if p])

    def generar_tabla_nc_eficacia(self, ncs: list[dict]) -> str:
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
            fecha_apertura = (
                nc.get("FECHAAPERTURA").strftime("%d/%m/%Y")
                if nc.get("FECHAAPERTURA")
                else ""
            )
            fecha_cierre = (
                nc.get("FPREVCIERRE").strftime("%d/%m/%Y")
                if nc.get("FPREVCIERRE")
                else ""
            )

            html += f"""
                <tr>
                    <td>{nc.get('CodigoNoConformidad', '')}</td>
                    <td>{nc.get('Nemotecnico', '')}</td>
                    <td>{nc.get('DESCRIPCION', '')}</td>
                    <td>{nc.get('RESPONSABLECALIDAD', '')}</td>
                    <td>{fecha_apertura}</td>
                    <td>{fecha_cierre}</td>
                </tr>"""

        html += """
            </tbody>
        </table>
        """

        return html

    def generar_tabla_arapc(self, arapcs: list[dict]) -> str:
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
            fecha_fin_prevista = arapc.get("FechaFinPrevista")
            fecha_fin = (
                fecha_fin_prevista.strftime("%d/%m/%Y") if fecha_fin_prevista else ""
            )

            # Determinar estado y clase CSS
            dias_restantes = (
                (fecha_fin_prevista - datetime.now()).days if fecha_fin_prevista else 0
            )
            if dias_restantes < 0:
                estado = f"VENCIDA ({abs(dias_restantes)} días)"
                clase_css = "Error"
            elif dias_restantes <= 7:
                estado = f"PRÓXIMA A VENCER ({dias_restantes} días)"
                clase_css = "critico"
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
                </tr>"""

        html += """
            </tbody>
        </table>
        """

        return html

    def generar_tabla_nc_caducar(self, ncs: list[dict]) -> str:
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
            fecha_apertura = (
                nc.get("FECHAAPERTURA").strftime("%d/%m/%Y")
                if nc.get("FECHAAPERTURA")
                else ""
            )
            fecha_cierre = (
                nc.get("FPREVCIERRE").strftime("%d/%m/%Y")
                if nc.get("FPREVCIERRE")
                else ""
            )
            dias_para_cierre = nc.get("DiasParaCierre", 0)

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
                </tr>"""

        html += """
            </tbody>
        </table>
        """

        return html

    def generar_tabla_nc_sin_acciones(self, ncs: list[dict]) -> str:
        """Genera tabla HTML para NCs sin acciones definidas"""
        if not ncs:
            return '<p class="info">No hay No Conformidades sin acciones definidas.</p>'

        html = """
        <p class="Cabecera">No Conformidades Registradas Sin Acciones Definidas</p>
        <table class="table">
            <tr class="Alert">
                <td colspan="6">
                    <strong>Atención:</strong> Las siguientes No Conformidades requieren que se
                    definan acciones correctivas/preventivas.
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
            fecha_apertura = (
                nc.get("FechaApertura").strftime("%d/%m/%Y")
                if nc.get("FechaApertura")
                else ""
            )
            fecha_cierre = (
                nc.get("FechaPrevistaCierre").strftime("%d/%m/%Y")
                if nc.get("FechaPrevistaCierre")
                else ""
            )

            html += f"""
                <tr>
                    <td>{nc.get('CodigoNoConformidad', '')}</td>
                    <td>{nc.get('Nemotecnico', '')}</td>
                    <td>{nc.get('DESCRIPCION', '')}</td>
                    <td>{nc.get('RESPONSABLECALIDAD', '')}</td>
                    <td>{fecha_apertura}</td>
                    <td>{fecha_cierre}</td>
                </tr>"""

        html += """
            </tbody>
        </table>
        """

        return html

    def generar_resumen_estadisticas(
        self,
        ncs_eficacia: list[dict],
        arapcs: list[dict],
        ncs_caducar: list[dict],
        ncs_sin_acciones: list[dict],
    ) -> str:
        """Genera un resumen con estadísticas generales"""
        total_ncs_eficacia = len(ncs_eficacia)
        total_arapcs = len(arapcs)
        total_ncs_caducar = len(ncs_caducar)
        total_ncs_sin_acciones = len(ncs_sin_acciones)

        # Contar ARAPs vencidas
        arapcs_vencidas = sum(
            1
            for arapc in arapcs
            if arapc.get("FechaFinPrevista")
            and (arapc.get("FechaFinPrevista") - datetime.now()).days < 0
        )

        # Contar NCs caducadas
        ncs_caducadas = sum(
            1 for nc in ncs_caducar if nc.get("dias_para_cierre", 1) < 0
        )

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

    def generar_reporte_completo(
        self,
        ncs_eficacia: list[dict],
        arapcs: list[dict],
        ncs_caducar: list[dict],
        ncs_sin_acciones: list[dict],
        titulo: str = "Reporte de No Conformidades",
    ) -> str:
        """Genera un reporte usando SOLO el header/footer modernos."""
        html = self.generar_header_moderno(titulo)
        html += self.generar_resumen_estadisticas(
            ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones
        )
        html += self.generar_tabla_nc_sin_acciones(ncs_sin_acciones)
        html += self.generar_tabla_arapc(arapcs)
        html += self.generar_tabla_nc_caducar(ncs_caducar)
        html += self.generar_tabla_nc_eficacia(ncs_eficacia)
        html += self.generar_footer_moderno()
        return html

    # ================= Notificación individual ARAPC =================
    def generar_notificacion_individual_arapc(self, arapc: dict, usuario: dict) -> str:
        """Genera HTML para una notificación individual de ARAPC.

        Args:
            arapc: Datos de la acción correctiva/preventiva.
            usuario: Datos del usuario responsable (correo / nombre).
        """
        correo = usuario.get("correo", "N/A")
        dias_restantes = arapc.get("dias_restantes", 0)
        fecha_prev = arapc.get("FechaFinPrevista")
        if isinstance(fecha_prev, datetime):
            fecha_prev_str = fecha_prev.strftime("%d/%m/%Y")
        else:
            try:
                fecha_prev_str = fecha_prev.strftime("%d/%m/%Y")  # type: ignore
            except Exception:
                fecha_prev_str = str(fecha_prev) if fecha_prev else "N/A"

        if dias_restantes < 0:
            estado = f"VENCIDA ({abs(dias_restantes)} días)"
            clase = "negativo"
        elif dias_restantes <= 7:
            estado = f"PRÓXIMA A VENCER ({dias_restantes} días)"
            clase = "critico"
        else:
            estado = f"{dias_restantes} días restantes"
            clase = "normal"

        # Devolver siempre el HTML, independientemente del estado
        return (
            f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><style>{self.css_styles}</style></head><body>"""
            f"""<h3>Aviso Acción Correctiva/Preventiva</h3>
        <table class='table'>
            <tr><th>Código NC</th><td>{arapc.get('CodigoNoConformidad','N/A')}</td></tr>
            <tr><th>Acción</th><td>{arapc.get('AccionRealizada') or arapc.get('AccionCorrectiva','N/A')}</td></tr>
            <tr><th>Responsable</th><td>{correo}</td></tr>
            <tr><th>Fecha Fin Prevista</th><td>{fecha_prev_str}</td></tr>
            <tr><th>Estado</th><td><span class='dias-indicador {clase}'>{estado}</span></td></tr>
        </table>
        <p>Por favor revise y actualice el estado en el sistema.</p>
        </body></html>"""
        )