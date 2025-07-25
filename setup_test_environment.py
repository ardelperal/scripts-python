#!/usr/bin/env python3
"""
Script de configuración inicial para el entorno de testing.
Configura todo lo necesario para ejecutar las pruebas del proyecto.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
import shutil

def check_python_version():
    """Verificar versión de Python."""
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Verificar e instalar dependencias."""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        'pytest', 'pytest-cov', 'flask', 'pandas', 
        'pyodbc', 'python-dotenv', 'tabulate'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - No encontrado")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Instalando paquetes faltantes: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✅ Dependencias instaladas correctamente")
        except subprocess.CalledProcessError:
            print("❌ Error instalando dependencias")
            return False
    
    return True

def setup_test_directories():
    """Crear estructura de directorios de testing."""
    print("\n📁 Configurando estructura de directorios...")
    
    directories = [
        'tests',
        'tests/unit',
        'tests/integration', 
        'tests/emails',
        'tests/fixtures',
        'tests/data',
        'htmlcov',
        'test_reports'
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Creado: {directory}")
        else:
            print(f"✅ Existe: {directory}")

def setup_test_database():
    """Configurar base de datos de pruebas."""
    print("\n🗄️  Configurando base de datos de pruebas...")
    
    test_db_path = "tests/data/test_database.db"
    
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
        
        # Crear base de datos de pruebas
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Crear tabla de prueba
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TbCorreosEnviados (
                IDCorreo INTEGER PRIMARY KEY AUTOINCREMENT,
                URLAdjunto TEXT,
                Aplicacion TEXT,
                Originador TEXT,
                Destinatarios TEXT,
                Asunto TEXT,
                Cuerpo TEXT,
                FechaEnvio DATETIME,
                Observaciones TEXT,
                NDPD TEXT,
                NPEDIDO TEXT,
                NFACTURA TEXT,
                FechaGrabacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                CuerpoHTML TEXT,
                IDEdicion INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Base de datos de pruebas creada: {test_db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        return False

def check_docker():
    """Verificar disponibilidad de Docker para MailHog."""
    print("\n🐳 Verificando Docker...")
    
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            
            # Verificar si MailHog está corriendo
            result = subprocess.run(['docker', 'ps'], 
                                  capture_output=True, text=True)
            if 'mailhog' in result.stdout.lower():
                print("✅ MailHog está ejecutándose")
            else:
                print("⚠️  MailHog no está ejecutándose")
                print("   Ejecuta: docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog")
            
            return True
    except FileNotFoundError:
        print("❌ Docker no está instalado o no está en PATH")
        return False

def create_test_config():
    """Crear archivo de configuración para tests."""
    print("\n⚙️  Creando configuración de tests...")
    
    config_content = '''# Configuración para tests
import os
from pathlib import Path

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "data"
TEST_DB_PATH = TEST_DATA_DIR / "test_database.db"

# Configuración de email para tests
SMTP_CONFIG = {
    "host": "localhost",
    "port": 1025,
    "use_tls": False,
    "username": None,
    "password": None
}

# Configuración de base de datos para tests
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

# Configuración de cobertura
COVERAGE_THRESHOLD = 80
'''
    
    config_path = "tests/config.py"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Configuración creada: {config_path}")

def create_conftest():
    """Crear archivo conftest.py para pytest."""
    print("\n🔧 Creando conftest.py...")
    
    conftest_content = '''"""
Configuración global para pytest.
"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

@pytest.fixture(scope="session")
def test_db():
    """Fixture para base de datos de pruebas."""
    db_path = "tests/data/test_database.db"
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Crear conexión
    conn = sqlite3.connect(db_path)
    
    # Crear tabla si no existe
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TbCorreosEnviados (
            IDCorreo INTEGER PRIMARY KEY AUTOINCREMENT,
            URLAdjunto TEXT,
            Aplicacion TEXT,
            Originador TEXT,
            Destinatarios TEXT,
            Asunto TEXT,
            Cuerpo TEXT,
            FechaEnvio DATETIME,
            Observaciones TEXT,
            NDPD TEXT,
            NPEDIDO TEXT,
            NFACTURA TEXT,
            FechaGrabacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            CuerpoHTML TEXT,
            IDEdicion INTEGER
        )
    """)
    conn.commit()
    
    yield conn
    
    conn.close()

@pytest.fixture
def clean_db(test_db):
    """Fixture para limpiar la base de datos antes de cada test."""
    cursor = test_db.cursor()
    cursor.execute("DELETE FROM TbCorreosEnviados")
    test_db.commit()
    yield test_db

@pytest.fixture
def smtp_config():
    """Configuración SMTP para tests."""
    return {
        "host": "localhost",
        "port": 1025,
        "use_tls": False,
        "username": None,
        "password": None
    }
'''
    
    conftest_path = "tests/conftest.py"
    with open(conftest_path, 'w', encoding='utf-8') as f:
        f.write(conftest_content)
    
    print(f"✅ conftest.py creado: {conftest_path}")

def run_initial_tests():
    """Ejecutar tests iniciales para verificar configuración."""
    print("\n🧪 Ejecutando tests iniciales...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', '-v', '--tb=short'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests iniciales pasaron correctamente")
            print(result.stdout)
        else:
            print("⚠️  Algunos tests fallaron:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        return False

def main():
    """Función principal de configuración."""
    print("🚀 Configurando entorno de testing para scripts-python")
    print("=" * 60)
    
    success = True
    
    # Verificaciones y configuraciones
    success &= check_python_version()
    success &= check_dependencies()
    
    setup_test_directories()
    success &= setup_test_database()
    check_docker()  # No es crítico
    
    create_test_config()
    create_conftest()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Entorno de testing configurado correctamente!")
        print("\nComandos disponibles:")
        print("  python run_tests.py              # Ejecutar todos los tests")
        print("  python run_tests.py --unit       # Solo tests unitarios")
        print("  python run_tests.py --emails     # Solo tests de email")
        print("  python run_tests.py --coverage   # Con reporte detallado")
        print("  python run_tests.py --html       # Generar reporte HTML")
        print("\nPuedes también usar pytest directamente:")
        print("  pytest tests/ -v --cov=src")
        
        # Ejecutar tests iniciales
        run_initial_tests()
        
    else:
        print("\n❌ Hubo errores en la configuración. Revisa los mensajes anteriores.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())