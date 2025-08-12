Blueprint del Proyecto de Automatización
1. Introducción
Este documento describe la arquitectura y los patrones de diseño del proyecto de automatización. Su propósito es servir como guía para el mantenimiento y la extensión del sistema, asegurando que el nuevo código siga una estructura coherente, limpia y fácil de probar.

2. Principios Fundamentales de la Arquitectura
El diseño del proyecto se basa en los siguientes principios clave:

Separación de Responsabilidades (Task vs. Manager): Es el pilar de la arquitectura.

Manager (_manager.py): Contiene la lógica de negocio pura. Sus responsabilidades son consultar bases de datos, procesar datos y generar informes. No sabe cuándo debe ejecutarse.

Task (_task.py): Actúa como orquestador. Su responsabilidad es decidir cuándo debe ejecutarse una tarea (planificación, frecuencia) y llamar al Manager para que haga el trabajo.

Orquestación Centralizada:

El script scripts/run_master.py es el único punto de entrada para la ejecución programada de todas las tareas.

Utiliza un TaskRegistry (src/common/task_registry.py) para descubrir y ejecutar las tareas disponibles.

Configuración Centralizada:

Entorno y BD: El archivo .env y la clase Config (src/common/config.py) centralizan todas las rutas de bases de datos, credenciales y configuraciones de entorno.

Informes HTML: El archivo src/common/reporting/table_configurations.py centraliza la definición (títulos, columnas, formatos) de todas las tablas HTML que se generan en los informes.

Logging Unificado:

Toda la aplicación utiliza un sistema de logging global configurado en src/common/logger.py.

Todos los logs se escriben en la consola y en un único archivo (logs/app.log), lo que facilita la integración con sistemas de monitoreo como Loki/Grafana.

3. Estructura del Repositorio
La estructura de carpetas sigue un patrón estándar para facilitar la navegación:

.
├── .github/workflows/         # Flujos de CI/CD (Linter, CodeQL)
├── analysis/                  # Dockerfile y scripts para análisis de código local
├── dbs-locales/               # Bases de datos Access para el entorno local
├── docs/                      # Documentación del proyecto (como este archivo)
├── examples/                  # Ejemplos de uso y conectividad
├── grafana/                   # Configuración de dashboards y datasources de Grafana
│   └── provisioning/
├── herramientas/              # Recursos auxiliares (festivos, CSS, etc.)
├── htmlcov/                   # Reportes de cobertura HTML generados automáticamente
├── logs/                      # Archivos de log generados por la aplicación
├── loki/                      # Configuración de Loki (monitorización de logs)
├── promtail/                  # Configuración de Promtail (recolección de logs)
├── scripts/                   # Scripts ejecutables (runners)
│   ├── run_master.py          # Orquestador principal
│   ├── run_agedys.py          # Runner AGEDYS
│   ├── run_brass.py           # Runner BRASS
│   ├── run_expedientes.py     # Runner EXPEDIENTES
│   ├── run_no_conformidades.py# Runner NO CONFORMIDADES
│   ├── run_riesgos.py         # Runner RIESGOS
│   └── run_email_services.py  # Runner para servicios de correo
├── src/                       # Código fuente de la aplicación
│   ├── common/                # Módulos y utilidades compartidas
│   │   ├── db/                # Lógica de conexión a BD y pools
│   │   ├── reporting/         # Generación de informes y configuración de tablas
│   │   ├── __init__.py
│   │   ├── base_task.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   ├── task_registry.py
│   │   ├── user_adapter.py
│   │   └── utils.py
│   ├── agedys/                # Módulo de negocio AGEDYS
│   │   ├── agedys_manager.py
│   │   ├── agedys_task.py
│   │   └── ...
│   ├── brass/                 # Módulo de negocio BRASS
│   │   ├── brass_manager.py
│   │   ├── brass_task.py
│   │   └── run_brass.py
│   ├── email_services/        # Módulo para el envío de correos
│   │   ├── email_manager.py
│   │   └── ...
│   ├── expedientes/           # Módulo de negocio EXPEDIENTES
│   │   ├── expedientes_manager.py
│   │   ├── expedientes_task.py
│   │   └── ...
│   ├── no_conformidades/      # Módulo de negocio NO CONFORMIDADES
│   │   ├── no_conformidades_manager.py
│   │   ├── no_conformidades_task.py
│   │   ├── report_registrar.py
│   │   └── ...
│   ├── riesgos/               # Módulo de negocio RIESGOS
│   │   ├── riesgos_manager.py
│   │   ├── riesgos_task.py
│   │   └── ...
│   └── ...                    # Otros módulos de negocio
├── tests/                     # Tests unitarios y de integración
│   ├── integration/           # Tests de integración por módulo
│   │   ├── agedys/
│   │   ├── brass/
│   │   ├── database/
│   │   ├── expedientes/
│   │   ├── no_conformidades/
│   │   └── riesgos/
│   ├── unit/                  # Tests unitarios por módulo
│   │   ├── agedys/
│   │   ├── brass/
│   │   ├── common/
│   │   ├── expedientes/
│   │   ├── master/
│   │   ├── no_conformidades/
│   │   ├── riesgos/
│   │   └── ...
│   └── ...
├── tools/                     # Scripts utilitarios y de mantenimiento
├── .env                       # Archivo de configuración de entorno
├── docker-compose.yml         # Orquestación de servicios (Loki, Grafana, SonarQube)
├── pyproject.toml             # Configuración de herramientas de desarrollo (black, pytest, etc.)
├── pytest.ini                 # Configuración de pytest
├── README.md                  # Documentación principal del proyecto
├── requirements-dev.txt       # Dependencias de desarrollo
├── requirements.txt           # Dependencias de Python
├── scripts_config.json        # Configuración de runners y mapeo de tareas
├── sonar-project.properties   # Configuración de SonarQube
└── ARCHITECTURE.md            # Blueprint y arquitectura del proyecto

