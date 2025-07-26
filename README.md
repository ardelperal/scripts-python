# Sistema de Gestión de Tareas - Migración de VBS a Python

Este proyecto es una migración del sistema legacy VBS a Python, implementando mejores prácticas de desarrollo, testing automatizado y soporte para múltiples entornos.

## 📋 Tabla de Contenidos

- [Estructura del Proyecto](#estructura-del-proyecto)
- [Características Implementadas](#características-implementadas)
- [Configuración de Entornos](#configuración-de-entornos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Testing](#testing)
- [Variables de Entorno Principales](#variables-de-entorno-principales)
- [Arquitectura](#arquitectura)

## Estructura del Proyecto

```
scripts-python/
├── .env                          # Variables de entorno
├── requirements.txt              # Dependencias Python
├── pyproject.toml               # Configuración de pytest y herramientas
├── run_brass.py                 # Script principal para módulo BRASS
├── run_expedientes.py           # Script para módulo expedientes
├── run_EnviarCorreo.py          # Script para módulo correos
├── run_tests.py                 # Script principal de testing
├── generate_coverage_report.py  # Generador reportes de cobertura
├── .coveragerc                  # Configuración coverage.py
├── src/                         # Código fuente
│   ├── __init__.py
│   ├── common/                  # Utilidades compartidas
│   │   ├── __init__.py
│   │   ├── config.py           # Configuración multi-entorno
│   │   ├── database.py         # Capa abstracción bases datos Access
│   │   ├── database_adapter.py # Adaptador de bases de datos
│   │   └── utils.py           # Utilidades HTML, logging, fechas
│   ├── brass/                  # Módulo BRASS (migrado)
│   │   ├── __init__.py
│   │   └── brass_manager.py    # Gestor principal BRASS
│   ├── correos/                # Módulo de correos
│   │   ├── __init__.py
│   │   └── correos_manager.py  # Gestor de correos
│   └── expedientes/            # Módulo de expedientes
│       ├── __init__.py
│       └── expedientes_manager.py # Gestor de expedientes
├── tests/                      # Tests automatizados (22 tests organizados)
│   ├── __init__.py
│   ├── config.py              # Configuración de tests
│   ├── conftest.py            # Configuración global pytest
│   ├── data/                  # Bases de datos de test
│   │   ├── __init__.py
│   │   └── test_database.db
│   ├── fixtures/              # Datos y utilidades de prueba
│   │   ├── __init__.py
│   │   ├── create_demo_databases.py
│   │   ├── create_demo_sqlite.py
│   │   ├── create_test_emails.py
│   │   ├── create_test_emails_demo.py
│   │   ├── migrate_databases.py
│   │   └── setup_smtp_local.py
│   ├── unit/                   # Tests unitarios por módulo
│   │   ├── __init__.py
│   │   ├── common/             # Tests módulos comunes
│   │   ├── brass/              # Tests específicos BRASS
│   │   ├── correos/            # Tests del módulo de correos
│   │   └── expedientes/        # Tests del módulo de expedientes
│   ├── integration/            # Tests de integración
│   │   ├── __init__.py
│   │   ├── brass/              # Integración del sistema brass
│   │   ├── correos/            # Integración del sistema de correos
│   │   └── database/           # Integración con bases de datos
│   └── functional/             # Tests funcionales
│       ├── access_sync/        # Sincronización con Access
│       └── correos_workflows/  # Flujos completos de correos
├── templates/                  # Plantillas HTML
├── logs/                       # Archivos de log
├── dbs-locales/               # Bases de datos locales
├── htmlcov/                   # Reportes HTML de cobertura
├── herramientas/              # Archivos de configuración (CSS, etc.)
├── docs/                      # Documentación
│   ├── coverage_setup_summary.md # Resumen configuración coverage
│   ├── htmlcov_usage_guide.md     # Guía uso reportes HTML
│   ├── docker_guia.md             # Guía completa de Docker
│   ├── panel_control_guia.md      # Guía del panel de control
│   └── smtp_config_changes.md     # Cambios configuración SMTP
├── examples/                    # Ejemplos y demos
│   └── smtp_config_demo.py      # Demo configuración SMTP
└── legacy/                    # Sistema VBS original
```

## Características Implementadas

### ✅ Módulos Migrados
- **BRASS**: Sistema de gestión de tareas migrado completamente
- **Correos**: Sistema de envío de correos HTML
- **Expedientes**: Gestión de expedientes (en desarrollo)

### 🔧 Infraestructura
- **Multi-entorno**: Soporte para local/oficina con detección automática
- **Base de datos**: Abstracción para Access con ODBC
- **Logging**: Sistema de logs estructurado
- **Testing**: 196 tests organizados con cobertura del 18%
- **Coverage**: Reportes HTML interactivos con coverage.py
- **SMTP**: Configuración sin autenticación para entorno oficina

### 🚀 Mejoras Implementadas
- Manejo robusto de errores
- Configuración centralizada
- Estructura modular
- Documentación completa
- CI/CD preparado

## Configuración de Entornos

El sistema soporta dos entornos configurables mediante el archivo `.env`:

### Configuración inicial
```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar configuraciones específicas
nano .env  # o tu editor preferido
```

### Entorno Local (`ENVIRONMENT=local`)
- **Bases de datos**: Archivos `.accdb` en `dbs-locales/`
- **Archivos CSS**: `herramientas/CSS.txt`
- **Uso**: Desarrollo, testing, trabajo sin red corporativa
- **Ventajas**: No requiere conexión de red, datos de prueba

### Entorno Oficina (`ENVIRONMENT=oficina`)
- **Bases de datos**: Rutas de red `\\servidor\aplicaciones\...`
- **Archivos CSS**: Rutas de red corporativas
- **Uso**: Producción, datos reales, integración completa
- **Requisitos**: Acceso a red corporativa, permisos ODBC

### Variables de entorno importantes
```bash
ENVIRONMENT=local|oficina          # Seleccionar entorno
DB_PASSWORD=contraseña_bd          # Contraseña bases datos
DEFAULT_RECIPIENT=email@empresa.com # Destinatario notificaciones
LOG_LEVEL=INFO|DEBUG|ERROR         # Nivel de logging

# Configuración SMTP (Entorno Oficina)
SMTP_SERVER=10.73.54.85           # Servidor SMTP oficina
SMTP_PORT=25                      # Puerto SMTP (sin autenticación)
SMTP_FROM=noreply@empresa.com     # Email remitente

# Configuración SMTP (Entorno Local)
SMTP_SERVER=localhost             # MailHog local
SMTP_PORT=1025                    # Puerto MailHog
SMTP_FROM=test@example.com        # Email de prueba
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

## Instalación

1. **Clonar el repositorio y navegar al directorio**
   ```bash
   git clone <repo-url>
   cd scripts-python
   ```

2. **Configurar variables de entorno**
   ```bash
   # Copiar el archivo de ejemplo
   cp .env.example .env
   
   # Editar .env con tus configuraciones específicas
   # - Cambiar DB_PASSWORD por la contraseña real
   # - Ajustar rutas de red para entorno oficina
   # - Configurar email de destinatario
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar script de instalación (opcional)**
   ```bash
   python setup.py
   ```

2. **Configurar variables de entorno**
   ```bash
   # Editar .env según el entorno deseado
   # Por defecto está configurado para entorno local
   ```

3. **Instalar driver ODBC para Access** (si no está instalado)
   - Descargar Microsoft Access Database Engine

## Uso

### 🌐 Panel de Control Web (Recomendado)
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

### 🔧 Línea de Comandos (Alternativo)

**Ejecutar Módulos:**
```bash
# Ejecutar tarea BRASS
python run_brass.py

# Ejecutar módulo de correos
python run_EnviarCorreo.py

# Ejecutar módulo de expedientes
python run_expedientes.py
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
```

### 📊 Coverage (Cobertura de Código)

**Generar Reportes de Cobertura:**
```bash
# Método rápido (recomendado)
python generate_coverage_report.py

# Método manual
coverage run --source=src -m pytest tests/unit/ -v
coverage html
start htmlcov\index.html
```

**Estado Actual:**
- **Total**: 196 tests ejecutándose correctamente
- **Cobertura**: 18% del código fuente
- **Reportes HTML**: Disponibles en `htmlcov/index.html`

**Archivos de Coverage:**
- `.coveragerc` - Configuración de coverage.py
- `htmlcov/` - Reportes HTML interactivos
- `generate_coverage_report.py` - Script automatizado

**Interpretación de Reportes:**
- 🟢 **Verde**: Líneas cubiertas por tests
- 🔴 **Rojo**: Líneas sin cobertura (necesitan tests)
- 🟡 **Amarillo**: Cobertura parcial
- ⚪ **Blanco**: Líneas no ejecutables

## Variables de Entorno Principales

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ENVIRONMENT` | Entorno (local/oficina) | `local` |
| `DB_PASSWORD` | Contraseña bases de datos | `dpddpd` |
| `LOCAL_DB_BRASS` | Ruta local BD BRASS | `dbs-locales/Brass.accdb` |
| `OFFICE_DB_BRASS` | Ruta oficina BD BRASS | `\\servidor\aplicaciones\Brass.accdb` |
| `DEFAULT_RECIPIENT` | Correo por defecto | `user@domain.com` |
| `SMTP_SERVER` | Servidor SMTP | `10.73.54.85` |
| `SMTP_PORT` | Puerto SMTP | `25` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |

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
