#!/usr/bin/env python3
"""
Demostración de cómo usar la configuración SMTP alternativa
cuando no se puede acceder al servidor de oficina.
"""

import os
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def demo_smtp_override():
    """Demuestra cómo usar la configuración SMTP alternativa"""
    
    print("=== Demostración de Configuración SMTP Alternativa ===\n")
    
    # Importar después de configurar el path
    from common.config import config, reload_config
    
    # Mostrar configuración actual
    print("1. Configuración SMTP actual:")
    print(f"   Entorno: {config.environment}")
    print(f"   Servidor SMTP: {config.smtp_server}")
    print(f"   Puerto SMTP: {config.smtp_port}")
    print(f"   Usuario SMTP: '{config.smtp_user}'")
    print(f"   Autenticación: {config.smtp_auth}")
    print(f"   TLS: {config.smtp_tls}")
    print()
    
    # Configurar SMTP alternativo
    print("2. Configurando SMTP alternativo...")
    os.environ['SMTP_OVERRIDE_SERVER'] = 'localhost'
    os.environ['SMTP_OVERRIDE_PORT'] = '1025'
    os.environ['SMTP_OVERRIDE_USER'] = 'test@example.com'
    os.environ['SMTP_OVERRIDE_PASSWORD'] = 'testpass'
    os.environ['SMTP_OVERRIDE_TLS'] = 'false'
    
    # Recargar configuración
    reload_config()
    
    # Reimportar para obtener la nueva configuración
    from common.config import config as new_config
    
    print("3. Nueva configuración SMTP (con override):")
    print(f"   Entorno: {new_config.environment}")
    print(f"   Servidor SMTP: {new_config.smtp_server}")
    print(f"   Puerto SMTP: {new_config.smtp_port}")
    print(f"   Usuario SMTP: '{new_config.smtp_user}'")
    print(f"   Autenticación: {new_config.smtp_auth}")
    print(f"   TLS: {new_config.smtp_tls}")
    print()
    
    # Limpiar variables de entorno
    print("4. Limpiando variables de override...")
    for key in ['SMTP_OVERRIDE_SERVER', 'SMTP_OVERRIDE_PORT', 'SMTP_OVERRIDE_USER', 
                'SMTP_OVERRIDE_PASSWORD', 'SMTP_OVERRIDE_TLS']:
        if key in os.environ:
            del os.environ[key]
    
    # Recargar configuración original
    reload_config()
    from common.config import config as original_config
    
    print("5. Configuración restaurada:")
    print(f"   Entorno: {original_config.environment}")
    print(f"   Servidor SMTP: {original_config.smtp_server}")
    print(f"   Puerto SMTP: {original_config.smtp_port}")
    print(f"   Usuario SMTP: '{original_config.smtp_user}'")
    print(f"   Autenticación: {original_config.smtp_auth}")
    print(f"   TLS: {original_config.smtp_tls}")
    print()
    
    print("6. Instrucciones para uso permanente:")
    print("   Para usar un servidor SMTP alternativo de forma permanente,")
    print("   descomenta y configura estas líneas en tu archivo .env:")
    print()
    print("   SMTP_OVERRIDE_SERVER=tu_servidor_smtp")
    print("   SMTP_OVERRIDE_PORT=587")
    print("   SMTP_OVERRIDE_USER=tu_usuario@gmail.com")
    print("   SMTP_OVERRIDE_PASSWORD=tu_contraseña")
    print("   SMTP_OVERRIDE_TLS=true")
    print()
    print("   Esto sobrescribirá la configuración SMTP por defecto")
    print("   independientemente del entorno (local/oficina).")


if __name__ == "__main__":
    demo_smtp_override()