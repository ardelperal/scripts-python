"""
Script de prueba para la migración de Expedientes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.expedientes.expedientes_task import ExpedientesTask
from src.expedientes.expedientes_manager import ExpedientesManager


def test_expedientes_task():
    """Prueba la clase ExpedientesTask"""
    print("=== Probando ExpedientesTask ===")
    
    try:
        task = ExpedientesTask()
        print(f"✓ Nombre de tarea: {task.name}")
        print(f"✓ Script filename: {task.script_filename}")
        print(f"✓ Task names: {task.task_names}")
        print(f"✓ Frecuencia: {task.frequency_days} días")
        print("✓ ExpedientesTask creada correctamente")
        return True
    except Exception as e:
        print(f"✗ Error en ExpedientesManager: {e}")
        return False


def test_expedientes_manager_new():
    """Prueba la clase ExpedientesManager"""
    print("\n=== Probando ExpedientesManager ===")
    
    try:
        manager = ExpedientesManager()
        print(f"✓ Manager creado: {manager.name}")
        
        # Probar obtención de correos de administradores
        print("\n--- Probando obtención de correos de administradores ---")
        admin_emails = manager.get_admin_emails()
        print(f"✓ Correos de administradores encontrados: {len(admin_emails)}")
        for email in admin_emails[:3]:  # Mostrar solo los primeros 3
            print(f"  - {email}")
        
        # Probar obtención de correos de tramitadores
        print("\n--- Probando obtención de correos de tramitadores ---")
        task_emails = manager.get_task_emails()
        print(f"✓ Correos de tramitadores encontrados: {len(task_emails)}")
        for email in task_emails[:3]:  # Mostrar solo los primeros 3
            print(f"  - {email}")
        
        # Probar obtención de expedientes TSOL sin código S4H
        print("\n--- Probando expedientes TSOL sin código S4H ---")
        expedientes_tsol = manager.get_expedientes_tsol_sin_cod_s4h()
        print(f"✓ Expedientes TSOL sin código S4H: {len(expedientes_tsol)}")
        for exp in expedientes_tsol[:2]:  # Mostrar solo los primeros 2
            print(f"  - ID: {exp['IDExpediente']}, Código: {exp['CodExp']}, Nemotécnico: {exp['Nemotecnico']}")
        
        # Probar obtención de expedientes a punto de finalizar
        print("\n--- Probando expedientes a punto de finalizar ---")
        expedientes_finalizar = manager.get_expedientes_a_punto_finalizar()
        print(f"✓ Expedientes a punto de finalizar: {len(expedientes_finalizar)}")
        for exp in expedientes_finalizar[:2]:  # Mostrar solo los primeros 2
            print(f"  - ID: {exp['IDExpediente']}, Código: {exp['CodExp']}, Días para fin: {exp['DiasParaFin']}")
        
        # Probar obtención de hitos a punto de finalizar
        print("\n--- Probando hitos a punto de finalizar ---")
        hitos = manager.get_hitos_a_punto_finalizar()
        print(f"✓ Hitos a punto de finalizar: {len(hitos)}")
        for hito in hitos[:2]:  # Mostrar solo los primeros 2
            print(f"  - ID: {hito['IDExpediente']}, Descripción: {hito['Descripcion'][:50]}...")
        
        # Probar obtención de expedientes con estado desconocido
        print("\n--- Probando expedientes con estado desconocido ---")
        expedientes_desconocido = manager.get_expedientes_estado_desconocido()
        print(f"✓ Expedientes con estado desconocido: {len(expedientes_desconocido)}")
        
        # Probar obtención de expedientes adjudicados sin contrato
        print("\n--- Probando expedientes adjudicados sin contrato ---")
        expedientes_sin_contrato = manager.get_expedientes_adjudicados_sin_contrato()
        print(f"✓ Expedientes adjudicados sin contrato: {len(expedientes_sin_contrato)}")
        
        # Probar obtención de expedientes en fase de oferta por mucho tiempo
        print("\n--- Probando expedientes en fase de oferta por mucho tiempo ---")
        expedientes_oferta = manager.get_expedientes_fase_oferta_mucho_tiempo()
        print(f"✓ Expedientes en fase de oferta por mucho tiempo: {len(expedientes_oferta)}")
        
        # Cerrar conexiones
        manager.close_connections()
        print("✓ Conexiones cerradas correctamente")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en ExpedientesManager: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_expedientes_full_execution():
    """Prueba la ejecución completa de Expedientes"""
    print("\n=== Probando ejecución completa de Expedientes ===")
    
    try:
        manager = ExpedientesManager()
        
        # Ejecutar la lógica completa
        result = manager.execute()
        
        if result:
            print("✓ Expedientes ejecutado correctamente")
        else:
            print("✗ Error en la ejecución de Expedientes")
        
        # Cerrar conexiones
        manager.close_connections()
        
        return result
        
    except Exception as e:
        print(f"✗ Error en la ejecución completa: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal de pruebas"""
    print("Iniciando pruebas de migración de Expedientes...")
    
    # Ejecutar pruebas
    test1_ok = test_expedientes_task()
    test2_ok = test_expedientes_manager_new()
    
    # Preguntar si ejecutar la prueba completa
    if test1_ok and test2_ok:
        response = input("\n¿Deseas ejecutar la prueba completa de Expedientes? (s/n): ")
        if response.lower() in ['s', 'sí', 'si', 'y', 'yes']:
            test3_ok = test_expedientes_full_execution()
        else:
            test3_ok = True
            print("Prueba completa omitida por el usuario")
    else:
        test3_ok = False
        print("No se ejecutará la prueba completa debido a errores anteriores")
    
    # Resumen
    print(f"\n=== RESUMEN DE PRUEBAS ===")
    print(f"ExpedientesTask: {'✓' if test1_ok else '✗'}")
    print(f"ExpedientesManager: {'✓' if test2_ok else '✗'}")
    print(f"Ejecución completa: {'✓' if test3_ok else '✗'}")
    
    if test1_ok and test2_ok and test3_ok:
        print("\n🎉 ¡Todas las pruebas de migración de Expedientes pasaron correctamente!")
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa los errores anteriores.")


if __name__ == "__main__":
    main()