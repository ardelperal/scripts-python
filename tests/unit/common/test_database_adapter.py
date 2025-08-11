"""Prueba de compatibilidad tras eliminar AccessAdapter.

Garantiza que el módulo actual de base de datos expone AccessDatabase y que
no existe ya una clase AccessAdapter (eliminación definitiva del legado).
"""

from common.db.database import AccessDatabase


def test_access_adapter_removed_and_access_database_present():
    # La clase principal debe existir
    assert AccessDatabase is not None
    # Y AccessAdapter ya no debe estar disponible en el paquete
    import common.db.database as db_mod

    assert not hasattr(db_mod, "AccessAdapter")
