#!/usr/bin/env python3
"""
Script de prueba para verificar las funciones de usuario del módulo común.
"""

import sys
import logging
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from common.config import config
from common.utils import (
    get_technical_users,
    get_quality_users,
    get_user_email,
    get_technical_emails_string,
    get_quality_emails_string,
    get_admin_users,
    get_admin_emails_string
)

def setup_logging():
    """Configura el logging para las pruebas."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_user_functions():
    """Prueba las funciones de usuario."""
    logger = setup_logging()
    
    print("=== PRUEBA DE FUNCIONES DE USUARIO ===")
    print(f"Entorno: {config.environment}")
    print(f"ID Aplicación Riesgos: {config.app_id_riesgos}")
    print()
    
    # Crear conexión a la base de datos de tareas
    try:
        from common.database import AccessDatabase
        db_connection = AccessDatabase(config.get_db_tareas_connection_string())
        if not db_connection.connect():
            print("Error: No se pudo conectar a la base de datos de tareas")
            return
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return
    
    # Probar funciones de administradores
    print("1. Probando funciones de administradores...")
    try:
        admin_users = get_admin_users(db_connection)
        admin_emails = get_admin_emails_string(db_connection)
        
        print(f"   Usuarios admin encontrados: {len(admin_users)}")
        print(f"   Emails admin: {admin_emails}")
        
        for user in admin_users[:3]:  # Mostrar solo los primeros 3
            print(f"   - {user.get('Nombre', 'N/A')} ({user.get('CorreoUsuario', 'N/A')})")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Probar funciones técnicas
    print("2. Probando funciones técnicas...")
    try:
        technical_users = get_technical_users(str(config.app_id_riesgos), config, logger)
        technical_emails = get_technical_emails_string(str(config.app_id_riesgos), config, logger)
        
        print(f"   Usuarios técnicos encontrados: {len(technical_users)}")
        print(f"   Emails técnicos: {technical_emails}")
        
        for user in technical_users[:3]:  # Mostrar solo los primeros 3
            print(f"   - {user.get('Nombre', 'N/A')} ({user.get('CorreoUsuario', 'N/A')})")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Probar funciones de calidad
    print("3. Probando funciones de calidad...")
    try:
        quality_users = get_quality_users(str(config.app_id_riesgos), config, logger)
        quality_emails = get_quality_emails_string(str(config.app_id_riesgos), config, logger)
        
        print(f"   Usuarios de calidad encontrados: {len(quality_users)}")
        print(f"   Emails de calidad: {quality_emails}")
        
        for user in quality_users[:3]:  # Mostrar solo los primeros 3
            print(f"   - {user.get('Nombre', 'N/A')} ({user.get('CorreoUsuario', 'N/A')})")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Probar función de email individual
    print("4. Probando función de email individual...")
    try:
        # Intentar con algunos usuarios comunes
        test_users = ['admin', 'test', 'usuario1']
        
        for username in test_users:
            email = get_user_email(username, config, logger)
            if email:
                print(f"   Usuario '{username}': {email}")
            else:
                print(f"   Usuario '{username}': No encontrado")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Cerrar conexión
    try:
        db_connection.disconnect()
    except:
        pass
    
    print("=== FIN DE PRUEBAS ===")

if __name__ == "__main__":
    test_user_functions()