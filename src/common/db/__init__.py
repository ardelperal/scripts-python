"""Subpaquete de base de datos para common.

Expone AccessDatabase y helpers de pool. Mantiene compatibilidad retro para
imports antiguos `common.database` mediante una inserción ligera en sys.modules
si aún existe código que lo requiera durante la transición.
"""

from .database import AccessDatabase  # noqa: F401
from .access_connection_pool import (  # noqa: F401
	AccessConnectionPool,
	get_tareas_connection_pool,
	get_correos_connection_pool,
	get_agedys_connection_pool,
	get_expedientes_connection_pool,
	get_nc_connection_pool,
	get_brass_connection_pool,
)

# Backward compatibility: permitir `import common.database`.
import types as _types
import sys as _sys

if "common.database" not in _sys.modules:  # pragma: no cover - sólo ruta legacy
	legacy_mod = _types.ModuleType("common.database")
	legacy_mod.AccessDatabase = AccessDatabase
	# Exponer también pyodbc si el módulo real lo define internamente
	try:  # puede fallar si pyodbc no está instalado en entorno de tests aislados
		import pyodbc as _pyodbc  # type: ignore

		legacy_mod.pyodbc = _pyodbc  # type: ignore
	except Exception:  # pragma: no cover
		pass
	_sys.modules["common.database"] = legacy_mod
