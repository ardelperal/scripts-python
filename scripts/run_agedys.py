#!/usr/bin/env python3
"""
Script principal para ejecutar las tareas de AGEDYS
Adaptación del script legacy AGEDYS.VBS a Python

Uso:
    python run_agedys.py                    # Ejecución normal (verifica horarios)
    python run_agedys.py --force            # Fuerza ejecución independientemente del horario
    python run_agedys.py --dry-run          # Simula ejecución sin enviar emails
"""

import sys
import argparse
import logging
from pathlib import Path

# Añadir el directorio src al path para importaciones
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from common.logger import setup_logger
from agedys.agedys_manager import AgedysManager


def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Script para ejecutar tareas de AGEDYS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                    # Ejecución normal (verifica horarios)
  %(prog)s --force            # Fuerza ejecución independientemente del horario
  %(prog)s --dry-run          # Simula ejecución sin enviar emails
        """
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Fuerza la ejecución independientemente del horario'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Simula la ejecución sin enviar emails reales'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Habilita logging detallado'
    )
    
    return parser.parse_args()


def main():
    """Función principal"""
    # Parsear argumentos
    args = parse_arguments()
    
    # Configurar logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(__name__, level=log_level)
    
    print("🚀 INICIANDO SISTEMA AGEDYS")
    print("=" * 50)
    logger.info("=== INICIANDO TAREAS AGEDYS ===")
    
    if args.dry_run:
        print("🧪 MODO SIMULACIÓN: Los emails se registrarán pero no se enviarán")
        logger.info("MODO DRY-RUN: No se enviarán emails reales")
    
    if args.force:
        print("⚡ MODO FORZADO: Ejecutando sin verificar horarios programados")
        logger.info("MODO FORZADO: Ejecutando independientemente del horario")
    
    try:
        print("📊 Conectando a las bases de datos...")
        # Crear instancia del gestor AGEDYS
        agedys_manager = AgedysManager()
        
        print("🔍 Iniciando análisis de facturas y DPDs pendientes...")
        # Ejecutar tarea con los argumentos especificados
        success = agedys_manager.execute_task(force=args.force, dry_run=args.dry_run)
        
        if success:
            print("✅ PROCESO COMPLETADO EXITOSAMENTE")
            print("📧 Todos los emails han sido procesados correctamente")
            logger.info("Todas las tareas AGEDYS completadas exitosamente")
            return 0
        else:
            print("❌ ERROR EN EL PROCESO")
            print("⚠️  Revise los logs para más detalles")
            logger.error("Error en la ejecución de las tareas AGEDYS")
            return 1
            
    except Exception as e:
        print(f"🔴 ERROR CRÍTICO: {e}")
        print("💡 Verifique la conectividad de las bases de datos")
        logger.error(f"Error crítico en AGEDYS: {e}")
        return 1
    
    finally:
        print("=" * 50)
        print("🏁 FINALIZANDO SISTEMA AGEDYS")
        logger.info("=== FINALIZANDO TAREAS AGEDYS ===")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)