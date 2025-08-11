"""Configuración centralizada de logging.

Proporciona una función única ``setup_global_logging`` reutilizada por todos
los runners para garantizar formato y destinos consistentes.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_global_logging(log_level_str: str = "INFO") -> None:
    """Configura logging global (consola + archivo logs/app.log).

    Idempotente: si root ya tiene handlers se asume configurado.
    """
    root = logging.getLogger()
    if root.handlers:  # Ya configurado
        return
    log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"
    level = getattr(logging, log_level_str.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_h = logging.FileHandler(log_file, encoding="utf-8")
    file_h.setFormatter(formatter)
    stream_h = logging.StreamHandler(sys.stdout)
    stream_h.setFormatter(formatter)
    root.setLevel(level)
    root.addHandler(file_h)
    root.addHandler(stream_h)


__all__ = ["setup_global_logging"]
