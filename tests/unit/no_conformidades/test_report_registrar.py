"""Tests unitarios para el módulo report_registrar de no conformidades"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from src.no_conformidades.report_registrar import (
    ReportRegistrar,
    enviar_notificacion_calidad,
    enviar_notificacion_tecnica,
    enviar_notificacion_individual_arapc,
    enviar_notificaciones_individuales_arapcs,
    _register_email_nc,
    _register_arapc_notification
)


class TestReportRegistrar(unittest.TestCase):
    """Tests para la clase ReportRegistrar"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.registrar = ReportRegistrar()
    
    def test_init(self):
        """Test de inicialización de ReportRegistrar"""
        self.assertIsNotNone(self.registrar)
        self.assertIsNotNone(self.registrar.html_generator)
    
    @patch('src.no_conformidades.report_registrar.AccessDatabase')
    @patch('src.no_conformidades.report_registrar.config')
    def test_get_admin_emails(self, mock_config, mock_db):
        """Test para obtener emails de administradores"""
        # Configurar mocks
        mock_config.get_database_path.return_value = "test_db.accdb"
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("admin1@test.com",), ("admin2@test.com",)]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = mock_connection
        
        # Ejecutar
        emails = self.registrar.get_admin_emails()
        
        # Verificar
        self.assertEqual(emails, ["admin1@test.com", "admin2@test.com"])
        mock_cursor.execute.assert_called_once()
    
    @patch('src.no_conformidades.report_registrar.AccessDatabase')
    @patch('src.no_conformidades.report_registrar.config')
    def test_get_quality_emails(self, mock_config, mock_db):
        """Test para obtener emails de calidad"""
        # Configurar mocks
        mock_config.get_database_path.return_value = "test_db.accdb"
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("quality1@test.com",), ("quality2@test.com",)]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = mock_connection
        
        # Ejecutar
        emails = self.registrar.get_quality_emails()
        
        # Verificar
        self.assertEqual(emails, ["quality1@test.com", "quality2@test.com"])
        mock_cursor.execute.assert_called_once()
    
    def test_generate_technical_report_html_empty(self):
        """Test de generación de HTML técnico sin datos"""
        html = self.registrar.generate_technical_report_html()
        
        self.assertIn("Aviso de Acciones de Resolución", html)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("</html>", html)
    
    def test_generate_technical_report_html_with_data(self):
        """Test de generación de HTML técnico con datos"""
        ars_8_15 = [{"CodigoNoConformidad": "NC001", "AccionRealizada": "Test"}]
        ars_1_7 = [{"CodigoNoConformidad": "NC002", "AccionRealizada": "Test2"}]
        ars_vencidas = [{"CodigoNoConformidad": "NC003", "AccionRealizada": "Test3"}]
        
        html = self.registrar.generate_technical_report_html(
            ars_proximas_vencer_8_15=ars_8_15,
            ars_proximas_vencer_1_7=ars_1_7,
            ars_vencidas=ars_vencidas
        )
        
        self.assertIn("Acciones Próximas a Vencer (8-15 días)", html)
        self.assertIn("Acciones Próximas a Vencer (1-7 días)", html)
        self.assertIn("Acciones Vencidas", html)
        self.assertIn("NC001", html)
        self.assertIn("NC002", html)
        self.assertIn("NC003", html)


class TestEmailRegistration(unittest.TestCase):
    """Tests para funciones de registro de emails"""
    
    @patch('src.no_conformidades.report_registrar.AccessDatabase')
    @patch('src.no_conformidades.report_registrar.config')
    def test_register_email_nc_success(self, mock_config, mock_db):
        """Test de registro exitoso de email"""
        # Configurar mocks
        mock_config.get_database_path.return_value = "test_db.accdb"
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = mock_connection
        mock_db.return_value.get_max_id.return_value = 10
        
        # Ejecutar
        result = _register_email_nc(
            application="NoConformidades",
            subject="Test Subject",
            body="<html>Test Body</html>",
            recipients="test@example.com",
            admin_emails="admin@example.com"
        )
        
        # Verificar
        self.assertEqual(result, 11)
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
    
    @patch('src.no_conformidades.report_registrar.AccessDatabase')
    @patch('src.no_conformidades.report_registrar.config')
    def test_register_arapc_notification_success(self, mock_config, mock_db):
        """Test de registro exitoso de notificación ARAPC"""
        # Configurar mocks
        mock_config.get_database_path.return_value = "test_db.accdb"
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = mock_connection
        
        # Ejecutar
        result = _register_arapc_notification(
            id_correo=123,
            arapcs_15=[1, 2],
            arapcs_7=[3, 4],
            arapcs_0=[5, 6]
        )
        
        # Verificar
        self.assertTrue(result)
        self.assertEqual(mock_cursor.execute.call_count, 6)  # 2+2+2 registros
        mock_connection.commit.assert_called_once()


