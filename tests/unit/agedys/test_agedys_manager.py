import logging
from unittest.mock import Mock
import pytest

from agedys.agedys_manager import AgedysManager


@pytest.fixture
def logger():
    return logging.getLogger("test")

@pytest.fixture
def db():
    return Mock()

@pytest.fixture
def manager(db, logger):
    return AgedysManager(db, logger)

# ---------------------- Tests de métodos get_* (muestran consulta) ----------------------

def test_get_facturas_pendientes_por_tecnico_calls_db(manager, db):
    db.execute_query.side_effect = [[{'NFactura': 'F1', 'NDOCUMENTO': 'D1'}], [], [], []]
    rows = manager.get_facturas_pendientes_por_tecnico(10, 'User')
    # 4 subconsultas
    assert db.execute_query.call_count == 4
    assert rows[0]['NFactura'] == 'F1'


def test_get_dpds_sin_so_por_tecnico(manager, db):
    db.execute_query.return_value = [{'CODPROYECTOS': 'D1'}]
    rows = manager.get_dpds_sin_so_por_tecnico('User')
    assert db.execute_query.called
    assert rows == [{'CODPROYECTOS': 'D1'}]


def test_get_dpds_con_so_sin_ro_por_tecnico(manager, db):
    db.execute_query.return_value = [{'CODPROYECTOS': 'D2'}]
    rows = manager.get_dpds_con_so_sin_ro_por_tecnico('User')
    assert rows[0]['CODPROYECTOS'] == 'D2'


def test_get_dpds_sin_visado_calidad_por_tecnico(manager, db):
    db.execute_query.return_value = [{'CODPROYECTOS': 'D3'}]
    assert manager.get_dpds_sin_visado_calidad_por_tecnico('User') == [{'CODPROYECTOS': 'D3'}]


def test_get_dpds_rechazados_calidad_por_tecnico(manager, db):
    db.execute_query.return_value = [{'CODPROYECTOS': 'D4'}]
    assert manager.get_dpds_rechazados_calidad_por_tecnico('User') == [{'CODPROYECTOS': 'D4'}]


def test_get_dpds_sin_visado_calidad_agrupado(manager, db):
    db.execute_query.return_value = [{'CODPROYECTOS': 'D5'}]
    assert manager.get_dpds_sin_visado_calidad_agrupado() == [{'CODPROYECTOS': 'D5'}]


def test_get_dpds_con_fin_agenda_tecnica_agrupado(manager, db):
    db.execute_query.return_value = [{'CODPROYECTOS': 'D6'}]
    assert manager.get_dpds_con_fin_agenda_tecnica_agrupado() == [{'CODPROYECTOS': 'D6'}]


def test_get_dpds_sin_pedido_agrupado(manager, db):
    db.execute_query.return_value = [{'CODPROYECTOS': 'D7'}]
    assert manager.get_dpds_sin_pedido_agrupado() == [{'CODPROYECTOS': 'D7'}]


def test_get_facturas_rechazadas_agrupado(manager, db):
    db.execute_query.return_value = [{'NFactura': 'F2'}]
    assert manager.get_facturas_rechazadas_agrupado() == [{'NFactura': 'F2'}]


def test_get_facturas_visadas_pendientes_op_agrupado(manager, db):
    db.execute_query.return_value = [{'NFactura': 'F3'}]
    assert manager.get_facturas_visadas_pendientes_op_agrupado() == [{'NFactura': 'F3'}]


# ---------------------- Tests de generación de informes ----------------------

def test_generate_technical_user_report_html_empty(manager, monkeypatch):
    # Forzar todos los métodos get_* a devolver vacío
    for name in [
        'get_dpds_sin_so_por_tecnico', 'get_dpds_con_so_sin_ro_por_tecnico',
        'get_dpds_sin_visado_calidad_por_tecnico', 'get_dpds_rechazados_calidad_por_tecnico',
        'get_facturas_pendientes_por_tecnico']:
        monkeypatch.setattr(manager, name, Mock(return_value=[]))
    # Espiar uso de header/footer
    gen = manager.html_generator
    monkeypatch.setattr(gen, 'generar_header_moderno', Mock(wraps=gen.generar_header_moderno))
    monkeypatch.setattr(gen, 'generar_footer_moderno', Mock(wraps=gen.generar_footer_moderno))

    html = manager.generate_technical_user_report_html(1, 'User', 'u@x')
    assert html == ''
    gen.generar_header_moderno.assert_not_called()
    gen.generar_footer_moderno.assert_not_called()


