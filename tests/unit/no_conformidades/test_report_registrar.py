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

    # Tests legacy de notificaciones técnicas e individuales eliminados (flujo moderno usa enviar_notificacion_tecnico_individual)

    def test__register_email_nc_inserta(self):
        # Simplificación: parchear directamente get_max_id y conexión mínima
        fake_cursor = MagicMock()
        fake_conn = ContextConn(fake_cursor)
        fake_db = MagicMock(get_connection=MagicMock(return_value=fake_conn), get_max_id=MagicMock(return_value=10))
        with patch('no_conformidades.report_registrar.AccessDatabase', return_value=fake_db), \
             patch('no_conformidades.report_registrar.Config.get_db_tareas_connection_string', return_value='DSN=mem'):
            new_id = rr._register_email_nc('App','Asunto','<b>Body</b>','dest@a.com','cc@a.com')
        self.assertEqual(new_id, 11)  # max + 1
        fake_cursor.execute.assert_called_once()
        fake_db.get_max_id.assert_called_once_with('TbCorreosEnviados', 'IDCorreo')

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

# ---------------------------------------------------------------------------
# Tests unificados de enviar_notificacion_tecnico_individual (antes en archivo separado)
# Escenarios:
#  - Sin contenido HTML (generador devuelve string vacío) -> retorna True y no registra correo
#  - Sin email técnico encontrado -> retorna False
#  - Éxito completo -> registra correo y avisos AR
# ---------------------------------------------------------------------------

def test_enviar_notificacion_tecnico_individual_sin_contenido():
    datos = {"ars_15_dias": [], "ars_7_dias": [], "ars_vencidas": []}
    with patch("no_conformidades.report_registrar.HTMLReportGenerator.generar_reporte_tecnico_moderno", return_value="   ") as gen, \
         patch("no_conformidades.report_registrar._obtener_email_tecnico") as get_mail, \
         patch("no_conformidades.report_registrar._register_email_nc") as reg_mail, \
         patch("no_conformidades.report_registrar._register_arapc_notification") as reg_av:
        ok = rr.enviar_notificacion_tecnico_individual("TEC1", datos)
    assert ok is True
    gen.assert_called_once()
    get_mail.assert_not_called()  # Se sale antes de buscar email
    reg_mail.assert_not_called()
    reg_av.assert_not_called()


def test_enviar_notificacion_tecnico_individual_sin_email():
    datos = {"ars_15_dias": [{"IDAccionRealizada": 1}], "ars_7_dias": [], "ars_vencidas": []}
    with patch("no_conformidades.report_registrar.HTMLReportGenerator.generar_reporte_tecnico_moderno", return_value="<html>cuerpo</html>") as gen, \
         patch("no_conformidades.report_registrar._obtener_email_tecnico", return_value=None) as get_mail, \
         patch("no_conformidades.report_registrar._register_email_nc") as reg_mail, \
         patch("no_conformidades.report_registrar._register_arapc_notification") as reg_av:
        ok = rr.enviar_notificacion_tecnico_individual("TEC2", datos)
    assert ok is False
    gen.assert_called_once()
    get_mail.assert_called_once_with("TEC2")
    reg_mail.assert_not_called()  # Sin email no se registra
    reg_av.assert_not_called()


def test_enviar_notificacion_tecnico_individual_exito():
    datos = {
        "ars_15_dias": [{"IDAccionRealizada": 10}],
        "ars_7_dias": [{"IDAccionRealizada": 20}],
        "ars_vencidas": [{"IDAccionRealizada": 30}],
    }
    with patch("no_conformidades.report_registrar.HTMLReportGenerator.generar_reporte_tecnico_moderno", return_value="<html>ok</html>") as gen, \
         patch("no_conformidades.report_registrar._obtener_email_tecnico", return_value="tec@ex.com") as get_mail, \
         patch("no_conformidades.report_registrar.ReportRegistrar.get_admin_emails", return_value=["admin@ex.com"]) as get_admins, \
         patch("no_conformidades.report_registrar._register_email_nc", return_value=999) as reg_mail, \
         patch("no_conformidades.report_registrar._register_arapc_notification") as reg_av:
        ok = rr.enviar_notificacion_tecnico_individual("TEC3", datos)
    assert ok is True
    gen.assert_called_once()
    get_mail.assert_called_once_with("TEC3")
    reg_mail.assert_called_once()
    reg_av.assert_called_once()
    args, kwargs = reg_av.call_args
    assert args[0] == 999
    assert args[1] == [10]
    assert args[2] == [20]
    assert args[3] == [30]


if __name__ == '__main__':
    unittest.main()
