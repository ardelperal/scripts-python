"""
Tests unitarios para CorreosManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from correos.correos_manager import CorreosManager


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
            mock_config.get_db_correos_connection_string.return_value = "DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=test_correos.accdb;"
            yield mock_config
    
    @pytest.fixture
    def mock_access_db(self):
        """Mock de AccessDatabase"""
        with patch('src.correos.correos_manager.AccessDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db_class.return_value = mock_db
            yield mock_db
    
    @pytest.fixture
    def correos_manager(self, mock_config, mock_access_db):
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
    
    def test_process_pending_emails_success(self, correos_manager, mock_access_db):
        """Test process_pending_emails exitoso"""
        # Mock de datos de correos desde Access
        mock_correos = [
            {
                'IDCorreo': 1, 'Destinatarios': 'test1@example.com', 
                'Asunto': 'Test 1', 'Cuerpo': 'Body 1', 'URLAdjunto': None
            },
            {
                'IDCorreo': 2, 'Destinatarios': 'test2@example.com', 
                'Asunto': 'Test 2', 'Cuerpo': 'Body 2', 'URLAdjunto': None
            }
        ]
        
        mock_access_db.execute_query.return_value = mock_correos
        
        with patch.object(correos_manager, '_enviar_correo_individual') as mock_enviar, \
             patch.object(correos_manager, '_marcar_correo_enviado') as mock_marcar:
            
            mock_enviar.side_effect = [True, True]
            
            result = correos_manager.process_pending_emails()
            
            assert result == 2
            assert mock_enviar.call_count == 2
            assert mock_marcar.call_count == 2
    
    def test_process_pending_emails_partial_success(self, correos_manager, mock_access_db):
        """Test process_pending_emails con éxito parcial"""
        mock_correos = [
            {
                'IDCorreo': 1, 'Destinatarios': 'test1@example.com', 
                'Asunto': 'Test 1', 'Cuerpo': 'Body 1', 'URLAdjunto': None
            },
            {
                'IDCorreo': 2, 'Destinatarios': 'test2@example.com', 
                'Asunto': 'Test 2', 'Cuerpo': 'Body 2', 'URLAdjunto': None
            }
        ]
        
        mock_access_db.execute_query.return_value = mock_correos
        
        with patch.object(correos_manager, '_enviar_correo_individual') as mock_enviar, \
             patch.object(correos_manager, '_marcar_correo_enviado') as mock_marcar:
            
            mock_enviar.side_effect = [True, False]
            
            result = correos_manager.process_pending_emails()
            
            assert result == 1
            assert mock_marcar.call_count == 1
    
    def test_process_pending_emails_no_emails(self, correos_manager, mock_access_db):
        """Test process_pending_emails sin emails"""
        mock_access_db.execute_query.return_value = []
        result = correos_manager.process_pending_emails()
        assert result == 0

    def test_process_pending_emails_exception(self, correos_manager, mock_access_db):
        """Test process_pending_emails con excepción"""
        mock_access_db.connect.side_effect = Exception("DB Error")
        result = correos_manager.process_pending_emails()
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
    
    def test_marcar_correo_enviado_success(self, correos_manager, mock_access_db):
        """Test marcar correo enviado exitoso"""
        fecha_envio = datetime.now()
        mock_access_db.update_record.return_value = True
        
        correos_manager._marcar_correo_enviado(1, fecha_envio)
        
        mock_access_db.update_record.assert_called_once()
    
    def test_marcar_correo_enviado_exception(self, correos_manager, mock_access_db):
        """Test marcar correo enviado con excepción"""
        fecha_envio = datetime.now()
        mock_access_db.update_record.side_effect = Exception("DB Error")
        
        # El método no retorna nada, solo loggea el error
        correos_manager._marcar_correo_enviado(1, fecha_envio)

    def test_insertar_correo_success(self, correos_manager, mock_access_db):
        """Test insertar correo exitoso"""
        mock_access_db.get_max_id.return_value = 5
        mock_access_db.insert_record.return_value = True
        
        result = correos_manager.insertar_correo(
            aplicacion="TestApp",
            asunto="Test Subject",
            cuerpo="Test Body",
            destinatarios="test@example.com",
            destinatarios_cc="cc@example.com",
            destinatarios_bcc="bcc@example.com",
            url_adjunto="/path/to/file.pdf"
        )
        
        assert result == 6  # max_id + 1
        mock_access_db.connect.assert_called_once()
        mock_access_db.get_max_id.assert_called_once_with("TbCorreosEnviados", "IDCorreo")
        mock_access_db.insert_record.assert_called_once()
        mock_access_db.disconnect.assert_called_once()
    
    def test_insertar_correo_insert_failure(self, correos_manager, mock_access_db):
        """Test insertar correo con fallo en insert"""
        mock_access_db.get_max_id.return_value = 5
        mock_access_db.insert_record.return_value = False
        
        result = correos_manager.insertar_correo(
            aplicacion="TestApp",
            asunto="Test Subject",
            cuerpo="Test Body",
            destinatarios="test@example.com"
        )
        
        assert result == 0
        mock_access_db.disconnect.assert_called_once()
    
    def test_insertar_correo_exception(self, correos_manager, mock_access_db):
        """Test insertar correo con excepción"""
        mock_access_db.connect.side_effect = Exception("DB Error")
        
        result = correos_manager.insertar_correo(
            aplicacion="TestApp",
            asunto="Test Subject",
            cuerpo="Test Body",
            destinatarios="test@example.com"
        )
        
        assert result == 0
        mock_access_db.disconnect.assert_called_once()
    
    def test_insertar_correo_minimal_params(self, correos_manager, mock_access_db):
        """Test insertar correo con parámetros mínimos"""
        mock_access_db.get_max_id.return_value = 10
        mock_access_db.insert_record.return_value = True
        
        result = correos_manager.insertar_correo(
            aplicacion="TestApp",
            asunto="Test Subject",
            cuerpo="<html><body>Test HTML Body</body></html>",
            destinatarios="test@example.com"
        )
        
        assert result == 11
        
        # Verificar que se llamó insert_record con los datos correctos
        call_args = mock_access_db.insert_record.call_args
        assert call_args[0][0] == "TbCorreosEnviados"
        email_data = call_args[0][1]
        assert email_data["IDCorreo"] == 11
        assert email_data["Aplicacion"] == "TestApp"
        assert email_data["Asunto"] == "Test Subject"
        assert email_data["Destinatarios"] == "test@example.com"
        assert email_data["DestinatariosConCopia"] is None
        assert email_data["DestinatariosConCopiaOculta"] is None
        assert email_data["URLAdjunto"] is None
        assert email_data["CuerpoHTML"] is True  # Detecta HTML por < y >