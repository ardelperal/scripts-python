import os
import re
import sys

from common.html_report_generator import HTMLReportGenerator

# Agregar src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(
    os.path.dirname(current_dir)
)  # subir de unit -> tests -> root
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


def test_reporte_calidad_moderno_vacio():
    gen = HTMLReportGenerator()
    html = gen.generar_reporte_calidad_moderno([], [], [], [])
    assert "<html" in html.lower()
    # Sin tablas de datos -> debería incluir header y footer
    assert "Informe de No Conformidades - Calidad" in html


def test_reporte_calidad_moderno_con_datos():
    gen = HTMLReportGenerator()
    ars = [
        {
            "CodigoNoConformidad": "NC001",
            "Nemotecnico": "NEMO",
            "DESCRIPCION": "Desc",
            "RESPONSABLECALIDAD": "Resp",
            "FECHAAPERTURA": "2025-08-01",
            "FPREVCIERRE": "2025-08-20",
            "DiasParaCierre": 5,
        }
    ]
    html = gen.generar_reporte_calidad_moderno(ars, [], [], [])
    assert "NC001" in html
    assert "Desc" in html
    # Días badge
    assert re.search(r"dias-indicador", html)


def test_reporte_tecnico_moderno():
    gen = HTMLReportGenerator()
    ars15 = [
        {
            "CodigoNoConformidad": "NC002",
            "Nemotecnico": "NM",
            "AccionCorrectiva": "Acción",
            "AccionRealizada": "Tarea",
            "FechaInicio": "2025-08-01",
            "FechaFinPrevista": "2025-08-25",
            "Nombre": "Tec",
            "DiasParaCaducar": 10,
            "CorreoCalidad": "calidad@test",
        }
    ]
    html = gen.generar_reporte_tecnico_moderno(ars15, [], [])
    assert "NC002" in html
    assert "Acción" in html or "Acci" in html
    assert "Tec" in html
