"""Utilidades comunes para construir tablas HTML simples reutilizables.

Responsabilidad: dado un título y una lista de diccionarios homogéneos, producir
un fragmento HTML consistente (div.section > h2 + table.data-table) usando el
estilo global.
"""
from __future__ import annotations
from datetime import datetime, date
from pathlib import Path
from typing import Iterable, Mapping, Sequence, Any, List

from src.common.utils import safe_str

# Política de orden de columnas: preservamos el orden de la primera fila si es Mapping
# (Python 3.7+ preserva el orden de inserción). Si se desea orden alfabético, se puede
# pasar sort_headers=True.

def build_table_html(title: str, rows: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]], *,
                     sort_headers: bool = False,
                     date_format: str = '%d/%m/%Y') -> str:
    """Construye tabla HTML estándar.

    Args:
        title: Título de la sección
        rows: Secuencia (o iterable) de dict-like con mismas claves
        sort_headers: Si True ordena alfabéticamente las columnas
        date_format: Formato de fechas datetime/date
    Returns:
        Fragmento HTML (string) o cadena vacía si no hay filas
    """
    rows_list: List[Mapping[str, Any]] = list(rows)
    if not rows_list:
        return ''

    first = rows_list[0]
    headers = list(first.keys())
    if sort_headers:
        headers = sorted(headers)

    parts: List[str] = [f"<div class='section'><h2>{title}</h2><table class='data-table'>"]
    parts.append('<thead><tr>')
    for h in headers:
        parts.append(f"<th>{h}</th>")
    parts.append('</tr></thead><tbody>')

    for row in rows_list:
        parts.append('<tr>')
        for h in headers:
            val = row.get(h, '')
            if isinstance(val, (datetime, date)):
                val = val.strftime(date_format)
            parts.append(f"<td>{safe_str(val)}</td>")
        parts.append('</tr>')

    parts.append('</tbody></table></div>')
    return ''.join(parts)
