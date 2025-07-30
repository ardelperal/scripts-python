"""
Configuración específica para tests de integración de AGEDYS
"""
import pytest
from agedys.agedys_manager import AgedysManager


@pytest.fixture
def real_agedys_manager():
    """
    Fixture que proporciona una instancia real de AgedysManager
    para tests de integración con bases de datos reales.
    """
    return AgedysManager()