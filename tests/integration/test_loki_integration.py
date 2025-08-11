"""Tests de integración básicos para setup_logging (archivo + opcional Loki).

Adaptado al signature actual: setup_logging(log_file: Path, level=...).
"""
import logging
from pathlib import Path

from common.utils import setup_logging


def _leer_contenido(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def test_setup_logging_basico_sin_env(tmp_path, monkeypatch):
    monkeypatch.delenv("LOKI_URL", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    log_file = tmp_path / "basic.log"
    setup_logging(log_file=log_file, level=logging.INFO)
    logging.getLogger().info("Linea basica")
    assert log_file.exists()
    assert "Linea basica" in _leer_contenido(log_file)


def test_setup_logging_con_env_sin_loki_module(tmp_path, monkeypatch):
    # LokiQueueHandler podría no estar instalado; sólo validamos que no rompe
    monkeypatch.setenv("LOKI_URL", "http://localhost:3100")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    log_file = tmp_path / "env.log"
    setup_logging(log_file=log_file, level=logging.DEBUG)
    logging.getLogger().debug("Linea debug env")
    assert log_file.exists()
    assert "Linea debug env" in _leer_contenido(log_file)


def test_setup_logging_con_archivo(tmp_path, monkeypatch):
    monkeypatch.delenv("LOKI_URL", raising=False)
    log_file = tmp_path / "archivo.log"
    setup_logging(log_file=log_file, level=logging.WARNING)
    logging.getLogger().warning("Linea warning archivo")
    logging.getLogger().error("Linea error archivo")
    content = _leer_contenido(log_file)
    assert "Linea warning archivo" in content
    assert "Linea error archivo" in content
