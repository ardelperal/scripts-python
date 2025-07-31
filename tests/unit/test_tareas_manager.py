"""
Tests unitarios para TareasManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.tareas.tareas_manager import TareasManager


class TestTareasManager:
    """Tests para la clase TareasManager"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de configuración"""
        config = Mock()
        config.smtp_server = 'localhost'
        config.smtp_port = 1025
        config.smtp_user = 'test@example.com'
        config.smtp_password = 'password'
        config.smtp_tls = False
        config.get_db_connection_string.return_value = 'mock_connection_string'
        return config
    
    @pytest.fixture
    def mock_db(self):
        """Mock de base de datos"""
        return Mock()
    
    @pytest.fixture
    def tareas_manager(self, mock_config, mock_db):
        """Instancia de TareasManager con mocks"""
        with patch('src.tareas.tareas_manager.config', mock_config), \
             patch('src.tareas.tareas_manager.AccessDatabase', return_value=mock_db):
            return TareasManager()
    
    def test_init(self, tareas_manager, mock_config):
        """Test de inicialización"""
        assert tareas_manager.smtp_server == 'localhost'
        assert tareas_manager.smtp_port == 1025
        assert tareas_manager.smtp_user == 'test@example.com'
        mock_config.get_db_connection_string.assert_called_once_with('tareas')
    
    def test_obtener_correos_pendientes_success(self, tareas_manager):
        """Test obtener correos pendientes exitoso"""
        # Arrange
        mock_correos = [
            {'IDCorreo': 1, 'Destinatarios': 'test@example.com', 'Asunto': 'Test'},
            {'IDCorreo': 2, 'Destinatarios': 'test2@example.com', 'Asunto': 'Test2'}
        ]
        tareas_manager.db_conn.execute_query.return_value = mock_correos
        
        # Act
        result = tareas_manager.obtener_correos_pendientes()
        
        # Assert
        assert len(result) == 2
        assert result[0]['IDCorreo'] == 1
        tareas_manager.db_conn.execute_query.assert_called_once()
    
    def test_obtener_correos_pendientes_empty(self, tareas_manager):
        """Test obtener correos pendientes cuando no hay correos"""
        # Arrange
        tareas_manager.db_conn.execute_query.return_value = []
        
        # Act
        result = tareas_manager.obtener_correos_pendientes()
        
        # Assert
        assert len(result) == 0
    
    def test_obtener_correos_pendientes_error(self, tareas_manager):
        """Test obtener correos pendientes con error"""
        # Arrange
        tareas_manager.db_conn.execute_query.side_effect = Exception("DB Error")
        
        # Act
        result = tareas_manager.obtener_correos_pendientes()
        
        # Assert
        assert result == []
    
    def test_marcar_correo_enviado_success(self, tareas_manager):
        """Test marcar correo como enviado exitoso"""
        # Arrange
        tareas_manager.db_conn.update_record.return_value = True
        fecha_envio = datetime.now()
        
        # Act
        tareas_manager._marcar_correo_enviado(1, fecha_envio)
        
        # Assert
        tareas_manager.db_conn.update_record.assert_called_once()
        args = tareas_manager.db_conn.update_record.call_args
        assert args[0][0] == "TbCorreosEnviados"
        assert args[0][1]["FechaEnvio"] == fecha_envio
        assert args[0][2] == "IDCorreo = 1"
    
    @patch('src.tareas.tareas_manager.smtplib.SMTP')
    def test_enviar_smtp_success(self, mock_smtp, tareas_manager):
        """Test envío SMTP exitoso"""
        # Arrange
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        msg = Mock()
        destinatarios = ['test@example.com']
        
        # Act
        result = tareas_manager._enviar_smtp(msg, destinatarios)
        
        # Assert
        assert result is True
        mock_server.sendmail.assert_called_once_with(
            tareas_manager.smtp_user, destinatarios, msg.as_string()
        )
    
    @patch('src.tareas.tareas_manager.smtplib.SMTP')
    def test_enviar_smtp_error(self, mock_smtp, tareas_manager):
        """Test envío SMTP con error"""
        # Arrange
        mock_smtp.side_effect = Exception("SMTP Error")
        msg = Mock()
        destinatarios = ['test@example.com']
        
        # Act
        result = tareas_manager._enviar_smtp(msg, destinatarios)
        
        # Assert
        assert result is False
    
    @patch('src.tareas.tareas_manager.Path')
    def test_agregar_adjuntos_single_file(self, mock_path, tareas_manager):
        """Test agregar un solo adjunto"""
        # Arrange
        msg = Mock()
        mock_file_path = Mock()
        mock_file_path.exists.return_value = True
        mock_file_path.name = 'test.pdf'
        mock_path.return_value = mock_file_path
        
        with patch('builtins.open', mock_open(read_data=b'file content')):
            # Act
            tareas_manager._agregar_adjuntos(msg, '/path/to/test.pdf')
            
            # Assert
            msg.attach.assert_called_once()
    
    def test_enviar_correos_no_enviados_no_pending(self, tareas_manager):
        """Test enviar correos cuando no hay pendientes"""
        # Arrange
        tareas_manager.obtener_correos_pendientes = Mock(return_value=[])
        
        # Act
        result = tareas_manager.enviar_correos_no_enviados()
        
        # Assert
        assert result == 0
    
    def test_enviar_correos_no_enviados_with_pending(self, tareas_manager):
        """Test enviar correos con correos pendientes"""
        # Arrange
        mock_correos = [
            {'IDCorreo': 1, 'Destinatarios': 'test@example.com', 'Asunto': 'Test', 'Cuerpo': 'Test body'}
        ]
        tareas_manager.obtener_correos_pendientes = Mock(return_value=mock_correos)
        tareas_manager._enviar_correo_individual = Mock(return_value=True)
        
        # Act
        result = tareas_manager.enviar_correos_no_enviados()
        
        # Assert
        assert result == 1
        tareas_manager._enviar_correo_individual.assert_called_once_with(mock_correos[0])
    
    def test_execute_continuous_task(self, tareas_manager):
        """Test ejecución de tarea continua"""
        # Arrange
        tareas_manager.enviar_correos_no_enviados = Mock(return_value=5)
        
        # Act
        result = tareas_manager.execute_continuous_task()
        
        # Assert
        assert result is True
        tareas_manager.enviar_correos_no_enviados.assert_called_once()
    
    def test_execute_daily_task(self, tareas_manager):
        """Test ejecución de tarea diaria"""
        # Arrange
        tareas_manager.enviar_correos_no_enviados = Mock(return_value=3)
        
        # Act
        result = tareas_manager.execute_daily_task()
        
        # Assert
        assert result is True
        tareas_manager.enviar_correos_no_enviados.assert_called_once()


def mock_open(read_data=b''):
    """Helper para mockear open()"""
    mock_file = MagicMock()
    mock_file.read.return_value = read_data
    mock_file.__enter__.return_value = mock_file
    return MagicMock(return_value=mock_file)