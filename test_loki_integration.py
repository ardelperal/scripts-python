#!/usr/bin/env python3
"""
Test simple para verificar la integración con Loki
"""

import os
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.common.utils import setup_logging

def test_loki_integration():
    """Test básico para verificar que la función setup_logging funciona con Loki"""
    
    print("🧪 Probando integración con Loki...")
    
    # Test 1: Sin variables de entorno (debería usar valores por defecto)
    print("\n1. Test sin variables de entorno:")
    logger1 = setup_logging("test_app", "INFO")
    logger1.info("Test log sin variables de entorno")
    print("✅ Logger creado correctamente sin variables de entorno")
    
    # Test 2: Con variables de entorno configuradas
    print("\n2. Test con variables de entorno:")
    os.environ['LOKI_URL'] = 'http://localhost:3100/loki/api/v1/push'
    os.environ['ENVIRONMENT'] = 'testing'
    
    logger2 = setup_logging("test_app_env", "DEBUG")
    logger2.info("Test log con variables de entorno configuradas")
    logger2.debug("Test debug log")
    logger2.warning("Test warning log")
    print("✅ Logger creado correctamente con variables de entorno")
    
    # Test 3: Con archivo de log
    print("\n3. Test con archivo de log:")
    log_file = Path("logs/test_loki.log")
    logger3 = setup_logging("test_app_file", "INFO", log_file)
    logger3.info("Test log con archivo")
    logger3.error("Test error log")
    print(f"✅ Logger creado correctamente con archivo: {log_file}")
    
    # Verificar que el archivo se creó
    if log_file.exists():
        print(f"✅ Archivo de log creado: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📄 Contenido del archivo de log:\n{content}")
    else:
        print("❌ Archivo de log no se creó")
    
    print("\n🎉 Todos los tests de integración con Loki completados!")
    
    # Limpiar variables de entorno
    if 'LOKI_URL' in os.environ:
        del os.environ['LOKI_URL']
    if 'ENVIRONMENT' in os.environ:
        del os.environ['ENVIRONMENT']

if __name__ == "__main__":
    test_loki_integration()