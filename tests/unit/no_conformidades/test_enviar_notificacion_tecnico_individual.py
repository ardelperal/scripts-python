"""Tests unitarios de enviar_notificacion_tecnico_individual

Escenarios:
 - Sin contenido HTML (generador devuelve string vacío) -> retorna True y no registra correo
 - Sin email técnico encontrado -> retorna False
 - Éxito completo -> registra correo y avisos AR
"""
from unittest.mock import patch

from no_conformidades.no_conformidades_manager import NoConformidadesManager


def test_enviar_notificacion_tecnico_individual_sin_contenido():
    datos = {"ars_15_dias": [], "ars_7_dias": [], "ars_vencidas": []}
    mgr = NoConformidadesManager()
    with patch.object(
        mgr, "html_generator", **{"generar_reporte_tecnico_moderno.return_value": "   "}
    ) as gen_obj, patch.object(
        mgr, "_obtener_email_tecnico"
    ) as get_mail, patch.object(
        mgr, "_register_email_nc"
    ) as reg_mail, patch.object(
        mgr, "_register_arapc_notification"
    ) as reg_av:
        ok = mgr.enviar_notificacion_tecnico_individual("TEC1", datos)
    gen = gen_obj.generar_reporte_tecnico_moderno
    assert ok is True
    gen.assert_called_once()
    get_mail.assert_not_called()
    reg_mail.assert_not_called()
    reg_av.assert_not_called()


def test_enviar_notificacion_tecnico_individual_sin_email():
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
    assert ok is False
    gen.assert_called_once()
    get_mail.assert_called_once_with("TEC2")
    reg_mail.assert_not_called()
    reg_av.assert_not_called()


def test_enviar_notificacion_tecnico_individual_exito():
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
