#!/usr/bin/env python3
"""
Script de prueba para el informe mensual de riesgos
Fuerza la ejecución del informe mensual independientemente de si ya se ejecutó
"""
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path para importaciones
sys.path.insert(0, str(Path(__file__).parent))

from common.config import Config
from common.utils import setup_logging
from riesgos.riesgos_manager import RiesgosManager


def main():
    """Función principal para probar el informe mensual"""
    # Configurar logging
    logger = setup_logging("test_monthly_report")

    if not logger:
        print("Error: No se pudo configurar el logging")
        sys.exit(1)

    try:
        logger.info("=== INICIANDO PRUEBA DE INFORME MENSUAL ===")

        # Configurar entorno
        config = Config()

        # Crear instancia del gestor de riesgos
        manager = RiesgosManager(config, logger)

        # Conectar a las bases de datos
        manager.connect_to_database()

        try:
            logger.info("Forzando ejecución del informe mensual...")

            # Modificar temporalmente la verificación para forzar ejecución
            # Guardamos el método original
            original_method = manager.should_execute_monthly_quality_task

            # Reemplazamos temporalmente con una función que siempre devuelve True
            manager.should_execute_monthly_quality_task = lambda: True

            try:
                # Ejecutar informe mensual
                result = manager.execute_monthly_report()
                logger.info(f"Resultado de la ejecución: {result}")
            finally:
                # Restaurar el método original
                manager.should_execute_monthly_quality_task = original_method
        finally:
            # Desconectar de las bases de datos
            manager.disconnect_from_database()

        logger.info("=== PRUEBA DE INFORME MENSUAL COMPLETADA ===")

    except Exception as e:
        logger.error(f"Error en la prueba del informe mensual: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
