"""
Punto de entrada para la ejecución de la tarea de No Conformidades
"""
import logging
import os
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('no_conformidades.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Agregar el directorio src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from no_conformidades.no_conformidades_task import NoConformidadesTask


def main():
    """
    Función principal para ejecutar la tarea de No Conformidades
    """
    task = None
    try:
        logger.info("=== INICIANDO TAREA NO CONFORMIDADES ===")
        
        # Crear y ejecutar la tarea
        task = NoConformidadesTask()
        success = task.execute()
        
        if success:
            logger.info("=== TAREA NO CONFORMIDADES COMPLETADA EXITOSAMENTE ===")
            return 0
        else:
            logger.error("=== ERROR EN LA EJECUCIÓN DE LA TAREA NO CONFORMIDADES ===")
            return 1
            
    except Exception as e:
        logger.error(f"Error crítico en la tarea No Conformidades: {e}")
        return 1
    finally:
        # Cerrar conexiones
        if task:
            try:
                task.close_connections()
                logger.info("Conexiones cerradas correctamente")
            except Exception as e:
                logger.warning(f"Error cerrando conexiones: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)