"""Tests centrados en consultas y caché de RiesgosManager."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.riesgos.riesgos_manager import RiesgosManager


@pytest.fixture
def manager():
    cfg = MagicMock()
    logger = MagicMock()
    m = RiesgosManager(cfg, logger)
    m.db = MagicMock()
    m.db_tareas = MagicMock()
    return m


def test_build_technical_users_query_variants(manager):
    types = [
        "EDICIONESNECESITANPROPUESTAPUBLICACION",
        "EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS",
        "RIESGOSACEPTADOSNOMOTIVADOS",
        "RIESGOSACEPTADOSRECHAZADOS",
        "RIESGOSRETIRADOSNOMOTIVADOS",
        "RIESGOSRETIRADOSRECHAZADOS",
        "RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR",
        "RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR",
    ]
    for t in types:
        q = manager._build_technical_users_query(t)
        assert 'SELECT' in q and 'FROM' in q and 'WHERE' in q


def test_get_distinct_technical_users_fallback(manager, monkeypatch):
    # Forzar fallo de consulta optimizada para usar fallback
    manager._build_optimized_technical_users_query = lambda: "SELECT 1"
    # Simular _execute_query_with_error_logging que lanza para forzar fallback
    def side_effect(*a, **k):
        raise Exception("fail")
    manager._execute_query_with_error_logging = MagicMock(side_effect=side_effect)
    # Ahora parchear fallback internamente con un execute query que devuelva usuarios
    def fallback_exec(query, params=None, context=""):
        return [{'UsuarioRed': context[-1] if context else 'u', 'Nombre': 'Nombre', 'CorreoUsuario': 'n@test.com'}]
    # Empaquetar _execute_query_with_error_logging dentro del fallback método
    # En fallback se vuelve a llamar a _execute_query_with_error_logging, sustituimos temporalmente
    manager._execute_query_with_error_logging = MagicMock(return_value=[{'UsuarioRed':'u1','Nombre':'N1','CorreoUsuario':'u1@test.com'}])
    users = manager._get_distinct_technical_users_fallback()
    assert isinstance(users, list)


def test_get_distinct_technical_users_cache(manager, monkeypatch):
    # Simular consulta optimizada con duplicados
    manager._build_optimized_technical_users_query = lambda: "SELECT X"
    sample_rows = [
        {'UsuarioRed':'u1','Nombre':'N1','CorreoUsuario':'u1@test.com'},
        {'UsuarioRed':'u1','Nombre':'N1','CorreoUsuario':'u1@test.com'},
        {'UsuarioRed':'u2','Nombre':'N2','CorreoUsuario':'u2@test.com'},
    ]
    manager._execute_query_with_error_logging = MagicMock(return_value=sample_rows)
    first = manager.get_distinct_technical_users()
    second = manager.get_distinct_technical_users()  # caché
    assert len(first) == 2 and second == first
    manager._execute_query_with_error_logging.assert_called_once()
