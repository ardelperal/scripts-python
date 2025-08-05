#!/usr/bin/env python3
"""
Script de ejecución para el módulo de Tareas
Adaptación del script legacy EnviarCorreoTareas.vbs
"""

import sys
import logging
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from correo_tareas import CorreoTareasManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent.parent / "logs" / "run_correo_tareas.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Función principal"""
    logger.info("=== Iniciando script de Tareas ===")
    
    try:
        # Crear instancia del manager
        tareas_manager = CorreoTareasManager()
        
        # Ejecutar tarea de envío de correos
        success = tareas_manager.execute_continuous_task()
        
        if success:
            logger.info("Script de Tareas completado exitosamente")
            return 0
        else:
            logger.error("Script de Tareas completado con errores")
            return 1
            
    except Exception as e:
        logger.error(f"Error crítico en script de Tareas: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)