from unittest.mock import MagicMock, patch

import pytest

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
                    "IDCorreo": 1,
                    "Aplicacion": "App",
                    "Destinatarios": "a@example.com;b@example.com",
                    "Asunto": "Test1",
                    "Cuerpo": "Hola",
                    "URLAdjunto": "",
                },
                {
                    "IDCorreo": 2,
                    "Aplicacion": "App",
                    "Destinatarios": "c@example.com",
                    "DestinatariosConCopia": "d@example.com",
                    "Asunto": "Test2",
                    "Cuerpo": "<html>Hi</html>",
                    "URLAdjunto": "",
                },
            ]

        def update_record(self, table, data, where):
            self.updates.append((table, data, where))

    return DummyPool()


@pytest.fixture
def mock_pools():
    """Fixture que proporciona mocks estructurados para pools de BD.
    mock_pools['correos'] es el mock que simula get_correos_connection_pool.
    Su return_value es el objeto pool real mockeado.
    """
    correos_pool = MagicMock()
    # Lista vacía de correos pendientes
    correos_pool.execute_query.return_value = []
    correos_pool.update_record = MagicMock()
    correos_getter = MagicMock(return_value=correos_pool)
    return {"correos": correos_getter, "correos_pool": correos_pool}


@patch("email_services.email_manager.get_correos_connection_pool")
@patch("email_services.email_manager.config")
@patch("email_services.email_manager.smtplib.SMTP")
def test_process_pending_emails_correos(
    mock_smtp, mock_config, mock_get_pool, mock_pool
):
    mock_config.smtp_server = "localhost"
    mock_config.smtp_port = 25
    mock_config.smtp_user = "user@example.com"
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_correos_connection_string.return_value = "conn"
    mock_get_pool.return_value = mock_pool

    sent_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = sent_server

    mgr = EmailManager("correos")
    count = mgr.process_pending_emails()
    assert count == 2
    # two update calls for sent, since _marcar_correo_enviado updates FechaEnvio
    assert len(mock_pool.updates) == 2


@patch("email_services.email_manager.get_tareas_connection_pool")
@patch("email_services.email_manager.config")
@patch("email_services.email_manager.smtplib.SMTP")
def test_process_pending_emails_tareas(mock_smtp, mock_config, mock_get_pool):
    class DummyPool2:
        def execute_query(self, q):
            return []  # no pending

        def update_record(self, *a, **k):
            pass

    mock_config.smtp_server = "localhost"
    mock_config.smtp_port = 25
    mock_config.smtp_user = "user@example.com"
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_connection_string.return_value = "conn2"
    mock_get_pool.return_value = DummyPool2()
    mock_smtp.return_value.__enter__.return_value = MagicMock()

    mgr = EmailManager("tareas")
    count = mgr.process_pending_emails()
    assert count == 0


@patch("email_services.email_manager.smtplib.SMTP", side_effect=Exception("smtp fail"))
@patch("email_services.email_manager.get_correos_connection_pool")
@patch("email_services.email_manager.config")
def test_process_pending_emails_error_path(mock_config, mock_get_pool, mock_smtp):
    class DummyPool3:
        def execute_query(self, q):
            return [
                {
                    "IDCorreo": 5,
                    "Aplicacion": "App",
                    "Destinatarios": "x@example.com",
                    "Asunto": "A",
                    "Cuerpo": "B",
                }
            ]

        def update_record(self, *a, **k):
            pass

    mock_config.smtp_server = "localhost"
    mock_config.smtp_port = 25
    mock_config.smtp_user = "user@example.com"
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_correos_connection_string.return_value = "c"
    mock_get_pool.return_value = DummyPool3()

    mgr = EmailManager("correos")
    count = mgr.process_pending_emails()
    assert count == 0


@patch("email_services.email_manager.get_correos_connection_pool")
@patch("email_services.email_manager.config")
@patch("email_services.email_manager.smtplib.SMTP")
def test_process_pending_emails_when_no_emails(
    mock_smtp, mock_config, mock_get_pool, mock_pools
):
    """Verifica que cuando no hay correos pendientes no se envía nada ni se actualiza BD."""
    # Config SMTP mínima
    mock_config.smtp_server = "localhost"
    mock_config.smtp_port = 25
    mock_config.smtp_user = "user@example.com"
    mock_config.smtp_password = None
    mock_config.smtp_tls = False
    mock_config.get_db_correos_connection_string.return_value = "conn"

    # Inyectar mock del pool (sin correos)
    mock_get_pool.side_effect = mock_pools["correos"].side_effect
    mock_get_pool.return_value = mock_pools["correos"].return_value

    mgr = EmailManager("correos")
    count = mgr.process_pending_emails()

    assert count == 0
    # No debe haberse intentado abrir conexión SMTP
    mock_smtp.assert_not_called()
    # No debe haberse intentado actualizar registros
    mock_pools["correos_pool"].update_record.assert_not_called()


