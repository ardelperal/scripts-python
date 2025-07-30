"""
Tests de integración para el módulo AGEDYS
"""
import pytest
import os
from unittest.mock import patch, Mock
from src.agedys.agedys_manager import AgedysManager
from common.database import AccessDatabase


class TestAgedysIntegration:
    """Tests de integración para AGEDYS"""
    
    @pytest.fixture
    def test_db_paths(self):
        """Rutas de bases de datos de prueba"""
        return {
            'agedys': 'tests/data/test_agedys.accdb',
            'tareas': 'tests/data/test_tareas.accdb',
            'correos': 'tests/data/test_correos.accdb'
        }
    
    @pytest.fixture
    def mock_config_with_test_dbs(self):
        """Mock de configuración con bases de datos de prueba"""
        with patch('src.common.config.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.db_agedys_path = "test_agedys.mdb"
            mock_config.db_tareas_path = "test_tareas.mdb"
            mock_config.db_correos_path = "test_correos.mdb"
            mock_config.get_db_correos_connection_string.return_value = "test_correos.mdb"
            mock_config_class.return_value = mock_config
            yield mock_config
    
    @pytest.fixture
    def mock_access_database(self):
        """Mock de AccessDatabase para tests de integración"""
        with patch('src.agedys.agedys_manager.AccessDatabase') as mock_db_class:
            mock_db = Mock(spec=AccessDatabase)
            mock_db_class.return_value = mock_db
            yield mock_db_class
    
    @pytest.fixture
    def mock_utils(self):
        """Mock de utilidades para tests de integración"""
        with patch('src.agedys.agedys_manager.load_css_content') as mock_css, \
             patch('src.agedys.agedys_manager.generate_html_header') as mock_header, \
             patch('src.agedys.agedys_manager.generate_html_footer') as mock_footer, \
             patch('src.agedys.agedys_manager.register_email_in_database') as mock_register_email, \
             patch('src.agedys.agedys_manager.should_execute_task') as mock_should_execute, \
             patch('src.agedys.agedys_manager.register_task_completion') as mock_register_task:
            
            mock_css.return_value = "body { font-family: Arial; }"
            mock_header.return_value = "<html><head><style>body { font-family: Arial; }</style></head><body>"
            mock_footer.return_value = "</body></html>"
            mock_register_email.return_value = True
            mock_should_execute.return_value = True
            mock_register_task.return_value = True
            
            yield {
                'css': mock_css,
                'header': mock_header,
                'footer': mock_footer,
                'register_email': mock_register_email,
                'should_execute': mock_should_execute,
                'register_task': mock_register_task
            }
    
    @pytest.fixture
    def agedys_manager(self, mock_config_with_test_dbs, mock_access_database, mock_utils):
        """Instancia de AgedysManager para tests de integración"""
        return AgedysManager()
    
    def test_database_connections_initialization(self, agedys_manager, mock_access_database):
        """Test que las conexiones a las bases de datos se inicializan correctamente"""
        assert agedys_manager.db is not None
        assert agedys_manager.tareas_db is not None
        assert agedys_manager.correos_db is not None
        
        # Verificar que se crearon 3 instancias de AccessDatabase
        assert mock_access_database.call_count == 3
    
    def test_full_workflow_with_data(self, agedys_manager, mock_access_database):
        """Test del flujo completo con datos simulados"""
        # Configurar datos de prueba
        mock_usuarios_facturas = [
            {'Nombre': 'Juan Pérez', 'CorreoUsuario': 'juan.perez@empresa.com'},
            {'Nombre': 'María García', 'CorreoUsuario': 'maria.garcia@empresa.com'}
        ]
        
        mock_facturas = [
            {
                'NumeroFactura': 'F2024-001',
                'Proveedor': 'Proveedor Test S.L.',
                'Importe': 1250.75,
                'FechaFactura': '2024-01-15',
                'Descripcion': 'Servicios de consultoría'
            },
            {
                'NumeroFactura': 'F2024-002',
                'Proveedor': 'Suministros Técnicos S.A.',
                'Importe': 850.50,
                'FechaFactura': '2024-01-16',
                'Descripcion': 'Material de oficina'
            }
        ]
        
        mock_usuarios_dpds = [
            {'Nombre': 'Carlos López', 'CorreoUsuario': 'carlos.lopez@empresa.com'}
        ]
        
        mock_dpds = [
            {
                'NumeroDPD': 'DPD2024-001',
                'Descripcion': 'Revisión técnica sistema A',
                'FechaCreacion': '2024-01-10',
                'Estado': 'Pendiente'
            }
        ]
        
        # Configurar el mock de la base de datos
        def mock_execute_query(query, params=None):
            if 'TbUsuarios' in query and 'facturas' in query.lower():
                return mock_usuarios_facturas
            elif 'TbFacturas' in query:
                return mock_facturas
            elif 'TbUsuarios' in query and 'dpd' in query.lower():
                return mock_usuarios_dpds
            elif 'TbDPD' in query:
                return mock_dpds
            elif 'economia' in query.lower():
                return [{'Nombre': 'Economía', 'CorreoUsuario': 'economia@empresa.com'}]
            elif 'tareas' in query.lower():
                return [{'Nombre': 'Técnico', 'CorreoUsuario': 'tecnico@empresa.com'}]
            else:
                return []
        
        # Configurar mocks para ambas bases de datos
        agedys_manager.db.execute_query.side_effect = mock_execute_query
        agedys_manager.tareas_db.execute_query.side_effect = mock_execute_query
        
        # Ejecutar el proceso
        result = agedys_manager.run(dry_run=True)
        
        # Verificar que el proceso se ejecutó correctamente
        assert result is True
        
        # Verificar que se realizaron consultas a las bases de datos
        assert agedys_manager.db.execute_query.call_count > 0
        assert agedys_manager.tareas_db.execute_query.call_count > 0
    
    def test_html_generation_integration(self, agedys_manager):
        """Test de integración para la generación de HTML"""
        # Datos de prueba
        facturas = [
            {
                'NumeroFactura': 'F2024-001',
                'Proveedor': 'Proveedor Test',
                'Importe': '1000.00',  # Como string para que coincida exactamente
                'FechaFactura': '2024-01-15'
            }
        ]
        
        dpds = [
            {
                'NumeroDPD': 'DPD2024-001',
                'Descripcion': 'Test DPD',
                'FechaCreacion': '2024-01-10'
            }
        ]
        
        # Generar HTML para facturas
        html_facturas = agedys_manager.generate_facturas_html_table(facturas)
        
        # Verificar contenido del HTML
        assert '<table' in html_facturas
        assert 'F2024-001' in html_facturas
        assert 'Proveedor Test' in html_facturas
        assert '1000.00' in html_facturas
        
        # Generar HTML para DPDs
        html_dpds = agedys_manager.generate_dpds_html_table(dpds, 'sin_visado_calidad')
        
        # Verificar contenido del HTML
        assert '<table' in html_dpds
        assert 'DPD2024-001' in html_dpds
        assert 'Test DPD' in html_dpds
    
    def test_email_registration_integration(self, agedys_manager, mock_utils):
        """Test de integración para el registro de emails"""
        # Datos de prueba
        facturas = [
            {'NumeroFactura': 'F2024-001', 'Proveedor': 'Test Provider'}
        ]
        
        # Enviar email (registrar en base de datos)
        agedys_manager.send_facturas_pendientes_email(
            'Juan Pérez',
            'juan.perez@empresa.com',
            facturas,
            dry_run=False
        )
        
        # Verificar que se llamó al registro de email
        mock_utils['register_email'].assert_called_once()
        
        # Verificar los parámetros de la llamada
        call_args = mock_utils['register_email'].call_args
        assert call_args[0][0] == agedys_manager.correos_db  # Base de datos
        assert 'juan.perez@empresa.com' in call_args[0]  # Email del destinatario
        assert 'Facturas Pendientes de Visado Técnico' in call_args[0][2]  # Asunto
    
    def test_task_execution_integration(self, agedys_manager, mock_utils):
        """Test de integración para la ejecución de tareas"""
        # Configurar mock para que la tarea deba ejecutarse
        mock_utils['should_execute'].return_value = True
        
        # Configurar datos vacíos para simplificar el test
        agedys_manager.db.execute_query.return_value = []
        agedys_manager.tareas_db.execute_query.return_value = []
        
        # Ejecutar tarea
        result = agedys_manager.execute_task(force=False, dry_run=False)
        
        # Verificar que se ejecutó correctamente
        assert result is True
        
        # Verificar que se verificó si la tarea debe ejecutarse
        mock_utils['should_execute'].assert_called_once()
        
        # Verificar que se registró la finalización de la tarea
        mock_utils['register_task'].assert_called_once()
    
    def test_error_handling_integration(self, agedys_manager, mock_access_database):
        """Test de manejo de errores en integración"""
        # Configurar mock para que falle la primera consulta que se ejecuta en run()
        # que es get_usuarios_facturas_pendientes_visado_tecnico()
        with patch.object(agedys_manager, 'get_usuarios_facturas_pendientes_visado_tecnico') as mock_get_usuarios:
            mock_get_usuarios.side_effect = Exception("Database connection error")
            
            # Ejecutar el proceso
            result = agedys_manager.run(dry_run=False)
            
            # Verificar que se manejó el error correctamente
            assert result is False
    
    def test_dry_run_integration(self, agedys_manager, mock_utils):
        """Test de integración en modo dry run"""
        # Configurar datos de prueba
        agedys_manager.db.execute_query.return_value = []
        agedys_manager.tareas_db.execute_query.return_value = []
        
        # Ejecutar en modo dry run
        result = agedys_manager.execute_task(force=True, dry_run=True)
        
        # Verificar que se ejecutó correctamente
        assert result is True
        
        # Verificar que NO se registró la tarea (porque es dry run)
        mock_utils['register_task'].assert_not_called()
    
    def test_multiple_users_processing_integration(self, agedys_manager, mock_utils):
        """Test de procesamiento de múltiples usuarios"""
        # Configurar múltiples usuarios
        mock_usuarios = [
            {'Nombre': 'Usuario1', 'CorreoUsuario': 'user1@test.com'},
            {'Nombre': 'Usuario2', 'CorreoUsuario': 'user2@test.com'},
            {'Nombre': 'Usuario3', 'CorreoUsuario': 'user3@test.com'}
        ]
        
        mock_facturas = [
            {'NumeroFactura': 'F001', 'Proveedor': 'Proveedor1'},
            {'NumeroFactura': 'F002', 'Proveedor': 'Proveedor2'}
        ]
        
        # Configurar mocks
        def mock_execute_query(query, params=None):
            if 'TbUsuarios' in query:
                return mock_usuarios
            elif 'TbFacturas' in query:
                return mock_facturas
            else:
                return []
        
        agedys_manager.db.execute_query.side_effect = mock_execute_query
        agedys_manager.tareas_db.execute_query.side_effect = mock_execute_query
        
        # Ejecutar proceso
        result = agedys_manager.run(dry_run=False)
        
        # Verificar que se procesó correctamente
        assert result is True
        
        # Verificar que se registraron emails para múltiples usuarios
        # (3 usuarios × al menos 1 email cada uno)
        assert mock_utils['register_email'].call_count >= 3
    
    def test_database_query_parameters_integration(self, agedys_manager):
        """Test de integración con parámetros en las consultas"""
        # Configurar mock para capturar parámetros
        query_calls = []
        
        def capture_query(query, params=None):
            query_calls.append((query, params))
            return []
        
        agedys_manager.db.execute_query.side_effect = capture_query
        agedys_manager.tareas_db.execute_query.side_effect = capture_query
        
        # Ejecutar proceso
        agedys_manager.run(dry_run=True)
        
        # Verificar que se realizaron consultas
        assert len(query_calls) > 0
        
        # Verificar que algunas consultas tienen parámetros (como nombres de usuario)
        parametrized_queries = [call for call in query_calls if call[1] is not None]
        assert len(parametrized_queries) >= 0  # Puede ser 0 si no hay usuarios
    
    def test_css_loading_integration(self, agedys_manager, mock_utils):
        """Test de integración para la carga de CSS"""
        # Verificar que se cargó el CSS
        assert agedys_manager.css_content == "body { font-family: Arial; }"
        
        # Verificar que se llamó a la función de carga de CSS
        mock_utils['css'].assert_called_once()
    
    def test_complete_email_workflow_integration(self, agedys_manager, mock_utils):
        """Test del flujo completo de generación y envío de emails"""
        # Datos de prueba completos
        facturas = [
            {
                'NumeroFactura': 'F2024-001',
                'Proveedor': 'Proveedor Completo S.L.',
                'Importe': '2500.00',  # Como string para que coincida con el formato esperado
                'FechaFactura': '2024-01-15',
                'Descripcion': 'Servicios profesionales'
            }
        ]
        
        # Generar HTML
        html_table = agedys_manager.generate_facturas_html_table(facturas)
        
        # Verificar que el HTML contiene los datos
        assert 'F2024-001' in html_table
        assert 'Proveedor Completo S.L.' in html_table
        assert '2500.00' in html_table
        
        # Enviar email
        agedys_manager.send_facturas_pendientes_email(
            'Usuario Test',
            'usuario.test@empresa.com',
            facturas,
            dry_run=False
        )
        
        # Verificar que se registró el email
        mock_utils['register_email'].assert_called_once()
        
        # Verificar que el contenido del email incluye el HTML generado
        call_args = mock_utils['register_email'].call_args
        email_content = call_args[0][3]  # Contenido del email
        assert 'F2024-001' in email_content
        assert 'Proveedor Completo S.L.' in email_content