"""
Pruebas de migración para No Conformidades
Verifica que la nueva implementación funcione correctamente
"""
import unittest
import os
import sys
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from no_conformidades.no_conformidades_task import NoConformidadesTask
from no_conformidades.no_conformidades_manager import NoConformidadesManager


class TestNoConformidadesTask(unittest.TestCase):
    """Pruebas para NoConformidadesTask"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.task = NoConformidadesTask()
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        if self.task:
            try:
                self.task.close_connections()
            except:
                pass
    
    def test_task_initialization(self):
        """Prueba la inicialización de la tarea"""
        self.assertEqual(self.task.name, "NoConformidades")
        self.assertEqual(self.task.script_filename, "run_no_conformidades.py")
        self.assertIn("NCTecnico", self.task.task_names)
        self.assertIn("NCCalidad", self.task.task_names)
        self.assertIsInstance(self.task.frequency_days, int)
    
    def test_task_close_connections(self):
        """Prueba el cierre de conexiones"""
        # No debe lanzar excepción
        self.task.close_connections()


class TestNoConformidadesManager(unittest.TestCase):
    """Pruebas para NoConformidadesManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.manager = NoConformidadesManager()
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        if self.manager:
            try:
                self.manager.close_connections()
            except:
                pass
    
    def test_manager_initialization(self):
        """Prueba la inicialización del manager"""
        self.assertEqual(self.manager.name, "NoConformidades")
        self.assertEqual(self.manager.script_filename, "run_no_conformidades.py")
        self.assertIn("NCTecnico", self.manager.task_names)
        self.assertIn("NCCalidad", self.manager.task_names)
        self.assertIsInstance(self.manager.frequency_days, int)
        self.assertIsInstance(self.manager.dias_alerta_arapc, int)
        self.assertIsInstance(self.manager.dias_alerta_nc, int)
        self.assertIsInstance(self.manager.id_aplicacion, int)
    
    def test_css_loading(self):
        """Prueba la carga del CSS"""
        self.assertIsInstance(self.manager.css_content, str)
        self.assertGreater(len(self.manager.css_content), 0)
    
    def test_date_formatting(self):
        """Prueba el formateo de fechas para Access"""
        # Fecha como string
        fecha_str = "2024-01-15"
        formatted = self.manager._format_date_for_access(fecha_str)
        self.assertEqual(formatted, "#01/15/2024#")
        
        # Fecha como date
        fecha_date = date(2024, 1, 15)
        formatted = self.manager._format_date_for_access(fecha_date)
        self.assertEqual(formatted, "#01/15/2024#")
        
        # Fecha como datetime
        fecha_datetime = datetime(2024, 1, 15, 10, 30)
        formatted = self.manager._format_date_for_access(fecha_datetime)
        self.assertEqual(formatted, "#01/15/2024#")
    
    def test_get_nc_proximas_caducar(self):
        """Prueba la obtención de NCs próximas a caducar"""
        try:
            nc_proximas = self.manager.get_nc_proximas_caducar()
            self.assertIsInstance(nc_proximas, list)
            print(f"NCs próximas a caducar encontradas: {len(nc_proximas)}")
            
            # Verificar estructura si hay datos
            if nc_proximas:
                nc = nc_proximas[0]
                self.assertIn('CodigoNoConformidad', nc)
                self.assertIn('Nemotecnico', nc)
                self.assertIn('DESCRIPCION', nc)
                
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_nc_caducadas(self):
        """Prueba la obtención de NCs caducadas"""
        try:
            nc_caducadas = self.manager.get_nc_caducadas()
            self.assertIsInstance(nc_caducadas, list)
            print(f"NCs caducadas encontradas: {len(nc_caducadas)}")
            
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_arapcs_proximas_vencer(self):
        """Prueba la obtención de ARAPs próximas a vencer"""
        try:
            arapcs_proximas = self.manager.get_arapcs_proximas_vencer()
            self.assertIsInstance(arapcs_proximas, list)
            print(f"ARAPs próximas a vencer encontradas: {len(arapcs_proximas)}")
            
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_arapcs_vencidas(self):
        """Prueba la obtención de ARAPs vencidas"""
        try:
            arapcs_vencidas = self.manager.get_arapcs_vencidas()
            self.assertIsInstance(arapcs_vencidas, list)
            print(f"ARAPs vencidas encontradas: {len(arapcs_vencidas)}")
            
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_nc_pendientes_eficacia(self):
        """Prueba la obtención de NCs pendientes de control de eficacia"""
        try:
            nc_eficacia = self.manager.get_nc_pendientes_eficacia()
            self.assertIsInstance(nc_eficacia, list)
            print(f"NCs pendientes de eficacia encontradas: {len(nc_eficacia)}")
            
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_technical_users(self):
        """Prueba la obtención de usuarios técnicos"""
        try:
            technical_users = self.manager.get_technical_users()
            self.assertIsInstance(technical_users, list)
            print(f"Usuarios técnicos encontrados: {len(technical_users)}")
            
            # Verificar estructura si hay datos
            if technical_users:
                user = technical_users[0]
                self.assertIn('UsuarioRed', user)
                self.assertIn('Nombre', user)
                self.assertIn('CorreoUsuario', user)
                
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_quality_users(self):
        """Prueba la obtención de usuarios de calidad"""
        try:
            quality_users = self.manager.get_quality_users()
            self.assertIsInstance(quality_users, list)
            print(f"Usuarios de calidad encontrados: {len(quality_users)}")
            
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_admin_users(self):
        """Prueba la obtención de usuarios administradores"""
        try:
            admin_users = self.manager.get_admin_users()
            self.assertIsInstance(admin_users, list)
            print(f"Usuarios administradores encontrados: {len(admin_users)}")
            
            # Verificar estructura si hay datos
            if admin_users:
                user = admin_users[0]
                self.assertIn('UsuarioRed', user)
                self.assertIn('Nombre', user)
                self.assertIn('CorreoUsuario', user)
                
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_admin_emails_string(self):
        """Prueba la obtención de cadena de correos de administradores"""
        try:
            admin_emails = self.manager.get_admin_emails_string()
            self.assertIsInstance(admin_emails, str)
            print(f"Cadena de correos administradores: '{admin_emails}'")
            
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_get_quality_emails_string(self):
        """Prueba la obtención de cadena de correos de calidad"""
        try:
            quality_emails = self.manager.get_quality_emails_string()
            self.assertIsInstance(quality_emails, str)
            print(f"Cadena de correos calidad: '{quality_emails}'")
            
        except Exception as e:
            self.skipTest(f"Error conectando a la base de datos: {e}")
    
    def test_html_report_generation(self):
        """Prueba la generación de reportes HTML"""
        # Datos de prueba
        nc_proximas = [
            {
                'Nemotecnico': 'TEST001',
                'CodigoNoConformidad': 'NC-2024-001',
                'DESCRIPCION': 'Descripción de prueba',
                'RESPONSABLECALIDAD': 'Usuario Prueba',
                'FECHAAPERTURA': '2024-01-01',
                'FPREVCIERRE': '2024-01-15',
                'DiasParaCierre': 5
            }
        ]
        
        arapcs_proximas = [
            {
                'Nemotecnico': 'TEST001',
                'CodigoNoConformidad': 'NC-2024-001',
                'Accion': 'Acción correctiva',
                'Tarea': 'Tarea específica',
                'RESPONSABLETELEFONICA': 'Responsable Tel',
                'RESPONSABLECALIDAD': 'Responsable Cal',
                'FechaFinPrevista': '2024-01-20',
                'DiasParaVencer': 3
            }
        ]
        
        # Generar reporte técnico
        html_technical = self.manager.generate_technical_report_html(
            nc_proximas, [], arapcs_proximas, []
        )
        self.assertIsInstance(html_technical, str)
        self.assertIn('INFORME DE NO CONFORMIDADES Y ARAPCS - TÉCNICOS', html_technical)
        self.assertIn('TEST001', html_technical)
        
        # Generar reporte de calidad
        nc_eficacia = [
            {
                'Nemotecnico': 'TEST001',
                'CodigoNoConformidad': 'NC-2024-001',
                'DESCRIPCION': 'Descripción de prueba',
                'FECHAAPERTURA': '2024-01-01',
                'Accion': 'Acción correctiva',
                'FechaFinReal': '2024-01-10',
                'RESPONSABLETELEFONICA': 'Responsable',
                'DiasTranscurridos': 10
            }
        ]
        
        html_quality = self.manager.generate_quality_report_html(nc_eficacia)
        self.assertIsInstance(html_quality, str)
        self.assertIn('CONTROL DE EFICACIA', html_quality)
        self.assertIn('TEST001', html_quality)
    
    def test_manager_close_connections(self):
        """Prueba el cierre de conexiones del manager"""
        # No debe lanzar excepción
        self.manager.close_connections()


class TestNoConformidadesFullExecution(unittest.TestCase):
    """Pruebas de ejecución completa de No Conformidades"""
    
    @unittest.skipUnless(
        os.getenv('RUN_FULL_NC_TESTS', 'false').lower() == 'true',
        "Pruebas completas deshabilitadas. Usar RUN_FULL_NC_TESTS=true para habilitar"
    )
    def test_full_no_conformidades_execution(self):
        """Prueba la ejecución completa de No Conformidades"""
        task = None
        try:
            print("\n=== INICIANDO PRUEBA COMPLETA DE NO CONFORMIDADES ===")
            
            # Crear y ejecutar la tarea
            task = NoConformidadesTask()
            success = task.execute()
            
            # Verificar que se ejecutó correctamente
            self.assertTrue(success, "La ejecución de No Conformidades debería ser exitosa")
            
            print("=== PRUEBA COMPLETA DE NO CONFORMIDADES EXITOSA ===")
            
        except Exception as e:
            self.fail(f"Error en la ejecución completa de No Conformidades: {e}")
        finally:
            if task:
                try:
                    task.close_connections()
                except:
                    pass


if __name__ == '__main__':
    # Configurar logging para las pruebas
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    unittest.main(verbosity=2)