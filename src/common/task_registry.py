"""
Registro de todas las tareas del sistema
Define las tareas específicas que heredan de las clases base
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Iterable, Dict, Any

from .base_task import TareaDiaria, TareaContinua
# Asegurar que raíz del proyecto y 'src' están en sys.path para ejecuciones de test
_here = Path(__file__).resolve()
_project_root = _here.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
_src_path = _project_root / 'src'
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

try:
    from src.brass.brass_task import BrassTask  # type: ignore
    from src.expedientes.expedientes_task import ExpedientesTask  # type: ignore
    from src.no_conformidades.no_conformidades_task import NoConformidadesTask  # type: ignore
    from src.agedys.agedys_task import AgedysTask  # type: ignore
    from src.correos.correos_task import CorreosTask  # type: ignore
    from src.correo_tareas.correo_tareas_task import CorreoTareasTask  # type: ignore
except ModuleNotFoundError:
    from brass.brass_task import BrassTask  # type: ignore
    from expedientes.expedientes_task import ExpedientesTask  # type: ignore
    from no_conformidades.no_conformidades_task import NoConformidadesTask  # type: ignore
    from agedys.agedys_task import AgedysTask  # type: ignore
    from correos.correos_task import CorreosTask  # type: ignore
    from correo_tareas.correo_tareas_task import CorreoTareasTask  # type: ignore

# Intento de importación ligera de RiesgosTask; si falla, se crea stub para tests unitarios
try:
    from src.riesgos.riesgos_task import RiesgosTask  # type: ignore
except Exception:  # pragma: no cover - fallback
    class RiesgosTask(TareaDiaria):  # type: ignore
        def __init__(self):
            super().__init__(
                name="Riesgos",
                script_filename="run_riesgos.py",
                task_names=["RiesgosDiariosTecnicos"],
                frequency_days=1
            )
        def debe_ejecutarse(self) -> bool:
            return False
        def marcar_como_completada(self):
            pass


class RiesgosTask(TareaDiaria):
    """Tarea para procesamiento de riesgos (técnicos, semanales y mensuales)"""
    
    def __init__(self):
        # Obtener frecuencias desde variables de entorno
        freq_tecnicos = int(os.getenv('RIESGOS_TECNICOS_FRECUENCIA_DIAS', '1'))
        freq_semanales = int(os.getenv('RIESGOS_CALIDAD_SEMANAL_FRECUENCIA_DIAS', '7'))
        freq_mensuales = int(os.getenv('RIESGOS_CALIDAD_MENSUAL_FRECUENCIA_DIAS', '30'))
        
        super().__init__(
            name="Riesgos",
            script_filename="run_riesgos.py",
            task_names=[
                "RiesgosDiariosTecnicos",
                "RiesgosSemanalesCalidad", 
                "RiesgosMensualesCalidad"
            ],
            frequency_days=1  # Se verifica individualmente cada subtarea
        )
        
        # Frecuencias específicas por subtarea
        self.task_frequencies = {
            "RiesgosDiariosTecnicos": freq_tecnicos,
            "RiesgosSemanalesCalidad": freq_semanales,
            "RiesgosMensualesCalidad": freq_mensuales
        }
    
    def debe_ejecutarse(self) -> bool:
        """Verifica si alguna de las subtareas de riesgos debe ejecutarse"""
        if not self.db_tareas:
            self.logger.warning(f"⚠️  No hay conexión a BD, no se puede verificar {self.name}")
            return False
        
        try:
            from .utils import should_execute_task
            
            # Verificar cada subtarea con su frecuencia específica
            for task_name in self.task_names:
                frequency = self.task_frequencies.get(task_name, 1)
                if should_execute_task(self.db_tareas, task_name, frequency, self.logger):
                    self.logger.info(f"📅 {task_name} debe ejecutarse (frecuencia: {frequency} días)")
                    return True
            
            self.logger.info(f"✅ {self.name} no necesita ejecutarse aún")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando {self.name}: {e}")
            return False


class BrassTask(TareaDiaria):
    """Tarea para procesamiento de datos BRASS"""
    
    def __init__(self):
        frequency = int(os.getenv('BRASS_FRECUENCIA_DIAS', '1'))
        super().__init__(
            name="BRASS",
            script_filename="run_brass.py",
            task_names=["BRASSDiario"],
            frequency_days=frequency
        )


class ExpedientesTask(TareaDiaria):
    """Tarea para procesamiento de expedientes"""
    
    def __init__(self):
        frequency = int(os.getenv('EXPEDIENTES_FRECUENCIA_DIAS', '1'))
        super().__init__(
            name="Expedientes",
            script_filename="run_expedientes.py",
            task_names=["ExpedientesDiario"],
            frequency_days=frequency
        )


class NoConformidadesTask(TareaDiaria):
    """Tarea para procesamiento de no conformidades (calidad y técnica)"""
    
    def __init__(self):
        freq_calidad = int(os.getenv('NO_CONFORMIDADES_DIAS_TAREA_CALIDAD', '1'))
        freq_tecnica = int(os.getenv('NO_CONFORMIDADES_DIAS_TAREA_TECNICA', '7'))
        
        super().__init__(
            name="NoConformidades",
            script_filename="run_no_conformidades.py",
            task_names=[
                "NoConformidadesCalidad",
                "NoConformidadesTecnica"
            ],
            frequency_days=1  # Se verifica individualmente cada subtarea
        )
        
        # Frecuencias específicas por subtarea
        self.task_frequencies = {
            "NoConformidadesCalidad": freq_calidad,
            "NoConformidadesTecnica": freq_tecnica
        }
    
    def debe_ejecutarse(self) -> bool:
        """Verifica si alguna de las subtareas de no conformidades debe ejecutarse"""
        if not self.db_tareas:
            self.logger.warning(f"⚠️  No hay conexión a BD, no se puede verificar {self.name}")
            return False
        
        try:
            from .utils import should_execute_task
            
            # Verificar cada subtarea con su frecuencia específica
            for task_name in self.task_names:
                frequency = self.task_frequencies.get(task_name, 1)
                if should_execute_task(self.db_tareas, task_name, frequency, self.logger):
                    self.logger.info(f"📅 {task_name} debe ejecutarse (frecuencia: {frequency} días)")
                    return True
            
            self.logger.info(f"✅ {self.name} no necesita ejecutarse aún")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando {self.name}: {e}")
            return False


class AgedysTask(TareaDiaria):
    """Tarea para sincronización con AGEDYS"""
    
    def __init__(self):
        frequency = int(os.getenv('AGEDYS_FRECUENCIA_DIAS', '1'))
        super().__init__(
            name="AGEDYS",
            script_filename="run_agedys.py",
            task_names=["AGEDYSDiario"],
            frequency_days=frequency
        )


class CorreosTask(TareaContinua):
    """Tarea continua para envío de correos pendientes"""
    
    def __init__(self):
        super().__init__(
            name="Correos",
            script_filename="run_correos.py"
        )


class CorreoTareasTask(TareaContinua):
    """Tarea continua para notificaciones de tareas"""
    
    def __init__(self):
        super().__init__(
            name="CorreoTareas",
            script_filename="run_correo_tareas.py"
        )


class TaskRegistry:
    """Registro encapsulado de tareas.

    Reemplaza las funciones globales para facilitar:
      - Inyección de dependencias futuras (p.ej. pools, config) al construir tareas
      - Tests: se puede instanciar un registro reducido / falso
      - Extensibilidad: permitir filtrado dinámico, plugins, etc.
    """

    def __init__(self,
                 include_daily: bool = True,
                 include_continuous: bool = True,
                 extra_daily: Optional[Sequence[TareaDiaria]] = None,
                 extra_continuous: Optional[Sequence[TareaContinua]] = None):
        self._daily_tasks: List[TareaDiaria] = []
        self._continuous_tasks: List[TareaContinua] = []

        if include_daily:
            self._daily_tasks.extend([
                RiesgosTask(),
                BrassTask(),
                ExpedientesTask(),
                NoConformidadesTask(),
                AgedysTask()
            ])
        if include_continuous:
            self._continuous_tasks.extend([
                CorreosTask(),
                CorreoTareasTask()
            ])
        if extra_daily:
            self._daily_tasks.extend(extra_daily)
        if extra_continuous:
            self._continuous_tasks.extend(extra_continuous)

    # API pública
    def get_daily_tasks(self) -> List[TareaDiaria]:
        return list(self._daily_tasks)

    def get_continuous_tasks(self) -> List[TareaContinua]:
        return list(self._continuous_tasks)

    def get_all_tasks(self) -> List:
        return self.get_daily_tasks() + self.get_continuous_tasks()

    # Métodos auxiliares potenciales (extensión futura)
    def filter_daily(self, predicate) -> List[TareaDiaria]:
        return [t for t in self._daily_tasks if predicate(t)]

    def filter_continuous(self, predicate) -> List[TareaContinua]:
        return [t for t in self._continuous_tasks if predicate(t)]

    def summary(self) -> Dict[str, Any]:
        return {
            'daily_count': len(self._daily_tasks),
            'continuous_count': len(self._continuous_tasks),
            'daily_names': [t.name for t in self._daily_tasks],
            'continuous_names': [t.name for t in self._continuous_tasks]
        }


# Backwards compatibility exports (para código legado que aún importe las funciones)
def get_all_daily_tasks() -> List[TareaDiaria]:  # pragma: no cover - compat
    return TaskRegistry().get_daily_tasks()


def get_all_continuous_tasks() -> List[TareaContinua]:  # pragma: no cover - compat
    return TaskRegistry().get_continuous_tasks()


def get_all_tasks() -> List:  # pragma: no cover - compat
    return TaskRegistry().get_all_tasks()


__all__ = [
    'TaskRegistry',
    'get_all_daily_tasks',
    'get_all_continuous_tasks',
    'get_all_tasks',
    # Clases de tareas
    'RiesgosTask', 'BrassTask', 'ExpedientesTask', 'NoConformidadesTask', 'AgedysTask',
    'CorreosTask', 'CorreoTareasTask'
]