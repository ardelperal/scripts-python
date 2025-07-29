#!/usr/bin/env python3
"""
Script para verificar que las consultas SQL corregidas siguen la lógica del VBScript legacy.
Verifica que se use INNER JOIN con TbNCAccionesRealizadas en lugar de NOT EXISTS.
"""

import os
import re
from pathlib import Path

def verificar_consultas_corregidas():
    """Verifica que las consultas SQL estén corregidas según la lógica del VBScript legacy"""
    
    print("🔍 Verificando correcciones en las consultas SQL...")
    print("=" * 60)
    
    # Archivo a verificar
    archivo_manager = Path("src/no_conformidades/no_conformidades_manager.py")
    
    if not archivo_manager.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_manager}")
        return False
    
    with open(archivo_manager, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Verificaciones
    verificaciones_exitosas = 0
    total_verificaciones = 0
    
    # 1. Verificar que NO hay NOT EXISTS
    total_verificaciones += 1
    not_exists_matches = re.findall(r'NOT EXISTS', contenido, re.IGNORECASE)
    if not not_exists_matches:
        print("✅ 1. No se encontraron consultas con NOT EXISTS")
        verificaciones_exitosas += 1
    else:
        print(f"❌ 1. Se encontraron {len(not_exists_matches)} instancias de NOT EXISTS")
        for i, match in enumerate(not_exists_matches, 1):
            print(f"   - Instancia {i}: {match}")
    
    # 2. Verificar que hay INNER JOIN con TbNCAccionesRealizadas
    total_verificaciones += 1
    inner_join_matches = re.findall(r'INNER JOIN TbNCAccionesRealizadas', contenido, re.IGNORECASE)
    if inner_join_matches:
        print(f"✅ 2. Se encontraron {len(inner_join_matches)} INNER JOIN con TbNCAccionesRealizadas")
        verificaciones_exitosas += 1
    else:
        print("❌ 2. No se encontraron INNER JOIN con TbNCAccionesRealizadas")
    
    # 3. Verificar que se usa FechaFinReal IS NULL
    total_verificaciones += 1
    fecha_fin_real_matches = re.findall(r'FechaFinReal IS NULL', contenido, re.IGNORECASE)
    if fecha_fin_real_matches:
        print(f"✅ 3. Se encontraron {len(fecha_fin_real_matches)} condiciones 'FechaFinReal IS NULL'")
        verificaciones_exitosas += 1
    else:
        print("❌ 3. No se encontraron condiciones 'FechaFinReal IS NULL'")
    
    # 4. Verificar que se usa ar.FechaFinPrevista en lugar de ac.FechaFinalUltima
    total_verificaciones += 1
    fecha_fin_prevista_matches = re.findall(r'ar\.FechaFinPrevista', contenido, re.IGNORECASE)
    if fecha_fin_prevista_matches:
        print(f"✅ 4. Se encontraron {len(fecha_fin_prevista_matches)} referencias a 'ar.FechaFinPrevista'")
        verificaciones_exitosas += 1
    else:
        print("❌ 4. No se encontraron referencias a 'ar.FechaFinPrevista'")
    
    # 5. Verificar que NO se usa ac.FechaFinalUltima en las consultas corregidas
    total_verificaciones += 1
    fecha_final_ultima_matches = re.findall(r'ac\.FechaFinalUltima', contenido, re.IGNORECASE)
    if not fecha_final_ultima_matches:
        print("✅ 5. No se encontraron referencias a 'ac.FechaFinalUltima' en las consultas")
        verificaciones_exitosas += 1
    else:
        print(f"❌ 5. Se encontraron {len(fecha_final_ultima_matches)} referencias a 'ac.FechaFinalUltima'")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumen: {verificaciones_exitosas}/{total_verificaciones} verificaciones exitosas")
    
    if verificaciones_exitosas == total_verificaciones:
        print("🎉 ¡Todas las correcciones están aplicadas correctamente!")
        print("✅ Las consultas SQL ahora siguen la lógica del VBScript legacy")
        return True
    else:
        print("⚠️  Algunas correcciones necesitan revisión")
        return False

def mostrar_consultas_corregidas():
    """Muestra las consultas SQL corregidas"""
    
    print("\n🔍 Consultas SQL corregidas:")
    print("=" * 60)
    
    archivo_manager = Path("src/no_conformidades/no_conformidades_manager.py")
    
    if not archivo_manager.exists():
        print(f"❌ Error: No se encuentra el archivo {archivo_manager}")
        return
    
    with open(archivo_manager, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar las consultas SQL
    consultas = re.findall(r'sql_query = f"""(.*?)"""', contenido, re.DOTALL)
    
    for i, consulta in enumerate(consultas, 1):
        if 'TbNCAccionesRealizadas' in consulta:
            print(f"\n📝 Consulta {i} (corregida):")
            print("-" * 40)
            # Limpiar la consulta para mejor visualización
            consulta_limpia = consulta.strip().replace('            ', '  ')
            print(consulta_limpia)

if __name__ == "__main__":
    print("🚀 Verificador de Correcciones SQL - VBScript Legacy")
    print("=" * 60)
    
    # Verificar correcciones
    correcciones_ok = verificar_consultas_corregidas()
    
    # Mostrar consultas corregidas
    mostrar_consultas_corregidas()
    
    print("\n" + "=" * 60)
    if correcciones_ok:
        print("✅ VERIFICACIÓN COMPLETADA: Las consultas están corregidas correctamente")
    else:
        print("❌ VERIFICACIÓN FALLIDA: Revisar las correcciones pendientes")