class TestNotificationFunctions(unittest.TestCase):
    """Tests para funciones de notificación"""
    
    @patch('src.no_conformidades.report_registrar.ReportRegistrar')
    @patch('src.no_conformidades.report_registrar.HTMLReportGenerator')
    @patch('src.no_conformidades.report_registrar._register_email_nc')
    def test_enviar_notificacion_calidad_success(self, mock_register, mock_html_gen, mock_registrar):
        """Test de envío exitoso de notificación de calidad"""
        # Configurar mocks
        mock_registrar_instance = MagicMock()
        mock_registrar_instance.get_quality_emails.return_value = ["quality@test.com"]
        mock_registrar_instance.get_admin_emails.return_value = ["admin@test.com"]
        mock_registrar.return_value = mock_registrar_instance
        
        mock_html_instance = MagicMock()
        mock_html_instance.generar_reporte_calidad.return_value = "<html>Test</html>"
        mock_html_gen.return_value = mock_html_instance
        
        mock_register.return_value = 123
        
        # Ejecutar
        result = enviar_notificacion_calidad({"test": "data"})
        
        # Verificar
        self.assertTrue(result)
        mock_register.assert_called_once()
    
    @patch('src.no_conformidades.report_registrar.ReportRegistrar')
    @patch('src.no_conformidades.report_registrar.HTMLReportGenerator')
    @patch('src.no_conformidades.report_registrar._register_email_nc')
    def test_enviar_notificacion_calidad_no_recipients(self, mock_register, mock_html_gen, mock_registrar):
        """Test de notificación de calidad sin destinatarios"""
        # Configurar mocks
        mock_registrar_instance = MagicMock()
        mock_registrar_instance.get_quality_emails.return_value = []
        mock_registrar_instance.get_admin_emails.return_value = []
        mock_registrar.return_value = mock_registrar_instance
        
        # Ejecutar
        result = enviar_notificacion_calidad({"test": "data"})
        
        # Verificar
        self.assertFalse(result)
        mock_register.assert_not_called()
    
    @patch('src.no_conformidades.report_registrar.ReportRegistrar')
    @patch('src.no_conformidades.report_registrar.HTMLReportGenerator')
    @patch('src.no_conformidades.report_registrar._register_email_nc')
    @patch('src.no_conformidades.report_registrar._register_arapc_notification')
    def test_enviar_notificacion_individual_arapc_success(self, mock_register_arapc, mock_register_email, mock_html_gen, mock_registrar):
        """Test de envío exitoso de notificación individual ARAPC"""
        # Configurar mocks
        mock_registrar_instance = MagicMock()
        mock_registrar_instance.get_admin_emails.return_value = ["admin@test.com"]
        mock_registrar.return_value = mock_registrar_instance
        
        mock_html_instance = MagicMock()
        mock_html_instance.generar_notificacion_individual_arapc.return_value = "<html>Test</html>"
        mock_html_gen.return_value = mock_html_instance
        
        mock_register_email.return_value = 123
        mock_register_arapc.return_value = True
        
        arapc_data = {
            "id_accion": 1,
            "dias_restantes": 5
        }
        usuario_data = {
            "correo": "user@test.com"
        }
        
        # Ejecutar
        result = enviar_notificacion_individual_arapc(arapc_data, usuario_data)
        
        # Verificar
        self.assertTrue(result)
        mock_register_email.assert_called_once()
        mock_register_arapc.assert_called_once()


if __name__ == '__main__':
    unittest.main()