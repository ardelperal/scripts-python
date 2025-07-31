"""
Tests unitarios para AgedysManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from src.agedys.agedys_manager import AgedysManager


class TestAgedysManager:
    """Tests para la clase AgedysManager"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de configuración"""
        with patch('src.agedys.agedys_manager.config') as mock_config:
            mock_config.get_db_agedys_connection_string.return_value = "mock_agedys_conn"
            mock_config.get_db_tareas_connection_string.return_value = "mock_tareas_conn"
            mock_config.get_db_correos_connection_string.return_value = "mock_correos_conn"
            mock_config.css_file_path = "mock_css_path"
            yield mock_config
    
    @pytest.fixture
    def mock_access_database(self):
        """Mock de AccessDatabase"""
        with patch('src.agedys.agedys_manager.AccessDatabase') as mock_db:
            yield mock_db
    
    @pytest.fixture
    def mock_utils(self):
        """Mock de utilidades"""
        with patch('src.agedys.agedys_manager.load_css_content') as mock_css, \
             patch('src.agedys.agedys_manager.generate_html_header') as mock_header, \
             patch('src.agedys.agedys_manager.generate_html_footer') as mock_footer, \
             patch('src.agedys.agedys_manager.register_email_in_database') as mock_register_email, \
             patch('src.agedys.agedys_manager.should_execute_task') as mock_should_execute, \
             patch('src.agedys.agedys_manager.register_task_completion') as mock_register_task:
            
            mock_css.return_value = "mock_css_content"
            mock_header.return_value = "<html><head></head><body>"
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
    def agedys_manager(self, mock_config, mock_access_database, mock_utils):
        """Instancia de AgedysManager con mocks"""
        return AgedysManager()
    
    def test_init(self, agedys_manager, mock_access_database, mock_config):
        """Test de inicialización"""
        assert agedys_manager.db is not None
        assert agedys_manager.tareas_db is not None
        assert agedys_manager.correos_db is not None
        assert agedys_manager.css_content == "mock_css_content"
    
    def test_get_usuarios_facturas_pendientes_visado_tecnico(self, agedys_manager):
        """Test obtener usuarios con facturas pendientes de visado técnico"""
        mock_users = [
            {'UsuarioRed': 'Usuario1'},
            {'UsuarioRed': 'Usuario2'}
        ]
        expected_result = [
            {'UsuarioRed': 'Usuario1', 'CorreoUsuario': 'Usuario1@telefonica.com'},
            {'UsuarioRed': 'Usuario2', 'CorreoUsuario': 'Usuario2@telefonica.com'}
        ]
        agedys_manager.db.execute_query.return_value = mock_users
        
        result = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
        
        assert result == expected_result
        agedys_manager.db.execute_query.assert_called_once()
    
    def test_get_usuarios_facturas_pendientes_visado_tecnico_exception(self, agedys_manager):
        """Test obtener usuarios con facturas pendientes - excepción"""
        agedys_manager.db.execute_query.side_effect = Exception("DB Error")
        
        result = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
        
        assert result == []
    
    def test_get_facturas_pendientes_visado_tecnico(self, agedys_manager):
        """Test obtener facturas pendientes de visado técnico"""
        mock_facturas = [
            {'NFactura': 'F001', 'Suministrador': 'Proveedor1', 'ImporteFactura': 100.50},
            {'NFactura': 'F002', 'Suministrador': 'Proveedor2', 'ImporteFactura': 200.75}
        ]
        agedys_manager.db.execute_query.return_value = mock_facturas
        
        result = agedys_manager.get_facturas_pendientes_visado_tecnico('Usuario1')
        
        assert result == mock_facturas
        # El método ejecuta hasta 4 queries, pero puede fallar algunas por TbUsuariosAplicaciones
        assert agedys_manager.db.execute_query.call_count >= 2  # Al menos las 2 últimas queries
    
    def test_get_facturas_pendientes_visado_tecnico_exception(self, agedys_manager):
        """Test obtener facturas pendientes - excepción"""
        agedys_manager.db.execute_query.side_effect = Exception("DB Error")
        
        result = agedys_manager.get_facturas_pendientes_visado_tecnico('Usuario1')
        
        assert result == []
    
    def test_get_usuarios_dpds_sin_visado_calidad(self, agedys_manager):
        """Test obtener usuarios con DPDs sin visado de calidad"""
        mock_users = [
            {'Nombre': 'Usuario1', 'CorreoUsuario': 'user1@test.com'},
            {'Nombre': 'Usuario2', 'CorreoUsuario': 'user2@test.com'}
        ]
        agedys_manager.tareas_db.execute_query.return_value = mock_users
        
        result = agedys_manager.get_usuarios_dpds_sin_visado_calidad()
        
        assert result == mock_users
        agedys_manager.tareas_db.execute_query.assert_called_once()
    
    def test_get_dpds_sin_visado_calidad(self, agedys_manager):
        """Test obtener DPDs sin visado de calidad"""
        mock_dpds = [
            {'NumeroDPD': 'DPD001', 'Descripcion': 'DPD Test 1'},
            {'NumeroDPD': 'DPD002', 'Descripcion': 'DPD Test 2'}
        ]
        agedys_manager.db.execute_query.return_value = mock_dpds
        
        result = agedys_manager.get_dpds_sin_visado_calidad('Usuario1')
        
        assert result == mock_dpds
        agedys_manager.db.execute_query.assert_called_once()
    
    def test_get_usuarios_dpds_rechazados_calidad(self, agedys_manager):
        """Test obtener usuarios con DPDs rechazados por calidad"""
        mock_users = [
            {'Nombre': 'Usuario1', 'CorreoUsuario': 'user1@test.com'}
        ]
        agedys_manager.tareas_db.execute_query.return_value = mock_users
        
        result = agedys_manager.get_usuarios_dpds_rechazados_calidad()
        
        assert result == mock_users
        agedys_manager.tareas_db.execute_query.assert_called_once()
    
    def test_get_dpds_rechazados_calidad(self, agedys_manager):
        """Test obtener DPDs rechazados por calidad"""
        mock_dpds = [
            {'NumeroDPD': 'DPD003', 'Descripcion': 'DPD Rechazado', 'FechaRechazo': datetime.now()}
        ]
        agedys_manager.db.execute_query.return_value = mock_dpds
        
        result = agedys_manager.get_dpds_rechazados_calidad('Usuario1')
        
        assert result == mock_dpds
        agedys_manager.db.execute_query.assert_called_once()
    
    def test_get_usuarios_economia(self, agedys_manager):
        """Test obtener usuarios de economía"""
        mock_users = [
            {'Nombre': 'Economia1', 'CorreoUsuario': 'economia1@test.com'}
        ]
        agedys_manager.tareas_db.execute_query.return_value = mock_users
        
        result = agedys_manager.get_usuarios_economia()
        
        assert result == mock_users
        agedys_manager.tareas_db.execute_query.assert_called_once()
    
    def test_get_dpds_fin_agenda_tecnica_por_recepcionar(self, agedys_manager):
        """Test obtener DPDs con fin de agenda técnica por recepcionar"""
        mock_dpds = [
            {'NumeroDPD': 'DPD004', 'Descripcion': 'DPD Fin Agenda'}
        ]
        agedys_manager.db.execute_query.return_value = mock_dpds
        
        result = agedys_manager.get_dpds_fin_agenda_tecnica_por_recepcionar()
        
        assert result == mock_dpds
        agedys_manager.db.execute_query.assert_called_once()
    
    def test_get_usuarios_tareas(self, agedys_manager):
        """Test obtener usuarios de tareas"""
        mock_users = [
            {'Nombre': 'Tecnico1', 'CorreoUsuario': 'tecnico1@test.com'}
        ]
        agedys_manager.tareas_db.execute_query.return_value = mock_users
        
        result = agedys_manager.get_usuarios_tareas()
        
        assert result == mock_users
        agedys_manager.tareas_db.execute_query.assert_called_once()
    
    def test_get_dpds_sin_pedido(self, agedys_manager):
        """Test obtener DPDs sin pedido"""
        mock_dpds = [
            {'NumeroDPD': 'DPD005', 'Descripcion': 'DPD Sin Pedido'}
        ]
        agedys_manager.db.execute_query.return_value = mock_dpds
        
        result = agedys_manager.get_dpds_sin_pedido()
        
        assert result == mock_dpds
        agedys_manager.db.execute_query.assert_called_once()
    
    def test_generate_facturas_html_table_empty(self, agedys_manager):
        """Test generar tabla HTML de facturas vacía"""
        result = agedys_manager.generate_facturas_html_table([])
        
        assert result == "<p>No hay facturas pendientes de visado técnico.</p>"
    
    def test_generate_facturas_html_table_with_data(self, agedys_manager):
        """Test generar tabla HTML de facturas con datos"""
        facturas = [
            {'NFactura': 'F001', 'Suministrador': 'Proveedor1', 'ImporteFactura': 100.50}
        ]
        
        result = agedys_manager.generate_facturas_html_table(facturas)
        
        assert "<table" in result
        assert "F001" in result
        assert "Proveedor1" in result
        assert "100.5" in result
    
    def test_generate_dpds_html_table_empty(self, agedys_manager):
        """Test generar tabla HTML de DPDs vacía"""
        result = agedys_manager.generate_dpds_html_table([], 'sin_visado_calidad')
        
        assert result == "<p>No hay DPDs sin_visado_calidad.</p>"
    
    def test_generate_dpds_html_table_with_data(self, agedys_manager):
        """Test generar tabla HTML de DPDs con datos"""
        dpds = [
            {'NumeroDPD': 'DPD001', 'Descripcion': 'DPD Test'}
        ]
        
        result = agedys_manager.generate_dpds_html_table(dpds, 'sin_visado_calidad')
        
        assert "<table" in result
        assert "DPD001" in result
        assert "DPD Test" in result
    
    def test_send_facturas_pendientes_email_empty(self, agedys_manager, mock_utils):
        """Test enviar email de facturas pendientes - lista vacía"""
        agedys_manager.send_facturas_pendientes_email('Usuario1', 'user1@test.com', [], dry_run=False)
        
        mock_utils['register_email'].assert_not_called()
    
    def test_send_facturas_pendientes_email_with_data(self, agedys_manager, mock_utils):
        """Test enviar email de facturas pendientes con datos"""
        facturas = [{'NumeroFactura': 'F001', 'Proveedor': 'Proveedor1'}]
        
        agedys_manager.send_facturas_pendientes_email('Usuario1', 'user1@test.com', facturas, dry_run=False)
        
        mock_utils['register_email'].assert_called_once()
    
    def test_send_facturas_pendientes_email_dry_run(self, agedys_manager, mock_utils):
        """Test enviar email de facturas pendientes - dry run"""
        facturas = [{'NumeroFactura': 'F001', 'Proveedor': 'Proveedor1'}]
        
        agedys_manager.send_facturas_pendientes_email('Usuario1', 'user1@test.com', facturas, dry_run=True)
        
        mock_utils['register_email'].assert_not_called()
    
    def test_send_dpds_sin_visado_email_empty(self, agedys_manager, mock_utils):
        """Test enviar email de DPDs sin visado - lista vacía"""
        agedys_manager.send_dpds_sin_visado_email('Usuario1', 'user1@test.com', [], dry_run=False)
        
        mock_utils['register_email'].assert_not_called()
    
    def test_send_dpds_sin_visado_email_with_data(self, agedys_manager, mock_utils):
        """Test enviar email de DPDs sin visado con datos"""
        dpds = [{'NumeroDPD': 'DPD001', 'Descripcion': 'DPD Test'}]
        
        agedys_manager.send_dpds_sin_visado_email('Usuario1', 'user1@test.com', dpds, dry_run=False)
        
        mock_utils['register_email'].assert_called_once()
    
    def test_send_dpds_rechazados_email_with_data(self, agedys_manager, mock_utils):
        """Test enviar email de DPDs rechazados con datos"""
        dpds = [{'NumeroDPD': 'DPD002', 'Descripcion': 'DPD Rechazado'}]
        
        agedys_manager.send_dpds_rechazados_email('Usuario1', 'user1@test.com', dpds, dry_run=False)
        
        mock_utils['register_email'].assert_called_once()
    
    def test_send_economia_email_empty_users(self, agedys_manager, mock_utils):
        """Test enviar email a economía - usuarios vacíos"""
        dpds = [{'NumeroDPD': 'DPD003'}]
        
        agedys_manager.send_economia_email([], dpds, dry_run=False)
        
        mock_utils['register_email'].assert_not_called()
    
    def test_send_economia_email_empty_dpds(self, agedys_manager, mock_utils):
        """Test enviar email a economía - DPDs vacíos"""
        usuarios = [{'UsuarioRed': 'Economia1', 'CorreoUsuario': 'economia1@test.com'}]
        
        agedys_manager.send_economia_email(usuarios, [], dry_run=False)
        
        mock_utils['register_email'].assert_not_called()
    
    def test_send_economia_email_with_data(self, agedys_manager, mock_utils):
        """Test enviar email a economía con datos"""
        usuarios = [{'UsuarioRed': 'Economia1', 'CorreoUsuario': 'economia1@test.com'}]
        dpds = [{'NumeroDPD': 'DPD003', 'Descripcion': 'DPD Economia'}]
        
        agedys_manager.send_economia_email(usuarios, dpds, dry_run=False)
        
        mock_utils['register_email'].assert_called_once()
    
    def test_send_dpds_sin_pedido_email_with_data(self, agedys_manager, mock_utils):
        """Test enviar email de DPDs sin pedido con datos"""
        dpds = [{'NumeroDPD': 'DPD004', 'Descripcion': 'DPD Sin Pedido'}]
        
        agedys_manager.send_dpds_sin_pedido_email('Usuario1', 'user1@test.com', dpds, dry_run=False)
        
        mock_utils['register_email'].assert_called_once()
    
    def test_execute_task_should_not_execute(self, agedys_manager, mock_utils):
        """Test ejecutar tarea - no debe ejecutarse"""
        mock_utils['should_execute'].return_value = False
        
        result = agedys_manager.execute_task(force=False, dry_run=False)
        
        assert result is True
    
    def test_execute_task_force_execution(self, agedys_manager, mock_utils):
        """Test ejecutar tarea - forzar ejecución"""
        with patch.object(agedys_manager, 'run') as mock_run:
            mock_run.return_value = True
            
            result = agedys_manager.execute_task(force=True, dry_run=False)
            
            assert result is True
            mock_run.assert_called_once_with(dry_run=False)
            mock_utils['register_task'].assert_called_once()
    
    def test_execute_task_dry_run(self, agedys_manager, mock_utils):
        """Test ejecutar tarea - dry run"""
        with patch.object(agedys_manager, 'run') as mock_run:
            mock_run.return_value = True
            
            result = agedys_manager.execute_task(force=True, dry_run=True)
            
            assert result is True
            mock_run.assert_called_once_with(dry_run=True)
            mock_utils['register_task'].assert_not_called()
    
    def test_execute_task_run_failure(self, agedys_manager, mock_utils):
        """Test ejecutar tarea - fallo en run"""
        with patch.object(agedys_manager, 'run') as mock_run:
            mock_run.return_value = False
            
            result = agedys_manager.execute_task(force=True, dry_run=False)
            
            assert result is False
            mock_utils['register_task'].assert_called_once()
    
    def test_execute_task_exception(self, agedys_manager, mock_utils):
        """Test ejecutar tarea - excepción"""
        with patch.object(agedys_manager, 'run') as mock_run:
            mock_run.side_effect = Exception("Test Error")
            
            result = agedys_manager.execute_task(force=True, dry_run=False)
            
            assert result is False
    
    def test_run_success_complete_flow(self, agedys_manager):
        """Test ejecutar proceso principal - flujo completo exitoso"""
        # Mock de todos los métodos get_usuarios_*
        with patch.object(agedys_manager, 'get_usuarios_facturas_pendientes_visado_tecnico') as mock_get_usuarios_facturas, \
             patch.object(agedys_manager, 'get_facturas_pendientes_visado_tecnico') as mock_get_facturas, \
             patch.object(agedys_manager, 'send_facturas_pendientes_email') as mock_send_facturas, \
             patch.object(agedys_manager, 'get_usuarios_dpds_sin_visado_calidad') as mock_get_usuarios_dpds, \
             patch.object(agedys_manager, 'get_dpds_sin_visado_calidad') as mock_get_dpds, \
             patch.object(agedys_manager, 'send_dpds_sin_visado_email') as mock_send_dpds, \
             patch.object(agedys_manager, 'get_usuarios_dpds_rechazados_calidad') as mock_get_usuarios_rechazados, \
             patch.object(agedys_manager, 'get_dpds_rechazados_calidad') as mock_get_dpds_rechazados, \
             patch.object(agedys_manager, 'send_dpds_rechazados_email') as mock_send_rechazados, \
             patch.object(agedys_manager, 'get_usuarios_economia') as mock_get_economia, \
             patch.object(agedys_manager, 'get_dpds_fin_agenda_tecnica_por_recepcionar') as mock_get_dpds_economia, \
             patch.object(agedys_manager, 'send_economia_email') as mock_send_economia, \
             patch.object(agedys_manager, 'get_usuarios_tareas') as mock_get_usuarios_tareas, \
             patch.object(agedys_manager, 'get_dpds_sin_pedido') as mock_get_dpds_sin_pedido, \
             patch.object(agedys_manager, 'send_dpds_sin_pedido_email') as mock_send_sin_pedido:
            
            # Configurar mocks
            mock_get_usuarios_facturas.return_value = [{'UsuarioRed': 'User1', 'CorreoUsuario': 'user1@test.com'}]
            mock_get_facturas.return_value = [{'NumeroFactura': 'F001'}]
            
            mock_get_usuarios_dpds.return_value = [{'UsuarioRed': 'User2', 'CorreoUsuario': 'user2@test.com'}]
            mock_get_dpds.return_value = [{'NumeroDPD': 'DPD001'}]
            
            mock_get_usuarios_rechazados.return_value = [{'UsuarioRed': 'User3', 'CorreoUsuario': 'user3@test.com'}]
            mock_get_dpds_rechazados.return_value = [{'NumeroDPD': 'DPD002'}]
            
            mock_get_economia.return_value = [{'UsuarioRed': 'Economia1', 'CorreoUsuario': 'economia1@test.com'}]
            mock_get_dpds_economia.return_value = [{'NumeroDPD': 'DPD003'}]
            
            mock_get_usuarios_tareas.return_value = [{'UsuarioRed': 'Tecnico1', 'CorreoUsuario': 'tecnico1@test.com'}]
            mock_get_dpds_sin_pedido.return_value = [{'NumeroDPD': 'DPD004', 'PETICIONARIO': 'Tecnico1'}]
            
            result = agedys_manager.run(dry_run=False)
            
            assert result is True
            
            # Verificar que se llamaron todos los métodos de envío
            mock_send_facturas.assert_called_once()
            mock_send_dpds.assert_called_once()
            mock_send_rechazados.assert_called_once()
            mock_send_economia.assert_called_once()
            mock_send_sin_pedido.assert_called_once()
    
    def test_run_exception(self, agedys_manager):
        """Test ejecutar proceso principal - excepción"""
        with patch.object(agedys_manager, 'get_usuarios_facturas_pendientes_visado_tecnico') as mock_get_usuarios:
            mock_get_usuarios.side_effect = Exception("Test Error")
            
            result = agedys_manager.run(dry_run=False)
            
            assert result is False
    
    def test_run_no_users_or_data(self, agedys_manager):
        """Test ejecutar proceso principal - sin usuarios o datos"""
        with patch.object(agedys_manager, 'get_usuarios_facturas_pendientes_visado_tecnico') as mock_get_usuarios_facturas, \
             patch.object(agedys_manager, 'get_usuarios_dpds_sin_visado_calidad') as mock_get_usuarios_dpds, \
             patch.object(agedys_manager, 'get_usuarios_dpds_rechazados_calidad') as mock_get_usuarios_rechazados, \
             patch.object(agedys_manager, 'get_usuarios_economia') as mock_get_economia, \
             patch.object(agedys_manager, 'get_dpds_fin_agenda_tecnica_por_recepcionar') as mock_get_dpds_economia, \
             patch.object(agedys_manager, 'get_usuarios_tareas') as mock_get_usuarios_tareas:
            
            # Configurar mocks para devolver listas vacías
            mock_get_usuarios_facturas.return_value = []
            mock_get_usuarios_dpds.return_value = []
            mock_get_usuarios_rechazados.return_value = []
            mock_get_economia.return_value = []
            mock_get_dpds_economia.return_value = []
            mock_get_usuarios_tareas.return_value = []
            
            result = agedys_manager.run(dry_run=False)
            
            assert result is True