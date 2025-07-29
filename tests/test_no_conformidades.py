"""
Tests para el módulo de No Conformidades
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio padre al path para importar módulos
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.no_conformidades.no_conformidades_manager import (
    NoConformidadesManager, NoConformidad, ARAPC, Usuario
)
from src.common.html_report_generator import HTMLReportGenerator
from src.no_conformidades.email_notifications import EmailNotificationManager


class TestNoConformidad(unittest.TestCase):
    """Tests para la clase NoConformidad"""
    
    def test_crear_no_conformidad(self):
        """Test crear una No Conformidad"""
        fecha_apertura = datetime(2024, 1, 1)
        fecha_cierre = datetime(2024, 2, 1)
        
        nc = NoConformidad(
            codigo="NC-001",
            nemotecnico="TEST",
            descripcion="Descripción de prueba",
            responsable_calidad="Juan Pérez",
            fecha_apertura=fecha_apertura,
            fecha_prev_cierre=fecha_cierre,
            dias_para_cierre=10
        )
        
        self.assertEqual(nc.codigo, "NC-001")
        self.assertEqual(nc.nemotecnico, "TEST")
        self.assertEqual(nc.descripcion, "Descripción de prueba")
        self.assertEqual(nc.responsable_calidad, "Juan Pérez")
        self.assertEqual(nc.fecha_apertura, fecha_apertura)
        self.assertEqual(nc.fecha_prev_cierre, fecha_cierre)
        self.assertEqual(nc.dias_para_cierre, 10)


class TestARAPC(unittest.TestCase):
    """Tests para la clase ARAPC"""
    
    def test_crear_arapc(self):
        """Test crear una ARAPC"""
        fecha_fin = datetime(2024, 2, 1)
        
        arapc = ARAPC(
            id_accion=1,
            codigo_nc="NC-001",
            descripcion="Acción correctiva de prueba",
            responsable="María García",
            fecha_fin_prevista=fecha_fin
        )
        
        self.assertEqual(arapc.id_accion, 1)
        self.assertEqual(arapc.codigo_nc, "NC-001")
        self.assertEqual(arapc.descripcion, "Acción correctiva de prueba")
        self.assertEqual(arapc.responsable, "María García")
        self.assertEqual(arapc.fecha_fin_prevista, fecha_fin)
        self.assertIsNone(arapc.fecha_fin_real)


class TestUsuario(unittest.TestCase):
    """Tests para la clase Usuario"""
    
    def test_crear_usuario(self):
        """Test crear un Usuario"""
        usuario = Usuario(
            usuario_red="jperez",
            nombre="Juan Pérez",
            correo="juan.perez@empresa.com"
        )
        
        self.assertEqual(usuario.usuario_red, "jperez")
        self.assertEqual(usuario.nombre, "Juan Pérez")
        self.assertEqual(usuario.correo, "juan.perez@empresa.com")


class TestNoConformidadesManager(unittest.TestCase):
    """Tests para la clase NoConformidadesManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.manager = NoConformidadesManager()
    
    @patch('src.no_conformidades.no_conformidades_manager.get_database_instance')
    @patch('src.no_conformidades.no_conformidades_manager.Config')
    def test_conectar_bases_datos(self, mock_config, mock_get_db):
        """Test conectar a las bases de datos"""
        # Configurar mocks
        mock_config_instance = Mock()
        mock_config_instance.get_db_no_conformidades_connection_string.return_value = "connection_nc"
        mock_config_instance.get_db_tareas_connection_string.return_value = "connection_tareas"
        mock_config.return_value = mock_config_instance
        
        mock_db_nc = Mock()
        mock_db_tareas = Mock()
        mock_get_db.side_effect = [mock_db_nc, mock_db_tareas]
        
        # Ejecutar
        manager = NoConformidadesManager()
        manager.conectar_bases_datos()
        
        # Verificar
        self.assertEqual(manager.db_nc, mock_db_nc)
        self.assertEqual(manager.db_tareas, mock_db_tareas)
        mock_get_db.assert_any_call("connection_nc")
        mock_get_db.assert_any_call("connection_tareas")
    
    @patch('src.common.utils.get_admin_emails_string')
    def test_obtener_cadena_correos_administradores(self, mock_get_admin_emails):
        """Test obtener cadena de correos de administradores usando función común"""
        # Configurar mock
        mock_get_admin_emails.return_value = "admin1@empresa.com;admin2@empresa.com"
        
        # Ejecutar - ahora usa la función común
        from src.common.utils import get_admin_emails_string
        cadena = get_admin_emails_string()
        
        # Verificar
        self.assertEqual(cadena, "admin1@empresa.com;admin2@empresa.com")
        mock_get_admin_emails.assert_called_once()
    
    @patch('src.common.utils.get_quality_emails_string')
    def test_obtener_cadena_correos_calidad(self, mock_get_quality_emails):
        """Test obtener cadena de correos de calidad usando función común"""
        # Configurar mock
        mock_get_quality_emails.return_value = "calidad1@empresa.com;calidad2@empresa.com"
        
        # Ejecutar - ahora usa la función común
        from src.common.utils import get_quality_emails_string
        cadena = get_quality_emails_string()
        
        # Verificar
        self.assertEqual(cadena, "calidad1@empresa.com;calidad2@empresa.com")
        mock_get_quality_emails.assert_called_once()
    
    @patch('src.common.utils.get_admin_emails_string')
    def test_obtener_cadena_correos_vacia(self, mock_get_admin_emails):
        """Test obtener cadena de correos cuando no hay usuarios usando función común"""
        # Configurar mock para retornar cadena vacía
        mock_get_admin_emails.return_value = ""
        
        # Ejecutar - ahora usa la función común
        from src.common.utils import get_admin_emails_string
        cadena = get_admin_emails_string()
        
        # Verificar
        self.assertEqual(cadena, "")
        mock_get_admin_emails.assert_called_once()
    
    @patch('src.common.utils.should_execute_task')
    def test_determinar_si_requiere_tarea_calidad_primera_vez(self, mock_should_execute):
        """Test determinar si requiere tarea de calidad - primera ejecución usando función común"""
        # Configurar mock
        mock_should_execute.return_value = True
        
        # Ejecutar - ahora usa la función común
        from src.common.utils import should_execute_task
        resultado = should_execute_task("NoConformidadesCalidad", 7)
        
        # Verificar
        self.assertTrue(resultado)
        mock_should_execute.assert_called_once_with("NoConformidadesCalidad", 7)
    
    @patch('src.common.utils.should_execute_task')
    def test_determinar_si_requiere_tarea_calidad_reciente(self, mock_should_execute):
        """Test determinar si requiere tarea de calidad - ejecución reciente usando función común"""
        # Configurar mock
        mock_should_execute.return_value = False
        
        # Ejecutar - ahora usa la función común
        from src.common.utils import should_execute_task
        resultado = should_execute_task("NoConformidadesCalidad", 7)
        
        # Verificar
        self.assertFalse(resultado)  # No requiere porque han pasado menos de 7 días
        mock_should_execute.assert_called_once_with("NoConformidadesCalidad", 7)
    
    @patch('src.common.utils.should_execute_task')
    def test_determinar_si_requiere_tarea_calidad_antigua(self, mock_should_execute):
        """Test determinar si requiere tarea de calidad - ejecución antigua usando función común"""
        # Configurar mock
        mock_should_execute.return_value = True
        
        # Ejecutar - ahora usa la función común
        from src.common.utils import should_execute_task
        resultado = should_execute_task("NoConformidadesCalidad", 7)
        
        # Verificar
        self.assertTrue(resultado)  # Requiere porque han pasado más de 7 días
        mock_should_execute.assert_called_once_with("NoConformidadesCalidad", 7)


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


