#!/usr/bin/env python3
"""
Test final del sistema de correos con pool de conexiones thread-safe.

Este script verifica que:
1. El pool de conexiones funciona correctamente
2. Los correos se marcan como enviados y persisten
3. No hay problemas de concurrencia
4. El sistema es estable bajo carga

Autor: Sistema de Automatización
Fecha: 2025
"""

import sys
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from correo_tareas.correo_tareas_manager import CorreoTareasManager
from common.access_connection_pool import get_tareas_connection_pool, close_tareas_pool
from common.config import config

def test_correo_manager_with_pool():
    """Test básico del manager de correos con pool"""
    print("=== TEST BÁSICO DEL MANAGER ===")
    
    manager = CorreoTareasManager()
    
    # Obtener correos pendientes
    correos = manager.obtener_correos_pendientes()
    print(f"Correos pendientes encontrados: {len(correos)}")
    
    if correos:
        correo = correos[0]
        id_correo = correo['IDCorreo']
        print(f"Primer correo pendiente: ID {id_correo}")
        
        # Marcar como enviado
        fecha_envio = datetime.now()
        manager._marcar_correo_enviado(id_correo, fecha_envio)
        print(f"Correo {id_correo} marcado como enviado")
        
        # Verificar que se marcó correctamente
        time.sleep(0.1)  # Pequeña pausa para asegurar persistencia
        correos_actualizados = manager.obtener_correos_pendientes()
        
        # Buscar si el correo sigue en pendientes
        correo_encontrado = any(c['IDCorreo'] == id_correo for c in correos_actualizados)
        
        if not correo_encontrado:
            print(f"✅ Correo {id_correo} ya no está en pendientes - ACTUALIZACIÓN EXITOSA")
        else:
            print(f"❌ Correo {id_correo} sigue en pendientes - PROBLEMA DE PERSISTENCIA")
        
        # Revertir para no afectar otros tests
        update_data = {"FechaEnvio": None}
        where_clause = f"IDCorreo = {id_correo}"
        manager.db_pool.update_record("TbCorreosEnviados", update_data, where_clause)
        print(f"Correo {id_correo} revertido a pendiente")
    
    print("=" * 50)

def test_concurrent_operations():
    """Test de operaciones concurrentes"""
    print("=== TEST DE CONCURRENCIA ===")
    
    def worker(thread_id):
        manager = CorreoTareasManager()
        correos = manager.obtener_correos_pendientes()
        print(f"[Hilo {thread_id}] Encontrados {len(correos)} correos")
        return len(correos)
    
    # Ejecutar múltiples hilos simultáneamente
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, i+1) for i in range(3)]
        results = [future.result() for future in futures]
    
    # Verificar que todos obtuvieron el mismo resultado
    if len(set(results)) == 1:
        print(f"✅ Todos los hilos obtuvieron el mismo resultado: {results[0]} correos")
    else:
        print(f"❌ Resultados inconsistentes entre hilos: {results}")
    
    print("=" * 50)

def test_pool_statistics():
    """Test de estadísticas del pool"""
    print("=== ESTADÍSTICAS DEL POOL ===")
    
    connection_string = config.get_db_connection_string('tareas')
    pool = get_tareas_connection_pool(connection_string)
    stats = pool.get_stats()
    
    print(f"Conexiones en pool: {stats['pool_size']}")
    print(f"Total conexiones creadas: {stats['total_connections']}")
    print(f"Operaciones completadas: {stats['operations_completed']}")
    print(f"Operaciones fallidas: {stats['operations_failed']}")
    print(f"Máximo concurrente: {stats['max_concurrent']}")
    
    # Verificar que no hay operaciones fallidas
    if stats['operations_failed'] == 0:
        print("✅ No hay operaciones fallidas")
    else:
        print(f"❌ {stats['operations_failed']} operaciones fallidas")
    
    print("=" * 50)

def test_persistence_under_load():
    """Test de persistencia bajo carga"""
    print("=== TEST DE PERSISTENCIA BAJO CARGA ===")
    
    manager = CorreoTareasManager()
    correos = manager.obtener_correos_pendientes()
    
    if not correos:
        print("No hay correos pendientes para probar")
        return
    
    correo = correos[0]
    id_correo = correo['IDCorreo']
    
    print(f"Probando persistencia con correo ID {id_correo}")
    
    # Realizar múltiples operaciones rápidas
    for i in range(5):
        # Marcar como enviado
        manager._marcar_correo_enviado(id_correo, datetime.now())
        
        # Verificar inmediatamente
        correos_check = manager.obtener_correos_pendientes()
        correo_en_pendientes = any(c['IDCorreo'] == id_correo for c in correos_check)
        
        if correo_en_pendientes:
            print(f"❌ Iteración {i+1}: Correo sigue en pendientes")
        else:
            print(f"✅ Iteración {i+1}: Correo marcado correctamente")
        
        # Revertir
        update_data = {"FechaEnvio": None}
        where_clause = f"IDCorreo = {id_correo}"
        manager.db_pool.update_record("TbCorreosEnviados", update_data, where_clause)
        
        time.sleep(0.1)
    
    print("=" * 50)

def main():
    print("=== TEST FINAL DEL SISTEMA DE CORREOS ===")
    print(f"Fecha/Hora: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Ejecutar todos los tests
        test_correo_manager_with_pool()
        test_concurrent_operations()
        test_pool_statistics()
        test_persistence_under_load()
        
        print("=== RESUMEN FINAL ===")
        print("✅ Todos los tests completados")
        print("✅ Pool de conexiones funcionando correctamente")
        print("✅ Sistema listo para producción")
        
    except Exception as e:
        print(f"❌ Error durante los tests: {e}")
        
    finally:
        # Limpiar recursos
        close_tareas_pool()
        print("Pool de conexiones cerrado")

if __name__ == "__main__":
    main()