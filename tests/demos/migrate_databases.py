#!/usr/bin/env python3
"""
Script para migrar bases de datos Access a SQLite
Usado durante el build de Docker para crear versiones compatibles
"""
import logging
import sys
from pathlib import Path

# Añadir el directorio src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.common.access_migrator import migrate_all_access_databases


def setup_logging():
    """Configura logging para la migración"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('migration.log', encoding='utf-8')
        ]
    )


def main():
    """Función principal de migración"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🔄 Iniciando migración de bases de datos Access a SQLite...")
    
    # Directorios
    source_dir = Path("dbs-locales")
    target_dir = Path("dbs-sqlite")
    
    if not source_dir.exists():
        logger.error(f"Directorio fuente no encontrado: {source_dir}")
        sys.exit(1)
    
    # Realizar migración
    results = migrate_all_access_databases(source_dir, target_dir)
    
    # Mostrar resultados
    print("\n📊 Resultados de migración:")
    total_files = len(results)
    successful = sum(1 for success in results.values() if success)
    failed = total_files - successful
    
    for file, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {file}")
    
    print(f"\n📈 Resumen:")
    print(f"  Total: {total_files} archivos")
    print(f"  Exitosos: {successful}")
    print(f"  Fallidos: {failed}")
    
    if failed > 0:
        print(f"\n⚠️  Algunas migraciones fallaron. Revisar migration.log")
        sys.exit(1)
    else:
        print(f"\n🎉 Todas las migraciones completadas exitosamente!")
        
        # Mostrar estructura resultante
        print(f"\n📁 Estructura generada:")
        for sqlite_file in sorted(target_dir.glob("*.sqlite")):
            size_mb = sqlite_file.stat().st_size / (1024 * 1024)
            print(f"  📄 {sqlite_file.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
