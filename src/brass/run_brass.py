"""
Script principal para ejecutar la tarea BRASS
"""
import logging
import os
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio src al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from brass.brass_task import BrassTask

def main():
    """Función principal"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Iniciando ejecución de BRASS")
        
        # Crear y ejecutar la tarea
        task = BrassTask()
        success = task.execute()
        
        if success:
            logger.info("BRASS ejecutado correctamente")
            return 0
        else:
            logger.error("Error en la ejecución de BRASS")
            return 1
            
    except Exception as e:
        logger.error(f"Error crítico en BRASS: {e}")
        return 1
    finally:
        # Cerrar conexiones
        try:
            task.close_connections()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)