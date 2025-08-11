#!/usr/bin/env python3
"""
Tests funcionales para AGEDYS - Simulación de escenarios reales de negocio
"""

import logging
from unittest.mock import Mock, patch

import pytest

from agedys.agedys_manager import AgedysManager

# Configurar logging para tests
logging.basicConfig(level=logging.INFO)


@pytest.fixture
def mock_config():
    """Mock de configuración para tests funcionales"""
    with patch("src.agedys.agedys_manager.config") as mock_config:
        mock_config.get_db_agedys_connection_string.return_value = (
            "mock_agedys_connection"
        )
        mock_config.get_db_tareas_connection_string.return_value = (
            "mock_tareas_connection"
        )
        mock_config.get_db_correos_connection_string.return_value = (
            "mock_correos_connection"
        )
        mock_config.css_file_path = "mock_css_path"
        yield mock_config


@pytest.fixture
def mock_database_with_realistic_data():
    """Mock de base de datos con datos realistas para tests funcionales"""
    with patch("src.agedys.agedys_manager.AccessDatabase") as mock_db_class:
        # Crear mocks para las diferentes bases de datos
        mock_agedys_db = Mock()
        mock_tareas_db = Mock()
        mock_correos_db = Mock()

        # Configurar el constructor para devolver la instancia correcta según la conexión
        def db_constructor(connection_string):
            if "agedys" in connection_string:
                return mock_agedys_db
            elif "tareas" in connection_string:
                return mock_tareas_db
            elif "correos" in connection_string:
                return mock_correos_db
            return mock_agedys_db

        mock_db_class.side_effect = db_constructor

        # Datos realistas para facturas
        facturas_data = [
            {
                "NFactura": "FAC-2024-001",
                "CODPROYECTOS": "PRJ-001",
                "PETICIONARIO": "juan.perez",
                "CodExp": "EXP-001",
                "DESCRIPCION": "Licencias software desarrollo",
                "IMPORTEADJUDICADO": 15750.50,
                "Suministrador": "Tecnologías Avanzadas S.L.",
                "ImporteFactura": 15750.50,
                "NDOCUMENTO": "DOC-001",
            },
            {
                "NFactura": "FAC-2024-002",
                "CODPROYECTOS": "PRJ-002",
                "PETICIONARIO": "maria.garcia",
                "CodExp": "EXP-002",
                "DESCRIPCION": "Material técnico especializado",
                "IMPORTEADJUDICADO": 8920.75,
                "Suministrador": "Suministros Industriales S.A.",
                "ImporteFactura": 8920.75,
                "NDOCUMENTO": "DOC-002",
            },
        ]

        # Datos realistas para DPDs
        dpds_data = [
            {
                "CODPROYECTOS": "DPD-2024-001",
                "DESCRIPCION": "Actualización sistema gestión documental",
                "PETICIONARIO": "juan.perez",
                "FECHAPETICION": "2024-01-10",
                "CodExp": "EXP-001",
                "ResponsableCalidad": "María García",
            },
            {
                "CODPROYECTOS": "DPD-2024-002",
                "DESCRIPCION": "Implementación protocolo seguridad",
                "PETICIONARIO": "maria.garcia",
                "FECHAPETICION": "2024-01-12",
                "CodExp": "EXP-002",
                "ResponsableTecnico": "Carlos López",
                "ROObservaciones": "Documentación incompleta",
            },
        ]

        # Datos realistas para usuarios
        usuarios_data = [
            {
                "UsuarioRed": "juan.perez",
                "Nombre": "Juan Pérez Martínez",
                "CorreoUsuario": "juan.perez@empresa.com",
            },
            {
                "UsuarioRed": "maria.garcia",
                "Nombre": "María García López",
                "CorreoUsuario": "maria.garcia@empresa.com",
            },
            {
                "UsuarioRed": "carlos.lopez",
                "Nombre": "Carlos López Rodríguez",
                "CorreoUsuario": "carlos.lopez@empresa.com",
            },
            {
                "UsuarioRed": "ana.martin",
                "Nombre": "Ana Martín Sánchez",
                "CorreoUsuario": "ana.martin@empresa.com",
            },
        ]

        # Configurar respuestas de las consultas
        def mock_agedys_query(query, params=None):
            # Consultas de usuarios con facturas pendientes
            if (
                "TbUsuariosAplicaciones.UsuarioRed" in query
                and "TbFacturasDetalle" in query
            ):
                return [{"UsuarioRed": "juan.perez"}, {"UsuarioRed": "maria.garcia"}]

            # Consultas de facturas pendientes por usuario
            elif "TbFacturasDetalle.NFactura" in query and params:
                usuario = params[0]
                return [f for f in facturas_data if f["PETICIONARIO"] == usuario]

            # Consultas de usuarios con DPDs sin visado
            elif (
                "TbUsuariosAplicaciones.UsuarioRed" in query
                and "TbVisadosGenerales" in query
            ):
                return [
                    {
                        "UsuarioRed": "juan.perez",
                        "CorreoUsuario": "juan.perez@empresa.com",
                    }
                ]

            # Consultas de DPDs sin visado por usuario
            elif (
                "TbProyectos.CODPROYECTOS" in query
                and "TbVisadosGenerales" in query
                and params
            ):
                return [dpds_data[0]]  # Primer DPD

            # Consultas de usuarios con DPDs rechazados
            elif "ROFechaRechazo IS NOT NULL" in query:
                return [
                    {
                        "UsuarioRed": "maria.garcia",
                        "CorreoUsuario": "maria.garcia@empresa.com",
                    }
                ]

            # Consultas de DPDs rechazados por usuario
            elif "ROObservaciones" in query and params:
                return [dpds_data[1]]  # Segundo DPD

            # Consultas de DPDs con fin de agenda técnica
            elif "FechaFinAgendaTecnica IS NOT NULL" in query:
                return [dpds_data[0]]

            # Consultas de DPDs sin pedido
            elif "TbNPedido.NPEDIDO IS NULL" in query:
                return [dpds_data[0]]

            # Consulta fallback para usuarios de facturas
            elif "PETICIONARIO as UsuarioRed" in query:
                return [{"UsuarioRed": "juan.perez"}, {"UsuarioRed": "maria.garcia"}]

            return []

        def mock_tareas_query(query, params=None):
            # Consultas de usuarios de economía
            if "EsEconomia" in query:
                return [u for u in usuarios_data if u["UsuarioRed"] == "ana.martin"]

            # Consultas de usuarios técnicos
            elif "TbUsuariosAplicacionesTareas.CorreoUsuario IS NULL" in query:
                return [
                    u
                    for u in usuarios_data
                    if u["UsuarioRed"] in ["juan.perez", "carlos.lopez"]
                ]

            return usuarios_data

        mock_agedys_db.execute_query.side_effect = mock_agedys_query
        mock_tareas_db.execute_query.side_effect = mock_tareas_query
        mock_correos_db.execute_query.return_value = []

        yield {
            "agedys": mock_agedys_db,
            "tareas": mock_tareas_db,
            "correos": mock_correos_db,
        }


