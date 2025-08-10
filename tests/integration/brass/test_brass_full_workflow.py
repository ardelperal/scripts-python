"""Tests de integración consolidados para BrassTask.

Objetivo: reemplazar antiguos tests funcionales de BRASS con una verificación
focalizada del flujo principal (happy path) y el caso sin datos.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Bootstrap robusto: subir hasta encontrar carpeta que contenga 'src'
_THIS = Path(__file__).resolve()
for parent in [_THIS.parent, *_THIS.parents]:
    src_dir = parent / 'src'
    if src_dir.is_dir():
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        break

from brass.brass_task import BrassTask


@pytest.fixture
def task_instance():
    # Instanciamos la tarea; la conexión real se mockeará antes de ejecutar la lógica
    return BrassTask()


def _patch_db_and_manager(mock_generate_return):
    """Helper para parchear AccessDatabase/BrassManager y devolver html controlado."""
    patcher_manager = patch('brass.brass_task.BrassManager')
    mock_manager_cls = patcher_manager.start()
    mock_manager = MagicMock()
    mock_manager.generate_brass_report_html.return_value = mock_generate_return
    mock_manager_cls.return_value = mock_manager

    # Parchear pool y AccessDatabase para que no intenten conexiones reales
    patcher_pool = patch('brass.brass_task.get_brass_connection_pool', return_value=None)
    patcher_access = patch('brass.brass_task.AccessDatabase')

    p_pool = patcher_pool.start()
    p_access = patcher_access.start()

    return [patcher_manager, patcher_pool, patcher_access], mock_manager


def test_brass_happy_path(task_instance, monkeypatch):
    """Happy path: debe_ejecutarse True, informe con contenido -> registra correo y marca completada."""
    # Forzar que la tarea debe ejecutarse
    monkeypatch.setattr(task_instance, 'debe_ejecutarse', lambda : True)

    # Parchear manager e informe no vacío
    patchers, mock_manager = _patch_db_and_manager('<html>algo</html>')

    # Parchear register_standard_report para verificar llamada
    with patch('brass.brass_task.register_standard_report', return_value=True) as mock_register:
        # Simular base tareas y brass para que pasen verificaciones internas
        task_instance.db_tareas = MagicMock()
        task_instance.db_brass = MagicMock()

        # Ejecutar lógica específica directamente
        ok = task_instance.execute_specific_logic()

        assert ok is True, 'La ejecución debería ser exitosa'
        mock_manager.generate_brass_report_html.assert_called_once()
        mock_register.assert_called_once()

    # Limpiar patchers
    for p in patchers:
        p.stop()


def test_brass_no_data(task_instance, monkeypatch):
    """Caso sin datos: informe vacío => no se registra correo."""
    monkeypatch.setattr(task_instance, 'debe_ejecutarse', lambda : True)

    patchers, mock_manager = _patch_db_and_manager('')  # Informe vacío

    with patch('brass.brass_task.register_standard_report', return_value=True) as mock_register:
        task_instance.db_tareas = MagicMock()
        task_instance.db_brass = MagicMock()
        ok = task_instance.execute_specific_logic()
        assert ok is True, 'Debe devolver True aunque no registre correo (flujo controlado)'
        mock_manager.generate_brass_report_html.assert_called_once()
        mock_register.assert_not_called()

    for p in patchers:
        p.stop()
