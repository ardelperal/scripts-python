# Scripts de Producción - Sistema de Monitoreo Continuo

Este directorio contiene los scripts de producción del sistema de monitoreo continuo, diseñados para ser ejecutados por `run_master.py` como daemon principal.

## 📁 Estructura del Directorio

```
scripts/
├── run_master.py              # 🎯 Script maestro - daemon principal del sistema
├── run_email_services.py      # 📧 Servicios unificados de envío de correos
├── run_brass.py               # 🔧 Procesamiento de datos BRASS
├── run_expedientes.py         # 📋 Gestión de expedientes y ofertas
├── run_riesgos.py             # ⚠️  Análisis y gestión de riesgos
├── run_no_conformidades.py    # 🔍 Gestión de no conformidades y ARAPs
├── development/               # 🛠️ Scripts de desarrollo y testing
│   ├── run_tests.py          # 🧪 Sistema completo de testing
│   ├── validate_*.py         # ✅ Scripts de validación
│   └── test_*.py             # 🔬 Scripts de pruebas específicas
└── README.md                  # 📖 Esta documentación
```

## 🎯 Script Principal: run_master.py

El **Master Runner** es el corazón del sistema de monitoreo continuo. Ejecuta de forma automática y programada todos los scripts de producción según horarios y contextos específicos.

### Características Principales:
- **Daemon de producción**: Ejecuta 24/7 con ciclos adaptativos
- **Gestión inteligente de horarios**: Diferentes frecuencias según día/noche y laborable/no laborable
- **Manejo robusto de errores**: Logging detallado y recuperación automática
- **Monitoreo de estado**: Seguimiento de ejecuciones y estadísticas
- **Configuración flexible**: Variables de entorno para todos los parámetros

### Scripts Gestionados:
1. **email_services** → `run_email_services.py` (continuo unificado)
2. **riesgos** → `run_riesgos.py` (diario)
3. **brass** → `run_brass.py` (diario)
4. **expedientes** → `run_expedientes.py` (diario)
5. **no_conformidades** → `run_no_conformidades.py` (diario)

## 📧 Scripts de Producción

### run_email_services.py
- **Función**: Gestión unificada de servicios de correo (reemplaza correos y correo_tareas)
- **Tipo**: Tarea continua (ejecutada en cada ciclo)
- **Descripción**: Procesa colas de correo de múltiples orígenes (correos, tareas) y envía notificaciones

### run_brass.py
- **Función**: Procesamiento de datos BRASS
- **Tipo**: Tarea diaria
- **Descripción**: Análisis y procesamiento de información BRASS

### run_expedientes.py
- **Función**: Gestión de expedientes y ofertas
- **Tipo**: Tarea diaria
- **Descripción**: Monitoreo de expedientes en fase de oferta de larga duración

### run_riesgos.py
- **Función**: Análisis y gestión de riesgos
- **Tipo**: Tarea diaria
- **Descripción**: Evaluación y reporte de riesgos del sistema

### run_no_conformidades.py
- **Función**: Gestión de no conformidades y ARAPs
- **Tipo**: Tarea diaria
- **Descripción**: Monitoreo de no conformidades y acciones correctivas

## 🛠️ Scripts de Desarrollo

Los scripts de desarrollo se encuentran en el subdirectorio `development/` y incluyen:

- **run_tests.py**: Sistema completo de testing con cobertura
- **validate_*.py**: Scripts de validación de datos y conexiones
- **test_*.py**: Scripts de pruebas específicas para módulos

## 🚀 Uso en Producción

### Ejecución del Master Runner:
```bash
# Ejecución normal (recomendado para producción)
python run_master.py

# Con logging detallado
python run_master.py --verbose

# Modo dry-run (para testing)
python run_master.py --dry-run
```

### Ejecución Individual de Scripts:
```bash
# Ejecutar script específico
python run_email_services.py
python run_brass.py
python run_expedientes.py
python run_riesgos.py
python run_no_conformidades.py
```

## ⚙️ Configuración

Los scripts utilizan variables de entorno definidas en `.env` en la raíz del proyecto. Consulte el README principal del proyecto para la configuración completa.

### Variables Clave para Scripts:
- `MASTER_CYCLE_*`: Tiempos de ciclo del master runner
- `MASTER_SCRIPT_TIMEOUT`: Timeout para ejecución de scripts
- `MASTER_LOG_LEVEL`: Nivel de logging
- Variables específicas de cada módulo (SMTP, BD, etc.)

## 📊 Monitoreo y Logs

- **Logs del Master**: `logs/run_master.log`
- **Estado del Master**: `logs/run_master_status.json`
- **Logs individuales**: Cada script genera sus propios logs

## 🔒 Seguridad

- **No incluir credenciales**: Usar variables de entorno
- **Validación de entrada**: Todos los scripts validan parámetros
- **Manejo de errores**: Logging seguro sin exposición de datos sensibles
- **Timeouts**: Prevención de ejecuciones colgadas

## 📈 Estadísticas y Rendimiento

El Master Runner mantiene estadísticas detalladas:
- Número de ciclos ejecutados
- Scripts exitosos/fallidos
- Tiempos de ejecución
- Estado de cada módulo

---

**Nota**: Este directorio contiene únicamente scripts de producción. Para desarrollo, testing y validación, consulte el subdirectorio `development/`.