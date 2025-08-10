"""Integration-style tests for AgedysManager using an in-memory stub DB.
Focus: multi-user technical report generation loop & aggregate reports.
"""
from __future__ import annotations

from unittest.mock import Mock

from agedys.agedys_manager import AgedysManager

class StubDB:
    def __init__(self, data_map):
        self.data_map = data_map
        self.calls = []

    def execute_query(self, sql: str, params=None):
        key = (sql.strip(), tuple(params or []))
        self.calls.append(key)
        return self.data_map.get(key, [])


def build_manager():
    # Minimal sections exercised; we simulate only the datasets used by high-level methods.
    db = StubDB(data_map={})
    return AgedysManager(db, None), db


def test_full_quality_report_flow():
    manager, db = build_manager()
    # Inject dataset producing a non-empty quality report
    manager.get_dpds_sin_visado_calidad_agrupado = Mock(return_value=[{"CODPROYECTOS": "D1", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-01", "CodExp": "E1", "DESCRIPCION": "Desc", "ResponsableCalidad": "RC"}])
    html = manager.generate_quality_report_html()
    assert "D1" in html
    # Column header may be prettified ("Responsable Calidad") or raw ("ResponsableCalidad")
    assert ("ResponsableCalidad" in html or "Responsable Calidad" in html) and "RC" in html


def test_full_economy_report_flow():
    manager, db = build_manager()
    manager.get_dpds_con_fin_agenda_tecnica_agrupado = Mock(return_value=[{"CODPROYECTOS": "D1", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-01", "EXPEDIENTE": "E1", "DESCRIPCION": "Desc"}])
    manager.get_dpds_sin_pedido_agrupado = Mock(return_value=[{"CODPROYECTOS": "D2", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-02", "EXPEDIENTE": "E2", "DESCRIPCION": "Desc2"}])
    manager.get_facturas_rechazadas_agrupado = Mock(return_value=[])
    manager.get_facturas_visadas_pendientes_op_agrupado = Mock(return_value=[])
    html = manager.generate_economy_report_html()
    assert "D1" in html and "D2" in html


def test_full_technical_user_report_multiple_sections():
    manager, db = build_manager()
    manager.get_dpds_sin_so_por_tecnico = Mock(return_value=[{"CODPROYECTOS": "D1", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-01", "EXPEDIENTE": "E1", "DESCRIPCION": "Desc"}])
    manager.get_dpds_con_so_sin_ro_por_tecnico = Mock(return_value=[{"CODPROYECTOS": "D2", "PETICIONARIO": "Tec", "FECHAPETICION": "2025-01-02", "EXPEDIENTE": "E2", "DESCRIPCION": "Desc2"}])
    manager.get_dpds_sin_visado_calidad_por_tecnico = Mock(return_value=[])
    manager.get_dpds_rechazados_calidad_por_tecnico = Mock(return_value=[])
    manager.get_facturas_pendientes_por_tecnico = Mock(return_value=[])
    html = manager.generate_technical_user_report_html(7, "Tec", "tec@example.com")
    assert "D1" in html and "D2" in html
