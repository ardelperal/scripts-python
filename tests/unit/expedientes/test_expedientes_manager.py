"""
Tests unitarios para ExpedientesManager
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.expedientes.expedientes_manager import ExpedientesManager


class TestExpedientesManager:
    """Tests para la clase ExpedientesManager"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de configuración"""
        with patch('src.expedientes.expedientes_manager.config') as mock_config:
            mock_config.database_mode = 'access'
            mock_config.get_db_expedientes_connection_string.return_value = "mock_exp_conn"
            mock_config.get_db_correos_connection_string.return_value = "mock_correos_conn"
            mock_config.get_db_tareas_connection_string.return_value = "mock_tareas_conn"
            mock_config.default_recipient = "test@example.com"
            yield mock_config
    
    @pytest.fixture
    def mock_access_database(self):
        """Mock de AccessDatabase"""
        with patch('src.expedientes.expedientes_manager.AccessDatabase') as mock_db:
            yield mock_db
    
    @pytest.fixture
    def mock_utils(self):
        """Mock de utilidades"""
        with patch('src.expedientes.expedientes_manager.format_date') as mock_format_date, \
             patch('src.expedientes.expedientes_manager.send_email') as mock_send_email:
            
            mock_format_date.return_value = "2024-01-15"
            mock_send_email.return_value = True
            
            yield {
                'format_date': mock_format_date,
                'send_email': mock_send_email
            }
    
    @pytest.fixture
    def expedientes_manager(self, mock_config, mock_access_database, mock_utils):
        """Instancia de ExpedientesManager con mocks"""
        return ExpedientesManager()
    
    def test_init(self, expedientes_manager, mock_access_database, mock_config):
        """Test de inicialización"""
        assert expedientes_manager.expedientes_conn is not None
        assert expedientes_manager.correos_conn is not None
        assert expedientes_manager.tareas_conn is not None
    
    def test_close_connections(self, expedientes_manager):
        """Test cerrar conexiones"""
        # Mock de conexiones con método close
        expedientes_manager.expedientes_conn = Mock()
        expedientes_manager.correos_conn = Mock()
        expedientes_manager.tareas_conn = Mock()
        
        expedientes_manager.close_connections()
        
        expedientes_manager.expedientes_conn.close.assert_called_once()
        expedientes_manager.correos_conn.close.assert_called_once()
        expedientes_manager.tareas_conn.close.assert_called_once()
    
    def test_close_connections_exception(self, expedientes_manager):
        """Test cerrar conexiones con excepción"""
        expedientes_manager.expedientes_conn = Mock()
        expedientes_manager.expedientes_conn.close.side_effect = Exception("Close error")
        
        # No debe lanzar excepción
        expedientes_manager.close_connections()
    
    def test_get_expedientes_about_to_finish_access(self, expedientes_manager):
        """Test obtener expedientes próximos a finalizar - Access"""
        mock_cursor = Mock()
        mock_results = [
            ('EXP001', '2024-02-01', 'En Proceso', 'Juan Pérez', 'Descripción 1'),
            ('EXP002', '2024-02-05', 'En Proceso', 'María García', 'Descripción 2')
        ]
        mock_cursor.fetchall.return_value = mock_results
        expedientes_manager.expedientes_conn.get_cursor.return_value = mock_cursor
        
        result = expedientes_manager.get_expedientes_about_to_finish(30)
        
        assert len(result) == 2
        assert result[0]['expediente'] == 'EXP001'
        assert result[0]['estado'] == 'En Proceso'
        assert result[1]['expediente'] == 'EXP002'
        mock_cursor.execute.assert_called_once()
    
    def test_get_expedientes_about_to_finish_exception(self, expedientes_manager):
        """Test obtener expedientes próximos a finalizar con excepción"""
        expedientes_manager.expedientes_conn.get_cursor.side_effect = Exception("DB Error")
        
        result = expedientes_manager.get_expedientes_about_to_finish()
        
        assert result == []
    
    def test_get_hitos_about_to_finish_access(self, expedientes_manager):
        """Test obtener hitos próximos a finalizar - Access"""
        mock_cursor = Mock()
        mock_results = [
            (1, 'EXP001', 'Hito 1', '2024-02-01', 'Pendiente', 'Juan Pérez'),
            (2, 'EXP002', 'Hito 2', '2024-02-05', 'Pendiente', 'María García')
        ]
        mock_cursor.fetchall.return_value = mock_results
        expedientes_manager.expedientes_conn.get_cursor.return_value = mock_cursor
        
        result = expedientes_manager.get_hitos_about_to_finish(15)
        
        assert len(result) == 2
        assert result[0]['id_hito'] == 1
        assert result[0]['expediente'] == 'EXP001'
        assert result[1]['id_hito'] == 2
        mock_cursor.execute.assert_called_once()
    
    def test_get_hitos_about_to_finish_exception(self, expedientes_manager):
        """Test obtener hitos próximos a finalizar con excepción"""
        expedientes_manager.expedientes_conn.get_cursor.side_effect = Exception("DB Error")
        
        result = expedientes_manager.get_hitos_about_to_finish()
        
        assert result == []
    
    def test_get_expedientes_sin_cods4h_access(self, expedientes_manager):
        """Test obtener expedientes sin CodS4H - Access"""
        mock_cursor = Mock()
        mock_results = [
            ('TSOL001', '2024-01-15', 50000.0, 'Proveedor A', 'Adjudicado'),
            ('TSOL002', '2024-01-20', 75000.0, 'Proveedor B', 'Adjudicado')
        ]
        mock_cursor.fetchall.return_value = mock_results
        expedientes_manager.expedientes_conn.get_cursor.return_value = mock_cursor
        
        result = expedientes_manager.get_expedientes_sin_cods4h()
        
        assert len(result) == 2
        assert result[0]['expediente'] == 'TSOL001'
        assert result[0]['importe'] == 50000.0
        assert result[1]['expediente'] == 'TSOL002'
        mock_cursor.execute.assert_called_once()
    
    def test_get_expedientes_sin_cods4h_exception(self, expedientes_manager):
        """Test obtener expedientes sin CodS4H con excepción"""
        expedientes_manager.expedientes_conn.get_cursor.side_effect = Exception("DB Error")
        
        result = expedientes_manager.get_expedientes_sin_cods4h()
        
        assert result == []
    
    def test_get_expedientes_fase_oferta_largo_tiempo_access(self, expedientes_manager):
        """Test obtener expedientes en fase de oferta por mucho tiempo - Access"""
        mock_cursor = Mock()
        mock_results = [
            ('EXP001', '2023-11-01', 'En Oferta', 'Juan Pérez', 'Descripción 1'),
            ('EXP002', '2023-10-15', 'En Oferta', 'María García', 'Descripción 2')
        ]
        mock_cursor.fetchall.return_value = mock_results
        expedientes_manager.expedientes_conn.get_cursor.return_value = mock_cursor
        
        result = expedientes_manager.get_expedientes_fase_oferta_largo_tiempo(60)
        
        assert len(result) == 2
        assert result[0]['expediente'] == 'EXP001'
        assert result[0]['estado'] == 'En Oferta'
        assert result[1]['expediente'] == 'EXP002'
        mock_cursor.execute.assert_called_once()
    
    def test_get_expedientes_fase_oferta_largo_tiempo_exception(self, expedientes_manager):
        """Test obtener expedientes en fase de oferta con excepción"""
        expedientes_manager.expedientes_conn.get_cursor.side_effect = Exception("DB Error")
        
        result = expedientes_manager.get_expedientes_fase_oferta_largo_tiempo()
        
        assert result == []
    
    def test_generate_html_header(self, expedientes_manager):
        """Test generar cabecera HTML"""
        result = expedientes_manager._generate_html_header()
        
        assert "<html>" in result
        assert "<title>Reporte Diario de Expedientes" in result
        assert "font-family: Arial" in result
    
    def test_generate_expedientes_proximos_section(self, expedientes_manager):
        """Test generar sección de expedientes próximos"""
        expedientes = [
            {
                'expediente': 'EXP001',
                'fecha_finalizacion': '2024-02-01',
                'estado': 'En Proceso',
                'responsable': 'Juan Pérez',
                'descripcion': 'Descripción 1'
            }
        ]
        
        result = expedientes_manager._generate_expedientes_proximos_section(expedientes)
        
        assert "Expedientes Próximos a Finalizar" in result
        assert "EXP001" in result
        assert "Juan Pérez" in result
        assert "<table>" in result
    
    def test_generate_hitos_proximos_section(self, expedientes_manager):
        """Test generar sección de hitos próximos"""
        hitos = [
            {
                'id_hito': 1,
                'expediente': 'EXP001',
                'descripcion': 'Hito 1',
                'fecha_limite': '2024-02-01',
                'estado': 'Pendiente',
                'responsable': 'Juan Pérez'
            }
        ]
        
        result = expedientes_manager._generate_hitos_proximos_section(hitos)
        
        assert "Hitos Próximos a Finalizar" in result
        assert "EXP001" in result
        assert "Hito 1" in result
        assert "<table>" in result
    
    def test_generate_sin_cods4h_section(self, expedientes_manager):
        """Test generar sección de expedientes sin CodS4H"""
        expedientes = [
            {
                'expediente': 'TSOL001',
                'fecha_adjudicacion': '2024-01-15',
                'importe': 50000.0,
                'proveedor': 'Proveedor A',
                'estado': 'Adjudicado'
            }
        ]
        
        result = expedientes_manager._generate_sin_cods4h_section(expedientes)
        
        assert "Expedientes TSOL Adjudicados sin CodS4H" in result
        assert "TSOL001" in result
        assert "Proveedor A" in result
        assert "<table>" in result
    
    def test_generate_oferta_largo_section(self, expedientes_manager):
        """Test generar sección de expedientes en oferta por mucho tiempo"""
        expedientes = [
            {
                'expediente': 'EXP001',
                'fecha_inicio_oferta': '2023-11-01',
                'estado': 'En Oferta',
                'responsable': 'Juan Pérez',
                'descripcion': 'Descripción 1'
            }
        ]
        
        result = expedientes_manager._generate_oferta_largo_section(expedientes)
        
        assert "Expedientes en Fase de Oferta por Mucho Tiempo" in result
        assert "EXP001" in result
        assert "Juan Pérez" in result
        assert "<table>" in result
    
    def test_generate_html_footer(self, expedientes_manager):
        """Test generar pie HTML"""
        result = expedientes_manager._generate_html_footer()
        
        assert "</body>" in result
        assert "</html>" in result
    
    def test_generate_html_report_with_data(self, expedientes_manager):
        """Test generar reporte HTML con datos"""
        with patch.object(expedientes_manager, 'get_expedientes_about_to_finish') as mock_exp, \
             patch.object(expedientes_manager, 'get_hitos_about_to_finish') as mock_hitos, \
             patch.object(expedientes_manager, 'get_expedientes_sin_cods4h') as mock_sin_cod, \
             patch.object(expedientes_manager, 'get_expedientes_fase_oferta_largo_tiempo') as mock_oferta:
            
            mock_exp.return_value = [{'expediente': 'EXP001', 'fecha_finalizacion': '2024-02-01', 'estado': 'En Proceso', 'responsable': 'Juan', 'descripcion': 'Desc'}]
            mock_hitos.return_value = [{'id_hito': 1, 'expediente': 'EXP001', 'descripcion': 'Hito', 'fecha_limite': '2024-02-01', 'estado': 'Pendiente', 'responsable': 'Juan'}]
            mock_sin_cod.return_value = [{'expediente': 'TSOL001', 'fecha_adjudicacion': '2024-01-15', 'importe': 50000, 'proveedor': 'Prov', 'estado': 'Adj'}]
            mock_oferta.return_value = [{'expediente': 'EXP002', 'fecha_inicio_oferta': '2023-11-01', 'estado': 'En Oferta', 'responsable': 'María', 'descripcion': 'Desc2'}]
            
            result = expedientes_manager.generate_html_report()
            
            assert "<html>" in result
            assert "Reporte Diario de Expedientes" in result
            assert "EXP001" in result
            assert "TSOL001" in result
            assert "EXP002" in result
            assert "</html>" in result
    
    def test_generate_html_report_no_data(self, expedientes_manager):
        """Test generar reporte HTML sin datos"""
        with patch.object(expedientes_manager, 'get_expedientes_about_to_finish') as mock_exp, \
             patch.object(expedientes_manager, 'get_hitos_about_to_finish') as mock_hitos, \
             patch.object(expedientes_manager, 'get_expedientes_sin_cods4h') as mock_sin_cod, \
             patch.object(expedientes_manager, 'get_expedientes_fase_oferta_largo_tiempo') as mock_oferta:
            
            mock_exp.return_value = []
            mock_hitos.return_value = []
            mock_sin_cod.return_value = []
            mock_oferta.return_value = []
            
            result = expedientes_manager.generate_html_report()
            
            assert "<html>" in result
            assert "Reporte Diario de Expedientes" in result
            assert "</html>" in result
    
    def test_generate_html_report_exception(self, expedientes_manager):
        """Test generar reporte HTML con excepción"""
        with patch.object(expedientes_manager, 'get_expedientes_about_to_finish') as mock_exp:
            mock_exp.side_effect = Exception("Error")
            
            result = expedientes_manager.generate_html_report()
            
            assert result == ""
    
    def test_register_email_sent_access_success(self, expedientes_manager):
        """Test registrar email enviado - Access exitoso"""
        mock_cursor = Mock()
        expedientes_manager.correos_conn.get_cursor.return_value = mock_cursor
        expedientes_manager.correos_conn.commit.return_value = None
        
        result = expedientes_manager.register_email_sent(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        expedientes_manager.correos_conn.commit.assert_called_once()
    
    def test_register_email_sent_exception(self, expedientes_manager):
        """Test registrar email enviado con excepción"""
        expedientes_manager.correos_conn.get_cursor.side_effect = Exception("DB Error")
        
        result = expedientes_manager.register_email_sent(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        
        assert result is False
    
    def test_execute_daily_task_success(self, expedientes_manager, mock_utils):
        """Test ejecutar tarea diaria exitoso"""
        with patch.object(expedientes_manager, 'generate_html_report') as mock_generate, \
             patch.object(expedientes_manager, 'register_email_sent') as mock_register:
            
            mock_generate.return_value = "<html>Test Report</html>"
            mock_register.return_value = True
            mock_utils['send_email'].return_value = True
            
            result = expedientes_manager.execute_daily_task()
            
            assert result is True
            mock_generate.assert_called_once()
            mock_utils['send_email'].assert_called_once()
            mock_register.assert_called_once()
    
    def test_execute_daily_task_no_report(self, expedientes_manager):
        """Test ejecutar tarea diaria sin reporte"""
        with patch.object(expedientes_manager, 'generate_html_report') as mock_generate:
            mock_generate.return_value = ""
            
            result = expedientes_manager.execute_daily_task()
            
            assert result is False
    
    def test_execute_daily_task_email_failure(self, expedientes_manager, mock_utils):
        """Test ejecutar tarea diaria con fallo en email"""
        with patch.object(expedientes_manager, 'generate_html_report') as mock_generate:
            mock_generate.return_value = "<html>Test Report</html>"
            mock_utils['send_email'].return_value = False
            
            result = expedientes_manager.execute_daily_task()
            
            assert result is False
    
    def test_execute_daily_task_exception(self, expedientes_manager):
        """Test ejecutar tarea diaria con excepción"""
        with patch.object(expedientes_manager, 'generate_html_report') as mock_generate:
            mock_generate.side_effect = Exception("Error")
            
            result = expedientes_manager.execute_daily_task()
            
            assert result is False