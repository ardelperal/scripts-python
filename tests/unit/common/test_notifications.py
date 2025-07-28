"""
Tests unitarios para el módulo de notificaciones.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.common.notifications import NotificationManager, send_notification


class TestNotificationManager:
    """Tests para la clase NotificationManager."""
    
    def setup_method(self):
        """Configuración para cada test."""
        self.manager = NotificationManager()
    
    @patch('src.common.notifications.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test envío exitoso de email."""
        # Configurar mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Ejecutar
        result = self.manager.send_email(
            to=['test@example.com'],
            subject='Test Subject',
            body='Test Body'
        )
        
        # Verificar
        assert result is True
        mock_smtp.assert_called_once_with(self.manager.smtp_server, self.manager.smtp_port)
        mock_server.send_message.assert_called_once()
    
    @patch('src.common.notifications.smtplib.SMTP')
    def test_send_email_with_html(self, mock_smtp):
        """Test envío de email con contenido HTML."""
        # Configurar mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Ejecutar
        result = self.manager.send_email(
            to=['test@example.com'],
            subject='Test Subject',
            body='Test Body',
            html_body='<h1>Test HTML</h1>'
        )
        
        # Verificar
        assert result is True
        mock_server.send_message.assert_called_once()
    
    @patch('src.common.notifications.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test fallo en envío de email."""
        # Configurar mock para fallar
        mock_smtp.side_effect = Exception("SMTP Error")
        
        # Ejecutar
        result = self.manager.send_email(
            to=['test@example.com'],
            subject='Test Subject',
            body='Test Body'
        )
        
        # Verificar
        assert result is False
    
    @patch.object(NotificationManager, 'send_email')
    def test_send_error_notification(self, mock_send_email):
        """Test envío de notificación de error."""
        mock_send_email.return_value = True
        
        # Ejecutar
        result = self.manager.send_error_notification("Test error", "TestModule")
        
        # Verificar
        assert result is True
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert "Error en TestModule" in args[1]  # subject
        assert "Test error" in args[2]  # body
    
    @patch.object(NotificationManager, 'send_email')
    def test_send_success_notification(self, mock_send_email):
        """Test envío de notificación de éxito."""
        mock_send_email.return_value = True
        
        # Ejecutar
        result = self.manager.send_success_notification("Test success", "TestModule")
        
        # Verificar
        assert result is True
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert "Operación completada en TestModule" in args[1]  # subject
        assert "Test success" in args[2]  # body


class TestSendNotification:
    """Tests para la función send_notification."""
    
    @patch('src.common.notifications.NotificationManager')
    def test_send_notification_info(self, mock_manager_class):
        """Test envío de notificación tipo info."""
        mock_manager = Mock()
        mock_manager.send_email.return_value = True
        mock_manager_class.return_value = mock_manager
        
        # Ejecutar
        result = send_notification("Test message", "info")
        
        # Verificar
        assert result is True
        mock_manager.send_email.assert_called_once()
    
    @patch('src.common.notifications.NotificationManager')
    def test_send_notification_error(self, mock_manager_class):
        """Test envío de notificación tipo error."""
        mock_manager = Mock()
        mock_manager.send_error_notification.return_value = True
        mock_manager_class.return_value = mock_manager
        
        # Ejecutar
        result = send_notification("Test error", "error")
        
        # Verificar
        assert result is True
        mock_manager.send_error_notification.assert_called_once_with("Test error")
    
    @patch('src.common.notifications.NotificationManager')
    def test_send_notification_success(self, mock_manager_class):
        """Test envío de notificación tipo success."""
        mock_manager = Mock()
        mock_manager.send_success_notification.return_value = True
        mock_manager_class.return_value = mock_manager
        
        # Ejecutar
        result = send_notification("Test success", "success")
        
        # Verificar
        assert result is True
        mock_manager.send_success_notification.assert_called_once_with("Test success")


class TestNotificationManagerConfiguration:
    """Tests para la configuración del NotificationManager."""
    
    @patch.dict('os.environ', {
        'SMTP_SERVER': 'test.smtp.com',
        'SMTP_PORT': '587',
        'SMTP_FROM': 'test@test.com',
        'DEFAULT_RECIPIENT': 'admin@test.com'
    })
    def test_manager_configuration(self):
        """Test configuración del manager."""
        # Ejecutar
        manager = NotificationManager()
        
        # Verificar
        assert manager.smtp_server == 'test.smtp.com'
        assert manager.smtp_port == 587
        assert manager.smtp_from == 'test@test.com'
        assert manager.default_recipient == 'admin@test.com'
    
    @patch.dict('os.environ', {}, clear=True)
    def test_manager_default_configuration(self):
        """Test configuración por defecto del manager."""
        # Ejecutar
        manager = NotificationManager()
        
        # Verificar valores por defecto
        assert manager.smtp_server == 'localhost'
        assert manager.smtp_port == 1025
        assert manager.smtp_from == 'noreply@example.com'
        assert manager.default_recipient == 'admin@example.com'