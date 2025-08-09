import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import sys, os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from no_conformidades import report_registrar as rr
from no_conformidades.no_conformidades_manager import NoConformidadesManager


class ContextConn:
    def __init__(self, cursor):
        self._cursor = cursor
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def cursor(self):
        return self._cursor
    def commit(self):
        return None


class TestReportRegistrar(unittest.TestCase):
    def test_enviar_notificacion_calidad_ok(self):
        datos = {
            'ars_proximas_vencer': [{'CodigoNoConformidad': 'NC1'}],
            'ncs_pendientes_eficacia': [],
            'ncs_sin_acciones': [],
            'ars_para_replanificar': []
        }
        with patch.object(rr.ReportRegistrar, 'get_quality_emails', return_value=['q@a.com']), \
             patch.object(rr.ReportRegistrar, 'get_admin_emails', return_value=['admin@a.com']), \
             patch('no_conformidades.report_registrar.HTMLReportGenerator.generar_reporte_calidad_moderno', return_value='<html></html>'), \
             patch('no_conformidades.report_registrar._register_email_nc', return_value=99):
            self.assertTrue(rr.enviar_notificacion_calidad(datos))

    def test_enviar_notificacion_calidad_sin_destinatarios(self):
        datos = { 'ars_proximas_vencer': [], 'ncs_pendientes_eficacia': [], 'ncs_sin_acciones': [], 'ars_para_replanificar': [] }
        with patch.object(rr.ReportRegistrar, 'get_quality_emails', return_value=[]), \
             patch.object(rr.ReportRegistrar, 'get_admin_emails', return_value=[]):
            self.assertFalse(rr.enviar_notificacion_calidad(datos))

    def test_enviar_notificacion_tecnica_ok_con_arapcs(self):
        datos = { 'arapcs': {'15_dias': [1], '7_dias': [2], '0_dias': [3]} }
        with patch.object(rr.ReportRegistrar, 'get_quality_emails', return_value=['tec@a.com']), \
             patch.object(rr.ReportRegistrar, 'get_admin_emails', return_value=['admin@a.com']), \
             patch('no_conformidades.report_registrar.HTMLReportGenerator.generar_reporte_tecnico_moderno', return_value='<html></html>'), \
             patch('no_conformidades.report_registrar._register_email_nc', return_value=77) as reg_email, \
             patch('no_conformidades.report_registrar._register_arapc_notification', return_value=True) as reg_arapc:
            self.assertTrue(rr.enviar_notificacion_tecnica(datos))
            reg_email.assert_called_once()
            reg_arapc.assert_called_once()

    def test_enviar_notificacion_tecnica_sin_destinatarios(self):
        with patch.object(rr.ReportRegistrar, 'get_quality_emails', return_value=[]), \
             patch.object(rr.ReportRegistrar, 'get_admin_emails', return_value=[]):
            self.assertFalse(rr.enviar_notificacion_tecnica({'arapcs': {}}))

    def test_enviar_notificacion_individual_arapc_categoria(self):
        base_arapc = {
            'id_accion': 10,
            'CodigoNoConformidad': 'NCX',
            'FechaFinPrevista': datetime.now() + timedelta(days=10),
            'dias_restantes': 10
        }
        usuario = {'correo': 't@a.com'}
        # Patches dentro del método (antes estaban a nivel de clase causando fallo)
        with patch('no_conformidades.report_registrar.HTMLReportGenerator.generar_notificacion_individual_arapc', return_value='<html/>'), \
             patch('no_conformidades.report_registrar._register_email_nc', return_value=5), \
             patch('no_conformidades.report_registrar._register_arapc_notification', return_value=True) as reg_arapc:
            self.assertTrue(rr.enviar_notificacion_individual_arapc(base_arapc, usuario))
            # call_args: (id_correo, arapcs_15, arapcs_7, arapcs_0)
            args_cat = reg_arapc.call_args[0][1:]
            self.assertEqual(args_cat[0], [10])  # Debe caer en categoría 15 días

    def test__register_email_nc_inserta(self):
        # Parchar AccessDatabase para simular inserción y get_max_id
        fake_cursor = MagicMock()
        fake_cursor.execute.return_value = None
        fake_cursor.fetchall.return_value = []
        fake_cursor.fetchone.return_value = [5]
        fake_db = MagicMock()
        fake_db.get_connection.return_value = ContextConn(fake_cursor)
        fake_db.get_max_id.return_value = 10
        with patch('no_conformidades.report_registrar.AccessDatabase', return_value=fake_db), \
             patch('no_conformidades.report_registrar.Config.get_db_tareas_connection_string', return_value='DSN=mem'):
            new_id = rr._register_email_nc('App','Asunto','<b>Body</b>','dest@a.com','cc@a.com')
            self.assertEqual(new_id, 11)  # max + 1
            fake_cursor.execute.assert_called()

    def test__register_arapc_notification_registra(self):
        fake_cursor = MagicMock()
        seq = {'max':0}
        def fetchone_side_effect():
            seq['max'] += 1
            return [seq['max']-1]  # previous max
        fake_cursor.fetchone.side_effect = fetchone_side_effect
        fake_conn = ContextConn(fake_cursor)
        fake_db = MagicMock()
        fake_db.get_connection.return_value = fake_conn
        with patch('no_conformidades.report_registrar.AccessDatabase', return_value=fake_db), \
             patch('no_conformidades.report_registrar.Config.get_database_path', return_value='fake.accdb'):
            ok = rr._register_arapc_notification(99, [1,2], [3], [4])
            self.assertTrue(ok)
            # Should have executed insert for each id (2 + 1 + 1 = 4)
            inserts = [call for call in fake_cursor.execute.call_args_list if 'INSERT INTO TbNCARAvisos' in str(call)]
            self.assertEqual(len(inserts), 4)


class TestManagerDelegacion(unittest.TestCase):
    def setUp(self):
        with patch('no_conformidades.no_conformidades_manager.config') as mock_config, \
             patch('no_conformidades.no_conformidades_manager.AccessDatabase'):
            mock_config.get_nc_css_content.return_value = '/*css*/'
            mock_config.get_db_no_conformidades_connection_string.return_value = 'conn'
            self.manager = NoConformidadesManager()

    def test_generar_correo_calidad_delegacion(self):
        with patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=True) as mock_send, \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=[{'x':1}]), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            self.manager._generar_correo_calidad()
            mock_send.assert_called_once()

    def test_generar_correo_calidad_sin_datos_no_envia(self):
        with patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=True) as mock_send, \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=[]), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            self.manager._generar_correo_calidad()
            mock_send.assert_not_called()

    def test_get_ars_tecnico_error(self):
        class FakeDB:  # raises generic error
            def execute_query(self_inner, q, p):
                raise Exception('db fail')
        with patch.object(self.manager, '_get_nc_connection', return_value=FakeDB()):
            res = self.manager.get_ars_tecnico_por_vencer('TEC',8,15,'IDCorreo15')
            self.assertEqual(res, [])


if __name__ == '__main__':
    unittest.main()
