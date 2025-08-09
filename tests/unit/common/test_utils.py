"""
Tests unitarios para utils.py
"""
import pytest
import logging
from datetime import datetime, date
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import tempfile
import os

from src.common.utils import (
    setup_logging,
    is_workday,
    is_night_time,
    load_css_content,
    generate_html_header,
    generate_html_footer,
    safe_str,
    format_date,
    send_email
)


class TestSetupLogging:
    """Tests para la función setup_logging"""
    
    def test_setup_logging_default(self, tmp_path):
        """Test configuración básica de logging"""
        log_file = tmp_path / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            setup_logging(log_file)
            
            # Verificar que se configuró el logger
            mock_logger.setLevel.assert_called_once_with(logging.INFO)
            assert mock_logger.addHandler.call_count >= 2  # archivo + consola (+ loki si está disponible)
    
    def test_setup_logging_with_level(self, tmp_path):
        """Test configuración con nivel específico"""
        log_file = tmp_path / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            setup_logging(log_file, level=logging.DEBUG)
            
            mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
    
    def test_setup_logging_invalid_level(self, tmp_path):
        """Test configuración con nivel inválido"""
        log_file = tmp_path / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            # Pasar un nivel inválido debería funcionar (Python lo maneja)
            setup_logging(log_file, level="INVALID")
            
            mock_logger.setLevel.assert_called_once_with("INVALID")
    
    def test_setup_logging_with_file(self, tmp_path):
        """Test configuración con archivo de log"""
        log_file = tmp_path / "logs" / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            setup_logging(log_file)
            
            # Verificar que se creó el directorio
            assert log_file.parent.exists()
            
            # Verificar que se añadieron handlers
            assert mock_logger.addHandler.call_count >= 2  # archivo + consola
    
    def test_setup_logging_clears_existing_handlers(self, tmp_path):
        """Test que se limpian handlers existentes"""
        log_file = tmp_path / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = True
            mock_handlers = Mock()
            mock_logger.handlers = mock_handlers
            mock_get_logger.return_value = mock_logger
            
            setup_logging(log_file)
            
            # Verificar que se limpiaron los handlers
            mock_handlers.clear.assert_called_once()
    
    @patch.dict(os.environ, {'LOKI_URL': 'http://test-loki:3100', 'ENVIRONMENT': 'test'})
    def test_setup_logging_with_loki_success(self, tmp_path):
        """Test configuración exitosa con Loki"""
        log_file = tmp_path / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            with patch('src.common.utils.LokiQueueHandler') as mock_loki_handler:
                with patch('src.common.utils.Queue') as mock_queue:
                    mock_handler_instance = Mock()
                    mock_loki_handler.return_value = mock_handler_instance
                    mock_queue_instance = Mock()
                    mock_queue.return_value = mock_queue_instance
                    
                    setup_logging(log_file)
                    
                    # Verificar que se creó el LokiQueueHandler con los parámetros correctos
                    mock_loki_handler.assert_called_once_with(
                        queue=mock_queue_instance,
                        url='http://test-loki:3100/loki/api/v1/push',
                        tags={
                            "application": "scripts_python",
                            "environment": "test"
                        },
                        version="1"
                    )
                    
                    # Verificar que se añadió el handler
                    mock_logger.addHandler.assert_any_call(mock_handler_instance)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_logging_without_loki_url(self, tmp_path):
        """Test cuando LOKI_URL no está configurada"""
        log_file = tmp_path / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            with patch('logging.info') as mock_info:
                setup_logging(log_file)
                
                # Verificar que se registró el mensaje informativo
                mock_info.assert_called_with("LOKI_URL no configurada. Logging configurado solo para archivo y consola.")
    
    @patch.dict(os.environ, {'LOKI_URL': 'http://test-loki:3100'})
    def test_setup_logging_loki_general_error(self, tmp_path):
        """Test error general al configurar Loki"""
        log_file = tmp_path / "test.log"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            with patch('src.common.utils.LokiQueueHandler', side_effect=Exception("Connection error")):
                with patch('logging.warning') as mock_warning:
                    setup_logging(log_file)
                    
                    # Verificar que se registró el warning con el error
                    mock_warning.assert_called_with("No se pudo configurar Loki handler: Connection error. Continuando solo con archivo y consola.")


