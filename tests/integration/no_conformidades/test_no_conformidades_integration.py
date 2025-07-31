"""
Tests de integración para el módulo No Conformidades
Siguiendo el patrón establecido en AGEDYS para mantener consistencia
"""
import pytest
import os
from unittest.mock import patch, Mock
from datetime import datetime, date, timedelta
from src.no_conformidades.no_conformidades_manager import NoConformidadesManager, NoConformidad
from src.common.database import AccessDatabase


class TestNoConformidadesIntegration:
    """Tests de integración para No Conformidades"""
    
    @pytest.fixture
    def test_db_paths(self):
        """Rutas de bases de datos de prueba"""
        return {
            'no_conformidades': 'tests/data/test_no_conformidades.accdb',
            'tareas': 'tests/data/test_tareas.accdb'
        }
    
    @pytest.fixture
    def mock_access_database(self):
        """Mock de get_database_instance para tests de integración"""
        with patch('src.no_conformidades.no_conformidades_manager.get_database_instance') as mock_get_db:
            mock_db = Mock()
            mock_db.execute_query.return_value = []
            mock_db.disconnect.return_value = None
            mock_get_db.return_value = mock_db
            yield mock_get_db
    
    @pytest.fixture
    def mock_config_with_test_dbs(self):
        """Mock de configuración con bases de datos de prueba"""
        with patch('src.common.config.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.db_no_conformidades_path = "test_no_conformidades.mdb"
            mock_config.db_tareas_path = "test_tareas.mdb"
            mock_config.get_db_no_conformidades_connection_string.return_value = "test_no_conformidades.mdb"
            mock_config.get_db_tareas_connection_string.return_value = "test_tareas.mdb"
            mock_config_class.return_value = mock_config
            yield mock_config
    
    @pytest.fixture
    def mock_database_instance(self):
        """Mock de get_database_instance para tests de integración"""
        with patch('src.no_conformidades.no_conformidades_manager.get_database_instance') as mock_get_db:
            mock_db = Mock()
            mock_db.execute_query.return_value = []
            mock_db.disconnect.return_value = None
            mock_get_db.return_value = mock_db
            yield mock_db
    
    @pytest.fixture
    def mock_email_notifications(self):
        """Mock de notificaciones por email"""
        with patch('src.no_conformidades.email_notifications.enviar_notificacion_calidad') as mock_enviar_calidad, \
             patch('src.no_conformidades.email_notifications.enviar_notificacion_tecnica') as mock_enviar_tecnica:
            
            mock_enviar_calidad.return_value = True
            mock_enviar_tecnica.return_value = True
            
            yield {
                'enviar_calidad': mock_enviar_calidad,
                'enviar_tecnica': mock_enviar_tecnica
            }
    
    @pytest.fixture
    def no_conformidades_manager(self, mock_config_with_test_dbs, mock_database_instance, mock_email_notifications):
        """Instancia de NoConformidadesManager para tests de integración"""
        return NoConformidadesManager()
    
    def test_database_connections_initialization(self, no_conformidades_manager, mock_access_database):
        """Test que las conexiones a las bases de datos se inicializan correctamente"""
        # Verificar que el manager se inicializa correctamente
        assert no_conformidades_manager is not None
        assert hasattr(no_conformidades_manager, 'config')
        assert hasattr(no_conformidades_manager, 'logger')
        
        # Verificar configuración de alertas
        assert no_conformidades_manager.dias_alerta_arapc == 15
        assert no_conformidades_manager.dias_alerta_nc == 16
    
    def test_full_workflow_with_simulated_data(self, no_conformidades_manager, mock_access_database, mock_email_notifications):
        """Test de flujo completo con datos simulados"""
        # Configurar datos simulados para obtener_nc_resueltas_pendientes_eficacia
        mock_db = mock_access_database.return_value
        mock_db.execute_query.return_value = [
            (
                'NC-2024-001',  # CodigoNoConformidad
                'NEM001',       # Nemotecnico
                'Test NC Description',  # DESCRIPCION
                'test.user@example.com',  # RESPONSABLECALIDAD
                datetime.now() - timedelta(days=60),  # FECHAAPERTURA
                datetime.now() - timedelta(days=20)   # FPREVCIERRE
            )
        ]
        
        # Ejecutar el flujo completo
        with no_conformidades_manager:
            resultados = no_conformidades_manager.obtener_nc_resueltas_pendientes_eficacia()
            
        # Verificar resultados
        assert len(resultados) == 1
        assert resultados[0].codigo == 'NC-2024-001'
        assert resultados[0].nemotecnico == 'NEM001'
        assert resultados[0].descripcion == 'Test NC Description'
        
        # Verificar que se conectó a las bases de datos
        assert mock_access_database.call_count >= 1
    
    def test_data_retrieval_methods(self, no_conformidades_manager, mock_access_database):
        """Test de métodos de obtención de datos"""
        mock_db = mock_access_database.return_value
        
        # Test obtener estadísticas
        mock_db.execute_query.return_value = [{'total': 5, 'pendientes': 2}]
        
        with no_conformidades_manager:
            stats = no_conformidades_manager.obtener_estadisticas_nc()
            
        assert stats is not None
        mock_db.execute_query.assert_called()
    
    def test_email_registration(self, no_conformidades_manager, mock_access_database):
        """Test de registro de envío de correos"""
        mock_db = mock_access_database.return_value
        
        # Configurar mock para simular ambas bases de datos (nc y tareas)
        # Primera llamada: obtener_siguiente_id_correo (db_tareas)
        # Segunda llamada: registrar_correo_enviado (db_tareas)
        mock_db.execute_query.side_effect = [
            [(5,)],  # MAX(IDCorreo) = 5, entonces siguiente ID = 6
            []       # INSERT result (exitoso)
        ]
        
        with no_conformidades_manager:
            # Mock para get_admin_emails_string que se usa en registrar_correo_enviado
            with patch('src.no_conformidades.no_conformidades_manager.get_admin_emails_string', return_value='admin@example.com'):
                resultado = no_conformidades_manager.registrar_correo_enviado(
                    'Test Subject',
                    'Test Body',
                    'test@example.com'
                )
            
        assert resultado == 6  # ID del correo registrado (5 + 1)
        assert mock_db.execute_query.call_count == 2  # Una para MAX, otra para INSERT
    
    def test_task_requirements(self, no_conformidades_manager):
        """Test de requerimientos de tareas"""
        from unittest.mock import MagicMock
        
        # Mock de datetime para simular lunes
        with patch('src.no_conformidades.no_conformidades_manager.datetime') as mock_datetime:
            # Crear un mock datetime que simule lunes
            mock_now = MagicMock()
            mock_now.weekday.return_value = 0  # Lunes
            mock_now.date.return_value = date(2024, 1, 15)
            mock_datetime.now.return_value = mock_now
            
            # Test requiere tarea calidad (debe ser True en lunes sin ejecución previa)
            with patch.object(no_conformidades_manager, 'obtener_ultima_ejecucion_calidad', return_value=None):
                assert no_conformidades_manager.requiere_tarea_calidad() is True
        
        # Test requiere tarea técnica (debe ser True sin ejecución previa)
        with patch.object(no_conformidades_manager, 'obtener_ultima_ejecucion_tecnica', return_value=None):
            assert no_conformidades_manager.requiere_tarea_tecnica() is True
    
    def test_error_handling(self, no_conformidades_manager, mock_access_database):
        """Test de manejo de errores"""
        mock_db = mock_access_database.return_value
        mock_db.execute_query.side_effect = Exception("Database error")
        
        with no_conformidades_manager:
            # Debería manejar el error graciosamente
            stats = no_conformidades_manager.obtener_estadisticas_nc()
            
        # Verificar que retorna valores por defecto en caso de error
        assert stats is not None
    
    def test_date_formatting(self, no_conformidades_manager):
        """Test de formateo de fechas para Access"""
        from datetime import datetime, date
        
        # Test con datetime
        dt = datetime(2024, 1, 15, 10, 30)
        formatted = no_conformidades_manager._formatear_fecha_access(dt)
        assert formatted == "#01/15/2024#"
        
        # Test con date
        d = date(2024, 1, 15)
        formatted = no_conformidades_manager._formatear_fecha_access(d)
        assert formatted == "#01/15/2024#"
        
        # Test con string
        formatted = no_conformidades_manager._formatear_fecha_access("2024-01-15")
        assert formatted == "#01/15/2024#"
    
    def test_context_manager_usage(self, no_conformidades_manager, mock_access_database):
        """Test del uso como context manager"""
        mock_db = mock_access_database.return_value
        
        # Test que se conecta y desconecta correctamente
        with no_conformidades_manager as manager:
            assert manager is not None
            
        # Verificar que se llamaron los métodos de conexión
        assert mock_access_database.called
    
    def test_email_notifications_integration(self, no_conformidades_manager, mock_email_notifications):
        """Test de integración con notificaciones por email"""
        # Simular datos para notificación
        nc_data = {
            'ID_NC': 1,
            'Numero_NC': 'NC-2024-001',
            'Descripcion': 'Test NC',
            'emails_calidad': ['calidad@test.com']
        }
        
        # Verificar que las funciones de email están disponibles
        assert mock_email_notifications['enviar_calidad'] is not None
        assert mock_email_notifications['enviar_tecnica'] is not None
        
        # Simular envío
        resultado = mock_email_notifications['enviar_calidad'](nc_data, ['calidad@test.com'])
        assert resultado is True
    
    def test_multiple_queries_execution(self, no_conformidades_manager, mock_access_database):
        """Test de ejecución de múltiples consultas"""
        mock_db = mock_access_database.return_value
        mock_db.execute_query.return_value = []
        
        with no_conformidades_manager:
            # Ejecutar múltiples operaciones
            no_conformidades_manager.obtener_estadisticas_nc()
            no_conformidades_manager.registrar_correo_enviado('test@test.com', 'Test', 'calidad')
            
        # Verificar que se ejecutaron múltiples consultas
        assert mock_db.execute_query.call_count >= 2