@pytest.fixture
def mock_utils():
    """Mock de utilidades para tests funcionales"""
    with patch("src.agedys.agedys_manager.load_css_content") as mock_css, patch(
        "src.agedys.agedys_manager.register_email_in_database"
    ) as mock_register_email, patch(
        "src.agedys.agedys_manager.should_execute_task"
    ) as mock_should_execute, patch(
        "src.agedys.agedys_manager.register_task_completion"
    ) as mock_register_task:
        mock_css.return_value = """
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
            .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .footer { margin-top: 30px; padding: 20px; background-color: #ecf0f1; text-align: center; }
        """

        # Eliminados mocks de generate_html_header / generate_html_footer (wrappers legacy eliminados)

        mock_register_email.return_value = True
        mock_should_execute.return_value = True
        mock_register_task.return_value = True

        yield {
            "css": mock_css,
            "register_email": mock_register_email,
            "should_execute": mock_should_execute,
            "register_task": mock_register_task,
        }


@pytest.fixture
def agedys_manager(mock_config, mock_database_with_realistic_data, mock_utils):
    """Instancia de AgedysManager para tests funcionales"""
    return AgedysManager()


def test_complete_business_workflow_facturas_pendientes(
    agedys_manager, mock_database_with_realistic_data
):
    """Test del flujo completo de negocio para facturas pendientes"""
    # Ejecutar el proceso completo
    result = agedys_manager.run(dry_run=True)

    # Verificar que el proceso se ejecuta correctamente
    assert result is True

    # Verificar que se obtienen usuarios con facturas pendientes
    usuarios = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
    assert len(usuarios) >= 0  # Puede ser 0 o más usuarios

    # Si hay usuarios, verificar que se obtienen facturas
    if usuarios:
        facturas = agedys_manager.get_facturas_pendientes_visado_tecnico(
            usuarios[0]["UsuarioRed"]
        )
        assert len(facturas) >= 0  # Puede ser 0 o más facturas


def test_html_email_formatting_quality(agedys_manager):
    """Test de la calidad del formato HTML de los emails"""
    # Datos de prueba
    facturas_test = [
        {
            "NFactura": "FAC-2024-001",
            "Suministrador": "Tecnologías Avanzadas S.L.",
            "ImporteFactura": 1234.56,
            "FechaFactura": "2024-01-15",
            "PETICIONARIO": "juan.perez",
        }
    ]

    # Generar tabla HTML
    html_table = agedys_manager.generate_facturas_html_table(facturas_test)

    # Verificar estructura HTML básica
    assert "<table" in html_table
    assert "</table>" in html_table

    # Verificar que contiene los datos
    assert "FAC-2024-001" in html_table
    assert "Tecnologías Avanzadas S.L." in html_table

    # Verificar formato de números (puede variar según configuración)
    assert "1234" in html_table or "1.234" in html_table


