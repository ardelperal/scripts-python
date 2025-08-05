"""
Script de prueba para validar la nueva arquitectura de tareas
"""

import os
import sys
import logging
from datetime import datetime, date

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from common.logger import setup_logger
from common.utils import is_workday
from common.task_registry import get_all_daily_tasks, get_all_continuous_tasks


def test_task_initialization():
    """Prueba la inicialización de todas las tareas"""
    logger = setup_logger('test_architecture')
    logger.info("🧪 Iniciando pruebas de la nueva arquitectura")
    
    # Probar tareas diarias
    logger.info("📋 Probando inicialización de tareas diarias...")
    daily_tasks = get_all_daily_tasks()
    
    for task in daily_tasks:
        try:
            logger.info(f"  ✅ {task.name}: {task.script_filename}")
            logger.info(f"     Tareas BD: {task.task_names}")
            logger.info(f"     Frecuencia: {task.frequency_days} días")
        except Exception as e:
            logger.error(f"  ❌ Error en {task.name}: {e}")
    
    # Probar tareas continuas
    logger.info("🔄 Probando inicialización de tareas continuas...")
    continuous_tasks = get_all_continuous_tasks()
    
    for task in continuous_tasks:
        try:
            logger.info(f"  ✅ {task.name}: {task.script_filename}")
        except Exception as e:
            logger.error(f"  ❌ Error en {task.name}: {e}")
    
    logger.info(f"📊 Total tareas diarias: {len(daily_tasks)}")
    logger.info(f"📊 Total tareas continuas: {len(continuous_tasks)}")
    
    return daily_tasks, continuous_tasks


def test_task_verification():
    """Prueba la verificación de si las tareas deben ejecutarse"""
    logger = setup_logger('test_verification')
    logger.info("🔍 Probando verificación de tareas...")
    
    daily_tasks = get_all_daily_tasks()
    
    # Solo probar si es día laborable
    if not is_workday(date.today()):
        logger.info("📅 No es día laborable, omitiendo pruebas de verificación")
        return
    
    for task in daily_tasks:
        try:
            logger.info(f"🔍 Verificando {task.name}...")
            debe_ejecutarse = task.debe_ejecutarse()
            logger.info(f"  {'✅' if debe_ejecutarse else '⏭️ '} {task.name}: {'Debe ejecutarse' if debe_ejecutarse else 'No necesita ejecutarse'}")
            
        except Exception as e:
            logger.error(f"  ❌ Error verificando {task.name}: {e}")
        
        finally:
            # Cerrar conexiones
            try:
                task.close_connections()
            except:
                pass


def test_environment_variables():
    """Prueba que las variables de entorno estén configuradas"""
    logger = setup_logger('test_env')
    logger.info("🌍 Verificando variables de entorno...")
    
    required_vars = [
        'RIESGOS_TECNICOS_FRECUENCIA_DIAS',
        'RIESGOS_CALIDAD_SEMANAL_FRECUENCIA_DIAS',
        'RIESGOS_CALIDAD_MENSUAL_FRECUENCIA_DIAS',
        'BRASS_FRECUENCIA_DIAS',
        'EXPEDIENTES_FRECUENCIA_DIAS',
        'NO_CONFORMIDADES_DIAS_TAREA_CALIDAD',
        'NO_CONFORMIDADES_DIAS_TAREA_TECNICA',
        'AGEDYS_FRECUENCIA_DIAS'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"  ✅ {var} = {value}")
        else:
            logger.warning(f"  ⚠️  {var} no está definida (usando valor por defecto)")
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Variables faltantes: {missing_vars}")
    else:
        logger.info("✅ Todas las variables de entorno están configuradas")


def main():
    """Función principal de pruebas"""
    print("🧪 Iniciando pruebas de la nueva arquitectura de tareas")
    print("=" * 60)
    
    try:
        # Prueba 1: Inicialización
        print("\n1️⃣  Prueba de inicialización...")
        daily_tasks, continuous_tasks = test_task_initialization()
        
        # Prueba 2: Variables de entorno
        print("\n2️⃣  Prueba de variables de entorno...")
        test_environment_variables()
        
        # Prueba 3: Verificación de tareas
        print("\n3️⃣  Prueba de verificación de tareas...")
        test_task_verification()
        
        print("\n" + "=" * 60)
        print("✅ Pruebas completadas exitosamente")
        print(f"📊 Tareas diarias: {len(daily_tasks)}")
        print(f"📊 Tareas continuas: {len(continuous_tasks)}")
        print(f"📅 Es día laborable: {'Sí' if is_workday(date.today()) else 'No'}")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()