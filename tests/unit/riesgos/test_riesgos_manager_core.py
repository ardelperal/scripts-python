import json
import logging
from datetime import datetime, date, timedelta
from unittest.mock import Mock

import pytest

from riesgos.riesgos_manager import RiesgosManager


class DummyConfig:
    def get_db_riesgos_connection_string(self):
        return "RIE_DB"
    def get_db_tareas_connection_string(self):
        return "TAR_DB"


class TestRiesgosManagerCore:
    def setup_method(self):
        self.logger = logging.getLogger("riesgos_test")
        self.logger.handlers = []
        self.logger.addHandler(logging.NullHandler())
        self.mgr = RiesgosManager(DummyConfig(), self.logger)

    def test_log_sql_error_file_rotation(self, tmp_path):
        error_file = tmp_path / 'riesgos_sql_errors.json'
        self.mgr.error_log_file = error_file
        existing = [{"timestamp":"t","context":"c","query":"q","error_type":"E","error_message":"m","traceback":"tb"} for _ in range(105)]
        error_file.parent.mkdir(parents=True, exist_ok=True)
        error_file.write_text(json.dumps(existing), encoding='utf-8')
        self.mgr._log_sql_error("SELECT 1", Exception("boom"), context="ctx")
        data = json.loads(error_file.read_text(encoding='utf-8'))
        assert len(data) == 100
        assert any(d.get('error_message') == 'boom' for d in data)

    def test_execute_query_with_error_logging_success(self):
        db_mock = Mock()
        db_mock.execute_query.return_value = [{"a":1}]
        self.mgr.db = db_mock
        res = self.mgr._execute_query_with_error_logging("SELECT a")
        assert res == [{"a":1}]
        db_mock.execute_query.assert_called_once()

    def test_execute_query_with_error_logging_failure(self):
        class Boom(Exception):
            pass
        db_mock = Mock()
        db_mock.execute_query.side_effect = Boom("fail")
        self.mgr.db = db_mock
        with pytest.raises(Boom):
            self.mgr._execute_query_with_error_logging("BAD")
        assert self.mgr.error_count == 1

    def test_get_summary_stats(self):
        self.mgr.error_count = 2
        self.mgr.warning_count = 1
        stats = self.mgr.get_summary_stats()
        assert stats['error_count'] == 2 and stats['has_errors'] is True

    def test_disconnect_from_database_safe(self):
        db1 = Mock(); db2 = Mock()
        self.mgr.db = db1; self.mgr.db_tareas = db2
        self.mgr.disconnect_from_database()
        db1.disconnect.assert_called_once(); db2.disconnect.assert_called_once()

    def test_connect_to_database_failure(self, monkeypatch):
        from riesgos import riesgos_manager as rm

        def boom(conn):
            raise Exception("conn err")

        monkeypatch.setattr(rm, 'AccessDatabase', lambda conn: boom(conn))
        with pytest.raises(Exception):
            self.mgr.connect_to_database()

    def test_normalize_date_varios(self):
        # None
        assert self.mgr._normalize_date(None) is None
        # datetime passthrough
        now = datetime.now()
        assert self.mgr._normalize_date(now) == now
        # date -> datetime
        d = date.today()
        nd = self.mgr._normalize_date(d)
        assert nd.year == d.year and nd.hour == 0
        # string formatos
        assert self.mgr._normalize_date('2025-01-02').date() == date(2025,1,2)
        # invalid -> None (warning silenciada por logger NullHandler)
        assert self.mgr._normalize_date('xx/yy/zz') is None

    def test_calculate_days_difference(self):
        today = datetime.now()
        future = today + timedelta(days=5)
        past = today - timedelta(days=3)
        assert self.mgr._calculate_days_difference(future, today) == 5
        assert self.mgr._calculate_days_difference(past, today) == -3
        assert self.mgr._calculate_days_difference(None, today) == 0

    def test_get_last_execution_date_ok(self, monkeypatch):
        mock_db = Mock()
        mock_db.execute_query.return_value = [{'Fecha': datetime.now()}]
        self.mgr.db_tareas = mock_db
        # Patch internal call name used in riesgos_manager (get_last_execution_date uses db_tareas & column Fecha)
        result = self.mgr.get_last_execution_date('TEST')
        assert isinstance(result, date)
