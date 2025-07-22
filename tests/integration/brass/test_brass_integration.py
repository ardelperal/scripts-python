"""
Test de integración para el módulo BRASS
Prueba el funcionamiento completo del sistema de gestión de equipos de medida
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import date

# Añadir src al path
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestBrassIntegration:
    """Tests de integración para el módulo BRASS completo"""
    
    def test_brass_config_loading(self):
        """Test BRASS: carga correcta de configuración para equipos de medida"""
        from common.config import config
        
        assert config.environment == 'local'
        assert config.db_password == 'dpddpd'
        assert 'Gestion_Brass_Gestion_Datos.accdb' in str(config.db_brass_path)
        assert 'Tareas_datos1.accdb' in str(config.db_tareas_path)
    
    def test_brass_database_connection_strings(self):
        """Test BRASS: generación correcta de cadenas de conexión para bases de datos de equipos"""
        from common.config import config
        
        brass_conn = config.get_db_brass_connection_string()
        tareas_conn = config.get_db_tareas_connection_string()
        
        assert "Driver=" in brass_conn
        assert "Gestion_Brass_Gestion_Datos.accdb" in brass_conn
        assert config.db_password in brass_conn
        
        assert "Driver=" in tareas_conn
        assert "Tareas_datos1.accdb" in tareas_conn
        assert config.db_password in tareas_conn
    
    @patch('common.database.AccessDatabase')
    def test_brass_manager_initialization(self, mock_db_class):
        """Test BRASS: inicialización correcta del gestor de equipos de medida"""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        with patch('common.utils.load_css_content', return_value="/* CSS test */"):
            from brass.brass_manager import BrassManager
            manager = BrassManager()
            
            # Verificar que se creó el manager correctamente
            assert manager is not None
    
    @patch('common.database.AccessDatabase')
    def test_brass_complete_workflow_simulation(self, mock_db_class):
        """Test BRASS: simulación del flujo completo de trabajo"""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        # Simular que la tarea no se ha ejecutado hoy
        mock_db.execute_query.return_value = []
        
        with patch('common.utils.load_css_content') as mock_css:
            mock_css.return_value = "body { margin: 0; }"
            
            from brass.brass_manager import BrassManager
            manager = BrassManager()
            
            # Mock de todos los métodos principales de BRASS
            with patch.object(manager, 'is_task_completed_today', return_value=False), \
                 patch.object(manager, 'get_equipment_out_of_calibration', return_value=[]), \
                 patch.object(manager, 'register_task_completion', return_value=True):
                
                result = manager.execute_task()
                
                # Verificar que el flujo BRASS se ejecutó correctamente
                assert result == True
