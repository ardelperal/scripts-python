#!/usr/bin/env python3
"""
Script principal para ejecutar la tarea BRASS
Adaptación del sistema legacy VBS a Python
"""
import sys
import argparse
from pathlib import Path

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from common.config import config
from common.utils import setup_logging
from brass.brass_manager import BrassManager

def main():
    """Función principal"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Ejecutar tarea BRASS')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Forzar ejecución aunque ya se haya ejecutado hoy')
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(config.log_level, config.log_file)
    
    try:
        # Crear instancia del gestor BRASS
        brass_manager = BrassManager()
        
        # Ejecutar tarea con modo forzado si se especifica
        success = brass_manager.execute_task(force=args.force)
        
        if success:
            print("Tarea BRASS ejecutada exitosamente")
            return 0
        else:
            print("Error en la ejecución de la tarea BRASS")
            return 1
            
    except Exception as e:
        print(f"Error crítico: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
