import unittest
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from no_conformidades.no_conformidades_manager import NoConformidadesManager
from no_conformidades import report_registrar as rr

class TestNotificacionTecnicaIndividual(unittest.TestCase):
    def setUp(self):
        with patch('no_conformidades.no_conformidades_manager.config') as mock_conf, \
             patch('no_conformidades.no_conformidades_manager.AccessDatabase'):
            mock_conf.get_nc_css_content.return_value = '/*css*/'
            mock_conf.get_db_no_conformidades_connection_string.return_value = 'conn_nc'
            self.manager = NoConformidadesManager()

    def test_generar_correo_tecnico_individual_registra(self):
        tecnico = 'TEC1'
        ars_15 = [{'IDAccionRealizada': 11}]
        ars_7 = [{'IDAccionRealizada': 22}]
        ars_0 = [{'IDAccionRealizada': 33}]
        with patch.object(self.manager, 'get_ars_tecnico_por_vencer', side_effect=[ars_15, ars_7]), \
             patch.object(self.manager, 'get_ars_tecnico_vencidas', return_value=ars_0), \
             patch('no_conformidades.no_conformidades_manager.enviar_notificacion_tecnico_individual', return_value=True) as mock_envio:
            self.manager._generar_correo_tecnico_individual(tecnico)
            mock_envio.assert_called_once()
            args = mock_envio.call_args[0]
            self.assertEqual(args[0], tecnico)
            datos = args[1]
            self.assertIn('ars_15_dias', datos)
            self.assertEqual(len(datos['ars_7_dias']), 1)

if __name__ == '__main__':
    unittest.main()
