"""Generador de reportes HTML (centralizado)."""
import logging
import os
import textwrap
from datetime import datetime, date

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    theme = "modern"

    def __init__(self):
        self.css_styles = self.get_css_styles()

    # ----------------------------------------------------------------------------------
    # Utilidades base
    # ----------------------------------------------------------------------------------
    def generate_table(self, data: list, headers: list) -> str:
        if not data:
            return "<p>No hay datos para mostrar.</p>"
        field_mapping = {
            "Código": "CodigoNoConformidad",
            "Código NC": "CodigoNoConformidad",
            "Descripción": "DESCRIPCION",
            "Nemotecnico": "Nemotecnico",
            "Responsable Calidad": "RESPONSABLECALIDAD",
            "Fecha Cierre": "FECHACIERRE",
            "Fecha Prevista Control Eficacia": "FechaPrevistaControlEficacia",
            "Días Restantes": "Dias",
            "Días": "DiasParaCaducar",
            "Fecha Límite": "FPREVCIERRE",
            "Fecha Registro": "FECHAAPERTURA",
            "Fecha Fin Prevista": "FechaFinPrevista",
            "Nombre": "Nombre",
        }
        rows_html = []
        for row in data:
            dias_value = None
            for key in ("DiasParaCaducar", "Dias", "dias_para_cierre", "DiasParaCierre"):
                if key in row and isinstance(row[key], (int, float)):
                    dias_value = row[key]
                    break
            row_class = ""
            if dias_value is not None:
                if dias_value < 0:
                    row_class = "negativo"
                elif dias_value <= 7:
                    row_class = "critico"
                else:
                    row_class = "normal"
            cells = []
            for header in headers:
                field = field_mapping.get(header, header)
                value = row.get(field, "")
                if isinstance(value, (datetime, date)):
                    value = value.strftime("%Y-%m-%d")
                if header.lower().startswith("días") and value != "":
                    try:
                        dias_num = int(row.get(field, value))
                        value = f"<span class=\"dias-indicador {row_class}\">{dias_num}</span>"
                    except Exception:
                        value = f"<span class=\"dias-indicador\">{value}</span>"
                cells.append(f"<td>{value}</td>")
            rows_html.append("<tr>" + "".join(cells) + "</tr>")
        header_html = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
        return f"<table>{header_html}{''.join(rows_html)}</table>"

    def get_css_styles(self) -> str:
        css_path = os.path.join("herramientas", "CSS_moderno.css")
        if os.path.exists(css_path):
            try:
                with open(css_path, encoding="utf-8") as f:
                    return f"<style>\n{f.read()}\n</style>"
            except Exception:
                pass
        # Fallback mínimo
        return "<style>table{border-collapse:collapse;}th,td{border:1px solid #ddd;padding:8px;}</style>"

    def generar_header_moderno(self, titulo: str) -> str:
        return textwrap.dedent(
            f"""<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\"/><title>{titulo}</title>{self.css_styles}</head><body><h1>{titulo}</h1>"""
        )

    def generar_footer_moderno(self) -> str:
        return "</body></html>"

    # ----------------------------------------------------------------------------------
    # Tablas específicas
    # ----------------------------------------------------------------------------------
    def tabla_arapc_proximas(self, rows: list) -> str:
        if not rows:
            return ""
        return self.generate_table(
            rows,
            [
                "Código NC",
                "Descripción",
                "Responsable Calidad",
                "Fecha Registro",
                "Fecha Límite",
                "Días",
            ],
        )

    def tabla_nc_pendientes_eficacia(self, rows: list) -> str:
        if not rows:
            return "<p>No hay NC pendientes de control de eficacia.</p>"
        return self.generate_table(
            rows,
            [
                "Código NC",
                "Descripción",
                "Responsable Calidad",
                "Fecha Cierre",
                "Fecha Prevista Control Eficacia",
                "Días",
            ],
        )

    def generar_tabla_nc_eficacia(self, rows: list) -> str:
        if not rows:
            return "<p>No hay NC pendientes de control de eficacia.</p>"
        return self.generate_table(
            rows,
            [
                "Código NC",
                "Descripción",
                "Responsable Calidad",
                "Fecha Registro",
                "Fecha Límite",
            ],
        )

    def generar_tabla_arapc(self, rows: list) -> str:
        from datetime import datetime as _dt
        if not rows:
            return "<p>No hay Acciones Correctivas/Preventivas.</p>"
        now = _dt.now()
        partes = [
            "<table><tr><th>Código NC</th><th>Acción</th><th>Responsable</th><th>Fecha Fin Prevista</th><th>Estado</th></tr>"
        ]
        for r in rows:
            ffp = r.get("FechaFinPrevista")
            if isinstance(ffp, (datetime, date)):
                dias = (ffp - now).days
                ffp_str = ffp.strftime("%Y-%m-%d")
            else:
                try:
                    ffp_parsed = _dt.fromisoformat(str(ffp))
                    dias = (ffp_parsed - now).days
                    ffp_str = ffp_parsed.strftime("%Y-%m-%d")
                except Exception:
                    dias = 0
                    ffp_str = str(ffp)
            if dias < 0:
                estado = "VENCIDA"
            elif dias <= 7:
                estado = "PRÓXIMA A VENCER"
            else:
                estado = f"{dias} días restantes"
            partes.append(
                f"<tr><td>{r.get('CodigoNoConformidad','')}</td><td>{r.get('AccionRealizada','')}</td><td>{r.get('Responsable','')}</td><td>{ffp_str}</td><td>{estado}</td></tr>"
            )
        partes.append("</table>")
        return "".join(partes)

    def generar_tabla_nc_caducar(self, rows: list) -> str:
        if not rows:
            return "<p>No hay NC próximas a caducar.</p>"
        partes = ["<table><tr><th>Código NC</th><th>Descripción</th><th>Días</th><th>Estado</th></tr>"]
        for r in rows:
            dias = r.get("dias_para_cierre") or r.get("DiasParaCierre") or r.get("DiasParaCaducar") or r.get("DiasParaCierre", "")
            try:
                dias_int = int(dias)
            except Exception:
                dias_int = 0
            estado = "CADUCADA" if dias_int < 0 else f"{dias_int} días"
            partes.append(
                f"<tr><td>{r.get('CodigoNoConformidad','')}</td><td>{r.get('DESCRIPCION','')}</td><td>{dias_int}</td><td>{estado}</td></tr>"
            )
        partes.append("</table>")
        return "".join(partes)

    def generar_tabla_nc_sin_acciones(self, rows: list) -> str:
        if not rows:
            return "<p>No hay NC sin acciones definidas.</p>"
        return self.generate_table(
            rows,
            [
                "Código NC",
                "Nemotecnico",
                "Descripción",
                "Responsable Calidad",
                "Fecha Registro",
                "Fecha Límite",
            ],
        )

    # ----------------------------------------------------------------------------------
    # Composición de reportes
    # ----------------------------------------------------------------------------------
    def generar_resumen_estadisticas(self, ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones) -> str:
        total_ar = len(arapcs)
        vencidas = sum(
            1
            for r in arapcs
            if (
                r.get("FechaFinPrevista")
                and isinstance(r.get("FechaFinPrevista"), (datetime, date))
                and r["FechaFinPrevista"] < datetime.now()
            )
        )
        caducadas = sum(
            1 for r in ncs_caducar if (r.get("dias_para_cierre") or r.get("DiasParaCaducar", 0)) < 0
        )
        return (
            "<section><h2>Resumen Ejecutivo</h2>"
            f"<p>Acciones Correctivas/Preventivas: {total_ar} (vencidas: {vencidas})</p>"
            f"<p>NC próximas a caducar: {len(ncs_caducar)} (caducadas: {caducadas})</p>"
            f"<p>NC pendientes de control de eficacia: {len(ncs_eficacia)}</p>"
            f"<p>NC sin acciones: {len(ncs_sin_acciones)}</p>"
            "</section>"
        )

    def generar_reporte_completo(self, ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones, titulo: str = "Reporte") -> str:
        partes = [self.generar_header_moderno(titulo)]
        partes.append(
            self.generar_resumen_estadisticas(
                ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones
            )
        )
        partes.append("<h2>Acciones Correctivas/Preventivas Próximas a Vencer</h2>")
        partes.append(self.generar_tabla_arapc(arapcs))
        partes.append("<h2>NC Próximas a Caducar</h2>")
        partes.append(self.generar_tabla_nc_caducar(ncs_caducar))
        partes.append("<h2>NC Pendientes de Control de Eficacia</h2>")
        partes.append(self.generar_tabla_nc_eficacia(ncs_eficacia))
        partes.append("<h2>NC sin Acciones</h2>")
        partes.append(self.generar_tabla_nc_sin_acciones(ncs_sin_acciones))
        partes.append(self.generar_footer_moderno())
        return "".join(partes)

    def generar_reporte_calidad_moderno(self, ars_proximas, ncs_pendientes_eficacia, ncs_sin_acciones, ars_replanificar) -> str:
        titulo = "Informe de No Conformidades - Calidad"
        partes = [self.generar_header_moderno(titulo)]
        if ars_proximas:
            partes.append("<h2>AR/APC Próximas a Vencer</h2>")
            partes.append(self.tabla_arapc_proximas(ars_proximas))
        if ncs_pendientes_eficacia:
            partes.append("<h2>No Conformidades Pendientes de Control de Eficacia</h2>")
            partes.append(self.tabla_nc_pendientes_eficacia(ncs_pendientes_eficacia))
        if ncs_sin_acciones:
            partes.append("<h2>NC sin Acciones</h2>")
            partes.append(self.generar_tabla_nc_sin_acciones(ncs_sin_acciones))
        if ars_replanificar:
            partes.append("<h2>AR/APC para Replanificar</h2>")
            partes.append(
                self.generate_table(
                    ars_replanificar, ["Código NC", "Descripción", "Responsable Calidad"]
                )
            )
        partes.append(self.generar_footer_moderno())
        return "".join(partes)

    def generar_reporte_tecnico_moderno(self, ars_15, ars_7, ars_vencidas) -> str:
        titulo = "Informe de Acciones Correctivas - Técnicos"
        partes = [self.generar_header_moderno(titulo)]
        columnas = [
            "Código NC",
            "Descripción",
            "Fecha Fin Prevista",
            "Responsable Calidad",
            "Días",
            "Nombre",
        ]
        if ars_15:
            partes.append("<h2>Acciones Correctivas con fecha fin prevista a 8-15 días</h2>")
            partes.append(self.generate_table(ars_15, columnas))
        if ars_7:
            partes.append("<h2>Acciones Correctivas con fecha fin prevista a 1-7 días</h2>")
            partes.append(self.generate_table(ars_7, columnas))
        if ars_vencidas:
            partes.append("<h2>Acciones Correctivas Vencidas</h2>")
            partes.append(self.generate_table(ars_vencidas, columnas))
        partes.append(self.generar_footer_moderno())
        return "".join(partes)

    # ----------------------------------------------------------------------------------
    # Notificaciones individuales
    # ----------------------------------------------------------------------------------
    def generar_notificacion_individual_arapc(self, arapc: dict, user: dict) -> str:
        titulo = f"Aviso AR/APC {arapc.get('CodigoNoConformidad','')}"
        partes = [self.generar_header_moderno(titulo)]
        partes.append(
            f"<p>Código: {arapc.get('CodigoNoConformidad','')}<br>Acción: {arapc.get('AccionRealizada','')}<br>Destinatario: {user.get('correo','')}</p>"
        )
        partes.append(self.generar_footer_moderno())
        return "".join(partes)
