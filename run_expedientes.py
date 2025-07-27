"""
Script para ejecutar la tarea diaria de expedientes
Adaptación del script legacy Expedientes.vbs
"""
import sys
import logging
import argparse
from pathlib import Path

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

from expedientes import ExpedientesManager
from common import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Función principal para ejecutar la tarea diaria de expedientes"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Ejecutar tarea diaria de expedientes')
    parser.add_argument('--forzar', '-f', action='store_true', 
                       help='Forzar ejecución independientemente de las condiciones normales')
    args = parser.parse_args()
    
    logger.info("Iniciando tarea diaria de expedientes")
    
    expedientes_manager = None
    
    try:
        # Crear instancia del gestor de expedientes
        expedientes_manager = ExpedientesManager()
        
        # Ejecutar tarea diaria (con o sin forzar según el parámetro)
        success = expedientes_manager.execute_daily_task(forzar_ejecucion=args.forzar)
        
        if success:
            if args.forzar:
                logger.info("Tarea diaria de expedientes completada exitosamente (ejecución forzada)")
                print("Tarea diaria de expedientes ejecutada exitosamente (ejecución forzada)")
            else:
                logger.info("Tarea diaria de expedientes completada exitosamente")
                print("Tarea diaria de expedientes ejecutada exitosamente")
            return 0
        else:
            logger.error("Error ejecutando la tarea diaria de expedientes")
            print("Error en la ejecución de la tarea diaria de expedientes")
            return 1
            
    except Exception as e:
        logger.error(f"Error inesperado en la tarea diaria de expedientes: {e}")
        print(f"Error crítico: {e}")
        return 1
        
    finally:
        # Cerrar conexiones
        if expedientes_manager:
            expedientes_manager.close_connections()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)