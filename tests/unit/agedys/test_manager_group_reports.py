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


def test_quality_empty():
    assert build_mgr([[]]).generate_quality_report_html() == ""


def test_quality_one():
    row = {
        "CODPROYECTOS": "D1",
        "PETICIONARIO": "P",
        "FECHAPETICION": "2025-01-01",
        "CodExp": "E1",
        "DESCRIPCION": "Desc",
        "ResponsableCalidad": "RC",
    }
    html = build_mgr([[row]]).generate_quality_report_html()
    assert "DPDs sin visado calidad" in html


def test_economy_mixed():
    row1 = {
        "CODPROYECTOS": "D1",
        "PETICIONARIO": "P",
        "FECHAPETICION": "2025-01-01",
        "EXPEDIENTE": "E1",
        "DESCRIPCION": "D",
    }
    fact = {
        "NFactura": "F1",
        "NDocumento": "N",
        "CODPROYECTOS": "D2",
        "PETICIONARIO": "P2",
        "EXPEDIENTE": "E2",
        "DESCRIPCION": "D2",
        "IMPORTESINIVA": 100,
        "Suministrador": "S",
        "ImporteFactura": 50,
    }
    html = build_mgr([[row1], [], [fact], []]).generate_economy_report_html()
    assert (
        "DPDs fin agenda técnica pendientes recepción" in html
        and "Facturas rechazadas" in html
    )
