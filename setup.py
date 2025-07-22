#!/usr/bin/env python3
"""
Script de instalación y configuración rápida
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Script principal de instalación"""
    print("🐍 Sistema de Gestión de Tareas - Instalación")
    print("=" * 50)
    
    # Verificar Python
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        return 1
    
    print(f"✅ Python {sys.version} detectado")
    
    # Instalar dependencias
    print("\n📦 Instalando dependencias...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return 1
    
    # Verificar archivo .env
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Error: Archivo .env no encontrado")
        print("   Por favor, configura las variables de entorno en .env")
        return 1
    
    print("✅ Archivo .env encontrado")
    
    # Crear directorio de logs
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    print("✅ Directorio de logs creado")
    
    # Verificar estructura de directorios
    required_dirs = ['src', 'tests', 'dbs-locales', 'herramientas']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"⚠️  Advertencia: Directorio {dir_name} no encontrado")
    
    print("\n🎉 Instalación completada!")
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar tests unitarios: pytest tests/unit/ -v")
    print("   2. Ejecutar tests integración: pytest tests/integration/ -v -m integration")
    print("   3. Ejecutar BRASS: python run_brass.py")
    print("   4. Ver logs en: logs/brass.log")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
