#!/usr/bin/env python3
"""
Ejemplo de uso de la configuración SMTP para diferentes entornos
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from common.config import config

def demo_smtp_config():
    """Demostrar la configuración SMTP según el entorno"""
    
    print("=== Configuración SMTP ===")
    print(f"Entorno: {config.environment}")
    print(f"Servidor SMTP: {config.smtp_server}")
    print(f"Puerto SMTP: {config.smtp_port}")
    print(f"Usuario SMTP: {config.smtp_user if config.smtp_user else '(sin usuario)'}")
    print(f"Contraseña SMTP: {'***' if config.smtp_password else '(sin contraseña)'}")
    print(f"Autenticación: {config.smtp_auth}")
    print(f"TLS: {config.smtp_tls}")
    print()
    
    # Explicar las diferencias entre entornos
    if config.environment == 'local':
        print("📧 ENTORNO LOCAL:")
        print("- Usa servidor SMTP local (localhost:1025) para desarrollo")
        print("- Requiere usuario/contraseña para autenticación")
        print("- Ideal para testing con herramientas como MailHog o similar")
    else:
        print("📧 ENTORNO OFICINA:")
        print("- Usa servidor SMTP corporativo (10.73.54.85:25)")
        print("- NO requiere autenticación (usuario/contraseña vacíos)")
        print("- Envío directo a través del servidor de la empresa")
        print("- Configuración basada en el script VBS legacy")
    
    print()
    print("=== Configuración de Base de Datos ===")
    print(f"BD BRASS: {config.db_brass_path}")
    print(f"BD Tareas: {config.db_tareas_path}")
    print(f"BD Correos: {config.db_correos_path}")
    print()
    
    print("=== Otros Archivos ===")
    print(f"Archivo CSS: {config.css_file_path}")
    print(f"Directorio logs: {config.logs_dir}")
    print(f"Destinatario por defecto: {config.default_recipient}")

if __name__ == "__main__":
    demo_smtp_config()