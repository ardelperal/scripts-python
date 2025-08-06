"""
Tests unitarios para el módulo html_report_generator de No Conformidades
"""

import unittest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.no_conformidades.no_conformidades_manager import NoConformidadesManager


class TestHTMLReportGenerator(unittest.TestCase):
    """Tests para las funciones de generación de HTML en NoConformidadesManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Mock de la configuración
        self.mock_config = Mock()
        self.mock_config.get_database_config.return_value = {
            'host': 'localhost',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
        
        # Crear instancia del manager con configuración mockeada
        with patch('src.no_conformidades.no_conformidades_manager.Config') as mock_config_class:
            mock_config_class.return_value = self.mock_config
            self.manager = NoConformidadesManager()
    
    def test_generate_quality_report_html_con_datos(self):
        """Test generar reporte HTML de calidad con datos"""
        # Datos simulados
        nc_pendientes = [{'codigo': 'NC001', 'descripcion': 'Test NC'}]
        nc_sin_acciones = [{'codigo': 'NC002', 'descripcion': 'Test NC 2'}]
        ar_vencidas = [{'codigo': 'AR001', 'descripcion': 'Test AR'}]
        ar_proximas = [{'codigo': 'AR002', 'descripcion': 'Test AR 2'}]
        
        # Mock del método get_ars_para_replanificar
        with patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            html = self.manager.generate_quality_report_html(
                nc_pendientes_eficacia=nc_pendientes,
                nc_sin_acciones=nc_sin_acciones,
                ar_vencidas_calidad=ar_vencidas,
                ar_proximas_vencer_calidad=ar_proximas
            )
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Informe de No Conformidades', html)
        self.assertIn('</html>', html)
    
    def test_generate_quality_report_html_sin_datos(self):
        """Test generar reporte HTML de calidad sin datos"""
        with patch.object(self.manager, 'get_ars_para_replanificar', return_value=[]):
            html = self.manager.generate_quality_report_html(
                nc_pendientes_eficacia=[],
                nc_sin_acciones=[],
                ar_vencidas_calidad=[],
                ar_proximas_vencer_calidad=[]
            )
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Informe de No Conformidades', html)
        self.assertIn('</html>', html)
    
    def test_generate_technician_report_html_con_datos(self):
        """Test generar reporte HTML de técnico con datos"""
        ar_15_dias = [{'codigo': 'AR001', 'descripcion': 'Test AR 15'}]
        ar_7_dias = [{'codigo': 'AR002', 'descripcion': 'Test AR 7'}]
        ar_vencidas = [{'codigo': 'AR003', 'descripcion': 'Test AR vencida'}]
        
        html = self.manager.generate_technician_report_html(
            ar_15_dias=ar_15_dias,
            ar_7_dias=ar_7_dias,
            ar_vencidas=ar_vencidas
        )
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Informe de No Conformidades', html)
        self.assertIn('</html>', html)
    
    def test_generate_technician_report_html_sin_datos(self):
        """Test generar reporte HTML de técnico sin datos"""
        html = self.manager.generate_technician_report_html(
            ar_15_dias=[],
            ar_7_dias=[],
            ar_vencidas=[]
        )
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Informe de No Conformidades', html)
        self.assertIn('</html>', html)
    
    def test_generar_informe_tecnico_individual_html(self):
        """Test generar informe técnico individual HTML"""
        araps_8_15 = [{'codigo': 'AR001', 'descripcion': 'Test AR 8-15'}]
        araps_1_7 = [{'codigo': 'AR002', 'descripcion': 'Test AR 1-7'}]
        araps_vencidas = [{'codigo': 'AR003', 'descripcion': 'Test AR vencida'}]
        
        html = self.manager.generar_informe_tecnico_individual_html(
            araps_8_15=araps_8_15,
            araps_1_7=araps_1_7,
            araps_vencidas=araps_vencidas
        )
        
        self.assertIn('<html>', html)
        self.assertIn('Informe de Acciones Correctivas Pendientes', html)
        self.assertIn('</html>', html)
    
    def test_generate_nc_table_html(self):
        """Test generar tabla HTML de No Conformidades"""
        nc_list = [
            {
                'Nemotecnico': 'TEST001',
                'CodigoNoConformidad': 'NC001',
                'DESCRIPCION': 'Test NC',
                'RESPONSABLECALIDAD': 'calidad@test.com',
                'FECHAAPERTURA': '2023-01-01',
                'FPREVCIERRE': '2023-12-31',
                'DiasParaCierre': 10
            }
        ]
        
        html = self.manager._generate_nc_table_html(nc_list)
        
        self.assertIn('<table>', html)
        self.assertIn('TEST001', html)
        self.assertIn('NC001', html)
        self.assertIn('Test NC', html)
        self.assertIn('</table>', html)
    
    def test_generate_arapc_table_html(self):
        """Test generar tabla HTML de ARAPs"""
        arapc_list = [
            {
                'Nemotecnico': 'TEST001',
                'CodigoNoConformidad': 'NC001',
                'Accion': 'Acción test',
                'Tarea': 'Tarea test',
                'RESPONSABLETELEFONICA': 'tecnico@test.com',
                'RESPONSABLECALIDAD': 'calidad@test.com',
                'FechaFinPrevista': '2023-12-31',
                'DiasParaCaducar': 5
            }
        ]
        
        html = self.manager._generate_arapc_table_html(arapc_list)
        
        self.assertIn('<table>', html)
        self.assertIn('TEST001', html)
        self.assertIn('NC001', html)
        self.assertIn('Acción test', html)
        self.assertIn('</table>', html)


if __name__ == '__main__':
    unittest.main()