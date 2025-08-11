from __future__ import annotations
"""Compatibilidad mínima para tests que aún importan report_registrar.

Toda la lógica real vive en no_conformidades_manager. Este archivo sólo
reexpone símbolos patchables y wrappers ligeros mientras existan tests
dependientes.
"""

from typing import Any

from common.reporting.html_report_generator import HTMLReportGenerator  # patch target
from .no_conformidades_manager import (
    enviar_notificacion_calidad,
    enviar_notificacion_tecnico_individual as _enviar_notificacion_tecnico_individual_real,
    _register_email_nc,
    _register_arapc_notification,
    _obtener_email_tecnico as _real_obtener_email_tecnico,
)

__all__ = [
    "enviar_notificacion_calidad",
    "enviar_notificacion_tecnico_individual",
    "_register_email_nc",
    "_register_arapc_notification",
    "_obtener_email_tecnico",
    "HTMLReportGenerator",
    "ReportRegistrar",
]

# Wrappers opcionales (por si algún test aún usa nombres distintos)

def enviar_notificacion_calidad_wrapper(datos_calidad: dict[str, Any]) -> bool:  # pragma: no cover
    return enviar_notificacion_calidad(datos_calidad)


def enviar_notificacion_tecnico_individual(tecnico: str, datos: dict[str, Any]) -> bool:  # pragma: no cover - wrapper acorde a expectativas tests
    # 1. Generar HTML primero
    cuerpo = HTMLReportGenerator.generar_reporte_tecnico_moderno(tecnico, datos)  # type: ignore
    if not cuerpo or not cuerpo.strip():  # sin contenido -> True y no se busca email
        return True
    # 2. Obtener email técnico (función parcheable)
    correo = _obtener_email_tecnico(tecnico)
    if not correo:
        return False
    # 3. Registrar correo y avisos
    id_correo = _register_email_nc(
        application="NoConformidades",
        subject=f"ARs Pendientes Técnico {tecnico}",
        body_html=cuerpo,
        recipients=correo,
        admin_emails="",
    )
    _register_arapc_notification(
        id_correo,
        [a["IDAccionRealizada"] for a in datos.get("ars_15_dias", [])],
        [a["IDAccionRealizada"] for a in datos.get("ars_7_dias", [])],
        [a["IDAccionRealizada"] for a in datos.get("ars_vencidas", [])],
    )
    return True


class ReportRegistrar:  # pragma: no cover - stub para tests legacy
    def get_admin_emails(self) -> list[str]:
        return []
    def get_quality_emails(self) -> list[str]:
        return []

# Reexponer wrapper _obtener_email_tecnico si los tests lo parchean
def _obtener_email_tecnico(tecnico: str):  # pragma: no cover
    # Delegar a implementación real para no romper llamadas si no está parcheado
    try:
        from .no_conformidades_manager import _obtener_email_tecnico as real
        return real(tecnico)
    except Exception:
        return None
