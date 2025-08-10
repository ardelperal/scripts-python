#!/usr/bin/env python3
"""
Script principal para ejecutar la tarea BRASS
Adaptación del sistema original VBS a Python
"""
import sys
import argparse
from pathlib import Path

# Añadir el directorio raíz del proyecto al path para importaciones
project_root = Path(__file__).parent.parent
src_dir = project_root / 'src'
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.common.config import config
from src.common.utils import setup_logging
from src.brass.brass_task import BrassTask

def main():
    """Función principal"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Ejecutar tarea BRASS')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Forzar ejecución aunque ya se haya ejecutado hoy')
    parser.add_argument('--dry-run', action='store_true',
                       help='Modo simulación - no ejecuta la tarea real')
    args = parser.parse_args()
    
    # Configurar logging
    # setup_logging espera primero el archivo y luego el nivel
    setup_logging(log_file=config.log_file, level=config.log_level)
    
    try:
        with BrassTask() as task:
            if args.dry_run:
                print("Modo simulación - verificando si la tarea debe ejecutarse...")
                should_run = task.debe_ejecutarse()
                print(f"¿Debe ejecutarse la tarea BRASS? {'Sí' if should_run else 'No'}")
                return 0

            if args.force:
                print("Modo forzado - ejecutando tarea BRASS...")
                success = task.execute_specific_logic()
                if success:
                    task.marcar_como_completada()
            else:
                success = task.run()

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
