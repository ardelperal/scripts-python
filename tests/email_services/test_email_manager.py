import pytest
from unittest.mock import MagicMock, patch
from email_services.email_manager import EmailManager

@pytest.fixture
def mock_pool():
    class DummyPool:
        def __init__(self):
            self.queries = []
            self.updates = []
        def execute_query(self, q):
            self.queries.append(q)
            # Return two fake pending emails
            return [
                {
                    'IDCorreo': 1,
                    'Aplicacion': 'App',
                    'Destinatarios': 'a@example.com;b@example.com',
                    'Asunto': 'Test1',
                    'Cuerpo': 'Hola',
                    'URLAdjunto': ''
                },
                {
                    'IDCorreo': 2,
                    'Aplicacion': 'App',
                    'Destinatarios': 'c@example.com',
                    'DestinatariosConCopia': 'd@example.com',
                    'Asunto': 'Test2',
                    'Cuerpo': '<html>Hi</html>',
                    'URLAdjunto': ''
                }
            ]
        def update_record(self, table, data, where):
            self.updates.append((table, data, where))
    return DummyPool()

@patch('email_services.email_manager.get_correos_connection_pool')
@patch('email_services.email_manager.config')
@patch('email_services.email_manager.smtplib.SMTP')
def test_process_pending_emails_correos(mock_smtp, mock_config, mock_get_pool, mock_pool):
    mock_config.smtp_server = 'localhost'
    mock_config.smtp_port = 25
    mock_config.smtp_user = 'user@example.com'
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_correos_connection_string.return_value = 'conn'
    mock_get_pool.return_value = mock_pool

    sent_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = sent_server

    mgr = EmailManager('correos')
    count = mgr.process_pending_emails()
    assert count == 2
    # two update calls for sent, since _marcar_correo_enviado updates FechaEnvio
    assert len(mock_pool.updates) == 2

@patch('email_services.email_manager.get_tareas_connection_pool')
@patch('email_services.email_manager.config')
@patch('email_services.email_manager.smtplib.SMTP')
def test_process_pending_emails_tareas(mock_smtp, mock_config, mock_get_pool):
    class DummyPool2:
        def execute_query(self, q):
            return []  # no pending
        def update_record(self, *a, **k):
            pass
    mock_config.smtp_server = 'localhost'
    mock_config.smtp_port = 25
    mock_config.smtp_user = 'user@example.com'
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_connection_string.return_value = 'conn2'
    mock_get_pool.return_value = DummyPool2()
    mock_smtp.return_value.__enter__.return_value = MagicMock()

    mgr = EmailManager('tareas')
    count = mgr.process_pending_emails()
    assert count == 0

@patch('email_services.email_manager.smtplib.SMTP', side_effect=Exception('smtp fail'))
@patch('email_services.email_manager.get_correos_connection_pool')
@patch('email_services.email_manager.config')
def test_process_pending_emails_error_path(mock_config, mock_get_pool, mock_smtp):
    class DummyPool3:
        def execute_query(self, q):
            return [{'IDCorreo': 5, 'Aplicacion': 'App', 'Destinatarios': 'x@example.com', 'Asunto': 'A', 'Cuerpo': 'B'}]
        def update_record(self, *a, **k):
            pass
    mock_config.smtp_server = 'localhost'
    mock_config.smtp_port = 25
    mock_config.smtp_user = 'user@example.com'
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_correos_connection_string.return_value = 'c'
    mock_get_pool.return_value = DummyPool3()

    mgr = EmailManager('correos')
    count = mgr.process_pending_emails()
    assert count == 0
