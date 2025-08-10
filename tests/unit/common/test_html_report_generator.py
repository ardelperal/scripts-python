import datetime
import pytest
from src.common.html_report_generator import HTMLReportGenerator


def test_header_footer_basic():
    gen = HTMLReportGenerator()
    head = gen.generar_header_moderno("Titulo X")
    foot = gen.generar_footer_moderno()
    assert "<!DOCTYPE html>" in head
    assert "Titulo X" in head
    assert foot.strip().endswith("</html>")


def test_tabla_arapc_proximas_empty():
    gen = HTMLReportGenerator()
    assert gen.tabla_arapc_proximas([]) == ""


def test_tabla_arapc_proximas_rows():
    gen = HTMLReportGenerator()
    rows = [{
        'CodigoNoConformidad': 'NC1',
        'Nemotecnico': 'N1',
        'DESCRIPCION': 'Desc',
        'RESPONSABLECALIDAD': 'Resp',
        'FECHAAPERTURA': datetime.date(2025,1,1),
        'FPREVCIERRE': datetime.date(2025,2,1),
        'Dias': 5
    }]
    html = gen.tabla_arapc_proximas(rows)
    assert 'NC1' in html and 'Desc' in html and 'Resp' in html


def test_tabla_nc_pendientes_eficacia_color_classes():
    gen = HTMLReportGenerator()
    rows = [
        {'CodigoNoConformidad':'A','Nemotecnico':'NA','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHACIERRE': datetime.date(2025,1,1),'FechaPrevistaControlEficacia': datetime.date(2025,2,1),'Dias': -1},
        {'CodigoNoConformidad':'B','Nemotecnico':'NB','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHACIERRE': datetime.date(2025,1,1),'FechaPrevistaControlEficacia': datetime.date(2025,2,1),'Dias': 0},
        {'CodigoNoConformidad':'C','Nemotecnico':'NC','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHACIERRE': datetime.date(2025,1,1),'FechaPrevistaControlEficacia': datetime.date(2025,2,1),'Dias': 3},
        {'CodigoNoConformidad':'D','Nemotecnico':'ND','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHACIERRE': datetime.date(2025,1,1),'FechaPrevistaControlEficacia': datetime.date(2025,2,1),'Dias': 10},
    ]
    html = gen.tabla_nc_pendientes_eficacia(rows)
    # Verifica que las cuatro filas estén representadas
    assert html.count('<tr>') >= 4


def test_generar_reporte_tecnico_moderno_partial():
    gen = HTMLReportGenerator()
    # Solo una sección con datos para asegurar composición condicional
    ars_15 = [{'CodigoNoConformidad':'X','Nemotecnico':'NX','AccionCorrectiva':'AC','AccionRealizada':'AR','FechaInicio': datetime.date(2025,1,1),'FechaFinPrevista': datetime.date(2025,1,10),'Nombre':'Tec','DiasParaCaducar':4,'CorreoCalidad':'c@x'}]
    html = gen.generar_reporte_tecnico_moderno(ars_15, [], [])
    assert 'Acciones Correctivas con fecha fin prevista a 8-15 días' in html
    assert 'Acciones Correctivas con fecha fin prevista a 1-7 días' not in html or html.count('<table') == 2  # header + 1 tabla


def test_generar_notificacion_individual_arapc():
    gen = HTMLReportGenerator()
    arapc = {'CodigoNoConformidad':'NC9','AccionRealizada':'Revisar','dias_restantes':2,'FechaFinPrevista': datetime.datetime(2025,1,15)}
    user = {'correo':'user@x'}
    html = gen.generar_notificacion_individual_arapc(arapc, user)
    assert 'NC9' in html and 'Revisar' in html and 'user@x' in html


# ==== NUEVAS PRUEBAS AMPLIACIÓN COBERTURA ====
def test_generar_tabla_nc_eficacia_empty():
    gen = HTMLReportGenerator()
    html = gen.generar_tabla_nc_eficacia([])
    assert 'pendientes de control de eficacia' in html.lower()


def test_generar_tabla_nc_eficacia_rows():
    gen = HTMLReportGenerator()
    rows = [{
        'CodigoNoConformidad': 'NC10',
        'Nemotecnico': 'NM',
        'DESCRIPCION': 'Desc',
        'RESPONSABLECALIDAD': 'Resp',
        'FECHAAPERTURA': datetime.datetime(2025,1,1),
        'FPREVCIERRE': datetime.datetime(2025,1,20)
    }]
    html = gen.generar_tabla_nc_eficacia(rows)
    assert 'NC10' in html and 'Desc' in html


def test_generar_tabla_arapc_states():
    gen = HTMLReportGenerator()
    now = datetime.datetime.now()
    rows = [
        {'IDAccionRealizada':1,'CodigoNoConformidad':'NC1','AccionRealizada':'A1','Responsable':'R1','FechaFinPrevista': now - datetime.timedelta(days=2)},  # vencida
        {'IDAccionRealizada':2,'CodigoNoConformidad':'NC2','AccionRealizada':'A2','Responsable':'R2','FechaFinPrevista': now + datetime.timedelta(days=3)},  # <=7
        {'IDAccionRealizada':3,'CodigoNoConformidad':'NC3','AccionRealizada':'A3','Responsable':'R3','FechaFinPrevista': now + datetime.timedelta(days=15)}, # >7
    ]
    html = gen.generar_tabla_arapc(rows)
    # Frases clave por estados
    assert 'VENCIDA' in html and 'PRÓXIMA A VENCER' in html and 'restantes' in html


