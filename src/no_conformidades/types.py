"""Typed definitions for No Conformidades domain objects.

TypedDict structures for records returned from database queries. Using
TypedDict keeps interoperability with existing dict-based code while
enabling static analysis.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TypedDict


class ARTecnicaRecord(TypedDict, total=False):
    CodigoNoConformidad: str
    IDAccionRealizada: int
    AccionCorrectiva: str | None
    AccionRealizada: str | None
    FechaInicio: date | datetime | None
    FechaFinPrevista: date | datetime | None
    Nombre: str | None
    DiasParaCaducar: int | None
    CorreoCalidad: str | None
    Nemotecnico: str | None


class ARCalidadProximaRecord(TypedDict, total=False):
    DiasParaCierre: int | None
    CodigoNoConformidad: str
    Nemotecnico: str | None
    DESCRIPCION: str | None
    RESPONSABLECALIDAD: str | None
    FECHAAPERTURA: date | datetime | None
    FPREVCIERRE: date | datetime | None
