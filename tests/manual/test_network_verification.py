#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de verificación de red
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Agregar el directorio src al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_network_verification():
    """Prueba la verificación de accesibilidad de red"""
    
    # Cargar variables de entorno
    env_path = project_root / '.env'
    
    if not env_path.exists():
        logger.error(f"Archivo .env no encontrado en: {env_path}")
        return False
    
    load_dotenv(env_path)
    logger.info(f"Cargando configuración desde: {env_path}")
    
    # Importar la clase después de cargar el .env
    from setup_local_environment import LocalEnvironmentSetup
    
    try:
        setup = LocalEnvironmentSetup()
        
        logger.info("=== PRUEBA DE VERIFICACIÓN DE RED ===")
        
        # Mostrar configuración
        setup.show_configuration()
        
        # Verificar accesibilidad de red
        network_accessible = setup._check_network_accessibility()
        
        logger.info("=== RESULTADO DE LA PRUEBA ===")
        if network_accessible:
            logger.info("✅ Todas las ubicaciones de red son accesibles")
        else:
            logger.warning("⚠️ Algunas ubicaciones de red no son accesibles")
        
        return network_accessible
        
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}")
        return False

def test_database_discovery():
    """Prueba el descubrimiento de bases de datos desde .env"""
    
    # Cargar variables de entorno
    env_path = project_root / '.env'
    load_dotenv(env_path)
    
    from setup_local_environment import LocalEnvironmentSetup
    
    try:
        setup = LocalEnvironmentSetup()
        
        logger.info("=== PRUEBA DE DESCUBRIMIENTO DE BASES DE DATOS ===")
        
        databases = setup.databases
        logger.info(f"Bases de datos descubiertas: {len(databases)}")
        
        for db_name, (office_var, local_var, filename) in databases.items():
            logger.info(f"  {db_name}: {filename}")
            logger.info(f"    Oficina: {office_var}")
            logger.info(f"    Local: {local_var}")
        
        return len(databases) > 0
        
    except Exception as e:
        logger.error(f"❌ Error durante el descubrimiento: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("PRUEBA DE VERIFICACIÓN DE RED Y CONFIGURACIÓN")
    print("=" * 60)
    print()
    
    try:
        # Prueba 1: Descubrimiento de bases de datos
        logger.info("🔍 Iniciando prueba de descubrimiento de bases de datos...")
        discovery_ok = test_database_discovery()
        
        if not discovery_ok:
            logger.error("❌ Falló el descubrimiento de bases de datos")
            return 1
        
        print()
        
        # Prueba 2: Verificación de red
        logger.info("🌐 Iniciando prueba de verificación de red...")
        network_ok = test_network_verification()
        
        print()
        print("=" * 60)
        print("RESUMEN DE PRUEBAS:")
        print(f"  Descubrimiento de BD: {'✅' if discovery_ok else '❌'}")
        print(f"  Verificación de red: {'✅' if network_ok else '❌'}")
        print("=" * 60)
        
        if discovery_ok and network_ok:
            print("✅ TODAS LAS PRUEBAS PASARON")
            print("El sistema está listo para configurar el entorno local")
            return 0
        else:
            print("⚠️ ALGUNAS PRUEBAS FALLARON")
            if not network_ok:
                print("Nota: La verificación de red puede fallar si no estás conectado a la red de oficina")
            return 1
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit(main())