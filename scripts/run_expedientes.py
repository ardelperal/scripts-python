"""Script de entrada para la ejecución de la Tarea de Expedientes.

Responsabilidad única: instanciar y ejecutar la clase ExpedientesTask.

Ejecución recomendada (sin tocar sys.path):
    python -m scripts.run_expedientes

Requiere que el directorio del proyecto (que contiene 'src' y 'scripts') esté en PYTHONPATH (lo está al ejecutar desde raíz con -m).
"""
import sys
import logging
from pathlib import Path

from src.common.utils import setup_logging
from src.expedientes.expedientes_task import ExpedientesTask

def main():
    """
    Función principal que instancia y ejecuta la Tarea de Expedientes.
    """
    # 1. Configurar el logging centralizado
    setup_logging(log_file=Path('logs/expedientes.log'))
    logger = logging.getLogger()

    logger.info("===============================================")
    logger.info("=      INICIANDO TAREA DE EXPEDIENTES         =")
    logger.info("===============================================")

    exit_code = 0
    
    try:
        # 2. Usar un context manager para que las conexiones se cierren solas
        with ExpedientesTask() as task:
            # 3. Verificar si la tarea debe ejecutarse
            if task.debe_ejecutarse():
                logger.info("La tarea de Expedientes requiere ejecución.")
                # 4. Ejecutar la lógica y marcar como completada si tiene éxito
                if task.execute_specific_logic():
                    task.marcar_como_completada()
                    logger.info("Tarea de Expedientes completada y marcada exitosamente.")
                else:
                    logger.error("La lógica específica de la tarea de Expedientes falló.")
                    exit_code = 1
            else:
                logger.info("La tarea de Expedientes no requiere ejecución hoy.")
    except Exception as e:
        # Captura de errores no controlados en el nivel más alto
        logging.getLogger().critical(f"Error fatal no controlado en la ejecución de la tarea de Expedientes: {e}", exc_info=True)
        exit_code = 1

    logger.info("Finalizada la ejecución de la tarea de Expedientes.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()