"""
Tests unitarios para NoConformidadesManager
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import os
import sys

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'src')
sys.path.insert(0, src_dir)

from no_conformidades.no_conformidades_manager import NoConformidadesManager


class TestNoConformidadesManager(unittest.TestCase):
    """Tests para NoConformidadesManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Mock de las dependencias externas
        with patch('no_conformidades.no_conformidades_manager.config') as mock_config, \
             patch('no_conformidades.no_conformidades_manager.AccessDatabase') as mock_db:
            
            # Configurar mocks
            mock_config.get_nc_css_content.return_value = "/* test css */"
            mock_config.get_db_no_conformidades_connection_string.return_value = "test_connection"
            
            self.manager = NoConformidadesManager()
            self.mock_db = mock_db
    
    def test_init(self):
        """Test de inicialización del manager"""
        self.assertEqual(self.manager.name, "NoConformidades")
        self.assertEqual(self.manager.script_filename, "run_no_conformidades.py")
        self.assertEqual(self.manager.task_names, ["NCTecnico", "NCCalidad"])
        self.assertEqual(self.manager.frequency_days, 1)
        self.assertIsNotNone(self.manager.css_content)
    
    def test_load_css_content_success(self):
        """Test de carga exitosa del contenido CSS"""
        with patch('no_conformidades.no_conformidades_manager.config') as mock_config:
            mock_config.get_nc_css_content.return_value = "body { color: red; }"
            manager = NoConformidadesManager()
            self.assertEqual(manager.css_content, "body { color: red; }")
    
    def test_load_css_content_error(self):
        """Test de manejo de error al cargar CSS"""
        with patch('no_conformidades.no_conformidades_manager.config') as mock_config:
            mock_config.get_nc_css_content.side_effect = Exception("CSS error")
            manager = NoConformidadesManager()
            self.assertEqual(manager.css_content, "/* CSS no disponible */")
    
    def test_get_nc_connection(self):
        """Test de obtención de conexión a base de datos NC"""
        with patch('no_conformidades.no_conformidades_manager.config') as mock_config, \
             patch('no_conformidades.no_conformidades_manager.AccessDatabase') as mock_db:
            
            mock_config.get_db_no_conformidades_connection_string.return_value = "test_connection"
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            
            manager = NoConformidadesManager()
            connection = manager._get_nc_connection()
            
            self.assertEqual(connection, mock_db_instance)
            mock_db.assert_called_with("test_connection")
    
    def test_ejecutar_consulta_success(self):
        """Test de ejecución exitosa de consulta"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = [{'id': 1, 'name': 'test'}]
        
        with patch.object(self.manager, '_get_nc_connection', return_value=mock_db_instance):
            result = self.manager.ejecutar_consulta("SELECT * FROM test")
            
            self.assertEqual(result, [{'id': 1, 'name': 'test'}])
            mock_db_instance.execute_query.assert_called_once_with("SELECT * FROM test", None)
    
    def test_ejecutar_consulta_error(self):
        """Test de manejo de error en consulta"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("DB error")
        
        with patch.object(self.manager, '_get_nc_connection', return_value=mock_db_instance):
            result = self.manager.ejecutar_consulta("SELECT * FROM test")
            
            self.assertEqual(result, [])
    
    def test_ejecutar_insercion_success(self):
        """Test de ejecución exitosa de inserción"""
        mock_db_instance = Mock()
        mock_db_instance.execute_non_query.return_value = 1
        
        with patch.object(self.manager, '_get_nc_connection', return_value=mock_db_instance):
            result = self.manager.ejecutar_insercion("INSERT INTO test VALUES (1)")
            
            self.assertTrue(result)
            mock_db_instance.execute_non_query.assert_called_once_with("INSERT INTO test VALUES (1)", None)
    
    def test_ejecutar_insercion_error(self):
        """Test de manejo de error en inserción"""
        mock_db_instance = Mock()
        mock_db_instance.execute_non_query.side_effect = Exception("DB error")
        
        with patch.object(self.manager, '_get_nc_connection', return_value=mock_db_instance):
            result = self.manager.ejecutar_insercion("INSERT INTO test VALUES (1)")
            
            self.assertFalse(result)
    
    def test_format_date_for_access_string_date(self):
        """Test de formateo de fecha string para Access"""
        result = self.manager._format_date_for_access("2024-01-15")
        self.assertEqual(result, "#01/15/2024#")
    
    def test_format_date_for_access_datetime(self):
        """Test de formateo de datetime para Access"""
        test_date = datetime(2024, 1, 15)
        result = self.manager._format_date_for_access(test_date)
        self.assertEqual(result, "#01/15/2024#")
    
    def test_format_date_for_access_date(self):
        """Test de formateo de date para Access"""
        test_date = date(2024, 1, 15)
        result = self.manager._format_date_for_access(test_date)
        self.assertEqual(result, "#01/15/2024#")
    
    def test_format_date_for_access_invalid(self):
        """Test de formateo de fecha inválida para Access"""
        result = self.manager._format_date_for_access("invalid_date")
        self.assertEqual(result, "#01/01/1900#")
    
    def test_get_ars_proximas_vencer_calidad_success(self):
        """Test de obtención exitosa de ARs próximas a vencer"""
        mock_data = [
            {
                'DiasParaCierre': 5,
                'CodigoNoConformidad': 'NC001',
                'Nemotecnico': 'TEST',
                'DESCRIPCION': 'Test description',
                'RESPONSABLECALIDAD': 'user1',
                'FECHAAPERTURA': date(2024, 1, 1),
                'FPREVCIERRE': date(2024, 1, 15)
            }
        ]
        
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = mock_data
        
        with patch.object(self.manager, '_get_nc_connection', return_value=mock_db_instance):
            result = self.manager.get_ars_proximas_vencer_calidad()
            
            self.assertEqual(result, mock_data)
            mock_db_instance.execute_query.assert_called_once()
    
    def test_get_ars_proximas_vencer_calidad_error(self):
        """Test de manejo de error al obtener ARs próximas a vencer"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("DB error")
        
        with patch.object(self.manager, '_get_nc_connection', return_value=mock_db_instance):
            result = self.manager.get_ars_proximas_vencer_calidad()
            
            self.assertEqual(result, [])
    
    def test_get_modern_html_header(self):
        """Test de generación de header HTML moderno"""
        header = self.manager._get_modern_html_header()
        
        self.assertIn("<!DOCTYPE html>", header)
        self.assertIn("Informe de No Conformidades", header)
        self.assertIn(self.manager.css_content, header)
    
    def test_get_modern_html_footer(self):
        """Test de generación de footer HTML moderno"""
        footer = self.manager._get_modern_html_footer()
        
        self.assertIn("</body>", footer)
        self.assertIn("</html>", footer)
        self.assertIn("mensaje generado por el servicio automatizado", footer)
    
    def test_generate_modern_arapc_table_html_empty(self):
        """Test de generación de tabla ARAPC vacía"""
        result = self.manager._generate_modern_arapc_table_html([])
        self.assertEqual(result, "")
    
    def test_generate_modern_arapc_table_html_with_data(self):
        """Test de generación de tabla ARAPC con datos"""
        test_data = [
            {
                'DiasParaCierre': 5,
                'CodigoNoConformidad': 'NC001',
                'Nemotecnico': 'TEST',
                'DESCRIPCION': 'Test description',
                'RESPONSABLECALIDAD': 'user1',
                'FECHAAPERTURA': date(2024, 1, 1),
                'FPREVCIERRE': date(2024, 1, 15)
            }
        ]
        
        with patch.object(self.manager, '_get_dias_class', return_value='dias-critico'), \
             patch.object(self.manager, '_format_date_display', return_value='01/01/2024'):
            
            result = self.manager._generate_modern_arapc_table_html(test_data)
            
            self.assertIn("Acciones Correctivas/Preventivas Próximas a Caducar", result)
            self.assertIn("NC001", result)
            self.assertIn("TEST", result)
            self.assertIn("Test description", result)
    
    def test_close_connections(self):
        """Test de cierre de conexiones"""
        mock_db_nc = Mock()
        self.manager.db_nc = mock_db_nc
        
        with patch('no_conformidades.no_conformidades_manager.TareaDiaria.close_connections') as mock_super:
            self.manager.close_connections()
            
            mock_super.assert_called_once()
            mock_db_nc.disconnect.assert_called_once()
            self.assertIsNone(self.manager.db_nc)
    
    def test_close_connections_error(self):
        """Test de manejo de error al cerrar conexiones"""
        mock_db_nc = Mock()
        mock_db_nc.disconnect.side_effect = Exception("Close error")
        self.manager.db_nc = mock_db_nc
        
        with patch('no_conformidades.no_conformidades_manager.TareaDiaria.close_connections'):
            # No debe lanzar excepción
            self.manager.close_connections()
            self.assertIsNone(self.manager.db_nc)


if __name__ == '__main__':
    unittest.main()