def test_generate_technical_user_report_html_with_data(manager, monkeypatch):
    monkeypatch.setattr(manager, 'get_dpds_sin_so_por_tecnico', Mock(return_value=[{'CODPROYECTOS': 'D1'}]))
    monkeypatch.setattr(manager, 'get_dpds_con_so_sin_ro_por_tecnico', Mock(return_value=[]))
    monkeypatch.setattr(manager, 'get_dpds_sin_visado_calidad_por_tecnico', Mock(return_value=[]))
    monkeypatch.setattr(manager, 'get_dpds_rechazados_calidad_por_tecnico', Mock(return_value=[]))
    monkeypatch.setattr(manager, 'get_facturas_pendientes_por_tecnico', Mock(return_value=[]))

    gen = manager.html_generator
    monkeypatch.setattr(gen, 'generar_header_moderno', Mock(wraps=gen.generar_header_moderno))
    monkeypatch.setattr(gen, 'generar_footer_moderno', Mock(wraps=gen.generar_footer_moderno))

    # Patch build_table_html en el módulo objetivo
    import src.agedys.agedys_manager as mod
    spy_build = Mock(return_value='<table/>')
    monkeypatch.setattr(mod, 'build_table_html', spy_build)

    html = manager.generate_technical_user_report_html(1, 'User', 'u@x')
    assert 'INFORME TAREAS PENDIENTES' in html
    assert spy_build.call_count == 1  # solo una sección con datos
    gen.generar_header_moderno.assert_called_once()
    gen.generar_footer_moderno.assert_called_once()


def test_generate_quality_report_html_empty(manager, monkeypatch):
    monkeypatch.setattr(manager, 'get_dpds_sin_visado_calidad_agrupado', Mock(return_value=[]))
    gen = manager.html_generator
    monkeypatch.setattr(gen, 'generar_header_moderno', Mock(wraps=gen.generar_header_moderno))
    html = manager.generate_quality_report_html()
    assert html == ''
    gen.generar_header_moderno.assert_not_called()


def test_generate_quality_report_html_with_data(manager, monkeypatch):
    monkeypatch.setattr(manager, 'get_dpds_sin_visado_calidad_agrupado', Mock(return_value=[{'CODPROYECTOS': 'D1'}]))
    import src.agedys.agedys_manager as mod
    spy_build = Mock(return_value='<table/>')
    monkeypatch.setattr(mod, 'build_table_html', spy_build)
    html = manager.generate_quality_report_html()
    assert 'CALIDAD' in html
    spy_build.assert_called_once()


def test_generate_economy_report_html_empty(manager, monkeypatch):
    for name in [
        'get_dpds_con_fin_agenda_tecnica_agrupado', 'get_dpds_sin_pedido_agrupado',
        'get_facturas_rechazadas_agrupado', 'get_facturas_visadas_pendientes_op_agrupado']:
        monkeypatch.setattr(manager, name, Mock(return_value=[]))
    html = manager.generate_economy_report_html()
    assert html == ''


def test_generate_economy_report_html_some(manager, monkeypatch):
    monkeypatch.setattr(manager, 'get_dpds_con_fin_agenda_tecnica_agrupado', Mock(return_value=[{'CODPROYECTOS': 'D1'}]))
    monkeypatch.setattr(manager, 'get_dpds_sin_pedido_agrupado', Mock(return_value=[]))
    monkeypatch.setattr(manager, 'get_facturas_rechazadas_agrupado', Mock(return_value=[{'NFactura': 'F1'}]))
    monkeypatch.setattr(manager, 'get_facturas_visadas_pendientes_op_agrupado', Mock(return_value=[]))
    import src.agedys.agedys_manager as mod
    spy_build = Mock(return_value='<table/>')
    monkeypatch.setattr(mod, 'build_table_html', spy_build)
    html = manager.generate_economy_report_html()
    assert 'ECONOMÍA' in html
    assert spy_build.call_count == 2


