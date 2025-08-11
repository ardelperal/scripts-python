from unittest.mock import MagicMock, patch

from email_services.email_task import EmailServicesTask


@patch("email_services.email_task.EmailManager")
def test_email_services_task_execute(mock_manager_cls):
    inst1 = MagicMock()
    inst2 = MagicMock()
    inst1.process_pending_emails.return_value = 1
    inst2.process_pending_emails.return_value = 0
    # Side effects for two instantiations
    mock_manager_cls.side_effect = [inst1, inst2]

    task = EmailServicesTask()
    ok = task.execute_specific_logic()

    assert ok is True
    assert inst1.process_pending_emails.called
    assert inst2.process_pending_emails.called
