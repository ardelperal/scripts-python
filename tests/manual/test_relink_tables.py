#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de revinculación de tablas vinculadas
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from setup_local_environment import LocalEnvironmentSetup

def main():
    """Función principal de prueba"""
    
    # Configurar logging para ver detalles
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    print("=" * 60)
    print("PRUEBA DE REVINCULACIÓN DE TABLAS")
    print("=" * 60)
    print()
    
    try:
        # Crear instancia del setup
        setup = LocalEnvironmentSetup()
        
        # Mostrar configuración
        setup.show_configuration()
        
        print()
        print("🔗 Iniciando prueba de revinculación de tablas...")
        print()
        
        # Probar actualización de vínculos en todas las bases de datos locales
        success = setup.update_all_database_links()
        
        print()
        print("=" * 60)
        if success:
            print("✅ PRUEBA DE REVINCULACIÓN EXITOSA")
            print("Todos los vínculos han sido actualizados correctamente")
        else:
            print("⚠️ PRUEBA COMPLETADA CON ALGUNOS ERRORES")
            print("Revisa el log para más detalles")
        print("=" * 60)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ Prueba cancelada por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit(main())