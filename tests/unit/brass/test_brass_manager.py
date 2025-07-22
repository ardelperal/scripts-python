"""
Tests unitarios para el módulo BRASS - Manager
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock

# Añadir src al path
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestBrassManager:
    """Tests unitarios para la clase BrassManager del módulo BRASS"""
    
    @pytest.fixture
    def brass_manager(self):
        """Fixture que crea una instancia mock del BrassManager"""
        with patch('common.database.AccessDatabase'), \
             patch('common.utils.load_css_content'), \
             patch('common.config.config'):
            
            # Importación después del patch para evitar errores
            from brass.brass_manager import BrassManager
            manager = BrassManager()
            return manager
    
    def test_brass_is_task_completed_today_true(self, brass_manager):
        """Test BRASS: cuando la tarea ya se ejecutó hoy"""
        # Mock para retornar la fecha de hoy
        with patch.object(brass_manager, 'get_last_execution_date', return_value=date.today()):
            assert brass_manager.is_task_completed_today() == True
    
    def test_brass_is_task_completed_today_false(self, brass_manager):
        """Test BRASS: cuando la tarea no se ejecutó hoy"""
        # Mock para retornar una fecha anterior
        yesterday = date.today().replace(day=date.today().day - 1)
        with patch.object(brass_manager, 'get_last_execution_date', return_value=yesterday):
            assert brass_manager.is_task_completed_today() == False
    
    def test_brass_is_task_completed_today_no_previous_execution(self, brass_manager):
        """Test BRASS: cuando no hay ejecución previa"""
        with patch.object(brass_manager, 'get_last_execution_date', return_value=None):
            assert brass_manager.is_task_completed_today() == False
    
    def test_brass_generate_html_report_empty_list(self, brass_manager):
        """Test BRASS: generación de reporte con lista vacía"""
        result = brass_manager.generate_html_report([])
        assert result == ""
    
    def test_brass_generate_html_report_with_equipment(self, brass_manager):
        """Test BRASS: generación de reporte con equipos"""
        equipment_list = [
            {
                'NOMBRE': 'Multímetro BRASS Test',
                'NS': 'BRASS001',
                'PN': 'PN001',
                'MARCA': 'Fluke',
                'MODELO': 'Model X'
            }
        ]
        
        # Mock del CSS content
        brass_manager.css_content = "body { margin: 0; }"
        
        result = brass_manager.generate_html_report(equipment_list)
        
        assert "EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN" in result
        assert "Multímetro BRASS Test" in result
        assert "BRASS001" in result
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result
    
    def test_brass_get_admin_emails_string(self, brass_manager):
        """Test BRASS: obtención de string de correos de administradores"""
        # Mock de usuarios administradores
        mock_users = [
            {'CorreoUsuario': 'admin1.brass@test.com'},
            {'CorreoUsuario': 'admin2.brass@test.com'},
            {'CorreoUsuario': 'admin3.brass@test.com'}
        ]
        
        with patch.object(brass_manager, 'get_admin_users', return_value=mock_users):
            result = brass_manager.get_admin_emails_string()
            
            assert result == "admin1.brass@test.com;admin2.brass@test.com;admin3.brass@test.com"
    
    def test_brass_execute_task_already_completed(self, brass_manager):
        """Test BRASS: ejecución cuando la tarea ya se completó hoy"""
        with patch.object(brass_manager, 'is_task_completed_today', return_value=True):
            result = brass_manager.execute_task()
            assert result == True
    
    def test_brass_execute_task_no_equipment_out_of_calibration(self, brass_manager):
        """Test BRASS: ejecución sin equipos fuera de calibración"""
        with patch.object(brass_manager, 'is_task_completed_today', return_value=False), \
             patch.object(brass_manager, 'get_equipment_out_of_calibration', return_value=[]), \
             patch.object(brass_manager, 'register_task_completion', return_value=True):
            
            result = brass_manager.execute_task()
            assert result == True
    
    def test_brass_execute_task_with_equipment_out_of_calibration(self, brass_manager):
        """Test BRASS: ejecución con equipos fuera de calibración"""
        mock_equipment = [{'NOMBRE': 'BRASS Test Equipment'}]
        
        with patch.object(brass_manager, 'is_task_completed_today', return_value=False), \
             patch.object(brass_manager, 'get_equipment_out_of_calibration', return_value=mock_equipment), \
             patch.object(brass_manager, 'generate_html_report', return_value="<html>BRASS test</html>"), \
             patch.object(brass_manager, 'register_email', return_value=True), \
             patch.object(brass_manager, 'register_task_completion', return_value=True):
            
            result = brass_manager.execute_task()
            assert result == True
