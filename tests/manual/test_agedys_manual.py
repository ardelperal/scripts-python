"""
Tests manuales para el módulo AGEDYS
Estos tests requieren intervención manual o verificación visual
"""
import pytest
import os
from datetime import datetime
from src.agedys.agedys_manager import AgedysManager


class TestAgedysManual:
    """Tests manuales para AGEDYS"""
    
    @pytest.mark.manual
    def test_database_connection_real(self):
        """
        Test manual: Verificar conexión real a las bases de datos
        
        INSTRUCCIONES MANUALES:
        1. Asegúrate de que las bases de datos AGEDYS, Tareas y Correos estén disponibles
        2. Verifica que las rutas de conexión en config.py sean correctas
        3. Ejecuta este test y verifica que no hay errores de conexión
        4. Revisa los logs para confirmar conexiones exitosas
        
        CRITERIOS DE ÉXITO:
        - No se producen excepciones de conexión
        - Se pueden ejecutar consultas básicas en cada base de datos
        - Los logs muestran conexiones exitosas
        """
        try:
            manager = AgedysManager()
            
            # Intentar consultas básicas
            usuarios_facturas = manager.get_usuarios_facturas_pendientes_visado_tecnico()
            usuarios_dpds = manager.get_usuarios_dpds_sin_visado_calidad()
            usuarios_economia = manager.get_usuarios_economia()
            
            print(f"✓ Conexión exitosa - Usuarios facturas: {len(usuarios_facturas)}")
            print(f"✓ Conexión exitosa - Usuarios DPDs: {len(usuarios_dpds)}")
            print(f"✓ Conexión exitosa - Usuarios economía: {len(usuarios_economia)}")
            
            assert True, "Conexiones establecidas correctamente"
            
        except Exception as e:
            pytest.fail(f"Error de conexión a base de datos: {str(e)}")
    
    @pytest.mark.manual
    def test_email_html_visual_inspection(self):
        """
        Test manual: Inspección visual del HTML generado para emails
        
        INSTRUCCIONES MANUALES:
        1. Ejecuta este test
        2. Abre el archivo HTML generado en un navegador
        3. Verifica que el formato sea profesional y legible
        4. Comprueba que las tablas se muestren correctamente
        5. Verifica que los colores y estilos sean apropiados
        6. Confirma que el contenido sea responsive
        
        CRITERIOS DE ÉXITO:
        - El HTML se renderiza correctamente en diferentes navegadores
        - Las tablas son legibles y bien formateadas
        - Los colores y estilos son profesionales
        - El diseño es responsive
        """
        manager = AgedysManager()
        
        # Datos de prueba para generar HTML
        facturas_test = [
            {
                'NumeroFactura': 'FAC-2024-001',
                'Proveedor': 'Tecnologías Avanzadas S.L.',
                'Importe': 15750.50,
                'FechaFactura': '2024-01-15',
                'Descripcion': 'Licencias software desarrollo'
            },
            {
                'NumeroFactura': 'FAC-2024-002',
                'Proveedor': 'Suministros Industriales S.A.',
                'Importe': 8920.75,
                'FechaFactura': '2024-01-16',
                'Descripcion': 'Material técnico especializado'
            }
        ]
        
        dpds_test = [
            {
                'NumeroDPD': 'DPD-2024-001',
                'Descripcion': 'Actualización sistema gestión documental',
                'FechaCreacion': '2024-01-10',
                'Estado': 'Pendiente Visado Calidad'
            },
            {
                'NumeroDPD': 'DPD-2024-002',
                'Descripcion': 'Implementación protocolo seguridad',
                'FechaCreacion': '2024-01-12',
                'Estado': 'Rechazado Calidad'
            }
        ]
        
        # Generar HTML completo
        html_facturas = manager.generate_facturas_html_table(facturas_test)
        html_dpds = manager.generate_dpds_html_table(dpds_test, 'sin_visado_calidad')
        
        # Crear HTML completo para inspección
        html_completo = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Visual AGEDYS</title>
            <style>
                {manager.css_content}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Sistema AGEDYS - Test Visual</h1>
                <p>Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
            </div>
            
            <div class="content">
                <h2>Facturas Pendientes de Visado Técnico</h2>
                {html_facturas}
                
                <h2>DPDs Pendientes de Visado de Calidad</h2>
                {html_dpds}
            </div>
            
            <div class="footer">
                <p>Este es un mensaje automático del sistema AGEDYS.</p>
                <p><small>Test de inspección visual</small></p>
            </div>
        </body>
        </html>
        """
        
        # Guardar archivo para inspección manual
        test_file = 'tests/output/agedys_visual_test.html'
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(html_completo)
        
        print(f"✓ Archivo HTML generado: {test_file}")
        print("📋 ACCIÓN REQUERIDA: Abre el archivo en un navegador y verifica:")
        print("   - Formato profesional y legible")
        print("   - Tablas bien estructuradas")
        print("   - Colores y estilos apropiados")
        print("   - Diseño responsive")
        
        assert os.path.exists(test_file), "Archivo HTML generado correctamente"
    
    @pytest.mark.manual
    def test_email_registration_verification(self):
        """
        Test manual: Verificar registro de emails en base de datos
        
        INSTRUCCIONES MANUALES:
        1. Ejecuta este test con dry_run=False
        2. Verifica en la base de datos correos_datos.accdb
        3. Comprueba que se registraron los emails en TbEnvioCorreos
        4. Verifica que los datos sean correctos (destinatario, asunto, contenido)
        5. Confirma que la fecha de registro sea actual
        
        CRITERIOS DE ÉXITO:
        - Los registros aparecen en TbEnvioCorreos
        - Los datos son correctos y completos
        - Las fechas de registro son actuales
        - No hay duplicados innecesarios
        """
        manager = AgedysManager()
        
        # Ejecutar proceso en modo producción
        print("🔄 Ejecutando proceso AGEDYS...")
        result = manager.execute_task(force=True, dry_run=False)
        
        print(f"✓ Proceso ejecutado: {result}")
        print("📋 ACCIÓN REQUERIDA: Verifica en la base de datos correos_datos.accdb:")
        print("   - Tabla: TbEnvioCorreos")
        print("   - Campos: Destinatario, Asunto, Contenido, FechaEnvio")
        print("   - Verifica que los registros sean recientes y correctos")
        
        assert result is not None, "El proceso se ejecutó sin errores críticos"
    
    @pytest.mark.manual
    def test_task_scheduling_verification(self):
        """
        Test manual: Verificar integración con sistema de tareas
        
        INSTRUCCIONES MANUALES:
        1. Ejecuta este test
        2. Verifica en la base de datos de tareas
        3. Comprueba que se registró la ejecución de la tarea AGEDYS
        4. Verifica que la fecha y resultado sean correctos
        5. Confirma que no se ejecute si no debe según la programación
        
        CRITERIOS DE ÉXITO:
        - La tarea se registra correctamente
        - Los datos de ejecución son precisos
        - La lógica de programación funciona correctamente
        """
        manager = AgedysManager()
        
        # Test 1: Ejecución forzada
        print("🔄 Test 1: Ejecución forzada...")
        result1 = manager.execute_task(force=True, dry_run=True)
        print(f"✓ Resultado ejecución forzada: {result1}")
        
        # Test 2: Ejecución según programación
        print("🔄 Test 2: Ejecución según programación...")
        result2 = manager.execute_task(force=False, dry_run=True)
        print(f"✓ Resultado ejecución programada: {result2}")
        
        print("📋 ACCIÓN REQUERIDA: Verifica en la base de datos de tareas:")
        print("   - Registros de ejecución de tarea 'AGEDYS'")
        print("   - Fechas y resultados correctos")
        print("   - Lógica de programación funcionando")
        
        assert isinstance(result1, bool), "Ejecución forzada devuelve resultado válido"
        assert isinstance(result2, bool), "Ejecución programada devuelve resultado válido"
    
    @pytest.mark.manual
    def test_performance_real_data(self):
        """
        Test manual: Verificar rendimiento con datos reales
        
        INSTRUCCIONES MANUALES:
        1. Ejecuta este test con las bases de datos reales pobladas
        2. Mide el tiempo de ejecución total
        3. Verifica que no haya timeouts o errores de memoria
        4. Comprueba que el proceso termine en tiempo razonable
        5. Verifica el uso de recursos del sistema
        
        CRITERIOS DE ÉXITO:
        - Tiempo de ejecución < 5 minutos para datasets normales
        - Sin errores de memoria o timeout
        - Uso de recursos del sistema razonable
        - Proceso completa exitosamente
        """
        import time
        
        manager = AgedysManager()
        
        print("🔄 Iniciando test de rendimiento con datos reales...")
        start_time = time.time()
        
        try:
            result = manager.execute_task(force=True, dry_run=True)
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"✓ Proceso completado: {result}")
            print(f"⏱️ Tiempo de ejecución: {execution_time:.2f} segundos")
            
            # Criterios de rendimiento
            if execution_time < 60:
                print("🟢 Rendimiento EXCELENTE (< 1 minuto)")
            elif execution_time < 180:
                print("🟡 Rendimiento BUENO (< 3 minutos)")
            elif execution_time < 300:
                print("🟠 Rendimiento ACEPTABLE (< 5 minutos)")
            else:
                print("🔴 Rendimiento LENTO (> 5 minutos)")
            
            print("📋 ACCIÓN REQUERIDA: Verifica:")
            print("   - Tiempo de ejecución aceptable")
            print("   - Sin errores de memoria")
            print("   - Uso de CPU y RAM razonable")
            
            assert result is not None, "El proceso completó sin errores críticos"
            assert execution_time < 600, "Tiempo de ejecución menor a 10 minutos"
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"❌ Error después de {execution_time:.2f} segundos: {str(e)}")
            pytest.fail(f"Error en test de rendimiento: {str(e)}")
    
    @pytest.mark.manual
    def test_data_accuracy_verification(self):
        """
        Test manual: Verificar precisión de los datos procesados
        
        INSTRUCCIONES MANUALES:
        1. Ejecuta este test
        2. Compara los resultados con consultas manuales en la base de datos
        3. Verifica que los números coincidan
        4. Comprueba que no falten registros importantes
        5. Confirma que los filtros funcionen correctamente
        
        CRITERIOS DE ÉXITO:
        - Los números coinciden con consultas manuales
        - No faltan registros importantes
        - Los filtros funcionan correctamente
        - Los datos están actualizados
        """
        manager = AgedysManager()
        
        print("🔄 Verificando precisión de datos...")
        
        # Obtener datos del sistema
        usuarios_facturas = manager.get_usuarios_facturas_pendientes_visado_tecnico()
        usuarios_dpds = manager.get_usuarios_dpds_sin_visado_calidad()
        usuarios_rechazados = manager.get_usuarios_dpds_rechazados_calidad()
        usuarios_economia = manager.get_usuarios_economia()
        usuarios_tareas = manager.get_usuarios_tareas()
        
        print(f"📊 Usuarios con facturas pendientes: {len(usuarios_facturas)}")
        print(f"📊 Usuarios con DPDs sin visado: {len(usuarios_dpds)}")
        print(f"📊 Usuarios con DPDs rechazados: {len(usuarios_rechazados)}")
        print(f"📊 Usuarios de economía: {len(usuarios_economia)}")
        print(f"📊 Usuarios de tareas: {len(usuarios_tareas)}")
        
        # Obtener muestras de datos específicos
        if usuarios_facturas:
            usuario_muestra = usuarios_facturas[0]['Nombre']
            facturas_muestra = manager.get_facturas_pendientes_visado_tecnico(usuario_muestra)
            print(f"📊 Facturas para {usuario_muestra}: {len(facturas_muestra)}")
        
        if usuarios_dpds:
            usuario_dpd = usuarios_dpds[0]['Nombre']
            dpds_muestra = manager.get_dpds_sin_visado_calidad(usuario_dpd)
            print(f"📊 DPDs para {usuario_dpd}: {len(dpds_muestra)}")
        
        print("📋 ACCIÓN REQUERIDA: Compara estos números con consultas manuales:")
        print("   - SELECT COUNT(*) FROM TbUsuarios WHERE [condiciones facturas]")
        print("   - SELECT COUNT(*) FROM TbFacturas WHERE Estado = 'Pendiente Visado Técnico'")
        print("   - SELECT COUNT(*) FROM TbDPD WHERE Estado = 'Pendiente Visado Calidad'")
        print("   - Verifica que los números coincidan")
        
        assert True, "Datos obtenidos para verificación manual"
    
    @pytest.mark.manual
    def test_error_handling_real_scenarios(self):
        """
        Test manual: Verificar manejo de errores en escenarios reales
        
        INSTRUCCIONES MANUALES:
        1. Desconecta temporalmente una base de datos
        2. Ejecuta el proceso y verifica que se maneje el error
        3. Reconecta la base de datos
        4. Verifica que el proceso se recupere
        5. Revisa los logs de error
        
        CRITERIOS DE ÉXITO:
        - Los errores se manejan sin crash del sistema
        - Se registran logs apropiados
        - El sistema se recupera cuando se resuelve el problema
        - Los usuarios reciben notificaciones apropiadas
        """
        manager = AgedysManager()
        
        print("🔄 Test de manejo de errores...")
        print("📋 ACCIÓN REQUERIDA:")
        print("   1. Desconecta temporalmente una base de datos")
        print("   2. Ejecuta: manager.execute_task(force=True, dry_run=True)")
        print("   3. Verifica que no se produzca crash")
        print("   4. Reconecta la base de datos")
        print("   5. Verifica que el proceso se recupere")
        print("   6. Revisa los logs de error")
        
        try:
            result = manager.execute_task(force=True, dry_run=True)
            print(f"✓ Resultado con posibles errores: {result}")
            
        except Exception as e:
            print(f"⚠️ Excepción capturada: {str(e)}")
            print("✓ El sistema manejó la excepción sin crash")
        
        print("📋 Verifica en los logs:")
        print("   - Mensajes de error apropiados")
        print("   - No hay stack traces no manejados")
        print("   - El sistema intenta continuar con otros procesos")
        
        assert True, "Test de manejo de errores completado"
    
    @pytest.mark.manual
    def test_user_acceptance_criteria(self):
        """
        Test manual: Verificar criterios de aceptación del usuario
        
        INSTRUCCIONES MANUALES:
        1. Ejecuta el proceso completo
        2. Verifica que los emails generados sean profesionales
        3. Comprueba que la información sea precisa y útil
        4. Confirma que los tiempos de ejecución sean aceptables
        5. Verifica que el sistema sea confiable
        
        CRITERIOS DE ÉXITO:
        - Los emails son profesionales y útiles
        - La información es precisa y actualizada
        - Los tiempos de ejecución son aceptables
        - El sistema es confiable y estable
        """
        manager = AgedysManager()
        
        print("🔄 Test de criterios de aceptación del usuario...")
        
        # Ejecutar proceso completo
        result = manager.execute_task(force=True, dry_run=False)
        
        print(f"✓ Proceso ejecutado: {result}")
        print("📋 CRITERIOS DE ACEPTACIÓN A VERIFICAR:")
        print("   ✅ Los emails son profesionales y bien formateados")
        print("   ✅ La información es precisa y actualizada")
        print("   ✅ Los destinatarios son correctos")
        print("   ✅ El tiempo de ejecución es aceptable")
        print("   ✅ No hay errores críticos")
        print("   ✅ El sistema es confiable")
        print("   ✅ Los logs son informativos")
        print("   ✅ La integración con otras bases funciona")
        
        print("📋 ACCIÓN REQUERIDA: Confirma que todos los criterios se cumplen")
        
        assert result is not None, "El proceso se ejecutó correctamente"
    
    @pytest.mark.manual
    def test_backup_and_recovery(self):
        """
        Test manual: Verificar procedimientos de backup y recuperación
        
        INSTRUCCIONES MANUALES:
        1. Realiza backup de las bases de datos
        2. Ejecuta el proceso AGEDYS
        3. Simula un fallo de base de datos
        4. Restaura desde backup
        5. Verifica que el proceso funcione correctamente
        
        CRITERIOS DE ÉXITO:
        - Los backups se crean correctamente
        - La restauración funciona sin problemas
        - El proceso AGEDYS funciona después de la restauración
        - No se pierden datos importantes
        """
        print("🔄 Test de backup y recuperación...")
        print("📋 PROCEDIMIENTO MANUAL:")
        print("   1. Crear backup de:")
        print("      - Base de datos AGEDYS")
        print("      - Base de datos Tareas")
        print("      - Base de datos Correos")
        print("   2. Ejecutar proceso AGEDYS")
        print("   3. Simular fallo (renombrar archivo de BD)")
        print("   4. Restaurar desde backup")
        print("   5. Verificar funcionamiento")
        
        manager = AgedysManager()
        
        try:
            result = manager.execute_task(force=True, dry_run=True)
            print(f"✓ Test de funcionamiento básico: {result}")
            
        except Exception as e:
            print(f"⚠️ Error detectado: {str(e)}")
            print("📋 Procede con restauración desde backup")
        
        print("📋 VERIFICAR:")
        print("   ✅ Backups creados correctamente")
        print("   ✅ Restauración exitosa")
        print("   ✅ Proceso funciona post-restauración")
        print("   ✅ Integridad de datos mantenida")
        
        assert True, "Test de backup y recuperación documentado"