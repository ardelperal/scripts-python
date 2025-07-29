#!/usr/bin/env python3
"""
Script de prueba simplificado para verificar las consultas SQL del manager
"""

import os
import sys
sys.path.append('src')

from no_conformidades.no_conformidades_manager import NoConformidadesManager

def test_manager_queries():
    """Prueba las consultas del manager directamente"""
    print("=== Probando consultas del NoConformidadesManager ===")
    
    manager = NoConformidadesManager()
    
    try:
        # Conectar a las bases de datos
        manager.conectar_bases_datos()
        
        # Probar ARAPs próximas a vencer
        print("\n1. Probando ARAPs próximas a vencer...")
        arapcs = manager.obtener_arapc_proximas_vencer()
        print(f"✓ ARAPs encontradas: {len(arapcs)}")
        
        # Probar NCs próximas a caducar por eficacia
        print("\n2. Probando NCs próximas a caducar por eficacia...")
        ncs_eficacia = manager.obtener_nc_resueltas_pendientes_eficacia()
        print(f"✓ NCs eficacia encontradas: {len(ncs_eficacia)}")
        
        # Probar NCs sin acciones
        print("\n3. Probando NCs sin acciones...")
        ncs_sin_acciones = manager.obtener_nc_registradas_sin_acciones()
        print(f"✓ NCs sin acciones encontradas: {len(ncs_sin_acciones)}")
        
        # Probar estadísticas
        print("\n4. Probando estadísticas...")
        estadisticas = manager.obtener_estadisticas_nc()
        print(f"✓ Estadísticas obtenidas: {estadisticas}")
        
        print("\n✅ Todas las consultas funcionan correctamente!")
        
    except Exception as e:
        print(f"✗ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        manager.desconectar_bases_datos()

if __name__ == "__main__":
    test_manager_queries()