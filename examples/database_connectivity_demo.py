#!/usr/bin/env python3
"""
Demostración del Test de Conectividad de Bases de Datos
======================================================

Este script demuestra cómo usar el nuevo test de conectividad de bases de datos
que verifica el acceso a todas las BD configuradas según el entorno.

Uso:
    python examples/database_connectivity_demo.py
"""

import subprocess
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from common.config import config


def print_header(title: str):
    """Imprimir encabezado decorativo"""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}")


def print_config_info():
    """Mostrar información de configuración actual"""
    print_header("📋 CONFIGURACIÓN ACTUAL")

    print(f"🌍 Entorno: {config.environment}")
    print(f"🔐 Password BD configurado: {'✅ Sí' if config.db_password else '❌ No'}")

    print("\n📊 Bases de datos configuradas:")
    databases = {
        "BRASS": config.db_brass_path,
        "Tareas": config.db_tareas_path,
        "Correos": config.db_correos_path,
    }

    for db_name, db_path in databases.items():
        exists = "✅" if Path(db_path).exists() else "❌"
        print(f"  {exists} {db_name}: {db_path}")


def run_database_connectivity_test():
    """Ejecutar el test de conectividad de bases de datos"""
    print_header("🧪 EJECUTANDO TEST DE CONECTIVIDAD")

    print("Ejecutando: python run_tests.py --database")
    print("Este test verificará la conectividad a todas las bases de datos...")

    try:
        # Ejecutar el test de conectividad
        result = subprocess.run(
            [sys.executable, "run_tests.py", "--database"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        print(f"\n📊 Código de salida: {result.returncode}")

        if result.returncode == 0:
            print("✅ Todos los tests de conectividad pasaron")
        else:
            print("⚠️ Algunos tests fallaron (normal si no estás en la red de oficina)")

        # Mostrar parte de la salida
        output_lines = result.stdout.split("\n")
        summary_started = False

        print("\n📋 Resumen de resultados:")
        for line in output_lines:
            if "RESUMEN DE RESULTADOS" in line:
                summary_started = True
            elif summary_started and (
                "TESTS FALLIDOS" in line or "RECOMENDACIONES" in line
            ):
                break
            elif summary_started and line.strip():
                print(f"  {line}")

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def show_usage_examples():
    """Mostrar ejemplos de uso"""
    print_header("💡 EJEMPLOS DE USO")

    examples = [
        ("Ejecutar solo tests de BD", "python run_tests.py --database"),
        ("Tests de BD con reporte HTML", "python run_tests.py --database --html"),
        ("Todos los tests de integración", "python run_tests.py --integration"),
        ("Tests específicos de BD", "python -m pytest tests/integration/database/ -v"),
    ]

    for description, command in examples:
        print(f"📌 {description}:")
        print(f"   {command}")
        print()


def main():
    """Función principal de demostración"""
    print_header("🔍 DEMO: TEST DE CONECTIVIDAD DE BASES DE DATOS")

    print("Este demo muestra el nuevo test de integración que verifica")
    print("la conectividad a todas las bases de datos configuradas.")

    # Mostrar configuración actual
    print_config_info()

    # Ejecutar test de conectividad
    success = run_database_connectivity_test()

    # Mostrar ejemplos de uso
    show_usage_examples()

    # Resumen final
    print_header("📝 RESUMEN")

    if success:
        print("✅ El test de conectividad se ejecutó exitosamente")
        print("   Todas las bases de datos accesibles están funcionando correctamente")
    else:
        print("⚠️ Algunos tests de conectividad fallaron")
        print("   Esto es normal si no estás conectado a la red de oficina")
        print("   o si algunas bases de datos no están disponibles")

    print(f"\n🎯 Entorno actual: {config.environment}")
    print("💡 Tip: Usa 'python run_tests.py --database' para verificar conectividad")

    print(f"\n{'='*60}")
    print("Demo completado. ¡El test de conectividad está listo para usar!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
