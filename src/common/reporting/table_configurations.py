"""Centralized HTML table configurations for reports.

Provides:
- TABLE_CONFIGURATIONS: Riesgos module table metadata.
- AGEDYS_TABLE_CONFIGURATIONS: Agedys module table metadata.

Each entry maps an internal table key to a dict with:
  title: str
  columns: list of {header, field, optional format}

This avoids duplication across managers and enables future generic renderers.
"""
from __future__ import annotations

# Riesgos table configurations (moved from riesgos_manager.py)
TABLE_CONFIGURATIONS = {
    "accepted_risks_unmotivated": {
        "title": "Riesgos Aceptados sin Motivación",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha Aceptación", "field": "FechaAceptacion", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "accepted_risks_rejected": {
        "title": "Riesgos Aceptados Rechazados",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha Aceptación", "field": "FechaAceptacion", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "retired_risks_unmotivated": {
        "title": "Riesgos Retirados sin Motivación",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha Retirada", "field": "FechaRetirada", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "retired_risks_rejected": {
        "title": "Riesgos Retirados Rechazados",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha Retirada", "field": "FechaRetirada", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "editions_ready_for_publication": {
        "title": "Ediciones Listas para Publicación",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Últ Ed", "field": "UltimaEdicion"},
            {"header": "Fecha Edición", "field": "FechaEdicion", "format": "date"},
            {"header": "Fecha Publicación", "field": "FechaPublicacion", "format": "date"},
            {"header": "Responsable Técnico", "field": "ResponsableTecnico"},
            {"header": "Resp. Calidad", "field": "ResponsableCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "accepted_risks_pending_approval": {
        "title": "Riesgos Aceptados Pendientes de Aprobación",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha Aceptación", "field": "FechaAceptacion", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "retired_risks_pending_approval": {
        "title": "Riesgos Retirados Pendientes de Aprobación",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha Retirada", "field": "FechaRetirada", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "materialized_risks_pending_decision": {
        "title": "Riesgos Materializados Pendientes de Decisión",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha Materialización", "field": "FechaMaterializacion", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "editions_with_expired_dates": {
        "title": "Ediciones con Fechas Caducadas",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Últ Ed", "field": "UltimaEdicion"},
            {"header": "Fecha Máx.Próx Ed.", "field": "FechaMaximaProximaEdicion", "format": "date"},
            {"header": "Resp. Calidad", "field": "ResponsableCalidad"},
            {"header": "Días", "field": "Dias", "format": "days"},
        ],
    },
    "active_editions": {
        "title": "Ediciones Activas",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Últ Ed", "field": "Edicion"},
            {"header": "Fecha Edición", "field": "FechaEdicion", "format": "date"},
            {"header": "Fecha Publicación", "field": "FechaPublicacion", "format": "date"},
            {"header": "Responsable Técnico", "field": "ResponsableTecnico"},
            {"header": "Estado", "field": "Estado"},
        ],
    },
    "closed_editions_last_month": {
        "title": "Ediciones Cerradas en los Últimos 30 Días",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Últ Ed", "field": "Edicion"},
            {"header": "Fecha Edición", "field": "FechaEdicion", "format": "date"},
            {"header": "Fecha Publicación", "field": "FechaPublicacion", "format": "date"},
            {"header": "Fecha Cierre", "field": "FechaCierre", "format": "date"},
            {"header": "Responsable Técnico", "field": "ResponsableTecnico"},
            {"header": "Días desde Cierre", "field": "DiasDesdeCierre"},
        ],
    },
    "risks_to_reclassify": {
        "title": "Riesgos que hay que Asignar un Código de Biblioteca",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa raíz", "field": "CausaRaiz"},
            {"header": "Fecha para retific.", "field": "FechaRiesgoParaRetipificar", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
        ],
    },
    "mitigation_actions_reschedule": {
        "title": "Riesgos con Acciones de Mitigación para Replanificar",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código Riesgo", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa Raíz", "field": "CausaRaiz"},
            {"header": "Disparador", "field": "DisparadorDelPlan"},
            {"header": "Acción", "field": "Accion"},
            {"header": "Fecha Inicio", "field": "FechaInicio", "format": "date"},
            {"header": "Fecha Fin Prevista", "field": "FechaFinPrevista", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
        ],
    },
    "contingency_actions_reschedule": {
        "title": "Riesgos con Acciones de Contingencia para Replanificar",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Código Riesgo", "field": "CodigoRiesgo"},
            {"header": "Descripción", "field": "Descripcion"},
            {"header": "Causa Raíz", "field": "CausaRaiz"},
            {"header": "Disparador", "field": "DisparadorDelPlan"},
            {"header": "Acción", "field": "Accion"},
            {"header": "Fecha Inicio", "field": "FechaInicio", "format": "date"},
            {"header": "Fecha Fin Prevista", "field": "FechaFinPrevista", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
        ],
    },
    "editions_need_publication": {
        "title": "Ediciones que necesitan propuesta de publicación",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Últ Ed", "field": "Edicion"},
            {"header": "Fecha Máx.Próx Ed.", "field": "FechaMaxProximaPublicacion", "format": "date"},
            {"header": "Propuesta para Publicación", "field": "FechaPreparadaParaPublicar", "format": "date"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
            {"header": "Faltan (días)", "field": "Dias", "format": "css_days"},
        ],
    },
    "editions_with_rejected_proposals": {
        "title": "Ediciones con propuestas de publicación rechazadas",
        "columns": [
            {"header": "Proyecto", "field": "Nemotecnico"},
            {"header": "Últ Ed", "field": "Edicion"},
            {"header": "Fecha Máx.Próx Ed.", "field": "FechaMaxProximaPublicacion", "format": "date"},
            {"header": "Propuesta para Publicación", "field": "FechaPreparadaParaPublicar", "format": "date"},
            {"header": "Fecha Rechazo", "field": "PropuestaRechazadaPorCalidadFecha", "format": "date"},
            {"header": "Motivo Rechazo", "field": "PropuestaRechazadaPorCalidadMotivo"},
            {"header": "Resp. Calidad", "field": "UsuarioCalidad"},
        ],
    },
}

# Agedys table configurations (new)
AGEDYS_TABLE_CONFIGURATIONS = {
    # Placeholder structure: populate with real Agedys table configs if standardized
    # Example:
    # "dpds_sin_visado_calidad": {
    #     "title": "DPDs sin visado calidad",
    #     "columns": [
    #         {"header": "Proyecto", "field": "CODPROYECTOS"},
    #         {"header": "Código", "field": "CODIGO"},
    #         {"header": "Descripción", "field": "Descripcion"},
    #     ],
    # },
}

__all__ = ["TABLE_CONFIGURATIONS", "AGEDYS_TABLE_CONFIGURATIONS"]
