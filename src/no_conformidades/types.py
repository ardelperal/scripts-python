"""Typed definitions for No Conformidades domain objects.

TypedDict structures for records returned from database queries. Using
TypedDict keeps interoperability with existing dict-based code while
enabling static analysis.
"""
from __future__ import annotations

from typing import TypedDict, Optional
from datetime import date, datetime


class ARTecnicaRecord(TypedDict, total=False):
    CodigoNoConformidad: str
    IDAccionRealizada: int
    AccionCorrectiva: Optional[str]
    AccionRealizada: Optional[str]
    FechaInicio: Optional[date | datetime]
    FechaFinPrevista: Optional[date | datetime]
    Nombre: Optional[str]
    DiasParaCaducar: Optional[int]
    CorreoCalidad: Optional[str]
    Nemotecnico: Optional[str]


class ARCalidadProximaRecord(TypedDict, total=False):
    DiasParaCierre: Optional[int]
    CodigoNoConformidad: str
    Nemotecnico: Optional[str]
    DESCRIPCION: Optional[str]
    RESPONSABLECALIDAD: Optional[str]
    FECHAAPERTURA: Optional[date | datetime]
    FPREVCIERRE: Optional[date | datetime]
