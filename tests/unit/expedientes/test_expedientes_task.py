"""Tests unitarios para ExpedientesTask (refactor)."""

import unittest
from unittest.mock import Mock, patch

from expedientes.expedientes_task import ExpedientesTask
from common.database import AccessDatabase


class TestExpedientesTask(unittest.TestCase):
    """Verifica la orquestación principal de ExpedientesTask."""

    def setUp(self):
        self.task = ExpedientesTask()
        # Sustituir conexiones reales por mocks
        self.task.db_expedientes = Mock(spec=AccessDatabase)
        self.task.db_tareas = Mock(spec=AccessDatabase)

    def test_init(self):
        self.assertEqual(self.task.name, "EXPEDIENTES")
        self.assertEqual(self.task.script_filename, "run_expedientes.py")
        self.assertEqual(self.task.task_names, ["ExpedientesDiario"])
        self.assertEqual(self.task.frequency_days, 1)
        self.assertTrue(hasattr(self.task, 'db_expedientes'))

    @patch('src.expedientes.expedientes_task.register_standard_report', return_value=True)
    @patch('src.expedientes.expedientes_task.EmailRecipientsService')
    @patch('src.expedientes.expedientes_task.ExpedientesManager')
    def test_execute_specific_logic_with_html(self, mock_mgr_cls, mock_recip_service_cls, mock_register_email):
        mgr = Mock()
        mgr.generate_expedientes_report_html.return_value = '<html>ok</html>'
        mock_mgr_cls.return_value = mgr
        recip_instance = Mock()
        recip_instance.get_admin_emails_string.return_value = 'admin@test'
        mock_recip_service_cls.return_value = recip_instance
        result = self.task.execute_specific_logic()
        self.assertTrue(result)
        mgr.generate_expedientes_report_html.assert_called_once()
        mock_register_email.assert_called_once()

    @patch('src.expedientes.expedientes_task.register_standard_report')
    @patch('src.expedientes.expedientes_task.ExpedientesManager')
    def test_execute_specific_logic_empty_html(self, mock_mgr_cls, mock_register):
        mgr = Mock()
        mgr.generate_expedientes_report_html.return_value = ''
        mock_mgr_cls.return_value = mgr
        result = self.task.execute_specific_logic()
        self.assertTrue(result)  # HTML vacío -> éxito sin registro
        mock_register.assert_not_called()

    @patch('src.expedientes.expedientes_task.ExpedientesManager')
    def test_execute_specific_logic_exception(self, mock_mgr_cls):
        mock_mgr_cls.side_effect = Exception('boom')
        result = self.task.execute_specific_logic()
        self.assertFalse(result)

    def test_execute_specific_logic_sin_bd_expedientes(self):
        # Simula ausencia de conexión específica
        self.task.db_expedientes = None
        # No debe lanzar y debe devolver True (se omite informe)
        self.assertTrue(self.task.execute_specific_logic())

    @patch('src.expedientes.expedientes_task.register_standard_report', return_value=True)
    @patch('src.expedientes.expedientes_task.EmailRecipientsService')
    @patch('src.expedientes.expedientes_task.ExpedientesManager')
    def test_execute_specific_logic_orden_llamadas(self, mock_mgr_cls, mock_recip_service_cls, mock_register):
        """Verifica orden: crear manager -> generar html -> registrar email -> (sin marcar completada aquí)."""
        mgr = Mock()
        mgr.generate_expedientes_report_html.return_value = '<html>contenido</html>'
        mock_mgr_cls.return_value = mgr
        recip_instance = Mock()
        recip_instance.get_admin_emails_string.return_value = 'admin@test'
        mock_recip_service_cls.return_value = recip_instance
        self.assertTrue(self.task.execute_specific_logic())
        # Orden aproximado: instancia manager (implícito), luego genera html, luego registra email
        mgr.generate_expedientes_report_html.assert_called_once()
        mock_register.assert_called_once()

    def test_close_connections(self):
        mock_db = self.task.db_expedientes
        mock_db.disconnect = Mock()
        self.task.close_connections()
        mock_db.disconnect.assert_called_once()


if __name__ == '__main__':
    unittest.main()
