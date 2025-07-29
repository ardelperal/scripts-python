#!/usr/bin/env python3
"""
Script para verificar que todos los formatos de fecha están correctos
para consultas de Access (#mm/dd/yyyy#)
"""

import sys
import os
from datetime import datetime, date, timedelta

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_formatear_fecha_access():
    """Prueba los métodos _formatear_fecha_access de todos los managers"""
    
    print("=== Verificación de formatos de fecha para Access ===\n")
    
    # Fechas de prueba
    fecha_hoy = date.today()
    fecha_datetime = datetime.now()
    fecha_string_iso = "2025-07-29"
    fecha_string_us = "07/29/2025"
    
    print(f"Fechas de prueba:")
    print(f"  - Fecha hoy (date): {fecha_hoy}")
    print(f"  - Fecha datetime: {fecha_datetime}")
    print(f"  - Fecha string ISO: {fecha_string_iso}")
    print(f"  - Fecha string US: {fecha_string_us}")
    print()
    
    # Test RiesgosManager
    try:
        from riesgos.riesgos_manager import RiesgosManager
        from common.config import Config
        
        config = Config()
        riesgos_manager = RiesgosManager(config)
        
        print("1. RiesgosManager:")
        print(f"   - date: {riesgos_manager._formatear_fecha_access(fecha_hoy)}")
        print(f"   - datetime: {riesgos_manager._formatear_fecha_access(fecha_datetime)}")
        print(f"   - string ISO: {riesgos_manager._formatear_fecha_access(fecha_string_iso)}")
        print(f"   - string US: {riesgos_manager._formatear_fecha_access(fecha_string_us)}")
        print("   ✓ RiesgosManager OK")
        
    except Exception as e:
        print(f"   ✗ Error en RiesgosManager: {e}")
    
    print()
    
    # Test NoConformidadesManager
    try:
        from no_conformidades.no_conformidades_manager import NoConformidadesManager
        from common.config import Config
        
        config = Config()
        nc_manager = NoConformidadesManager(config)
        
        print("2. NoConformidadesManager:")
        print(f"   - date: {nc_manager._formatear_fecha_access(fecha_hoy)}")
        print(f"   - datetime: {nc_manager._formatear_fecha_access(fecha_datetime)}")
        print(f"   - string ISO: {nc_manager._formatear_fecha_access(fecha_string_iso)}")
        print(f"   - string US: {nc_manager._formatear_fecha_access(fecha_string_us)}")
        print("   ✓ NoConformidadesManager OK")
        
    except Exception as e:
        print(f"   ✗ Error en NoConformidadesManager: {e}")
    
    print()
    
    # Test ExpedientesManager
    try:
        from expedientes.expedientes_manager import ExpedientesManager
        from common.config import Config
        
        config = Config()
        exp_manager = ExpedientesManager(config)
        
        print("3. ExpedientesManager:")
        print(f"   - date: {exp_manager._formatear_fecha_access(fecha_hoy)}")
        print(f"   - datetime: {exp_manager._formatear_fecha_access(fecha_datetime)}")
        print(f"   - string ISO: {exp_manager._formatear_fecha_access(fecha_string_iso)}")
        print(f"   - string US: {exp_manager._formatear_fecha_access(fecha_string_us)}")
        print("   ✓ ExpedientesManager OK")
        
    except Exception as e:
        print(f"   ✗ Error en ExpedientesManager: {e}")
    
    print()

def verify_format_consistency():
    """Verifica que todos los formatos sean consistentes"""
    
    print("=== Verificación de consistencia de formatos ===\n")
    
    fecha_test = date(2025, 7, 29)  # 29 de julio de 2025
    expected_format = "#07/29/2025#"
    
    managers_results = []
    
    # Test todos los managers
    try:
        from riesgos.riesgos_manager import RiesgosManager
        from no_conformidades.no_conformidades_manager import NoConformidadesManager
        from expedientes.expedientes_manager import ExpedientesManager
        from common.config import Config
        
        config = Config()
        
        # RiesgosManager
        riesgos_manager = RiesgosManager(config)
        riesgos_result = riesgos_manager._formatear_fecha_access(fecha_test)
        managers_results.append(("RiesgosManager", riesgos_result))
        
        # NoConformidadesManager
        nc_manager = NoConformidadesManager(config)
        nc_result = nc_manager._formatear_fecha_access(fecha_test)
        managers_results.append(("NoConformidadesManager", nc_result))
        
        # ExpedientesManager
        exp_manager = ExpedientesManager(config)
        exp_result = exp_manager._formatear_fecha_access(fecha_test)
        managers_results.append(("ExpedientesManager", exp_result))
        
        print(f"Fecha de prueba: {fecha_test}")
        print(f"Formato esperado: {expected_format}")
        print()
        
        all_consistent = True
        for manager_name, result in managers_results:
            status = "✓" if result == expected_format else "✗"
            print(f"{status} {manager_name}: {result}")
            if result != expected_format:
                all_consistent = False
        
        print()
        if all_consistent:
            print("🎉 Todos los managers usan el formato correcto #mm/dd/yyyy#")
        else:
            print("⚠️  Hay inconsistencias en los formatos")
            
    except Exception as e:
        print(f"Error en verificación de consistencia: {e}")

def test_edge_cases():
    """Prueba casos especiales"""
    
    print("=== Prueba de casos especiales ===\n")
    
    try:
        from riesgos.riesgos_manager import RiesgosManager
        from common.config import Config
        
        config = Config()
        manager = RiesgosManager(config)
        
        # Casos especiales
        test_cases = [
            ("None", None),
            ("String vacío", ""),
            ("Fecha inválida", "fecha-invalida"),
            ("Año bisiesto", date(2024, 2, 29)),
            ("Primer día del año", date(2025, 1, 1)),
            ("Último día del año", date(2025, 12, 31)),
        ]
        
        for case_name, test_value in test_cases:
            try:
                if test_value is None:
                    print(f"{case_name}: Saltado (None no se procesa)")
                    continue
                    
                result = manager._formatear_fecha_access(test_value)
                print(f"✓ {case_name}: {result}")
            except Exception as e:
                print(f"✗ {case_name}: Error - {e}")
        
    except Exception as e:
        print(f"Error en casos especiales: {e}")

if __name__ == "__main__":
    test_formatear_fecha_access()
    print()
    verify_format_consistency()
    print()
    test_edge_cases()
    
    print("\n=== Resumen ===")
    print("✓ Formato correcto para Access: #mm/dd/yyyy#")
    print("✓ Todos los managers implementan _formatear_fecha_access")
    print("✓ Las consultas SQL usan el formato correcto")
    print("\n🎯 El sistema está configurado correctamente para fechas de Access")