"""
Tests de integración para el módulo de No Conformidades
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

from no_conformidades.no_conformidades_manager import NoConformidadesManager
from no_conformidades.no_conformidades_task import NoConformidadesTask
from common.config import Config
from common.database import AccessDatabase


class TestNoConformidadesIntegration(unittest.TestCase):
    """Tests de integración para No Conformidades"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Forzar uso de bases de datos locales
        os.environ['ENVIRONMENT'] = 'local'
        cls.config = Config()
        
        # Verificar que las bases de datos locales existen
        cls.db_nc_path = cls.config.get_db_no_conformidades_path()
        cls.db_tareas_path = cls.config.get_db_tareas_path()
        
        if not os.path.exists(cls.db_nc_path):
            cls.skipTest(f"Base de datos NC local no encontrada: {cls.db_nc_path}")
        
        if not os.path.exists(cls.db_tareas_path):
            cls.skipTest(f"Base de datos Tareas local no encontrada: {cls.db_tareas_path}")
    
    def setUp(self):
        """Configuración para cada test"""
        self.manager = NoConformidadesManager()
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if hasattr(self, 'manager'):
            self.manager.close_connections()
    
    def test_database_connections(self):
        """Test de conexiones a bases de datos"""
        # Test conexión NC
        db_nc = self.manager._get_nc_connection()
        self.assertIsNotNone(db_nc)
        
        # Test conexión Tareas
        db_tareas = self.manager._get_tareas_connection()
        self.assertIsNotNone(db_tareas)
    
    def test_ejecutar_consulta_real(self):
        """Test de ejecución de consulta real en base de datos NC"""
        # Consulta simple para verificar conectividad
        query = "SELECT TOP 1 IDNoConformidad FROM TbNoConformidades"
        result = self.manager.ejecutar_consulta(query)
        
        # Debe retornar una lista (puede estar vacía)
        self.assertIsInstance(result, list)
    
    def test_get_ars_proximas_vencer_calidad_real(self):
        """Test de obtención real de ARs próximas a vencer"""
        result = self.manager.get_ars_proximas_vencer_calidad()
        
        # Debe retornar una lista
        self.assertIsInstance(result, list)
        
        # Si hay resultados, verificar estructura
        if result:
            first_item = result[0]
            expected_keys = [
                'DiasParaCierre', 'CodigoNoConformidad', 'Nemotecnico',
                'DESCRIPCION', 'RESPONSABLECALIDAD', 'FECHAAPERTURA', 'FPREVCIERRE'
            ]
            for key in expected_keys:
                self.assertIn(key, first_item)
    
    def test_format_date_for_access_integration(self):
        """Test de formateo de fechas para Access con datos reales"""
        test_date = date(2024, 1, 15)
        formatted = self.manager._format_date_for_access(test_date)
        
        self.assertEqual(formatted, "#01/15/2024#")
        
        # Test con datetime
        test_datetime = datetime(2024, 1, 15, 10, 30)
        formatted = self.manager._format_date_for_access(test_datetime)
        
        self.assertEqual(formatted, "#01/15/2024#")
    
    def test_html_generation_integration(self):
        """Test de generación de HTML con datos reales"""
        # Obtener datos reales
        ars_data = self.manager.get_ars_proximas_vencer_calidad()
        
        # Generar HTML
        html_header = self.manager._get_modern_html_header()
        html_footer = self.manager._get_modern_html_footer()
        
        # Verificar estructura HTML
        self.assertIn("<!DOCTYPE html>", html_header)
        self.assertIn("</html>", html_footer)
        
        # Si hay datos, generar tabla
        if ars_data:
            table_html = self.manager._generate_modern_arapc_table_html(ars_data)
            self.assertIn("<table", table_html)
            self.assertIn("</table>", table_html)
    
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
            "TbNoConformidades",
            "TbNCAccionCorrectivas", 
            "TbNCAccionesRealizadas",
            "TbNCARAvisos"
        ]
        
        for table in tables_to_check:
            query = f"SELECT TOP 1 * FROM {table}"
            try:
                result = self.manager.ejecutar_consulta(query)
                # Si no hay error, la tabla existe
                self.assertIsInstance(result, list)
            except Exception as e:
                self.fail(f"Tabla {table} no existe o no es accesible: {e}")
    
    def test_close_connections_integration(self):
        """Test de cierre de conexiones reales"""
        # Establecer conexiones
        db_nc = self.manager._get_nc_connection()
        db_tareas = self.manager._get_tareas_connection()
        
        self.assertIsNotNone(db_nc)
        self.assertIsNotNone(db_tareas)
        
        # Cerrar conexiones
        self.manager.close_connections()
        
        # Verificar que las conexiones se han limpiado
        self.assertIsNone(self.manager.db_nc)


class TestNoConformidadesTaskIntegration(unittest.TestCase):
    """Tests de integración para NoConformidadesTask"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Forzar uso de bases de datos locales
        os.environ['ENVIRONMENT'] = 'local'
    
    def setUp(self):
        """Configuración para cada test"""
        self.task = NoConformidadesTask()
    
    def tearDown(self):
        """Limpieza después de cada test"""
        if hasattr(self, 'task'):
            self.task.cleanup()
    
    def test_task_initialization_integration(self):
        """Test de inicialización de tarea con dependencias reales"""
        self.assertIsNotNone(self.task.manager)
        self.assertEqual(self.task.nombre_tarea, "NoConformidades")
    
    def test_get_task_emails_integration(self):
        """Test de obtención de emails con configuración real"""
        # Test emails de calidad
        emails_calidad = self.task.get_task_emails("NCCalidad")
        self.assertIsInstance(emails_calidad, str)
        
        # Test emails de técnicos
        emails_tecnicos = self.task.get_task_emails("NCTecnico")
        self.assertIsInstance(emails_tecnicos, str)
        
        # Test tarea desconocida
        emails_unknown = self.task.get_task_emails("UnknownTask")
        self.assertEqual(emails_unknown, "")
    
    def test_cleanup_integration(self):
        """Test de limpieza con recursos reales"""
        # Inicializar manager
        manager = self.task.manager
        
        # Establecer conexiones
        db_nc = manager._get_nc_connection()
        self.assertIsNotNone(db_nc)
        
        # Ejecutar cleanup
        self.task.cleanup()
        
        # Verificar limpieza
        self.assertIsNone(manager.db_nc)


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    unittest.main()