#!/usr/bin/env python3
"""
Script para probar el pool de conexiones thread-safe con múltiples hilos
simulando el comportamiento de run_master.py
"""

import sys
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from common.config import config
from common.access_connection_pool import get_tareas_connection_pool
from correo_tareas.correo_tareas_manager import CorreoTareasManager

def test_concurrent_access(thread_id: int, num_operations: int = 5):
    """Simular acceso concurrente a la base de datos"""
    print(f"[Hilo {thread_id}] Iniciando prueba de concurrencia")
    
    try:
        # Crear instancia del manager (usa pool internamente)
        manager = CorreoTareasManager()
        
        for i in range(num_operations):
            print(f"[Hilo {thread_id}] Operación {i+1}/{num_operations}")
            
            # Obtener correos pendientes
            correos = manager.obtener_correos_pendientes()
            print(f"[Hilo {thread_id}] Encontrados {len(correos)} correos pendientes")
            
            # Simular una pequeña pausa
            time.sleep(0.1)
            
            # Si hay correos, intentar marcar uno como enviado y luego revertir
            if correos:
                correo = correos[0]
                id_correo = correo['IDCorreo']
                
                # Marcar como enviado
                manager._marcar_correo_enviado(id_correo, datetime.now())
                print(f"[Hilo {thread_id}] Correo {id_correo} marcado como enviado")
                
                # Revertir (marcar como pendiente)
                update_data = {"FechaEnvio": None}
                where_clause = f"IDCorreo = {id_correo}"
                success = manager.db_pool.update_record("TbCorreosEnviados", update_data, where_clause)
                if success:
                    print(f"[Hilo {thread_id}] Correo {id_correo} revertido a pendiente")
                
            time.sleep(0.1)
        
        print(f"[Hilo {thread_id}] Prueba completada exitosamente")
        return True
        
    except Exception as e:
        print(f"[Hilo {thread_id}] Error: {e}")
        return False

def test_pool_statistics():
    """Mostrar estadísticas del pool de conexiones"""
    connection_string = config.get_db_connection_string('tareas')
    pool = get_tareas_connection_pool(connection_string)
    
    stats = pool.get_stats()
    
    print("\n=== ESTADÍSTICAS DEL POOL ===")
    print(f"Conexiones en pool: {stats['pool_size']}")
    print(f"Total conexiones creadas: {stats['total_connections']}")
    print(f"Máximo de conexiones: {stats['max_connections']}")
    print(f"Conexiones reutilizadas: {stats['connections_reused']}")
    print(f"Operaciones completadas: {stats['operations_completed']}")
    print(f"Operaciones fallidas: {stats['operations_failed']}")
    print(f"Operaciones concurrentes actuales: {stats['concurrent_operations']}")
    print(f"Máximo concurrente alcanzado: {stats['max_concurrent']}")
    print("================================\n")

def main():
    print("=== PRUEBA DE POOL DE CONEXIONES THREAD-SAFE ===")
    print(f"Fecha/Hora: {datetime.now()}")
    print("=" * 50)
    
    # Mostrar estadísticas iniciales
    test_pool_statistics()
    
    # Configurar prueba concurrente
    num_threads = 3  # Simular el mismo número que run_master.py
    operations_per_thread = 3
    
    print(f"Ejecutando prueba con {num_threads} hilos concurrentes")
    print(f"Cada hilo realizará {operations_per_thread} operaciones")
    print("-" * 50)
    
    # Ejecutar prueba concurrente
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Enviar tareas a los hilos
        futures = []
        for i in range(num_threads):
            future = executor.submit(test_concurrent_access, i+1, operations_per_thread)
            futures.append(future)
        
        # Recoger resultados
        results = []
        for future in futures:
            try:
                result = future.result(timeout=30)  # 30 segundos timeout
                results.append(result)
            except Exception as e:
                print(f"Error en hilo: {e}")
                results.append(False)
    
    end_time = time.time()
    
    # Mostrar estadísticas finales
    test_pool_statistics()
    
    # Resumen de resultados
    print("=" * 50)
    print("RESUMEN DE RESULTADOS:")
    print(f"Tiempo total: {end_time - start_time:.2f} segundos")
    print(f"Hilos exitosos: {sum(results)}/{len(results)}")
    print(f"Hilos fallidos: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ TODAS LAS PRUEBAS PASARON - Pool funciona correctamente")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON - Revisar logs")
    
    print("=" * 50)

if __name__ == "__main__":
    main()