class TestIsWorkday:
    """Tests para la función is_workday"""
    
    def test_is_workday_monday(self):
        """Test día lunes (laborable)"""
        monday = date(2024, 1, 1)  # 1 enero 2024 es lunes
        assert is_workday(monday) is True
    
    def test_is_workday_friday(self):
        """Test día viernes (laborable)"""
        friday = date(2024, 1, 5)  # 5 enero 2024 es viernes
        assert is_workday(friday) is True
    
    def test_is_workday_saturday(self):
        """Test día sábado (no laborable)"""
        saturday = date(2024, 1, 6)  # 6 enero 2024 es sábado
        assert is_workday(saturday) is False
    
    def test_is_workday_sunday(self):
        """Test día domingo (no laborable)"""
        sunday = date(2024, 1, 7)  # 7 enero 2024 es domingo
        assert is_workday(sunday) is False
    
    def test_is_workday_with_holidays_file_exists(self, tmp_path):
        """Test con archivo de festivos que existe"""
        holidays_file = tmp_path / "holidays.txt"
        holidays_file.write_text("2024-01-01\n2024-12-25\n", encoding='utf-8')
        
        holiday = date(2024, 1, 1)  # Día en el archivo de festivos
        normal_day = date(2024, 1, 2)  # Día no en el archivo
        
        assert is_workday(holiday, holidays_file) is False
        assert is_workday(normal_day, holidays_file) is True
    
    def test_is_workday_with_holidays_file_not_exists(self, tmp_path):
        """Test con archivo de festivos que no existe"""
        holidays_file = tmp_path / "nonexistent.txt"
        monday = date(2024, 1, 1)
        
        assert is_workday(monday, holidays_file) is True
    
    def test_is_workday_holidays_file_read_error(self, tmp_path):
        """Test error al leer archivo de festivos"""
        holidays_file = tmp_path / "holidays.txt"
        holidays_file.write_text("2024-01-01", encoding='utf-8')
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('logging.warning') as mock_warning:
                monday = date(2024, 1, 1)
                result = is_workday(monday, holidays_file)
                
                assert result is True  # Debería devolver True en caso de error
                mock_warning.assert_called_once()


