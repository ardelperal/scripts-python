# Sistema de Gestión de Tareas Empresariales

Sistema de **monitoreo continuo** para la gestión automatizada de tareas empresariales desarrollado en Python. El objetivo principal es ejecutar el script maestro `run_master.py` que funciona como un **daemon de producción** que monitorea y ejecuta automáticamente todos los módulos del sistema según horarios específicos.

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
7. **Correo Tareas** (`run_correo_tareas.py`): Sistema de gestión de correos que interactúa con la base de datos de tareas

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
│   ├── run_correo_tareas.py    # Script para módulo correo tareas
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
│   └── correo_tareas/          # Módulo de gestión de correos que interactúa con la base de datos de tareas
│       ├── __init__.py
│       └── correo_tareas_manager.py   # Gestor de correos para tareas empresariales
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
│   │   └── correo_tareas/      # Tests del módulo de correo tareas
│   ├── integration/            # Tests de integración
│   │   ├── __init__.py
│   │   ├── agedys/             # Integración del sistema AGEDYS
│   │   ├── brass/              # Integración del sistema brass
│   │   ├── correos/            # Integración del sistema de correos
│   │   ├── expedientes/        # Integración del sistema de expedientes
│   │   ├── no_conformidades/   # Integración no conformidades
│   │   ├── riesgos/            # Integración del sistema de riesgos
│   │   ├── correo_tareas/      # Integración del sistema de correo tareas
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

### ✅ Módulos del Sistema
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
- **Sistema Modular**: Arquitectura modular y extensible

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
# Instalar dependencias de Python
pip install -r requirements.txt

# Verificar instalación
pip list
```

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
   # Copiar el archivo de ejemplo desde config/
   cp config/.env.example .env
   
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

# Correos - Sistema de envío de correos
python scripts/run_correos.py                   # Ejecución normal
python scripts/run_correos.py --force           # Fuerza ejecución
python scripts/run_correos.py --dry-run         # Modo simulación

# Tareas - Sistema de gestión de tareas
python scripts/run_correo_tareas.py                    # Ejecución normal
python scripts/run_correo_tareas.py --force            # Fuerza ejecución
python scripts/run_correo_tareas.py --dry-run          # Modo simulación

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
```

**🎯 Funcionalidades del Script:**

1. **Descubrimiento Automático**: Lee automáticamente las variables de entorno del `.env` para encontrar todas las bases de datos configuradas (pares `OFFICE_DB_*` y `LOCAL_DB_*`)

2. **Verificación de Red**: Comprueba que puedas acceder a las ubicaciones de red de oficina antes de intentar copiar

3. **Copia Inteligente de Bases de Datos**:
   - **Bases normales**: Copia completa desde oficina a local
   - **Base de correos**: Modo ligero (solo últimos 5 registros para desarrollo)
   - **Manejo de contraseñas**: Crea bases locales con la misma contraseña que las remotas

4. **Actualización de Vínculos**: Actualiza automáticamente todas las tablas vinculadas para que apunten a las bases de datos locales

5. **Logging Detallado**: Genera un log completo del proceso en `setup_local_environment.log`

**📋 Casos de Uso Típicos:**

```bash
# Primer setup en un nuevo entorno de desarrollo
python tools/setup_local_environment.py --check-network  # Verificar configuración
python tools/setup_local_environment.py                  # Setup completo

# Actualizar solo vínculos después de cambios en .env
python tools/setup_local_environment.py --links-only

# Verificar problemas de conectividad
python tools/setup_local_environment.py --check-network
```

**⚠️ Importante para Desarrolladores:**
- **Ejecutar desde la red de oficina** o con VPN para acceder a las bases remotas
- **Verificar el archivo `.env`** antes de ejecutar el script
- **Usar `--check-network`** para diagnosticar problemas de conectividad
- **El script es seguro**: no modifica las bases de datos de oficina, solo las copia

#### 📊 Otras Herramientas de Desarrollo

**Configuración y Mantenimiento:**
```bash
# Generar reportes de cobertura
python tools/generate_coverage_report.py

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
