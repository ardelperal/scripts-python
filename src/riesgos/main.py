#!/usr/bin/env python3
"""
Script principal para el módulo de Gestión de Riesgos

Este script ejecuta las tareas automatizadas del sistema de Gestión de Riesgos:
- Informes técnicos semanales personalizados
- Informes de calidad semanales detallados
- Informes de calidad mensuales de alto nivel

Uso:
    python main.py [--technical] [--quality] [--monthly] [--force]

Argumentos:
    --technical: Ejecutar informes técnicos semanales
    --quality: Ejecutar informes de calidad semanales
    --monthly: Ejecutar informe mensual de calidad
    --force: Forzar ejecución aunque ya se haya ejecutado recientemente

Nota: Se pueden especificar múltiples argumentos para ejecutar varias tareas a la vez.
      Si no se especifica ningún argumento, se ejecutarán todas las tareas según corresponda.
"""

import argparse
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..common.config import Config
from ..common.utils import setup_logging
from .riesgos_manager import RiesgosManager


def main():
    """Función principal del script."""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Gestión de Riesgos - Informes Automatizados"
    )
    parser.add_argument(
        "--technical", action="store_true", help="Ejecutar informes técnicos semanales"
    )
    parser.add_argument(
        "--quality", action="store_true", help="Ejecutar informes de calidad semanales"
    )
    parser.add_argument(
        "--monthly", action="store_true", help="Ejecutar informe mensual de calidad"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar ejecución aunque ya se haya ejecutado recientemente",
    )

    args = parser.parse_args()

    # Configurar logging
    logger = setup_logging("riesgos")

    if not logger:
        print("Error: No se pudo configurar el logging")
        sys.exit(1)

    try:
        logger.info("=== INICIANDO GESTIÓN DE RIESGOS ===")

        # Inicializar configuración
        config = Config()

        # Crear gestor de riesgos
        riesgos_manager = RiesgosManager(config, logger)

        # Conectar a bases de datos
        riesgos_manager.connect_to_database()

        # Delegar toda la lógica de ejecución al manager
        # El manager ya sabe cómo interpretar los flags de forzado
        results = riesgos_manager.run_daily_tasks(
            force_technical=args.technical or args.force,
            force_quality=args.quality or args.force,
            force_monthly=args.monthly or args.force,
        )

        # Determinar éxito general
        success = (
            any(results.values())
            if any([args.technical, args.quality, args.monthly])
            else all(results.values())
        )

        # Desconectar de bases de datos
        riesgos_manager.disconnect_from_database()

        # Obtener estadísticas de errores
        stats = riesgos_manager.get_summary_stats()

        # Reportar estadísticas finales
        logger.info("=== ESTADÍSTICAS DE EJECUCIÓN ===")
        logger.info(f"Total de errores: {stats['error_count']}")
        logger.info(f"Total de warnings: {stats['warning_count']}")

        if stats["has_errors"]:
            logger.error(
                f"🚨 SE DETECTARON {stats['error_count']} ERRORES DURANTE LA EJECUCIÓN"
            )
            logger.error("Revisa el archivo de logs de errores SQL para más detalles")

        if stats["has_warnings"]:
            logger.warning(
                f"⚠️ SE DETECTARON {stats['warning_count']} WARNINGS DURANTE LA EJECUCIÓN"
            )

        if success and not stats["has_errors"]:
            logger.info("=== GESTIÓN DE RIESGOS COMPLETADA EXITOSAMENTE ===")
            sys.exit(0)
        else:
            if stats["has_errors"]:
                logger.error("=== GESTIÓN DE RIESGOS COMPLETADA CON ERRORES ===")
            else:
                logger.error("=== GESTIÓN DE RIESGOS COMPLETADA CON FALLOS ===")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error crítico en gestión de riesgos: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
