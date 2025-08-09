import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from no_conformidades.no_conformidades_task import NoConformidadesTask


class TestNoConformidadesTask(unittest.TestCase):
    """Tests unitarios para NoConformidadesTask"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.task = NoConformidadesTask()
        self.task.manager = None
    
    def test_init(self):
        """Test de inicialización de la tarea"""
        task = NoConformidadesTask()
        
        self.assertEqual(task.name, "NoConformidades")
        self.assertEqual(task.script_filename, "run_no_conformidades.py")
        self.assertEqual(task.task_names, ["NCTecnico", "NCCalidad"])
        self.assertEqual(task.frequency_days, 1)
    
    @patch('no_conformidades.no_conformidades_task.NoConformidadesManager')
    def test_execute_specific_logic_success(self, mock_manager_class):
        """Test de ejecución exitosa de lógica específica"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run.return_value = True
        
        result = self.task.execute()
        
        self.assertTrue(result)
        mock_manager.run.assert_called_once()
    
    @patch('no_conformidades.no_conformidades_task.NoConformidadesManager')
    def test_execute_specific_logic_calidad_fail(self, mock_manager_class):
        """Test de fallo en procesamiento de calidad"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run.return_value = False
        
        result = self.task.execute()
        
        self.assertFalse(result)
    
    @patch('no_conformidades.no_conformidades_task.NoConformidadesManager')
    def test_execute_specific_logic_tecnicos_fail(self, mock_manager_class):
        """Test de fallo en procesamiento de técnicos"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run.return_value = False
        
        result = self.task.execute()
        
        self.assertFalse(result)
    
    @patch('no_conformidades.no_conformidades_task.NoConformidadesManager')
    def test_execute_specific_logic_both_fail(self, mock_manager_class):
        """Test de fallo en ambos procesamientos"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run.return_value = False
        
        result = self.task.execute()
        
        self.assertFalse(result)
    
    @patch('no_conformidades.no_conformidades_task.NoConformidadesManager')
    def test_execute_specific_logic_exception(self, mock_manager_class):
        """Test de manejo de excepciones en lógica específica"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run.side_effect = Exception("Test error")
        
        result = self.task.execute()
        
        self.assertFalse(result)
    
    def test_close_connections_success(self):
        """Test de cierre exitoso de conexiones"""
        mock_manager = Mock()
        self.task.manager = mock_manager
        
        self.task.close_connections()
        
        mock_manager.close_connections.assert_called_once()
    
    def test_close_connections_no_manager(self):
        """Test de cierre sin manager"""
        self.task.manager = None
        
        # No debería lanzar excepción
        self.task.close_connections()
    
    def test_close_connections_exception(self):
        """Test de cierre con excepción"""
        mock_manager = Mock()
        mock_manager.close_connections.side_effect = Exception("Close error")
        self.task.manager = mock_manager
        
        # No debería lanzar excepción
        self.task.close_connections()


if __name__ == '__main__':
    unittest.main()