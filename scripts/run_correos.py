#!/usr/bin/env python3
"""
Script para enviar correos no enviados
Adaptación del script legacy EnviarCorreoNoEnviado.vbs
"""
import sys
import logging
from pathlib import Path

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.common.config import config
from src.common.utils import setup_logging
from correos.correos_manager import CorreosManager


def main():
    """Función principal"""
    # Configurar logging
    setup_logging(config.log_level, config.log_file)
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando script de envío de correos no enviados")
    
    try:
        # Verificar que existe la base de datos de correos
        if not Path(config.db_correos_path).exists():
            logger.error(f"No se encuentra la base de datos de correos: {config.db_correos_path}")
            return 1
        
        # Crear instancia del gestor de correos
        correos_manager = CorreosManager()
        
        # Ejecutar el envío de correos pendientes
        correos_enviados = correos_manager.enviar_correos_no_enviados()
        
        if correos_enviados >= 0:
            logger.info(f"Script completado exitosamente. Correos enviados: {correos_enviados}")
            return 0
        else:
            logger.error("Error en la ejecución del script de envío de correos")
            return 1
            
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)