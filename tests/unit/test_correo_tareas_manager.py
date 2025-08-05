"""Tests unitarios para CorreoTareasManager"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys

# Agregar el directorio src al path para importaciones
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.correo_tareas.correo_tareas_manager import CorreoTareasManager


class TestCorreoTareasManager:
    """Tests para la clase CorreoTareasManager"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de configuración"""
        mock_config = Mock()
        mock_config.get_db_connection_string.return_value = "mock_connection_string"
        mock_config.smtp_server = "smtp.test.com"
        mock_config.smtp_port = 587
        mock_config.smtp_user = "test@test.com"
        mock_config.smtp_password = "password"
        mock_config.smtp_tls = True
        return mock_config

    @pytest.fixture
    def mock_db_conn(self):
        """Mock de conexión a base de datos"""
        return Mock()

    @pytest.fixture
    @patch('src.correo_tareas.correo_tareas_manager.AccessDatabase')
    @patch('src.correo_tareas.correo_tareas_manager.config')
    def correo_tareas_manager(self, mock_config_module, mock_access_db, mock_config, mock_db_conn):
        """Instancia de CorreoTareasManager con mocks"""
        mock_config_module.return_value = mock_config
        mock_access_db.return_value = mock_db_conn
        
        return CorreoTareasManager()
    
    def test_init(self, correo_tareas_manager, mock_config):
        """Test de inicialización del manager"""
        assert correo_tareas_manager is not None
        assert correo_tareas_manager.config is not None
    
    def test_obtener_correos_pendientes_success(self, correo_tareas_manager):
        """Test obtener correos pendientes exitoso"""
        # Arrange
        mock_correos = [
            {'IDCorreo': 1, 'Destinatarios': 'test@example.com', 'Asunto': 'Test'},
            {'IDCorreo': 2, 'Destinatarios': 'test2@example.com', 'Asunto': 'Test2'}
        ]
        correo_tareas_manager.db_conn.execute_query.return_value = mock_correos
        
        # Act
        result = correo_tareas_manager.obtener_correos_pendientes()
        
        # Assert
        assert len(result) == 2
        assert result[0]['IDCorreo'] == 1
        correo_tareas_manager.db_conn.execute_query.assert_called_once()
    
    def test_obtener_correos_pendientes_empty(self, correo_tareas_manager):
        """Test obtener correos pendientes cuando no hay correos"""
        # Arrange
        correo_tareas_manager.db_conn.execute_query.return_value = []
        
        # Act
        result = correo_tareas_manager.obtener_correos_pendientes()
        
        # Assert
        assert len(result) == 0
    
    def test_obtener_correos_pendientes_error(self, correo_tareas_manager):
        """Test obtener correos pendientes con error"""
        # Arrange
        correo_tareas_manager.db_conn.execute_query.side_effect = Exception("DB Error")
        
        # Act
        result = correo_tareas_manager.obtener_correos_pendientes()
        
        # Assert
        assert result == []
    
    def test_marcar_correo_enviado_success(self, correo_tareas_manager):
        """Test marcar correo como enviado exitoso"""
        # Arrange
        correo_tareas_manager.db_conn.update_record.return_value = True
        fecha_envio = datetime.now()
        
        # Act
        correo_tareas_manager._marcar_correo_enviado(1, fecha_envio)
        
        # Assert
        correo_tareas_manager.db_conn.update_record.assert_called_once()
        args = correo_tareas_manager.db_conn.update_record.call_args
        assert args[0][0] == "TbCorreosEnviados"
        assert args[0][1]["FechaEnvio"] == fecha_envio
        assert args[0][2] == "IDCorreo = 1"
    
    @patch('src.correo_tareas.correo_tareas_manager.smtplib.SMTP')
    def test_enviar_smtp_success(self, mock_smtp, correo_tareas_manager):
        """Test envío SMTP exitoso"""
        # Arrange
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        msg = Mock()
        destinatarios = ['test@example.com']
        
        # Act
        result = correo_tareas_manager._enviar_smtp(msg, destinatarios)
        
        # Assert
        assert result is True
        mock_server.sendmail.assert_called_once_with(
            correo_tareas_manager.smtp_user, destinatarios, msg.as_string()
        )
    
    @patch('src.correo_tareas.correo_tareas_manager.smtplib.SMTP')
    def test_enviar_smtp_error(self, mock_smtp, correo_tareas_manager):
        """Test envío SMTP con error"""
        # Arrange
        mock_smtp.side_effect = Exception("SMTP Error")
        msg = Mock()
        destinatarios = ['test@example.com']
        
        # Act
        result = correo_tareas_manager._enviar_smtp(msg, destinatarios)
        
        # Assert
        assert result is False
    
    @patch('src.correo_tareas.correo_tareas_manager.Path')
    def test_agregar_adjuntos_single_file(self, mock_path, correo_tareas_manager):
        """Test agregar un solo adjunto"""
        # Arrange
        msg = Mock()
        mock_file_path = Mock()
        mock_file_path.exists.return_value = True
        mock_file_path.name = 'test.pdf'
        mock_path.return_value = mock_file_path
        
        with patch('builtins.open', mock_open(read_data=b'file content')):
            # Act
            correo_tareas_manager._agregar_adjuntos(msg, '/path/to/test.pdf')
            
            # Assert
            msg.attach.assert_called_once()
    
    def test_enviar_correos_no_enviados_no_pending(self, correo_tareas_manager):
        """Test enviar correos cuando no hay pendientes"""
        # Arrange
        correo_tareas_manager.obtener_correos_pendientes = Mock(return_value=[])
        
        # Act
        result = correo_tareas_manager.enviar_correos_no_enviados()
        
        # Assert
        assert result == 0
    
    def test_enviar_correos_no_enviados_with_pending(self, correo_tareas_manager):
        """Test enviar correos con correos pendientes"""
        # Arrange
        mock_correos = [
            {'IDCorreo': 1, 'Destinatarios': 'test@example.com', 'Asunto': 'Test', 'Cuerpo': 'Test body'}
        ]
        correo_tareas_manager.obtener_correos_pendientes = Mock(return_value=mock_correos)
        correo_tareas_manager._enviar_correo_individual = Mock(return_value=True)
        
        # Act
        result = correo_tareas_manager.enviar_correos_no_enviados()
        
        # Assert
        assert result == 1
        correo_tareas_manager._enviar_correo_individual.assert_called_once_with(mock_correos[0])
    
    def test_execute_continuous_task(self, correo_tareas_manager):
        """Test ejecución de tarea continua"""
        # Arrange
        correo_tareas_manager.enviar_correos_no_enviados = Mock(return_value=5)
        
        # Act
        result = correo_tareas_manager.execute_continuous_task()
        
        # Assert
        assert result is True
        correo_tareas_manager.enviar_correos_no_enviados.assert_called_once()
    
    def test_execute_daily_task(self, correo_tareas_manager):
        """Test ejecución de tarea diaria"""
        # Arrange
        correo_tareas_manager.enviar_correos_no_enviados = Mock(return_value=3)
        
        # Act
        result = correo_tareas_manager.execute_daily_task()
        
        # Assert
        assert result is True
        correo_tareas_manager.enviar_correos_no_enviados.assert_called_once()


def mock_open(read_data=b''):
    """Helper para mockear open()"""
    mock_file = MagicMock()
    mock_file.read.return_value = read_data
    mock_file.__enter__.return_value = mock_file
    return MagicMock(return_value=mock_file)