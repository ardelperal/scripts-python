#!/usr/bin/env python3
"""
Sistema Completo de Testing con Reporte de Cobertura
====================================================

Este script ejecuta todos los tests del proyecto y genera un reporte completo
con tabla de resultados y métricas de cobertura.

Uso:
    python run_tests.py                    # Ejecutar todos los tests
    python run_tests.py --unit            # Solo tests unitarios
    python run_tests.py --integration     # Solo tests de integración
    python run_tests.py --emails          # Solo tests de emails
    python run_tests.py --database        # Solo tests de conectividad de BD
    python run_tests.py --module brass    # Tests de un módulo específico
    python run_tests.py --coverage        # Con reporte de cobertura detallado
    python run_tests.py --html            # Generar reporte HTML
"""

import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class TestResult:
    """Clase para almacenar resultados de tests"""
    def __init__(self):
        self.total_tests = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0
        self.duration = 0.0
        self.coverage_percentage = 0.0
        self.modules_coverage = {}
        self.failed_tests = []
        self.error_tests = []

class TestRunner:
    """Ejecutor principal del sistema de testing"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent  # Subir un nivel desde scripts/
        self.results = TestResult()
        self.start_time = None
        self.end_time = None
        
    def run_pytest(self, test_path: str, extra_args: List[str] = None) -> Tuple[int, str]:
        """Ejecutar pytest con argumentos específicos"""
        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            "-v",
            "--tb=short",
            "--cov=src",
            "--cov-report=xml",
            "--cov-report=term-missing",
            "--junit-xml=test-results.xml"
        ]
        
        if extra_args:
            cmd.extend(extra_args)
            
        print(f"{Colors.BLUE}🚀 Ejecutando: {' '.join(cmd)}{Colors.END}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.returncode, result.stdout + result.stderr
        except Exception as e:
            return 1, f"Error ejecutando pytest: {str(e)}"
    
    def parse_junit_xml(self) -> None:
        """Parsear resultados de JUnit XML"""
        junit_file = self.project_root / "test-results.xml"
        if not junit_file.exists():
            print(f"{Colors.YELLOW}⚠️  Archivo JUnit XML no encontrado{Colors.END}")
            return
            
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()
            
            # Obtener estadísticas generales
            self.results.total_tests = int(root.get('tests', 0))
            self.results.failed = int(root.get('failures', 0))
            self.results.errors = int(root.get('errors', 0))
            self.results.skipped = int(root.get('skipped', 0))
            self.results.passed = self.results.total_tests - self.results.failed - self.results.errors - self.results.skipped
            self.results.duration = float(root.get('time', 0))
            
            # Obtener tests fallidos
            for testcase in root.findall('.//testcase'):
                failure = testcase.find('failure')
                error = testcase.find('error')
                
                if failure is not None:
                    self.results.failed_tests.append({
                        'name': testcase.get('name'),
                        'classname': testcase.get('classname'),
                        'message': failure.get('message', ''),
                        'type': 'failure'
                    })
                    
                if error is not None:
                    self.results.error_tests.append({
                        'name': testcase.get('name'),
                        'classname': testcase.get('classname'),
                        'message': error.get('message', ''),
                        'type': 'error'
                    })
                    
        except Exception as e:
            print(f"{Colors.RED}❌ Error parseando JUnit XML: {e}{Colors.END}")
    
    def parse_coverage_xml(self) -> None:
        """Parsear resultados de cobertura XML"""
        coverage_file = self.project_root / "coverage.xml"
        if not coverage_file.exists():
            print(f"{Colors.YELLOW}⚠️  Archivo de cobertura XML no encontrado{Colors.END}")
            return
            
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            # Cobertura general
            self.results.coverage_percentage = float(root.get('line-rate', 0)) * 100
            
            # Cobertura por módulo
            for package in root.findall('.//package'):
                package_name = package.get('name', '')
                package_coverage = float(package.get('line-rate', 0)) * 100
                
                for class_elem in package.findall('.//class'):
                    class_name = class_elem.get('name', '')
                    class_coverage = float(class_elem.get('line-rate', 0)) * 100
                    
                    module_path = f"{package_name}.{class_name}" if package_name else class_name
                    self.results.modules_coverage[module_path] = class_coverage
                    
        except Exception as e:
            print(f"{Colors.RED}❌ Error parseando cobertura XML: {e}{Colors.END}")
    
    def print_header(self, title: str) -> None:
        """Imprimir encabezado decorativo"""
        print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{title.center(80)}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    def print_summary_table(self) -> None:
        """Imprimir tabla resumen de resultados"""
        self.print_header("📊 RESUMEN DE RESULTADOS DE TESTING")
        
        # Tabla principal
        print(f"{Colors.BOLD}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}")
        print(f"{Colors.BOLD}│                           RESULTADOS GENERALES                             │{Colors.END}")
        print(f"{Colors.BOLD}├─────────────────────────────────────────────────────────────────────────────┤{Colors.END}")
        
        # Estadísticas de tests
        total_color = Colors.BLUE if self.results.total_tests > 0 else Colors.YELLOW
        passed_color = Colors.GREEN if self.results.passed > 0 else Colors.YELLOW
        failed_color = Colors.RED if self.results.failed > 0 else Colors.GREEN
        error_color = Colors.RED if self.results.errors > 0 else Colors.GREEN
        skipped_color = Colors.YELLOW if self.results.skipped > 0 else Colors.GREEN
        
        print(f"│ {Colors.BOLD}Total Tests:{Colors.END}      {total_color}{self.results.total_tests:>3}{Colors.END}                                                    │")
        print(f"│ {Colors.BOLD}✅ Pasaron:{Colors.END}       {passed_color}{self.results.passed:>3}{Colors.END}                                                    │")
        print(f"│ {Colors.BOLD}❌ Fallaron:{Colors.END}      {failed_color}{self.results.failed:>3}{Colors.END}                                                    │")
        print(f"│ {Colors.BOLD}🚨 Errores:{Colors.END}       {error_color}{self.results.errors:>3}{Colors.END}                                                    │")
        print(f"│ {Colors.BOLD}⏭️  Omitidos:{Colors.END}      {skipped_color}{self.results.skipped:>3}{Colors.END}                                                    │")
        print(f"│ {Colors.BOLD}⏱️  Duración:{Colors.END}      {Colors.CYAN}{self.results.duration:.2f}s{Colors.END}                                               │")
        
        # Porcentaje de éxito
        success_rate = (self.results.passed / self.results.total_tests * 100) if self.results.total_tests > 0 else 0
        success_color = Colors.GREEN if success_rate >= 90 else Colors.YELLOW if success_rate >= 70 else Colors.RED
        
        print(f"│ {Colors.BOLD}📈 Éxito:{Colors.END}         {success_color}{success_rate:.1f}%{Colors.END}                                                  │")
        
        # Cobertura
        coverage_color = Colors.GREEN if self.results.coverage_percentage >= 80 else Colors.YELLOW if self.results.coverage_percentage >= 60 else Colors.RED
        print(f"│ {Colors.BOLD}🎯 Cobertura:{Colors.END}     {coverage_color}{self.results.coverage_percentage:.1f}%{Colors.END}                                                  │")
        
        print(f"{Colors.BOLD}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}")
    
    def print_coverage_table(self) -> None:
        """Imprimir tabla de cobertura por módulos"""
        if not self.results.modules_coverage:
            return
            
        self.print_header("🎯 COBERTURA POR MÓDULOS")
        
        print(f"{Colors.BOLD}┌─────────────────────────────────────────────┬─────────────┬─────────────────┐{Colors.END}")
        print(f"{Colors.BOLD}│                   MÓDULO                    │  COBERTURA  │     ESTADO      │{Colors.END}")
        print(f"{Colors.BOLD}├─────────────────────────────────────────────┼─────────────┼─────────────────┤{Colors.END}")
        
        for module, coverage in sorted(self.results.modules_coverage.items()):
            # Determinar color y estado
            if coverage >= 90:
                color = Colors.GREEN
                status = "🟢 Excelente"
            elif coverage >= 80:
                color = Colors.GREEN
                status = "✅ Bueno"
            elif coverage >= 60:
                color = Colors.YELLOW
                status = "⚠️  Aceptable"
            else:
                color = Colors.RED
                status = "❌ Bajo"
            
            # Truncar nombre del módulo si es muy largo
            module_display = module[:43] if len(module) <= 43 else module[:40] + "..."
            
            print(f"│ {module_display:<43} │ {color}{coverage:>8.1f}%{Colors.END} │ {status:<15} │")
        
        print(f"{Colors.BOLD}└─────────────────────────────────────────────┴─────────────┴─────────────────┘{Colors.END}")
    
    def print_failed_tests(self) -> None:
        """Imprimir tests fallidos"""
        if not self.results.failed_tests and not self.results.error_tests:
            return
            
        self.print_header("❌ TESTS FALLIDOS")
        
        all_failed = self.results.failed_tests + self.results.error_tests
        
        for i, test in enumerate(all_failed, 1):
            icon = "❌" if test['type'] == 'failure' else "🚨"
            print(f"{Colors.RED}{Colors.BOLD}{icon} {i}. {test['classname']}.{test['name']}{Colors.END}")
            print(f"   {Colors.YELLOW}Mensaje: {test['message'][:100]}{'...' if len(test['message']) > 100 else ''}{Colors.END}")
            print()
    
    def print_recommendations(self) -> None:
        """Imprimir recomendaciones basadas en resultados"""
        self.print_header("💡 RECOMENDACIONES")
        
        recommendations = []
        
        # Recomendaciones basadas en cobertura
        if self.results.coverage_percentage < 60:
            recommendations.append("🎯 Aumentar cobertura de tests (objetivo: >80%)")
        elif self.results.coverage_percentage < 80:
            recommendations.append("🎯 Mejorar cobertura de tests (objetivo: >80%)")
        
        # Recomendaciones basadas en tests fallidos
        if self.results.failed > 0:
            recommendations.append("❌ Corregir tests fallidos antes del deploy")
        
        if self.results.errors > 0:
            recommendations.append("🚨 Resolver errores críticos en tests")
        
        # Recomendaciones basadas en módulos con baja cobertura
        low_coverage_modules = [
            module for module, coverage in self.results.modules_coverage.items()
            if coverage < 60
        ]
        
        if low_coverage_modules:
            recommendations.append(f"📝 Añadir tests para módulos: {', '.join(low_coverage_modules[:3])}")
        
        # Recomendaciones positivas
        if self.results.coverage_percentage >= 80 and self.results.failed == 0:
            recommendations.append("🎉 ¡Excelente calidad de código! Mantener este nivel")
        
        if not recommendations:
            recommendations.append("✅ Todo está en orden. ¡Buen trabajo!")
        
        for rec in recommendations:
            print(f"  • {rec}")
        
        print()
    
    def generate_html_report(self) -> None:
        """Generar reporte HTML"""
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Testing - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric h3 {{ margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }}
        .metric .value {{ font-size: 32px; font-weight: bold; margin: 0; }}
        .success {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); }}
        .warning {{ background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); }}
        .error {{ background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%); }}
        .coverage-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .coverage-table th, .coverage-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .coverage-table th {{ background-color: #f8f9fa; font-weight: 600; }}
        .coverage-bar {{ width: 100px; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .coverage-fill {{ height: 100%; border-radius: 10px; }}
        .high-coverage {{ background: linear-gradient(90deg, #4CAF50, #45a049); }}
        .medium-coverage {{ background: linear-gradient(90deg, #ff9800, #f57c00); }}
        .low-coverage {{ background: linear-gradient(90deg, #f44336, #d32f2f); }}
        .timestamp {{ text-align: center; color: #666; margin-top: 30px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Reporte de Testing</h1>
        
        <div class="summary">
            <div class="metric">
                <h3>Total Tests</h3>
                <p class="value">{self.results.total_tests}</p>
            </div>
            <div class="metric success">
                <h3>✅ Pasaron</h3>
                <p class="value">{self.results.passed}</p>
            </div>
            <div class="metric {'error' if self.results.failed > 0 else 'success'}">
                <h3>❌ Fallaron</h3>
                <p class="value">{self.results.failed}</p>
            </div>
            <div class="metric {'warning' if self.results.coverage_percentage < 80 else 'success'}">
                <h3>🎯 Cobertura</h3>
                <p class="value">{self.results.coverage_percentage:.1f}%</p>
            </div>
        </div>
        
        <h2>🎯 Cobertura por Módulos</h2>
        <table class="coverage-table">
            <thead>
                <tr>
                    <th>Módulo</th>
                    <th>Cobertura</th>
                    <th>Progreso</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for module, coverage in sorted(self.results.modules_coverage.items()):
            coverage_class = "high-coverage" if coverage >= 80 else "medium-coverage" if coverage >= 60 else "low-coverage"
            status = "🟢 Excelente" if coverage >= 90 else "✅ Bueno" if coverage >= 80 else "⚠️ Aceptable" if coverage >= 60 else "❌ Bajo"
            
            html_content += f"""
                <tr>
                    <td>{module}</td>
                    <td>{coverage:.1f}%</td>
                    <td>
                        <div class="coverage-bar">
                            <div class="coverage-fill {coverage_class}" style="width: {coverage}%"></div>
                        </div>
                    </td>
                    <td>{status}</td>
                </tr>
