import os
import sys
from unittest.mock import MagicMock, patch

import pytest

CURR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURR)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from agedys.agedys_task import AgedysTask  # noqa: E402


@pytest.mark.integration
@patch("agedys.agedys_task.AccessDatabase")
@patch("agedys.agedys_task.register_standard_report", return_value=True)
def test_full_flow_all_empty(mock_reg, mock_db_cls):
    mock_db = MagicMock()
    mock_db_cls.return_value = mock_db
    # Manager methods all return empty
    with patch("agedys.agedys_task.AgedysManager") as mgr_cls:
        mgr = mgr_cls.return_value
        mgr.get_usuarios_con_tareas_pendientes.return_value = []
        mgr.generate_quality_report_html.return_value = ""
        mgr.generate_economy_report_html.return_value = ""
        task = AgedysTask()
        assert task.execute_specific_logic() is True
        # no reports registered
        mock_reg.assert_not_called()


@pytest.mark.integration
@patch("agedys.agedys_task.AccessDatabase")
@patch("agedys.agedys_task.register_standard_report", return_value=True)
def test_flow_some_reports(mock_reg, mock_db_cls):
    mock_db = MagicMock()
    mock_db_cls.return_value = mock_db
    with patch("agedys.agedys_task.AgedysManager") as mgr_cls:
        mgr = mgr_cls.return_value
        mgr.get_usuarios_con_tareas_pendientes.return_value = [
            {"UserId": 1, "UserName": "User1", "UserEmail": "u1@example.com"}
        ]
        mgr.generate_technical_user_report_html.return_value = "<html>t1</html>"
        mgr.generate_quality_report_html.return_value = "<html>q</html>"
        mgr.generate_economy_report_html.return_value = ""
        task = AgedysTask()
        assert task.execute_specific_logic() is True
        # technical + quality
        assert mock_reg.call_count == 2


@pytest.mark.integration
@patch("agedys.agedys_task.AccessDatabase")
@patch("agedys.agedys_task.register_standard_report", return_value=True)
def test_flow_economy_fallback_admin(mock_reg, mock_db_cls):
    mock_db = MagicMock()
    mock_db_cls.return_value = mock_db
    with patch("agedys.agedys_task.AgedysManager") as mgr_cls, patch(
        "agedys.agedys_task.EmailRecipientsService"
    ) as rec_srv_cls:
        mgr = mgr_cls.return_value
        mgr.get_usuarios_con_tareas_pendientes.return_value = []
        mgr.generate_quality_report_html.return_value = ""
        mgr.generate_economy_report_html.return_value = "<html>e</html>"
        rec_srv = rec_srv_cls.return_value
        rec_srv.get_economy_emails.return_value = []
        rec_srv.get_admin_emails.return_value = ["admin@example.com"]
        task = AgedysTask()
        assert task.execute_specific_logic() is True
        # only economy report
        assert mock_reg.call_count == 1
