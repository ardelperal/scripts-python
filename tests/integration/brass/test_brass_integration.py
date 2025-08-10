"""Tests de integración para el módulo BRASS
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import date, datetime

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from common.config import config
from common.database import AccessDatabase
from common.utils import load_css_content
from brass.brass_task import BrassTask


class TestBrassIntegration:
    """Tests de integración para el módulo BRASS completo"""
    
    def test_brass_config_loading(self):
        """Test BRASS: carga correcta de configuración para equipos de medida"""
        assert config.environment in ['local', 'oficina']
        assert config.db_password == 'dpddpd'
        assert 'Gestion_Brass_Gestion_Datos.accdb' in str(config.db_brass_path)
        assert 'Tareas_datos1.accdb' in str(config.db_tareas_path)
    
    def test_brass_database_connection_strings(self):
        """Test BRASS: generación correcta de cadenas de conexión para bases de datos de equipos"""
        brass_conn = config.get_db_brass_connection_string()
        tareas_conn = config.get_db_tareas_connection_string()
        
        assert "Driver=" in brass_conn
        assert "Gestion_Brass_Gestion_Datos.accdb" in brass_conn
        assert config.db_password in brass_conn
        
        assert "Driver=" in tareas_conn
        assert "Tareas_datos1.accdb" in tareas_conn
        assert config.db_password in tareas_conn
    
    @patch('src.common.database.AccessDatabase')
    def test_brass_task_initialization(self, mock_db_class):
        """Test BRASS: inicialización correcta de BrassTask (nuevo patrón)"""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        task = BrassTask()
        assert task is not None

    @patch('src.common.database.AccessDatabase')
    def test_brass_task_workflow_empty_report(self, mock_db_class):
        """Flujo BrassTask cuando el manager devuelve informe vacío (no registra correo)."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        task = BrassTask()
        with patch('brass.brass_task.BrassManager') as mock_manager_cls:
            instance = mock_manager_cls.return_value
            instance.generate_brass_report_html.return_value = ""
            ok = task.execute_specific_logic()
            assert ok is True
            instance.generate_brass_report_html.assert_called_once()

    @patch('src.common.database.AccessDatabase')
    def test_brass_task_workflow_with_report(self, mock_db_class):
        """Flujo BrassTask con informe no vacío registra correo estándar."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        task = BrassTask()
        with patch('brass.brass_task.BrassManager') as mock_manager_cls, \
             patch('brass.brass_task.register_standard_report', return_value=True) as mock_register:
            instance = mock_manager_cls.return_value
            instance.generate_brass_report_html.return_value = "<html>ok</html>"
            ok = task.execute_specific_logic()
            assert ok is True
            mock_register.assert_called_once()
