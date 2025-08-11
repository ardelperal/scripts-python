import pytest

def test_import_main_modules():
    """
    Verifica que los módulos principales se pueden importar sin errores.
    Esto ayuda a detectar problemas de dependencias circulares o importaciones rotas.
    """
    try:
        import src.common
        import src.email_services
        # Añade aquí otros módulos principales de tu aplicación
        # Ejemplo: import src.brass
    except ImportError as e:
        pytest.fail(f"Fallo al importar un módulo principal: {e}")