def test_generate_technical_user_report_html_multiple_sections(manager, monkeypatch):
    # Tres secciones con datos para verificar múltiples invocaciones
    monkeypatch.setattr(manager, 'get_dpds_sin_so_por_tecnico', Mock(return_value=[{'CODPROYECTOS': 'A'}]))
    monkeypatch.setattr(manager, 'get_dpds_con_so_sin_ro_por_tecnico', Mock(return_value=[{'CODPROYECTOS': 'B'}]))
    monkeypatch.setattr(manager, 'get_dpds_sin_visado_calidad_por_tecnico', Mock(return_value=[{'CODPROYECTOS': 'C'}]))
    monkeypatch.setattr(manager, 'get_dpds_rechazados_calidad_por_tecnico', Mock(return_value=[]))
    monkeypatch.setattr(manager, 'get_facturas_pendientes_por_tecnico', Mock(return_value=[]))
    import src.agedys.agedys_manager as mod
    calls = {}
    def side(title, rows, **kw):
        calls[title] = len(rows)
        return f"<table data-title='{title}'/>"
    monkeypatch.setattr(mod, 'build_table_html', side)
    html = manager.generate_technical_user_report_html(99, 'UserX', 'ux@example.com')
    assert "INFORME TAREAS PENDIENTES - UserX" in html
    # Verifica que se generaron exactamente las tres secciones con datos
    assert set(calls.keys()) == {"DPDs sin SO", "DPDs con SO sin RO", "DPDs sin visado calidad"}
    # Contenido HTML incluye los tres fragmentos
    for t in calls.keys():
        assert f"data-title='{t}'" in html

def test_pretty_headers_transformation(manager):
    """Valida que claves como 'ResponsableCalidad' se transforman a 'Responsable Calidad' en la tabla."""
    from common.reporting.table_builder import build_table_html
    sample_rows = [{'ResponsableCalidad': 'Juan'}]
    html = build_table_html('Seccion', sample_rows, pretty_headers=True)
    assert 'Responsable Calidad' in html
    assert 'ResponsableCalidad' not in html


def test_pretty_headers_camelcase_split():
    from common.reporting.table_builder import build_table_html
    sample_rows = [{'UserName': 'Ana', 'UserEmail': 'ana@x'}]
    html = build_table_html('Seccion', sample_rows, pretty_headers=True)
    assert '<th>User Name</th>' in html
    assert '<th>UserName</th>' not in html


# ---------------------- Nuevos tests de cobertura adicional ----------------------

def test_get_usuarios_con_tareas_pendientes_basic(manager, db):
    # Simular 5 subconsultas con usuarios distintos y repetidos
    db.execute_query.side_effect = [
        [{'UsuarioRed': 'u1'}],  # sin SO
        [{'UsuarioRed': 'u2'}],  # con SO sin RO
        [{'UsuarioRed': 'u1'}],  # sin visado calidad (dup)
        [],                      # rechazados calidad vacío
        [{'UsuarioRed': 'u3'}],  # facturas pendientes
        # Detalle final: tres usuarios
        [
            {'UserId': 1, 'UserName': 'U1', 'UserEmail': 'u1@x'},
            {'UserId': 2, 'UserName': 'U2', 'UserEmail': 'u2@x'},
            {'UserId': 3, 'UserName': 'U3', 'UserEmail': 'u3@x'},
        ]
    ]
    users = manager.get_usuarios_con_tareas_pendientes()
    assert len(users) == 3
    # Verificar llamada final (6 total: 5 subqueries + detalle)
    assert db.execute_query.call_count == 6


def test_get_usuarios_con_tareas_pendientes_error_path(manager, db, caplog):
    # Forzar excepción en primera subconsulta y devolver datos en la segunda
    def side_effect(sql, params=None):
        if 'SELECT DISTINCT u.UsuarioRed' in sql and 'sop.DPD IS NULL' in sql:
            raise Exception('boom')
        return [{'UsuarioRed': 'uX'}] if 'UsuarioRed' in sql else []

    db.execute_query.side_effect = [Exception('boom'), [{'UsuarioRed': 'uX'}], [], [], [], [{'UserId': 9, 'UserName': 'UX', 'UserEmail': 'ux@x'}]]
    users = manager.get_usuarios_con_tareas_pendientes()
    assert users and users[0]['UserId'] == 9
    # Asegura que pese al fallo continúa
    assert db.execute_query.call_count == 6


def test_get_facturas_pendientes_por_tecnico_error_subquery(manager, db):
    # Primera subconsulta lanza excepción; las demás retornan vacío
    def exec_side(sql, params=None):
        if 'SELECT DISTINCT fd.NFactura' in sql and 'vf.FRECHAZOTECNICO IS NULL' in sql and 'er.CorreoSiempre=\'Sí\'' in sql:
            raise Exception('q1_fail')
        return []
    db.execute_query.side_effect = exec_side
    rows = manager.get_facturas_pendientes_por_tecnico(1, 'User')
    # No explota y retorna lista vacía
    assert rows == []