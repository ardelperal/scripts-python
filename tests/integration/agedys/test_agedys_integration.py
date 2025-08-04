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
        with patch('src.agedys.agedys_manager.config') as mock_config:
            mock_config.db_agedys_path = "test_agedys.mdb"
            mock_config.db_tareas_path = "test_tareas.mdb"
            mock_config.db_correos_path = "test_correos.mdb"
            mock_config.css_file_path = "test.css"
            mock_config.get_db_agedys_connection_string.return_value = "test_agedys.mdb"
            mock_config.get_db_tareas_connection_string.return_value = "test_tareas.mdb"
            mock_config.get_db_correos_connection_string.return_value = "test_correos.mdb"
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
        with patch('src.agedys.agedys_manager.utils') as mock_utils_module, \
             patch('src.common.utils.load_css_content') as mock_css, \
             patch('src.common.utils.generate_html_header') as mock_header, \
             patch('src.common.utils.generate_html_footer') as mock_footer, \
             patch('src.common.utils.should_execute_task') as mock_should_execute, \
             patch('src.common.utils.register_task_completion') as mock_register_task, \
             patch('src.common.utils.register_email_in_database') as mock_register_email, \
        patch('src.agedys.agedys_manager.get_quality_users') as mock_quality_users, \
        patch('src.common.utils.get_technical_users') as mock_technical_users, \
        patch('src.agedys.agedys_manager.get_economy_users') as mock_economy_users:
            
            mock_css.return_value = "body { font-family: Arial; }"
            # Configurar mock_header para aceptar dos parámetros (title y css_content)
            def mock_header_func(title, css_content):
                return f"<html><head><title>{title}</title><style>{css_content}</style></head><body>"
            mock_header.side_effect = mock_header_func
            mock_footer.return_value = "</body></html>"
            
            # Configurar el mock del módulo utils
            mock_register_email = Mock(return_value=True)
            mock_utils_module.register_email_in_database = mock_register_email
            
            mock_should_execute.return_value = True
            mock_register_task.return_value = True
            
            # Configurar mocks de usuarios
            mock_quality_users.return_value = [
                {'UsuarioRed': 'calidad1', 'Nombre': 'Usuario Calidad 1', 'CorreoUsuario': 'calidad1@test.com'}
            ]
            mock_technical_users.return_value = [
                {'UsuarioRed': 'tecnico1', 'Nombre': 'Usuario Técnico 1', 'CorreoUsuario': 'tecnico1@test.com'}
            ]
            mock_economy_users.return_value = [
                {'UsuarioRed': 'economia1', 'Nombre': 'Usuario Economía 1', 'CorreoUsuario': 'economia1@test.com'}
            ]
            
            yield {
                'css': mock_css,
                'header': mock_header,
                'footer': mock_footer,
                'register_email_in_database': mock_register_email,
                'should_execute_task': mock_should_execute,
                'register_task_completion': mock_register_task,
                'get_quality_users': mock_quality_users,
                'get_technical_users': mock_technical_users,
                'get_economy_users': mock_economy_users
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
        
        # Verificar que se crearon 2 instancias de AccessDatabase (correos_db es referencia a tareas_db)
        assert mock_access_database.call_count == 2
    
    @patch('src.common.utils.get_technical_users')
    @patch('src.agedys.agedys_manager.get_economy_users')
    @patch('src.agedys.agedys_manager.get_quality_users')
    def test_full_workflow_with_data(self, mock_get_quality_users, mock_get_economy_users, mock_get_technical_users, agedys_manager, mock_access_database, mock_utils):
        """Test de integración del flujo completo con datos"""
        # Configurar datos de prueba que coincidan con los campos reales de las consultas SQL
        mock_facturas = [
            {
                'NFactura': 'F001',
                'NDOCUMENTO': 'DOC001',
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'Proveedor Test',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'Descripción test',
                'IMPORTEADJUDICADO': 1000.00,
                'Suministrador': 'Suministrador Test',
                'ImporteFactura': 1000.00
            }
        ]
        
        mock_dpds_sin_visado = [
            {
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'usuario1',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'DPD Test',
                'IMPORTEADJUDICADO': 500.00
            }
        ]
        
        mock_dpds_calidad = [
            {
                'CODPROYECTOS': 'DPD002',
                'DESCRIPCION': 'DPD Calidad Test',
                'PETICIONARIO': 'usuario2',
                'FREGISTRO': '2024-01-01',
                'IMPORTESINIVA': 1000.00
            }
        ]
        
        mock_usuarios_facturas = [
            {'UsuarioRed': 'usuario1', 'CorreoUsuario': 'usuario1@test.com'}
        ]
        
        mock_usuarios_dpds = [
            {'UsuarioRed': 'usuario1', 'CorreoUsuario': 'usuario1@test.com'}
        ]
        
        # Configurar usuarios de calidad, economía y técnicos usando las funciones de utils
        mock_get_quality_users.return_value = [
            {'UsuarioRed': 'calidad1', 'Nombre': 'Usuario Calidad', 'CorreoUsuario': 'calidad1@test.com'}
        ]
        mock_get_economy_users.return_value = [
            {'UsuarioRed': 'economia1', 'Nombre': 'Usuario Economía', 'CorreoUsuario': 'economia1@test.com'}
        ]
        mock_get_technical_users.return_value = [
            {'UsuarioRed': 'tecnico1', 'Nombre': 'Usuario Técnico', 'CorreoUsuario': 'tecnico1@test.com'}
        ]
        
        # Configurar mock de base de datos para devolver datos según la consulta
        def mock_db_query(query, *args):
            # Consultas de usuarios con facturas pendientes (4 queries diferentes)
            if ('TbUsuariosAplicaciones' in query and 'UsuarioRed' in query and 
                ('TbFacturasDetalle' in query or 'TbProyectos' in query)):
                return mock_usuarios_facturas
            # Consultas de facturas pendientes (4 queries diferentes)
            elif ('TbFacturasDetalle' in query and 'NFactura' in query):
                return mock_facturas
            # Consultas específicas para calidad - DPDs sin visado
            elif ('TbProyectos' in query and 'TbVisadosGenerales' in query and 
                  'LEFT JOIN' in query and 'IS NULL' in query):
                return mock_dpds_calidad
            # Consultas específicas para calidad - DPDs rechazados
            elif ('TbProyectos' in query and 'TbVisadosGenerales' in query and 
                  'INNER JOIN' in query and 'Rechazado' in query):
                return mock_dpds_calidad
            # Consultas de DPDs sin visado para calidad (genérica)
            elif 'TbProyectos' in query and 'CODPROYECTOS' in query and 'TbVisadosGenerales' not in query:
                return mock_dpds_sin_visado
            # Consultas de DPDs sin pedido para economía
            elif ('TbProyectos' in query and 'FFINAGENDATECNICA' in query and 
                  'FRECEPCIONECONOMICA' in query):
                return mock_dpds_calidad  # Usar los mismos datos para economía
            # Consulta de ID de usuario
            elif 'SELECT Id FROM TbUsuariosAplicaciones' in query:
                return [{'Id': 118}]
            # Consultas de usuarios técnicos
            elif 'TbUsuariosAplicaciones' in query and 'UsuarioRed' in query:
                return [{'UsuarioRed': 'tecnico1', 'CorreoUsuario': 'tecnico1@test.com'}]
            return []
        
        agedys_manager.db.execute_query.side_effect = mock_db_query
        agedys_manager.tareas_db.execute_query.side_effect = mock_db_query
        
        # Ejecutar el proceso completo (sin dry_run para que registre emails)
        result = agedys_manager.run(dry_run=False)
        
        # Verificar que el proceso se ejecutó correctamente
        assert result is True
        
        # Verificar que se registraron emails en la base de datos (no se enviaron por SMTP)
        # Imprimir para debug
        print(f"Mock call count: {mock_utils['register_email_in_database'].call_count}")
        print(f"Mock calls: {mock_utils['register_email_in_database'].call_args_list}")
        print(f"Quality users mock called: {mock_get_quality_users.called}")
        print(f"Economy users mock called: {mock_get_economy_users.called}")
        print(f"Technical users mock called: {mock_get_technical_users.called}")
        
        # Verificar que se llamó al menos una vez
        mock_utils['register_email_in_database'].assert_called()
    
    def test_html_generation_integration(self, agedys_manager):
        """Test de integración para la generación de HTML"""
        # Datos de prueba con los campos correctos que espera el código
        facturas = [
            {
                'NFactura': 'F2024-001',
                'NDOCUMENTO': 'DOC001',
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'Proveedor Test',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'Descripción test',
                'IMPORTEADJUDICADO': 1000.00,
                'Suministrador': 'Suministrador Test',
                'ImporteFactura': 1000.00
            }
        ]
        
        dpds = [
            {
                'CODPROYECTOS': 'DPD2024-001',
                'PETICIONARIO': 'Peticionario Test',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'Test DPD',
                'IMPORTEADJUDICADO': 500.00,
                'Suministrador': 'Suministrador DPD'
            }
        ]
        
        # Generar HTML para facturas
        html_facturas = agedys_manager.generate_facturas_html_table(facturas)
        
        # Verificar contenido del HTML
        assert '<table' in html_facturas
        assert 'F2024-001' in html_facturas
        assert 'Proveedor Test' in html_facturas
        assert '1000.00€' in html_facturas
        
        # Generar HTML para DPDs
        html_dpds = agedys_manager.generate_dpds_html_table(dpds, 'sin_visado_calidad')
        
        # Verificar contenido del HTML
        assert '<table' in html_dpds
        assert 'DPD2024-001' in html_dpds
        assert 'Test DPD' in html_dpds
    
    def test_notification_registration_integration(self, agedys_manager, mock_utils):
        """Test de integración para el registro de notificaciones"""
        # Datos de prueba con los campos correctos
        facturas = [
            {
                'NFactura': 'F2024-001',
                'NDOCUMENTO': 'DOC001',
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'Test Provider',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'Descripción test',
                'IMPORTEADJUDICADO': 1000.00,
                'Suministrador': 'Suministrador Test',
                'ImporteFactura': 1000.00
            }
        ]
        
        # Registrar notificación (guardar en base de datos)
        agedys_manager.register_facturas_pendientes_notification(
            'Juan Pérez',
            'juan.perez@empresa.com',
            facturas,
            dry_run=False
        )
        
        # Verificar que se llamó al registro de notificación
        mock_utils['register_email_in_database'].assert_called_once()
        
        # Verificar los parámetros de la llamada
        call_args = mock_utils['register_email_in_database'].call_args
        assert call_args[0][0] == agedys_manager.correos_db  # Base de datos
        assert call_args[0][1] == "AGEDYS"  # Aplicación
        assert 'Facturas Pendientes de Visado Técnico' in call_args[0][2]  # Asunto
        assert 'juan.perez@empresa.com' in call_args[0][4]  # Email del destinatario
    
    def test_task_execution_integration(self, agedys_manager, mock_utils):
        """Test de integración para la ejecución de tareas"""
        # Configurar datos vacíos para simplificar el test
        agedys_manager.db.execute_query.return_value = []
        agedys_manager.tareas_db.execute_query.return_value = []
        
        # Ejecutar tarea con force=True para evitar verificaciones de tiempo
        result = agedys_manager.execute_task(force=True, dry_run=True)
        
        # Verificar que se ejecutó correctamente
        assert result is True
    
    def test_error_handling_integration(self, agedys_manager, mock_utils):
        """Test de integración para el manejo de errores"""
        # Configurar datos para que haya algo que procesar
        mock_utils['get_quality_users'].return_value = [
            {'UsuarioRed': 'calidad1', 'Nombre': 'Usuario Calidad 1', 'CorreoUsuario': 'calidad1@test.com'}
        ]
        
        # Configurar datos de DPDs para que process_calidad_tasks tenga algo que procesar
        agedys_manager.db.execute_query.return_value = [
            {'CODPROYECTOS': 'DPD001', 'DESCRIPCION': 'Test DPD', 'PETICIONARIO': 'test', 'FREGISTRO': '2024-01-01', 'IMPORTESINIVA': 1000}
        ]
        
        # Configurar mock para register_email_in_database que es lo que realmente falla
        mock_utils['register_email_in_database'].side_effect = Exception("Error registrando email")
        
        # Ejecutar tarea SIN dry_run para que realmente llame a register_email_in_database
        result = agedys_manager.run(dry_run=False)
        
        # Verificar que retorna False cuando hay error
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
        mock_utils['register_task_completion'].assert_not_called()
    
    @patch('src.common.utils.get_technical_users')
    @patch('src.agedys.agedys_manager.get_economy_users')
    @patch('src.agedys.agedys_manager.get_quality_users')
    def test_multiple_users_processing_integration(self, mock_get_quality_users, mock_get_economy_users, mock_get_technical_users, agedys_manager, mock_utils):
        """Test de integración para el procesamiento de múltiples usuarios"""
        # Configurar mocks de usuarios
        mock_get_quality_users.return_value = [
            {'UsuarioRed': 'usuario_calidad', 'CorreoUsuario': 'calidad@test.com'}
        ]
        mock_get_economy_users.return_value = [
            {'UsuarioRed': 'usuario_economia', 'CorreoUsuario': 'economia@test.com'}
        ]
        mock_get_technical_users.return_value = [
            {'UsuarioRed': 'usuario_tecnico', 'CorreoUsuario': 'tecnico@test.com'}
        ]
        # Configurar datos de prueba con múltiples usuarios usando campos reales
        mock_facturas = [
            {
                'NFactura': 'F001',
                'NDOCUMENTO': 'DOC001',
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'Proveedor Test 1',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'Descripción test 1',
                'IMPORTEADJUDICADO': 1000.00,
                'Suministrador': 'Suministrador Test 1',
                'ImporteFactura': 1000.00
            },
            {
                'NFactura': 'F002',
                'NDOCUMENTO': 'DOC002',
                'CODPROYECTOS': 'DPD002',
                'PETICIONARIO': 'Proveedor Test 2',
                'CodExp': 'EXP002',
                'DESCRIPCION': 'Descripción test 2',
                'IMPORTEADJUDICADO': 2000.00,
                'Suministrador': 'Suministrador Test 2',
                'ImporteFactura': 2000.00
            }
        ]
        
        mock_dpds_sin_visado = [
            {
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'user1',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'DPD Test 1',
                'IMPORTEADJUDICADO': 500.00
            },
            {
                'CODPROYECTOS': 'DPD002',
                'PETICIONARIO': 'user2',
                'CodExp': 'EXP002',
                'DESCRIPCION': 'DPD Test 2',
                'IMPORTEADJUDICADO': 750.00
            }
        ]
        
        mock_dpds_calidad = [
            {
                'CODPROYECTOS': 'DPD003',
                'DESCRIPCION': 'DPD Calidad Test',
                'PETICIONARIO': 'usuario_calidad',
                'FREGISTRO': '2024-01-01',
                'IMPORTESINIVA': 1000.00
            }
        ]
        
        mock_usuarios_facturas = [
            {'UsuarioRed': 'user1', 'CorreoUsuario': 'user1@test.com'},
            {'UsuarioRed': 'user2', 'CorreoUsuario': 'user2@test.com'}
        ]
        
        mock_usuarios_dpds = [
            {'UsuarioRed': 'user1', 'CorreoUsuario': 'user1@test.com'},
            {'UsuarioRed': 'user2', 'CorreoUsuario': 'user2@test.com'}
        ]
        
        # Configurar mock de base de datos para devolver datos según la consulta
        def mock_db_query(query, *args):
            # Consultas de DPDs sin visado de calidad (get_all_dpds_sin_visado_calidad)
            if ('TbProyectos' in query and 'TbVisadosGenerales' in query and 
                'ROFechaRechazo IS NULL' in query and 'ROFechaVisado IS NULL' in query and
                'FechaFinAgendaTecnica IS NULL' in query):
                return mock_dpds_calidad
            # Consultas de DPDs rechazados por calidad (get_all_dpds_rechazados_calidad)
            elif ('TbProyectos' in query and 'TbVisadosGenerales' in query and 
                  'ROFechaRechazo IS NOT NULL' in query):
                return mock_dpds_calidad
            # Consultas de DPDs fin agenda técnica por recepcionar (get_dpds_fin_agenda_tecnica_por_recepcionar)
            elif ('TbProyectos' in query and 'ELIMINADO = False' in query and 
                  'FECHARECEPCIONECONOMICA IS NULL' in query and 
                  'FechaFinAgendaTecnica IS NOT NULL' in query):
                return mock_dpds_sin_visado
            # Consultas de usuarios con facturas pendientes
            elif 'TbFacturasDetalle' in query and 'UsuarioRed' in query:
                return mock_usuarios_facturas
            # Consultas de facturas pendientes
            elif 'TbFacturasDetalle' in query and 'NFactura' in query:
                return mock_facturas
            # Consulta de ID de usuario
            elif 'SELECT Id FROM TbUsuariosAplicaciones' in query:
                return [{'Id': 118}]
            return []
        
        agedys_manager.db.execute_query.side_effect = mock_db_query
        agedys_manager.tareas_db.execute_query.side_effect = mock_db_query
        
        # Ejecutar el proceso (sin dry_run para que registre emails)
        result = agedys_manager.run(dry_run=False)
        
        # Verificar que se procesó correctamente
        assert result is True
        
        # Verificar que se registraron emails (mock_utils['register_email_in_database'] debería haberse llamado)
        assert mock_utils['register_email_in_database'].call_count > 0
    
    @patch('src.common.utils.get_technical_users')
    @patch('src.agedys.agedys_manager.get_economy_users')
    @patch('src.common.utils.get_quality_users')
    def test_database_query_parameters_integration(self, mock_get_quality_users, mock_get_economy_users, mock_get_technical_users, agedys_manager, mock_utils):
        """Test de integración para verificar parámetros de consultas de base de datos"""
        # Configurar mocks de usuarios que coincidan con los datos de las consultas
        mock_get_quality_users.return_value = [
            {'UsuarioRed': 'testuser', 'CorreoUsuario': 'testuser@test.com'}
        ]
        mock_get_economy_users.return_value = [
            {'UsuarioRed': 'testuser', 'CorreoUsuario': 'testuser@test.com'}
        ]
        mock_get_technical_users.return_value = [
            {'UsuarioRed': 'testuser', 'CorreoUsuario': 'testuser@test.com'}
        ]
        # Configurar datos de prueba usando campos reales
        mock_facturas = [
            {
                'NFactura': 'F001',
                'NDOCUMENTO': 'DOC001',
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'Proveedor Test',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'Descripción test',
                'IMPORTEADJUDICADO': 1000.00,
                'Suministrador': 'Suministrador Test',
                'ImporteFactura': 1000.00
            }
        ]
        
        mock_dpds_calidad = [
            {
                'CODPROYECTOS': 'DPD003',
                'DESCRIPCION': 'DPD Calidad Test',
                'PETICIONARIO': 'testuser',
                'FREGISTRO': '2024-01-01',
                'IMPORTESINIVA': 1000.00
            }
        ]
        
        mock_dpds_sin_visado = [
            {
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'testuser',
                'FECHAPETICION': '2024-01-01',
                'EXPEDIENTE': 'EXP001',
                'DESCRIPCION': 'DPD Test'
            }
        ]

        mock_usuarios_facturas = [
            {'UsuarioRed': 'testuser', 'CorreoUsuario': 'testuser@test.com'}
        ]
        
        # Configurar mock de base de datos
        def mock_db_query(query, *args):
            # Consultas de DPDs sin visado de calidad (get_all_dpds_sin_visado_calidad)
            if ('TbProyectos' in query and 'TbVisadosGenerales' in query and 
                'ROFechaRechazo IS NULL' in query and 'ROFechaVisado IS NULL' in query and
                'FechaFinAgendaTecnica IS NULL' in query):
                return mock_dpds_calidad
            # Consultas de DPDs rechazados por calidad (get_all_dpds_rechazados_calidad)
            elif ('TbProyectos' in query and 'TbVisadosGenerales' in query and 
                  'ROFechaRechazo IS NOT NULL' in query):
                return mock_dpds_calidad
            # Consultas de DPDs fin agenda técnica por recepcionar (get_dpds_fin_agenda_tecnica_por_recepcionar)
            elif ('TbProyectos' in query and 'ELIMINADO = False' in query and 
                  'FECHARECEPCIONECONOMICA IS NULL' in query and 
                  'FechaFinAgendaTecnica IS NOT NULL' in query):
                return mock_dpds_sin_visado
            # Consultas de DPDs sin pedido (get_dpds_sin_pedido)
            elif ('TbProyectos' in query and 'TbNPedido' in query and 'NPEDIDO IS NULL' in query):
                return mock_dpds_sin_visado
            # Consultas de usuarios con facturas pendientes
            elif 'TbFacturasDetalle' in query and 'UsuarioRed' in query:
                return mock_usuarios_facturas
            # Consultas de facturas pendientes
            elif 'TbFacturasDetalle' in query and 'NFactura' in query:
                return mock_facturas
            # Consulta de ID de usuario
            elif 'SELECT Id FROM TbUsuariosAplicaciones' in query:
                return [{'Id': 118}]
            return []
        
        agedys_manager.db.execute_query.side_effect = mock_db_query
        agedys_manager.tareas_db.execute_query.side_effect = mock_db_query
        
        # Ejecutar consultas específicas usando métodos reales de AgedysManager
        usuarios = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
        facturas = agedys_manager.get_facturas_pendientes_visado_tecnico('testuser')
        
        # Verificar que se obtuvieron datos
        assert len(usuarios) > 0
        assert len(facturas) > 0
        
        # Verificar estructura de datos
        assert 'UsuarioRed' in usuarios[0]
        assert 'CorreoUsuario' in usuarios[0]
        assert 'NFactura' in facturas[0]
        assert 'Suministrador' in facturas[0]
        
        # Ejecutar el proceso completo para verificar que se registran emails
        result = agedys_manager.run(dry_run=False)
        assert result is True
        
        # Verificar que se registraron emails
        print(f"Mock call count: {mock_utils['register_email_in_database'].call_count}")
        print(f"Mock calls: {mock_utils['register_email_in_database'].call_args_list}")
        assert mock_utils['register_email_in_database'].call_count > 0
    
    def test_css_loading_integration(self, mock_utils):
        """Test de integración para la carga de CSS"""
        # Crear una nueva instancia de AgedysManager después de configurar los mocks
        with patch('src.agedys.agedys_manager.AccessDatabase'), \
             patch('src.agedys.agedys_manager.load_css_content') as mock_css_load:
            
            # Configurar el mock para devolver CSS simplificado
            mock_css_load.return_value = "body { font-family: Arial; }"
            
            agedys_manager = AgedysManager()
            
            # Verificar que el CSS se cargó correctamente
            expected_css = "body { font-family: Arial; }"
            assert agedys_manager.css_content == expected_css
            
            # Verificar que se llamó a la función de carga de CSS
            mock_css_load.assert_called_once()
    
    def test_complete_notification_workflow_integration(self, agedys_manager, mock_utils):
        """Test del flujo completo de generación y registro de notificaciones"""
        # Datos de prueba completos con los campos correctos
        facturas = [
            {
                'NFactura': 'F2024-001',
                'NDOCUMENTO': 'DOC001',
                'CODPROYECTOS': 'DPD001',
                'PETICIONARIO': 'Proveedor Completo S.L.',
                'CodExp': 'EXP001',
                'DESCRIPCION': 'Servicios profesionales',
                'IMPORTEADJUDICADO': 2500.00,
                'Suministrador': 'Suministrador Test',
                'ImporteFactura': 2500.00
            }
        ]
        
        # Generar HTML
        html_table = agedys_manager.generate_facturas_html_table(facturas)
        
        # Verificar que el HTML contiene los datos
        assert 'F2024-001' in html_table
        assert 'Proveedor Completo S.L.' in html_table
        assert '2500.00€' in html_table
        
        # Registrar notificación
        agedys_manager.register_facturas_pendientes_notification(
            'Usuario Test',
            'usuario.test@empresa.com',
            facturas,
            dry_run=False
        )
        
        # Verificar que se registró la notificación
        mock_utils['register_email_in_database'].assert_called_once()
        
        # Verificar que el contenido de la notificación incluye el HTML generado
        call_args = mock_utils['register_email_in_database'].call_args
        notification_content = call_args[0][3]  # Contenido de la notificación
        assert 'F2024-001' in notification_content
        assert 'Proveedor Completo S.L.' in notification_content