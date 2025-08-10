import logging
from agedys.agedys_manager import AgedysManager

class DummyDB:
    def __init__(self, scripted):
        self.scripted = scripted
        self.calls = 0
    def execute_query(self, sql, params=None):
        if self.calls >= len(self.scripted):
            self.calls += 1
            return []
        resp = self.scripted[self.calls]
        self.calls += 1
        return resp

def build_manager(responses):
    return AgedysManager(DummyDB(responses), logger=logging.getLogger("test"))


def test_quality_empty():
    mgr = build_manager([[]])  # only one query used
    assert mgr.generate_quality_report_html() == ""


def test_quality_non_empty():
    row = {"CODPROYECTOS":"D1","PETICIONARIO":"P","FECHAPETICION":"2025-01-01","CodExp":"E1","DESCRIPCION":"Desc","ResponsableCalidad":"RC"}
    mgr = build_manager([[row]])
    html = mgr.generate_quality_report_html()
    assert "DPDs sin visado calidad" in html
    assert html.count('<table') == 1


def test_economy_empty():
    # economy queries order (4): fin agenda tecnica, sin pedido, facturas rechazadas, visadas pte op
    mgr = build_manager([[], [], [], []])
    assert mgr.generate_economy_report_html() == ""


def test_economy_some():
    row1 = {"CODPROYECTOS":"D1","PETICIONARIO":"P","FECHAPETICION":"2025-01-01","EXPEDIENTE":"E1","DESCRIPCION":"D"}
    row_fact = {"NFactura":"F1","NDocumento":"N","CODPROYECTOS":"D2","PETICIONARIO":"P2","EXPEDIENTE":"E2","DESCRIPCION":"D2","IMPORTESINIVA":100,"Suministrador":"S","ImporteFactura":50}
    mgr = build_manager([[row1], [], [row_fact], []])
    html = mgr.generate_economy_report_html()
    assert "DPDs fin agenda técnica pendientes recepción" in html
    assert "Facturas rechazadas" in html
    assert "DPDs sin pedido" not in html
    assert "Facturas visadas pendientes orden de pago" not in html
    assert html.count('<table') == 2
