"""Tests para TaskRegistry"""
import os
import pytest

from common.task_registry import TaskRegistry


def test_registry_default_counts():
    registry = TaskRegistry()
    daily = registry.get_daily_tasks()
    continuous = registry.get_continuous_tasks()
    assert len(daily) >= 5  # Riesgos, BRASS, Expedientes, NoConformidades, Agedys
    # Ahora solo una tarea continua unificada (EmailServices)
    assert len(continuous) == 1  # EmailServices


def test_registry_summary_names():
    registry = TaskRegistry()
    summary = registry.summary()
    assert 'daily_count' in summary and summary['daily_count'] == len(summary['daily_names'])
    assert 'continuous_count' in summary and summary['continuous_count'] == len(summary['continuous_names'])
    assert 'Riesgos' in summary['daily_names']
    assert 'EmailServices' in summary['continuous_names']


def test_registry_filters():
    registry = TaskRegistry()
    only_riesgos = registry.filter_daily(lambda t: t.name == 'Riesgos')
    assert len(only_riesgos) == 1
    assert only_riesgos[0].name == 'Riesgos'


def test_registry_with_extras():
    class DummyDaily(type(next(iter(TaskRegistry().get_daily_tasks())).__class__)):
        pass

    # Crear dummy heredando de la primera clase concreta diaria
    base_daily_cls = TaskRegistry().get_daily_tasks()[0].__class__
    class ExtraDaily(base_daily_cls):
        def __init__(self):
            super().__init__()
            self.name = 'ExtraDaily'
            self.script_filename = 'run_extra.py'
            self.task_names = ['ExtraDailyTask']

    registry = TaskRegistry(extra_daily=[ExtraDaily()])
    names = [t.name for t in registry.get_daily_tasks()]
    assert 'ExtraDaily' in names
