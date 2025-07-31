# Sistema de Gestión de Tareas - Migración de VBS a Python

Este proyecto es una migración del sistema legacy VBS a Python que implementa un **sistema de monitoreo continuo** para la gestión automatizada de tareas empresariales. El objetivo principal es ejecutar el script maestro `run_master.py` que funciona como un **daemon de producción** que monitorea y ejecuta automáticamente todos los módulos del sistema según horarios específicos.

## Migración de VBS a Python

Este proyecto representa la migración completa del sistema de automatización VBS legacy a Python moderno, manteniendo toda la funcionalidad original mientras se mejora la robustez, mantenibilidad y capacidades de testing.

### 🎯 Objetivos de la Migración
- **Modernización**: Migrar de VBS legacy a Python 3.11+
- **Robustez**: Implementar manejo de errores robusto y logging detallado
- **Testing**: Cobertura de tests >80% con tests unitarios, integración y funcionales
- **Mantenibilidad**: Código modular, documentado y siguiendo mejores prácticas
- **Configuración**: Sistema de configuración flexible multi-entorno
- **Monitoreo**: Herramientas de monitoreo y debugging avanzadas

### ✅ Estado de la Migración
- **AGEDYS**: ✅ Completamente migrado y funcional
- **BRASS**: ✅ Completamente migrado y funcional
- **Expedientes**: ✅ Completamente migrado y funcional
- **Correos**: ✅ Completamente migrado y funcional
- **Tareas**: ✅ Completamente migrado y funcional
- **No Conformidades**: ✅ Completamente migrado y funcional
- **Riesgos**: ✅ Completamente migrado y funcional
- **Script Maestro**: ✅ Completamente migrado y funcional con modo verbose

## 🎯 Objetivo Principal

El **script maestro (`run_master.py`)** es el corazón del sistema y reemplaza al legacy `script-continuo.vbs`. Funciona como un **servicio continuo** que:

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
6. **Correos** (`run_correos.py`): Sistema de envío de correos
7. **Tareas** (`run_tareas.py`): Sistema de gestión de tareas

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

