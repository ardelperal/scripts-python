"""
Script de integración para ejecutar y validar el módulo de No Conformidades
"""

import sys
import os
import unittest
import logging
from datetime import datetime

# Agregar el directorio padre al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.common.config import Config
from src.common.logger import setup_logger
from src.no_conformidades.no_conformidades_manager import NoConformidadesManager
from src.no_conformidades.html_report_generator import HTMLReportGenerator
from src.no_conformidades.email_notifications import EmailNotificationManager


def ejecutar_tests():
    """Ejecutar todos los tests del módulo de No Conformidades"""
    print("=" * 60)
    print("EJECUTANDO TESTS DEL MÓDULO DE NO CONFORMIDADES")
    print("=" * 60)
    
    # Configurar el loader de tests
    loader = unittest.TestLoader()
    
    # Cargar tests desde el archivo de tests
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'tests')
    suite = loader.discover(test_dir, pattern='test_no_conformidades.py')
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Éxito: {result.wasSuccessful()}")
    
    if result.errors:
        print("\nERRORES:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    return result.wasSuccessful()


def validar_configuracion():
    """Validar que la configuración esté correcta"""
    print("\n" + "=" * 60)
    print("VALIDANDO CONFIGURACIÓN")
    print("=" * 60)
    
    try:
        config = Config()
        
        # Verificar configuraciones básicas
        print(f"Entorno: {config.environment}")
        print(f"Conexión NC: {config.get_db_no_conformidades_connection_string()[:50]}...")
        print(f"Conexión Tareas: {config.get_db_tareas_connection_string()[:50]}...")
        print(f"SMTP Server: {config.smtp_server}")
        print(f"SMTP Port: {config.smtp_port}")
        
        # Verificar rutas de archivos
        db_path = config.get_db_path('no_conformidades')
        print(f"Ruta DB NC: {db_path}")
        
        if not os.path.exists(os.path.dirname(db_path)):
            print(f"⚠️  ADVERTENCIA: El directorio de la base de datos no existe: {os.path.dirname(db_path)}")
        
        print("✅ Configuración validada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en la configuración: {e}")
        return False


def probar_instanciacion_clases():
    """Probar que se pueden instanciar todas las clases principales"""
    print("\n" + "=" * 60)
    print("PROBANDO INSTANCIACIÓN DE CLASES")
    print("=" * 60)
    
    try:
        # Configurar logging para evitar ruido
        logging.getLogger().setLevel(logging.CRITICAL)
        
        # Probar NoConformidadesManager
        print("Instanciando NoConformidadesManager...")
        manager = NoConformidadesManager()
        print("✅ NoConformidadesManager instanciado correctamente")
        
        # Probar HTMLReportGenerator
        print("Instanciando HTMLReportGenerator...")
        html_generator = HTMLReportGenerator()
        print("✅ HTMLReportGenerator instanciado correctamente")
        
        # Probar EmailNotificationManager
        print("Instanciando EmailNotificationManager...")
        email_manager = EmailNotificationManager()
        print("✅ EmailNotificationManager instanciado correctamente")
        
        # Probar generación de HTML básico
        print("Probando generación de HTML...")
        header = html_generator.generar_header_html("Test")
        footer = html_generator.generar_footer_html()
        
        if len(header) > 100 and len(footer) > 50:
            print("✅ Generación de HTML funciona correctamente")
        else:
            print("⚠️  ADVERTENCIA: HTML generado parece incompleto")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la instanciación: {e}")
        import traceback
        traceback.print_exc()
        return False


def generar_reporte_demo():
    """Generar un reporte de demostración"""
    print("\n" + "=" * 60)
    print("GENERANDO REPORTE DE DEMOSTRACIÓN")
    print("=" * 60)
    
    try:
        from src.no_conformidades.no_conformidades_manager import NoConformidad, ARAPC
        
        # Crear datos de demostración
        ncs_demo = [
            NoConformidad(
                codigo="NC-DEMO-001",
                nemotecnico="DEMO",
                descripcion="No Conformidad de demostración para testing",
                responsable_calidad="Usuario Demo",
                fecha_apertura=datetime(2024, 1, 1),
                fecha_prev_cierre=datetime(2024, 2, 1),
                dias_para_cierre=15
            )
        ]
        
        arapcs_demo = [
            ARAPC(
                id_accion=1,
                codigo_nc="NC-DEMO-001",
                descripcion="Acción correctiva de demostración",
                responsable="usuario.demo",
                fecha_fin_prevista=datetime(2024, 1, 15)
            )
        ]
        
        # Generar reporte
        from src.common.html_report_generator import HTMLReportGenerator
        html_generator = HTMLReportGenerator()
        
        html_completo = html_generator.generar_reporte_completo(
            ncs_eficacia=ncs_demo,
            arapcs=arapcs_demo,
            ncs_caducar=[],
            ncs_sin_acciones=[]
        )
        
        # Guardar reporte demo
        demo_path = os.path.join(os.path.dirname(__file__), '..', 'temp', 'reporte_demo_nc.html')
        os.makedirs(os.path.dirname(demo_path), exist_ok=True)
        
        with open(demo_path, 'w', encoding='utf-8') as f:
            f.write(html_completo)
        
        print(f"✅ Reporte de demostración generado: {demo_path}")
        print(f"📄 Tamaño del reporte: {len(html_completo)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generando reporte demo: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal del script de integración"""
    print("🚀 INICIANDO VALIDACIÓN DEL MÓDULO DE NO CONFORMIDADES")
    print(f"⏰ Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    resultados = []
    
    # 1. Validar configuración
    resultados.append(("Configuración", validar_configuracion()))
    
    # 2. Probar instanciación de clases
    resultados.append(("Instanciación", probar_instanciacion_clases()))
    
    # 3. Ejecutar tests
    resultados.append(("Tests unitarios", ejecutar_tests()))
    
    # 4. Generar reporte demo
    resultados.append(("Reporte demo", generar_reporte_demo()))
    
    # Mostrar resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL DE VALIDACIÓN")
    print("=" * 60)
    
    todos_exitosos = True
    for nombre, exito in resultados:
        estado = "✅ ÉXITO" if exito else "❌ FALLO"
        print(f"{nombre:20} : {estado}")
        if not exito:
            todos_exitosos = False
    
    print("\n" + "=" * 60)
    if todos_exitosos:
        print("🎉 VALIDACIÓN COMPLETADA EXITOSAMENTE")
        print("El módulo de No Conformidades está listo para usar")
    else:
        print("⚠️  VALIDACIÓN COMPLETADA CON ERRORES")
        print("Revisa los errores anteriores antes de usar el módulo")
    print("=" * 60)
    
    return todos_exitosos


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)