"""
        
        html_content += f"""
            </tbody>
        </table>
        
        <div class="timestamp">
            Generado el {datetime.now().strftime('%Y-%m-%d a las %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        html_file = self.project_root / "test-report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"{Colors.GREEN}📄 Reporte HTML generado: {html_file}{Colors.END}")
    
    def run_tests(self, test_type: str = "all", module: str = None, generate_html: bool = False) -> None:
        """Ejecutar tests según el tipo especificado"""
        self.start_time = time.time()
        
        # Determinar qué tests ejecutar
        if test_type == "unit":
            test_path = "tests/unit"
        elif test_type == "integration":
            test_path = "tests/integration"
        elif test_type == "emails":
            test_path = "tests/emails"
        elif test_type == "database":
            test_path = "tests/integration/database"
        elif test_type == "module" and module:
            test_path = f"tests/unit/{module}"
            if not Path(self.project_root / test_path).exists():
                test_path = f"tests/integration/{module}"
        else:
            # Usar tests/manual como directorio por defecto ya que es el que existe
            test_path = "tests/manual"
        
        # Ejecutar tests
        return_code, output = self.run_pytest(test_path)
        
        self.end_time = time.time()
        
        # Parsear resultados
        self.parse_junit_xml()
        self.parse_coverage_xml()
        
        # Mostrar resultados
        print(f"\n{Colors.BLUE}📋 Salida de pytest:{Colors.END}")
        print(output)
        
        self.print_summary_table()
        self.print_coverage_table()
        self.print_failed_tests()
        self.print_recommendations()
        
        if generate_html:
            self.generate_html_report()
        
        # Limpiar archivos temporales
        for temp_file in ["test-results.xml", "coverage.xml", ".coverage"]:
            temp_path = self.project_root / temp_file
            if temp_path.exists():
                temp_path.unlink()

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Sistema Completo de Testing con Reporte de Cobertura",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_tests.py                    # Todos los tests
  python run_tests.py --unit            # Solo tests unitarios
  python run_tests.py --integration     # Solo tests de integración
  python run_tests.py --emails          # Solo tests de emails
  python run_tests.py --database        # Solo tests de conectividad de BD
  python run_tests.py --module brass    # Tests del módulo BRASS
  python run_tests.py --html            # Generar reporte HTML
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="Ejecutar solo tests unitarios")
    parser.add_argument("--integration", action="store_true", help="Ejecutar solo tests de integración")
    parser.add_argument("--emails", action="store_true", help="Ejecutar solo tests de emails")
    parser.add_argument("--database", action="store_true", help="Ejecutar solo tests de conectividad de BD")
    parser.add_argument("--module", type=str, help="Ejecutar tests de un módulo específico")
    parser.add_argument("--html", action="store_true", help="Generar reporte HTML")
    parser.add_argument("--coverage", action="store_true", help="Mostrar reporte de cobertura detallado")
    
    args = parser.parse_args()
    
    # Determinar tipo de test
    test_type = "all"
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    elif args.emails:
        test_type = "emails"
    elif args.database:
        test_type = "database"
    elif args.module:
        test_type = "module"
    
    # Crear y ejecutar runner
    runner = TestRunner()
    
    print(f"{Colors.PURPLE}{Colors.BOLD}")
    print("🧪 SISTEMA COMPLETO DE TESTING")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Tipo: {test_type.upper()}")
    if args.module:
        print(f"📦 Módulo: {args.module}")
    print(f"{Colors.END}")
    
    try:
        runner.run_tests(
            test_type=test_type,
            module=args.module,
            generate_html=args.html
        )
        
        # Código de salida basado en resultados
        if runner.results.failed > 0 or runner.results.errors > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrumpidos por el usuario{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error ejecutando tests: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()