# Sistema de Gestión de Tareas Empresariales

[![CI](https://github.com/ardelperal/scripts-python/actions/workflows/python-ci.yml/badge.svg?branch=main)](https://github.com/ardelperal/scripts-python/actions/workflows/python-ci.yml)
[![Coverage](https://codecov.io/gh/ardelperal/scripts-python/branch/main/graph/badge.svg)](https://codecov.io/gh/ardelperal/scripts-python)

Sistema de **monitoreo continuo** para la gestión automatizada de tareas empresariales desarrollado en Python. El objetivo principal es ejecutar el script maestro `run_master.py` que funciona como un **daemon de producción** que monitorea y ejecuta automáticamente todos los módulos del sistema según horarios específicos.

## 🎯 Objetivo Principal

El **script maestro (`run_master.py`)** es el corazón del sistema y reemplaza al script original `script-continuo.vbs`. Funciona como un **servicio continuo** que:

- 🔄 **Monitorea continuamente** todos los sistemas involucrados
- ⏰ **Ejecuta tareas diarias** una vez por día laborable (después de las 7 AM)
- 📧 **Ejecuta tareas continuas** (correos y tareas) en cada ciclo
- 📅 **Respeta días festivos** y horarios laborables
- ⚙️ **Ajusta tiempos de ciclo** según horario y tipo de día
- 📊 **Genera logs detallados** y archivos de estado
- 🛡️ **Manejo robusto de errores** y recuperación automática
- 🔍 **Modo verbose** para debugging y monitoreo detallado

### 📋 Módulos Integrados en el Script Maestro

#### Tareas Diarias (ejecutadas una vez por día laborable):
1. **AGEDYS** (`run_agedys.py`): Sistema de gestión de facturas y visados técnicos
2. **BRASS** (`run_brass.py`): Sistema de gestión de tareas BRASS  
3. **Expedientes** (`run_expedientes.py`): Gestión de expedientes y documentación
4. **No Conformidades** (`run_no_conformidades.py`): Gestión de no conformidades
5. **Riesgos** (`run_riesgos.py`): Gestión de riesgos empresariales

#### Tareas Continuas (ejecutadas en cada ciclo):
6. **Email Services** (`run_email_services.py`): Servicio unificado de envío de correos (fusiona antiguos módulos `correos` y `correo_tareas`)

### 🆕 Cambios Arquitectónicos Recientes (Refactor 2025)

Refactor integral para simplificar arquitectura, mejorar testabilidad y eliminar código legacy.

Principales mejoras:
1. Capa de datos unificada:
   - Eliminados `AccessAdapter` y `DemoDatabase`.
   - Nueva clase única `AccessDatabase` con soporte opcional de pool.
   - Introducido `AccessConnectionPool` (gestiona instancias reutilizables por cadena de conexión).
2. Gestión de tareas:
   - Reemplazo de funciones globales por clase `TaskRegistry` (extensible, inyectable, test-friendly).
   - API: `get_daily_tasks()`, `get_continuous_tasks()`, `get_all_tasks()`, `summary()`, filtros y extensión por parámetros `extra_daily/extra_continuous`.
   - Backwards compatibility: funciones wrapper conservadas para código legado.
3. Script maestro (`run_master.py`):
   - Consolidado antiguo `run_master_new.py` (eliminado).
   - Añadido modo `--simple` sobre `TaskRegistry` con resumen estructurado.
   - Fast-path en tests (`MASTER_DRY_SUBPROCESS=1`) evitando importaciones pesadas.
4. Riesgos y No Conformidades: parametrización explícita de frecuencias vía variables de entorno para subtareas.
5. Limpieza y cobertura:
   - Eliminado definitivamente archivo legacy `database_adapter.py` y su test.
   - Stub ligero de `RiesgosTask` para unit tests cuando el módulo completo no es necesario.
6. Documentación actualizada: ejemplos de extensión de tareas, uso de pools y guía de migración.

Pendiente futuro (no implementado aún):
- Sistema de plugins de tareas (descubrimiento dinámico).
- Persistencia de métricas de ejecución (duración/estado) para observabilidad.
- Reducción selectiva de coste de importación en módulos grandes (lazy loading adicional).

### Uso de TaskRegistry

```python
from common.task_registry import TaskRegistry

registry = TaskRegistry()
for task in registry.get_daily_tasks():
   if task.debe_ejecutarse():
      task.ejecutar()
      task.marcar_como_completada()
```

Extender con tareas personalizadas:

```python
from common.base_task import TareaDiaria
from common.task_registry import TaskRegistry

class MiTarea(TareaDiaria):
   def __init__(self):
      super().__init__(name="MiTarea", script_filename="run_mi_tarea.py", task_names=["MiTareaDiaria"], frequency_days=1)
   def debe_ejecutarse(self):
      return True
   def marcar_como_completada(self):
      pass

registry = TaskRegistry(extra_daily=[MiTarea()])
```

### Helper de Ejecución Unificada

Para reducir boilerplate en los `run_*.py`, todas las tareas se ejecutan mediante `execute_task_with_standard_boilerplate` (`common.utils`).

Características:
* Logging estándar con fichero dedicado `logs/<tarea>.log`.
* Banners `=== INICIO TAREA X ===` / `=== FIN TAREA X ===`.
* Modos soportados: normal, `--force` (ignora planificación y NO marca completada) y `--dry-run` (sólo evalúa planificación).
* Detección automática del método de lógica: `execute_specific_logic` > `execute_logic` > `execute`.
* Invoca `initialize()` si existe antes de la lógica.
* Marca completada sólo en tareas diarias exitosas (y no en `--force`).

Ejemplo de runner minimalista:

```python
import sys
from common.utils import execute_task_with_standard_boilerplate
from email_services.email_task import EmailServicesTask

def main():
   task = EmailServicesTask()
   code = execute_task_with_standard_boilerplate("CORREOS", task_obj=task)
   sys.exit(code)

if __name__ == "__main__":
   main()
```

Para lógica puntual sin clase se puede usar `custom_logic=callable`, pero se recomienda migrar a clases `TareaDiaria` / `TareaContinua` para uniformidad y testabilidad.

#### Añadir una nueva tarea
1. Crear clase `TareaDiaria` o `TareaContinua` con `execute_specific_logic`.
2. Registrar en `TaskRegistry` o pasar como `extra_*`.
3. Crear `run_<tarea>.py` que sólo instancie y llame al helper.
4. Añadir tests (mock de planificación y lógica).

#### ensure_project_root_in_path

Los runners llaman a `ensure_project_root_in_path()` (en `common.utils`) para insertar `src` en `sys.path` de forma idempotente, eliminando bloques repetidos de manipulación manual.


### Acceso unificado a BD

```python
from common.database import AccessDatabase
from common.access_connection_pool import get_tareas_connection_pool
from common.config import config

conn_str = config.get_db_tareas_connection_string()
pool = get_tareas_connection_pool(conn_str)
db = AccessDatabase(conn_str, pool=pool)
rows = db.execute_query("SELECT TOP 1 * FROM TbTareas")
```

### 🚀 Modo Verbose del Script Maestro

El script maestro incluye un **modo verbose** para debugging y monitoreo detallado:

```bash
# Ejecución normal
python scripts/run_master.py

# Ejecución con modo verbose (detallado)
python scripts/run_master.py --verbose
python scripts/run_master.py -v

# Ver ayuda
python scripts/run_master.py --help
```

**Características del Modo Verbose:**
- 📊 **Información detallada de configuración** al inicio
- 🔍 **Logs detallados de cada script** ejecutado
- ⏱️ **Tiempos de ejecución** de cada script individual
- 📈 **Estadísticas completas** de éxito/fallo por ciclo
- 🎯 **Información de salida** (stdout/stderr) de cada script
- 📋 **Resúmenes de ciclo** con métricas detalladas
- 🕐 **Información de espera** con tiempo estimado de reanudación

### Tiempos de Ciclo del Master Runner

El sistema ajusta automáticamente los tiempos de espera entre ciclos según el contexto:

| Contexto | Tiempo de Ciclo | Descripción |
|----------|----------------|-------------|
| **Día Laborable - Día** | 5 minutos | Monitoreo intensivo en horario laboral |
| **Día Laborable - Noche** | 60 minutos | Monitoreo reducido fuera de horario |
| **Día No Laborable - Día** | 60 minutos | Monitoreo básico en fines de semana |
| **Día No Laborable - Noche** | 120 minutos | Monitoreo mínimo en noches de fin de semana |

*Horario nocturno: 20:00 - 07:00*

## 📋 Tabla de Contenidos

- [🚀 Guía Rápida para Desarrolladores](#-guía-rápida-para-desarrolladores)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Características Implementadas](#características-implementadas)
- [Configuración de Entornos](#configuración-de-entornos)
- [📊 Estado de Cobertura de Tests](#-estado-de-cobertura-de-tests)
- [Instalación (Método Tradicional)](#instalación-método-tradicional)
- [Uso](#uso)
- [🔧 Script de Configuración del Entorno Local](#-script-de-configuración-del-entorno-local)
- [Seguridad](#seguridad)
- [Testing](#testing)
- [Variables de Entorno Principales](#variables-de-entorno-principales)
- [Arquitectura](#arquitectura)
- [Arquitectura](#arquitectura)
- [Arquitectura de Tareas](#arquitectura-de-tareas)

## Estructura del Proyecto

```
scripts-python/
├── .coveragerc                  # Configuración coverage.py
├── .env.example                 # Plantilla de variables de entorno
├── .gitignore                   # Archivos ignorados por Git
├── GEMINI.md                    # Documentación específica Gemini
├── README.md                    # Documentación principal
├── pyproject.toml               # Configuración de pytest y herramientas
├── requirements.txt             # Dependencias Python
├── .trae/                       # Configuración Trae AI
│   └── rules/
│       └── project_rules.md     # Reglas del proyecto
├── dbs-locales/                 # Bases de datos locales
├── docs/                        # Documentación
│   ├── NO_CONFORMIDADES.md      # Documentación no conformidades
│   ├── coverage_setup_summary.md # Resumen configuración coverage
│   ├── htmlcov_usage_guide.md   # Guía uso reportes HTML
│   ├── migracion_riesgos.md     # Guía migración GestionRiesgos.vbs
│   ├── panel_control_guia.md    # Guía del panel de control
│   ├── riesgos.md               # Documentación módulo de riesgos
│   ├── smtp_config_changes.md   # Cambios configuración SMTP
│   └── smtp_override_config.md  # Configuración override SMTP
├── examples/                    # Ejemplos y demos
│   ├── README.md                # Documentación de ejemplos
│   ├── database_connectivity_demo.py # Demo conectividad BD
│   ├── ejemplo_riesgos.py       # Ejemplo uso módulo riesgos
│   ├── smtp_config_demo.py      # Demo configuración SMTP
│   └── smtp_override_demo.py    # Demo override SMTP
├── herramientas/                # Archivos de configuración
│   └── CSS_moderno.css          # Estilos CSS modernos
├── original/                      # Sistema VBS original
│   ├── AGEDYS.VBS               # Sistema AGEDYS original
│   ├── BRASS.vbs                # Sistema BRASS original
│   ├── EnviarCorreoNoEnviado.vbs # Sistema correos original
│   ├── EnviarCorreoTareas.vbs   # Sistema tareas original
│   ├── Expedientes.vbs          # Sistema expedientes original
│   ├── GestionRiesgos.vbs       # Sistema riesgos original
│   ├── NoConformidades.vbs      # Sistema no conformidades original
│   ├── Nuevo Documento de texto.html # Archivo HTML original
│   └── script-continuo.vbs      # Script continuo original
├── logs/                        # Archivos de log del sistema
│   └── run_master_status.json   # Estado del script maestro
├── scripts/                     # Scripts principales de ejecución
│   ├── README.md                # Documentación de scripts
│   ├── migrations/              # Scripts de migración
│   │   └── add_status_to_tareas_db.py # Migración estado tareas
│   ├── run_agedys.py            # Script para módulo AGEDYS
│   ├── run_brass.py             # Script principal para módulo BRASS
│   ├── run_email_services.py    # Runner unificado de servicios de correo
│   ├── run_expedientes.py       # Script para módulo expedientes
│   ├── run_master.py            # Script maestro - daemon principal con modo verbose
│   ├── run_no_conformidades.py  # Script para no conformidades
│   └── run_riesgos.py           # Script para módulo de riesgos
├── src/                         # Código fuente
│   ├── __init__.py
│   ├── agedys/                  # Módulo AGEDYS (migrado)
│   │   ├── __init__.py
│   │   ├── agedys_manager.py    # Gestor principal AGEDYS
│   │   └── agedys_task.py       # Tareas AGEDYS
│   ├── brass/                   # Módulo BRASS (migrado)
│   │   ├── __init__.py
│   │   ├── brass_manager.py     # Gestor principal BRASS
│   │   ├── brass_task.py        # Tareas BRASS
│   │   └── run_brass.py         # Script BRASS interno
│   ├── common/                  # Utilidades compartidas
│   │   ├── __init__.py
│   │   ├── access_connection_pool.py # Pool de conexiones Access
│   │   ├── base_email_manager.py # Gestor base para emails
│   │   ├── base_task.py         # Clase base para tareas
│   │   ├── config.py            # Configuración multi-entorno
│   │   ├── database.py          # Capa unificada Access (AccessDatabase + pools)
│   │   ├── html_report_generator.py # Generador reportes HTML
│   │   ├── logger.py            # Sistema de logging
│   │   ├── notifications.py     # Sistema de notificaciones
│   │   ├── task_registry.py     # Registro de tareas (TaskRegistry OO)
│   │   ├── user_adapter.py      # Adaptador de usuarios
│   │   └── utils.py             # Utilidades HTML, logging, fechas
│   ├── email_services/          # Módulo unificado de correos (correos + tareas)
│   │   ├── __init__.py
│   │   ├── email_manager.py     # Lógica centralizada de envío
│   │   └── email_task.py        # Task continua unificada
│   ├── expedientes/             # Módulo de expedientes
│   │   ├── __init__.py
│   │   ├── expedientes_manager.py # Gestor de expedientes
│   │   └── expedientes_task.py  # Tareas de expedientes
│   ├── no_conformidades/        # Módulo de no conformidades
│   │   ├── __init__.py
│   │   ├── no_conformidades_manager.py # Gestor principal
│   │   ├── no_conformidades_task.py # Tareas no conformidades
│   │   ├── report_registrar.py  # Registrador de reportes
│   │   └── run_no_conformidades.py # Script no conformidades interno
│   └── riesgos/                 # Módulo de gestión de riesgos
│       ├── __init__.py
│       └── riesgos_manager.py   # Gestor de riesgos
├── tests/                       # Tests automatizados (cobertura >80%)
│   ├── __init__.py
│   ├── config.py                # Configuración de tests
│   ├── conftest.py              # Configuración global pytest
│   ├── data/                    # Datos de test
│   │   └── __init__.py
│   ├── fixtures/                # Datos y utilidades de prueba
│   │   ├── __init__.py
│   │   ├── create_demo_databases.py
│   │   ├── create_test_emails_demo.py
│   │   └── setup_smtp_local.py
│   ├── functional/              # Tests funcionales
│   │   ├── access_sync/         # Sincronización con Access
│   │   └── correos_workflows/   # Flujos completos de correos
│   ├── integration/             # Tests de integración
│   │   ├── __init__.py
│   │   ├── agedys/              # Integración del sistema AGEDYS
│   │   ├── brass/               # Integración del sistema brass
│   │   ├── email_services/      # Integración del servicio unificado de correos
│   │   ├── database/            # Integración con bases de datos
│   │   ├── expedientes/         # Integración del sistema de expedientes
│   │   ├── no_conformidades/    # Integración no conformidades
│   │   └── riesgos/             # Integración del sistema de riesgos
│   └── unit/                    # Tests unitarios por módulo
│       ├── __init__.py
│       ├── agedys/              # Tests específicos AGEDYS
│       ├── brass/               # Tests específicos BRASS
│       ├── common/              # Tests módulos comunes
│       ├── email_services/      # Tests del servicio unificado de correos
│       ├── expedientes/         # Tests del módulo de expedientes
│       ├── no_conformidades/    # Tests no conformidades
│       └── riesgos/             # Tests del módulo de riesgos
└── tools/                       # Herramientas de desarrollo y utilidades
    ├── README.md                # Documentación de herramientas
    ├── check_coverage_dependencies.py # Verificación dependencias coverage
    ├── check_email_recipients.py # Verificación destinatarios email
    ├── check_email_status.py    # Verificación estado emails
    ├── check_email_structure.py # Verificación estructura emails
    ├── continuous_runner.py     # Ejecución continua de tests
    ├── generate_coverage_report.py # Generador reportes de cobertura
    ├── generate_full_coverage_report.py # Generador reportes completos
    ├── prepare_test_emails.py   # Preparación emails de prueba
    └── setup_local_environment.py # Configuración entorno local
│   ├── database_connectivity_demo.py # Demo conectividad BD
│   ├── smtp_config_demo.py     # Demo configuración SMTP
│   ├── smtp_override_demo.py   # Demo override SMTP
│   └── ejemplo_riesgos.py      # Ejemplo uso módulo riesgos
├── original/                    # Sistema VBS original
    ├── AGEDYS.VBS             # Sistema AGEDYS original
    ├── BRASS.vbs              # Sistema BRASS original
    ├── Expedientes.vbs        # Sistema expedientes original
    ├── GestionRiesgos.vbs     # Sistema riesgos original
    ├── NoConformidades.vbs    # Sistema no conformidades original
    ├── EnviarCorreoNoEnviado.vbs # Sistema correos original
    ├── EnviarCorreoTareas.vbs    # Sistema tareas original
    └── script-continuo.vbs       # Script continuo original
```

## Características Implementadas

### ✅ Módulos del Sistema
- **AGEDYS**: Sistema completo de gestión de facturas y visados técnicos
- **BRASS**: Sistema completo de gestión de tareas BRASS
- **Expedientes**: Gestión de expedientes y documentación
- **Correos**: Sistema de envío y gestión de correos electrónicos
- **Tareas**: Sistema de gestión de tareas empresariales
- **No Conformidades**: Gestión de no conformidades y seguimiento
- **Riesgos**: Gestión completa de riesgos empresariales

## � Módulo No Conformidades – Funcionamiento, Arquitectura y Flujo

> Esta sección ha sido revisada tras la refactorización: unificación de generación HTML, método genérico para recuperación de ARs por técnico, tipado fuerte y manejo específico de errores.

### 1. Propósito
Automatizar el seguimiento y la comunicación sobre:
* No Conformidades (NCs) abiertas y su ciclo de vida.
* Acciones Correctivas / Preventivas (AR / ARAP) asociadas y su proximidad a vencimiento.
* Controles de eficacia pendientes tras el cierre.
* Replanificación de tareas y avisos escalonados a técnicos y calidad.

### 2. Componentes Principales
| Componente | Archivo | Responsabilidad clave |
|------------|---------|-----------------------|
| Runner CLI | `scripts/run_no_conformidades.py` | Orquestación, flags de fuerza / dry-run, logging y registro de tareas. |
| Manager | `src/no_conformidades/no_conformidades_manager.py` | Lógica de negocio, consultas SQL, flujo de generación interna. |
| Registrador | `src/no_conformidades/report_registrar.py` | Construcción y registro final de emails (calidad / técnicos). |
| Generador HTML | `src/common/html_report_generator.py` | Header / footer modernos y tablas unificadas. |
| Tipos | `src/no_conformidades/types.py` | TypedDict para estructuras de datos AR técnicas y calidad. |
| Persistencia Avisos | Tabla `TbNCARAvisos` | Evita correos repetidos por AR y rango (0 / 7 / 15 días). |
| Registro Email | Tabla `TbCorreosEnviados` (BD Tareas) | Trazabilidad de envíos y cuerpo HTML. |

### 3. Flujo Alto Nivel
```mermaid
flowchart TD
  A[Ejecutar run_no_conformidades.py] --> B{Flags fuerza?}
  B -->|--force-all| C[Calidad + Técnicos]
  B -->|--force-calidad| C1[Calidad]
  B -->|--force-tecnica| C2[Técnicos]
  B -->|Normal| D[Evalúa should_execute_*( )]
  D --> C
  C --> E[Manager obtiene datos]
  E --> F[HTMLReportGenerator compone HTML]
  F --> G[ReportRegistrar registra correo]
  G --> H[Registrar avisos TbNCARAvisos]
  H --> I[Actualizar TbTareas]
```

### 4. Consultas Clave (Resumen)
Calidad consolida 4 bloques de datos:
1. ARs próximas a vencer (<16 días) o vencidas sin fecha real.
2. NCs resueltas pendientes de control de eficacia (<30 días para control) aún sin control efectuado.
3. NCs sin acciones correctivas registradas.
4. ARs a replanificar (FechaFinPrevista <16 días / vencida y abierta).

Técnicos (por cada responsable):
* ARs 8–15 días (primer aviso – campo `IDCorreo15`).
* ARs 1–7 días (aviso urgente – `IDCorreo7`).
* ARs vencidas (≤0 días – `IDCorreo0`).

### 5. Método Genérico de Recuperación de ARs Técnicas
Se sustituyeron tres métodos duplicados por `_get_ars_tecnico(...)`, que parametriza:
* Rango de días (`dias_min`, `dias_max`) o bandera `vencidas`.
* Campo de control de aviso (`IDCorreo0`, `IDCorreo7`, `IDCorreo15`).
* Responsable (`RESPONSABLETELEFONICA`).

Esto reduce deuda técnica y facilita futuros ajustes de ventanas de aviso.

### 6. Unificación HTML
Todo el marcado moderno se centraliza en `HTMLReportGenerator`:
* `generar_header_moderno` / `generar_footer_moderno`.
* Tablas: `tabla_arapc_proximas`, `tabla_nc_pendientes_eficacia`, `tabla_nc_sin_acciones`, `tabla_ars_replanificar`, `tabla_ar_tecnico`.
* Reportes compuestos: `generar_reporte_calidad_moderno` y `generar_reporte_tecnico_moderno`.

Beneficios: estilo consistente, menor duplicación, facilidad para personalizar CSS global.

### 7. Control de Avisos (Anti-duplicado)
Tabla `TbNCARAvisos` mantiene columnas `IDCorreo0`, `IDCorreo7`, `IDCorreo15` por AR (`IDAR`). El manager:
1. Consulta si existe la fila (`IDAR`).
2. Inserta (con nuevo ID secuencial) o actualiza el campo de aviso.
3. Evita reenviar avisos ya marcados sin borrar histórico.

### 8. Manejo de Errores
* Errores de base de datos: captura específica (cuando `pyodbc` disponible) para logging diferenciado.
* Fallback genérico con `logger.exception` para trazas completas.
* Cierre seguro de conexiones incluso ante fallos parciales.

### 9. Tipado y Mantenibilidad
`types.py` define `ARTecnicaRecord` y `ARCalidadProximaRecord`. Ventajas:
* Mejora autocompletado IDE.
* Reduce errores de clave en dicts dinámicos.
* Base futura para migrar a `dataclasses` si se requiere inmutabilidad o validación.

### 10. Variables y Parámetros Relevantes
| Concepto | Variable / Origen | Descripción |
|----------|-------------------|-------------|
| Días ventana AR técnicos | Hardcoded (8–15 / 1–7 / ≤0) | Ajustables modificando llamadas a `_get_ars_tecnico`. |
| Umbral AR calidad | `<16` días | Consulta SQL principal. |
| Umbral control eficacia | `<30` días | Consulta NC eficacia. |
| App ID módulo | `APP_ID_NOCONFORMIDADES=8` (.env) | Identifica aplicación en registros. |
| CSS moderno | `herramientas/CSS_moderno.css` | Inyectado inline para emails. |

### 11. Ejecución Directa
```powershell
# Forzar ambas tareas (calidad + técnicos)
python scripts/run_no_conformidades.py --force-all

# Solo calidad
python scripts/run_no_conformidades.py --force-calidad

# Solo técnicos con logging detallado
python scripts/run_no_conformidades.py --force-tecnica -v

# Simulación (sin ingresar correos) – si se desea (modo no forzado existente en código)
python scripts/run_no_conformidades.py --dry-run
```

### 12. Pseudocódigo Simplificado Runner
```python
if args.force/all -> set flags
else:
  with NoConformidadesManager() as m:
    ejecutar_calidad = m.should_execute_quality_task()
    ejecutar_tecnica = m.should_execute_technical_task()

if ejecutar_calidad:
   ejecutar_tarea_calidad()
if ejecutar_tecnica:
   ejecutar_tarea_tecnica()
```

### 13. Depuración y Artefactos
* HTML de debug opcional guardado (si se activa internamente) en `src/no_conformidades/debug_html/`.
* Logs específicos: `logs/no_conformidades.log` (vía `setup_logging`).
* Revisar avisos en `TbNCARAvisos` para validar no duplicidades.

### 14. Pruebas
Archivo principal unitario: `tests/unit/no_conformidades/test_no_conformidades_manager.py` incluye:
* Casos de consulta simulada (mock DB) para rangos 8–15, 1–7 y vencidas.
* Inserción / actualización de avisos (`registrar_aviso_ar`).
* Generación de HTML moderno (calidad y técnico) con datos mínimos.

Sugerencias futuras:
* Test parametrizado de branch de error `DBErrors` simulando `pyodbc.Error`.
* Verificación de que un segundo envío no re-registra avisos ya existentes.

### 15. Extensión Rápida
Para añadir un nuevo rango (ej. 16–30 días) a técnicos:
1. Añadir llamada nueva a `_get_ars_tecnico(tecnico, 16, 30, 'IDCorreo30')` (requiere columna extra en `TbNCARAvisos`).
2. Ampliar tabla HTML (`tabla_ar_tecnico`).
3. Ajustar registrar avisos y tests.

---

## 🗃️ Control de Avisos

El sistema mantiene un registro de avisos enviados en la tabla `TbNCARAvisos`:

- **Campos de control**: `IDCorreo15`, `IDCorreo7`, `IDCorreo0`
- **Prevención de duplicados**: No se envían avisos ya notificados
- **Trazabilidad**: Registro de fecha y ID de correo para cada aviso
- **Gestión automática**: Inserción/actualización según existencia previa

### ⚙️ Configuración y Parámetros

- **Días de alerta ARAP**: 16 días (configurable)
- **Días de alerta NC**: 30 días para control de eficacia
- **Rangos de notificación técnicos**: 15, 7 y 0 días
- **Aplicación**: `NoConformidades` (campo en registro de correos)
- **Conexiones BD**: Base de datos NC y Tareas (separadas)
- **CSS**: Estilos modernos cargados desde archivo de configuración

### 🚀 Ejecución y Monitoreo

El módulo puede ejecutarse:

- **Automáticamente**: Como parte del Master Runner
- **Manualmente**: Con opciones de forzado específicas:
  - `--force-calidad`: Solo correos de calidad
  - `--force-tecnicos`: Solo correos de técnicos
  - `--debug`: Modo debug con logging detallado

**Logging detallado** incluye:
- Número de registros encontrados por consulta
- Técnicos procesados y correos generados
- Errores y excepciones con contexto
- Tiempos de ejecución y estado de conexiones

### 🔧 Infraestructura y Herramientas
- **Sistema de Testing**: Tests automatizados con cobertura >80%
- **Configuración Multi-entorno**: Desarrollo, testing y producción
- **Logging Avanzado**: Sistema de logs estructurado y configurable
- **Base de Datos**: Capa de abstracción para Microsoft Access
- **Reportes HTML**: Generación automática de reportes visuales
- **Herramientas de Desarrollo**: Scripts de setup, testing y monitoreo

### 📊 Calidad y Testing
- **Cobertura de Código**: >80% con reportes HTML detallados
- **Tests Unitarios**: Tests completos para todos los módulos
- **Tests de Integración**: Tests de integración con bases de datos
- **Tests Funcionales**: Validación de flujos completos
- **Tests Manuales**: Herramientas para testing manual y debugging

### 🔒 Seguridad
- **Enmascaramiento de contraseñas** en logs y salidas de consola
- **Protección de información sensible** en cadenas de conexión
- **Función utilitaria** `hide_password_in_connection_string` para logging seguro
- **Validación de seguridad** con tests automatizados

### 🚀 Características Avanzadas
- **Configuración SMTP Flexible**: Soporte para múltiples proveedores
- **Gestión de Usuarios**: Adaptador unificado para diferentes sistemas
- **Notificaciones**: Sistema de notificaciones por email
- **Plantillas HTML**: Sistema de plantillas para reportes y emails
- **Manejo de Errores**: Sistema robusto de manejo de excepciones
- **Sistema Modular**: Arquitectura modular y extensible

## Configuración de Entornos

El sistema soporta dos entornos configurables mediante el archivo `.env` con **separación completa de configuraciones**:

### Configuración inicial
```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar configuraciones específicas (NUNCA incluir contraseñas reales en el README)
nano .env  # o tu editor preferido
```

### Entorno Local (`ENVIRONMENT=local`)
- **Bases de datos**: Archivos `.accdb` en `dbs-locales/`
- **Archivos CSS**: `herramientas/CSS.txt`
- **SMTP**: MailHog local (localhost:1025)
- **Uso**: Desarrollo, testing, trabajo sin red corporativa
- **Ventajas**: No requiere conexión de red, datos de prueba

### Entorno Oficina (`ENVIRONMENT=oficina`)
- **Bases de datos**: Rutas de red `\\servidor\aplicaciones\...`
- **Archivos CSS**: Rutas de red corporativas
- **SMTP**: Servidor corporativo (10.73.54.85:25)
- **Uso**: Producción, datos reales, integración completa
- **Requisitos**: Acceso a red corporativa, permisos ODBC

### Variables de Entorno Completas

**⚠️ IMPORTANTE**: Nunca incluir contraseñas reales en documentación. Usar el archivo `.env` para valores sensibles.

#### Configuración General
```bash
ENVIRONMENT=local|oficina          # Seleccionar entorno
DB_PASSWORD=***                    # Contraseña bases datos (configurar en .env)
DEFAULT_RECIPIENT=email@empresa.com # Destinatario notificaciones
LOG_LEVEL=INFO|DEBUG|ERROR         # Nivel de logging
```

#### Bases de Datos - Entorno LOCAL
```bash
LOCAL_DB_AGEDYS=dbs-locales/AGEDYS_DATOS.accdb
LOCAL_DB_EXPEDIENTES=dbs-locales/Expedientes_datos.accdb
LOCAL_DB_SOLICITUDES_HPS=dbs-locales/Solicitudes_HPS_datos.accdb
LOCAL_DB_BRASS=dbs-locales/Gestion_Brass_Gestion_Datos.accdb
LOCAL_DB_TAREAS=dbs-locales/Tareas_datos1.accdb
LOCAL_DB_CORREOS=dbs-locales/correos_datos.accdb
LOCAL_DB_RIESGOS=dbs-locales/Gestion_Riesgos_Datos.accdb
LOCAL_DB_HPST=dbs-locales/HPST.accdb
LOCAL_DB_REGISTRO_ENT_SALIDA_DATOS=dbs-locales/Registro_Ent_Salida_Datos.accdb
LOCAL_DB_AGEDO20_DATOS=dbs-locales/AGEDO20_Datos.accdb
LOCAL_DB_REGISTRO_DATOS=dbs-locales/Registro_Datos.accdb
LOCAL_CSS_FILE=herramientas/CSS.txt
```

#### Bases de Datos - Entorno OFICINA
```bash
OFFICE_DB_AGEDYS=\\datoste\Aplicaciones_dys\Aplicaciones PpD\Proyectos\AGEDYS_DATOS.accdb
OFFICE_DB_EXPEDIENTES=\\datoste\Aplicaciones_dys\Aplicaciones PpD\EXPEDIENTES\Expedientes_datos.accdb
OFFICE_DB_SOLICITUDES_HPS=\\datoste\Aplicaciones_dys\Aplicaciones PpD\SOLICITUDES HPS\Solicitudes_HPS_datos.accdb
OFFICE_DB_BRASS=\\datoste\aplicaciones_dys\Aplicaciones PpD\BRASS\Gestion_Brass_Gestion_Datos.accdb
OFFICE_DB_TAREAS=\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb
OFFICE_DB_CORREOS=\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\correos_datos.accdb
OFFICE_DB_RIESGOS=\\datoste\Aplicaciones_dys\Aplicaciones PpD\GESTION RIESGOS\Gestion_Riesgos_Datos.accdb
OFFICE_DB_HPST=\\datoste\Aplicaciones_dys\Aplicaciones PpD\HPS\HPST.accdb
OFFICE_DB_REGISTRO_ENT_SALIDA_DATOS=\\datoste\aplicaciones_dys\Aplicaciones PpD\REGISTROS\Registro_Ent_Salida_Datos.accdb
OFFICE_DB_AGEDO20_DATOS=\\datoste\aplicaciones_Dys\Aplicaciones PpD\AGEDO\AGEDO20_Datos.accdb
OFFICE_DB_REGISTRO_DATOS=\\datoste\Aplicaciones_dys\Aplicaciones PpD\REGISTROS\Registro_Datos.accdb
OFFICE_CSS_FILE=\\datoste\Aplicaciones_dys\Aplicaciones PpD\CSS.txt
```

#### Configuración SMTP - Entorno LOCAL
```bash
LOCAL_SMTP_SERVER=localhost        # MailHog local
LOCAL_SMTP_PORT=1025              # Puerto MailHog
LOCAL_SMTP_USER=test@example.com  # Email de prueba
LOCAL_SMTP_PASSWORD=              # Sin contraseña
LOCAL_SMTP_TLS=false              # Sin TLS
```

#### Configuración SMTP - Entorno OFICINA
```bash
OFFICE_SMTP_SERVER=10.73.54.85    # Servidor SMTP oficina
OFFICE_SMTP_PORT=25               # Puerto SMTP (sin autenticación)
OFFICE_SMTP_USER=                 # Sin usuario
OFFICE_SMTP_PASSWORD=             # Sin contraseña
OFFICE_SMTP_TLS=false             # Sin TLS
```

#### IDs de Aplicaciones
```bash
APP_ID_AGEDYS=3
APP_ID_BRASS=6
APP_ID_RIESGOS=5
APP_ID_NOCONFORMIDADES=8
APP_ID_EXPEDIENTES=19
APP_ID_HPST=17
APP_ID_REGISTRO_ENT_SALIDA_DATOS=10
APP_ID_AGEDO20_DATOS=4
```

#### Configuración del Master Runner
```bash
# Tiempos de espera entre ciclos completos (en minutos)
MASTER_CYCLE_LABORABLE_DIA=5      # Día laborable - horario diurno
MASTER_CYCLE_LABORABLE_NOCHE=60   # Día laborable - horario nocturno
MASTER_CYCLE_NO_LABORABLE_DIA=60  # Fin de semana - horario diurno
MASTER_CYCLE_NO_LABORABLE_NOCHE=120 # Fin de semana - horario nocturno

# Timeout para scripts individuales (en segundos)
MASTER_SCRIPT_TIMEOUT=1800        # 30 minutos máximo por script

# Archivos de configuración
MASTER_FESTIVOS_FILE=herramientas/Festivos.txt
MASTER_LOG_LEVEL=INFO
MASTER_LOG_FILE=logs/run_master.log
MASTER_STATUS_FILE=logs/run_master_status.json
```

### 📧 Configuración SMTP

El sistema soporta dos configuraciones SMTP:

**Entorno Local (Desarrollo):**
- Servidor: `localhost:1025` (MailHog)
- Sin autenticación
- Emails capturados para testing

**Entorno Oficina (Producción):**
- Servidor: `10.73.54.85:25`
- Sin autenticación (compatible con VBS original)
- Envío real de emails

**Archivos relacionados:**
- `examples/smtp_config_demo.py` - Demo de configuración
- `docs/smtp_config_changes.md` - Documentación de cambios

## 📊 Estado de Cobertura de Tests

### Resumen General
- **Total de tests**: 289 tests
- **Cobertura global**: 82%
- **Tests unitarios**: 243 tests
- **Tests de integración**: 46 tests

### Cobertura por Módulo
| Módulo | Cobertura | Tests |
|--------|-----------|-------|
| `src/common/config.py` | 88% | ✅ |
| `src/common/database.py` | 55% | ✅ |
| `src/common/task_registry.py` | 64% | ✅ |
| `src/common/notifications.py` | 100% | ✅ |
| `src/common/utils.py` | 49% | ✅ |
| `src/email_services/email_manager.py` | 91% | ✅ |
| `src/expedientes/expedientes_manager.py` | 98% | ✅ |
| `src/riesgos/riesgos_manager.py` | 90% | ✅ |

### Comandos de Testing
```bash
# Ejecutar todos los tests principales
python -m pytest tests/unit/ tests/integration/ -v

# Generar reporte de cobertura HTML
python -m pytest --cov=src --cov-report=html

# Ver reporte de cobertura
# Abrir htmlcov/index.html en navegador

# Ejecutar tests específicos
python scripts/run_tests.py
```

## 🚀 Guía Rápida para Desarrolladores

**¿Acabas de abrir este proyecto en un nuevo ordenador?** Esta guía te llevará desde cero hasta tener un entorno de desarrollo completamente funcional.

### ✅ Prerrequisitos del Sistema

Antes de comenzar, asegúrate de tener instalado:

1. **Python 3.8 o superior**
   ```powershell
   # Verificar instalación
   python --version
   
   # Si no está instalado, descargar desde: https://python.org
   ```

2. **Node.js (para MCPs de TRAE)**
   ```powershell
   # Verificar instalación
   node --version
   npm --version
   
   # Si no está instalado, descargar desde: https://nodejs.org
   ```

3. **Docker (para SMTP local)**
   ```powershell
   # Verificar instalación
   docker --version
   
   # Si no está instalado, descargar Docker Desktop desde: https://docker.com
   ```

4. **Microsoft Access Database Engine** (para conectividad ODBC)
   - Descargar desde Microsoft: "Microsoft Access Database Engine 2016 Redistributable"

### 🛠️ Configuración Completa del Entorno

#### Paso 1: Clonar y Preparar el Proyecto

```powershell
# Clonar el repositorio
git clone <repo-url>
cd scripts-python

# Crear entorno virtual (solo la primera vez)
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Verificar que el entorno virtual está activo (debe aparecer "(venv)" en el prompt)
```

**💡 Importante sobre el Entorno Virtual:**
- **Primera vez**: Crear con `python -m venv venv`
- **Cada sesión**: Activar con `.\venv\Scripts\Activate.ps1`
- **Verificar activación**: Debe aparecer `(venv)` al inicio del prompt
- **Desactivar**: Ejecutar `deactivate` cuando termines

**Si tienes problemas de permisos en PowerShell:**
```powershell
# Permitir ejecución de scripts (solo una vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego activar normalmente
.\venv\Scripts\Activate.ps1
```

#### Paso 2: Configurar Variables de Entorno

```powershell
# Copiar el archivo de ejemplo
copy config\.env.example .env

# Editar .env con tus configuraciones específicas
# - Cambiar DB_PASSWORD por la contraseña real
# - Ajustar rutas de red para entorno oficina
# - Configurar email de destinatario
notepad .env
```

#### Paso 3: Instalar Dependencias

```powershell
# ENTORNO OFICINA (con proxy)
# Instalar dependencias usando proxy corporativo
pip install -r requirements.txt --proxy http://185.46.212.88:80

# ENTORNO CASA (sin proxy)
# Instalar dependencias directamente (forzar sin proxy aunque esté en variables de entorno)
pip install -r requirements.txt --proxy ""

# Verificar instalación
pip list
```

**💡 Nota sobre entornos:**
- **Oficina**: Usar el comando con `--proxy http://185.46.212.88:80`
- **Casa**: Usar el comando con `--proxy ""` para forzar sin proxy (incluso si está configurado en variables de entorno)
- Si tienes dudas sobre qué entorno usar, prueba primero con `--proxy ""`. Si falla, usa el proxy corporativo.

#### Paso 4: Configurar SMTP Local con Docker

```powershell
# Ejecutar MailHog para desarrollo local
docker run -d -p 1025:1025 -p 8025:8025 --name mailhog mailhog/mailhog

# Verificar que está funcionando
docker ps

# Acceder a la interfaz web: http://localhost:8025
```

**💡 Configuración SMTP Local en .env:**
```bash
LOCAL_SMTP_SERVER=localhost
LOCAL_SMTP_PORT=1025
LOCAL_SMTP_USER=
LOCAL_SMTP_PASSWORD=
LOCAL_SMTP_TLS=false
```

#### Paso 5: Migrar Bases de Datos a Local

```powershell
# Verificar conectividad de red (ejecutar desde red de oficina o VPN)
python tools/setup_local_environment.py --check-network

# Migrar todas las bases de datos
python tools/setup_local_environment.py

# Verificar que las bases locales se crearon correctamente
dir dbs-locales\
```

#### Paso 6: Verificar Configuración

```powershell
# Ejecutar tests para verificar que todo funciona
python scripts/run_tests.py

# Probar el panel de control web
python server.py
# Abrir: http://localhost:8080

# Probar envío de email de prueba (opcional)
python examples/smtp_config_demo.py
```

### 🎯 Comandos de Verificación Rápida

```powershell
# IMPORTANTE: Asegúrate de que el entorno virtual esté activo antes de ejecutar estos comandos
# Debe aparecer (venv) al inicio del prompt. Si no, ejecuta: .\venv\Scripts\Activate.ps1

# Verificar entorno completo
python --version                                    # Python instalado
node --version                                      # Node.js instalado  
docker --version                                    # Docker instalado
python tools/setup_local_environment.py --check-network  # Conectividad red
docker ps | findstr mailhog                        # MailHog funcionando
python -c "import pyodbc; print('ODBC OK')"       # Driver Access instalado

# Verificar que el entorno virtual está activo
python -c "import sys; print('Entorno virtual activo:' if 'venv' in sys.executable else 'Entorno virtual NO activo')"
```

### ⚠️ Solución de Problemas Comunes

**Error de conectividad de red:**
- Asegúrate de estar conectado a la red de oficina o VPN
- Verifica las rutas de red en el archivo `.env`

**Error de ODBC:**
- Instala Microsoft Access Database Engine 2016 Redistributable
- Reinicia PowerShell después de la instalación

**MailHog no funciona:**
```powershell
# Detener y reiniciar MailHog
docker stop mailhog
docker rm mailhog
docker run -d -p 1025:1025 -p 8025:8025 --name mailhog mailhog/mailhog
```

**Problemas con entorno virtual:**
```powershell
# Si no se activa correctamente (problema de permisos)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1

# Si el entorno virtual no existe, crearlo primero
python -m venv venv
.\venv\Scripts\Activate.ps1

# Verificar que está activo (debe mostrar "Entorno virtual activo:")
python -c "import sys; print('Entorno virtual activo:' if 'venv' in sys.executable else 'Entorno virtual NO activo')"

# Para desactivar el entorno virtual
deactivate
```

**Recordatorio importante:**
- **Siempre activa el entorno virtual** antes de trabajar: `.\venv\Scripts\Activate.ps1`
- **Cada nueva sesión de PowerShell** requiere activar el entorno virtual
- **Verifica que está activo** viendo `(venv)` en el prompt antes de ejecutar comandos Python

---

## Instalación (Método Tradicional)

1. **Clonar el repositorio y navegar al directorio**
   ```bash
   git clone <repo-url>
   cd scripts-python
   ```

2. **Crear y activar entorno virtual de Python (recomendado)**
   ```bash
   # Crear entorno virtual
   python -m venv venv
   
   # Activar entorno virtual
   # En Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   
   # En Windows (CMD):
   venv\Scripts\activate.bat
   
   # En Linux/macOS:
   source venv/bin/activate
   ```
   
   **💡 Nota**: Una vez activado el entorno virtual, verás `(venv)` al inicio de tu línea de comandos. Para desactivar el entorno virtual, simplemente ejecuta `deactivate`.

3. **Configurar variables de entorno**
   ```bash
   # Copiar el archivo de ejemplo desde la raíz
   cp .env.example .env
   
   # Editar .env con tus configuraciones específicas
   # - Cambiar DB_PASSWORD por la contraseña real
   # - Ajustar rutas de red para entorno oficina
   # - Configurar email de destinatario
   ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurar entorno local (opcional)**
   ```bash
   # Ejecutar herramienta de configuración
   python tools/setup_local_environment.py
   ```

6. **Instalar driver ODBC para Access** (si no está instalado)
   - Descargar Microsoft Access Database Engine

## Uso

### 🚀 Ejecución del Script Maestro (Recomendado)

**El script maestro es la forma principal de ejecutar el sistema en producción:**

```bash
# Ejecutar el script maestro (daemon de producción)
python scripts/run_master.py

# Ejecutar con modo verbose para debugging detallado
python scripts/run_master.py --verbose
python scripts/run_master.py -v

# Ver ayuda y opciones disponibles
python scripts/run_master.py --help
```

**Características del Master Runner:**
- 🔄 **Ejecución continua** con ciclos automáticos
- ⏰ **Tareas diarias**: Ejecutadas una vez por día laborable después de las 7 AM
- 📧 **Tareas continuas**: Correos y tareas ejecutados en cada ciclo
- 📅 **Respeta festivos** definidos en `herramientas/Festivos.txt`
- 🕐 **Ajuste automático** de tiempos según horario y tipo de día
- 📊 **Logs detallados** en `logs/run_master.log`
- 📈 **Archivo de estado** en `logs/run_master_status.json`
- 🛑 **Parada limpia** con Ctrl+C
- 🔍 **Modo verbose** para debugging y monitoreo detallado

### 🌐 Panel de Control Web (Alternativo)
```bash
# Iniciar servidor web del panel de control
python server.py

# Abrir navegador en: http://localhost:8080
```

**Características del Panel:**
- 🎛️ Interfaz gráfica para ejecutar módulos
- 🧪 Ejecución de tests con resultados en tiempo real
- 📊 Monitoreo del estado del sistema
- 🔄 Soporte multi-entorno (Local/Oficina)
- 📝 Consola integrada con logs detallados

### 🔧 Línea de Comandos (Desarrollo)

**Ejecutar Módulos Individuales:**
```bash
# AGEDYS - Gestión de facturas y visados técnicos
python scripts/run_agedys.py                    # Ejecución normal (verifica horarios)
python scripts/run_agedys.py --force            # Fuerza ejecución independientemente del horario
python scripts/run_agedys.py --dry-run          # Simula ejecución sin enviar emails

# BRASS - Gestión de tareas BRASS
python scripts/run_brass.py                     # Ejecución normal
python scripts/run_brass.py --force             # Fuerza ejecución
python scripts/run_brass.py --dry-run           # Modo simulación

# Expedientes - Gestión de expedientes
python scripts/run_expedientes.py               # Ejecución normal
python scripts/run_expedientes.py --force       # Fuerza ejecución
python scripts/run_expedientes.py --dry-run     # Modo simulación

# No Conformidades - Gestión de no conformidades
python scripts/run_no_conformidades.py          # Ejecución normal
python scripts/run_no_conformidades.py --force  # Fuerza ejecución
python scripts/run_no_conformidades.py --dry-run # Modo simulación

# Riesgos - Gestión de riesgos empresariales
python scripts/run_riesgos.py                   # Ejecución normal
python scripts/run_riesgos.py --force           # Fuerza ejecución
python scripts/run_riesgos.py --dry-run         # Modo simulación

# Email Services - Servicio unificado de correo (remplaza correos y correo_tareas)

### Manejo de errores transitorios SMTP (Refactor 2025)
Los errores de conexión SMTP (p.ej. desconexión inesperada, `SMTPConnectError`, `ConnectionRefusedError`) ahora se consideran **transitorios** y no marcan el correo como fallido en la base de datos. El registro permanece pendiente para reintentos en futuros ciclos. Sólo errores definitivos (credenciales inválidas, destinatario rechazado, formato de mensaje inválido) marcan el correo como fallido. Esto incrementa la resiliencia ante caídas puntuales del servidor de correo.
python scripts/run_email_services.py            # Ejecución normal
python scripts/run_email_services.py --force    # (Reservado) Fuerza ejecución

# Tests
python scripts/run_tests.py
```

### 🛠️ Herramientas de Desarrollo

#### 🔧 Configuración del Entorno Local para Desarrollo

**El script `setup_local_environment.py` es una herramienta esencial para desarrolladores** que automatiza la configuración del entorno local de desarrollo:

```bash
# Proceso completo: copia bases de datos + actualiza vínculos
python tools/setup_local_environment.py

# Solo actualizar vínculos (si ya tienes las bases locales)
python tools/setup_local_environment.py --links-only

# Solo verificar conectividad de red y mostrar configuración
python tools/setup_local_environment.py --check-network

# Crear base de correos completamente vacía (solo estructura)
python tools/setup_local_environment.py --empty-correos
```

**🎯 Funcionalidades del Script:**

1. **Descubrimiento Automático**: Lee automáticamente las variables de entorno del `.env` para encontrar todas las bases de datos configuradas (pares `OFFICE_DB_*` y `LOCAL_DB_*`)

2. **Verificación de Red**: Comprueba que puedas acceder a las ubicaciones de red de oficina antes de intentar copiar

3. **Copia Inteligente de Bases de Datos**:
   - **Bases normales**: Copia completa desde oficina a local
   - **Base de correos**: Modo ligero (solo últimos 5 registros para desarrollo)
   - **Base de correos vacía**: Opción `--empty-correos` para crear solo la estructura sin registros
   - **Manejo de contraseñas**: Crea bases locales con la misma contraseña que las remotas

4. **Actualización de Vínculos**: Actualiza automáticamente todas las tablas vinculadas para que apunten a las bases de datos locales

5. **Logging Detallado**: Genera un log completo del proceso en `logs/setup_local_environment.log` (directorio de logs central). Si usas stack Grafana/Loki, puedes desactivar este archivo estableciendo la variable de entorno `SETUP_LOCAL_FILE_LOG=0` y capturando stdout.

**📋 Casos de Uso Típicos:**

```bash
# Primer setup en un nuevo entorno de desarrollo
python tools/setup_local_environment.py --check-network  # Verificar configuración
python tools/setup_local_environment.py                  # Setup completo

# Actualizar solo vínculos después de cambios en .env
python tools/setup_local_environment.py --links-only

# Verificar problemas de conectividad
python tools/setup_local_environment.py --check-network

# Crear base de correos vacía para desarrollo sin datos
python tools/setup_local_environment.py --empty-correos
```

**⚠️ Importante para Desarrolladores:**
- **Ejecutar desde la red de oficina** o con VPN para acceder a las bases remotas
- **Verificar el archivo `.env`** antes de ejecutar el script
- **Usar `--check-network`** para diagnosticar problemas de conectividad
- **El script es seguro**: no modifica las bases de datos de oficina, solo las copia

#### 📊 Herramientas de Cobertura y Testing

**Generación de Reportes de Cobertura:**
```bash
# Generar reporte de cobertura UNITARIOS (rápido, 0% cobertura aparente)
python tools/generate_coverage_report.py

# Generar reporte de cobertura COMPLETO (unitarios + integración, cobertura real)
python tools/generate_full_coverage_report.py

# Diagnosticar problemas de coverage en Windows
python tools/check_coverage_dependencies.py
```

**🔧 Características de las Herramientas de Cobertura:**

- **`generate_coverage_report.py`** (Solo tests unitarios):
  - ⚡ **Ejecución rápida** (solo tests unitarios con mocks)
  - 📊 **0% cobertura aparente** (normal debido al uso extensivo de mocks)
  - ✅ **Compatibilidad Windows mejorada** con `sys.executable` y `shell=True`
  - 🛡️ **Manejo robusto de errores** con diagnóstico detallado
  - 🌐 **Apertura automática** del reporte HTML en navegador

- **`generate_full_coverage_report.py`** (Tests completos):
  - 🔍 **Cobertura REAL** del código (unitarios + integración)
  - 📈 **~35% cobertura** con interacción real con bases de datos
  - ⚠️ **Requiere bases de datos locales** configuradas
  - 🕐 **Ejecución más lenta** (~1 minuto)
  - 📊 **Reportes múltiples**: HTML interactivo, XML para CI/CD, y resumen en consola

- **`check_coverage_dependencies.py`**: 
  - 🔍 **Diagnóstico completo** del entorno Python y dependencias
  - ✅ **Verificación de instalación** de `coverage` y `pytest`
  - 📁 **Análisis de estructura** del proyecto
  - 🚀 **Instalación automática** de dependencias faltantes
  - 🧪 **Prueba funcional** de coverage con archivo de ejemplo

**💡 Solución de Problemas Comunes:**

```bash
# Si obtienes 0% de cobertura:
python tools/generate_full_coverage_report.py  # Usar reporte completo para cobertura real

# Si obtienes PermissionError en Windows:
python tools/check_coverage_dependencies.py  # Diagnosticar el problema

# Si coverage no se encuentra:
pip install coverage pytest  # Instalar dependencias

# Si hay problemas con el entorno virtual:
.\venv\Scripts\Activate.ps1  # Activar entorno virtual
python tools/generate_coverage_report.py  # Intentar de nuevo
```

#### 🛠️ Otras Herramientas de Desarrollo

**Configuración y Mantenimiento:**
```bash
# Ejecución continua de tests
python tools/continuous_runner.py

# Verificar estado de correos
python tools/check_email_status.py

# Verificar estructura de bases de datos
python tools/check_email_structure.py
```

## Seguridad

### Protección de Información Sensible
El sistema implementa medidas de seguridad para proteger información sensible como contraseñas de base de datos:

```python
from src.common.utils import hide_password_in_connection_string

# Ejemplo de uso
connection_string = "Server=server;Database=db;PWD=secret123"
safe_string = hide_password_in_connection_string(connection_string)
print(safe_string)  # Output: "Server=server;Database=db;PWD=***"
```

### Características de Seguridad
- **Enmascaramiento automático** de contraseñas en logs
- **Soporte para múltiples formatos**: `PWD=`, `Password=` (case-insensitive)
- **Preservación de estructura** de cadenas de conexión
- **Tests de seguridad** automatizados

### Validación de Seguridad
```bash
# Ejecutar tests de seguridad
pytest tests/test_utils_security.py -v
```

## Testing

### 🧪 Ejecución de Tests

**Ejecutar Tests:**
```bash
# Ejecutar todos los tests
pytest

# Ejecutar solo tests unitarios
pytest tests/unit/ -v

# Ejecutar solo tests de integración (requieren BD real)
pytest tests/integration/ -v -m integration

# Ejecutar tests específicos
pytest tests/unit/test_database.py -v

# Ejecutar tests manuales de desarrollo
pytest tests/manual/ -v
```

### Tipos de Tests

#### Tests de Conectividad
```bash
# Tests de integración de base de datos
pytest tests/test_database_connectivity.py -v

# Tests específicos por base de datos
pytest tests/test_database_connectivity.py::test_brass_database_connection -v
pytest tests/test_database_connectivity.py::test_tareas_database_connection -v
pytest tests/test_database_connectivity.py::test_correos_database_connection -v
```

#### Tests Manuales de Desarrollo
```bash
# Tests de conectividad COM Access
pytest tests/manual/test_com_access.py -v

# Tests de verificación de red
pytest tests/manual/test_network_verification.py -v

# Tests de reenlace de tablas
pytest tests/manual/test_relink_tables.py -v

# Tests de funciones de usuario
pytest tests/manual/test_user_functions.py -v
```

#### Tests de Seguridad
```bash
# Tests de enmascaramiento de contraseñas
pytest tests/test_utils_security.py -v
```

#### Tests Completos
```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=src

# Tests con reporte detallado
pytest -v --tb=short
```

### 📊 Coverage (Cobertura de Código)

**Generar Reportes de Cobertura:**
```bash
# Método rápido - Solo tests unitarios (0% cobertura aparente)
python tools/generate_coverage_report.py

# Método completo - Tests unitarios + integración (cobertura real ~35%)
python tools/generate_full_coverage_report.py

# Diagnosticar problemas de coverage
python tools/check_coverage_dependencies.py

# Método manual (unitarios)
coverage run --source=src -m pytest tests/unit/ -v
coverage html
start htmlcov\index.html

# Método manual (completo)
coverage run --source=src -m pytest tests/integration/ -v
coverage html
start htmlcov\index.html
```

**🔧 Herramientas de Cobertura Mejoradas:**

- **Compatibilidad Windows**: Scripts actualizados para resolver `PermissionError` comunes
- **Dos tipos de reportes**: Unitarios (rápido, 0% aparente) vs Completo (real, ~35%)
- **Diagnóstico automático**: Verificación de entorno y dependencias
- **Manejo robusto de errores**: Información detallada en caso de fallos
- **Reportes múltiples**: HTML, XML y consola en una sola ejecución

**Estado Actual:**
- **Total**: 494 tests ejecutándose correctamente
- **Cobertura Unitarios**: 0% (normal con mocks extensivos)
- **Cobertura Completa**: 35% (tests de integración + unitarios)
- **Reportes HTML**: Disponibles en `htmlcov/index.html`

**Archivos de Coverage:**
- `.coveragerc` - Configuración de coverage.py
- `htmlcov/` - Reportes HTML interactivos
- `tools/generate_coverage_report.py` - Script unitarios (mejorado para Windows)
- `tools/generate_full_coverage_report.py` - Script completo (nueva herramienta)
- `tools/check_coverage_dependencies.py` - Herramienta de diagnóstico

**Interpretación de Reportes:**
- 🟢 **Verde**: Líneas cubiertas por tests
- 🔴 **Rojo**: Líneas sin cobertura (necesitan tests)
- 🟡 **Amarillo**: Cobertura parcial
- ⚪ **Blanco**: Líneas no ejecutables

## 📊 Monitoreo y Logging

### Arquitectura de Logging con Loki y Grafana

El sistema implementa una arquitectura moderna de logging centralizado utilizando **Loki** como agregador de logs y **Grafana** como interfaz de visualización y análisis.

#### Componentes de la Arquitectura

```
Aplicación Python → Loki → Grafana
     ↓
  Logs Locales
```

- **Aplicación Python**: Genera logs estructurados con metadatos contextuales
- **Loki**: Almacena y indexa los logs de forma eficiente
- **Grafana**: Proporciona dashboards y alertas para monitoreo en tiempo real
- **Logs Locales**: Respaldo local en archivos para debugging

#### Características del Sistema de Logging

- **Logging Estructurado**: Metadatos contextuales (tags dinámicas) para filtrado avanzado
- **Envío No Bloqueante**: Utiliza `LokiQueueHandler` para no afectar el rendimiento
- **Multi-destino**: Archivo local, consola y Loki simultáneamente
- **Etiquetas Dinámicas**: Contexto específico por operación (`report_type`, `outcome`, `tecnico`)
- **Manejo de Errores**: `exc_info=True` para trazas completas de excepciones

### Iniciar los Servicios de Monitoreo

Para iniciar la infraestructura de monitoreo, ejecuta:

```bash
# Iniciar servicios en segundo plano
docker-compose up -d

# Verificar estado de los servicios
docker-compose ps

# Ver logs de los servicios
docker-compose logs -f loki
docker-compose logs -f grafana
```

### Acceso a Grafana

Una vez iniciados los servicios, puedes acceder a Grafana:

- **URL**: http://localhost:3000
- **Credenciales por defecto**:
  - Usuario: `admin`
  - Contraseña: `admin` (se solicitará cambio en el primer acceso)

#### Configuración Automática

La fuente de datos Loki se configura automáticamente al iniciar Grafana gracias al archivo de provisioning:
- **Nombre**: Loki
- **Tipo**: loki
- **URL**: http://loki:3100
- **Acceso**: proxy

### Configuración de la Aplicación Python

Para que la aplicación Python envíe logs a Loki, configura la variable de entorno:

```bash
# En tu archivo .env
LOKI_URL=http://localhost:3100
```

La aplicación automáticamente:
1. Detecta la variable `LOKI_URL`
2. Configura el `LokiQueueHandler`
3. Envía logs a `http://localhost:3100/loki/api/v1/push`

#### Ejemplo de Uso en Código

```python
import logging
from src.common.utils import setup_logging

# Configurar logging con Loki
logger = setup_logging("mi_modulo", "INFO")

# Log con metadatos contextuales
logger.info("Operación completada", extra={
    'report_type': 'calidad',
    'outcome': 'success',
    'tecnico': 'juan.perez'
})

# Log de error con traza completa
try:
    # operación que puede fallar
    pass
except Exception as e:
    logger.error("Error en operación", extra={
        'report_type': 'tecnico',
        'outcome': 'error'
    }, exc_info=True)
```

### Consultas y Filtros en Grafana

Ejemplos de consultas LogQL para filtrar logs:

```logql
# Todos los logs de un módulo específico
{job="scripts-python"} |= "no_conformidades"

# Logs de error con contexto específico
{job="scripts-python"} | json | outcome="error"

# Logs por tipo de reporte
{job="scripts-python"} | json | report_type="calidad"

# Logs de un técnico específico
{job="scripts-python"} | json | tecnico="juan.perez"
```

### Estructura de Archivos de Monitoreo

```
scripts-python/
├── docker-compose.yml                    # Configuración servicios
├── loki/
│   └── loki-config.yml                  # Configuración Loki
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── loki-datasource.yml      # Fuente de datos automática
└── logs/                                # Logs locales de respaldo
```

### Comandos Útiles

```bash
# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Ver logs en tiempo real
docker-compose logs -f

# Limpiar volúmenes (⚠️ elimina datos)
docker-compose down -v
```

## Variables de Entorno Principales

**⚠️ SEGURIDAD**: Las contraseñas y datos sensibles deben configurarse únicamente en el archivo `.env`, nunca en documentación.

| Variable | Descripción | Ejemplo Seguro |
|----------|-------------|----------------|
| `ENVIRONMENT` | Entorno (local/oficina) | `local` |
| `DB_PASSWORD` | Contraseña bases de datos | `***` (configurar en .env) |
| `LOCAL_DB_BRASS` | Ruta local BD BRASS | `dbs-locales/Brass.accdb` |
| `OFFICE_DB_BRASS` | Ruta oficina BD BRASS | `\\servidor\aplicaciones\Brass.accdb` |
| `DEFAULT_RECIPIENT` | Correo por defecto | `user@domain.com` |
| `OFFICE_SMTP_SERVER` | Servidor SMTP oficina | `10.73.54.85` |
| `OFFICE_SMTP_PORT` | Puerto SMTP oficina | `25` |
| `LOCAL_SMTP_SERVER` | Servidor SMTP local | `localhost` |
| `LOCAL_SMTP_PORT` | Puerto SMTP local | `1025` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `MASTER_CYCLE_LABORABLE_DIA` | Ciclo día laborable (min) | `5` |
| `MASTER_CYCLE_LABORABLE_NOCHE` | Ciclo noche laborable (min) | `60` |
| `MASTER_CYCLE_NO_LABORABLE_DIA` | Ciclo día no laborable (min) | `60` |
| `MASTER_CYCLE_NO_LABORABLE_NOCHE` | Ciclo noche no laborable (min) | `120` |
| `MASTER_SCRIPT_TIMEOUT` | Timeout scripts (seg) | `1800` |

## Arquitectura

### Arquitectura de Tareas

Esta sección describe cómo se estructuran y colaboran los componentes que permiten ejecutar cada módulo de negocio de forma consistente, testeable y extensible.

#### 1. Componentes Principales

| Componente | Responsabilidad | Código típico |
|------------|-----------------|---------------|
| Script Runner (`scripts/run_x.py`) | Punto de entrada ejecutable: parsea argumentos CLI, inicializa logging y delega en la Task | `scripts/run_no_conformidades.py` |
| Task (`BaseTask`, `TareaDiaria`, `TareaContinua`) | Orquestación de la lógica: decide si ejecutar, encapsula medición, logging estructurado y control de errores | `src/no_conformidades/no_conformidades_task.py` |
| Manager | Lógica de dominio y acceso a datos (queries, composición de datos, generación de HTML) | `no_conformidades_manager.py` / `*_manager.py` |
| TaskRegistry | Registro central de instancias de tareas para el script maestro | `common/task_registry.py` |
| Master Runner (`run_master.py`) | Bucle continuo que consulta el `TaskRegistry` y lanza tareas según frecuencia / tipo | `scripts/run_master.py` |

Separar estas capas reduce acoplamiento: los runners quedan triviales, las Tasks son testeables aislando sus métodos de decisión y ejecución con mocks, y los Managers concentran la lógica SQL / dominio reutilizable.

#### 2. Flujo General (Runner Individual)

```
parse_args()
setup_logging()
with Task() as task:
   if args.force_flags:
      task.ejecutar_forzado(sub-selección)
   elif task.debe_ejecutarse():
      task.ejecutar()
   else:
      log("skip")
```

La Task maneja internamente:
1. Registro de inicio (`event=task_start`).
2. Llamada a `execute_specific_logic()` (implementación concreta).
3. Marcado de completitud (`marcar_como_completada()`) sólo si la ejecución fue efectiva.
4. Registro de fin (`event=task_end`, `exit_code`).
5. Captura y log estructurado de excepciones sin comprometer el proceso principal.

#### 3. Flujo General (Master Runner)

1. Crea / reutiliza instancia de `TaskRegistry`.
2. Obtiene listas: `get_daily_tasks()` y `get_continuous_tasks()`.
3. Para cada tarea diaria: evalúa `debe_ejecutarse()` (frecuencia + horario + festivos) antes de lanzar.
4. Para cada tarea continua: se ejecuta en cada ciclo.
5. Aplica timeouts y registra resultados agregados para observabilidad.

#### 4. Contrato Simplificado de una Task

| Método | Propósito |
|--------|-----------|
| `debe_ejecutarse()` | Decide si corresponde ejecutar (diarias) |
| `execute_specific_logic()` | Lógica principal; devuelve bool éxito |
| `marcar_como_completada()` | Actualiza estado persistente (última ejecución) |

Errores lanzados en `execute_specific_logic()` se capturan en el wrapper de `BaseTask` para asegurar logging uniforme y evitar caída del ciclo maestro.

#### 5. Caso Específico: `NoConformidadesTask`

La tarea combina dos sub-tareas independientes: Calidad y Técnica. Para maximizar testabilidad se dividió en métodos discretos:

| Método | Rol |
|--------|-----|
| `debe_ejecutar_tarea_calidad()` | Evalúa si hay NC de calidad que justifiquen envío |
| `debe_ejecutar_tarea_tecnica()` | Evalúa si hay AR técnicas pendientes |
| `ejecutar_logica_calidad()` | Construye datos + HTML y registra envío (usa `NoConformidadesManagerPure`) |
| `ejecutar_logica_tecnica()` | Agrega datos técnicos por usuario mediante `get_technical_report_data_for_user()` |
| `execute_specific_logic()` | Orquesta decisiones, ejecuta subtareas y consolida resultado (éxito parcial permitido) |

Características clave:
* Separación de decisión vs ejecución -> tests unitarios rápidos (mocks sobre cada rama).
* Agregación técnica: una sola llamada por técnico en vez de 3 queries separadas (eficiencia y menor riesgo de inconsistencia temporal).
* Tolerancia a fallos: excepción en una sub-tarea no detiene la otra; se reporta resultado combinado.
* Flags de forzado (`--force-calidad`, `--force-tecnica`, `--force-all`) saltan las evaluaciones de `debe_ejecutar_*`.

Secuencia simplificada (técnica + calidad):

```
execute_specific_logic():
  resultados = []
  if forzar_calidad or debe_ejecutar_tarea_calidad():
     try: resultados.append(ejecutar_logica_calidad())
     except Exception: log(error)
  if forzar_tecnica or debe_ejecutar_tarea_tecnica():
     try: resultados.append(ejecutar_logica_tecnica())
     except Exception: log(error)
  return any(resultados)  # éxito si al menos una rama hizo trabajo
```

#### 6. Beneficios de la Arquitectura de Tareas

| Beneficio | Explicación |
|-----------|-------------|
| Testabilidad | Métodos pequeños permiten mocks específicos y alta cobertura |
| Observabilidad | Eventos start/end homogéneos y exit codes previsibles |
| Evolutividad | Añadir una nueva Task sólo requiere implementarla y registrarla |
| Aislamiento de fallos | Una Task con error no compromete el ciclo maestro |
| Reutilización | Managers compartidos entre múltiples Tasks o runners futuros |
| Rendimiento | Reducción de queries duplicadas y posibilidad futura de caching |

#### 7. Próximos Mejoras Potenciales

* Persistir métricas (duración, número de registros procesados) para dashboards.
* Sistema de descubrimiento dinámico de Tasks (entry points / plugin folder).
* Instrumentación opcional (trazas / spans) para tareas de larga duración.
* Caching de resultados intermedios entre subtareas (cuando comparten dataset base).

---

### Módulos Comunes (`src/common/`)

- **config.py**: Gestión centralizada de configuración
- **database.py**: Abstracción para bases de datos Access con ODBC  
- (Eliminado) `database_adapter.py` sustituido por `AccessDatabase`
- **utils.py**: Utilidades compartidas (HTML, fechas, logging)

### Mejoras vs VBS Original

1. **Type Safety**: Type hints en lugar de Variant
2. **Resource Management**: Context managers vs manual cleanup
3. **Error Handling**: Excepciones específicas vs On Error Resume Next
4. **Testing**: Tests automatizados vs testing manual
5. **Configuration**: Variables de entorno vs hard-coding
