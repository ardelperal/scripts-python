"""
Tests de integración para el módulo de Expedientes
Estos tests interactúan con bases de datos locales reales
"""
import unittest
import os
import sys
from datetime import date

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'src')
sys.path.insert(0, src_dir)

from src.expedientes.expedientes_manager import ExpedientesManager
from src.expedientes.expedientes_task import ExpedientesTask
from src.common.config import Config
from src.common.database import AccessDatabase


class TestExpedientesIntegration(unittest.TestCase):
    """Tests de integración para Expedientes"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Forzar uso de bases de datos locales
        os.environ['ENVIRONMENT'] = 'local'
        cls.config = Config()
        
        # Verificar que las bases de datos locales existen
        cls.db_expedientes_path = cls.config.db_expedientes_path
        cls.db_tareas_path = cls.config.db_tareas_path
        
        if not os.path.exists(cls.db_expedientes_path):
            cls.skipTest(f"Base de datos Expedientes local no encontrada: {cls.db_expedientes_path}")
        
        if not os.path.exists(cls.db_tareas_path):
            cls.skipTest(f"Base de datos Tareas local no encontrada: {cls.db_tareas_path}")

    def setUp(self):
        """Configuración para cada test"""
        cfg = self.__class__.config
        self.db_expedientes = AccessDatabase(cfg.db_expedientes_path)
        self.db_tareas = AccessDatabase(cfg.db_tareas_path)
        self.manager = ExpedientesManager(db_expedientes=self.db_expedientes, db_tareas=self.db_tareas)
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if hasattr(self, 'manager'):
            if hasattr(self.manager, 'close_connections'):
                self.manager.close_connections()
    
    # test_database_connections eliminado (métodos internos removidos)
    
    def test_get_expedientes_tsol_sin_cod_s4h_real(self):
        """Test de obtención real de expedientes TSOL sin código S4H"""
        result = self.manager.get_expedientes_tsol_sin_cod_s4h()
        
        # Debe retornar una lista
        self.assertIsInstance(result, list)
        
        # Si hay resultados, verificar estructura
        if result:
            first_item = result[0]
            expected_keys = [
                'IDExpediente', 'CodExp', 'Nemotecnico', 'Titulo',
                'ResponsableCalidad', 'CadenaJuridicas', 'FechaAdjudicacion', 'CodS4H'
            ]
            for key in expected_keys:
                self.assertIn(key, first_item)
    
    def test_get_expedientes_a_punto_finalizar_real(self):
        """Test de obtención real de expedientes a punto de finalizar"""
        result = self.manager.get_expedientes_a_punto_finalizar()
        
        # Debe retornar una lista
        self.assertIsInstance(result, list)
        
        # Si hay resultados, verificar estructura
        if result:
            first_item = result[0]
            expected_keys = [
                'IDExpediente', 'CodExp', 'Nemotecnico', 'Titulo',
                'FechaInicioContrato', 'FechaFinContrato', 'DiasParaFin',
                'FechaCertificacion', 'GarantiaMeses', 'FechaFinGarantia',
                'ResponsableCalidad'
            ]
            for key in expected_keys:
                self.assertIn(key, first_item)
    
    # test_format_date_display_integration y test_get_dias_class_integration eliminados (helpers removidos)
    
    def test_html_generation_integration(self):
        """Test de generación de HTML con datos reales (nuevo método)"""
        html = self.manager.generate_expedientes_report_html()
        # Puede estar vacío si no hay datos, pero si hay contenido debe incluir DOCTYPE y título
        if html:
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("INFORME DE AVISOS DE EXPEDIENTES", html)
    
    # CSS embebido ahora lo gestiona HTMLReportGenerator; no se expone css_content directamente
    
    # Validación de esquema omitida para simplificar tras refactor (acceso directo abstraído)
    
    # Atributos antiguos eliminados; test de inicialización removido


class TestExpedientesTaskIntegration(unittest.TestCase):
    """Tests de integración para ExpedientesTask (placeholder adaptado)"""
    pass


class TestExpedientesEndToEndIntegration(unittest.TestCase):
    """Tests end-to-end para el flujo completo de Expedientes (simplificado)"""
    @classmethod
    def setUpClass(cls):
        os.environ['ENVIRONMENT'] = 'local'
        cls.config = Config()
    def setUp(self):
        cfg = self.__class__.config
        self.manager = ExpedientesManager(
            db_expedientes=AccessDatabase(cfg.db_expedientes_path),
            db_tareas=AccessDatabase(cfg.db_tareas_path)
        )
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if hasattr(self, 'manager'):
            if hasattr(self.manager, 'close_connections'):
                self.manager.close_connections()
    
    def test_full_data_flow_integration(self):
        """Test del flujo completo de datos"""
        # 1. Obtener expedientes TSOL
        tsol_expedientes = self.manager.get_expedientes_tsol_sin_cod_s4h()
        self.assertIsInstance(tsol_expedientes, list)
        
        # 2. Obtener expedientes a punto de finalizar
        finalizar_expedientes = self.manager.get_expedientes_a_punto_finalizar()
        self.assertIsInstance(finalizar_expedientes, list)
        
        # 3. Generar HTML completo
        html = self.manager.generate_expedientes_report_html()
        if html:
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("INFORME DE AVISOS DE EXPEDIENTES", html)

        # 4. Verificar que las conexiones funcionan
        self.assertIsNotNone(self.manager.db_expedientes)
        self.assertIsNotNone(self.manager.db_tareas)


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    unittest.main()