"""
Script de prueba para validar la migración de BRASS a la nueva arquitectura
"""
import os
import sys
from datetime import date

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from common.logger import setup_logger
from brass.brass_task import BrassTask
from brass.brass_manager import BrassManager

def test_brass_task():
    """Prueba la nueva implementación de BrassTask"""
    print("=== Probando BrassTask ===")
    
    task = BrassTask()
    
    # Probar propiedades básicas
    print(f"Nombre de tarea: {task.get_task_name()}")
    print(f"Es continua: {task.is_continuous()}")
    print(f"Debe ejecutarse hoy: {task.should_run_today()}")
    
    # Cerrar conexiones
    task.close_connections()
    print("BrassTask - Prueba completada\n")

def test_brass_manager_new():
    """Prueba el nuevo BrassManager"""
    print("=== Probando BrassManager ===")
    
    try:
        manager = BrassManager()
        # Probar propiedades básicas
        print(f"Nombre de tarea: {manager.name}")
        print(f"Script: {manager.script_filename}")
        print(f"Frecuencia: {manager.frequency_days} días")
        print(f"Debe ejecutarse hoy: {manager.debe_ejecutarse()}")
        
        # Probar obtención de equipos (sin ejecutar la tarea completa)
        print("Obteniendo equipos fuera de calibración...")
        equipment_list = manager.get_equipment_out_of_calibration()
        print(f"Equipos encontrados: {len(equipment_list)}")
        
        # Probar obtención de usuarios admin
        print("Obteniendo usuarios administradores...")
        admin_users = manager.get_admin_users()
        print(f"Usuarios admin encontrados: {len(admin_users)}")
        
        admin_emails = manager.get_admin_emails_string()
        print(f"Emails admin: {admin_emails[:50]}..." if len(admin_emails) > 50 else f"Emails admin: {admin_emails}")
        
    except Exception as e:
        print(f"Error en prueba de BrassManager: {e}")
    finally:
        manager.close_connections()
    
    print("BrassManager - Prueba completada\n")

def test_brass_execution():
    """Prueba la ejecución completa de BRASS (solo si debe ejecutarse)"""
    print("=== Probando ejecución completa de BRASS ===")
    
    task = BrassTask()
    
    try:
        if task.should_run_today():
            print("La tarea debe ejecutarse hoy. Ejecutando...")
            success = task.execute()
            print(f"Resultado de ejecución: {'Éxito' if success else 'Error'}")
        else:
            print("La tarea no debe ejecutarse hoy según la lógica de negocio")
            print("Ejecutando de todas formas para prueba...")
            success = task.execute()
            print(f"Resultado de ejecución: {'Éxito' if success else 'Error'}")
    
    except Exception as e:
        print(f"Error en ejecución de BRASS: {e}")
    finally:
        task.close_connections()
    
    print("Ejecución completa - Prueba completada\n")

def main():
    """Función principal de pruebas"""
    # Configurar logging
    logger = setup_logger("test_brass_migration")
    
    print("Iniciando pruebas de migración de BRASS")
    print("=" * 50)
    
    try:
        # Ejecutar pruebas
        test_brass_task()
        test_brass_manager_new()
        
        # Preguntar si ejecutar la prueba completa
        response = input("¿Deseas ejecutar la prueba completa de BRASS? (s/n): ")
        if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            test_brass_execution()
        
        print("=" * 50)
        print("Pruebas de migración de BRASS completadas")
        
    except Exception as e:
        print(f"Error en las pruebas: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)