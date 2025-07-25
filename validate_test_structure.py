#!/usr/bin/env python3
"""
Script de validación de la nueva estructura de tests.
Verifica que la reorganización se completó correctamente.
"""

import os
from pathlib import Path
from collections import defaultdict

def validate_test_structure():
    """Valida la nueva estructura de tests reorganizada."""
    
    print("🔍 Validando estructura de tests reorganizada...\n")
    
    tests_path = Path("tests")
    
    # 1. Verificar estructura de directorios
    expected_dirs = [
        "unit",
        "unit/brass", 
        "unit/common",
        "unit/correos",
        "unit/expedientes",
        "integration",
        "integration/brass",
        "integration/database", 
        "integration/correos",
        "functional",
        "functional/access_sync",
        "functional/correos_workflows",
        "fixtures",
        "data"
    ]
    
    print("📁 Verificando estructura de directorios:")
    missing_dirs = []
    for dir_path in expected_dirs:
        full_path = tests_path / dir_path
        if full_path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path}")
            missing_dirs.append(dir_path)
    
    # 2. Contar archivos de test por categoría
    test_counts = defaultdict(int)
    test_files = defaultdict(list)
    
    for root, dirs, files in os.walk(tests_path):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, file), tests_path)
                category = rel_path.split(os.sep)[0] if os.sep in rel_path else "root"
                test_counts[category] += 1
                test_files[category].append(rel_path)
    
    print(f"\n📊 Distribución de archivos de test:")
    total_tests = 0
    for category, count in sorted(test_counts.items()):
        print(f"  📂 {category}: {count} archivos")
        total_tests += count
        for test_file in sorted(test_files[category]):
            print(f"     • {test_file}")
    
    print(f"\n📈 Total de archivos de test: {total_tests}")
    
    # 3. Verificar archivos de configuración
    print(f"\n⚙️ Verificando archivos de configuración:")
    config_files = [
        "config.py",
        "conftest.py", 
        "__init__.py"
    ]
    
    for config_file in config_files:
        file_path = tests_path / config_file
        if file_path.exists():
            print(f"  ✅ {config_file}")
        else:
            print(f"  ❌ {config_file}")
    
    # 4. Verificar que no hay duplicados
    print(f"\n🔍 Verificando duplicados:")
    all_test_files = []
    for category_files in test_files.values():
        all_test_files.extend([os.path.basename(f) for f in category_files])
    
    duplicates = []
    seen = set()
    for file in all_test_files:
        if file in seen:
            duplicates.append(file)
        seen.add(file)
    
    if duplicates:
        print(f"  ⚠️ Archivos duplicados encontrados: {duplicates}")
    else:
        print(f"  ✅ No se encontraron duplicados")
    
    # 5. Verificar archivos __init__.py
    print(f"\n📦 Verificando archivos __init__.py:")
    init_dirs = [
        "unit", "unit/brass", "unit/common", "unit/correos", "unit/expedientes",
        "integration", "integration/brass", "integration/database", "integration/correos",
        "functional/access_sync", "functional/correos_workflows",
        "fixtures", "data"
    ]
    
    missing_inits = []
    for dir_path in init_dirs:
        init_file = tests_path / dir_path / "__init__.py"
        if init_file.exists():
            print(f"  ✅ {dir_path}/__init__.py")
        else:
            print(f"  ❌ {dir_path}/__init__.py")
            missing_inits.append(f"{dir_path}/__init__.py")
    
    # 6. Resumen final
    print(f"\n" + "="*60)
    print(f"📋 RESUMEN DE VALIDACIÓN")
    print(f"="*60)
    
    if not missing_dirs and not duplicates and not missing_inits:
        print(f"🎉 ¡Estructura perfectamente organizada!")
        print(f"✅ Todos los directorios creados")
        print(f"✅ No hay archivos duplicados")
        print(f"✅ Todos los __init__.py presentes")
        print(f"✅ {total_tests} archivos de test organizados")
    else:
        print(f"⚠️ Algunos problemas encontrados:")
        if missing_dirs:
            print(f"  • Directorios faltantes: {missing_dirs}")
        if duplicates:
            print(f"  • Archivos duplicados: {duplicates}")
        if missing_inits:
            print(f"  • __init__.py faltantes: {missing_inits}")
    
    # 7. Comandos útiles
    print(f"\n🚀 Comandos útiles para la nueva estructura:")
    print(f"  # Todos los tests")
    print(f"  pytest")
    print(f"  ")
    print(f"  # Por categoría")
    print(f"  pytest tests/unit/          # Tests unitarios")
    print(f"  pytest tests/integration/   # Tests de integración")
    print(f"  pytest tests/functional/    # Tests funcionales")
    print(f"  ")
    print(f"  # Por módulo específico")
    print(f"  pytest tests/unit/brass/    # Tests unitarios de brass")
    print(f"  pytest tests/unit/common/   # Tests unitarios comunes")
    print(f"  pytest tests/integration/correos/  # Tests de integración de correos")
    print(f"  ")
    print(f"  # Con marcadores")
    print(f"  pytest -m unit              # Solo tests unitarios")
    print(f"  pytest -m integration       # Solo tests de integración")
    print(f"  pytest -m functional        # Solo tests funcionales")
    print(f"  pytest -m correos           # Solo tests de correos")

if __name__ == "__main__":
    validate_test_structure()