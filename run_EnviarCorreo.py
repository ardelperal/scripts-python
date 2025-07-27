#!/usr/bin/env python3
"""
Script principal para ejecutar la tarea de envío de correos
Adaptación del sistema legacy VBS a Python
"""
import sys
import argparse
from pathlib import Path

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from common import config, setup_logging
from correos import CorreosManager

def main():
    """Función principal"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Ejecutar tarea de envío de correos')
    parser.add_argument('--forzar', '-f', action='store_true', 
                       help='Forzar ejecución independientemente de las condiciones normales')
    args = parser.parse_args()
    
    # Configurar logging
    logger = setup_logging(config.log_level, config.log_file)
    
    try:
        # Crear instancia del gestor de correos
        correos_manager = CorreosManager(logger)
        
        # Ejecutar tarea diaria (con o sin forzar según el parámetro)
        success = correos_manager.ejecutar_tarea_diaria(forzar_ejecucion=args.forzar)
        
        if success:
            if args.forzar:
                print("Tarea de envío de correos ejecutada exitosamente (ejecución forzada)")
            else:
                print("Tarea de envío de correos ejecutada exitosamente")
            return 0
        else:
            print("Error en la ejecución de la tarea de envío de correos")
            return 1
            
    except Exception as e:
        print(f"Error crítico: {e}")
        return 1
    
    finally:
        # Cerrar conexiones si existen
        try:
            correos_manager.close_connections()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)