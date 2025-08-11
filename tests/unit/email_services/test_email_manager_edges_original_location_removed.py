from unittest.mock import MagicMock, patch

from email_services.email_manager import EmailManager


@patch("email_services.email_manager.get_correos_connection_pool")
@patch("email_services.email_manager.config")
@patch("email_services.email_manager.smtplib.SMTP")
def test_multiple_attachments_and_bcc_empty(mock_smtp, mock_config, mock_pool):
    class Pool:
        def execute_query(self, q):
            return [
                {
                    "IDCorreo": 10,
                    "Aplicacion": "App",
                    "Destinatarios": "x@example.com",
                    "DestinatariosConCopia": "y@example.com; y@example.com",
                    "DestinatariosConCopiaOculta": "   ",  # empty effectively
                    "Asunto": "Edge",
                    "Cuerpo": "Texto plano",
                    "URLAdjunto": "no_existe.pdf;tests/email_services/test_email_manager.py",
                }
            ]

        def update_record(self, *a, **k):
            pass

    mock_pool.return_value = Pool()
    mock_config.smtp_server = "localhost"
    mock_config.smtp_port = 25
    mock_config.smtp_user = "user@example.com"
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_correos_connection_string.return_value = "c"
    smtp_inst = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_inst

    mgr = EmailManager("correos")
    sent = mgr.process_pending_emails()
    assert sent == 1
    args, kwargs = smtp_inst.sendmail.call_args
    # dedup: x + y only
    assert set(args[1]) == {"x@example.com", "y@example.com"}
