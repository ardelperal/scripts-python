"""
Tests de integración para el módulo de Expedientes
Estos tests interactúan con bases de datos locales reales
"""
import unittest
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

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
        self.manager = ExpedientesManager()
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if hasattr(self, 'manager'):
            if hasattr(self.manager, 'close_connections'):
                self.manager.close_connections()
    
    def test_database_connections(self):
        """Test de conexiones a bases de datos"""
        # Test conexión Expedientes
        db_expedientes = self.manager._get_expedientes_connection()
        self.assertIsNotNone(db_expedientes)
        
        # Test conexión Tareas
        db_tareas = self.manager._get_tareas_connection()
        self.assertIsNotNone(db_tareas)
    
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
    
    def test_format_date_display_integration(self):
        """Test de formateo de fechas con datos reales"""
        test_date = date(2024, 1, 15)
        formatted = self.manager._format_date_display(test_date)
        
        self.assertEqual(formatted, "15/01/2024")
        
        # Test con datetime
        test_datetime = datetime(2024, 1, 15, 10, 30)
        formatted = self.manager._format_date_display(test_datetime)
        
        self.assertEqual(formatted, "15/01/2024")
        
        # Test con None
        formatted = self.manager._format_date_display(None)
        self.assertEqual(formatted, "&nbsp;")
    
    def test_get_dias_class_integration(self):
        """Test de clasificación de días con valores reales"""
        # Test días vencidos
        self.assertEqual(self.manager._get_dias_class(-5), 'dias-vencido')
        self.assertEqual(self.manager._get_dias_class(0), 'dias-vencido')
        
        # Test días críticos
        self.assertEqual(self.manager._get_dias_class(5), 'dias-critico')
        
        # Test días de alerta
        self.assertEqual(self.manager._get_dias_class(10), 'dias-alerta')
        
        # Test días normales
        self.assertEqual(self.manager._get_dias_class(20), 'dias-normal')
    
    def test_html_generation_integration(self):
        """Test de generación de HTML con datos reales"""
        # Generar HTML
        html_header = self.manager._get_modern_html_header()
        html_footer = self.manager._get_modern_html_footer()
        
        # Verificar estructura HTML
        self.assertIn("<!DOCTYPE html>", html_header)
        self.assertIn("INFORME DE AVISOS DE EXPEDIENTES", html_header)
        self.assertIn("</html>", html_footer)
        
        # Verificar que contiene CSS
        self.assertIn(self.manager.css_content, html_header)
        
        # Verificar fecha actual en header
        current_date = datetime.now().strftime('%d/%m/%Y')
        self.assertIn(current_date, html_header)
    
    def test_css_loading_integration(self):
        """Test de carga de CSS real"""
        css_content = self.manager.css_content
        
        # Debe tener contenido CSS
        self.assertIsInstance(css_content, str)
        self.assertGreater(len(css_content), 0)
    
    def test_database_schema_validation(self):
        """Test de validación del esquema de base de datos"""
        # Verificar que las tablas principales existen
        tables_to_check = [
            "TbExpedientes",
            "TbExpedientesConEntidades",
            "TbUsuariosAplicaciones"
        ]
        
        db_expedientes = self.manager._get_expedientes_connection()
        
        for table in tables_to_check:
            query = f"SELECT TOP 1 * FROM {table}"
            try:
                result = db_expedientes.execute_query(query)
                # Si no hay error, la tabla existe
                self.assertIsInstance(result, list)
            except Exception as e:
                self.fail(f"Tabla {table} no existe o no es accesible: {e}")
    
    def test_manager_initialization_integration(self):
        """Test de inicialización del manager con configuración real"""
        self.assertEqual(self.manager.name, "EXPEDIENTES")
        self.assertEqual(self.manager.script_filename, "run_expedientes.py")
        self.assertEqual(self.manager.task_names, ["ExpedientesDiario"])
        self.assertEqual(self.manager.frequency_days, 1)
        
        # Verificar que el config se cargó correctamente
        self.assertIsNotNone(self.manager.config)
        self.assertIsNotNone(self.manager.css_content)


class TestExpedientesTaskIntegration(unittest.TestCase):
    """Tests de integración para ExpedientesTask"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Forzar uso de bases de datos locales
        os.environ['ENVIRONMENT'] = 'local'
    
    def setUp(self):
        """Configuración para cada test"""
        self.task = ExpedientesTask()
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if hasattr(self, 'task'):
            self.task.close_connections()
    
    def test_task_initialization_integration(self):
        """Test de inicialización de tarea con dependencias reales"""
        self.assertIsNotNone(self.task.manager)
        self.assertEqual(self.task.name, "EXPEDIENTES")
    
    def test_get_task_emails_integration(self):
        """Test de obtención de emails con configuración real"""
        # Test emails de expedientes diario
        emails_expedientes = self.task.get_task_emails()
        self.assertIsInstance(emails_expedientes, list)
        
        # Verificar que es una lista válida (puede estar vacía)
        for email in emails_expedientes:
            self.assertIsInstance(email, str)
            if email:  # Si no está vacío, debe contener @
                self.assertIn('@', email)
    
    def test_cleanup_integration(self):
        """Test de limpieza con recursos reales"""
        # Inicializar manager
        manager = self.task.manager
        
        # Establecer conexiones
        db_expedientes = manager._get_expedientes_connection()
        self.assertIsNotNone(db_expedientes)
        
        # Ejecutar cleanup
        self.task.close_connections()
        
        # Verificar que no hay errores (el cleanup debe ser silencioso)
        # No podemos verificar el estado interno porque depende de la implementación


class TestExpedientesEndToEndIntegration(unittest.TestCase):
    """Tests end-to-end para el flujo completo de Expedientes"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Forzar uso de bases de datos locales
        os.environ['ENVIRONMENT'] = 'local'
    
    def setUp(self):
        """Configuración para cada test"""
        self.manager = ExpedientesManager()
    
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
        html_header = self.manager._get_modern_html_header()
        html_footer = self.manager._get_modern_html_footer()
        
        # Verificar que el HTML es válido
        self.assertIn("<!DOCTYPE html>", html_header)
        self.assertIn("</html>", html_footer)
        
        # 4. Verificar que las conexiones funcionan
        db_expedientes = self.manager._get_expedientes_connection()
        db_tareas = self.manager._get_tareas_connection()
        
        self.assertIsNotNone(db_expedientes)
        self.assertIsNotNone(db_tareas)


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    unittest.main()