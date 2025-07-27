#!/usr/bin/env python3
"""
Script principal para ejecutar la tarea de No Conformidades
Adaptación del sistema legacy VBS a Python
"""
import sys
import argparse
from pathlib import Path

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from common import config, setup_logging
from noconformidades import NoConformidadesManager

def main():
    """Función principal"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Ejecutar tarea de No Conformidades')
    parser.add_argument('--forzar', '-f', action='store_true', 
                       help='Forzar ejecución independientemente del día de la semana')
    args = parser.parse_args()
    
    # Configurar logging
    logger = setup_logging(config.log_level, config.log_file)
    
    try:
        # Crear instancia del manager
        manager = NoConformidadesManager(config, logger)
        
        # Ejecutar tarea (con o sin forzar según el parámetro)
        success = manager.lanzar(forzar_ejecucion=args.forzar)
        
        if success:
            if args.forzar:
                print("Tarea de No Conformidades ejecutada exitosamente (ejecución forzada)")
            else:
                print("Tarea de No Conformidades ejecutada exitosamente")
            return 0
        else:
            print("Error en la ejecución de la tarea de No Conformidades")
            return 1
            
    except Exception as e:
        print(f"Error crítico: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)