#!/usr/bin/env python3
"""
Script de instalación y configuración rápida
Soporta instalación nativa y con Docker
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_docker():
    """Verificar si Docker está disponible"""
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_docker_compose():
    """Verificar si Docker Compose está disponible"""
    try:
        subprocess.run(['docker-compose', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Probar docker compose (nueva sintaxis)
        try:
            subprocess.run(['docker', 'compose', 'version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

def setup_native():
    """Configuración nativa (sin Docker)"""
    print("\n🐍 Configuración Nativa")
    print("=" * 30)
    
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
        print("   Por favor, copia .env.example a .env y configura las variables")
        print("   cp .env.example .env")
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
    
    return 0

def setup_docker():
    """Configuración con Docker"""
    print("\n🐳 Configuración Docker")
    print("=" * 25)
    
    # Verificar .env
    env_file = Path('.env')
    if not env_file.exists():
        print("🔧 Creando archivo .env desde plantilla...")
        env_example = Path('.env.example')
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✅ Archivo .env creado (revisa la configuración)")
        else:
            print("❌ Error: .env.example no encontrado")
            return 1
    
    # Construir imágenes
    print("\n🏗️  Construyendo imágenes Docker...")
    try:
        subprocess.run(['docker-compose', 'build'], check=True)
        print("✅ Imágenes Docker construidas")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error construyendo imágenes: {e}")
        return 1
    
    return 0

def show_docker_help():
    """Mostrar ayuda para Docker"""
    print("\n🐳 Comandos Docker disponibles:")
    print("   • docker-run.sh start     - Iniciar sistema")
    print("   • docker-run.sh test      - Ejecutar tests")
    print("   • docker-run.sh panel     - Abrir panel web")
    print("   • docker-run.sh help      - Ver todos los comandos")
    print("\n   En Windows: usar docker-run.bat en lugar de docker-run.sh")

def show_native_help():
    """Mostrar ayuda para instalación nativa"""
    print("\n🐍 Comandos nativos disponibles:")
    print("   • python server.py        - Iniciar panel web")
    print("   • python run_brass.py     - Ejecutar BRASS")
    print("   • pytest tests/ -v        - Ejecutar tests")
    print("   • pytest --cov=src        - Tests con cobertura")

def main():
    """Script principal de instalación"""
    print("🚀 Sistema de Gestión de Tareas - Instalación")
    print("=" * 50)
    
    # Detectar capacidades del sistema
    has_docker = check_docker()
    has_compose = check_docker_compose()
    
    print("\n🔍 Detección del entorno:")
    print(f"   Docker: {'✅ Disponible' if has_docker else '❌ No disponible'}")
    print(f"   Docker Compose: {'✅ Disponible' if has_compose else '❌ No disponible'}")
    
    # Ofrecer opciones de instalación
    if has_docker and has_compose:
        print("\n🎯 Opciones de instalación:")
        print("   1. Docker (Recomendado) - Más fácil y consistente")
        print("   2. Nativo - Instalación tradicional en el sistema")
        print("   3. Ambos - Configurar Docker + instalación nativa")
        
        while True:
            choice = input("\nSelecciona una opción (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                break
            print("❌ Opción inválida. Selecciona 1, 2 o 3.")
        
        if choice == '1':
            result = setup_docker()
            if result == 0:
                show_docker_help()
        elif choice == '2':
            result = setup_native()
            if result == 0:
                show_native_help()
        elif choice == '3':
            result1 = setup_docker()
            result2 = setup_native()
            result = max(result1, result2)
            if result == 0:
                print("\n✅ Configuración completa - Docker y Nativo disponibles")
                show_docker_help()
                show_native_help()
    else:
        print("\n⚠️  Docker no disponible, configurando instalación nativa...")
        result = setup_native()
        if result == 0:
            show_native_help()
            if not has_docker:
                print("\n💡 Sugerencia: Instala Docker para una experiencia mejorada:")
                print("   https://docs.docker.com/get-docker/")
    
    if result == 0:
        print("\n🎉 Instalación completada!")
        print("\n🌐 Para acceder al panel web:")
        if has_docker and has_compose:
            print("   Docker: ./docker-run.sh start && ./docker-run.sh panel")
        print("   Nativo: python server.py (luego http://localhost:8888)")
    
    return result

if __name__ == "__main__":
    sys.exit(main())
