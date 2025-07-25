#!/usr/bin/env python3
"""
Resumen ejecutivo del sistema de testing
Muestra un dashboard con el estado actual de los tests y cobertura
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

def get_coverage_data():
    """Obtener datos de cobertura desde el archivo JSON."""
    coverage_file = "htmlcov/status.json"
    if os.path.exists(coverage_file):
        with open(coverage_file, 'r') as f:
            return json.load(f)
    return None

def get_test_summary():
    """Ejecutar tests y obtener resumen."""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', '--tb=no', '-q'
        ], capture_output=True, text=True)
        
        output = result.stdout
        lines = output.split('\n')
        
        # Buscar línea de resumen
        summary_line = ""
        for line in lines:
            if "passed" in line or "failed" in line or "error" in line:
                summary_line = line
                break
        
        return {
            'output': output,
            'summary': summary_line,
            'return_code': result.returncode
        }
    except Exception as e:
        return {
            'output': f"Error ejecutando tests: {e}",
            'summary': "Error",
            'return_code': 1
        }

def generate_dashboard():
    """Generar dashboard del sistema de testing."""
    print("=" * 80)
    print("🚀 DASHBOARD DEL SISTEMA DE TESTING - SCRIPTS PYTHON")
    print("=" * 80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Estado de los tests
    print("📊 ESTADO DE LOS TESTS")
    print("-" * 40)
    
    test_data = get_test_summary()
    if test_data['return_code'] == 0:
        print("✅ Estado: TODOS LOS TESTS PASARON")
    else:
        print("⚠️  Estado: ALGUNOS TESTS FALLARON")
    
    print(f"📝 Resumen: {test_data['summary']}")
    print()
    
    # Cobertura de código
    print("📈 COBERTURA DE CÓDIGO")
    print("-" * 40)
    
    coverage_data = get_coverage_data()
    if coverage_data:
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        print(f"🎯 Cobertura Total: {total_coverage:.1f}%")
        
        if total_coverage >= 80:
            print("✅ Estado: EXCELENTE (≥80%)")
        elif total_coverage >= 60:
            print("⚠️  Estado: BUENO (60-79%)")
        else:
            print("❌ Estado: NECESITA MEJORA (<60%)")
    else:
        print("❌ No se encontraron datos de cobertura")
    
    print()
    
    # Estructura de tests
    print("📁 ESTRUCTURA DE TESTS")
    print("-" * 40)
    
    test_dirs = [
        ("tests/unit", "Tests Unitarios"),
        ("tests/integration", "Tests de Integración"),
        ("tests/emails", "Tests de Email"),
    ]
    
    structure_table = []
    for dir_path, description in test_dirs:
        if os.path.exists(dir_path):
            test_files = list(Path(dir_path).glob("**/*.py"))
            test_files = [f for f in test_files if f.name.startswith("test_")]
            count = len(test_files)
            status = "✅" if count > 0 else "⚠️"
            structure_table.append([description, count, status])
        else:
            structure_table.append([description, 0, "❌"])
    
    print(tabulate(structure_table, 
                  headers=["Tipo de Test", "Archivos", "Estado"],
                  tablefmt="grid"))
    print()
    
    # Archivos de reporte
    print("📄 REPORTES GENERADOS")
    print("-" * 40)
    
    reports = [
        ("test-report.html", "Reporte de Tests HTML"),
        ("htmlcov/index.html", "Reporte de Cobertura HTML"),
        ("coverage.xml", "Reporte de Cobertura XML"),
    ]
    
    reports_table = []
    for file_path, description in reports:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            size_kb = size / 1024
            reports_table.append([description, f"{size_kb:.1f} KB", "✅"])
        else:
            reports_table.append([description, "N/A", "❌"])
    
    print(tabulate(reports_table,
                  headers=["Reporte", "Tamaño", "Estado"],
                  tablefmt="grid"))
    print()
    
    # Comandos útiles
    print("🛠️  COMANDOS ÚTILES")
    print("-" * 40)
    print("• Ejecutar todos los tests:")
    print("  python run_tests.py")
    print()
    print("• Ejecutar solo tests unitarios:")
    print("  python run_tests.py --unit")
    print()
    print("• Ejecutar tests de email:")
    print("  python run_tests.py --emails")
    print()
    print("• Generar reporte HTML:")
    print("  python run_tests.py --html")
    print()
    print("• Ver cobertura detallada:")
    print("  python run_tests.py --coverage")
    print()
    print("• Abrir reporte de cobertura:")
    print("  start htmlcov/index.html")
    print()
    
    # Recomendaciones
    print("💡 RECOMENDACIONES")
    print("-" * 40)
    
    recommendations = []
    
    if coverage_data:
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        if total_coverage < 80:
            recommendations.append("🎯 Aumentar cobertura de tests (objetivo: ≥80%)")
    
    # Verificar módulos sin tests
    src_files = list(Path("src").glob("**/*.py"))
    src_files = [f for f in src_files if not f.name.startswith("__")]
    
    test_files = list(Path("tests").glob("**/test_*.py"))
    tested_modules = set()
    for test_file in test_files:
        # Extraer nombre del módulo del archivo de test
        module_name = test_file.name.replace("test_", "").replace(".py", "")
        tested_modules.add(module_name)
    
    untested_modules = []
    for src_file in src_files:
        module_name = src_file.stem
        if module_name not in tested_modules and module_name != "__init__":
            untested_modules.append(str(src_file))
    
    if untested_modules:
        recommendations.append(f"📝 Añadir tests para {len(untested_modules)} módulos sin cobertura")
    
    if not recommendations:
        recommendations.append("✅ ¡Excelente! El sistema de testing está bien configurado")
    
    for rec in recommendations:
        print(f"  • {rec}")
    
    print()
    print("=" * 80)
    print("🎉 Dashboard generado exitosamente")
    print("=" * 80)

if __name__ == "__main__":
    generate_dashboard()