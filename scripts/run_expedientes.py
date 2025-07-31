"""
Script para ejecutar la tarea diaria de expedientes
Adaptación del script legacy Expedientes.vbs
"""
import sys
import logging
from pathlib import Path

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.expedientes.expedientes_manager import ExpedientesManager
from src.common.config import config

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
    logger.info("Iniciando tarea diaria de expedientes")
    
    expedientes_manager = None
    
    try:
        # Crear instancia del gestor de expedientes
        expedientes_manager = ExpedientesManager()
        
        # Ejecutar tarea diaria
        success = expedientes_manager.execute_daily_task()
        
        if success:
            logger.info("Tarea diaria de expedientes completada exitosamente")
            return 0
        else:
            logger.error("Error ejecutando la tarea diaria de expedientes")
            return 1
            
    except Exception as e:
        logger.error(f"Error inesperado en la tarea diaria de expedientes: {e}")
        return 1
        
    finally:
        # Cerrar conexiones
        if expedientes_manager:
            expedientes_manager.close_connections()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)