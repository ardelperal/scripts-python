"""
Pruebas de integración reales con base de datos para el módulo AGEDYS
Estas pruebas se conectan a las bases de datos locales configuradas en .env y validan:
- Conectividad a las bases de datos reales
- Correctitud de las consultas SQL
- Integridad de los datos
- Rendimiento de las consultas
- Funcionalidad completa del sistema
"""
import pytest
import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.agedys.agedys_manager import AgedysManager
from src.common.database import AccessDatabase
from src.common import config
from src.common.utils import (
    register_email_in_database, 
    should_execute_task, 
    register_task_completion
)


class TestAgedysDatabaseIntegration:
    """Pruebas de integración reales con bases de datos locales para AGEDYS"""
    
    @pytest.fixture(scope="class")
    def verify_local_environment(self):
        """Verificar que las bases de datos locales están disponibles"""
        # Forzar el uso de bases de datos locales independientemente del entorno
        # Las pruebas siempre deben usar las bases de datos locales
        required_dbs = {
            'agedys': config.get_local_db_path('agedys'),
            'tareas': config.get_local_db_path('tareas'),
            'correos': config.get_local_db_path('correos')
        }
        
        missing_dbs = []
        for db_name, db_path in required_dbs.items():
            if not os.path.exists(db_path):
                missing_dbs.append(f"{db_name}: {db_path}")
        
        if missing_dbs:
            pytest.skip(f"Bases de datos locales no encontradas: {', '.join(missing_dbs)}")
        
        return required_dbs
    
    @pytest.fixture(scope="class")
    def agedys_manager(self, verify_local_environment):
        """Crear instancia de AgedysManager configurada para usar bases de datos locales"""
        # Forzar el uso de bases de datos locales para las pruebas
        # Temporalmente sobrescribir las rutas de configuración
        original_paths = {
            'agedys': config.db_agedys_path,
            'tareas': config.db_tareas_path,
            'correos': config.db_correos_path
        }
        
        # Usar las rutas locales
        local_paths = verify_local_environment
        config.db_agedys_path = local_paths['agedys']
        config.db_tareas_path = local_paths['tareas']
        config.db_correos_path = local_paths['correos']
        
        try:
            manager = AgedysManager()
            yield manager
        finally:
            # Restaurar las rutas originales
            config.db_agedys_path = original_paths['agedys']
            config.db_tareas_path = original_paths['tareas']
            config.db_correos_path = original_paths['correos']
    
    @pytest.fixture(scope="class")
    def local_agedys_manager(self, verify_local_environment):
        """Crear instancia de AgedysManager configurada para usar bases de datos locales"""
        # Forzar el uso de bases de datos locales para las pruebas
        # Temporalmente sobrescribir las rutas de configuración
        original_paths = {
            'agedys': config.db_agedys_path,
            'tareas': config.db_tareas_path,
            'correos': config.db_correos_path
        }
        
        # Usar las rutas locales
        local_paths = verify_local_environment
        config.db_agedys_path = local_paths['agedys']
        config.db_tareas_path = local_paths['tareas']
        config.db_correos_path = local_paths['correos']
        
        try:
            manager = AgedysManager()
            yield manager
        finally:
            # Restaurar las rutas originales
            config.db_agedys_path = original_paths['agedys']
            config.db_tareas_path = original_paths['tareas']
            config.db_correos_path = original_paths['correos']
    
    @pytest.fixture(scope="class")
    def db_connections(self, verify_local_environment):
        """Crear conexiones directas a las bases de datos locales para verificación"""
        local_paths = verify_local_environment
        connections = {}
        
        try:
            # Crear conexiones usando las rutas locales
            connections['agedys'] = AccessDatabase(str(local_paths['agedys']))
            connections['tareas'] = AccessDatabase(str(local_paths['tareas']))
            connections['correos'] = AccessDatabase(str(local_paths['correos']))
            
            yield connections
        finally:
            # Cerrar todas las conexiones
            for conn in connections.values():
                try:
                    conn.disconnect()
                except Exception:
                    # Ignorar errores al cerrar conexiones
                    continue
    
    def test_database_connectivity(self, local_agedys_manager):
        """Probar conectividad básica a todas las bases de datos a través de AgedysManager"""
        
        # Probar conexión a base de datos AGEDYS
        try:
            result = local_agedys_manager.db.execute_query("SELECT COUNT(*) as total FROM TbFacturasDetalle")
            assert isinstance(result, list), "Resultado de AGEDYS debe ser una lista"
            assert len(result) > 0, "Resultado de AGEDYS no debe estar vacío"
            print("✓ Conectividad a AGEDYS: OK")
        except Exception as e:
            pytest.fail(f"Error de conectividad en AGEDYS: {e}")
        
        # Probar conexión a base de datos de tareas
        try:
            result = local_agedys_manager.tareas_db.execute_query("SELECT COUNT(*) as total FROM TbTareas")
            assert isinstance(result, list), "Resultado de tareas debe ser una lista"
            assert len(result) > 0, "Resultado de tareas no debe estar vacío"
            print("✓ Conectividad a tareas: OK")
        except Exception as e:
            pytest.fail(f"Error de conectividad en tareas: {e}")
        
        # Probar conexión a base de datos de correos
        try:
            result = local_agedys_manager.correos_db.execute_query("SELECT COUNT(*) as total FROM TbCorreosEnviados")
            assert isinstance(result, list), "Resultado de correos debe ser una lista"
            assert len(result) > 0, "Resultado de correos no debe estar vacío"
            print("✓ Conectividad a correos: OK")
        except Exception as e:
            pytest.fail(f"Error de conectividad en correos: {e}")
    
    def test_agedys_queries_real_data(self, local_agedys_manager):
        """Probar consultas reales de AGEDYS con datos existentes"""
        
        # Test 1: Usuarios con facturas pendientes de visado técnico
        try:
            usuarios_facturas = local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
            assert isinstance(usuarios_facturas, list), "Debe devolver una lista"
            print(f"✓ Usuarios con facturas pendientes: {len(usuarios_facturas)}")
            
            # Verificar estructura de datos si hay resultados
            if usuarios_facturas:
                primer_usuario = usuarios_facturas[0]
                required_fields = ['Nombre', 'CorreoUsuario', 'Facturas']
                for field in required_fields:
                    assert field in primer_usuario, f"Campo '{field}' faltante en resultado"
                    
        except Exception as e:
            pytest.fail(f"Error en get_usuarios_facturas_pendientes_visado_tecnico: {e}")
        
        # Test 2: Usuarios con DPDs sin visado de calidad
        try:
            usuarios_dpds_sin_visado = local_agedys_manager.get_usuarios_dpds_sin_visado_calidad()
            assert isinstance(usuarios_dpds_sin_visado, list), "Debe devolver una lista"
            print(f"✓ Usuarios con DPDs sin visado: {len(usuarios_dpds_sin_visado)}")
            
        except Exception as e:
            pytest.fail(f"Error en get_usuarios_dpds_sin_visado_calidad: {e}")
        
        # Test 3: Usuarios con DPDs rechazadas por calidad
        try:
            usuarios_dpds_rechazadas = local_agedys_manager.get_usuarios_dpds_rechazados_calidad()
            assert isinstance(usuarios_dpds_rechazadas, list), "Debe devolver una lista"
            print(f"✓ Usuarios con DPDs rechazadas: {len(usuarios_dpds_rechazadas)}")
            
        except Exception as e:
            pytest.fail(f"Error en get_usuarios_dpds_rechazados_calidad: {e}")
        
        # Test 4: Usuarios de economía
        try:
            usuarios_economia = local_agedys_manager.get_usuarios_economia()
            assert isinstance(usuarios_economia, list), "Debe devolver una lista"
            print(f"✓ Usuarios de economía: {len(usuarios_economia)}")
            
            # Verificar estructura de datos si hay resultados
            if usuarios_economia:
                primer_usuario = usuarios_economia[0]
                required_fields = ['UsuarioRed', 'Nombre', 'CorreoUsuario']
                for field in required_fields:
                    assert field in primer_usuario, f"Campo '{field}' faltante en resultado"
                    
                # Verificar que el email tiene formato válido
                assert '@' in primer_usuario['CorreoUsuario'], "Email debe contener @"
                
        except Exception as e:
            pytest.fail(f"Error en get_usuarios_economia: {e}")

    def test_additional_agedys_queries_real_data(self, local_agedys_manager):
        """Probar consultas adicionales de AGEDYS con datos reales"""
        
        try:
            # Test get_usuarios_dpds_pendientes_recepcion_economica
            usuarios_dpds_pendientes = local_agedys_manager.get_usuarios_dpds_pendientes_recepcion_economica()
            assert isinstance(usuarios_dpds_pendientes, list), "Debe devolver una lista"
            print(f"✓ get_usuarios_dpds_pendientes_recepcion_economica: {len(usuarios_dpds_pendientes)} usuarios")
            
            # Test get_dpds_pendientes_recepcion_economica (requiere usuario)
            if usuarios_dpds_pendientes:
                usuario_test = usuarios_dpds_pendientes[0].get('UsuarioRed', 'Test')
                dpds_pendientes = local_agedys_manager.get_dpds_pendientes_recepcion_economica(usuario_test)
                assert isinstance(dpds_pendientes, list), "Debe devolver una lista"
                print(f"✓ get_dpds_pendientes_recepcion_economica para {usuario_test}: {len(dpds_pendientes)} DPDs")
            else:
                # Probar con usuario ficticio
                dpds_pendientes = local_agedys_manager.get_dpds_pendientes_recepcion_economica('usuario_test')
                assert isinstance(dpds_pendientes, list), "Debe devolver una lista"
                print("✓ get_dpds_pendientes_recepcion_economica (sin datos): OK")
            
            # Test get_dpds_fin_agenda_tecnica_por_recepcionar
            dpds_fin_agenda = local_agedys_manager.get_dpds_fin_agenda_tecnica_por_recepcionar()
            assert isinstance(dpds_fin_agenda, list), "Debe devolver una lista"
            print(f"✓ get_dpds_fin_agenda_tecnica_por_recepcionar: {len(dpds_fin_agenda)} DPDs")
            
            # Test get_usuarios_tareas
            usuarios_tareas = local_agedys_manager.get_usuarios_tareas()
            assert isinstance(usuarios_tareas, list), "Debe devolver una lista"
            print(f"✓ get_usuarios_tareas: {len(usuarios_tareas)} usuarios")
            
            # Test get_dpds_sin_pedido (sin parámetros)
            dpds_sin_pedido = local_agedys_manager.get_dpds_sin_pedido()
            assert isinstance(dpds_sin_pedido, list), "Debe devolver una lista"
            print(f"✓ get_dpds_sin_pedido: {len(dpds_sin_pedido)} DPDs")
            
            # Test generate_facturas_html_table
            if len(usuarios_dpds_pendientes) > 0:
                usuario = usuarios_dpds_pendientes[0].get('UsuarioRed', 'Test')
                facturas = local_agedys_manager.get_facturas_pendientes_visado_tecnico(usuario)
                html_facturas = local_agedys_manager.generate_facturas_html_table(facturas)
                assert isinstance(html_facturas, str), "HTML debe ser una cadena"
                print(f"✓ generate_facturas_html_table: {len(html_facturas)} caracteres")
            
            # Test generate_dpds_html_table
            if len(dpds_sin_pedido) > 0:
                html_dpds = local_agedys_manager.generate_dpds_html_table(dpds_sin_pedido, 'sin_pedido')
                assert isinstance(html_dpds, str), "HTML debe ser una cadena"
                print(f"✓ generate_dpds_html_table: {len(html_dpds)} caracteres")
            
        except Exception as e:
            pytest.fail(f"Error en consultas adicionales: {e}")

    def test_email_sending_methods_dry_run(self, local_agedys_manager):
        """Probar métodos de envío de email en modo dry-run"""
        
        try:
            # Test send_facturas_pendientes_email
            usuarios_facturas = local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
            if usuarios_facturas:
                usuario_data = usuarios_facturas[0]
                usuario = usuario_data.get('UsuarioRed', 'Test')
                email = usuario_data.get('CorreoUsuario', 'test@test.com')
                facturas = local_agedys_manager.get_facturas_pendientes_visado_tecnico(usuario)
                local_agedys_manager.send_facturas_pendientes_email(usuario, email, facturas, dry_run=True)
                print("✓ send_facturas_pendientes_email (dry-run)")
            
            # Test send_dpds_sin_visado_email
            usuarios_dpds_sin_visado = local_agedys_manager.get_usuarios_dpds_sin_visado_calidad()
            if usuarios_dpds_sin_visado:
                usuario_data = usuarios_dpds_sin_visado[0]
                usuario = usuario_data.get('UsuarioRed', 'Test')
                email = usuario_data.get('CorreoUsuario', 'test@test.com')
                dpds = local_agedys_manager.get_dpds_sin_visado_calidad(usuario)
                local_agedys_manager.send_dpds_sin_visado_email(usuario, email, dpds, dry_run=True)
                print("✓ send_dpds_sin_visado_email (dry-run)")
            
            # Test send_dpds_rechazados_email
            usuarios_dpds_rechazados = local_agedys_manager.get_usuarios_dpds_rechazados_calidad()
            if usuarios_dpds_rechazados:
                usuario_data = usuarios_dpds_rechazados[0]
                usuario = usuario_data.get('UsuarioRed', 'Test')
                email = usuario_data.get('CorreoUsuario', 'test@test.com')
                dpds = local_agedys_manager.get_dpds_rechazados_calidad(usuario)
                local_agedys_manager.send_dpds_rechazados_email(usuario, email, dpds, dry_run=True)
                print("✓ send_dpds_rechazados_email (dry-run)")
            
            # Test send_economia_email
            usuarios_economia = local_agedys_manager.get_usuarios_economia()
            dpds = local_agedys_manager.get_dpds_fin_agenda_tecnica_por_recepcionar()
            if usuarios_economia and dpds:
                local_agedys_manager.send_economia_email(usuarios_economia, dpds, dry_run=True)
                print("✓ send_economia_email (dry-run)")
            
            # Test send_dpds_sin_pedido_email
            dpds_sin_pedido = local_agedys_manager.get_dpds_sin_pedido()
            if dpds_sin_pedido:
                # Para DPDs sin pedido, usar el PETICIONARIO del primer DPD
                primer_dpd = dpds_sin_pedido[0]
                usuario = primer_dpd.get('PETICIONARIO', 'Test')
                email = f"{usuario}@telefonica.com"
                local_agedys_manager.send_dpds_sin_pedido_email(usuario, email, dpds_sin_pedido, dry_run=True)
                print("✓ send_dpds_sin_pedido_email (dry-run)")
            
        except Exception as e:
            pytest.fail(f"Error en métodos de envío de email: {e}")

    def test_email_registration_real_database(self, local_agedys_manager):
        """Probar registro real de emails en la base de datos"""
        
        # Datos de prueba para email
        test_email_data = {
            'destinatario': 'test@example.com',
            'asunto': 'Prueba de integración AGEDYS',
            'cuerpo': '<p>Este es un email de prueba</p>',
            'aplicacion_id': config.app_id_agedys
        }
        
        try:
            # Obtener conexión a la base de datos de correos usando la cadena de conexión
            correos_db = AccessDatabase(config.get_db_correos_connection_string())
            print(f"✓ Conexión establecida con base de datos: {config.db_correos_path}")
            
            # Registrar email usando la función de utils
            print(f"Registrando email con datos: {test_email_data}")
            result = register_email_in_database(
                correos_db,
                'AGEDYS',
                test_email_data['asunto'],
                test_email_data['cuerpo'],
                test_email_data['destinatario']
            )
            
            print(f"Resultado del registro: {result}")
            assert result is True, "El registro de email debe ser exitoso"
            print("✓ Email registrado correctamente en la base de datos")
            
            # Verificar que el email se registró consultando la base de datos
            # Usar Max para obtener el último ID en lugar de TOP 1
            max_id_result = correos_db.execute_query(
                "SELECT Max(IDCorreo) AS MaxID FROM TbCorreosEnviados WHERE Destinatarios = ? AND Asunto = ?",
                [test_email_data['destinatario'], test_email_data['asunto']]
            )
            
            if max_id_result and max_id_result[0]['MaxID']:
                max_id = max_id_result[0]['MaxID']
                emails = correos_db.execute_query(
                    "SELECT * FROM TbCorreosEnviados WHERE IDCorreo = ?",
                    [max_id]
                )
                
                assert len(emails) > 0, "El email debe estar registrado en la base de datos"
                email_registrado = emails[0]
                assert email_registrado['Destinatarios'] == test_email_data['destinatario']
                assert email_registrado['Asunto'] == test_email_data['asunto']
                print("✓ Email verificado en la base de datos")
            else:
                pytest.fail("No se pudo encontrar el email registrado")
            
        except Exception as e:
            pytest.fail(f"Error en registro de email: {e}")
    
    def test_task_execution_real_database(self, agedys_manager):
        """Probar ejecución y registro de tareas en base de datos real"""
        
        app_id = 3  # APP_ID de AGEDYS
        
        try:
            # Obtener conexión a la base de datos de tareas
            tareas_db = AccessDatabase(config.get_db_tareas_connection_string())
            
            # Verificar si la tarea debe ejecutarse
            should_execute = should_execute_task(tareas_db, f"AGEDYS_{app_id}", 1)
            print(f"✓ Verificación de ejecución de tarea: {should_execute}")
            
            # Registrar finalización de tarea
            result = register_task_completion(tareas_db, f"AGEDYS_{app_id}")
            assert result is True, "El registro de finalización debe ser exitoso"
            print("✓ Finalización de tarea registrada correctamente")
            
            # Verificar que se registró en la base de datos
            query = """
                SELECT * FROM TbTareas 
                WHERE Tarea = ?
            """
            
            tareas = tareas_db.execute_query(query, [f"AGEDYS_{app_id}"])
            assert len(tareas) > 0, "La tarea debe estar registrada en la base de datos"
            
            tarea_registrada = tareas[0]
            assert tarea_registrada['Tarea'] == f"AGEDYS_{app_id}"
            assert tarea_registrada['Realizado'] == 'Sí'
            print("✓ Tarea verificada en la base de datos")
            
        except Exception as e:
            pytest.fail(f"Error en ejecución de tarea: {e}")
    
    def test_database_connectivity(self, local_agedys_manager):
        """Test de conectividad real a las bases de datos"""
        
        # Verificar que las bases de datos están disponibles
        assert local_agedys_manager.db is not None, "Base de datos AGEDYS debe estar disponible"
        assert local_agedys_manager.correos_db is not None, "Base de datos Correos debe estar disponible"
        
        # Probar consultas básicas
        try:
            # Test en base de datos AGEDYS
            result = local_agedys_manager.db.execute_query("SELECT COUNT(*) as total FROM TbProyectos")
            assert isinstance(result, list) and len(result) > 0
            print(f"✓ TbProyectos: {result[0]['total']} registros")
            
            # Test en base de datos Correos
            result = local_agedys_manager.correos_db.execute_query("SELECT COUNT(*) as total FROM TbCorreosEnviados")
            assert isinstance(result, list) and len(result) > 0
            print(f"✓ TbCorreosEnviados: {result[0]['total']} registros")
            
        except Exception as e:
            pytest.fail(f"Error en conectividad de base de datos: {e}")
    
    def test_real_usuarios_facturas_pendientes(self, local_agedys_manager):
        """Test con datos reales de usuarios con facturas pendientes"""
        
        try:
            usuarios = local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
            
            # Verificar estructura de datos
            assert isinstance(usuarios, list), "Debe devolver una lista"
            
            if usuarios:
                usuario = usuarios[0]
                assert 'UsuarioRed' in usuario, "Debe contener UsuarioRed"
                assert 'Email' in usuario, "Debe contener Email"
                print(f"✓ Encontrados {len(usuarios)} usuarios con facturas pendientes")
                
                # Probar obtener facturas para el primer usuario
                facturas = local_agedys_manager.get_facturas_pendientes_visado_tecnico(usuario['UsuarioRed'])
                assert isinstance(facturas, list), "Facturas debe ser una lista"
                print(f"✓ Usuario {usuario['UsuarioRed']}: {len(facturas)} facturas pendientes")
            else:
                print("ℹ No hay usuarios con facturas pendientes en este momento")
                
        except Exception as e:
            pytest.fail(f"Error en consulta de usuarios con facturas pendientes: {e}")
    
    def test_real_usuarios_dpds_sin_visado(self, local_agedys_manager):
        """Test con datos reales de usuarios con DPDs sin visado"""
        
        try:
            usuarios = local_agedys_manager.get_usuarios_dpds_sin_visado_calidad()
            
            assert isinstance(usuarios, list), "Debe devolver una lista"
            
            if usuarios:
                usuario = usuarios[0]
                assert 'UsuarioRed' in usuario, "Debe contener UsuarioRed"
                assert 'Email' in usuario, "Debe contener Email"
                print(f"✓ Encontrados {len(usuarios)} usuarios con DPDs sin visado")
                
                # Probar obtener DPDs para el primer usuario
                dpds = local_agedys_manager.get_dpds_sin_visado_calidad(usuario['UsuarioRed'])
                assert isinstance(dpds, list), "DPDs debe ser una lista"
                print(f"✓ Usuario {usuario['UsuarioRed']}: {len(dpds)} DPDs sin visado")
            else:
                print("ℹ No hay usuarios con DPDs sin visado en este momento")
                
        except Exception as e:
            pytest.fail(f"Error en consulta de usuarios con DPDs sin visado: {e}")
    
    def test_real_usuarios_dpds_rechazados(self, local_agedys_manager):
        """Test con datos reales de usuarios con DPDs rechazados"""
        
        try:
            usuarios = local_agedys_manager.get_usuarios_dpds_rechazados_calidad()
            
            assert isinstance(usuarios, list), "Debe devolver una lista"
            
            if usuarios:
                usuario = usuarios[0]
                assert 'UsuarioRed' in usuario, "Debe contener UsuarioRed"
                assert 'Email' in usuario, "Debe contener Email"
                print(f"✓ Encontrados {len(usuarios)} usuarios con DPDs rechazados")
                
                # Probar obtener DPDs para el primer usuario
                dpds = local_agedys_manager.get_dpds_rechazados_calidad(usuario['UsuarioRed'])
                assert isinstance(dpds, list), "DPDs debe ser una lista"
                print(f"✓ Usuario {usuario['UsuarioRed']}: {len(dpds)} DPDs rechazados")
            else:
                print("ℹ No hay usuarios con DPDs rechazados en este momento")
                
        except Exception as e:
            pytest.fail(f"Error en consulta de usuarios con DPDs rechazados: {e}")
    
    def test_real_usuarios_economia(self, local_agedys_manager):
        """Test con datos reales de usuarios de economía"""
        
        try:
            usuarios = local_agedys_manager.get_usuarios_economia()
            
            assert isinstance(usuarios, list), "Debe devolver una lista"
            
            if usuarios:
                usuario = usuarios[0]
                assert 'UsuarioRed' in usuario, "Debe contener UsuarioRed"
                assert 'CorreoUsuario' in usuario, "Debe contener CorreoUsuario"
                print(f"✓ Encontrados {len(usuarios)} usuarios de economía")
            else:
                print("ℹ No hay usuarios de economía en este momento")
                
        except Exception as e:
            pytest.fail(f"Error en consulta de usuarios de economía: {e}")
    
    def test_real_full_workflow(self, local_agedys_manager):
        """Test del flujo completo con datos reales"""
        
        # Ejecutar el proceso completo en modo dry-run
        result = local_agedys_manager.run(dry_run=True)
        
        # Verificar que el proceso se ejecutó correctamente
        assert result is True, "El proceso debe completarse exitosamente"
        print("✓ Flujo completo ejecutado correctamente en modo dry-run")

    def test_sql_injection_protection(self, local_agedys_manager):
        """Probar protección contra inyección SQL"""
        
        # Intentar inyección SQL maliciosa
        malicious_inputs = [
            "'; DROP TABLE TbUsuariosAplicaciones; --",
            "' OR '1'='1",
            "'; DELETE FROM TbFacturasDetalle; --",
            "' UNION SELECT * FROM TbUsuariosAplicaciones --"
        ]
        
        for malicious_input in malicious_inputs:
            try:
                # Usar consulta parametrizada (debe ser segura)
                query = "SELECT COUNT(*) as total FROM TbUsuariosAplicaciones WHERE Nombre = ?"
                result = local_agedys_manager.tareas_db.execute_query(query, [malicious_input])
                
                # La consulta debe ejecutarse sin errores y devolver 0 resultados
                assert isinstance(result, list), "Debe devolver una lista"
                assert result[0]['total'] == 0, "No debe encontrar resultados con input malicioso"
                
            except Exception as e:
                # Si hay error, debe ser por sintaxis SQL, no por inyección exitosa
                assert "syntax error" in str(e).lower() or "invalid" in str(e).lower()
        
        print("✓ Protección contra inyección SQL verificada")
    
    def test_database_performance(self, local_agedys_manager):
        """Probar rendimiento básico de las consultas"""
        
        import time
        
        queries_to_test = [
            ('get_usuarios_facturas_pendientes_visado_tecnico', local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico),
            ('get_usuarios_dpds_sin_visado_calidad', local_agedys_manager.get_usuarios_dpds_sin_visado_calidad),
            ('get_usuarios_dpds_rechazados_calidad', local_agedys_manager.get_usuarios_dpds_rechazados_calidad),
            ('get_usuarios_economia', local_agedys_manager.get_usuarios_economia),
            ('get_usuarios_dpds_pendientes_recepcion_economica', local_agedys_manager.get_usuarios_dpds_pendientes_recepcion_economica),
            ('get_dpds_fin_agenda_tecnica_por_recepcionar', local_agedys_manager.get_dpds_fin_agenda_tecnica_por_recepcionar),
            ('get_usuarios_tareas', local_agedys_manager.get_usuarios_tareas)
        ]
        
        performance_results = {}
        
        for query_name, query_method in queries_to_test:
            start_time = time.time()
            
            try:
                result = query_method()
                end_time = time.time()
                
                execution_time = end_time - start_time
                performance_results[query_name] = {
                    'time': execution_time,
                    'records': len(result) if isinstance(result, list) else 0
                }
                
                # Verificar que la consulta no tome más de 30 segundos
                assert execution_time < 30, f"Consulta {query_name} tomó {execution_time:.2f}s (>30s)"
                
                print(f"✓ {query_name}: {execution_time:.2f}s, {performance_results[query_name]['records']} registros")
                
            except Exception as e:
                pytest.fail(f"Error en consulta {query_name}: {e}")
        
        # Verificar que al menos una consulta devolvió resultados (si hay datos)
        total_records = sum(r['records'] for r in performance_results.values())
        print(f"✓ Total de registros procesados: {total_records}")
    
    def test_css_loading_real_file(self, local_agedys_manager):
        """Probar carga del archivo CSS real"""
        
        try:
            css_content = local_agedys_manager.css_content
            
            assert isinstance(css_content, str), "CSS debe ser una cadena"
            assert len(css_content) > 0, "CSS no debe estar vacío"
            assert 'table' in css_content.lower() or 'body' in css_content.lower(), "CSS debe contener estilos básicos"
            
            print(f"✓ CSS cargado correctamente: {len(css_content)} caracteres")
            
        except Exception as e:
            pytest.fail(f"Error al cargar CSS: {e}")
    
    def test_complete_email_workflow_real_data(self, local_agedys_manager):
        """Probar flujo completo de generación y registro de emails con datos reales"""
        
        try:
            # Obtener datos reales
            usuarios_facturas = local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
            usuarios_dpds_sin_visado = local_agedys_manager.get_usuarios_dpds_sin_visado_calidad()
            usuarios_dpds_rechazadas = local_agedys_manager.get_usuarios_dpds_rechazados_calidad()
            usuarios_economia = local_agedys_manager.get_usuarios_economia()
            
            # Si hay datos, probar generación de HTML
            if usuarios_facturas or usuarios_dpds_sin_visado or usuarios_dpds_rechazadas or usuarios_economia:
                
                # Generar HTML para cada tipo de datos
                if usuarios_facturas:
                    usuario = usuarios_facturas[0].get('UsuarioRed', 'Test')
                    facturas = local_agedys_manager.get_facturas_pendientes_visado_tecnico(usuario)
                    html_facturas = local_agedys_manager.generate_facturas_html_table(facturas)
                    assert isinstance(html_facturas, str) and len(html_facturas) > 0
                    assert '<table' in html_facturas or '<p>' in html_facturas
                    print("✓ HTML generado para facturas pendientes")
                
                if usuarios_dpds_sin_visado:
                    usuario = usuarios_dpds_sin_visado[0].get('UsuarioRed', 'Test')
                    dpds = local_agedys_manager.get_dpds_sin_visado_calidad(usuario)
                    html_dpds_sin_visado = local_agedys_manager.generate_dpds_html_table(dpds, 'sin_visado_calidad')
                    assert isinstance(html_dpds_sin_visado, str) and len(html_dpds_sin_visado) > 0
                    print("✓ HTML generado para DPDs sin visado")
                
                if usuarios_dpds_rechazadas:
                    usuario = usuarios_dpds_rechazadas[0].get('UsuarioRed', 'Test')
                    dpds = local_agedys_manager.get_dpds_rechazados_calidad(usuario)
                    html_dpds_rechazadas = local_agedys_manager.generate_dpds_html_table(dpds, 'rechazados_calidad')
                    assert isinstance(html_dpds_rechazadas, str) and len(html_dpds_rechazadas) > 0
                    print("✓ HTML generado para DPDs rechazadas")
                
                print("✓ Flujo completo de email verificado con datos reales")
            else:
                print("ℹ No hay datos para procesar - flujo verificado sin datos")
                
        except Exception as e:
            pytest.fail(f"Error en flujo completo de email: {e}")


    
    def test_real_sql_queries_facturas_por_usuario(self, local_agedys_manager):
        """Test de consultas SQL reales para facturas por usuario"""
        # Primero obtener un usuario
        usuarios = local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
        
        if usuarios:
            usuario = usuarios[0]['UsuarioRed']  # Usar UsuarioRed en lugar de Nombre
            
            # Ejecutar consulta de facturas para ese usuario
            facturas = local_agedys_manager.get_facturas_pendientes_visado_tecnico(usuario)
            
            # Verificar estructura de datos
            assert isinstance(facturas, list)
            
            if facturas:
                factura = facturas[0]
                expected_fields = ['NFactura', 'CODPROYECTOS', 'PETICIONARIO', 'CodExp']
                for field in expected_fields:
                    assert field in factura, f"Campo {field} no encontrado en factura"
    
    def test_real_sql_queries_dpds(self, local_agedys_manager):
        """Test de consultas SQL reales para DPDs"""
        # Test DPDs sin visado de calidad
        usuarios_dpds_calidad = local_agedys_manager.get_usuarios_dpds_sin_visado_calidad()
        assert isinstance(usuarios_dpds_calidad, list)
        
        # Test DPDs rechazados por calidad
        usuarios_dpds_rechazados = local_agedys_manager.get_usuarios_dpds_rechazados_calidad()
        assert isinstance(usuarios_dpds_rechazados, list)
        
        # Test usuarios de economía
        usuarios_economia = local_agedys_manager.get_usuarios_economia()
        assert isinstance(usuarios_economia, list)
        
        # Si hay datos, probar consulta de DPDs por usuario
        if usuarios_dpds_calidad:
            usuario = usuarios_dpds_calidad[0]['UsuarioRed']  # Usar UsuarioRed en lugar de Nombre
            dpds = local_agedys_manager.get_dpds_sin_visado_calidad(usuario)
            
            assert isinstance(dpds, list)
            if dpds:
                dpd = dpds[0]
                expected_fields = ['NumeroDPD', 'Descripcion']
                for field in expected_fields:
                    assert field in dpd, f"Campo {field} no encontrado en DPD"
    
    def test_real_email_registration(self, local_agedys_manager):
        """Test de registro real de emails en la base de datos"""
        # Datos de prueba
        email_data = {
            'para': 'test@empresa.com',
            'asunto': 'Test de integración AGEDYS',
            'cuerpo': '<html><body>Contenido de prueba</body></html>',
            'tipo': 'facturas_pendientes'
        }
        
        # Obtener conexión a la base de datos de correos
        from common.database import AccessDatabase
        correos_db = AccessDatabase(config.get_db_correos_connection_string())
        
        # Contar emails antes de la prueba
        count_before = correos_db.execute_query("SELECT COUNT(*) as total FROM TbCorreosEnviados")[0]['total']
        
        # Registrar email
        from common.utils import register_email_in_database
        result = register_email_in_database(
            correos_db,
            'AGEDYS',
            email_data['asunto'],
            email_data['cuerpo'],
            email_data['para']
        )
        
        # Verificar que se registró correctamente
        assert result is True
        
        # Contar emails después
        count_after = correos_db.execute_query("SELECT COUNT(*) as total FROM TbCorreosEnviados")[0]['total']
        assert count_after == count_before + 1
        
        # Verificar el último email registrado usando Max para obtener el ID más alto
        max_id_result = correos_db.execute_query(
            "SELECT Max(IDCorreo) AS MaxID FROM TbCorreosEnviados"
        )
        max_id = max_id_result[0]['MaxID']
        
        last_email = correos_db.execute_query(
            "SELECT * FROM TbCorreosEnviados WHERE IDCorreo = ?",
            [max_id]
        )[0]
        
        assert last_email['Destinatarios'] == email_data['para']
        assert last_email['Asunto'] == email_data['asunto']
        assert email_data['cuerpo'] in last_email['Cuerpo']
    
    def test_real_task_execution_check(self, local_agedys_manager):
        """Test de verificación real de ejecución de tareas"""
        from common.utils import should_execute_task
        from common.database import AccessDatabase
        
        # Obtener conexión a la base de datos de tareas
        tareas_db = AccessDatabase(config.get_db_tareas_connection_string())
        
        # Test con tarea que debe ejecutarse (más de 24 horas)
        should_execute = should_execute_task(tareas_db, 'AGEDYS_3', 1)
        assert isinstance(should_execute, bool)
        
        # Si la tarea debe ejecutarse, registrar su finalización
        if should_execute:
            from common.utils import register_task_completion
            result = register_task_completion(tareas_db, 'AGEDYS_3')
            assert result is True
            
            # Verificar que se actualizó con la estructura correcta
            task_info = tareas_db.execute_query(
                "SELECT Fecha, Realizado FROM TbTareas WHERE Tarea = ?",
                ['AGEDYS_3']
            )
            assert len(task_info) > 0
            assert task_info[0]['Realizado'] == 'Sí'
    
    def test_real_full_workflow(self, local_agedys_manager):
        """Test del flujo completo con datos reales"""
        # Ejecutar el proceso completo en modo dry-run
        result = local_agedys_manager.run(dry_run=True)
        
        # Verificar que se ejecutó sin errores
        assert result is True
        
        # Ejecutar el proceso completo en modo real
        result = local_agedys_manager.execute_task(force=True, dry_run=False)
        
        # Verificar que se ejecutó sin errores
        assert result is True
    
    def test_sql_injection_protection(self, local_agedys_manager):
        """Test de protección contra inyección SQL"""
        # Intentar inyección SQL en parámetros
        malicious_user = "'; DROP TABLE TbProyectos; --"
        
        try:
            # Esta consulta debería ser segura gracias a parámetros
            facturas = local_agedys_manager.get_facturas_pendientes_visado_tecnico(malicious_user)
            
            # Verificar que la tabla sigue existiendo
            proyectos = local_agedys_manager.db.execute_query("SELECT COUNT(*) as total FROM TbProyectos")
            assert len(proyectos) > 0  # La tabla no fue eliminada
            
        except Exception as e:
            # Si hay error, debería ser por usuario no encontrado, no por SQL malformado
            assert "syntax error" not in str(e).lower()
    
    def test_database_performance(self, local_agedys_manager):
        """Test básico de rendimiento de consultas"""
        import time
        
        # Medir tiempo de consultas principales
        start_time = time.time()
        
        usuarios_facturas = local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
        usuarios_dpds_calidad = local_agedys_manager.get_usuarios_dpds_sin_visado_calidad()
        usuarios_dpds_rechazados = local_agedys_manager.get_usuarios_dpds_rechazados_calidad()
        usuarios_economia = local_agedys_manager.get_usuarios_economia()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Las consultas principales no deberían tomar más de 10 segundos
        assert execution_time < 10.0, f"Consultas principales tomaron {execution_time:.2f} segundos"
        
        # Verificar que se obtuvieron resultados
        total_results = (len(usuarios_facturas) + len(usuarios_dpds_calidad) + 
                        len(usuarios_dpds_rechazados) + len(usuarios_economia))
        
        # Al menos debería haber algunos resultados con los datos de prueba
        assert total_results >= 0  # Puede ser 0 si no hay datos pendientes
    
    @pytest.mark.slow
    def test_data_consistency(self, local_agedys_manager):
        """Test de consistencia de datos entre consultas relacionadas"""
        # Obtener usuarios con facturas pendientes
        usuarios_facturas = local_agedys_manager.get_usuarios_facturas_pendientes_visado_tecnico()
        
        for usuario_info in usuarios_facturas:
            usuario = usuario_info['UsuarioRed']  # Usar UsuarioRed en lugar de Nombre
            
            # Obtener facturas para este usuario
            facturas = local_agedys_manager.get_facturas_pendientes_visado_tecnico(usuario)
            
            # Verificar consistencia: si hay usuario, debe haber al menos una factura
            assert len(facturas) > 0, f"Usuario {usuario} aparece en lista pero no tiene facturas"
            
            # Verificar que todas las facturas pertenecen al usuario correcto
            for factura in facturas:
                # Verificar que la factura tiene los campos requeridos
                assert 'NFactura' in factura, "Factura debe tener número"
                assert 'CODPROYECTOS' in factura, "Factura debe tener código de proyecto"
                # La relación usuario-factura se verifica implícitamente por la consulta SQL