- [Estructura del Proyecto](#estructura-del-proyecto)
- [Características Implementadas](#características-implementadas)
- [Configuración de Entornos](#configuración-de-entornos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Testing](#testing)
- [Seguridad](#seguridad)
- [Variables de Entorno Principales](#variables-de-entorno-principales)
- [Arquitectura](#arquitectura)

## Estructura del Proyecto

```
scripts-python/
├── .env                          # Variables de entorno (local)
├── requirements.txt              # Dependencias Python
├── pyproject.toml               # Configuración de pytest y herramientas
├── .coveragerc                  # Configuración coverage.py
├── README.md                    # Documentación principal
├── config/                      # Configuración del proyecto
│   └── .env.example            # Plantilla de variables de entorno
├── scripts/                     # Scripts principales de ejecución
│   ├── run_master.py           # Script maestro - daemon principal con modo verbose
│   ├── run_agedys.py           # Script para módulo AGEDYS
│   ├── run_brass.py            # Script principal para módulo BRASS
│   ├── run_expedientes.py      # Script para módulo expedientes
│   ├── run_correos.py          # Script para módulo correos
│   ├── run_tareas.py           # Script para módulo tareas
│   ├── run_no_conformidades.py # Script para no conformidades
│   └── run_riesgos.py          # Script para módulo de riesgos
├── tools/                       # Herramientas de desarrollo y utilidades
│   ├── setup_local_environment.py  # Configuración entorno local
│   ├── generate_coverage_report.py # Generador reportes de cobertura
│   ├── continuous_runner.py        # Ejecución continua de tests
│   ├── check_email_status.py       # Verificación estado emails
│   └── check_email_structure.py    # Verificación estructura emails
├── src/                         # Código fuente
│   ├── __init__.py
│   ├── common/                  # Utilidades compartidas
│   │   ├── __init__.py
│   │   ├── config.py           # Configuración multi-entorno
│   │   ├── database.py         # Capa abstracción bases datos Access
│   │   ├── database_adapter.py # Adaptador de bases de datos
│   │   ├── base_email_manager.py # Gestor base para emails
│   │   ├── html_report_generator.py # Generador reportes HTML
│   │   ├── logger.py           # Sistema de logging
│   │   ├── notifications.py    # Sistema de notificaciones
│   │   ├── user_adapter.py     # Adaptador de usuarios
│   │   └── utils.py           # Utilidades HTML, logging, fechas
│   ├── agedys/                 # Módulo AGEDYS (migrado)
│   │   ├── __init__.py
│   │   └── agedys_manager.py   # Gestor principal AGEDYS
│   ├── brass/                  # Módulo BRASS (migrado)
│   │   ├── __init__.py
│   │   └── brass_manager.py    # Gestor principal BRASS
│   ├── correos/                # Módulo de correos
│   │   ├── __init__.py
│   │   └── correos_manager.py  # Gestor de correos
│   ├── expedientes/            # Módulo de expedientes
│   │   ├── __init__.py
│   │   └── expedientes_manager.py # Gestor de expedientes
│   ├── no_conformidades/       # Módulo de no conformidades
│   │   ├── __init__.py
│   │   ├── no_conformidades_manager.py # Gestor principal
│   │   └── email_notifications.py     # Notificaciones email
│   ├── riesgos/                # Módulo de gestión de riesgos
│   │   ├── __init__.py
│   │   └── riesgos_manager.py  # Gestor de riesgos
│   └── tareas/                 # Módulo de gestión de tareas
│       ├── __init__.py
│       └── tareas_manager.py   # Gestor de tareas empresariales
├── tests/                      # Tests automatizados (cobertura >80%)
│   ├── __init__.py
│   ├── config.py              # Configuración de tests
│   ├── conftest.py            # Configuración global pytest
│   ├── data/                  # Datos de test
│   │   └── __init__.py
│   ├── fixtures/              # Datos y utilidades de prueba
│   │   ├── __init__.py
│   │   ├── create_demo_databases.py
│   │   ├── create_test_emails_demo.py
│   │   └── setup_smtp_local.py
│   ├── unit/                   # Tests unitarios por módulo
│   │   ├── __init__.py
│   │   ├── common/             # Tests módulos comunes
│   │   ├── agedys/             # Tests específicos AGEDYS
│   │   ├── brass/              # Tests específicos BRASS
│   │   ├── correos/            # Tests del módulo de correos
│   │   ├── expedientes/        # Tests del módulo de expedientes
│   │   ├── no_conformidades/   # Tests no conformidades
│   │   ├── riesgos/            # Tests del módulo de riesgos
│   │   └── tareas/             # Tests del módulo de tareas
│   ├── integration/            # Tests de integración
│   │   ├── __init__.py
│   │   ├── agedys/             # Integración del sistema AGEDYS
│   │   ├── brass/              # Integración del sistema brass
│   │   ├── correos/            # Integración del sistema de correos
│   │   ├── expedientes/        # Integración del sistema de expedientes
│   │   ├── no_conformidades/   # Integración no conformidades
│   │   ├── riesgos/            # Integración del sistema de riesgos
│   │   ├── tareas/             # Integración del sistema de tareas
│   │   └── database/           # Integración con bases de datos
│   ├── functional/             # Tests funcionales
│   │   ├── access_sync/        # Sincronización con Access
│   │   └── correos_workflows/  # Flujos completos de correos
│   └── manual/                 # Tests manuales esenciales
│       ├── test_agedys_manual.py       # Test manual AGEDYS
│       ├── test_env_config.py          # Test configuración entorno
│       ├── test_network_verification.py # Test verificación red
│       ├── test_smtp_riesgos.py        # Test SMTP riesgos
│       └── test_user_functions.py      # Test funciones usuario
├── templates/                  # Plantillas HTML
├── dbs-locales/               # Bases de datos locales
├── herramientas/              # Archivos de configuración
│   ├── CSS1.css               # Estilos CSS principales
│   └── Festivos.txt           # Archivo de días festivos
├── docs/                      # Documentación
│   ├── coverage_setup_summary.md # Resumen configuración coverage
│   ├── htmlcov_usage_guide.md     # Guía uso reportes HTML
│   ├── panel_control_guia.md      # Guía del panel de control
│   ├── smtp_config_changes.md     # Cambios configuración SMTP
│   ├── smtp_override_config.md    # Configuración override SMTP
│   ├── riesgos.md                 # Documentación módulo de riesgos
│   ├── migracion_riesgos.md       # Guía migración GestionRiesgos.vbs
│   └── NO_CONFORMIDADES.md        # Documentación no conformidades
├── examples/                    # Ejemplos y demos
│   ├── README.md               # Documentación de ejemplos
│   ├── database_connectivity_demo.py # Demo conectividad BD
│   ├── smtp_config_demo.py     # Demo configuración SMTP
│   ├── smtp_override_demo.py   # Demo override SMTP
│   └── ejemplo_riesgos.py      # Ejemplo uso módulo riesgos
├── legacy/                    # Sistema VBS original
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

### ✅ Módulos Migrados y Funcionales
- **AGEDYS**: Sistema completo de gestión de facturas y visados técnicos
- **BRASS**: Sistema completo de gestión de tareas BRASS
- **Expedientes**: Gestión de expedientes y documentación
- **Correos**: Sistema de envío y gestión de correos electrónicos
- **Tareas**: Sistema de gestión de tareas empresariales
- **No Conformidades**: Gestión de no conformidades y seguimiento
- **Riesgos**: Gestión completa de riesgos empresariales

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
- **Migración Completa**: Todos los sistemas VBS migrados a Python

## Configuración de Entornos

El sistema soporta dos entornos configurables mediante el archivo `.env` con **separación completa de configuraciones**:

### Configuración inicial
```bash
# Copiar plantilla de configuración
cp config/.env.example .env

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
- Sin autenticación (compatible con VBS legacy)
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
| `src/common/database_adapter.py` | 95% | ✅ |
| `src/common/notifications.py` | 100% | ✅ |
| `src/common/utils.py` | 49% | ✅ |
| `src/correos/correos_manager.py` | 91% | ✅ |
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

## Instalación

1. **Clonar el repositorio y navegar al directorio**
   ```bash
   git clone <repo-url>
   cd scripts-python
   ```

2. **Configurar variables de entorno**
   ```bash
   # Copiar el archivo de ejemplo desde config/
   cp config/.env.example .env
   
   # Editar .env con tus configuraciones específicas
   # - Cambiar DB_PASSWORD por la contraseña real
   # - Ajustar rutas de red para entorno oficina
   # - Configurar email de destinatario
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar entorno local (opcional)**
   ```bash
   # Ejecutar herramienta de configuración
   python tools/setup_local_environment.py
   ```

5. **Instalar driver ODBC para Access** (si no está instalado)
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

# Correos - Sistema de envío de correos
python scripts/run_correos.py                   # Ejecución normal
python scripts/run_correos.py --force           # Fuerza ejecución
python scripts/run_correos.py --dry-run         # Modo simulación

# Tareas - Sistema de gestión de tareas
python scripts/run_tareas.py                    # Ejecución normal
python scripts/run_tareas.py --force            # Fuerza ejecución
python scripts/run_tareas.py --dry-run          # Modo simulación

# Tests
python scripts/run_tests.py
```

### 🛠️ Herramientas de Desarrollo

**Configuración y Mantenimiento:**
```bash
# Configurar entorno local
python tools/setup_local_environment.py

# Generar reportes de cobertura
python tools/generate_coverage_report.py

# Ejecución continua de tests
python tools/continuous_runner.py
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
# Método rápido (recomendado)
python tools/generate_coverage_report.py

# Método manual
coverage run --source=src -m pytest tests/unit/ -v
coverage html
start htmlcov\index.html
```

**Estado Actual:**
- **Total**: 289 tests ejecutándose correctamente
- **Cobertura**: 82% del código fuente
- **Reportes HTML**: Disponibles en `htmlcov/index.html`

**Archivos de Coverage:**
- `.coveragerc` - Configuración de coverage.py
- `htmlcov/` - Reportes HTML interactivos
- `tools/generate_coverage_report.py` - Script automatizado

**Interpretación de Reportes:**
- 🟢 **Verde**: Líneas cubiertas por tests
- 🔴 **Rojo**: Líneas sin cobertura (necesitan tests)
- 🟡 **Amarillo**: Cobertura parcial
- ⚪ **Blanco**: Líneas no ejecutables

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

### Módulos Comunes (`src/common/`)

- **config.py**: Gestión centralizada de configuración
- **database.py**: Abstracción para bases de datos Access con ODBC  
- **database_adapter.py**: Adaptador de conexiones de base de datos
- **utils.py**: Utilidades compartidas (HTML, fechas, logging)

### Mejoras vs VBS Legacy

1. **Type Safety**: Type hints en lugar de Variant
2. **Resource Management**: Context managers vs manual cleanup
3. **Error Handling**: Excepciones específicas vs On Error Resume Next
4. **Testing**: Tests automatizados vs testing manual
5. **Configuration**: Variables de entorno vs hard-coding