4. Anatomía de un Módulo de Negocio (Ej: src/brass/)
Cada módulo que implementa una lógica de negocio específica debe seguir esta estructura:

__init__.py: Define el directorio como un paquete de Python.

brass_manager.py:

Contiene la clase BrassManager.

NO hereda de ninguna clase base.

Recibe las conexiones a la base de datos en su constructor.

Implementa métodos para la lógica de negocio: get_equipment_out_of_calibration(), generate_brass_report_html().

brass_task.py:

Contiene la clase BrassTask.

SIEMPRE hereda de TareaDiaria o TareaContinua (common.base_task).

En su método execute_specific_logic(), crea una instancia del BrassManager y lo utiliza para ejecutar la lógica.

Define la planificación (frecuencia, días de ejecución, etc.).

5. Guía: Cómo Añadir un Nuevo Módulo (Ej: "Inventario")
Para añadir una nueva funcionalidad, sigue estos pasos:

Crear la Estructura de Carpetas:

Crea la carpeta src/inventario/.

Crea la carpeta de tests tests/unit/inventario/.

Crear el Manager (src/inventario/inventario_manager.py):

Define la clase InventarioManager.

Añade los métodos con la lógica de negocio (consultas a la BD de inventario, generación de su informe, etc.).

Crear la Task (src/inventario/inventario_task.py):

Define la clase InventarioTask que herede de TareaDiaria.

Implementa execute_specific_logic() para que use el InventarioManager.

Crear el Runner (scripts/run_inventario.py):

Crea un script simple que importe InventarioTask y la ejecute usando la función execute_task_with_standard_boilerplate.

Registrar la Tarea:

Abre src/common/task_registry.py.

Importa la nueva InventarioTask.

Añade una instancia de InventarioTask() a la lista de tareas diarias.

Añadir la Configuración del Runner:

Abre scripts_config.json.

Añade una nueva entrada para la tarea "inventario", especificando su tipo (daily) y el nombre del archivo runner (run_inventario.py).

(Opcional) Añadir Configuración de Tablas:

Abre src/common/reporting/table_configurations.py.

Añade un nuevo diccionario INVENTARIO_TABLE_CONFIGURATIONS con la definición de las tablas para el informe de inventario.

Haz que InventarioManager importe y use esta configuración.

6. Modelo de Ejecución del Orquestador (run_master.py)

- Entrada única: `scripts/run_master.py` es el punto de entrada para ejecución programada y manual.
- Descubrimiento de tareas: usa `common.task_registry.TaskRegistry` para obtener instancias de tareas diarias y continuas.
- Ejecución secuencial: tanto las tareas diarias como las continuas se ejecutan una a una (sin hilos). Esto facilita el razonamiento, evita condiciones de carrera y simplifica el logging y el control de errores.
	- Diarias: se comprueba `debe_ejecutarse()` antes de `ejecutar()`; si tiene éxito, se marca con `marcar_como_completada()`.
	- Continuas: se invoca `ejecutar()` directamente (sin comprobación previa), registrando éxito/fracaso por tarea.
- Registro y sumario: cada ciclo registra un resumen con contadores de éxito/fallo y detalles por tarea.
- Configuración: `scripts_config.json` define scripts disponibles (p. ej., `brass`, `riesgos`) y tipos (diaria/continua). El orquestador carga esta configuración al inicio y la expone en los logs.
- Modo dry-run para tests: cuando `MASTER_DRY_SUBPROCESS=1` y se usa modo de ciclo único, el orquestador recorre un camino rápido (fast-path) que imprime claves de scripts y un mini-resumen, y termina enseguida. Este camino existe solo para pruebas, no debe usarse en producción.