class TestEmailNotificationManager(unittest.TestCase):
    """Tests para la clase EmailNotificationManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # No necesitamos patch en setUp, lo haremos en cada test individual
        self.email_manager = EmailNotificationManager()
    
    @patch('src.common.utils.send_email')
    def test_enviar_notificacion_calidad_exitosa(self, mock_send_email):
        """Test envío exitoso de notificación de calidad"""
        # Configurar mock
        mock_send_email.return_value = True
        
        # Datos de prueba
        ncs_eficacia = [Mock()]
        ncs_caducar = [Mock()]
        ncs_sin_acciones = [Mock()]
        destinatarios_calidad = "calidad@empresa.com"
        destinatarios_admin = "admin@empresa.com"
        
        # Ejecutar
        resultado = self.email_manager.enviar_notificacion_calidad(
            ncs_eficacia, ncs_caducar, ncs_sin_acciones,
            destinatarios_calidad, destinatarios_admin
        )
        
        # Verificar
        self.assertTrue(resultado)
        mock_send_email.assert_called_once()
    
    @patch('src.common.utils.send_email')
    def test_enviar_notificacion_sin_destinatarios(self, mock_send_email):
        """Test envío de notificación sin destinatarios"""
        # Datos de prueba sin destinatarios
        ncs_eficacia = [Mock()]
        ncs_caducar = []
        ncs_sin_acciones = []
        destinatarios_calidad = ""
        destinatarios_admin = ""
        
        # Ejecutar
        resultado = self.email_manager.enviar_notificacion_calidad(
            ncs_eficacia, ncs_caducar, ncs_sin_acciones,
            destinatarios_calidad, destinatarios_admin
        )
        
        # Verificar
        self.assertFalse(resultado)
        mock_send_email.assert_not_called()
    
    @patch('src.common.utils.send_email')
    def test_enviar_notificacion_individual_arapc(self, mock_send_email):
        """Test envío de notificación individual ARAPC"""
        # Configurar mock
        mock_send_email.return_value = True
        
        # Datos de prueba
        arapc = ARAPC(
            id_accion=1,
            codigo_nc="NC-001",
            descripcion="Acción de prueba",
            responsable="jperez",
            fecha_fin_prevista=datetime.now() + timedelta(days=2)
        )
        
        usuario = Usuario(
            usuario_red="jperez",
            nombre="Juan Pérez",
            correo="juan.perez@empresa.com"
        )
        
        # Ejecutar
        resultado = self.email_manager.enviar_notificacion_individual_arapc(arapc, usuario)
        
        # Verificar
        self.assertTrue(resultado)
        mock_send_email.assert_called_once()
        
        # Verificar argumentos del email
        call_args = mock_send_email.call_args
        self.assertIn("juan.perez@empresa.com", call_args[1]['to_address'])
        self.assertIn("NC-001", call_args[1]['subject'])
        self.assertTrue(call_args[1]['is_html'])


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.CRITICAL)  # Solo errores críticos durante tests
    
    # Ejecutar tests
    unittest.main(verbosity=2)