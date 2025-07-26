"""
Tests unitarios para BrassManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from src.brass.brass_manager import BrassManager


class TestBrassManager:
    """Tests para la clase BrassManager"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de configuración"""
        with patch('src.brass.brass_manager.config') as mock_config:
            mock_config.get_db_brass_connection_string.return_value = "mock_brass_conn"
            mock_config.get_db_tareas_connection_string.return_value = "mock_tareas_conn"
            mock_config.css_file_path = "mock_css_path"
            mock_config.default_recipient = "test@example.com"
            yield mock_config
    
    @pytest.fixture
    def mock_access_database(self):
        """Mock de AccessDatabase"""
        with patch('src.brass.brass_manager.AccessDatabase') as mock_db:
            yield mock_db
    
    @pytest.fixture
    def mock_utils(self):
        """Mock de utilidades"""
        with patch('src.brass.brass_manager.load_css_content') as mock_css, \
             patch('src.brass.brass_manager.generate_html_header') as mock_header, \
             patch('src.brass.brass_manager.generate_html_footer') as mock_footer, \
             patch('src.brass.brass_manager.safe_str') as mock_safe_str:
            
            mock_css.return_value = "mock_css_content"
            mock_header.return_value = "<html><head></head><body>"
            mock_footer.return_value = "</body></html>"
            mock_safe_str.side_effect = lambda x: str(x) if x else ""
            
            yield {
                'css': mock_css,
                'header': mock_header,
                'footer': mock_footer,
                'safe_str': mock_safe_str
            }
    
    @pytest.fixture
    def brass_manager(self, mock_config, mock_access_database, mock_utils):
        """Instancia de BrassManager con mocks"""
        return BrassManager()
    
    def test_init(self, brass_manager, mock_access_database, mock_config):
        """Test de inicialización"""
        assert brass_manager.db_brass is not None
        assert brass_manager.db_tareas is not None
        assert brass_manager.css_content == "mock_css_content"
        assert brass_manager._admin_users is None
        assert brass_manager._admin_emails is None
    
    def test_get_last_execution_date_with_datetime(self, brass_manager):
        """Test obtener última fecha de ejecución con datetime"""
        mock_result = [{'Ultima': datetime(2024, 1, 15, 10, 30)}]
        brass_manager.db_tareas.execute_query.return_value = mock_result
        
        result = brass_manager.get_last_execution_date()
        
        assert result == date(2024, 1, 15)
        brass_manager.db_tareas.execute_query.assert_called_once()
    
    def test_get_last_execution_date_with_date(self, brass_manager):
        """Test obtener última fecha de ejecución con date"""
        mock_result = [{'Ultima': date(2024, 1, 15)}]
        brass_manager.db_tareas.execute_query.return_value = mock_result
        
        result = brass_manager.get_last_execution_date()
        
        assert result == date(2024, 1, 15)
    
    def test_get_last_execution_date_none(self, brass_manager):
        """Test obtener última fecha cuando no existe"""
        brass_manager.db_tareas.execute_query.return_value = [{'Ultima': None}]
        
        result = brass_manager.get_last_execution_date()
        
        assert result is None
    
    def test_get_last_execution_date_empty(self, brass_manager):
        """Test obtener última fecha con resultado vacío"""
        brass_manager.db_tareas.execute_query.return_value = []
        
        result = brass_manager.get_last_execution_date()
        
        assert result is None
    
    def test_get_last_execution_date_exception(self, brass_manager):
        """Test obtener última fecha con excepción"""
        brass_manager.db_tareas.execute_query.side_effect = Exception("DB Error")
        
        result = brass_manager.get_last_execution_date()
        
        assert result is None
    
    def test_is_task_completed_today_true(self, brass_manager):
        """Test verificar si tarea se completó hoy - True"""
        with patch.object(brass_manager, 'get_last_execution_date') as mock_get_date:
            mock_get_date.return_value = date.today()
            
            result = brass_manager.is_task_completed_today()
            
            assert result is True
    
    def test_is_task_completed_today_false(self, brass_manager):
        """Test verificar si tarea se completó hoy - False"""
        with patch.object(brass_manager, 'get_last_execution_date') as mock_get_date:
            mock_get_date.return_value = date(2024, 1, 1)
            
            result = brass_manager.is_task_completed_today()
            
            assert result is False
    
    def test_is_task_completed_today_none(self, brass_manager):
        """Test verificar si tarea se completó hoy - None"""
        with patch.object(brass_manager, 'get_last_execution_date') as mock_get_date:
            mock_get_date.return_value = None
            
            result = brass_manager.is_task_completed_today()
            
            assert result is False
    
    def test_is_calibration_valid_true(self, brass_manager):
        """Test verificar calibración válida"""
        future_date = datetime(2025, 12, 31)
        brass_manager.db_brass.execute_query.return_value = [{'FechaFinCalibracion': future_date}]
        
        result = brass_manager._is_calibration_valid(123)
        
        assert result is True
    
    def test_is_calibration_valid_false_expired(self, brass_manager):
        """Test verificar calibración expirada"""
        past_date = datetime(2020, 1, 1)
        brass_manager.db_brass.execute_query.return_value = [{'FechaFinCalibracion': past_date}]
        
        result = brass_manager._is_calibration_valid(123)
        
        assert result is False
    
    def test_is_calibration_valid_false_no_date(self, brass_manager):
        """Test verificar calibración sin fecha"""
        brass_manager.db_brass.execute_query.return_value = [{'FechaFinCalibracion': None}]
        
        result = brass_manager._is_calibration_valid(123)
        
        assert result is False
    
    def test_is_calibration_valid_false_no_result(self, brass_manager):
        """Test verificar calibración sin resultados"""
        brass_manager.db_brass.execute_query.return_value = []
        
        result = brass_manager._is_calibration_valid(123)
        
        assert result is False
    
    def test_is_calibration_valid_exception(self, brass_manager):
        """Test verificar calibración con excepción"""
        brass_manager.db_brass.execute_query.side_effect = Exception("DB Error")
        
        result = brass_manager._is_calibration_valid(123)
        
        assert result is False
    
    def test_get_equipment_out_of_calibration(self, brass_manager):
        """Test obtener equipos fuera de calibración"""
        mock_equipos = [
            {'IDEquipoMedida': 1, 'NOMBRE': 'Equipo1', 'NS': 'NS1', 'PN': 'PN1', 'MARCA': 'Marca1', 'MODELO': 'Modelo1'},
            {'IDEquipoMedida': 2, 'NOMBRE': 'Equipo2', 'NS': 'NS2', 'PN': 'PN2', 'MARCA': 'Marca2', 'MODELO': 'Modelo2'}
        ]
        brass_manager.db_brass.execute_query.return_value = mock_equipos
        
        with patch.object(brass_manager, '_is_calibration_valid') as mock_is_valid:
            mock_is_valid.side_effect = [False, True]  # Primer equipo sin calibración, segundo válido
            
            result = brass_manager.get_equipment_out_of_calibration()
            
            assert len(result) == 1
            assert result[0]['IDEquipoMedida'] == 1
            assert result[0]['NOMBRE'] == 'Equipo1'
    
    def test_get_equipment_out_of_calibration_exception(self, brass_manager):
        """Test obtener equipos fuera de calibración con excepción"""
        brass_manager.db_brass.execute_query.side_effect = Exception("DB Error")
        
        result = brass_manager.get_equipment_out_of_calibration()
        
        assert result == []
    
    def test_generate_html_report_empty(self, brass_manager):
        """Test generar reporte HTML con lista vacía"""
        result = brass_manager.generate_html_report([])
        
        assert result == ""
    
    def test_generate_html_report_with_equipment(self, brass_manager):
        """Test generar reporte HTML con equipos"""
        equipment_list = [
            {'NOMBRE': 'Equipo1', 'NS': 'NS1', 'PN': 'PN1', 'MARCA': 'Marca1', 'MODELO': 'Modelo1'}
        ]
        
        result = brass_manager.generate_html_report(equipment_list)
        
        assert "<html><head></head><body>" in result
        assert "INFORME DE AVISOS DE EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN" in result
        assert "Equipo1" in result
        assert "</body></html>" in result
    
    def test_get_admin_users_cached(self, brass_manager):
        """Test obtener usuarios admin con cache"""
        cached_users = [{'UsuarioRed': 'user1', 'Nombre': 'User 1', 'CorreoUsuario': 'user1@test.com'}]
        brass_manager._admin_users = cached_users
        
        result = brass_manager.get_admin_users()
        
        assert result == cached_users
        brass_manager.db_tareas.execute_query.assert_not_called()
    
    def test_get_admin_users_from_db(self, brass_manager):
        """Test obtener usuarios admin desde BD"""
        mock_users = [{'UsuarioRed': 'user1', 'Nombre': 'User 1', 'CorreoUsuario': 'user1@test.com'}]
        brass_manager.db_tareas.execute_query.return_value = mock_users
        
        result = brass_manager.get_admin_users()
        
        assert result == mock_users
        assert brass_manager._admin_users == mock_users
    
    def test_get_admin_users_exception(self, brass_manager):
        """Test obtener usuarios admin con excepción"""
        brass_manager.db_tareas.execute_query.side_effect = Exception("DB Error")
        
        result = brass_manager.get_admin_users()
        
        assert result == []
    
    def test_get_admin_emails_string_cached(self, brass_manager):
        """Test obtener emails admin con cache"""
        brass_manager._admin_emails = "user1@test.com;user2@test.com"
        
        result = brass_manager.get_admin_emails_string()
        
        assert result == "user1@test.com;user2@test.com"
    
    def test_get_admin_emails_string_from_users(self, brass_manager):
        """Test obtener emails admin desde usuarios"""
        mock_users = [
            {'CorreoUsuario': 'user1@test.com'},
            {'CorreoUsuario': 'user2@test.com'},
            {'CorreoUsuario': None}  # Usuario sin email
        ]
        
        with patch.object(brass_manager, 'get_admin_users') as mock_get_users:
            mock_get_users.return_value = mock_users
            
            result = brass_manager.get_admin_emails_string()
            
            assert result == "user1@test.com;user2@test.com"
            assert brass_manager._admin_emails == "user1@test.com;user2@test.com"
    
    def test_register_email_success(self, brass_manager):
        """Test registrar email exitoso"""
        brass_manager.db_tareas.get_max_id.return_value = 5
        brass_manager.db_tareas.insert_record.return_value = True
        
        with patch.object(brass_manager, 'get_admin_emails_string') as mock_get_emails:
            mock_get_emails.return_value = "admin@test.com"
            
            result = brass_manager.register_email("Test Subject", "Test Body", "user@test.com")
            
            assert result is True
            brass_manager.db_tareas.insert_record.assert_called_once()
    
    def test_register_email_failure(self, brass_manager):
        """Test registrar email fallido"""
        brass_manager.db_tareas.get_max_id.return_value = 5
        brass_manager.db_tareas.insert_record.return_value = False
        
        with patch.object(brass_manager, 'get_admin_emails_string') as mock_get_emails:
            mock_get_emails.return_value = "admin@test.com"
            
            result = brass_manager.register_email("Test Subject", "Test Body", "user@test.com")
            
            assert result is False
    
    def test_register_email_exception(self, brass_manager):
        """Test registrar email con excepción"""
        brass_manager.db_tareas.get_max_id.side_effect = Exception("DB Error")
        
        result = brass_manager.register_email("Test Subject", "Test Body", "user@test.com")
        
        assert result is False
    
    def test_register_task_completion_update_existing(self, brass_manager):
        """Test registrar tarea completada - actualizar existente"""
        brass_manager.db_tareas.execute_query.return_value = [{'Count': 1}]
        brass_manager.db_tareas.update_record.return_value = True
        
        result = brass_manager.register_task_completion()
        
        assert result is True
        brass_manager.db_tareas.update_record.assert_called_once()
        brass_manager.db_tareas.insert_record.assert_not_called()
    
    def test_register_task_completion_insert_new(self, brass_manager):
        """Test registrar tarea completada - insertar nuevo"""
        brass_manager.db_tareas.execute_query.return_value = [{'Count': 0}]
        brass_manager.db_tareas.insert_record.return_value = True
        
        result = brass_manager.register_task_completion()
        
        assert result is True
        brass_manager.db_tareas.insert_record.assert_called_once()
        brass_manager.db_tareas.update_record.assert_not_called()
    
    def test_register_task_completion_exception(self, brass_manager):
        """Test registrar tarea completada con excepción"""
        brass_manager.db_tareas.execute_query.side_effect = Exception("DB Error")
        
        result = brass_manager.register_task_completion()
        
        assert result is False
    
    def test_execute_task_already_completed(self, brass_manager):
        """Test ejecutar tarea ya completada hoy"""
        with patch.object(brass_manager, 'is_task_completed_today') as mock_completed:
            mock_completed.return_value = True
            
            result = brass_manager.execute_task()
            
            assert result is True
    
    def test_execute_task_no_equipment(self, brass_manager):
        """Test ejecutar tarea sin equipos fuera de calibración"""
        with patch.object(brass_manager, 'is_task_completed_today') as mock_completed, \
             patch.object(brass_manager, 'get_equipment_out_of_calibration') as mock_get_equipment, \
             patch.object(brass_manager, 'register_task_completion') as mock_register:
            
            mock_completed.return_value = False
            mock_get_equipment.return_value = []
            mock_register.return_value = True
            
            result = brass_manager.execute_task()
            
            assert result is True
            mock_register.assert_called_once()
    
    def test_execute_task_with_equipment_success(self, brass_manager):
        """Test ejecutar tarea con equipos fuera de calibración - éxito"""
        mock_equipment = [{'NOMBRE': 'Equipo1'}]
        
        with patch.object(brass_manager, 'is_task_completed_today') as mock_completed, \
             patch.object(brass_manager, 'get_equipment_out_of_calibration') as mock_get_equipment, \
             patch.object(brass_manager, 'generate_html_report') as mock_generate_html, \
             patch.object(brass_manager, 'register_email') as mock_register_email, \
             patch.object(brass_manager, 'register_task_completion') as mock_register_task:
            
            mock_completed.return_value = False
            mock_get_equipment.return_value = mock_equipment
            mock_generate_html.return_value = "<html>Report</html>"
            mock_register_email.return_value = True
            mock_register_task.return_value = True
            
            result = brass_manager.execute_task()
            
            assert result is True
            mock_register_email.assert_called_once()
            mock_register_task.assert_called_once()
    
    def test_execute_task_with_equipment_email_failure(self, brass_manager):
        """Test ejecutar tarea con equipos - fallo en email"""
        mock_equipment = [{'NOMBRE': 'Equipo1'}]
        
        with patch.object(brass_manager, 'is_task_completed_today') as mock_completed, \
             patch.object(brass_manager, 'get_equipment_out_of_calibration') as mock_get_equipment, \
             patch.object(brass_manager, 'generate_html_report') as mock_generate_html, \
             patch.object(brass_manager, 'register_email') as mock_register_email:
            
            mock_completed.return_value = False
            mock_get_equipment.return_value = mock_equipment
            mock_generate_html.return_value = "<html>Report</html>"
            mock_register_email.return_value = False
            
            result = brass_manager.execute_task()
            
            assert result is False
    
    def test_execute_task_exception(self, brass_manager):
        """Test ejecutar tarea con excepción"""
        with patch.object(brass_manager, 'is_task_completed_today') as mock_completed:
            mock_completed.side_effect = Exception("Error")
            
            result = brass_manager.execute_task()
            
            assert result is False