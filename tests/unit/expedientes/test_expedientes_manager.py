"""Tests unitarios actualizados para ExpedientesManager refactorizado."""
import unittest
from unittest.mock import Mock
from datetime import date
import os, sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from expedientes.expedientes_manager import ExpedientesManager
from common.database import AccessDatabase


class TestExpedientesManager(unittest.TestCase):
    def setUp(self):
        self.db_exp = Mock(spec=AccessDatabase)
        self.db_tareas = Mock(spec=AccessDatabase)
        self.logger = Mock()
        self.manager = ExpedientesManager(self.db_exp, self.db_tareas, logger=self.logger)

    def test_init(self):
        self.assertIs(self.manager.db_expedientes, self.db_exp)
        self.assertIs(self.manager.db_tareas, self.db_tareas)
    # No app_id_expedientes en refactor

    def test_get_expedientes_tsol_sin_cod_s4h_success(self):
        mock_rows = [{'IDExpediente':1,'CodExp':'E1','Nemotecnico':'N','Titulo':'T','Nombre':'Cal','CadenaJuridicas':'TSOL','FECHAADJUDICACION':date(2024,1,1),'CodS4H':None}]
        self.db_exp.execute_query.return_value = mock_rows
        data = self.manager.get_expedientes_tsol_sin_cod_s4h()
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]['CodExp'],'E1')

    def test_get_expedientes_tsol_sin_cod_s4h_error(self):
        self.db_exp.execute_query.side_effect = Exception('db')
        data = self.manager.get_expedientes_tsol_sin_cod_s4h()
        self.assertEqual(data, [])
        self.assertTrue(any(k.get('extra',{}).get('context')=='get_expedientes_tsol_sin_cod_s4h' for _,k in ( (c.args,c.kwargs) for c in self.logger.error.call_args_list)))

    def test_get_expedientes_a_punto_finalizar_success(self):
        mock_rows = [{'IDExpediente':1,'CodExp':'E2','Nemotecnico':'N2','Titulo':'T2','FechaInicioContrato':date(2024,1,1),'FechaFinContrato':date(2024,12,31),'Dias':5,'FECHACERTIFICACION':date(2024,1,2),'GARANTIAMESES':12,'FechaFinGarantia':date(2025,12,31),'Nombre':'Cal'}]
        self.db_exp.execute_query.return_value = mock_rows
        data = self.manager.get_expedientes_a_punto_finalizar()
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]['CodExp'],'E2')

    def test_get_expedientes_a_punto_finalizar_error(self):
        self.db_exp.execute_query.side_effect = Exception('db')
        data = self.manager.get_expedientes_a_punto_finalizar()
        self.assertEqual(data, [])
        self.assertTrue(any(k.get('extra',{}).get('context')=='get_expedientes_a_punto_finalizar' for _,k in ( (c.args,c.kwargs) for c in self.logger.error.call_args_list)))

    def test_generate_expedientes_report_html_metrics(self):
        self.manager.get_expedientes_tsol_sin_cod_s4h = Mock(return_value=[{'IDExpediente':1,'CodExp':'E1'}])
        self.manager.get_expedientes_a_punto_finalizar = Mock(return_value=[{'IDExpediente':2,'CodExp':'E2'}])
        self.manager.get_hitos_a_punto_finalizar = Mock(return_value=[])
        self.manager.get_expedientes_estado_desconocido = Mock(return_value=[])
        self.manager.get_expedientes_adjudicados_sin_contrato = Mock(return_value=[])
        self.manager.get_expedientes_fase_oferta_mucho_tiempo = Mock(return_value=[])
        html = self.manager.generate_expedientes_report_html()
        self.assertTrue(html)
        metric_calls = [c for c in self.logger.info.call_args_list if c.kwargs.get('extra',{}).get('metric_name')]
        metrics = {c.kwargs['extra']['metric_name']:c.kwargs['extra']['metric_value'] for c in metric_calls}
        self.assertEqual(metrics.get('expedientes_report_sections'),2)
        self.assertGreater(metrics.get('expedientes_report_length_chars',0),0)

    # Tests de ejecución directa eliminados (método ejecutar_logica_especifica removido)


if __name__ == '__main__':
    unittest.main()