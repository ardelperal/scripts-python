"""Tests unitarios para ExpedientesTask"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'src')
sys.path.insert(0, src_dir)

from expedientes.expedientes_task import ExpedientesTask


class TestExpedientesTask(unittest.TestCase):
    """Tests para ExpedientesTask"""
    
    def setUp(self):
        """Configuración para cada test"""
        self.task = ExpedientesTask()
    
    def test_init(self):
        """Test de inicialización de ExpedientesTask"""
        self.assertEqual(self.task.name, "EXPEDIENTES")
        self.assertEqual(self.task.script_filename, "run_expedientes.py")
        self.assertEqual(self.task.task_names, ["ExpedientesDiario"])
        self.assertEqual(self.task.frequency_days, 1)
        self.assertIsNone(self.task.manager)  # Manager se inicializa como None
    
    @patch('expedientes.expedientes_task.ExpedientesManager')
    def test_execute_specific_logic_success(self, mock_manager_class):
        """Test de ejecución exitosa de lógica específica"""
        # Configurar mock
        mock_manager = Mock()
        mock_manager.ejecutar_logica_especifica.return_value = True
        mock_manager_class.return_value = mock_manager
        
        # Ejecutar
        result = self.task.execute_specific_logic()
        
        # Verificar
        self.assertTrue(result)
        mock_manager_class.assert_called_once()
        mock_manager.ejecutar_logica_especifica.assert_called_once()
        self.assertEqual(self.task.manager, mock_manager)
    
    @patch('expedientes.expedientes_task.ExpedientesManager')
    def test_execute_specific_logic_fail(self, mock_manager_class):
        """Test de fallo en ejecución de lógica específica"""
        # Configurar mock
        mock_manager = Mock()
        mock_manager.ejecutar_logica_especifica.return_value = False
        mock_manager_class.return_value = mock_manager
        
        # Ejecutar
        result = self.task.execute_specific_logic()
        
        # Verificar
        self.assertFalse(result)
        mock_manager_class.assert_called_once()
        mock_manager.ejecutar_logica_especifica.assert_called_once()
    
    @patch('expedientes.expedientes_task.ExpedientesManager')
    def test_execute_specific_logic_exception(self, mock_manager_class):
        """Test de excepción en ejecución de lógica específica"""
        # Configurar mock para lanzar excepción
        mock_manager_class.side_effect = Exception("Error de prueba")
        
        # Ejecutar
        result = self.task.execute_specific_logic()
        
        # Verificar
        self.assertFalse(result)
        mock_manager_class.assert_called_once()
    
    def test_close_connections(self):
        """Test de cierre de conexiones"""
        # Configurar mock manager
        mock_manager = Mock()
        self.task.manager = mock_manager
        
        # Ejecutar close_connections
        self.task.close_connections()
        
        # Verificar que se llamó close_connections
        mock_manager.close_connections.assert_called_once()
    
    def test_close_connections_no_manager(self):
        """Test de cierre de conexiones sin manager"""
        # Manager es None
        self.task.manager = None
        
        # Ejecutar close_connections (no debe lanzar excepción)
        self.task.close_connections()
        
        # No hay nada que verificar, solo que no lance excepción
    
    def test_close_connections_exception(self):
        """Test de cierre de conexiones con excepción"""
        # Configurar mock manager que lanza excepción
        mock_manager = Mock()
        mock_manager.close_connections.side_effect = Exception("Error de prueba")
        self.task.manager = mock_manager
        
        # Ejecutar close_connections (no debe lanzar excepción)
        self.task.close_connections()
        
        # Verificar que se intentó llamar close_connections
        mock_manager.close_connections.assert_called_once()


if __name__ == '__main__':
    unittest.main()