import os
import sys
import unittest
from unittest.mock import MagicMock, patch

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


class TestManagerEmailRegistro(unittest.TestCase):
    def test_enviar_notificacion_calidad_ok(self):
        datos = {
            "ars_proximas_vencer": [{"CodigoNoConformidad": "NC1"}],
            "ncs_pendientes_eficacia": [],
            "ncs_sin_acciones": [],
            "ars_para_replanificar": [],
        }
        mgr = NoConformidadesManager()
        with patch.object(mgr, "get_quality_users", return_value=[{"Correo": "q@a.com"}]), patch.object(
            mgr, "get_admin_users", return_value=[{"Correo": "admin@a.com"}]
        ), patch.object(
            mgr, "html_generator", **{"generar_reporte_calidad_moderno.return_value": "<html></html>"}
        ), patch.object(
            mgr, "_register_email_nc", return_value=99
        ):
            self.assertTrue(mgr.enviar_notificacion_calidad(datos))

    def test_enviar_notificacion_calidad_sin_destinatarios(self):
        datos = {
            "ars_proximas_vencer": [],
            "ncs_pendientes_eficacia": [],
            "ncs_sin_acciones": [],
            "ars_para_replanificar": [],
        }
        mgr = NoConformidadesManager()
        with patch.object(mgr, "get_quality_users", return_value=[]), patch.object(
            mgr, "get_admin_users", return_value=[]
        ):
            self.assertFalse(mgr.enviar_notificacion_calidad(datos))

    def test__register_email_nc_inserta(self):
        fake_cursor = MagicMock()
        fake_conn = ContextConn(fake_cursor)
        fake_db = MagicMock(
            get_connection=MagicMock(return_value=fake_conn),
            get_max_id=MagicMock(return_value=10),
        )
        with patch(
            "no_conformidades.no_conformidades_manager.AccessDatabase", return_value=fake_db
        ), patch(
            "no_conformidades.no_conformidades_manager.config"
        ) as mock_conf:
            mock_conf.get_nc_css_content.return_value = "/*css*/"
            mock_conf.get_db_no_conformidades_connection_string.return_value = "conn_nc"
            mgr = NoConformidadesManager()
            new_id = mgr._register_email_nc(
                application="App",
                subject="Asunto",
                body="<b>Body</b>",
                recipients="dest@a.com",
                admin_emails="cc@a.com",
            )
        self.assertEqual(new_id, 11)
        fake_cursor.execute.assert_called_once()
        fake_db.get_max_id.assert_called_once_with("TbCorreosEnviados", "IDCorreo")

    def test__register_arapc_notification_registra(self):
        fake_cursor = MagicMock()
        seq = {"max": 0}

        def fetchone_side_effect():
            seq["max"] += 1
            return [seq["max"] - 1]

        fake_cursor.fetchone.side_effect = fetchone_side_effect
        fake_conn = ContextConn(fake_cursor)
        fake_db = MagicMock()
        fake_db.get_connection.return_value = fake_conn
        with patch(
            "no_conformidades.no_conformidades_manager.AccessDatabase", return_value=fake_db
        ), patch(
            "no_conformidades.no_conformidades_manager.config.get_database_path",
            return_value="fake.accdb",
        ):
            mgr = NoConformidadesManager()
            ok = mgr._register_arapc_notification(99, [1, 2], [3], [4])
        self.assertTrue(ok)
        inserts = [
            call
            for call in fake_cursor.execute.call_args_list
            if "INSERT INTO TbNCARAvisos" in str(call)
        ]
        self.assertEqual(len(inserts), 4)


