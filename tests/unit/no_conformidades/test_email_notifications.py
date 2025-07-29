"""
Tests para las notificaciones por email del módulo de No Conformidades
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.no_conformidades.email_notifications import (
    EmailNotificationManager, 
    enviar_notificacion_calidad,
    enviar_notificacion_tecnica,
    enviar_notificacion_individual_arapc,
    enviar_notificaciones_individuales_arapcs
)


class TestEmailNotificationManager(unittest.TestCase):
    """Tests para la clase EmailNotificationManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # No necesitamos patch en setUp, lo haremos en cada test individual
        self.email_manager = EmailNotificationManager()
    
    @patch('src.no_conformidades.email_notifications.AccessDatabase')
    def test_enviar_notificacion_calidad_exitosa(self, mock_access_db):
        """Test envío exitoso de notificación de calidad"""
        # Mock de la base de datos
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Simular IDCorreo = 1
        mock_cursor.fetchall.return_value = [('admin@test.com',), ('quality@test.com',)]
        mock_access_db.return_value = mock_db
        
        # Mock del generador HTML y manager
        with patch('src.no_conformidades.email_notifications.HTMLReportGenerator') as mock_html_gen:
            mock_html_gen.return_value.generar_reporte_calidad.return_value = "<html>Test</html>"
            with patch('src.no_conformidades.email_notifications.EmailNotificationManager') as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_quality_emails.return_value = ['quality@test.com']
                mock_manager.get_admin_emails.return_value = ['admin@test.com']
                mock_manager_class.return_value = mock_manager
                
                # Ejecutar
                resultado = enviar_notificacion_calidad({'indicadores': 'test'})
                
                # Verificar
                self.assertTrue(resultado)
                mock_cursor.execute.assert_called()
                mock_conn.commit.assert_called_once()
    
    @patch('src.no_conformidades.email_notifications.AccessDatabase')
    def test_enviar_notificacion_sin_destinatarios(self, mock_access_db):
        """Test envío de notificación sin destinatarios"""
        # Mock de la base de datos que no devuelve destinatarios
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []  # Sin destinatarios
        mock_access_db.return_value = mock_db
        
        # Mock del manager para que no tenga emails
        with patch('src.no_conformidades.email_notifications.EmailNotificationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_admin_emails.return_value = []
            mock_manager.get_quality_emails.return_value = []
            mock_manager_class.return_value = mock_manager
            
            # Ejecutar
            resultado = enviar_notificacion_calidad({'indicadores': 'test'})
            
            # Verificar
            self.assertFalse(resultado)
            # No debe intentar insertar en la BD si no hay destinatarios
            mock_cursor.execute.assert_not_called()
    
    @patch('src.no_conformidades.email_notifications.AccessDatabase')
    def test_enviar_notificacion_individual_arapc(self, mock_access_db):
        """Test envío de notificación individual ARAPC"""
        # Mock de la base de datos
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Simular IDCorreo = 1
        mock_cursor.fetchall.return_value = [('admin@test.com',)]
        mock_access_db.return_value = mock_db
        
        # Datos de prueba
        arapc_data = {
            'id_accion': 1,
            'codigo_nc': 'NC-001',
            'descripcion': 'Test ARAPC',
            'dias_restantes': 5
        }
        usuario_responsable = {
            'nombre': 'Test User',
            'correo': 'test@example.com'
        }
        
        # Mock del generador HTML
        with patch('src.no_conformidades.email_notifications.HTMLReportGenerator') as mock_html_gen:
            mock_html_gen.return_value.generar_notificacion_individual_arapc.return_value = "<html>Individual</html>"
            
            # Ejecutar
            resultado = enviar_notificacion_individual_arapc(arapc_data, usuario_responsable)
            
            # Verificar
            self.assertTrue(resultado)
            mock_cursor.execute.assert_called()
            # Se llama commit al menos una vez (puede ser más por email + ARAPC)
            self.assertGreaterEqual(mock_conn.commit.call_count, 1)


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.CRITICAL)  # Solo errores críticos durante tests
    
    # Ejecutar tests
    unittest.main(verbosity=2)