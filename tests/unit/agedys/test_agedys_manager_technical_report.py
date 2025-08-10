import logging
import pytest
from src.agedys.agedys_manager import AgedysManager


class DummyDB:
    def __init__(self, scripted):
        self.scripted = scripted
        self.calls = 0

    def execute_query(self, sql, params=None):  # params ignored in scripted mock
        if self.calls >= len(self.scripted):
            self.calls += 1
            return []
        resp = self.scripted[self.calls]
        self.calls += 1
        return resp


def build_manager(responses):
    return AgedysManager(DummyDB(responses), logger=logging.getLogger("test"))


def test_technical_report_empty():
    # order of calls in generate_technical_user_report_html:
    # get_dpds_sin_so_por_tecnico, get_dpds_con_so_sin_ro_por_tecnico,
    # get_dpds_sin_visado_calidad_por_tecnico, get_dpds_rechazados_calidad_por_tecnico,
    # get_facturas_pendientes_por_tecnico (which itself triggers 4 internal queries)
    # Provide empties for first 4 + 4 empties for facturas subqueries
    mgr = build_manager([[], [], [], [], [], [], [], [],])
    html = mgr.generate_technical_user_report_html(1, "User", "user@example.com")
    assert html == ""


def test_technical_report_some_sections():
    dpds_sin_so = [{"CODPROYECTOS":"D1","PETICIONARIO":"P","FECHAPETICION":"2025-01-01","EXPEDIENTE":"E1","DESCRIPCION":"Desc"}]
    fact_sub = [{"NFactura":"F1","NDOCUMENTO":"DOC","CODPROYECTOS":"D2","PETICIONARIO":"P2","CodExp":"E2","DESCRIPCION":"Desc2","IMPORTEADJUDICADO":1000,"Suministrador":"SUM","ImporteFactura":500}]
    # 2 first queries empty, then dpds_sin_visado empty, rechazados empty, then 4 facturas subqueries (only first returns rows)
    mgr = build_manager([
        [], [], [], [],  # first 4 section queries
        fact_sub, [], [], [],  # 4 facturas subqueries
    ])
    html = mgr.generate_technical_user_report_html(1, "User", "user@example.com")
    assert "Facturas pendientes" in html
    assert "DPDs sin SO" not in html  # first section empty
    assert html.count("<table") == 1


def test_technical_report_all_sections():
    row_dpds = {"CODPROYECTOS":"D1","PETICIONARIO":"P","FECHAPETICION":"2025-01-01","EXPEDIENTE":"E1","DESCRIPCION":"Desc"}
    row_dpds_visado = {"CODPROYECTOS":"D2","PETICIONARIO":"P2","FECHAPETICION":"2025-02-02","CodExp":"E2","DESCRIPCION":"Desc2","ResponsableCalidad":"RC"}
    row_fact = {"NFactura":"F1","NDOCUMENTO":"X","CODPROYECTOS":"D3","PETICIONARIO":"P3","CodExp":"E3","DESCRIPCION":"Desc3","IMPORTEADJUDICADO":1000,"Suministrador":"S","ImporteFactura":250}
    # order: 4 section queries then 4 facturas subqueries
    mgr = build_manager([
        [row_dpds],  # sin SO
        [row_dpds],  # con SO sin RO
        [row_dpds_visado],  # sin visado calidad
        [row_dpds],  # rechazados calidad
        [row_fact], [row_fact], [row_fact], [row_fact],  # facturas subqueries
    ])
    html = mgr.generate_technical_user_report_html(1, "User", "user@example.com")
    assert "DPDs sin SO" in html
    assert "DPDs con SO sin RO" in html
    assert "DPDs sin visado calidad" in html
    assert "DPDs rechazados calidad" in html
    assert "Facturas pendientes" in html
    assert html.count("<table") == 5
    # Verificamos que aparece el valor numérico bruto (el formateo de moneda ya no se aplica en el manager moderno)
    assert "1000" in html
