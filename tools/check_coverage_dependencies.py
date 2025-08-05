#!/usr/bin/env python3
"""
Script para verificar dependencias de coverage y diagnosticar problemas
"""
import subprocess
import sys
import os
from pathlib import Path

def check_python_environment():
    """Verifica el entorno de Python"""
    print("🐍 Verificando entorno de Python...")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python version: {sys.version}")
    print(f"   Working directory: {os.getcwd()}")
    
    # Verificar si estamos en un entorno virtual
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("   ✅ Entorno virtual detectado")
    else:
        print("   ⚠️  No se detectó entorno virtual")
    
    return True

def check_coverage_installation():
    """Verifica si coverage está instalado"""
    print("\n📊 Verificando instalación de coverage...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "coverage", "--version"
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"   ✅ Coverage instalado: {result.stdout.strip()}")
            return True
        else:
            print("   ❌ Coverage no está instalado o no funciona correctamente")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error verificando coverage: {e}")
        return False

def check_pytest_installation():
    """Verifica si pytest está instalado"""
    print("\n🧪 Verificando instalación de pytest...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "--version"
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"   ✅ Pytest instalado: {result.stdout.strip()}")
            return True
        else:
            print("   ❌ Pytest no está instalado o no funciona correctamente")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error verificando pytest: {e}")
        return False

def check_project_structure():
    """Verifica la estructura del proyecto"""
    print("\n📁 Verificando estructura del proyecto...")
    
    required_paths = [
        "src",
        "tests",
        "tests/unit",
        "requirements.txt"
    ]
    
    all_good = True
    for path in required_paths:
        if Path(path).exists():
            print(f"   ✅ {path}")
        else:
            print(f"   ❌ {path} no encontrado")
            all_good = False
    
    return all_good

def install_missing_dependencies():
    """Instala dependencias faltantes"""
    print("\n📦 Instalando dependencias faltantes...")
    
    try:
        # Instalar coverage y pytest
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "coverage", "pytest"
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print("   ✅ Dependencias instaladas correctamente")
            return True
        else:
            print("   ❌ Error instalando dependencias:")
            print(f"   {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error instalando dependencias: {e}")
        return False

def run_simple_coverage_test():
    """Ejecuta una prueba simple de coverage"""
    print("\n🔬 Ejecutando prueba simple de coverage...")
    
    try:
        # Crear un archivo de prueba simple
        test_content = '''
def test_simple():
    assert True
'''
        
        with open("test_simple_temp.py", "w") as f:
            f.write(test_content)
        
        # Ejecutar coverage en el archivo de prueba
        result = subprocess.run([
            sys.executable, "-m", "coverage", "run", "-m", "pytest", "test_simple_temp.py", "-v"
        ], capture_output=True, text=True, shell=True)
        
        # Limpiar archivo temporal
        if Path("test_simple_temp.py").exists():
            Path("test_simple_temp.py").unlink()
        
        if result.returncode == 0:
            print("   ✅ Prueba simple de coverage exitosa")
            return True
        else:
            print("   ❌ Error en prueba simple de coverage:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en prueba simple: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Diagnóstico de Coverage")
    print("=" * 40)
    
    checks = [
        ("Entorno Python", check_python_environment),
        ("Coverage", check_coverage_installation),
        ("Pytest", check_pytest_installation),
        ("Estructura del proyecto", check_project_structure),
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
    
    if not all_passed:
        print("\n🔧 Intentando reparar problemas...")
        if install_missing_dependencies():
            print("\n🔄 Reejecutando verificaciones...")
            check_coverage_installation()
            check_pytest_installation()
    
    # Prueba final
    if run_simple_coverage_test():
        print("\n✨ ¡Todo parece estar funcionando correctamente!")
        print("\n💡 Ahora puedes ejecutar:")
        print("   python tools/generate_coverage_report.py")
    else:
        print("\n❌ Aún hay problemas. Posibles soluciones:")
        print("   1. Ejecuta como administrador")
        print("   2. Verifica que estés en el directorio correcto del proyecto")
        print("   3. Reinstala el entorno virtual:")
        print("      python -m venv .venv")
        print("      .venv\\Scripts\\activate")
        print("      pip install -r requirements.txt")