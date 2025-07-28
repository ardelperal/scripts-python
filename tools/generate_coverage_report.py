#!/usr/bin/env python3
"""
Script para generar reportes de cobertura de código
"""
import subprocess
import sys
import webbrowser
from pathlib import Path

def run_coverage_report():
    """Ejecuta tests con coverage y genera reporte HTML"""
    
    print("🧪 Ejecutando tests con coverage...")
    
    # Ejecutar tests con coverage
    print("🧪 Ejecutando tests con coverage...")
    result = subprocess.run([
        "coverage", "run", "--source=src", "-m", "pytest", "tests/unit/", "-v"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Error ejecutando tests:")
        print(result.stderr)
        return False
    
    print("✅ Tests ejecutados correctamente")
    print("📊 Resultados:")
    # Solo mostrar el resumen final
    lines = result.stdout.split('\n')
    for line in lines[-5:]:
        if line.strip():
            print(f"   {line}")
    
    # Generar reporte HTML
    print("\n📄 Generando reporte HTML...")
    result = subprocess.run([
        sys.executable, "-m", "coverage", "html"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Error generando reporte HTML:")
        print(result.stderr)
        return False
    
    print("✅ Reporte HTML generado en htmlcov/")
    
    # Mostrar resumen en consola
    print("\n📈 Resumen de cobertura:")
    subprocess.run([sys.executable, "-m", "coverage", "report"])
    
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
    print("🎯 Generador de Reportes de Cobertura")
    print("=" * 40)
    
    if run_coverage_report():
        print("\n" + "=" * 40)
        print("✨ ¡Reporte generado exitosamente!")
        print("\n📁 Archivos generados:")
        print("   - htmlcov/index.html (reporte principal)")
        print("   - coverage.xml (para CI/CD)")
        print("\n💡 Cómo usar el reporte:")
        print("   1. Abre htmlcov/index.html en tu navegador")
        print("   2. Haz clic en cualquier archivo para ver líneas no cubiertas")
        print("   3. Las líneas rojas necesitan más tests")
        print("   4. Las líneas verdes están bien cubiertas")
        
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