# Sistema de Gestión de Tareas - Migración de VBS a Python

Este proyecto es una migración del sistema legacy VBS a Python, implementando mejores prácticas de desarrollo, testing automatizado y soporte para múltiples entornos.

## Estructura del Proyecto

```
scripts-python/
├── .env                          # Variables de entorno
├── requirements.txt              # Dependencias Python
├── pyproject.toml               # Configuración de pytest y herramientas
├── setup.py                     # Script de instalación automática
├── run_brass.py                 # Script principal para módulo BRASS
├── src/                         # Código fuente
│   ├── __init__.py
│   ├── common/                  # Utilidades compartidas
│   │   ├── __init__.py
│   │   ├── config.py           # Configuración multi-entorno
│   │   ├── database.py         # Capa abstracción bases datos Access
│   │   └── utils.py           # Utilidades HTML, logging, fechas
│   └── brass/                  # Módulo BRASS (migrado)
│       ├── __init__.py
│       └── brass_manager.py    # Gestor principal BRASS
├── tests/                      # Tests automatizados (49 tests, 61% cobertura)
│   ├── __init__.py
│   ├── README.md              # Documentación estructura tests
│   ├── access_sync/           # 🔄 Tests sincronización Access-SQLite
│   │   ├── README.md          # Documentación específica
│   │   ├── sync_bidirectional_final.py (✅ FUNCIONAL)
│   │   ├── test_access_simple.py
│   │   └── test_bidirectional_sync.py
│   ├── emails/                # 📧 Tests sistema de correo HTML
│   │   ├── README.md
│   │   ├── test_correos_mailhog.py (✅ FUNCIONAL)
│   │   └── setup_smtp_local.py

│   ├── unit/                   # Tests unitarios por módulo
│   │   ├── common/             # Tests módulos comunes (31 tests)
│   │   │   ├── test_common_config.py
│   │   │   ├── test_common_database.py
│   │   │   └── test_common_utils.py
│   │   └── brass/              # Tests específicos BRASS (10 tests)
│   │       ├── test_brass_manager.py
│   │       └── test_brass_utils.py
│   └── integration/            # Tests integración BD real
│       └── brass/              # Tests flujo completo BRASS (4 tests)
│           └── test_brass_integration.py
├── templates/                  # Plantillas HTML
├── logs/                       # Archivos de log
├── dbs-locales/               # Bases de datos locales
├── herramientas/              # Archivos de configuración (CSS, etc.)
└── legacy/                    # Sistema VBS original
```

## Características Implementadas

### ✅ Migración Completada - Módulo BRASS
- **Gestión de equipos de medida y calibraciones**
- **Generación de reportes HTML**
- **Integración con bases de datos Access**
- **Sistema de notificaciones por correo**
- **Logging estructurado**

### 🔄 Próximas Migraciones
- Módulo NoConformidades
- Módulo GestionRiesgos
- Módulo Expedientes
- Módulo AGEDYS
- Sistema de correos

## 🐳 Entorno Docker

### Configuración Simplificada
- **Dockerfile**: Container ligero con Python 3.11-slim (~200MB)
- **docker-compose.yml**: Orquestación completa con múltiples perfiles
- **Sincronización Access ↔ SQLite**: Bidireccional sin pérdida de datos

### Comandos Docker
```bash
# Desarrollo local con MailHog
docker-compose --profile local up

# Solo dashboard web
docker-compose --profile local up scripts-python-web

# Producción con SMTP real
docker-compose --profile prod up

# Ver logs
docker-compose logs -f
```

### Perfiles Disponibles
- **`dev`**: Desarrollo con hot-reload
- **`local`**: Local con MailHog para testing de emails
- **`prod`**: Producción con SMTP real de oficina

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
```

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
```

**Ejecutar Tests:**
```bash
# Ejecutar todos los tests
pytest

# Ejecutar solo tests unitarios
pytest tests/unit/ -v

# Ejecutar solo tests de integración (requieren BD real)
pytest tests/integration/ -v -m integration

# Ejecutar con coverage completo
pytest --cov=src --cov-report=html --cov-report=term-missing

# Ejecutar tests específicos
pytest tests/unit/test_database.py -v
```

## Variables de Entorno Principales

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ENVIRONMENT` | Entorno (local/oficina) | `local` |
| `DB_PASSWORD` | Contraseña bases de datos | `dpddpd` |
| `LOCAL_DB_BRASS` | Ruta local BD BRASS | `dbs-locales/Brass.accdb` |
| `DEFAULT_RECIPIENT` | Correo por defecto | `user@domain.com` |

## Arquitectura

### Módulos Comunes (`src/common/`)

- **config.py**: Gestión centralizada de configuración
- **database.py**: Abstracción para bases de datos Access con ODBC  
- **utils.py**: Utilidades compartidas (HTML, fechas, logging)

### Mejoras vs VBS Legacy

1. **Type Safety**: Type hints en lugar de Variant
2. **Resource Management**: Context managers vs manual cleanup
3. **Error Handling**: Excepciones específicas vs On Error Resume Next
4. **Testing**: Tests automatizados vs testing manual
5. **Configuration**: Variables de entorno vs hard-coding
