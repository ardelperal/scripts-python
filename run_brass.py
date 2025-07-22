#!/usr/bin/env python3
"""
Script principal para ejecutar la tarea BRASS
Adaptación del sistema legacy VBS a Python
"""
import sys
from pathlib import Path

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from common import config, setup_logging
from brass import BrassManager

def main():
    """Función principal"""
    # Configurar logging
    setup_logging(config.log_level, config.log_file)
    
    try:
        # Crear instancia del gestor BRASS
        brass_manager = BrassManager()
        
        # Ejecutar tarea
        success = brass_manager.execute_task()
        
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
