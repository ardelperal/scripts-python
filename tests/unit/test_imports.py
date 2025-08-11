import pytest


def test_import_main_modules():
    """Asegura que módulos raíz se importan sin errores (detección temprana de dependencias rotas)."""
    modules = [
        "src.common",
        "src.email_services",
        "src.brass",  # shim + paquete
        "src.no_conformidades",  # paquete consolidado
    ]
    for mod in modules:
        try:
            __import__(mod)
        except ImportError as e:  # pragma: no cover - específico de fallo
            pytest.fail(f"Fallo al importar {mod}: {e}")
