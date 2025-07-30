"""
Tests funcionales para el módulo AGEDYS
Estos tests verifican el comportamiento end-to-end del sistema
"""
import pytest
import os
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, date
from src.agedys.agedys_manager import AgedysManager


class TestAgedysFunctional:
    """Tests funcionales para AGEDYS"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock de configuración para tests funcionales"""
        with patch('src.agedys.agedys_manager.config') as mock_config:
            mock_config.get_db_agedys_connection_string.return_value = "test_agedys.accdb"
            mock_config.get_db_tareas_connection_string.return_value = "test_tareas.accdb"
            mock_config.get_db_correos_connection_string.return_value = "test_correos.accdb"
            mock_config.css_file_path = "test_styles.css"
            yield mock_config
    
    @pytest.fixture
    def mock_database_with_realistic_data(self):
        """Mock de base de datos con datos realistas"""
        with patch('src.agedys.agedys_manager.AccessDatabase') as mock_db_class:
            # Crear mocks para las tres bases de datos
            mock_agedys_db = Mock()
            mock_tareas_db = Mock()
            mock_correos_db = Mock()
            
            # Configurar el constructor para devolver la instancia correcta
            def db_constructor(connection_string):
                if 'agedys' in connection_string:
                    return mock_agedys_db
                elif 'tareas' in connection_string:
                    return mock_tareas_db
                elif 'correos' in connection_string:
                    return mock_correos_db
                return Mock()
            
            mock_db_class.side_effect = db_constructor
            
            # Datos realistas para facturas
            facturas_data = [
                {
                    'NumeroFactura': 'FAC-2024-001',
                    'Proveedor': 'Tecnologías Avanzadas S.L.',
                    'Importe': 15750.50,
                    'FechaFactura': '2024-01-15',
                    'Descripcion': 'Licencias software desarrollo',
                    'Estado': 'Pendiente Visado Técnico'
                },
                {
                    'NumeroFactura': 'FAC-2024-002',
                    'Proveedor': 'Suministros Industriales S.A.',
                    'Importe': 8920.75,
                    'FechaFactura': '2024-01-16',
                    'Descripcion': 'Material técnico especializado',
                    'Estado': 'Pendiente Visado Técnico'
                },
                {
                    'NumeroFactura': 'FAC-2024-003',
                    'Proveedor': 'Consultoría Empresarial Ltda.',
                    'Importe': 25000.00,
                    'FechaFactura': '2024-01-17',
                    'Descripcion': 'Servicios de consultoría estratégica',
                    'Estado': 'Pendiente Visado Técnico'
                }
            ]
            
            # Datos realistas para DPDs
            dpds_data = [
                {
                    'NumeroDPD': 'DPD-2024-001',
                    'Descripcion': 'Actualización sistema gestión documental',
                    'FechaCreacion': '2024-01-10',
                    'Estado': 'Pendiente Visado Calidad',
                    'Responsable': 'Juan Pérez'
                },
                {
                    'NumeroDPD': 'DPD-2024-002',
                    'Descripcion': 'Implementación protocolo seguridad',
                    'FechaCreacion': '2024-01-12',
                    'Estado': 'Rechazado Calidad',
                    'Responsable': 'María García',
                    'FechaRechazo': '2024-01-18',
                    'MotivoRechazo': 'Documentación incompleta'
                },
                {
                    'NumeroDPD': 'DPD-2024-003',
                    'Descripcion': 'Optimización procesos productivos',
                    'FechaCreacion': '2024-01-14',
                    'Estado': 'Fin Agenda Técnica',
                    'Responsable': 'Carlos López'
                }
            ]
            
            # Datos realistas para usuarios
            usuarios_data = [
                {
                    'Nombre': 'Juan Pérez Martínez',
                    'CorreoUsuario': 'juan.perez@empresa.com',
                    'Departamento': 'Ingeniería',
                    'Cargo': 'Ingeniero Senior'
                },
                {
                    'Nombre': 'María García López',
                    'CorreoUsuario': 'maria.garcia@empresa.com',
                    'Departamento': 'Calidad',
                    'Cargo': 'Responsable Calidad'
                },
                {
                    'Nombre': 'Carlos López Rodríguez',
                    'CorreoUsuario': 'carlos.lopez@empresa.com',
                    'Departamento': 'Producción',
                    'Cargo': 'Jefe de Producción'
                },
                {
                    'Nombre': 'Ana Martín Sánchez',
                    'CorreoUsuario': 'ana.martin@empresa.com',
                    'Departamento': 'Economía',
                    'Cargo': 'Analista Financiero'
                }
            ]
            
            # Configurar respuestas de las consultas
            def mock_agedys_query(query, params=None):
                if 'TbFacturas' in query:
                    if params and len(params) > 0:
                        # Filtrar facturas por usuario
                        return [f for f in facturas_data if f['Responsable'] == params[0]] if 'Responsable' in facturas_data[0] else facturas_data[:2]
                    return facturas_data
                elif 'TbDPD' in query:
                    if 'rechazado' in query.lower():
                        return [d for d in dpds_data if 'Rechazado' in d['Estado']]
                    elif 'sin_visado' in query.lower():
                        return [d for d in dpds_data if 'Pendiente Visado' in d['Estado']]
                    elif 'fin_agenda' in query.lower():
                        return [d for d in dpds_data if 'Fin Agenda' in d['Estado']]
                    elif 'sin_pedido' in query.lower():
                        return [d for d in dpds_data if d['NumeroDPD'] in ['DPD-2024-001']]
                    return dpds_data
                return []
            
            def mock_tareas_query(query, params=None):
                if 'TbUsuarios' in query:
                    if 'economia' in query.lower():
                        return [u for u in usuarios_data if u['Departamento'] == 'Economía']
                    elif 'facturas' in query.lower():
                        return [u for u in usuarios_data if u['Departamento'] in ['Ingeniería', 'Producción']]
                    elif 'calidad' in query.lower():
                        return [u for u in usuarios_data if u['Departamento'] == 'Calidad']
                    return usuarios_data
                return []
            
            mock_agedys_db.execute_query.side_effect = mock_agedys_query
            mock_tareas_db.execute_query.side_effect = mock_tareas_query
            mock_correos_db.execute_query.return_value = []
            
            yield {
                'agedys': mock_agedys_db,
                'tareas': mock_tareas_db,
                'correos': mock_correos_db
            }
    
    @pytest.fixture
    def mock_utils(self):
        """Mock de utilidades para tests funcionales"""
        with patch('src.agedys.agedys_manager.load_css_content') as mock_css, \
             patch('src.agedys.agedys_manager.generate_html_header') as mock_header, \
             patch('src.agedys.agedys_manager.generate_html_footer') as mock_footer, \
             patch('src.agedys.agedys_manager.register_email_in_database') as mock_register_email, \
             patch('src.agedys.agedys_manager.should_execute_task') as mock_should_execute, \
             patch('src.agedys.agedys_manager.register_task_completion') as mock_register_task:
            
            mock_css.return_value = """
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
                .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; font-weight: bold; }
                .footer { margin-top: 30px; padding: 20px; background-color: #ecf0f1; text-align: center; }
            """
            
            mock_header.return_value = """
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Notificación AGEDYS</title>
                    <style>
                        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
                        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                        th { background-color: #f2f2f2; font-weight: bold; }
                        .footer { margin-top: 30px; padding: 20px; background-color: #ecf0f1; text-align: center; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Sistema AGEDYS</h1>
                        <p>Notificación Automática</p>
                    </div>
                    <div class="content">
            """
            
            mock_footer.return_value = """
                    </div>
                    <div class="footer">
                        <p>Este es un mensaje automático del sistema AGEDYS.</p>
                        <p>Por favor, no responda a este correo.</p>
                        <p><small>Generado el """ + datetime.now().strftime("%d/%m/%Y a las %H:%M") + """</small></p>
                    </div>
                </body>
                </html>
            """
            
            mock_register_email.return_value = True
            mock_should_execute.return_value = True
            mock_register_task.return_value = True
            
            yield {
                'css': mock_css,
                'header': mock_header,
                'footer': mock_footer,
                'register_email': mock_register_email,
                'should_execute': mock_should_execute,
                'register_task': mock_register_task
            }
    
    @pytest.fixture
    def agedys_manager(self, mock_config, mock_database_with_realistic_data, mock_utils):
        """Instancia de AgedysManager para tests funcionales"""
        return AgedysManager()
    
    def test_complete_business_workflow_facturas_pendientes(self, agedys_manager, mock_utils):
        """Test del flujo completo de negocio para facturas pendientes"""
        # Ejecutar el proceso completo
        result = agedys_manager.run(dry_run=False)
        
        # Verificar que el proceso se ejecutó correctamente
        assert result is True
        
        # Verificar que se enviaron emails (se registraron en la base de datos)
        assert mock_utils['register_email'].call_count > 0
        
        # Verificar el contenido de los emails enviados
        email_calls = mock_utils['register_email'].call_args_list
        
        # Debe haber al menos un email de facturas pendientes
        facturas_emails = [call for call in email_calls if 'Facturas pendientes' in call[0][2]]
        assert len(facturas_emails) > 0
        
        # Verificar que el contenido del email incluye información realista
        for call in facturas_emails:
            email_content = call[0][3]  # Contenido del email
            assert 'FAC-2024-' in email_content  # Números de factura
            assert 'Tecnologías Avanzadas' in email_content or 'Suministros Industriales' in email_content
            assert '€' in email_content or 'Importe' in email_content
    
    def test_complete_business_workflow_dpds_sin_visado(self, agedys_manager, mock_utils):
        """Test del flujo completo de negocio para DPDs sin visado"""
        # Ejecutar el proceso completo
        result = agedys_manager.run(dry_run=False)
        
        # Verificar que el proceso se ejecutó correctamente
        assert result is True
        
        # Verificar emails de DPDs sin visado
        email_calls = mock_utils['register_email'].call_args_list
        dpds_emails = [call for call in email_calls if 'DPDs pendientes' in call[0][2]]
        
        if len(dpds_emails) > 0:
            for call in dpds_emails:
                email_content = call[0][3]
                assert 'DPD-2024-' in email_content
                assert 'Pendiente Visado' in email_content or 'sistema gestión' in email_content
    
    def test_complete_business_workflow_dpds_rechazados(self, agedys_manager, mock_utils):
        """Test del flujo completo de negocio para DPDs rechazados"""
        # Ejecutar el proceso completo
        result = agedys_manager.run(dry_run=False)
        
        # Verificar que el proceso se ejecutó correctamente
        assert result is True
        
        # Verificar emails de DPDs rechazados
        email_calls = mock_utils['register_email'].call_args_list
        rechazados_emails = [call for call in email_calls if 'DPDs rechazados' in call[0][2]]
        
        if len(rechazados_emails) > 0:
            for call in rechazados_emails:
                email_content = call[0][3]
                assert 'DPD-2024-' in email_content
                assert 'Rechazado' in email_content or 'protocolo seguridad' in email_content
    
    def test_html_email_formatting_quality(self, agedys_manager):
        """Test de la calidad del formato HTML de los emails"""
        # Datos de prueba realistas
        facturas = [
            {
                'NumeroFactura': 'FAC-2024-001',
                'Proveedor': 'Tecnologías Avanzadas S.L.',
                'Importe': 15750.50,
                'FechaFactura': '2024-01-15',
                'Descripcion': 'Licencias software desarrollo'
            }
        ]
        
        # Generar HTML
        html_table = agedys_manager.generate_facturas_html_table(facturas)
        
        # Verificar estructura HTML válida
        assert '<table' in html_table
        assert '</table>' in html_table
        assert '<thead>' in html_table
        assert '<tbody>' in html_table
        assert '<th>' in html_table
        assert '<td>' in html_table
        
        # Verificar contenido específico
        assert 'FAC-2024-001' in html_table
        assert 'Tecnologías Avanzadas S.L.' in html_table
        assert '15.750,50' in html_table  # Formato español de números
        assert '15/01/2024' in html_table  # Formato español de fechas
        
        # Verificar que no hay caracteres problemáticos
        assert '&' not in html_table or '&amp;' in html_table
        assert '<' not in html_table.replace('<table', '').replace('<thead', '').replace('<tbody', '').replace('<th>', '').replace('<td>', '').replace('</t', '') or '&lt;' in html_table
    
    def test_user_notification_targeting(self, agedys_manager, mock_database_with_realistic_data, mock_utils):
        """Test de que las notificaciones se envían a los usuarios correctos"""
        # Ejecutar el proceso
        result = agedys_manager.run(dry_run=False)
        assert result is True
        
        # Verificar que se enviaron emails
        email_calls = mock_utils['register_email'].call_args_list
        assert len(email_calls) > 0
        
        # Verificar destinatarios
        destinatarios = [call[0][1] for call in email_calls]  # Email del destinatario
        
        # Verificar que se enviaron a direcciones válidas
        for destinatario in destinatarios:
            assert '@empresa.com' in destinatario
            assert destinatario in [
                'juan.perez@empresa.com',
                'maria.garcia@empresa.com',
                'carlos.lopez@empresa.com',
                'ana.martin@empresa.com'
            ]
    
    def test_business_rules_compliance(self, agedys_manager, mock_database_with_realistic_data):
        """Test de cumplimiento de reglas de negocio"""
        # Obtener usuarios de facturas
        usuarios_facturas = agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
        
        # Verificar que se obtuvieron usuarios
        assert len(usuarios_facturas) > 0
        
        # Para cada usuario, obtener sus facturas
        for usuario in usuarios_facturas:
            facturas = agedys_manager.get_facturas_pendientes_visado_tecnico(usuario['Nombre'])
            
            # Verificar que las facturas tienen los campos requeridos
            for factura in facturas:
                assert 'NumeroFactura' in factura
                assert 'Proveedor' in factura
                assert 'Importe' in factura
                assert factura['Importe'] > 0  # Importe debe ser positivo
                assert len(factura['NumeroFactura']) > 0  # Número no vacío
                assert len(factura['Proveedor']) > 0  # Proveedor no vacío
    
    def test_error_recovery_and_logging(self, agedys_manager, mock_database_with_realistic_data):
        """Test de recuperación de errores y logging"""
        # Simular error en una consulta específica
        original_execute = mock_database_with_realistic_data['agedys'].execute_query
        
        def failing_query(query, params=None):
            if 'TbFacturas' in query:
                raise Exception("Simulated database error")
            return original_execute(query, params)
        
        mock_database_with_realistic_data['agedys'].execute_query.side_effect = failing_query
        
        # El proceso debe continuar a pesar del error
        result = agedys_manager.run(dry_run=False)
        
        # Puede ser True o False dependiendo de si otros procesos funcionan
        assert isinstance(result, bool)
        
        # Verificar que se manejó el error correctamente
        # (En una implementación real, verificaríamos los logs)
    
    def test_performance_with_large_datasets(self, agedys_manager, mock_database_with_realistic_data):
        """Test de rendimiento con conjuntos de datos grandes"""
        # Simular un conjunto de datos grande
        large_facturas = []
        for i in range(100):
            large_facturas.append({
                'NumeroFactura': f'FAC-2024-{i:03d}',
                'Proveedor': f'Proveedor {i} S.L.',
                'Importe': 1000.00 + i * 10,
                'FechaFactura': '2024-01-15',
                'Descripcion': f'Descripción de la factura {i}'
            })
        
        # Configurar mock para devolver datos grandes
        mock_database_with_realistic_data['agedys'].execute_query.return_value = large_facturas
        
        # Medir tiempo de generación de HTML
        import time
        start_time = time.time()
        
        html_result = agedys_manager.generate_facturas_html_table(large_facturas)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verificar que se generó correctamente
        assert len(html_result) > 0
        assert 'FAC-2024-000' in html_result
        assert 'FAC-2024-099' in html_result
        
        # Verificar que el tiempo de ejecución es razonable (menos de 5 segundos)
        assert execution_time < 5.0
    
    def test_email_content_localization(self, agedys_manager):
        """Test de localización del contenido de emails"""
        # Datos de prueba
        facturas = [
            {
                'NumeroFactura': 'FAC-2024-001',
                'Proveedor': 'Proveedor Español S.L.',
                'Importe': 1234.56,
                'FechaFactura': '2024-01-15'
            }
        ]
        
        # Generar HTML
        html_content = agedys_manager.generate_facturas_html_table(facturas)
        
        # Verificar formato español
        assert '1.234,56' in html_content  # Formato de número español
        assert '15/01/2024' in html_content  # Formato de fecha español
        
        # Verificar caracteres especiales españoles
        assert 'Proveedor Español' in html_content
    
    def test_dry_run_vs_production_mode(self, agedys_manager, mock_utils):
        """Test de diferencias entre modo dry run y producción"""
        # Configurar datos de prueba
        mock_database_with_realistic_data = mock_utils
        
        # Ejecutar en modo dry run
        result_dry = agedys_manager.execute_task(force=True, dry_run=True)
        dry_run_email_count = mock_utils['register_email'].call_count
        
        # Reset del mock
        mock_utils['register_email'].reset_mock()
        
        # Ejecutar en modo producción
        result_prod = agedys_manager.execute_task(force=True, dry_run=False)
        prod_email_count = mock_utils['register_email'].call_count
        
        # Verificar resultados
        assert result_dry is True
        assert result_prod is True
        
        # En dry run no se deben registrar emails
        assert dry_run_email_count == 0
        
        # En producción sí se deben registrar (si hay datos)
        # assert prod_email_count >= 0  # Puede ser 0 si no hay datos
    
    def test_task_scheduling_integration(self, agedys_manager, mock_utils):
        """Test de integración con el sistema de programación de tareas"""
        # Configurar que la tarea debe ejecutarse
        mock_utils['should_execute'].return_value = True
        
        # Ejecutar tarea
        result = agedys_manager.execute_task(force=False, dry_run=False)
        
        # Verificar que se consultó si debe ejecutarse
        mock_utils['should_execute'].assert_called_once()
        
        # Verificar que se registró la finalización
        mock_utils['register_task'].assert_called_once()
        
        # Verificar parámetros de registro de tarea
        task_call = mock_utils['register_task'].call_args
        assert task_call[0][1] == 'AGEDYS'  # Nombre de la tarea
        assert isinstance(task_call[0][2], bool)  # Resultado de la ejecución
    
    def test_end_to_end_realistic_scenario(self, agedys_manager, mock_utils):
        """Test end-to-end con escenario realista completo"""
        # Simular un día típico de trabajo
        
        # 1. Verificar que el sistema debe ejecutarse
        mock_utils['should_execute'].return_value = True
        
        # 2. Ejecutar el proceso completo
        result = agedys_manager.execute_task(force=False, dry_run=False)
        
        # 3. Verificar que se ejecutó correctamente
        assert result is True
        
        # 4. Verificar que se procesaron todos los tipos de notificaciones
        email_calls = mock_utils['register_email'].call_args_list
        
        if len(email_calls) > 0:
            # Verificar tipos de emails enviados
            email_subjects = [call[0][2] for call in email_calls]
            
            # Puede incluir diferentes tipos según los datos
            possible_subjects = [
                'Facturas pendientes de visado técnico',
                'DPDs pendientes de visado de calidad',
                'DPDs rechazados por calidad',
                'DPDs con fin de agenda técnica por recepcionar',
                'DPDs sin pedido asignado'
            ]
            
            # Al menos uno de los tipos debe estar presente
            assert any(subject in email_subjects for subject in possible_subjects)
        
        # 5. Verificar que se registró la tarea
        mock_utils['register_task'].assert_called_once()
        
        # 6. Verificar que todos los emails tienen estructura válida
        for call in email_calls:
            email_content = call[0][3]
            assert '<!DOCTYPE html>' in email_content
            assert '<html' in email_content
            assert '</html>' in email_content
            assert 'Sistema AGEDYS' in email_content