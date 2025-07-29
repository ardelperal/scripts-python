#!/usr/bin/env python3
"""
Script para verificar que todos los formatos de fecha están correctos
para consultas de Access (#mm/dd/yyyy#)
"""

import re
import os

def check_formatear_fecha_access_methods():
    """Verifica que todos los métodos _formatear_fecha_access usen el formato correcto"""
    
    print("=== Verificación de métodos _formatear_fecha_access ===\n")
    
    files_to_check = [
        "src/riesgos/riesgos_manager.py",
        "src/no_conformidades/no_conformidades_manager.py", 
        "src/expedientes/expedientes_manager.py"
    ]
    
    correct_format_pattern = r"strftime\(['\"]%m/%d/%Y['\"]\)"
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"Verificando {file_path}:")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar el método _formatear_fecha_access
            method_pattern = r"def _formatear_fecha_access\(.*?\):(.*?)(?=def|\Z)"
            method_match = re.search(method_pattern, content, re.DOTALL)
            
            if method_match:
                method_content = method_match.group(1)
                
                # Verificar que use el formato correcto
                if re.search(correct_format_pattern, method_content):
                    print("  ✓ Usa formato correcto: strftime('%m/%d/%Y')")
                else:
                    print("  ✗ No usa el formato correcto")
                
                # Verificar que envuelva con #
                if "#" in method_content and "f\"#{" in method_content:
                    print("  ✓ Envuelve la fecha con # correctamente")
                else:
                    print("  ✗ No envuelve la fecha con #")
                    
            else:
                print("  ✗ Método _formatear_fecha_access no encontrado")
        else:
            print(f"  ✗ Archivo no encontrado: {file_path}")
        
        print()

def check_sql_queries_for_hardcoded_dates():
    """Busca fechas hardcodeadas en consultas SQL"""
    
    print("=== Verificación de fechas hardcodeadas en SQL ===\n")
    
    # Buscar archivos Python en src
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                    except:
                        continue
                
                # Buscar patrones de fechas incorrectos en SQL
                wrong_patterns = [
                    r"WHERE.*\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
                    r"WHERE.*\d{2}/\d{2}/\d{4}",  # DD/MM/YYYY
                    r"AND.*\d{4}-\d{2}-\d{2}",    # YYYY-MM-DD en AND
                    r"AND.*\d{2}/\d{2}/\d{4}",    # DD/MM/YYYY en AND
                ]
                
                found_issues = False
                for pattern in wrong_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        if not found_issues:
                            print(f"⚠️  Posibles fechas incorrectas en {file_path}:")
                            found_issues = True
                        for match in matches:
                            print(f"    {match}")
                
                if found_issues:
                    print()

def check_correct_date_usage():
    """Verifica el uso correcto de fechas en formato Access"""
    
    print("=== Verificación de uso correcto de fechas ===\n")
    
    # Buscar archivos Python en src
    correct_usage_count = 0
    
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                    except:
                        continue
                
                # Buscar uso de _formatear_fecha_access
                if "_formatear_fecha_access" in content:
                    matches = re.findall(r".*_formatear_fecha_access.*", content)
                    if matches:
                        correct_usage_count += len(matches)
                        print(f"✓ {file_path}: {len(matches)} usos de _formatear_fecha_access")
    
    print(f"\nTotal de usos correctos encontrados: {correct_usage_count}")

def verify_access_format_examples():
    """Verifica ejemplos de formato Access en el código"""
    
    print("\n=== Ejemplos de formato Access encontrados ===\n")
    
    access_format_pattern = r"#\d{2}/\d{2}/\d{4}#"
    
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                    except:
                        continue
                
                matches = re.findall(access_format_pattern, content)
                if matches:
                    print(f"✓ {file_path}:")
                    for match in matches:
                        print(f"    {match}")
                    print()

if __name__ == "__main__":
    check_formatear_fecha_access_methods()
    check_sql_queries_for_hardcoded_dates()
    check_correct_date_usage()
    verify_access_format_examples()
    
    print("=== Resumen Final ===")
    print("✓ Verificación completada")
    print("✓ Formato Access requerido: #mm/dd/yyyy#")
    print("✓ Método estándar: _formatear_fecha_access()")
    print("🎯 Sistema configurado para fechas de Access")