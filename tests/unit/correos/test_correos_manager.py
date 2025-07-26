"""
Tests unitarios para CorreosManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import smtplib
import sqlite3
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from src.correos.correos_manager import CorreosManager


class TestCorreosManager:
    """Tests para la clase CorreosManager"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de configuración"""
        with patch('src.correos.correos_manager.config') as mock_config:
            mock_config.smtp_server = "localhost"
            mock_config.smtp_port = 587
            mock_config.smtp_user = "test@example.com"
            mock_config.smtp_password = "password"
            mock_config.smtp_tls = False
            mock_config.sqlite_dir = Path("/mock/sqlite")
            yield mock_config
    
    @pytest.fixture
    def mock_sqlite_connect(self):
        """Mock de sqlite3.connect"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            yield mock_connect, mock_conn, mock_cursor
    
    @pytest.fixture
    def correos_manager(self, mock_config):
        """Instancia de CorreosManager con mocks"""
        return CorreosManager()
    
    def test_init(self, correos_manager, mock_config):
        """Test de inicialización"""
        assert correos_manager.config is not None
        assert correos_manager.smtp_server == "localhost"
        assert correos_manager.smtp_port == 587
        assert correos_manager.smtp_user == "test@example.com"
    
    def test_enviar_correo_individual_success(self, correos_manager):
        """Test enviar correo individual exitoso"""
        mock_email = {
            'IDCorreo': 1,
            'Destinatarios': 'test@example.com',
            'Asunto': 'Test Subject',
            'Cuerpo': 'Test Body',
            'URLAdjunto': None
        }
        
        with patch.object(correos_manager, '_enviar_smtp') as mock_smtp:
            mock_smtp.return_value = True
            
            result = correos_manager._enviar_correo_individual(mock_email)
            
            assert result is True
            mock_smtp.assert_called_once()
    
    def test_enviar_correo_individual_smtp_failure(self, correos_manager):
        """Test enviar correo individual con fallo SMTP"""
        mock_email = {
            'IDCorreo': 1,
            'Destinatarios': 'test@example.com',
            'Asunto': 'Test Subject',
            'Cuerpo': 'Test Body',
            'URLAdjunto': None
        }
        
        with patch.object(correos_manager, '_enviar_smtp') as mock_smtp:
            mock_smtp.return_value = False
            
            result = correos_manager._enviar_correo_individual(mock_email)
            
            assert result is False
    
    def test_enviar_correo_individual_exception(self, correos_manager):
        """Test enviar correo individual con excepción"""
        mock_email = {
            'IDCorreo': 1,
            'Destinatarios': 'test@example.com',
            'Asunto': 'Test Subject',
            'Cuerpo': 'Test Body',
            'URLAdjunto': None
        }
        
        with patch.object(correos_manager, '_enviar_smtp') as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP Error")
            
            result = correos_manager._enviar_correo_individual(mock_email)
            
            assert result is False
    
    def test_enviar_correos_no_enviados_success(self, correos_manager):
        """Test enviar correos no enviados exitoso"""
        # Mock de datos de correos como sqlite3.Row
        mock_row1 = Mock()
        mock_row1.keys.return_value = ['IDCorreo', 'Destinatarios', 'Asunto', 'Cuerpo', 'URLAdjunto']
        mock_row1.__getitem__ = lambda self, key: {
            'IDCorreo': 1, 'Destinatarios': 'test1@example.com', 
            'Asunto': 'Test 1', 'Cuerpo': 'Body 1', 'URLAdjunto': None
        }[key]
        
        mock_row2 = Mock()
        mock_row2.keys.return_value = ['IDCorreo', 'Destinatarios', 'Asunto', 'Cuerpo', 'URLAdjunto']
        mock_row2.__getitem__ = lambda self, key: {
            'IDCorreo': 2, 'Destinatarios': 'test2@example.com', 
            'Asunto': 'Test 2', 'Cuerpo': 'Body 2', 'URLAdjunto': None
        }[key]
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [mock_row1, mock_row2]
            
            with patch.object(correos_manager, '_enviar_correo_individual') as mock_enviar, \
                 patch.object(correos_manager, '_marcar_correo_enviado') as mock_marcar:
                
                mock_enviar.side_effect = [True, True]
                
                result = correos_manager.enviar_correos_no_enviados()
                
                assert result == 2
                assert mock_enviar.call_count == 2
                assert mock_marcar.call_count == 2
    
    def test_enviar_correos_no_enviados_partial_success(self, correos_manager):
        """Test enviar correos no enviados con éxito parcial"""
        mock_row1 = Mock()
        mock_row1.keys.return_value = ['IDCorreo', 'Destinatarios', 'Asunto', 'Cuerpo', 'URLAdjunto']
        mock_row1.__getitem__ = lambda self, key: {
            'IDCorreo': 1, 'Destinatarios': 'test1@example.com', 
            'Asunto': 'Test 1', 'Cuerpo': 'Body 1', 'URLAdjunto': None
        }[key]
        
        mock_row2 = Mock()
        mock_row2.keys.return_value = ['IDCorreo', 'Destinatarios', 'Asunto', 'Cuerpo', 'URLAdjunto']
        mock_row2.__getitem__ = lambda self, key: {
            'IDCorreo': 2, 'Destinatarios': 'test2@example.com', 
            'Asunto': 'Test 2', 'Cuerpo': 'Body 2', 'URLAdjunto': None
        }[key]
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [mock_row1, mock_row2]
            
            with patch.object(correos_manager, '_enviar_correo_individual') as mock_enviar, \
                 patch.object(correos_manager, '_marcar_correo_enviado') as mock_marcar:
                
                mock_enviar.side_effect = [True, False]
                
                result = correos_manager.enviar_correos_no_enviados()
                
                assert result == 1
                assert mock_marcar.call_count == 1
    
    def test_enviar_correos_no_enviados_no_emails(self, correos_manager):
        """Test enviar correos no enviados sin emails"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            
            result = correos_manager.enviar_correos_no_enviados()
            
            assert result == 0
    
    def test_enviar_correos_no_enviados_exception(self, correos_manager):
        """Test enviar correos no enviados con excepción"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = Exception("DB Error")
            
            result = correos_manager.enviar_correos_no_enviados()
            
            assert result == 0
    
    def test_adjuntar_archivo_success(self, correos_manager):
        """Test adjuntar archivo exitoso"""
        mock_msg = MIMEMultipart()
        file_path = Path("test_file.pdf")
        
        with patch('builtins.open', mock_open(read_data=b'test content')), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.name', 'test_file.pdf'):
            
            # El método no retorna nada, solo adjunta
            correos_manager._adjuntar_archivo(mock_msg, file_path)
            
            # Verificar que se adjuntó algo
            assert len(mock_msg.get_payload()) > 0
    
    def test_adjuntar_archivo_file_not_found(self, correos_manager):
        """Test adjuntar archivo no encontrado"""
        mock_msg = MIMEMultipart()
        file_path = Path("nonexistent_file.pdf")
        
        with patch('pathlib.Path.exists', return_value=False):
            # El método no retorna nada, pero no debería adjuntar nada
            correos_manager._adjuntar_archivo(mock_msg, file_path)
            
            # Verificar que no se adjuntó nada
            assert len(mock_msg.get_payload()) == 0
    
    def test_adjuntar_archivo_exception(self, correos_manager):
        """Test adjuntar archivo con excepción"""
        mock_msg = MIMEMultipart()
        file_path = Path("test_file.pdf")
        
        with patch('builtins.open', side_effect=Exception("File error")), \
             patch('pathlib.Path.exists', return_value=True):
            
            # El método no retorna nada, pero no debería adjuntar nada por la excepción
            correos_manager._adjuntar_archivo(mock_msg, file_path)
            
            # Verificar que no se adjuntó nada
            assert len(mock_msg.get_payload()) == 0
    
    def test_enviar_smtp_success(self, correos_manager):
        """Test enviar SMTP exitoso"""
        mock_msg = MIMEMultipart()
        destinatarios = ["test@example.com"]
        
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            
            result = correos_manager._enviar_smtp(mock_msg, destinatarios)
            
            assert result is True
            mock_server.sendmail.assert_called_once()
    
    def test_enviar_smtp_with_tls(self, correos_manager):
        """Test enviar SMTP con TLS"""
        correos_manager.smtp_tls = True
        correos_manager.smtp_user = "test@example.com"
        correos_manager.smtp_password = "password"
        
        mock_msg = MIMEMultipart()
        destinatarios = ["test@example.com"]
        
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_server = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_server
            
            result = correos_manager._enviar_smtp(mock_msg, destinatarios)
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()
    
    def test_enviar_smtp_exception(self, correos_manager):
        """Test enviar SMTP con excepción"""
        mock_msg = MIMEMultipart()
        destinatarios = ["test@example.com"]
        
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = Exception("SMTP Error")
            
            result = correos_manager._enviar_smtp(mock_msg, destinatarios)
            
            assert result is False
    
    def test_marcar_correo_enviado_success(self, correos_manager):
        """Test marcar correo enviado exitoso"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        fecha_envio = datetime.now()
        
        correos_manager._marcar_correo_enviado(mock_conn, 1, fecha_envio)
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_marcar_correo_enviado_exception(self, correos_manager):
        """Test marcar correo enviado con excepción"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB Error")
        
        fecha_envio = datetime.now()
        
        # El método no retorna nada, solo loggea el error
        correos_manager._marcar_correo_enviado(mock_conn, 1, fecha_envio)
    
    def test_sync_databases_success(self, correos_manager):
        """Test sincronización de bases de datos exitosa"""
        result = correos_manager.sync_databases()
        
        # Como es un placeholder, debería retornar True
        assert result is True
    
    def test_sync_back_to_access_success(self, correos_manager):
        """Test sincronización de vuelta a Access exitosa"""
        result = correos_manager.sync_back_to_access()
        
        # Como es un placeholder, debería retornar True
        assert result is True
    
    def test_execute_daily_task_success(self, correos_manager):
        """Test ejecución de tarea diaria exitosa"""
        with patch.object(correos_manager, 'enviar_correos_no_enviados') as mock_enviar, \
             patch.object(correos_manager, 'sync_databases') as mock_sync, \
             patch.object(correos_manager, 'sync_back_to_access') as mock_sync_back:
            
            mock_enviar.return_value = 5
            mock_sync.return_value = True
            mock_sync_back.return_value = True
            
            result = correos_manager.execute_daily_task()
            
            assert result is True
            mock_enviar.assert_called_once()
            mock_sync.assert_called_once()
            mock_sync_back.assert_called_once()
    
    def test_execute_daily_task_email_failure(self, correos_manager):
        """Test ejecución de tarea diaria con fallo en envío de emails"""
        with patch.object(correos_manager, 'enviar_correos_no_enviados') as mock_enviar, \
             patch.object(correos_manager, 'sync_databases') as mock_sync, \
             patch.object(correos_manager, 'sync_back_to_access') as mock_sync_back:
            
            mock_enviar.side_effect = Exception("Email error")
            mock_sync.return_value = True
            mock_sync_back.return_value = True
            
            result = correos_manager.execute_daily_task()
            
            assert result is False
    
    def test_execute_daily_task_exception(self, correos_manager):
        """Test ejecución de tarea diaria con excepción general"""
        with patch.object(correos_manager, 'enviar_correos_no_enviados') as mock_enviar:
            mock_enviar.side_effect = Exception("General error")
            
            result = correos_manager.execute_daily_task()
            
            assert result is False