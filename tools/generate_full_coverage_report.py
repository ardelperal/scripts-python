#!/usr/bin/env python3
"""
Script para generar reportes de cobertura COMPLETA (unitarios + integración)
"""
import subprocess
import sys
import webbrowser
from pathlib import Path

def run_full_coverage_report():
    """Ejecuta TODOS los tests con coverage y genera reporte HTML"""
    
    print("🧪 Ejecutando TODOS los tests con coverage...")
    print("📋 Incluye: tests unitarios + tests de integración")
    
    # Ejecutar TODOS los tests con coverage
    try:
        result = subprocess.run([
            sys.executable, "-m", "coverage", "run", "--source=src", "-m", "pytest", "tests/", "-v"
        ], capture_output=True, text=True, shell=True)
    except Exception as e:
        print(f"❌ Error ejecutando coverage: {e}")
        print("💡 Posibles soluciones:")
        print("   1. Instala coverage: pip install coverage")
        print("   2. Verifica que estés en el entorno virtual correcto")
        print("   3. Ejecuta como administrador si es necesario")
        return False
    
    if result.returncode != 0:
        print("❌ Error ejecutando tests:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    print("✅ Tests ejecutados correctamente")
    print("📊 Resultados:")
    # Solo mostrar el resumen final
    lines = result.stdout.split('\n')
    for line in lines[-10:]:
        if line.strip():
            print(f"   {line}")
    
    # Generar reporte HTML
    print("\n📄 Generando reporte HTML...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "coverage", "html"
        ], capture_output=True, text=True, shell=True)
    except Exception as e:
        print(f"❌ Error generando reporte HTML: {e}")
        return False
    
    if result.returncode != 0:
        print("❌ Error generando reporte HTML:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    print("✅ Reporte HTML generado en htmlcov/")
    
    # Generar reporte XML
    print("📄 Generando reporte XML...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "coverage", "xml"
        ], capture_output=True, text=True, shell=True)
    except Exception as e:
        print(f"❌ Error generando reporte XML: {e}")
        return False
    
    if result.returncode != 0:
        print("❌ Error generando reporte XML:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    # Mostrar resumen en consola
    print("\n📈 Resumen de cobertura COMPLETA:")
    try:
        result = subprocess.run([
            sys.executable, "-m", "coverage", "report"
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ Error mostrando resumen:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"❌ Error ejecutando coverage report: {e}")
    
    print("\n✅ Reportes generados:")
    print("   📄 HTML: htmlcov/index.html")
    print("   📄 XML: coverage.xml")
    print("   📄 Data: .coverage")
    
    return True

def open_report():
    """Abre el reporte HTML en el navegador"""
    html_file = Path("htmlcov/index.html")
    if html_file.exists():
        print(f"\n🌐 Abriendo reporte en navegador: {html_file.absolute()}")
        webbrowser.open(f"file://{html_file.absolute()}")
    else:
        print("❌ No se encontró el archivo htmlcov/index.html")

if __name__ == "__main__":
    print("🎯 Generador de Reportes de Cobertura COMPLETA")
    print("=" * 50)
    print("📋 Incluye: Tests Unitarios + Tests de Integración")
    print("⚠️  Nota: Requiere bases de datos locales configuradas")
    print("=" * 50)
    
    if run_full_coverage_report():
        print("\n" + "=" * 50)
        print("✨ ¡Reporte COMPLETO generado exitosamente!")
        print("\n📁 Archivos generados:")
        print("   - htmlcov/index.html (reporte principal)")
        print("   - coverage.xml (para CI/CD)")
        print("\n💡 Cómo usar el reporte:")
        print("   1. Abre htmlcov/index.html en tu navegador")
        print("   2. Haz clic en cualquier archivo para ver líneas no cubiertas")
        print("   3. Las líneas rojas necesitan más tests")
        print("   4. Las líneas verdes están bien cubiertas")
        print("   5. Este reporte incluye cobertura REAL del código")
        
        # Preguntar si abrir automáticamente
        try:
            response = input("\n¿Abrir reporte en navegador? (y/n): ").lower()
            if response in ['y', 'yes', 's', 'si', '']:
                open_report()
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
    else:
        print("❌ Error generando reporte")
        sys.exit(1)