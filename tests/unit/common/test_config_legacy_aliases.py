import pytest

from common.config import Config, config as global_config


@pytest.mark.parametrize(
    "db_type,alias_method,kwargs",
    [
        ("agedys", "get_db_agedys_connection_string", {}),
        ("brass", "get_db_brass_connection_string", {}),
        ("tareas", "get_db_tareas_connection_string", {}),
        ("correos", "get_db_correos_connection_string", {"with_password": True}),
        ("correos", "get_db_correos_connection_string", {"with_password": False}),
        ("riesgos", "get_db_riesgos_connection_string", {}),
        ("expedientes", "get_db_expedientes_connection_string", {}),
        ("no_conformidades", "get_db_no_conformidades_connection_string", {}),
    ],
)
def test_legacy_alias_methods_match_generic(db_type, alias_method, kwargs):
    """Cada método legacy debe producir exactamente la misma cadena que el método genérico."""
    # Usar una nueva instancia para evitar que otros tests hayan mutado rutas
    cfg = Config()

    # Resultado alias
    alias_func = getattr(cfg, alias_method)
    alias_value = alias_func(**kwargs) if kwargs else alias_func()

    # Resultado genérico (con posible control de password)
    with_password = kwargs.get("with_password", True)
    generic_value = cfg.get_db_connection_string(db_type, with_password=with_password)

    assert alias_value == generic_value, (
        f"Alias {alias_method} difiere del genérico para {db_type}.\n"
        f"Alias:   {alias_value}\nGenérico: {generic_value}"
    )


def test_global_config_instance_alias_equivalence():
    """Verifica también contra la instancia global por si se usa en producción directamente."""
    # Asegurar que la instancia global se comporta igual al crear otra nueva
    fresh = Config()
    assert global_config.get_db_brass_connection_string() == fresh.get_db_brass_connection_string()
    assert global_config.get_db_connection_string('brass') == fresh.get_db_connection_string('brass')
    # Consistencia cruzada alias vs genérico en la instancia global
    assert global_config.get_db_brass_connection_string() == global_config.get_db_connection_string('brass')