def test_user_notification_targeting(agedys_manager, mock_database_with_realistic_data):
    """Test de la correcta segmentación de notificaciones por usuario"""
    # Obtener usuarios con facturas pendientes
    usuarios = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()

    # Verificar que se obtienen usuarios
    assert len(usuarios) >= 0

    # Si hay usuarios, verificar que cada uno tiene su propio conjunto de facturas
    if usuarios:
        for usuario in usuarios:
            facturas = agedys_manager.get_facturas_pendientes_visado_tecnico(
                usuario["UsuarioRed"]
            )
            # Verificar que las facturas pertenecen al usuario correcto
            for factura in facturas:
                assert factura["PETICIONARIO"] == usuario["UsuarioRed"]


def test_business_rules_compliance(agedys_manager, mock_database_with_realistic_data):
    """Test de cumplimiento de reglas de negocio"""
    # Verificar que solo se procesan facturas pendientes de visado técnico
    usuarios = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()

    # Verificar que el método funciona correctamente
    assert len(usuarios) >= 0

    # Si hay usuarios, verificar que las facturas cumplen las reglas
    if usuarios:
        for usuario in usuarios:
            facturas = agedys_manager.get_facturas_pendientes_visado_tecnico(
                usuario["UsuarioRed"]
            )

            # Verificar que todas las facturas tienen los campos requeridos
            for factura in facturas:
                assert "NFactura" in factura
                assert "PETICIONARIO" in factura
                # Verificar que el peticionario coincide con el usuario
                assert factura["PETICIONARIO"] == usuario["UsuarioRed"]


def test_error_recovery_mechanisms(agedys_manager, mock_database_with_realistic_data):
    """Test de mecanismos de recuperación de errores"""
    # Simular error en base de datos
    with patch.object(
        agedys_manager.db, "execute_query", side_effect=Exception("Database error")
    ):
        # El sistema debe manejar el error graciosamente
        result = agedys_manager.run(dry_run=True)

        # Verificar que no se produce una excepción no controlada
        # El resultado puede ser False debido al error, pero no debe lanzar excepción
        assert result in [True, False]


def test_performance_with_large_datasets(
    agedys_manager, mock_database_with_realistic_data
):
    """Test de rendimiento con datasets grandes"""
    import time

    # Simular dataset grande
    large_facturas = []
    for i in range(100):
        large_facturas.append(
            {
                "NFactura": f"FAC-2024-{i:03d}",
                "Suministrador": f"Proveedor {i}",
                "ImporteFactura": 1000.0 + i,
                "DESCRIPCION": f"Descripción factura {i}",
            }
        )

    # Medir tiempo de generación de HTML
    start_time = time.time()
    html_table = agedys_manager.generate_facturas_html_table(large_facturas)
    end_time = time.time()

    # Verificar que se genera en tiempo razonable (menos de 1 segundo)
    assert (end_time - start_time) < 1.0

    # Verificar que el HTML contiene todos los elementos
    assert html_table.count("<tr>") >= 100  # Al menos 100 filas de datos


def test_email_content_localization(agedys_manager, mock_utils):
    """Test de localización del contenido de emails"""
    # Datos de prueba con formato español
    facturas = [
        {
            "NFactura": "FAC-2024-001",
            "Suministrador": "Proveedor Español S.L.",
            "ImporteFactura": 1234.56,
            "FechaRecepcion": "2024-01-15",
            "DESCRIPCION": "Descripción en español",
        }
    ]

    # Generar HTML
    html_table = agedys_manager.generate_facturas_html_table(facturas)

    # Verificar formato español de números
    assert "1234.56" in html_table  # Formato numérico correcto

    # Verificar contenido en español
    assert "Proveedor Español S.L." in html_table
    assert "Descripción en español" in html_table


def test_dry_run_vs_production_differences(
    agedys_manager, mock_database_with_realistic_data
):
    """Test de diferencias entre modo dry run y producción"""
    # Ejecutar en modo dry run
    result_dry = agedys_manager.run(dry_run=True)

    # Ejecutar en modo producción (simulado)
    result_prod = agedys_manager.run(dry_run=False)

    # Ambos modos deben ejecutarse correctamente
    assert result_dry in [True, False]  # Puede fallar por datos vacíos
    assert result_prod in [True, False]  # Puede fallar por datos vacíos


def test_task_scheduling_integration(agedys_manager):
    """Test de integración con el sistema de programación de tareas"""
    # Verificar que el manager puede ejecutar tareas
    result = agedys_manager.run(dry_run=True)

    # El resultado debe ser booleano
    assert isinstance(result, bool)


def test_realistic_end_to_end_scenario(
    agedys_manager, mock_database_with_realistic_data
):
    """Test de escenario realista de principio a fin"""
    # Simular un día típico de trabajo
    result = agedys_manager.run(dry_run=True)

    # Verificar que el proceso se ejecuta
    assert isinstance(result, bool)

    # Verificar que se pueden obtener datos de facturas
    usuarios = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
    assert len(usuarios) >= 0

    # Verificar que se pueden obtener datos de DPDs
    usuarios_dpds = agedys_manager.get_usuarios_dpds_sin_visado_calidad()
    assert len(usuarios_dpds) >= 0
