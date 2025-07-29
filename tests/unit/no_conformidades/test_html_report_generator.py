"""
Tests para el generador de reportes HTML del módulo de No Conformidades
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.no_conformidades.no_conformidades_manager import NoConformidad
from src.common.html_report_generator import HTMLReportGenerator


class TestHTMLReportGenerator(unittest.TestCase):
    """Tests para la clase HTMLReportGenerator"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.generator = HTMLReportGenerator()
    
    def test_generar_header_html(self):
        """Test generar header HTML"""
        titulo = "Reporte de Prueba"
        
        # Ejecutar
        html = self.generator.generar_header_html(titulo)
        
        # Verificar
        self.assertIn(titulo, html)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html>", html)
        self.assertIn("<head>", html)
        self.assertIn("<body>", html)
        self.assertIn("Generado el:", html)
    
    def test_generar_footer_html(self):
        """Test generar footer HTML"""
        # Ejecutar
        html = self.generator.generar_footer_html()
        
        # Verificar
        self.assertIn("</body>", html)
        self.assertIn("</html>", html)
        self.assertIn("Sistema de Gestión", html)
    
    def test_generar_tabla_nc_eficacia_vacia(self):
        """Test generar tabla de NCs de eficacia vacía"""
        # Ejecutar
        html = self.generator.generar_tabla_nc_eficacia([])
        
        # Verificar
        self.assertIn("No hay No Conformidades", html)
        self.assertIn("info", html)
    
    def test_generar_tabla_nc_eficacia_con_datos(self):
        """Test generar tabla de NCs de eficacia con datos"""
        # Crear datos de prueba
        ncs = [
            NoConformidad(
                codigo="NC-001",
                nemotecnico="TEST1",
                descripcion="Descripción 1",
                responsable_calidad="Juan Pérez",
                fecha_apertura=datetime(2024, 1, 1),
                fecha_prev_cierre=datetime(2024, 2, 1)
            ),
            NoConformidad(
                codigo="NC-002",
                nemotecnico="TEST2",
                descripcion="Descripción 2",
                responsable_calidad="María García",
                fecha_apertura=datetime(2024, 1, 5),
                fecha_prev_cierre=datetime(2024, 2, 5)
            )
        ]
        
        # Ejecutar
        html = self.generator.generar_tabla_nc_eficacia(ncs)
        
        # Verificar
        self.assertIn("NC-001", html)
        self.assertIn("NC-002", html)
        self.assertIn("TEST1", html)
        self.assertIn("TEST2", html)
        self.assertIn("Juan Pérez", html)
        self.assertIn("María García", html)
        self.assertIn("<table", html)
        self.assertIn("</table>", html)
    
    def test_generar_resumen_estadisticas(self):
        """Test generar resumen de estadísticas"""
        # Crear datos de prueba
        ncs_eficacia = [Mock(), Mock()]  # 2 NCs
        arapcs = [Mock(), Mock(), Mock()]  # 3 ARAPs
        ncs_caducar = [Mock()]  # 1 NC
        ncs_sin_acciones = []  # 0 NCs
        
        # Configurar ARAPs para simular vencidas
        arapcs[0].fecha_fin_prevista = datetime.now() - timedelta(days=5)  # Vencida
        arapcs[1].fecha_fin_prevista = datetime.now() + timedelta(days=5)  # No vencida
        arapcs[2].fecha_fin_prevista = datetime.now() - timedelta(days=2)  # Vencida
        
        # Configurar NCs para simular caducadas
        ncs_caducar[0].dias_para_cierre = -3  # Caducada
        
        # Ejecutar
        html = self.generator.generar_resumen_estadisticas(
            ncs_eficacia, arapcs, ncs_caducar, ncs_sin_acciones
        )
        
        # Verificar
        self.assertIn("2", html)  # Total NCs eficacia
        self.assertIn("3", html)  # Total ARAPs
        self.assertIn("1", html)  # Total NCs caducar
        self.assertIn("0", html)  # Total NCs sin acciones
        self.assertIn("🔴 Crítico", html)  # Estado crítico por ARAPs vencidas
        self.assertIn("✅ OK", html)  # Estado OK para NCs sin acciones


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.CRITICAL)  # Solo errores críticos durante tests
    
    # Ejecutar tests
    unittest.main(verbosity=2)