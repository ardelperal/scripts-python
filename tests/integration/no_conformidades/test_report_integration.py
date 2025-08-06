"""
Tests de integración para el módulo de reportes de No Conformidades.
Prueba la integración real entre report_registrar y las bases de datos locales.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from src.no_conformidades.report_registrar import (
    enviar_notificacion_calidad,
    enviar_notificacion_tecnica,
    obtener_tecnicos_con_nc_activas,
    obtener_arapc_por_tecnico_y_rango,
    obtener_responsables_calidad_por_arapc,
    registrar_avisos_arapc
)
from src.no_conformidades.no_conformidades_manager import NoConformidadesManager
from src.common.html_report_generator import HTMLReportGenerator
from src.common.email_notification_manager import EmailNotificationManager


class TestReportIntegration:
    """Tests de integración para el sistema de reportes"""
    
    @pytest.fixture
    def manager(self):
        """Fixture que crea una instancia del manager con bases de datos locales"""
        # Forzar uso de bases de datos locales
        with patch.dict(os.environ, {
            'DB_NO_CONFORMIDADES': 'no_conformidades',
            'DB_TAREAS': 'tareas', 
            'DB_CORREOS': 'correos'
        }):
            return NoConformidadesManager()
    
    @pytest.fixture
    def mock_html_generator(self):
        """Mock del generador de HTML"""
        with patch.object(HTMLReportGenerator, '__init__', return_value=None):
            generator = HTMLReportGenerator()
            generator.generar_tabla_nc_pendientes_eficacia = MagicMock(return_value="<table>NC Eficacia</table>")
            generator.generar_tabla_arapc_proximas_caducar = MagicMock(return_value="<table>ARAPC Próximas</table>")
            generator.generar_tabla_nc_sin_acciones = MagicMock(return_value="<table>NC Sin Acciones</table>")
            generator.generar_tabla_arapc_replanificar = MagicMock(return_value="<table>ARAPC Replanificar</table>")
            generator.generar_tabla_arapc_tecnico = MagicMock(return_value="<table>ARAPC Técnico</table>")
            yield generator
    
    @pytest.fixture
    def mock_email_manager(self):
        """Mock del manager de email"""
        with patch.object(EmailNotificationManager, '__init__', return_value=None):
            email_manager = EmailNotificationManager()
            email_manager.registrar_correo = MagicMock(return_value=12345)
            yield email_manager
    
    def test_obtener_tecnicos_con_nc_activas_integracion(self, manager):
        """Test de integración para obtener técnicos con NC activas"""
        with patch.object(manager, 'ejecutar_consulta') as mock_consulta:
            # Simular datos de técnicos
            mock_consulta.return_value = [
                {'RESPONSABLETELEFONICA': 'tecnico1'},
                {'RESPONSABLETELEFONICA': 'tecnico2'}
            ]
            
            tecnicos = obtener_tecnicos_con_nc_activas(manager)
            
            assert len(tecnicos) == 2
            assert 'tecnico1' in tecnicos
            assert 'tecnico2' in tecnicos
            
            # Verificar que se ejecutó la consulta correcta
            mock_consulta.assert_called_once()
            consulta_ejecutada = mock_consulta.call_args[0][0]
            assert 'RESPONSABLETELEFONICA' in consulta_ejecutada
            assert 'FechaFinReal IS NULL' in consulta_ejecutada
    
    def test_obtener_arapc_por_tecnico_y_rango_integracion(self, manager):
        """Test de integración para obtener ARAPC por técnico y rango"""
        with patch.object(manager, 'ejecutar_consulta') as mock_consulta:
            # Simular datos de ARAPC
            mock_consulta.return_value = [
                {
                    'CodigoNoConformidad': 'NC001',
                    'IDAccionRealizada': 1,
                    'AccionCorrectiva': 'Acción 1',
                    'AccionRealizada': 'Tarea 1',
                    'FechaFinPrevista': datetime.now() + timedelta(days=10),
                    'DiasParaCaducar': 10
                }
            ]
            
            arapc_data = obtener_arapc_por_tecnico_y_rango(manager, 'tecnico1', 8, 15, 'IDCorreo15')
            
            assert len(arapc_data) == 1
            assert arapc_data[0]['CodigoNoConformidad'] == 'NC001'
            
            # Verificar que se ejecutó la consulta con los parámetros correctos
            mock_consulta.assert_called_once()
            consulta_ejecutada = mock_consulta.call_args[0][0]
            assert 'tecnico1' in consulta_ejecutada
            assert 'BETWEEN 8 AND 15' in consulta_ejecutada
            assert 'IDCorreo15 IS NULL' in consulta_ejecutada
    
    def test_obtener_responsables_calidad_por_arapc_integracion(self, manager):
        """Test de integración para obtener responsables de calidad"""
        arapc_data = [
            {'CorreoCalidad': 'calidad1@empresa.com'},
            {'CorreoCalidad': 'calidad2@empresa.com'},
            {'CorreoCalidad': 'calidad1@empresa.com'}  # Duplicado
        ]
        
        responsables = obtener_responsables_calidad_por_arapc(arapc_data)
        
        assert len(responsables) == 2
        assert 'calidad1@empresa.com' in responsables
        assert 'calidad2@empresa.com' in responsables
    
    def test_registrar_avisos_arapc_integracion(self, manager):
        """Test de integración para registrar avisos ARAPC"""
        with patch.object(manager, 'ejecutar_insercion') as mock_insercion:
            arapc_data = [
                {'IDAccionRealizada': 1},
                {'IDAccionRealizada': 2}
            ]
            
            registrar_avisos_arapc(manager, 12345, arapc_data, 'IDCorreo15')
            
            # Verificar que se ejecutaron las inserciones
            assert mock_insercion.call_count == 2
            
            # Verificar el contenido de las inserciones
            for call in mock_insercion.call_args_list:
                consulta = call[0][0]
                assert 'INSERT INTO TbNCARAvisos' in consulta
                assert 'IDCorreo15' in consulta
                assert '12345' in consulta
    
    @patch('src.no_conformidades.report_registrar.HTMLReportGenerator')
    @patch('src.no_conformidades.report_registrar.EmailNotificationManager')
    def test_enviar_notificacion_calidad_integracion(self, mock_email_class, mock_html_class, manager):
        """Test de integración completo para envío de notificación a calidad"""
        # Configurar mocks
        mock_html_instance = MagicMock()
        mock_html_class.return_value = mock_html_instance
        mock_html_instance.generar_tabla_nc_pendientes_eficacia.return_value = "<table>Eficacia</table>"
        mock_html_instance.generar_tabla_arapc_proximas_caducar.return_value = "<table>Próximas</table>"
        mock_html_instance.generar_tabla_nc_sin_acciones.return_value = "<table>Sin Acciones</table>"
        mock_html_instance.generar_tabla_arapc_replanificar.return_value = "<table>Replanificar</table>"
        
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        mock_email_instance.registrar_correo.return_value = 12345
        
        # Mock de las consultas del manager
        with patch.object(manager, 'ejecutar_consulta') as mock_consulta:
            mock_consulta.side_effect = [
                [{'CodigoNoConformidad': 'NC001'}],  # NC pendientes eficacia
                [{'CodigoNoConformidad': 'NC002'}],  # ARAPC próximas
                [{'CodigoNoConformidad': 'NC003'}],  # NC sin acciones
                [{'CodigoNoConformidad': 'NC004'}]   # ARAPC replanificar
            ]
            
            with patch.object(manager, 'obtener_correos_calidad', return_value=['calidad@empresa.com']):
                resultado = enviar_notificacion_calidad(manager)
                
                assert resultado is True
                
                # Verificar que se ejecutaron las 4 consultas principales
                assert mock_consulta.call_count == 4
                
                # Verificar que se generaron las tablas HTML
                mock_html_instance.generar_tabla_nc_pendientes_eficacia.assert_called_once()
                mock_html_instance.generar_tabla_arapc_proximas_caducar.assert_called_once()
                mock_html_instance.generar_tabla_nc_sin_acciones.assert_called_once()
                mock_html_instance.generar_tabla_arapc_replanificar.assert_called_once()
                
                # Verificar que se registró el correo
                mock_email_instance.registrar_correo.assert_called_once()
    
    @patch('src.no_conformidades.report_registrar.HTMLReportGenerator')
    @patch('src.no_conformidades.report_registrar.EmailNotificationManager')
    def test_enviar_notificacion_tecnica_integracion(self, mock_email_class, mock_html_class, manager):
        """Test de integración completo para envío de notificación técnica"""
        # Configurar mocks
        mock_html_instance = MagicMock()
        mock_html_class.return_value = mock_html_instance
        mock_html_instance.generar_tabla_arapc_tecnico.return_value = "<table>ARAPC Técnico</table>"
        
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        mock_email_instance.registrar_correo.return_value = 12345
        
        # Mock de las consultas del manager
        with patch.object(manager, 'ejecutar_consulta') as mock_consulta:
            # Primera consulta: obtener técnicos
            # Siguientes consultas: ARAPC por rango para cada técnico
            mock_consulta.side_effect = [
                [{'RESPONSABLETELEFONICA': 'tecnico1'}],  # Técnicos con NC activas
                [{'IDAccionRealizada': 1, 'CorreoCalidad': 'calidad@empresa.com'}],  # ARAPC 8-15 días
                [],  # ARAPC 1-7 días (vacío)
                []   # ARAPC vencidas (vacío)
            ]
            
            with patch.object(manager, 'ejecutar_insercion') as mock_insercion:
                resultado = enviar_notificacion_tecnica(manager)
                
                assert resultado is True
                
                # Verificar que se ejecutaron las consultas
                assert mock_consulta.call_count == 4
                
                # Verificar que se generó la tabla HTML
                mock_html_instance.generar_tabla_arapc_tecnico.assert_called_once()
                
                # Verificar que se registró el correo
                mock_email_instance.registrar_correo.assert_called_once()
                
                # Verificar que se registraron los avisos
                mock_insercion.assert_called_once()
    
    def test_enviar_notificacion_calidad_sin_datos(self, manager):
        """Test para verificar comportamiento cuando no hay datos para calidad"""
        with patch.object(manager, 'ejecutar_consulta') as mock_consulta:
            # Todas las consultas devuelven listas vacías
            mock_consulta.return_value = []
            
            resultado = enviar_notificacion_calidad(manager)
            
            assert resultado is False
            
            # Verificar que se ejecutaron las 4 consultas
            assert mock_consulta.call_count == 4
    
    def test_enviar_notificacion_tecnica_sin_tecnicos(self, manager):
        """Test para verificar comportamiento cuando no hay técnicos con NC activas"""
        with patch.object(manager, 'ejecutar_consulta') as mock_consulta:
            # Primera consulta devuelve lista vacía (no hay técnicos)
            mock_consulta.return_value = []
            
            resultado = enviar_notificacion_tecnica(manager)
            
            assert resultado is False
            
            # Solo se ejecutó la consulta de técnicos
            assert mock_consulta.call_count == 1
    
    def test_manejo_errores_integracion(self, manager):
        """Test para verificar el manejo de errores en la integración"""
        with patch.object(manager, 'ejecutar_consulta') as mock_consulta:
            # Simular error en la consulta
            mock_consulta.side_effect = Exception("Error de base de datos")
            
            resultado = enviar_notificacion_calidad(manager)
            
            assert resultado is False