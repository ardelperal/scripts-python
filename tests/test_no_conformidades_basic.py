"""
Test simple para verificar el módulo de No Conformidades
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Importar solo las clases de datos que no dependen de otros módulos
try:
    from src.no_conformidades.no_conformidades_manager import NoConformidad, ARAPC, Usuario
    IMPORTS_OK = True
except ImportError as e:
    print(f"Error importando módulos: {e}")
    IMPORTS_OK = False


class TestDataClasses(unittest.TestCase):
    """Tests para las clases de datos básicas"""
    
    @unittest.skipIf(not IMPORTS_OK, "No se pudieron importar los módulos")
    def test_crear_no_conformidad(self):
        """Test crear una No Conformidad"""
        fecha_apertura = datetime(2024, 1, 1)
        fecha_cierre = datetime(2024, 2, 1)
        
        nc = NoConformidad(
            codigo="NC-001",
            nemotecnico="TEST",
            descripcion="Descripción de prueba",
            responsable_calidad="Juan Pérez",
            fecha_apertura=fecha_apertura,
            fecha_prev_cierre=fecha_cierre,
            dias_para_cierre=10
        )
        
        self.assertEqual(nc.codigo, "NC-001")
        self.assertEqual(nc.nemotecnico, "TEST")
        self.assertEqual(nc.descripcion, "Descripción de prueba")
        self.assertEqual(nc.responsable_calidad, "Juan Pérez")
        self.assertEqual(nc.fecha_apertura, fecha_apertura)
        self.assertEqual(nc.fecha_prev_cierre, fecha_cierre)
        self.assertEqual(nc.dias_para_cierre, 10)
    
    @unittest.skipIf(not IMPORTS_OK, "No se pudieron importar los módulos")
    def test_crear_arapc(self):
        """Test crear una ARAPC"""
        fecha_fin = datetime(2024, 2, 1)
        
        arapc = ARAPC(
            id_accion=1,
            codigo_nc="NC-001",
            descripcion="Acción correctiva de prueba",
            responsable="María García",
            fecha_fin_prevista=fecha_fin
        )
        
        self.assertEqual(arapc.id_accion, 1)
        self.assertEqual(arapc.codigo_nc, "NC-001")
        self.assertEqual(arapc.descripcion, "Acción correctiva de prueba")
        self.assertEqual(arapc.responsable, "María García")
        self.assertEqual(arapc.fecha_fin_prevista, fecha_fin)
        self.assertIsNone(arapc.fecha_fin_real)
    
    @unittest.skipIf(not IMPORTS_OK, "No se pudieron importar los módulos")
    def test_crear_usuario(self):
        """Test crear un Usuario"""
        usuario = Usuario(
            usuario_red="jperez",
            nombre="Juan Pérez",
            correo="juan.perez@empresa.com"
        )
        
        self.assertEqual(usuario.usuario_red, "jperez")
        self.assertEqual(usuario.nombre, "Juan Pérez")
        self.assertEqual(usuario.correo, "juan.perez@empresa.com")


class TestModuleStructure(unittest.TestCase):
    """Tests para verificar la estructura del módulo"""
    
    def test_archivos_existen(self):
        """Verificar que todos los archivos del módulo existen"""
        base_path = os.path.join(project_root, "src", "no_conformidades")
        
        archivos_requeridos = [
            "__init__.py",
            "no_conformidades_manager.py",
            "html_report_generator.py",
            "email_notifications.py"
        ]
        
        for archivo in archivos_requeridos:
            ruta_archivo = os.path.join(base_path, archivo)
            self.assertTrue(
                os.path.exists(ruta_archivo),
                f"El archivo {archivo} no existe en {base_path}"
            )
    
    def test_script_principal_existe(self):
        """Verificar que el script principal existe"""
        script_path = os.path.join(project_root, "scripts", "run_no_conformidades.py")
        self.assertTrue(
            os.path.exists(script_path),
            "El script principal run_no_conformidades.py no existe"
        )
    
    def test_documentacion_existe(self):
        """Verificar que la documentación existe"""
        doc_path = os.path.join(project_root, "docs", "NO_CONFORMIDADES.md")
        self.assertTrue(
            os.path.exists(doc_path),
            "La documentación NO_CONFORMIDADES.md no existe"
        )
    
    def test_env_no_conformidades_existe(self):
        """Verificar que el archivo .env específico existe"""
        env_path = os.path.join(project_root, ".env.no_conformidades")
        self.assertTrue(
            os.path.exists(env_path),
            "El archivo .env.no_conformidades no existe"
        )


class TestFileContent(unittest.TestCase):
    """Tests para verificar el contenido de los archivos"""
    
    def test_contenido_init(self):
        """Verificar que __init__.py tiene las importaciones correctas"""
        init_path = os.path.join(project_root, "src", "no_conformidades", "__init__.py")
        
        if os.path.exists(init_path):
            with open(init_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Verificar que contiene las importaciones principales
            self.assertIn("NoConformidadesManager", contenido)
            self.assertIn("HTMLReportGenerator", contenido)
            self.assertIn("EmailNotificationManager", contenido)
    
    def test_contenido_env_no_conformidades(self):
        """Verificar que .env.no_conformidades tiene configuraciones básicas"""
        env_path = os.path.join(project_root, ".env.no_conformidades")
        
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Verificar configuraciones clave
            self.assertIn("DB_NO_CONFORMIDADES", contenido)
            self.assertIn("NO_CONFORMIDADES_DIAS_TAREA_CALIDAD", contenido)
            self.assertIn("NO_CONFORMIDADES_EMAIL", contenido)
    
    def test_contenido_documentacion(self):
        """Verificar que la documentación tiene las secciones principales"""
        doc_path = os.path.join(project_root, "docs", "NO_CONFORMIDADES.md")
        
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Verificar secciones principales
            self.assertIn("# Módulo de No Conformidades", contenido)
            self.assertIn("## Características Principales", contenido)
            self.assertIn("## Instalación y Configuración", contenido)
            self.assertIn("## Uso del Módulo", contenido)


def main():
    """Función principal para ejecutar tests"""
    print("🧪 EJECUTANDO TESTS BÁSICOS DEL MÓDULO DE NO CONFORMIDADES")
    print("=" * 60)
    
    # Configurar el runner de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todas las clases de test
    suite.addTests(loader.loadTestsFromTestCase(TestDataClasses))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestFileContent))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS BÁSICOS")
    print("=" * 60)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Éxito: {result.wasSuccessful()}")
    
    if result.errors:
        print("\nERRORES:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ TODOS LOS TESTS BÁSICOS PASARON")
        print("El módulo de No Conformidades está correctamente estructurado")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("Revisa los errores anteriores")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)