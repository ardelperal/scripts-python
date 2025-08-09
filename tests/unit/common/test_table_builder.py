"""Tests unitarios para build_table_html (utilidad común)."""
import re
from datetime import datetime, date
from src.common.reporting.table_builder import build_table_html


def test_build_table_html_empty():
    assert build_table_html("Titulo", []) == ''


def test_build_table_html_basic():
    rows = [
        {"A": 1, "B": "x"},
        {"A": 2, "B": "y"},
    ]
    html = build_table_html("Mi Tabla", rows)
    assert "Mi Tabla" in html
    assert html.count('<tr>') == 3  # header + 2 rows
    assert '<th>A</th>' in html and '<th>B</th>' in html


def test_build_table_html_date_format():
    rows = [{"Fecha": datetime(2025, 1, 2), "Valor": 10}]
    html = build_table_html("Fechas", rows)
    assert '02/01/2025' in html


def test_build_table_html_sorted_headers():
    rows = [{"B": 1, "A": 2}]
    html = build_table_html("Orden", rows, sort_headers=True)
    # Cabeceras en orden alfabético A luego B
    assert re.search(r"<th>A</th>.*<th>B</th>", html)
