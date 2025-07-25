#!/usr/bin/env python3
"""
Configurador del Entorno de Testing
===================================

Este script configura y valida el entorno de testing, incluyendo:
- Instalación de dependencias de testing
- Configuración de bases de datos de prueba
- Validación de estructura de tests
- Creación de datos de prueba
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestEnvironmentSetup:
    """Configurador del entorno de testing"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_db_path = self.project_root / "dbs-sqlite" / "correos_datos.sqlite"
        
    def print_step(self, step: str, status: str = "info"):
        """Imprimir paso con formato"""
        if status == "success":
            icon = "✅"
            color = Colors.GREEN
        elif status == "error":
            icon = "❌"
            color = Colors.RED
        elif status == "warning":
            icon = "⚠️"
            color = Colors.YELLOW
        else:
            icon = "🔧"
            color = Colors.BLUE
            
        print(f"{color}{icon} {step}{Colors.END}")
    
    def check_dependencies(self) -> bool:
        """Verificar dependencias de testing"""
        self.print_step("Verificando dependencias de testing...")
        
        required_packages = [
            'pytest',
            'pytest-cov',
            'pytest-mock',
            'pytest-flask'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.print_step(f"  {package}: Instalado", "success")
            except ImportError:
                missing_packages.append(package)
                self.print_step(f"  {package}: No encontrado", "error")
        
        if missing_packages:
            self.print_step(f"Instalando paquetes faltantes: {', '.join(missing_packages)}")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install"
                ] + missing_packages, check=True)
                self.print_step("Dependencias instaladas correctamente", "success")
                return True
            except subprocess.CalledProcessError:
                self.print_step("Error instalando dependencias", "error")
                return False
        else:
            self.print_step("Todas las dependencias están instaladas", "success")
            return True
    
    def setup_test_databases(self) -> bool:
        """Configurar bases de datos de prueba"""
        self.print_step("Configurando bases de datos de prueba...")
        
        # Crear directorio de bases de datos si no existe
        db_dir = self.project_root / "dbs-sqlite"
        db_dir.mkdir(exist_ok=True)
        
        # Configurar base de datos de correos
        if not self.test_db_path.exists():
            self.print_step("Creando base de datos de correos de prueba...")
            self._create_emails_test_db()
        else:
            self.print_step("Base de datos de correos ya existe", "success")
        
        # Verificar estructura de la base de datos
        if self._verify_db_structure():
            self.print_step("Estructura de base de datos verificada", "success")
            return True
        else:
            self.print_step("Error en estructura de base de datos", "error")
            return False
    
    def _create_emails_test_db(self) -> None:
        """Crear base de datos de correos de prueba"""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Crear tabla TbCorreosEnviados con estructura real
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS TbCorreosEnviados (
                    IDCorreo INTEGER PRIMARY KEY AUTOINCREMENT,
                    URLAdjunto TEXT,
                    Aplicacion TEXT NOT NULL,
                    Originador TEXT,
                    Destinatarios TEXT,
                    DestinatariosConCopia TEXT,
                    DestinatariosConCopiaOculta TEXT,
                    Asunto TEXT NOT NULL,
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
    
    def _verify_db_structure(self) -> bool:
        """Verificar estructura de la base de datos"""
        try:
            with sqlite3.connect(self.test_db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que existe la tabla
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='TbCorreosEnviados'
                """)
                
                if not cursor.fetchone():
                    return False
                
                # Verificar columnas principales
                cursor.execute("PRAGMA table_info(TbCorreosEnviados)")
                columns = [row[1] for row in cursor.fetchall()]
                
                required_columns = [
                    'IDCorreo', 'Aplicacion', 'Destinatarios', 
                    'Asunto', 'Cuerpo', 'FechaEnvio', 'FechaGrabacion'
                ]
                
                for col in required_columns:
                    if col not in columns:
                        self.print_step(f"Columna faltante: {col}", "error")
                        return False
                
                return True
                
        except Exception as e:
            self.print_step(f"Error verificando base de datos: {e}", "error")
            return False
    
    def validate_test_structure(self) -> bool:
        """Validar estructura de directorios de tests"""
        self.print_step("Validando estructura de tests...")
        
        required_dirs = [
            "tests",
            "tests/unit",
            "tests/integration", 
            "tests/emails",
            "tests/unit/common",
            "tests/unit/brass"
        ]
        
        missing_dirs = []
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                self.print_step(f"  {dir_path}: Existe", "success")
            else:
                missing_dirs.append(dir_path)
                self.print_step(f"  {dir_path}: No encontrado", "warning")
        
        # Crear directorios faltantes
        for dir_path in missing_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Crear __init__.py si es necesario
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
            
            self.print_step(f"  {dir_path}: Creado", "success")
        
        return True
    
    def create_sample_tests(self) -> bool:
        """Crear tests de ejemplo si no existen"""
        self.print_step("Verificando tests de ejemplo...")
        
        # Test unitario de ejemplo
        unit_test_path = self.project_root / "tests" / "unit" / "test_example.py"
        if not unit_test_path.exists():
            self._create_example_unit_test(unit_test_path)
            self.print_step("Test unitario de ejemplo creado", "success")
        
        # Test de integración de ejemplo
        integration_test_path = self.project_root / "tests" / "integration" / "test_example_integration.py"
        if not integration_test_path.exists():
            self._create_example_integration_test(integration_test_path)
            self.print_step("Test de integración de ejemplo creado", "success")
        
        return True
    
    def _create_example_unit_test(self, path: Path) -> None:
        """Crear test unitario de ejemplo"""
        content = '''#!/usr/bin/env python3
"""
Test unitario de ejemplo
"""
import pytest
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def test_basic_math():
    """Test básico de matemáticas"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12

def test_string_operations():
    """Test de operaciones con strings"""
    text = "Hello World"
    assert text.upper() == "HELLO WORLD"
    assert text.lower() == "hello world"
    assert len(text) == 11

def test_list_operations():
    """Test de operaciones con listas"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
])
def test_double_function(input, expected):
    """Test parametrizado"""
    def double(x):
        return x * 2
    
    assert double(input) == expected

class TestExampleClass:
    """Clase de tests de ejemplo"""
    
    def test_setup_method(self):
        """Test con setup"""
        self.data = {"key": "value"}
        assert "key" in self.data
        assert self.data["key"] == "value"
    
    def test_fixture_usage(self):
        """Test usando fixture"""
        # Este test demuestra el uso básico
        assert True
'''
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_example_integration_test(self, path: Path) -> None:
        """Crear test de integración de ejemplo"""
        content = '''#!/usr/bin/env python3
"""
Test de integración de ejemplo
"""
import pytest
import sqlite3
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

@pytest.mark.integration
def test_database_connection():
    """Test de conexión a base de datos"""
    db_path = Path(__file__).parent.parent.parent / "dbs-sqlite" / "correos_datos.sqlite"
    
    if not db_path.exists():
        pytest.skip("Base de datos de prueba no encontrada")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        assert len(tables) > 0, "No se encontraron tablas en la base de datos"

@pytest.mark.integration
def test_email_table_structure():
    """Test de estructura de tabla de correos"""
    db_path = Path(__file__).parent.parent.parent / "dbs-sqlite" / "correos_datos.sqlite"
    
    if not db_path.exists():
        pytest.skip("Base de datos de prueba no encontrada")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Verificar que existe la tabla
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='TbCorreosEnviados'
        """)
        
        table_exists = cursor.fetchone()
        assert table_exists, "Tabla TbCorreosEnviados no encontrada"
        
        # Verificar columnas
        cursor.execute("PRAGMA table_info(TbCorreosEnviados)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = ['IDCorreo', 'Aplicacion', 'Destinatarios', 'Asunto']
        for col in required_columns:
            assert col in columns, f"Columna {col} no encontrada"

@pytest.mark.integration
@pytest.mark.slow
def test_full_email_workflow():
    """Test completo del flujo de correos"""
    db_path = Path(__file__).parent.parent.parent / "dbs-sqlite" / "correos_datos.sqlite"
    
    if not db_path.exists():
        pytest.skip("Base de datos de prueba no encontrada")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Insertar correo de prueba
        cursor.execute("""
            INSERT INTO TbCorreosEnviados 
            (Aplicacion, Destinatarios, Asunto, Cuerpo, FechaEnvio)
            VALUES (?, ?, ?, ?, NULL)
        """, ("TEST", "test@example.com", "Test Subject", "Test Body"))
        
        test_id = cursor.lastrowid
        
        # Verificar inserción
        cursor.execute("""
            SELECT * FROM TbCorreosEnviados WHERE IDCorreo = ?
        """, (test_id,))
        
        result = cursor.fetchone()
        assert result is not None, "Correo de prueba no insertado"
        
        # Limpiar
        cursor.execute("DELETE FROM TbCorreosEnviados WHERE IDCorreo = ?", (test_id,))
        conn.commit()
'''
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def create_test_data(self) -> bool:
        """Crear datos de prueba"""
        self.print_step("Creando datos de prueba...")
        
        # Ejecutar script de creación de emails de prueba si existe
        create_emails_script = self.project_root / "tests" / "emails" / "create_test_emails.py"
        
        if create_emails_script.exists():
            try:
                subprocess.run([
                    sys.executable, str(create_emails_script), "--create"
                ], cwd=self.project_root, check=True, capture_output=True)
                self.print_step("Datos de prueba de emails creados", "success")
            except subprocess.CalledProcessError as e:
                self.print_step(f"Error creando datos de prueba: {e}", "warning")
        
        return True
    
    def run_quick_test(self) -> bool:
        """Ejecutar test rápido para verificar configuración"""
        self.print_step("Ejecutando test rápido de verificación...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/unit/test_example.py", 
                "-v", "--tb=short"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_step("Test rápido completado exitosamente", "success")
                return True
            else:
                self.print_step("Test rápido falló", "error")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            self.print_step(f"Error ejecutando test rápido: {e}", "error")
            return False
    
    def setup_complete_environment(self) -> bool:
        """Configurar entorno completo de testing"""
        print(f"{Colors.PURPLE}{Colors.BOLD}")
        print("🔧 CONFIGURADOR DEL ENTORNO DE TESTING")
        print("=" * 50)
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.END}")
        
        steps = [
            ("Verificar dependencias", self.check_dependencies),
            ("Configurar bases de datos", self.setup_test_databases),
            ("Validar estructura", self.validate_test_structure),
            ("Crear tests de ejemplo", self.create_sample_tests),
            ("Crear datos de prueba", self.create_test_data),
            ("Ejecutar test rápido", self.run_quick_test),
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            print(f"\n{Colors.CYAN}📋 {step_name}...{Colors.END}")
            try:
                if step_func():
                    success_count += 1
                else:
                    self.print_step(f"Falló: {step_name}", "error")
            except Exception as e:
                self.print_step(f"Error en {step_name}: {e}", "error")
        
        # Resumen final
        print(f"\n{Colors.CYAN}{'='*50}{Colors.END}")
        print(f"{Colors.BOLD}📊 RESUMEN DE CONFIGURACIÓN{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}")
        
        if success_count == len(steps):
            self.print_step(f"✅ Configuración completada exitosamente ({success_count}/{len(steps)})", "success")
            print(f"\n{Colors.GREEN}🎉 El entorno de testing está listo para usar!{Colors.END}")
            print(f"\n{Colors.BLUE}Comandos disponibles:{Colors.END}")
            print(f"  python run_tests.py                 # Ejecutar todos los tests")
            print(f"  python run_tests.py --unit         # Solo tests unitarios")
            print(f"  python run_tests.py --integration  # Solo tests de integración")
            print(f"  python run_tests.py --html         # Generar reporte HTML")
            return True
        else:
            self.print_step(f"⚠️ Configuración parcial ({success_count}/{len(steps)})", "warning")
            print(f"\n{Colors.YELLOW}Algunos pasos fallaron. Revisa los errores arriba.{Colors.END}")
            return False

def main():
    """Función principal"""
    setup = TestEnvironmentSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Solo test rápido
        setup.run_quick_test()
    else:
        # Configuración completa
        success = setup.setup_complete_environment()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()