def test_generar_tabla_nc_caducar_varios():
    gen = HTMLReportGenerator()
    rows = [
        {'CodigoNoConformidad':'A','Nemotecnico':'NA','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHAAPERTURA': datetime.datetime(2025,1,1), 'FPREVCIERRE': datetime.datetime(2025,1,10), 'DiasParaCierre': -3, 'dias_para_cierre': -3},
        {'CodigoNoConformidad':'B','Nemotecnico':'NB','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHAAPERTURA': datetime.datetime(2025,1,1), 'FPREVCIERRE': datetime.datetime(2025,1,10), 'DiasParaCierre': 0, 'dias_para_cierre': 0},
        {'CodigoNoConformidad':'C','Nemotecnico':'NC','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHAAPERTURA': datetime.datetime(2025,1,1), 'FPREVCIERRE': datetime.datetime(2025,1,20), 'DiasParaCierre': 5, 'dias_para_cierre': 5},
        {'CodigoNoConformidad':'D','Nemotecnico':'ND','DESCRIPCION':'D','RESPONSABLECALIDAD':'R','FECHAAPERTURA': datetime.datetime(2025,1,1), 'FPREVCIERRE': datetime.datetime(2025,2,1), 'DiasParaCierre': 12, 'dias_para_cierre': 12},
    ]
    html = gen.generar_tabla_nc_caducar(rows)
    assert 'CADUCADA' in html and '12 días' in html


def test_generar_tabla_nc_sin_acciones_empty_y_rows():
    gen = HTMLReportGenerator()
    assert 'sin acciones definidas' in gen.generar_tabla_nc_sin_acciones([]).lower()
    rows = [{
        'CodigoNoConformidad':'X','Nemotecnico':'NX','DESCRIPCION':'Desc','RESPONSABLECALIDAD':'Resp',
        'FechaApertura': datetime.datetime(2025,1,1), 'FechaPrevistaCierre': datetime.datetime(2025,1,20)
    }]
    html = gen.generar_tabla_nc_sin_acciones(rows)
    assert 'Desc' in html and 'NX' in html


def test_generar_resumen_estadisticas_conteos():
    gen = HTMLReportGenerator()
    now = datetime.datetime.now()
    ncs_eficacia = [{}]  # 1
    arapcs = [{'FechaFinPrevista': now - datetime.timedelta(days=1)}, {'FechaFinPrevista': now + datetime.timedelta(days=5)}]  # 2, 1 vencida
    ncs_caducar = [{'dias_para_cierre': -1}, {'dias_para_cierre': 3}]  # 1 caducada
    ncs_sin_acciones = [{}, {}]  # 2
    html = gen.generar_resumen_estadisticas(ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones)
    assert 'Resumen Ejecutivo' in html and 'Acciones Correctivas/Preventivas' in html
    assert 'vencidas' in html and 'caducadas' in html


def test_generar_reporte_completo_integration():
    gen = HTMLReportGenerator()
    now = datetime.datetime.now()
    ncs_eficacia = [{'CodigoNoConformidad':'E1','Nemotecnico':'NE','DESCRIPCION':'DE','RESPONSABLECALIDAD':'RC','FECHAAPERTURA': now, 'FPREVCIERRE': now}]
    arapcs = [{'IDAccionRealizada':1,'CodigoNoConformidad':'A1','AccionRealizada':'AR','Responsable':'R','FechaFinPrevista': now + datetime.timedelta(days=10)}]
    ncs_caducar = [{'CodigoNoConformidad':'C1','Nemotecnico':'NC','DESCRIPCION':'DC','RESPONSABLECALIDAD':'RC','FECHAAPERTURA': now, 'FPREVCIERRE': now, 'DiasParaCierre':5, 'dias_para_cierre':5}]
    ncs_sin_acciones = [{'CodigoNoConformidad':'S1','Nemotecnico':'NS','DESCRIPCION':'DS','RESPONSABLECALIDAD':'RC','FechaApertura': now, 'FechaPrevistaCierre': now}]
    html = gen.generar_reporte_completo(ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones, titulo='Reporte X')
    assert 'Reporte X' in html and 'Resumen Ejecutivo' in html and 'Acciones Correctivas/Preventivas Próximas a Vencer' in html


def test_generate_table_color_states_and_mapping():
    gen = HTMLReportGenerator()
    data = [
        {"CodigoNoConformidad":"NC1","DESCRIPCION":"Desc1","RESPONSABLECALIDAD":"Resp","FECHACIERRE": datetime.datetime(2025,1,1),"DiasParaCaducar": -2},
        {"CodigoNoConformidad":"NC2","DESCRIPCION":"Desc2","RESPONSABLECALIDAD":"Resp","FECHACIERRE": datetime.datetime(2025,1,2),"DiasParaCaducar": 0},
        {"CodigoNoConformidad":"NC3","DESCRIPCION":"Desc3","RESPONSABLECALIDAD":"Resp","FECHACIERRE": datetime.datetime(2025,1,3),"DiasParaCaducar": 4},
        {"CodigoNoConformidad":"NC4","DESCRIPCION":"Desc4","RESPONSABLECALIDAD":"Resp","FECHACIERRE": datetime.datetime(2025,1,4),"DiasParaCaducar": 10},
    ]
    headers = ["Código NC","Descripción","Responsable Calidad","Fecha Cierre","Días"]
    html = gen.generate_table(data, headers)
    # Verificar mapping y clases de color
    assert html.count('<tr>') == 5  # header + 4 rows
    # clases de color esperadas para -2,0,4,10
    assert 'negativo' in html and html.count('critico') >= 2 and 'normal' in html


def test_generate_table_empty():
    gen = HTMLReportGenerator()
    html = gen.generate_table([], ["Código NC"])
    assert 'No hay datos' in html
