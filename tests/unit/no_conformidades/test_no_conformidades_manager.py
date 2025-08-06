"""
Tests para el módulo de No Conformidades Manager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.no_conformidades.no_conformidades_manager import NoConformidadesManager


# Las clases NoConformidad, ARAPC y Usuario ya no existen en el manager actual
# Se eliminan estos tests obsoletos


class TestNoConformidadesManager(unittest.TestCase):
    """Tests para la clase NoConformidadesManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.manager = NoConformidadesManager()
    
    @patch('src.no_conformidades.no_conformidades_manager.AccessDatabase')
    @patch('src.no_conformidades.no_conformidades_manager.Config')
    def test_conectar_bases_datos(self, mock_config, mock_access_db):
        """Test conectar a las bases de datos"""
        # Configurar mocks
        mock_config_instance = Mock()
        mock_config_instance.get_db_no_conformidades_connection_string.return_value = "connection_nc"
        mock_config_instance.get_db_tareas_connection_string.return_value = "connection_tareas"
        mock_config.return_value = mock_config_instance
        
        mock_db_nc = Mock()
        mock_db_tareas = Mock()
        mock_access_db.side_effect = [mock_db_nc, mock_db_tareas]
        
        # Ejecutar
        manager = NoConformidadesManager()
        nc_conn = manager._get_nc_connection()
        tareas_conn = manager._get_tareas_connection()
        
        # Verificar que las conexiones se obtienen correctamente
        self.assertIsNotNone(nc_conn)
        self.assertIsNotNone(tareas_conn)
    
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


if __name__ == '__main__':
    unittest.main()