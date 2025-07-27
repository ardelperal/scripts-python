"""
Pruebas unitarias para el módulo de gestión de riesgos.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.common.config import Config
from src.riesgos.riesgos_manager import RiesgosManager


class TestRiesgosManager(unittest.TestCase):
    """Pruebas para la clase RiesgosManager."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.config = Mock(spec=Config)
        self.config.database_path = "test.accdb"
        self.manager = RiesgosManager(self.config)
        self.manager.db = Mock()
    
    def test_init(self):
        """Prueba la inicialización del manager."""
        self.assertEqual(self.manager.config, self.config)
        self.assertIsNotNone(self.manager.logger)
    
    def test_connect_success(self):
        """Prueba conexión exitosa a la base de datos."""
        self.manager.db.connect.return_value = True
        
        result = self.manager.connect()
        
        self.assertTrue(result)
        self.manager.db.connect.assert_called_once()
    
    def test_connect_failure(self):
        """Prueba fallo en la conexión a la base de datos."""
        self.manager.db.connect.side_effect = Exception("Connection error")
        
        result = self.manager.connect()
        
        self.assertFalse(result)
    
    def test_disconnect(self):
        """Prueba desconexión de la base de datos."""
        self.manager.disconnect()
        
        self.manager.db.disconnect.assert_called_once()
    
    def test_get_last_execution_with_result(self):
        """Prueba obtener última ejecución cuando existe."""
        expected_date = datetime(2023, 1, 15, 10, 30)
        self.manager.db.execute_query.return_value = [
            {'FechaEjecucion': expected_date}
        ]
        
        result = self.manager.get_last_execution('TECNICA')
        
        self.assertEqual(result, expected_date)
        self.manager.db.execute_query.assert_called_once()
    
    def test_get_last_execution_no_result(self):
        """Prueba obtener última ejecución cuando no existe."""
        self.manager.db.execute_query.return_value = []
        
        result = self.manager.get_last_execution('TECNICA')
        
        self.assertIsNone(result)
    
    def test_get_last_execution_error(self):
        """Prueba error al obtener última ejecución."""
        self.manager.db.execute_query.side_effect = Exception("DB error")
        
        result = self.manager.get_last_execution('TECNICA')
        
        self.assertIsNone(result)
    
    def test_should_execute_technical_task_no_previous(self):
        """Prueba si debe ejecutar tarea técnica sin ejecución previa."""
        self.manager.get_last_execution = Mock(return_value=None)
        
        result = self.manager.should_execute_technical_task()
        
        self.assertTrue(result)
    
    def test_should_execute_technical_task_recent(self):
        """Prueba si debe ejecutar tarea técnica con ejecución reciente."""
        recent_date = datetime.now() - timedelta(days=3)
        self.manager.get_last_execution = Mock(return_value=recent_date)
        
        result = self.manager.should_execute_technical_task()
        
        self.assertFalse(result)
    
    def test_should_execute_technical_task_old(self):
        """Prueba si debe ejecutar tarea técnica con ejecución antigua."""
        old_date = datetime.now() - timedelta(days=10)
        self.manager.get_last_execution = Mock(return_value=old_date)
        
        result = self.manager.should_execute_technical_task()
        
        self.assertTrue(result)
    
    def test_should_execute_quality_task_no_previous(self):
        """Prueba si debe ejecutar tarea de calidad sin ejecución previa."""
        self.manager.get_last_execution = Mock(return_value=None)
        
        result = self.manager.should_execute_quality_task()
        
        self.assertTrue(result)
    
    def test_should_execute_quality_task_recent(self):
        """Prueba si debe ejecutar tarea de calidad con ejecución reciente."""
        recent_date = datetime.now() - timedelta(days=3)
        self.manager.get_last_execution = Mock(return_value=recent_date)
        
        result = self.manager.should_execute_quality_task()
        
        self.assertFalse(result)
    
    def test_should_execute_quality_task_old(self):
        """Prueba si debe ejecutar tarea de calidad con ejecución antigua."""
        old_date = datetime.now() - timedelta(days=10)
        self.manager.get_last_execution = Mock(return_value=old_date)
        
        result = self.manager.should_execute_quality_task()
        
        self.assertTrue(result)
    
    def test_should_execute_monthly_quality_task_no_previous(self):
        """Prueba si debe ejecutar tarea mensual sin ejecución previa."""
        self.manager.get_last_execution = Mock(return_value=None)
        
        result = self.manager.should_execute_monthly_quality_task()
        
        self.assertTrue(result)
    
    def test_should_execute_monthly_quality_task_recent(self):
        """Prueba si debe ejecutar tarea mensual con ejecución reciente."""
        recent_date = datetime.now() - timedelta(days=15)
        self.manager.get_last_execution = Mock(return_value=recent_date)
        
        result = self.manager.should_execute_monthly_quality_task()
        
        self.assertFalse(result)
    
    def test_should_execute_monthly_quality_task_old(self):
        """Prueba si debe ejecutar tarea mensual con ejecución antigua."""
        old_date = datetime.now() - timedelta(days=35)
        self.manager.get_last_execution = Mock(return_value=old_date)
        
        result = self.manager.should_execute_monthly_quality_task()
        
        self.assertTrue(result)
    
    def test_get_distinct_users(self):
        """Prueba obtener usuarios distintos."""
        # Mock de las consultas
        self.manager.db.execute_query.side_effect = [
            [{'UsuarioRed': 'user1', 'Nombre': 'Usuario 1', 'CorreoUsuario': 'user1@test.com'}],
            [{'UsuarioRed': 'user2', 'Nombre': 'Usuario 2', 'CorreoUsuario': 'user2@test.com'}],
            [],  # Consulta sin resultados
            [{'UsuarioRed': 'user1', 'Nombre': 'Usuario 1', 'CorreoUsuario': 'user1@test.com'}],  # Usuario duplicado
            [],
            [],
            [],
            []
        ]
        
        result = self.manager.get_distinct_users()
        
        # Verificar que se obtuvieron usuarios únicos
        self.assertEqual(len(result), 2)
        self.assertIn('user1', result)
        self.assertIn('user2', result)
        self.assertEqual(result['user1'], ('Usuario 1', 'user1@test.com'))
        self.assertEqual(result['user2'], ('Usuario 2', 'user2@test.com'))
    
    def test_get_css_styles(self):
        """Prueba obtener estilos CSS."""
        result = self.manager.get_css_styles()
        
        self.assertIn('<style', result)
        self.assertIn('body', result)
        self.assertIn('table', result)
    
    def test_record_task_execution_success(self):
        """Prueba registrar ejecución de tarea exitosamente."""
        self.manager.db.execute_query.return_value = None
        
        result = self.manager.record_task_execution('TECNICA')
        
        self.assertTrue(result)
        self.manager.db.execute_query.assert_called_once()
    
    def test_record_task_execution_error(self):
        """Prueba error al registrar ejecución de tarea."""
        self.manager.db.execute_query.side_effect = Exception("DB error")
        
        result = self.manager.record_task_execution('TECNICA')
        
        self.assertFalse(result)
    
    @patch('src.riesgos.riesgos_manager.get_admin_emails_string')
    @patch('src.riesgos.riesgos_manager.send_notification_email')
    def test_execute_daily_task_success(self, mock_send_email, mock_get_emails):
        """Prueba ejecución exitosa de tareas diarias."""
        # Configurar mocks
        self.manager.connect = Mock(return_value=True)
        self.manager.disconnect = Mock()
        self.manager.should_execute_technical_task = Mock(return_value=True)
        self.manager.should_execute_quality_task = Mock(return_value=False)
        self.manager.should_execute_monthly_quality_task = Mock(return_value=False)
        self.manager.execute_technical_task = Mock(return_value=True)
        self.manager.record_task_execution = Mock(return_value=True)
        mock_get_emails.return_value = "admin@test.com"
        
        result = self.manager.execute_daily_task()
        
        self.assertTrue(result)
        self.manager.connect.assert_called_once()
        self.manager.execute_technical_task.assert_called_once()
        self.manager.record_task_execution.assert_called_once_with('TECNICA')
        mock_send_email.assert_called_once()
        self.manager.disconnect.assert_called_once()
    
    def test_execute_daily_task_connection_failure(self):
        """Prueba fallo de conexión en tareas diarias."""
        self.manager.connect = Mock(return_value=False)
        self.manager.disconnect = Mock()
        
        result = self.manager.execute_daily_task()
        
        self.assertFalse(result)
        self.manager.disconnect.assert_called_once()
    
    @patch('src.riesgos.riesgos_manager.send_notification_email')
    def test_execute_technical_task_success(self, mock_send_email):
        """Prueba ejecución exitosa de tarea técnica."""
        # Configurar usuarios mock
        users = {
            'user1': ('Usuario 1', 'user1@test.com'),
            'user2': ('Usuario 2', 'user2@test.com')
        }
        self.manager.get_distinct_users = Mock(return_value=users)
        self.manager._generate_technical_report_html = Mock(return_value="<html>Report</html>")
        
        result = self.manager.execute_technical_task()
        
        self.assertTrue(result)
        self.assertEqual(mock_send_email.call_count, 2)
    
    def test_execute_technical_task_error(self):
        """Prueba error en ejecución de tarea técnica."""
        self.manager.get_distinct_users = Mock(side_effect=Exception("Error"))
        
        result = self.manager.execute_technical_task()
        
        self.assertFalse(result)
    
    @patch('src.riesgos.riesgos_manager.get_admin_emails_string')
    @patch('src.riesgos.riesgos_manager.send_notification_email')
    def test_execute_quality_task_success(self, mock_send_email, mock_get_emails):
        """Prueba ejecución exitosa de tarea de calidad."""
        mock_get_emails.return_value = "admin@test.com"
        self.manager._generate_quality_report_html = Mock(return_value="<html>Quality Report</html>")
        
        result = self.manager.execute_quality_task()
        
        self.assertTrue(result)
        mock_send_email.assert_called_once()
    
    def test_execute_quality_task_error(self):
        """Prueba error en ejecución de tarea de calidad."""
        self.manager._generate_quality_report_html = Mock(side_effect=Exception("Error"))
        
        result = self.manager.execute_quality_task()
        
        self.assertFalse(result)
    
    @patch('src.riesgos.riesgos_manager.get_admin_emails_string')
    @patch('src.riesgos.riesgos_manager.send_notification_email')
    def test_execute_monthly_quality_task_success(self, mock_send_email, mock_get_emails):
        """Prueba ejecución exitosa de tarea de calidad mensual."""
        mock_get_emails.return_value = "admin@test.com"
        self.manager._generate_monthly_quality_report_html = Mock(return_value="<html>Monthly Report</html>")
        
        result = self.manager.execute_monthly_quality_task()
        
        self.assertTrue(result)
        mock_send_email.assert_called_once()
    
    def test_execute_monthly_quality_task_error(self):
        """Prueba error en ejecución de tarea de calidad mensual."""
        self.manager._generate_monthly_quality_report_html = Mock(side_effect=Exception("Error"))
        
        result = self.manager.execute_monthly_quality_task()
        
        self.assertFalse(result)
    
    def test_generate_technical_report_html(self):
        """Prueba generación de reporte HTML técnico."""
        # Mock de métodos de datos
        self.manager._get_editions_need_publication_data = Mock(return_value=[])
        self.manager._get_editions_rejected_proposals_data = Mock(return_value=[])
        self.manager._get_accepted_risks_unmotivated_data = Mock(return_value=[])
        self.manager._get_accepted_risks_rejected_data = Mock(return_value=[])
        self.manager._get_retired_risks_unmotivated_data = Mock(return_value=[])
        self.manager._get_retired_risks_rejected_data = Mock(return_value=[])
        self.manager._get_mitigation_actions_reschedule_data = Mock(return_value=[])
        self.manager._get_contingency_actions_reschedule_data = Mock(return_value=[])
        
        result = self.manager._generate_technical_report_html('user1', 'Usuario 1')
        
        self.assertIn('<html>', result)
        self.assertIn('Usuario 1', result)
        self.assertIn('</html>', result)
    
    def test_generate_quality_report_html(self):
        """Prueba generación de reporte HTML de calidad."""
        self.manager._generate_quality_metrics_html = Mock(return_value="<div>Metrics</div>")
        
        result = self.manager._generate_quality_report_html()
        
        self.assertIn('<html>', result)
        self.assertIn('Informe Semanal de Calidad', result)
        self.assertIn('</html>', result)
    
    def test_generate_monthly_quality_report_html(self):
        """Prueba generación de reporte HTML de calidad mensual."""
        self.manager._generate_monthly_metrics_html = Mock(return_value="<div>Monthly Metrics</div>")
        
        result = self.manager._generate_monthly_quality_report_html()
        
        self.assertIn('<html>', result)
        self.assertIn('Informe Mensual de Calidad', result)
        self.assertIn('</html>', result)
    
    def test_generate_section_html_with_data(self):
        """Prueba generación de sección HTML con datos."""
        data = [
            {'Columna1': 'Valor1', 'Columna2': 'Valor2'},
            {'Columna1': 'Valor3', 'Columna2': 'Valor4'}
        ]
        
        result = self.manager._generate_section_html('Test Section', data)
        
        self.assertIn('Test Section', result)
        self.assertIn('Total: 2 elementos', result)
        self.assertIn('<table>', result)
        self.assertIn('Valor1', result)
    
    def test_generate_section_html_no_data(self):
        """Prueba generación de sección HTML sin datos."""
        result = self.manager._generate_section_html('Empty Section', [])
        
        self.assertIn('Empty Section', result)
        self.assertIn('Total: 0 elementos', result)
        self.assertIn('No hay elementos para mostrar', result)
    
    def test_data_methods_error_handling(self):
        """Prueba manejo de errores en métodos de datos."""
        self.manager.db.execute_query.side_effect = Exception("DB error")
        
        # Probar todos los métodos de datos
        methods = [
            '_get_editions_need_publication_data',
            '_get_editions_rejected_proposals_data',
            '_get_accepted_risks_unmotivated_data',
            '_get_accepted_risks_rejected_data',
            '_get_retired_risks_unmotivated_data',
            '_get_retired_risks_rejected_data',
            '_get_mitigation_actions_reschedule_data',
            '_get_contingency_actions_reschedule_data'
        ]
        
        for method_name in methods:
            method = getattr(self.manager, method_name)
            result = method('user1')
            self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()