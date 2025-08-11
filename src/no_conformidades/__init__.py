"""
Archivo __init__.py para el módulo de No Conformidades
"""

# Importar solo las clases principales para evitar problemas de dependencias circulares
try:
    from no_conformidades.no_conformidades_manager import NoConformidadesManager
    from no_conformidades.no_conformidades_task import NoConformidadesTask

    __all__ = ["NoConformidadesManager", "NoConformidadesTask"]
except ImportError:
    # Si hay problemas con las dependencias, al menos permitir que el módulo se importe
    __all__ = []