@patch("src.email_services.email_manager.smtplib.SMTP")
def test_process_pending_emails_handles_smtp_connection_error(
    mock_smtp, mock_pools, monkeypatch
):
    """Simula un fallo de conexión SMTP y verifica que no se envían correos ni se actualiza BD.

    Requisitos:
    - Usa fixture mock_pools (provee pool vacío; lo ajustamos para tener un correo pendiente)
    - mock_smtp lanza ConnectionRefusedError
    - process_pending_emails devuelve 0 y no propaga excepción
    - No se llama update_record
    """
    from email_services import email_manager as em_mod

    # Config mínima
    em_mod.config.smtp_server = "localhost"
    em_mod.config.smtp_port = 25
    em_mod.config.smtp_user = "user@example.com"
    em_mod.config.smtp_password = None
    em_mod.config.smtp_tls = False
    # Reemplazar método para devolver cadena fija
    monkeypatch.setattr(
        em_mod.config,
        "get_db_correos_connection_string",
        lambda with_password=True: "conn",
    )

    # Ajustar pool para devolver un correo pendiente
    pool = mock_pools["correos_pool"]
    pool.execute_query.return_value = [
        {
            "IDCorreo": 123,
            "Aplicacion": "App",
            "Destinatarios": "x@example.com",
            "Asunto": "Test",
            "Cuerpo": "Body",
        }
    ]

    # Inyectar getter
    monkeypatch.setattr(em_mod, "get_correos_connection_pool", mock_pools["correos"])

    # Configurar SMTP para lanzar excepción al instanciar
    mock_smtp.side_effect = ConnectionRefusedError("Conexión rechazada")

    mgr = EmailManager("correos")
    count = mgr.process_pending_emails()  # No debe propagar excepción

    assert count == 0
    # No debe marcar como no enviado en fallo transitorio
    pool.update_record.assert_not_called()
    assert mock_smtp.call_count == 1


@patch("email_services.email_manager.Path")
@patch("email_services.email_manager.smtplib.SMTP")
@patch("email_services.email_manager.logger")
def test_process_pending_emails_sends_email_if_attachment_not_found(
    mock_logger, mock_smtp, mock_path
):
    """Verifica que si la URLAdjunto apunta a un fichero inexistente:
    - Se emite un warning
    - NO se intenta abrir el fichero
    - El correo se envía igualmente (SMTP llamado)
    - Se marca como enviado en la BD (update_record llamado)
    Requisitos indicados por el usuario.
    """
    # Configuración del Path simulado: cualquier instancia -> exists() == False
    path_instance = mock_path.return_value
    path_instance.exists.return_value = False

    # Simular el contexto SMTP
    smtp_ctx = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_ctx

    # Importar módulo para manipular config y pool
    from email_services import email_manager as em_mod

    # Config mínima SMTP
    em_mod.config.smtp_server = "localhost"
    em_mod.config.smtp_port = 25
    em_mod.config.smtp_user = "user@example.com"
    em_mod.config.smtp_password = None
    em_mod.config.smtp_tls = False
    em_mod.config.get_db_correos_connection_string = lambda with_password=True: "conn"

    # Pool simulado con un solo correo con URLAdjunto inexistente
    class DummyPool:
        def __init__(self):
            self.updated = []

        def execute_query(self, q):
            return [
                {
                    "IDCorreo": 999,
                    "Aplicacion": "App",
                    "Destinatarios": "dest@example.com",
                    "Asunto": "Con adjunto faltante",
                    "Cuerpo": "Contenido",
                    "URLAdjunto": "C:/ruta/no_existe/archivo.pdf",
                }
            ]

        def update_record(self, table, data, where):
            self.updated.append((table, data, where))

    dummy_pool = DummyPool()
    em_mod.get_correos_connection_pool = lambda _cs: dummy_pool

    mgr = em_mod.EmailManager("correos")
    enviados = mgr.process_pending_emails()

    # 1) Se envió 1 correo
    assert enviados == 1
    # 2) SMTP fue llamado
    mock_smtp.assert_called_once()
    # 3) update_record llamado para marcar FechaEnvio
    assert len(dummy_pool.updated) == 1
    table, data, where = dummy_pool.updated[0]
    assert table == "TbCorreosEnviados"
    assert "FechaEnvio" in data
    assert "999" in where
    # 4) Warning por adjunto no encontrado
    found_warning = False
    for call in mock_logger.warning.call_args_list:
        if "Adjunto no encontrado" in str(call):
            found_warning = True
            break
    assert found_warning, "No se registró warning de adjunto faltante"
    # 5) No se intentó abrir el adjunto (Path().open no usado)
    path_instance.open.assert_not_called()
