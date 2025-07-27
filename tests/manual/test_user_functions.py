#!/usr/bin/env python3
"""
Script de prueba para las funciones de usuarios comunes
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / '..' / '..' / 'src'))

from common.config import Config
from common.utils import (
    get_application_users, 
    get_quality_users, 
    get_technical_users, 
    get_admin_users
)
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_user_functions():
    """Prueba las funciones de usuarios"""
    try:
        # Cargar configuración
        config = Config()
        logger.info(f"Configuración cargada - Entorno: {config.environment}")
        
        # Obtener IDs de aplicaciones desde la configuración
        app_ids = config.get_all_app_ids()
        
        print("\n=== PRUEBA DE FUNCIONES DE USUARIOS ===\n")
        print(f"IDs de aplicaciones desde configuración: {app_ids}\n")
        
        # Probar usuarios de calidad para cada aplicación
        print("1. USUARIOS DE CALIDAD:")
        print("-" * 40)
        for app_name, app_id in app_ids.items():
            try:
                users = get_quality_users(app_id, config)
                print(f"{app_name} (ID: {app_id}): {len(users)} usuarios de calidad")
                for user in users[:3]:  # Mostrar solo los primeros 3
                    print(f"  - {user.get('NombreUsuario', 'N/A')} ({user.get('CorreoUsuario', 'N/A')})")
                if len(users) > 3:
                    print(f"  ... y {len(users) - 3} más")
                print()
            except Exception as e:
                print(f"{app_name} (ID: {app_id}): Error - {e}")
                print()
        
        # Probar usuarios técnicos para cada aplicación
        print("2. USUARIOS TÉCNICOS:")
        print("-" * 40)
        for app_name, app_id in app_ids.items():
            try:
                users = get_technical_users(app_id, config)
                print(f"{app_name} (ID: {app_id}): {len(users)} usuarios técnicos")
                for user in users[:3]:  # Mostrar solo los primeros 3
                    print(f"  - {user.get('NombreUsuario', 'N/A')} ({user.get('CorreoUsuario', 'N/A')})")
                if len(users) > 3:
                    print(f"  ... y {len(users) - 3} más")
                print()
            except Exception as e:
                print(f"{app_name} (ID: {app_id}): Error - {e}")
                print()
        
        # Probar usuarios administradores (no depende de aplicación)
        print("3. USUARIOS ADMINISTRADORES:")
        print("-" * 40)
        try:
            users = get_admin_users(config)
            print(f"Total: {len(users)} usuarios administradores")
            for user in users:
                print(f"  - {user.get('NombreUsuario', 'N/A')} ({user.get('CorreoUsuario', 'N/A')})")
            print()
        except Exception as e:
            print(f"Error obteniendo administradores: {e}")
            print()
        
        # Probar función genérica
        print("4. FUNCIÓN GENÉRICA get_application_users:")
        print("-" * 40)
        try:
            # Probar con diferentes tipos usando AGEDYS
            agedys_id = config.app_id_agedys
            for user_type in ['quality', 'technical', 'admin']:
                users = get_application_users(agedys_id, user_type, config)
                print(f"AGEDYS (ID: {agedys_id}) - {user_type}: {len(users)} usuarios")
            print()
        except Exception as e:
            print(f"Error en función genérica: {e}")
            print()
        
        # Probar métodos de configuración
        print("5. MÉTODOS DE CONFIGURACIÓN:")
        print("-" * 40)
        try:
            print(f"ID AGEDYS: {config.get_app_id('agedys')}")
            print(f"ID BRASS: {config.get_app_id('brass')}")
            print(f"ID No Conformidades: {config.get_app_id('noconformidades')}")
            print(f"ID Expedientes: {config.get_app_id('expedientes')}")
            print(f"Cadena conexión Lanzadera: {config.get_db_lanzadera_connection_string()[:50]}...")
            print()
        except Exception as e:
            print(f"Error en métodos de configuración: {e}")
            print()
        
        print("=== PRUEBA COMPLETADA ===")
        
    except Exception as e:
        logger.error(f"Error en la prueba: {e}")
        raise

if __name__ == "__main__":
    test_user_functions()