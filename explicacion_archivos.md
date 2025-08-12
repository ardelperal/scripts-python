El Blueprint (El más importante):

ARCHITECTURE.md (el archivo que creamos en el Canvas).

Los Pilares de la Arquitectura (Módulo common):

src/common/base_task.py (Define TareaDiaria y TareaContinua).

src/common/task_registry.py (Define cómo se descubren las tareas).

src/common/config.py (Define cómo funciona la configuración).

src/common/reporting/table_configurations.py (El archivo central de configuración de tablas).

src/common/logger.py (El sistema de logging unificado).

El Orquestador Principal:

scripts/run_master.py (El punto de entrada que une todo).

Un Módulo de Ejemplo Perfecto (Ej: BRASS):

src/brass/brass_manager.py

src/brass/brass_task.py

scripts/run_brass.py

