"""Integración lógica (mock DB) del módulo No Conformidades.

Objetivo: Validar flujo orquestado de ejecutar_logica_especifica sin depender de
Access real, verificando delegaciones a registrar para Calidad y Técnicos.
"""
import unittest
import sys, os
from datetime import datetime, timedelta
from unittest.mock import patch

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from no_conformidades.no_conformidades_manager import NoConformidadesManager


class TestNoConformidadesIntegration(unittest.TestCase):
    def setUp(self):
        with patch('no_conformidades.no_conformidades_manager.config') as mock_conf, \
             patch('no_conformidades.no_conformidades_manager.AccessDatabase'):
            mock_conf.get_nc_css_content.return_value = '/*css*/'
            mock_conf.get_db_no_conformidades_connection_string.return_value = 'conn_nc'
            self.manager = NoConformidadesManager()

        # Datos de ejemplo
        now = datetime.now()
        self.ar_15 = [{'CodigoNoConformidad': 'NC1', 'IDAccionRealizada': 1, 'FechaFinPrevista': now + timedelta(days=12)}]
        self.ar_7 = [{'CodigoNoConformidad': 'NC1', 'IDAccionRealizada': 2, 'FechaFinPrevista': now + timedelta(days=5)}]
        self.ar_0 = [{'CodigoNoConformidad': 'NC2', 'IDAccionRealizada': 3, 'FechaFinPrevista': now - timedelta(days=1)}]
        self.nc_sin_acciones = [{'CodigoNoConformidad': 'NC3', 'Nemotecnico': 'NEM3', 'DESCRIPCION': 'Desc', 'RESPONSABLECALIDAD': 'Q1', 'FECHAAPERTURA': now}]
        self.nc_pend_ef = [{'CodigoNoConformidad': 'NC4', 'Nemotecnico': 'NEM4', 'DESCRIPCION': 'Desc2', 'RESPONSABLECALIDAD': 'Q1', 'FECHACIERRE': now, 'FechaPrevistaControlEficacia': now + timedelta(days=3)}]
        self.ar_replanificar = [{'CodigoNoConformidad': 'NC5', 'Nemotecnico': 'NEM5', 'Accion': 'A', 'Tarea': 'T', 'Tecnico': 'TEC1', 'RESPONSABLECALIDAD': 'Q1', 'FechaFinPrevista': now + timedelta(days=4), 'Dias': 4}]

    def tearDown(self):
        if hasattr(self, 'manager'):
            self.manager.close_connections()

    @patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=True)
    @patch('no_conformidades.no_conformidades_manager.enviar_notificacion_tecnico_individual', return_value=True)
    def test_flujo_completo_mixto(self, mock_tecnico_envio, mock_calidad_envio):
        with patch.object(self.manager, '_get_tecnicos_con_nc_activas', return_value=['TEC1']), \
             patch.object(self.manager, 'get_ars_tecnico_por_vencer', side_effect=[self.ar_15, self.ar_7]), \
             patch.object(self.manager, 'get_ars_tecnico_vencidas', return_value=self.ar_0), \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=self.ar_15 + self.ar_7 + self.ar_0), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=self.nc_pend_ef), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=self.nc_sin_acciones), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=self.ar_replanificar):
            ok = self.manager.ejecutar_logica_especifica()
        self.assertTrue(ok)
        mock_calidad_envio.assert_called_once()
        mock_tecnico_envio.assert_called_once()

    @patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=False)
    @patch('no_conformidades.no_conformidades_manager.enviar_notificacion_tecnico_individual', return_value=False)
    def test_flujo_sin_datos(self, mock_tecnico_envio, mock_calidad_envio):
        with patch.object(self.manager, '_get_tecnicos_con_nc_activas', return_value=[]), \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=[]), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            ok = self.manager.ejecutar_logica_especifica()
        self.assertTrue(ok)
        mock_calidad_envio.assert_not_called()
        mock_tecnico_envio.assert_not_called()

    def test_flujo_multiple_tecnicos(self):
        # Capturar llamadas técnico individuales
        capturas = []
        def fake_envio(tecnico, datos):
            capturas.append((tecnico, datos))
            return True

        now = datetime.now()
        # Para TEC1 y TEC2 retornamos secuencialmente listas diferentes
        ars_15_t1 = [{'CodigoNoConformidad': 'NC10', 'IDAccionRealizada': 10, 'FechaFinPrevista': now + timedelta(days=12)}]
        ars_7_t1 = [{'CodigoNoConformidad': 'NC11', 'IDAccionRealizada': 11, 'FechaFinPrevista': now + timedelta(days=6)}]
        ars_0_t1 = [{'CodigoNoConformidad': 'NC12', 'IDAccionRealizada': 12, 'FechaFinPrevista': now - timedelta(days=2)}]
        ars_15_t2 = [{'CodigoNoConformidad': 'NC20', 'IDAccionRealizada': 20, 'FechaFinPrevista': now + timedelta(days=14)}]
        ars_7_t2 = []
        ars_0_t2 = [{'CodigoNoConformidad': 'NC22', 'IDAccionRealizada': 22, 'FechaFinPrevista': now - timedelta(days=1)}]

        with patch('no_conformidades.no_conformidades_manager.enviar_notificacion_tecnico_individual', side_effect=fake_envio), \
             patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=True), \
             patch.object(self.manager, '_get_tecnicos_con_nc_activas', return_value=['TEC1','TEC2']), \
             patch.object(self.manager, 'get_ars_tecnico_por_vencer', side_effect=[ars_15_t1, ars_7_t1, ars_15_t2, ars_7_t2]), \
             patch.object(self.manager, 'get_ars_tecnico_vencidas', side_effect=[ars_0_t1, ars_0_t2]), \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=[]), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            ok = self.manager.ejecutar_logica_especifica()
        self.assertTrue(ok)
        self.assertEqual(len(capturas), 2)
        tecnicos_llamados = {c[0] for c in capturas}
        self.assertEqual(tecnicos_llamados, {'TEC1','TEC2'})
        # Verificar clasificación para TEC1
        datos_t1 = [d for t,d in capturas if t=='TEC1'][0]
        self.assertEqual(len(datos_t1['ars_15_dias']),1)
        self.assertEqual(len(datos_t1['ars_7_dias']),1)
        self.assertEqual(len(datos_t1['ars_vencidas']),1)

    def test_excepcion_en_datos_calidad_no_rompe(self):
        # Provocar excepción al obtener ars_proximas_vencer_calidad
        with patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=True) as mock_cal, \
             patch('no_conformidades.no_conformidades_manager.enviar_notificacion_tecnico_individual', return_value=True) as mock_tec, \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', side_effect=Exception('Fallo BD')), \
             patch.object(self.manager, '_get_tecnicos_con_nc_activas', return_value=[]), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            ok = self.manager.ejecutar_logica_especifica()
        self.assertTrue(ok)  # Lógica debería continuar y considerarse exitosa
        # No se llama a técnico ni a calidad (porque datos_calidad se queda vacío tras excepción)
        mock_cal.assert_not_called()
        mock_tec.assert_not_called()

    def test_clasificacion_por_dias_en_parametros(self):
        # Usar side effect para captar datos técnico y validar días
        capturas = []
        def fake_envio(tecnico, datos):
            capturas.append(datos)
            return True
        now = datetime.now()
        ars_15 = [{'CodigoNoConformidad':'NCX','IDAccionRealizada':101,'FechaFinPrevista': now + timedelta(days=9)}]
        ars_7 = [{'CodigoNoConformidad':'NCY','IDAccionRealizada':102,'FechaFinPrevista': now + timedelta(days=2)}]
        ars_0 = [{'CodigoNoConformidad':'NCZ','IDAccionRealizada':103,'FechaFinPrevista': now - timedelta(days=3)}]
        with patch('no_conformidades.no_conformidades_manager.enviar_notificacion_tecnico_individual', side_effect=fake_envio), \
             patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=True), \
             patch.object(self.manager, '_get_tecnicos_con_nc_activas', return_value=['TEC1']), \
             patch.object(self.manager, 'get_ars_tecnico_por_vencer', side_effect=[ars_15, ars_7]), \
             patch.object(self.manager, 'get_ars_tecnico_vencidas', return_value=ars_0), \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=[]), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            self.manager.ejecutar_logica_especifica()
        self.assertEqual(len(capturas),1)
        datos = capturas[0]
        self.assertIn('ars_15_dias', datos)
        self.assertIn('ars_7_dias', datos)
        self.assertIn('ars_vencidas', datos)
        self.assertEqual([r['IDAccionRealizada'] for r in datos['ars_15_dias']], [101])
        self.assertEqual([r['IDAccionRealizada'] for r in datos['ars_7_dias']], [102])
        self.assertEqual([r['IDAccionRealizada'] for r in datos['ars_vencidas']], [103])

    def test_html_calidad_contenido(self):
        # Capturar cuerpo HTML de calidad
        cuerpos = []
        def fake_register(application, subject, body, recipients, admin_emails=""):
            cuerpos.append(body)
            return 999  # id_correo simulado
        now = datetime.now()
        ars_prox = [{
            'CodigoNoConformidad':'NCQ1','Nemotecnico':'NEMQ','DESCRIPCION':'Desc Calidad','RESPONSABLECALIDAD':'RespQ',
            'FECHAAPERTURA': now, 'FPREVCIERRE': now + timedelta(days=5), 'DiasParaCierre':5
        }]
        with patch('no_conformidades.report_registrar._register_email_nc', side_effect=fake_register), \
             patch('no_conformidades.report_registrar.ReportRegistrar.get_quality_emails', return_value=['q@ex.com']), \
             patch('no_conformidades.report_registrar.ReportRegistrar.get_admin_emails', return_value=['admin@ex.com']), \
             patch('no_conformidades.no_conformidades_manager.enviar_notificacion_tecnico_individual', return_value=True), \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=ars_prox), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]), \
             patch.object(self.manager, '_get_tecnicos_con_nc_activas', return_value=[]):
            self.manager.ejecutar_logica_especifica()
        self.assertTrue(cuerpos, "No se capturó HTML de calidad")
        html = cuerpos[0]
        self.assertIn('Informe de No Conformidades - Calidad', html)
        self.assertIn('Acciones Correctivas/Preventivas Próximas a Caducar', html)
        self.assertIn('NCQ1', html)
        self.assertIn('Desc Calidad', html)
        self.assertIn('dias-indicador', html)

    def test_html_tecnico_contenido(self):
        cuerpos = []
        def fake_register(application, subject, body, recipients, admin_emails=""):
            cuerpos.append(body)
            return 1000
        now = datetime.now()
        ars_15 = [{'CodigoNoConformidad':'NCT1','IDAccionRealizada':1,'FechaInicio':now,'FechaFinPrevista':now+timedelta(days=10),'AccionCorrectiva':'AC','AccionRealizada':'AR','Nombre':'Tec1','DiasParaCaducar':10,'CorreoCalidad':'q@ex.com','Nemotecnico':'NEMT'}]
        with patch('no_conformidades.report_registrar._register_email_nc', side_effect=fake_register), \
             patch('no_conformidades.report_registrar._obtener_email_tecnico', return_value='tec1@ex.com'), \
             patch('no_conformidades.report_registrar.ReportRegistrar.get_admin_emails', return_value=['admin@ex.com']), \
             patch.object(self.manager, '_get_tecnicos_con_nc_activas', return_value=['TEC1']), \
             patch.object(self.manager, 'get_ars_tecnico_por_vencer', side_effect=[ars_15, []]), \
             patch.object(self.manager, 'get_ars_tecnico_vencidas', return_value=[]), \
             patch('no_conformidades.no_conformidades_manager.enviar_notificacion_calidad', return_value=True), \
             patch.object(self.manager, 'get_ars_proximas_vencer_calidad', return_value=[]), \
             patch.object(self.manager, 'get_ncs_pendientes_eficacia', return_value=[]), \
             patch.object(self.manager, 'get_ncs_sin_acciones', return_value=[]), \
             patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            self.manager.ejecutar_logica_especifica()
        self.assertTrue(cuerpos, "No se capturó HTML técnico")
        html = cuerpos[0]
        self.assertIn('Informe de Acciones Correctivas - Técnicos', html)
        self.assertIn('Acciones Correctivas con fecha fin prevista a 8-15 días', html)
        self.assertIn('NCT1', html)
        self.assertIn('AC', html)
        self.assertIn('Tec1', html)


if __name__ == '__main__':
    unittest.main()