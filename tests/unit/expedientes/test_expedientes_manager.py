"""
Tests unitarios para ExpedientesManager
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import os
import sys

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'src')
sys.path.insert(0, src_dir)

from expedientes.expedientes_manager import ExpedientesManager


class TestExpedientesManager(unittest.TestCase):
    """Tests para ExpedientesManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        with patch('expedientes.expedientes_manager.Config'), \
             patch('expedientes.expedientes_manager.ExpedientesManager._load_css_content', return_value="body { color: blue; }"):
            self.manager = ExpedientesManager()
    
    @patch('expedientes.expedientes_manager.Config')
    @patch('expedientes.expedientes_manager.ExpedientesManager._load_css_content')
    def test_init(self, mock_load_css, mock_config):
        """Test de inicialización del manager"""
        mock_load_css.return_value = "body { color: red; }"
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        manager = ExpedientesManager()
        
        # Verificar que se inicializa correctamente
        self.assertEqual(manager.name, "EXPEDIENTES")
        self.assertEqual(manager.script_filename, "run_expedientes.py")
        self.assertEqual(manager.task_names, ["ExpedientesDiario"])
        self.assertEqual(manager.frequency_days, 1)
        self.assertIsNone(manager.db_expedientes)
        self.assertIsNone(manager.db_tareas)
        self.assertEqual(manager.css_content, "body { color: red; }")
    
    def test_get_expedientes_connection(self):
        """Test de obtención de conexión a base de datos de expedientes"""
        with patch('expedientes.expedientes_manager.AccessDatabase') as mock_db:
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            
            connection = self.manager._get_expedientes_connection()
            
            self.assertEqual(connection, mock_db_instance)
            self.assertEqual(self.manager.db_expedientes, mock_db_instance)
    
    def test_get_tareas_connection(self):
        """Test de obtención de conexión a base de datos de tareas"""
        with patch('expedientes.expedientes_manager.AccessDatabase') as mock_db:
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            
            connection = self.manager._get_tareas_connection()
            
            self.assertEqual(connection, mock_db_instance)
            self.assertEqual(self.manager.db_tareas, mock_db_instance)
    
    def test_format_date_display_none(self):
        """Test de formateo de fecha None"""
        result = self.manager._format_date_display(None)
        self.assertEqual(result, '&nbsp;')
    
    def test_format_date_display_string_date(self):
        """Test de formateo de fecha string"""
        result = self.manager._format_date_display("2024-01-15")
        self.assertEqual(result, "15/01/2024")
    
    def test_format_date_display_datetime(self):
        """Test de formateo de datetime"""
        test_date = datetime(2024, 1, 15)
        result = self.manager._format_date_display(test_date)
        self.assertEqual(result, "15/01/2024")
    
    def test_format_date_display_date(self):
        """Test de formateo de date"""
        test_date = date(2024, 1, 15)
        result = self.manager._format_date_display(test_date)
        self.assertEqual(result, "15/01/2024")
    
    def test_format_date_display_invalid(self):
        """Test de formateo de fecha inválida"""
        result = self.manager._format_date_display("invalid_date")
        self.assertEqual(result, "invalid_date")
    
    def test_get_dias_class_vencido(self):
        """Test de clase CSS para días vencidos"""
        result = self.manager._get_dias_class(0)
        self.assertEqual(result, 'dias-vencido')
        
        result = self.manager._get_dias_class(-5)
        self.assertEqual(result, 'dias-vencido')
    
    def test_get_dias_class_critico(self):
        """Test de clase CSS para días críticos"""
        result = self.manager._get_dias_class(5)
        self.assertEqual(result, 'dias-critico')
    
    def test_get_dias_class_alerta(self):
        """Test de clase CSS para días de alerta"""
        result = self.manager._get_dias_class(10)
        self.assertEqual(result, 'dias-alerta')
    
    def test_get_dias_class_normal(self):
        """Test de clase CSS para días normales"""
        result = self.manager._get_dias_class(20)
        self.assertEqual(result, 'dias-normal')
    
    def test_get_modern_html_header(self):
        """Test de generación de header HTML moderno"""
        header = self.manager._get_modern_html_header()
        
        self.assertIn("<!DOCTYPE html>", header)
        self.assertIn("INFORME DE AVISOS DE EXPEDIENTES", header)
        self.assertIn(self.manager.css_content, header)
        self.assertIn("Generado el", header)
    
    def test_get_modern_html_footer(self):
        """Test de generación de footer HTML moderno"""
        footer = self.manager._get_modern_html_footer()
        
        self.assertIn("</body>", footer)
        self.assertIn("</html>", footer)
        self.assertIn("informe automático", footer)
    
    def test_get_expedientes_tsol_sin_cod_s4h_success(self):
        """Test de obtención exitosa de expedientes TSOL sin código S4H"""
        mock_data = [
            {
                'IDExpediente': 1,
                'CodExp': 'EXP001',
                'Nemotecnico': 'TEST',
                'Titulo': 'Test Expediente',
                'Nombre': 'Usuario Test',
                'CadenaJuridicas': 'TSOL',
                'FECHAADJUDICACION': date(2024, 1, 1),
                'CodS4H': None
            }
        ]
        
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = mock_data
        mock_logger = Mock()
        self.manager.logger = mock_logger
        
        with patch.object(self.manager, '_get_expedientes_connection', return_value=mock_db_instance):
            result = self.manager.get_expedientes_tsol_sin_cod_s4h()
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['CodExp'], 'EXP001')
            self.assertEqual(result[0]['Nemotecnico'], 'TEST')
            self.assertEqual(result[0]['ResponsableCalidad'], 'Usuario Test')
            mock_db_instance.execute_query.assert_called_once()
            # Verifica que NO se loguea métrica aquí (métricas se hacen en generate_email_body)
            self.assertFalse(any(call_args.kwargs.get('extra', {}).get('metric_name') == 'expedientes_tsol_count'
                                 for call_args in mock_logger.info.call_args_list))
    
    def test_get_expedientes_tsol_sin_cod_s4h_error(self):
        """Test de manejo de error al obtener expedientes TSOL"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("DB error")
        mock_logger = Mock()
        self.manager.logger = mock_logger
        
        with patch.object(self.manager, '_get_expedientes_connection', return_value=mock_db_instance):
            result = self.manager.get_expedientes_tsol_sin_cod_s4h()
            self.assertEqual(result, [])
            # Verifica logging de error con contexto
            self.assertTrue(any(
                (args and 'Error obteniendo expedientes TSOL' in args[0]) and
                kwargs.get('extra', {}).get('context') == 'get_expedientes_tsol_sin_cod_s4h'
                for args, kwargs in ( (c.args, c.kwargs) for c in mock_logger.error.call_args_list )
            ))
    
    def test_get_expedientes_a_punto_finalizar_success(self):
        """Test de obtención exitosa de expedientes a punto de finalizar"""
        mock_data = [
            {
                'IDExpediente': 1,
                'CodExp': 'EXP001',
                'Nemotecnico': 'TEST',
                'Titulo': 'Test Expediente',
                'FechaInicioContrato': date(2024, 1, 1),
                'FechaFinContrato': date(2024, 12, 31),
                'Dias': 10,
                'FECHACERTIFICACION': date(2024, 1, 15),
                'GARANTIAMESES': 12,
                'FechaFinGarantia': date(2025, 12, 31),
                'Nombre': 'Usuario Test'
            }
        ]
        
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = mock_data
        
        mock_logger = Mock()
        self.manager.logger = mock_logger
        with patch.object(self.manager, '_get_expedientes_connection', return_value=mock_db_instance):
            result = self.manager.get_expedientes_a_punto_finalizar()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['CodExp'], 'EXP001')
            self.assertEqual(result[0]['DiasParaFin'], 10)
            self.assertEqual(result[0]['ResponsableCalidad'], 'Usuario Test')
            mock_db_instance.execute_query.assert_called_once()
            self.assertFalse(any(call_args.kwargs.get('extra', {}).get('metric_name') == 'expedientes_finalizar_count'
                                 for call_args in mock_logger.info.call_args_list))
    
    def test_get_expedientes_a_punto_finalizar_error(self):
        """Test de manejo de error al obtener expedientes a punto de finalizar"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("DB error")
        
        mock_logger = Mock()
        self.manager.logger = mock_logger
        with patch.object(self.manager, '_get_expedientes_connection', return_value=mock_db_instance):
            result = self.manager.get_expedientes_a_punto_finalizar()
            self.assertEqual(result, [])
            self.assertTrue(any(
                (args and 'Error obteniendo expedientes a punto de finalizar' in args[0]) and
                kwargs.get('extra', {}).get('context') == 'get_expedientes_a_punto_finalizar'
                for args, kwargs in ( (c.args, c.kwargs) for c in mock_logger.error.call_args_list )
            ))
    
    @patch('expedientes.expedientes_manager.Config')
    @patch('expedientes.expedientes_manager.ExpedientesManager._load_css_content')
    def test_load_css_content(self, mock_load_css, mock_config):
        """Test de carga de contenido CSS"""
        mock_load_css.return_value = "body { color: red; }"
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        manager = ExpedientesManager()
        
        self.assertEqual(manager.css_content, "body { color: red; }")
        mock_load_css.assert_called_once()

    def test_generate_email_body_metrics_logging(self):
        """Test de logging estructurado de métricas en generate_email_body"""
        # Prepara datos para que se generen varias tablas
        self.manager.get_expedientes_tsol_sin_cod_s4h = Mock(return_value=[{'IDExpediente':1,'CodExp':'E1','Nemotecnico':'N','Titulo':'T','Nombre':'User','CadenaJuridicas':'TSOL','FECHAADJUDICACION':date(2024,1,1),'CodS4H':None}])
        self.manager.get_expedientes_a_punto_finalizar = Mock(return_value=[{'IDExpediente':1,'CodExp':'E2','Nemotecnico':'N2','Titulo':'T2','FechaInicioContrato':date(2024,1,1),'FechaFinContrato':date(2024,12,31),'Dias':5,'FECHACERTIFICACION':date(2024,1,2),'GARANTIAMESES':12,'FechaFinGarantia':date(2025,12,31),'Nombre':'User2'}])
        self.manager.get_hitos_a_punto_finalizar = Mock(return_value=[])
        self.manager.get_expedientes_estado_desconocido = Mock(return_value=[])
        self.manager.get_expedientes_adjudicados_sin_contrato = Mock(return_value=[])
        self.manager.get_expedientes_fase_oferta_mucho_tiempo = Mock(return_value=[])
        mock_logger = Mock()
        self.manager.logger = mock_logger
        body = self.manager.generate_email_body()
        self.assertTrue(body)  # Debe generar cuerpo
        # Extrae metric logs
        metric_calls = [c for c in mock_logger.info.call_args_list if c.kwargs.get('extra', {}).get('metric_name')]
        metric_names = {c.kwargs['extra']['metric_name']: c.kwargs['extra']['metric_value'] for c in metric_calls}
        self.assertIn('expedientes_tsol_count', metric_names)
        self.assertIn('expedientes_finalizar_count', metric_names)
        # Verifica longitud HTML
        self.assertIn('expedientes_email_html_length_chars', metric_names)
        self.assertGreater(metric_names['expedientes_email_html_length_chars'], 0)


if __name__ == '__main__':
    unittest.main()