class TestManagerDelegacion(unittest.TestCase):
    def setUp(self):
        with patch(
            "no_conformidades.no_conformidades_manager.config"
        ) as mock_config, patch(
            "no_conformidades.no_conformidades_manager.AccessDatabase"
        ):
            mock_config.get_nc_css_content.return_value = "/*css*/"
            mock_config.get_db_no_conformidades_connection_string.return_value = "conn"
            self.manager = NoConformidadesManager()

    def test_generar_correo_calidad_delegacion(self):
        with patch.object(
            self.manager, "get_ars_proximas_vencer_calidad", return_value=[{"x": 1}]
        ), patch.object(
            self.manager, "get_ncs_pendientes_eficacia", return_value=[]
        ), patch.object(
            self.manager, "get_ncs_sin_acciones", return_value=[]
        ), patch.object(
            self.manager, "get_ars_para_replanificar", return_value=[]
        ), patch.object(
            self.manager, "enviar_notificacion_calidad", return_value=True
        ) as mock_send:
            self.manager._generar_correo_calidad()
            mock_send.assert_called_once()

    def test_generar_correo_calidad_sin_datos_no_envia(self):
        with patch.object(
            self.manager, "get_ars_proximas_vencer_calidad", return_value=[]
        ), patch.object(
            self.manager, "get_ncs_pendientes_eficacia", return_value=[]
        ), patch.object(
            self.manager, "get_ncs_sin_acciones", return_value=[]
        ), patch.object(
            self.manager, "get_ars_para_replanificar", return_value=[]
        ), patch.object(
            self.manager, "enviar_notificacion_calidad", return_value=True
        ) as mock_send:
            self.manager._generar_correo_calidad()
            mock_send.assert_not_called()

    def test_get_ars_tecnico_error(self):
        class FakeDB:
            def execute_query(self_inner, q, p):
                raise Exception("db fail")

        with patch.object(self.manager, "_get_nc_connection", return_value=FakeDB()):
            res = self.manager.get_ars_tecnico_por_vencer("TEC", 8, 15, "IDCorreo15")
            self.assertEqual(res, [])


class TestNotificacionTecnicaIndividual(unittest.TestCase):
    def test_enviar_notificacion_tecnico_individual_sin_contenido(self):
        datos = {"ars_15_dias": [], "ars_7_dias": [], "ars_vencidas": []}
        mgr = NoConformidadesManager()
        with patch.object(
            mgr, "html_generator", **{"generar_reporte_tecnico_moderno.return_value": "   "}
        ) as gen_obj, patch.object(
            mgr, "_register_email_nc"
        ) as reg_mail, patch.object(
            mgr, "_register_arapc_notification"
        ) as reg_av:
            ok = mgr.enviar_notificacion_tecnico_individual("TEC1", datos)
        gen = gen_obj.generar_reporte_tecnico_moderno
        self.assertTrue(ok)
        gen.assert_called_once()
        reg_mail.assert_not_called()
        reg_av.assert_not_called()

    def test_enviar_notificacion_tecnico_individual_sin_email(self):
        datos = {"ars_15_dias": [{"IDAccionRealizada": 1}], "ars_7_dias": [], "ars_vencidas": []}
        mgr = NoConformidadesManager()
        with patch.object(
            mgr, "html_generator", **{"generar_reporte_tecnico_moderno.return_value": "<html>cuerpo</html>"}
        ) as gen_obj, patch.object(
            mgr, "_obtener_email_tecnico", return_value=None
        ) as get_mail, patch.object(
            mgr, "_register_email_nc"
        ) as reg_mail, patch.object(
            mgr, "_register_arapc_notification"
        ) as reg_av:
            ok = mgr.enviar_notificacion_tecnico_individual("TEC2", datos)
        gen = gen_obj.generar_reporte_tecnico_moderno
        self.assertFalse(ok)
        gen.assert_called_once()
        get_mail.assert_called_once_with("TEC2")
        reg_mail.assert_not_called()
        reg_av.assert_not_called()

    def test_enviar_notificacion_tecnico_individual_exito(self):
        datos = {"ars_15_dias": [{"IDAccionRealizada": 10}], "ars_7_dias": [{"IDAccionRealizada": 20}], "ars_vencidas": [{"IDAccionRealizada": 30}]}
        mgr = NoConformidadesManager()
        with patch.object(
            mgr, "html_generator", **{"generar_reporte_tecnico_moderno.return_value": "<html>ok</html>"}
        ) as gen_obj, patch.object(
            mgr, "_obtener_email_tecnico", return_value="tec@ex.com"
        ) as get_mail, patch.object(
            mgr, "get_admin_users", return_value=[{"Correo": "admin@ex.com"}]
        ), patch.object(
            mgr, "_register_email_nc", return_value=999
        ) as reg_mail, patch.object(
            mgr, "_register_arapc_notification"
        ) as reg_av:
            ok = mgr.enviar_notificacion_tecnico_individual("TEC3", datos)
        gen = gen_obj.generar_reporte_tecnico_moderno
        self.assertTrue(ok)
        gen.assert_called_once()
        get_mail.assert_called_once_with("TEC3")
        reg_mail.assert_called_once()
        reg_av.assert_called_once()
        args, kwargs = reg_av.call_args
        self.assertEqual(args[0], 999)
        self.assertEqual(args[1], [10])
        self.assertEqual(args[2], [20])
        self.assertEqual(args[3], [30])


if __name__ == "__main__":
    unittest.main()
