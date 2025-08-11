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


def build_mgr(responses):
    return AgedysManager(DummyDB(responses), logger=logging.getLogger("test"))


def test_empty():
    mgr = build_mgr([[], [], [], [], [], [], [], []])
    assert mgr.generate_technical_user_report_html(1, "User", "u@example.com") == ""


def test_some():
    fact_row = {
        "NFactura": "F1",
        "NDOCUMENTO": "DOC",
        "CODPROYECTOS": "D2",
        "PETICIONARIO": "P2",
        "CodExp": "E2",
        "DESCRIPCION": "Desc2",
        "IMPORTEADJUDICADO": 1000,
        "Suministrador": "SUM",
        "ImporteFactura": 500,
    }
    mgr = build_mgr([[], [], [], [], [fact_row], [], [], []])
    html = mgr.generate_technical_user_report_html(1, "User", "u@example.com")
    assert "Facturas pendientes" in html and html.count("<table") == 1


def test_all():
    dpd = {
        "CODPROYECTOS": "D1",
        "PETICIONARIO": "P",
        "FECHAPETICION": "2025-01-01",
        "EXPEDIENTE": "E1",
        "DESCRIPCION": "Desc",
    }
    dpd_visado = {
        "CODPROYECTOS": "D2",
        "PETICIONARIO": "P2",
        "FECHAPETICION": "2025-02-02",
        "CodExp": "E2",
        "DESCRIPCION": "Desc2",
        "ResponsableCalidad": "RC",
    }
    fact = {
        "NFactura": "F1",
        "NDOCUMENTO": "X",
        "CODPROYECTOS": "D3",
        "PETICIONARIO": "P3",
        "CodExp": "E3",
        "DESCRIPCION": "Desc3",
        "IMPORTEADJUDICADO": 1000,
        "Suministrador": "S",
        "ImporteFactura": 250,
    }
    mgr = build_mgr([[dpd], [dpd], [dpd_visado], [dpd], [fact], [fact], [fact], [fact]])
    html = mgr.generate_technical_user_report_html(1, "User", "u@example.com")
    assert html.count("<table") == 5
