#!/usr/bin/env python3
"""
Script de prueba para la migración de AGEDYS
"""

import sys
import os
from pathlib import Path

# Añadir el directorio src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from common.logger import setup_logger
from agedys.agedys_task import AgedysTask
from agedys.agedys_manager import AgedysManager

def test_agedys_task():
    """Prueba la clase AgedysTask"""
    print("=== Probando AgedysTask ===")
    
    task = AgedysTask()
    print(f"Nombre de tarea: {task.name}")
    print(f"Script: {task.script_filename}")
    print(f"Debe ejecutarse hoy: {task.debe_ejecutarse()}")
    
    task.close_connections()
    print("AgedysTask - Prueba completada")

def test_agedys_manager_new():
    """Prueba la clase AgedysManager"""
    print("\n=== Probando AgedysManager ===")
    try:
        manager = AgedysManager()
        print(f"Nombre de tarea: {manager.name}")
        print(f"Script: {manager.script_filename}")
        print(f"Frecuencia: {manager.frequency_days} días")
        print(f"Debe ejecutarse hoy: {manager.debe_ejecutarse()}")
        
        # Probar obtención de usuarios
        print("Obteniendo usuarios con facturas pendientes...")
        try:
            usuarios = manager.get_usuarios_facturas_pendientes_visado_tecnico()
            print(f"Usuarios encontrados: {len(usuarios)}")
            
            # Mostrar algunos usuarios si los hay
            if usuarios:
                for i, usuario in enumerate(usuarios[:3]):  # Mostrar máximo 3
                    print(f"  Usuario {i+1}: {usuario.get('UsuarioRed', 'N/A')} - {usuario.get('CorreoUsuario', 'N/A')}")
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
        
        # Probar obtención de emails de administradores
        print("Obteniendo emails de administradores...")
        try:
            admin_emails = manager.get_admin_emails()
            print(f"Emails admin: {admin_emails[:50]}...")  # Mostrar solo los primeros 50 caracteres
        except Exception as e:
            print(f"Error obteniendo emails admin: {e}")
        
        manager.close_connections()
        print("AgedysManager - Prueba completada")
    except Exception as e:
        print(f"Error en AgedysManager: {e}")
        import traceback
        traceback.print_exc()

def test_agedys_full_execution():
    """Prueba la ejecución completa de AGEDYS"""
    print("\n=== Probando ejecución completa de AGEDYS ===")
    
    # Preguntar al usuario si quiere ejecutar la prueba completa
    response = input("¿Deseas ejecutar la prueba completa de AGEDYS? (s/n): ").lower().strip()
    if response != 's':
        print("Prueba completa omitida")
        return
    
    manager = AgedysManager()
    
    if not manager.debe_ejecutarse():
        print("La tarea no debe ejecutarse hoy según la lógica de negocio")
        print("Ejecutando de todas formas para prueba...")
    
    try:
        success = manager.run()
        if success:
            print("Resultado de ejecución: Éxito")
        else:
            print("Resultado de ejecución: Fallo")
    except Exception as e:
        print(f"Error en ejecución: {e}")
    
    manager.close_connections()
    print("Ejecución completa - Prueba completada")

def main():
    """Función principal"""
    # Configurar logging
    logger = setup_logger(name="test_agedys_migration")
    
    print("Iniciando pruebas de migración de AGEDYS")
    print("=" * 50)
    
    try:
        test_agedys_task()
        test_agedys_manager_new()
        test_agedys_full_execution()
        
        print("\n" + "=" * 50)
        print("Pruebas de migración de AGEDYS completadas")
        
    except Exception as e:
        print(f"Error en las pruebas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()