"""Integration-style test for unified EmailServicesTask processing both sources.
Simulates DB pools for 'correos' and 'tareas' without touching real Access files.
"""
from unittest.mock import MagicMock, patch

from email_services.email_task import EmailServicesTask


class DummyPool:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []
        self.updates = []

    def execute_query(self, q):  # simplistic capture
        self.queries.append(q)
        return list(self.rows)

    def update_record(self, table, data, where):
        self.updates.append((table, data, where))
        return True


@patch("email_services.email_manager.smtplib.SMTP")
@patch("email_services.email_manager.get_tareas_connection_pool")
@patch("email_services.email_manager.get_correos_connection_pool")
@patch("email_services.email_manager.config")
def test_email_services_task_full_cycle(
    mock_config, mock_get_correos_pool, mock_get_tareas_pool, mock_smtp
):
    # Configure fake config
    mock_config.smtp_server = "localhost"
    mock_config.smtp_port = 25
    mock_config.smtp_user = "user@example.com"
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_correos_connection_string.return_value = "c_conn"
    mock_config.get_db_connection_string.return_value = "t_conn"

    # Two pending in correos, one in tareas
    correos_rows = [
        {
            "IDCorreo": 1,
            "Aplicacion": "App",
            "Destinatarios": "a@example.com",
            "Asunto": "A1",
            "Cuerpo": "Body1",
        },
        {
            "IDCorreo": 2,
            "Aplicacion": "App",
            "Destinatarios": "b@example.com",
            "Asunto": "A2",
            "Cuerpo": "Body2",
        },
    ]
    tareas_rows = [
        {
            "IDCorreo": 10,
            "Aplicacion": "Task",
            "Destinatarios": "c@example.com",
            "Asunto": "T1",
            "Cuerpo": "TB",
        },
    ]

    correos_pool = DummyPool(correos_rows)
    tareas_pool = DummyPool(tareas_rows)
    mock_get_correos_pool.return_value = correos_pool
    mock_get_tareas_pool.return_value = tareas_pool

    smtp_inst = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_inst

    task = EmailServicesTask()
    ok = task.execute_specific_logic()

    assert ok is True
    # We expect three sendmail calls total
    assert smtp_inst.sendmail.call_count == 3
    # Each pool should have update calls matching its rows
    assert len(correos_pool.updates) == 2
    assert len(tareas_pool.updates) == 1