class TestIsNightTime:
    """Tests para la función is_night_time"""
    
    def test_is_night_time_evening(self):
        """Test horario nocturno (20:00)"""
        evening_time = datetime(2024, 1, 1, 20, 0)
        assert is_night_time(evening_time) is True
    
    def test_is_night_time_late_night(self):
        """Test horario nocturno (23:00)"""
        late_night = datetime(2024, 1, 1, 23, 0)
        assert is_night_time(late_night) is True
    
    def test_is_night_time_early_morning(self):
        """Test horario nocturno (06:00)"""
        early_morning = datetime(2024, 1, 1, 6, 0)
        assert is_night_time(early_morning) is True
    
    def test_is_night_time_day_time(self):
        """Test horario diurno (12:00)"""
        day_time = datetime(2024, 1, 1, 12, 0)
        assert is_night_time(day_time) is False
    
    def test_is_night_time_morning(self):
        """Test horario diurno (08:00)"""
        morning = datetime(2024, 1, 1, 8, 0)
        assert is_night_time(morning) is False
    
    def test_is_night_time_default_current_time(self):
        """Test usando tiempo actual por defecto"""
        with patch('src.common.utils.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 21, 0)
            mock_datetime.now.return_value = mock_now
            
            result = is_night_time()
            assert result is True


class TestLoadCssContent:
    """Tests para la función load_css_content"""
    
    def test_load_css_content_success_utf8(self, tmp_path):
        """Test carga exitosa con UTF-8"""
        css_file = tmp_path / "style.css"
        css_content = "body { color: red; }"
        css_file.write_text(css_content, encoding='utf-8')
        
        with patch('logging.info') as mock_info:
            result = load_css_content(css_file)
            assert result == css_content
            mock_info.assert_called_once()
    
    def test_load_css_content_success_latin1(self, tmp_path):
        """Test carga exitosa con latin1"""
        css_file = tmp_path / "style.css"
        css_content = "body { color: blue; }"
        
        # Simular que UTF-8 falla pero latin1 funciona
        with patch('builtins.open', side_effect=[
            UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'),
            mock_open(read_data=css_content).return_value
        ]):
            with patch('logging.info') as mock_info:
                result = load_css_content(css_file)
                assert result == css_content
                mock_info.assert_called_once()
    
    def test_load_css_content_all_encodings_fail(self, tmp_path):
        """Test cuando todos los encodings fallan"""
        css_file = tmp_path / "style.css"
        css_file.write_text("content", encoding='utf-8')
        
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            with patch('logging.warning') as mock_warning:
                result = load_css_content(css_file)
                
                # Debería devolver CSS por defecto
                assert "body { font-family: Arial" in result
                mock_warning.assert_called_once()
    
    def test_load_css_content_file_error(self, tmp_path):
        """Test error al leer archivo"""
        css_file = tmp_path / "style.css"
        css_file.write_text("content", encoding='utf-8')
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('logging.error') as mock_error:
                with patch('logging.warning') as mock_warning:
                    result = load_css_content(css_file)
                    
                    # Debería devolver CSS por defecto
                    assert "body { font-family: Arial" in result
                    mock_error.assert_called_once()
                    mock_warning.assert_called_once()


class TestGenerateHtmlHeader:
    """Tests para la función generate_html_header"""
    
    def test_generate_html_header(self):
        """Test generación de header HTML"""
        title = "Test Page"
        css_content = "body { color: red; }"
        
        result = generate_html_header(title, css_content)
        
        assert "<!DOCTYPE html>" in result
        assert f"<title>{title}</title>" in result
        assert css_content in result
        assert '<meta charset="UTF-8"' in result


class TestGenerateHtmlFooter:
    """Tests para la función generate_html_footer"""
    
    def test_generate_html_footer(self):
        """Test generación de footer HTML"""
        result = generate_html_footer()
        
        assert "</body>" in result
        assert "</html>" in result


class TestSafeStr:
    """Tests para la función safe_str"""
    
    def test_safe_str_normal_value(self):
        """Test con valor normal"""
        assert safe_str("test") == "test"
        assert safe_str(123) == "123"
    
    def test_safe_str_none_value(self):
        """Test con valor None"""
        assert safe_str(None) == "&nbsp;"
    
    def test_safe_str_empty_string(self):
        """Test con string vacío"""
        assert safe_str("") == "&nbsp;"
    
    def test_safe_str_custom_default(self):
        """Test con valor por defecto personalizado"""
        assert safe_str(None, "N/A") == "N/A"
        assert safe_str("", "EMPTY") == "EMPTY"


class TestFormatDate:
    """Tests para la función format_date"""
    
    def test_format_date_none(self):
        """Test con valor None"""
        assert format_date(None) == ""
    
    def test_format_date_datetime_object(self):
        """Test con objeto datetime"""
        dt = datetime(2024, 1, 15, 10, 30)
        result = format_date(dt)
        assert result == "15/01/2024"
    
    def test_format_date_date_object(self):
        """Test con objeto date"""
        d = date(2024, 1, 15)
        result = format_date(d)
        assert result == "15/01/2024"
    
    def test_format_date_custom_format(self):
        """Test con formato personalizado"""
        dt = datetime(2024, 1, 15, 10, 30)
        result = format_date(dt, "%Y-%m-%d")
        assert result == "2024-01-15"
    
    def test_format_date_string_iso(self):
        """Test con string en formato ISO"""
        result = format_date("2024-01-15")
        assert result == "15/01/2024"
    
    def test_format_date_string_spanish(self):
        """Test con string en formato español"""
        result = format_date("15/01/2024")
        assert result == "15/01/2024"
    
    def test_format_date_string_with_time(self):
        """Test con string que incluye hora"""
        result = format_date("2024-01-15 10:30:00")
        assert result == "15/01/2024"
    
    def test_format_date_invalid_string(self):
        """Test con string inválido"""
        result = format_date("invalid_date")
        assert result == "invalid_date"
    
    def test_format_date_string_parse_exception(self):
        """Test excepción al parsear string"""
        # Usar un string que cause excepción en el parsing pero no en strptime
        result = format_date("not-a-date-format")
        assert result == "not-a-date-format"
    
    def test_format_date_other_type(self):
        """Test con otro tipo de dato"""
        result = format_date(12345)
        assert result == "12345"


class TestSendEmail:
    """Tests para la función send_email"""
    
    @patch('smtplib.SMTP')
    @patch('src.common.utils.config')
    def test_send_email_success(self, mock_config, mock_smtp):
        """Test envío exitoso de email"""
        # Configurar mocks
        mock_config.smtp_server = "localhost"
        mock_config.smtp_port = 25
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        with patch('logging.info') as mock_info:
            result = send_email("test@example.com", "Test Subject", "Test Body")
            
            assert result is True
            mock_info.assert_called_once()
            assert "test@example.com" in mock_info.call_args[0][0]
            assert "Test Subject" in mock_info.call_args[0][0]
            mock_smtp_instance.sendmail.assert_called_once()
    
    @patch('smtplib.SMTP')
    @patch('src.common.utils.config')
    def test_send_email_html_false(self, mock_config, mock_smtp):
        """Test envío con HTML desactivado"""
        # Configurar mocks
        mock_config.smtp_server = "localhost"
        mock_config.smtp_port = 25
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        with patch('logging.info') as mock_info:
            result = send_email("test@example.com", "Subject", "Body", is_html=False)
            
            assert result is True
            mock_info.assert_called_once()
            mock_smtp_instance.sendmail.assert_called_once()
    
    @patch('smtplib.SMTP')
    @patch('src.common.utils.config')
    def test_send_email_failure(self, mock_config, mock_smtp):
        """Test fallo en envío de email"""
        # Configurar mocks
        mock_config.smtp_server = "localhost"
        mock_config.smtp_port = 25
        mock_smtp.side_effect = Exception("SMTP Error")
        
        with patch('logging.error') as mock_error:
            result = send_email("test@example.com", "Subject", "Body")
            
            assert result is False
            mock_error.assert_called_once()
            assert "Error enviando email" in mock_error.call_args[0][0]