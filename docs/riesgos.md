# Módulo de Gestión de Riesgos

## Descripción

El módulo de gestión de riesgos (`src/riesgos`) es una migración completa del script VBScript `GestionRiesgos.vbs` a Python. Este módulo gestiona las tareas automatizadas relacionadas con el seguimiento y control de riesgos en proyectos.

## Funcionalidades Principales

### 1. Tareas Técnicas Semanales
- Generación de reportes personalizados para jefes de proyecto
- Identificación de ediciones que necesitan propuesta de publicación
- Seguimiento de propuestas rechazadas
- Control de riesgos aceptados y retirados
- Monitoreo de acciones de mitigación y contingencia

### 2. Tareas de Calidad Semanales
- Reportes de calidad para administradores
- Métricas de seguimiento de procesos
- Indicadores de cumplimiento

### 3. Tareas de Calidad Mensuales
- Reportes mensuales consolidados
- Análisis de tendencias
- Métricas de rendimiento a largo plazo

### 4. Generación de Reportes HTML
- Reportes con formato profesional
- Estilos CSS integrados
- Tablas dinámicas con datos actualizados

### 5. Sistema de Notificaciones
- Envío automático de correos electrónicos
- Notificaciones personalizadas por usuario
- Alertas para administradores

## Estructura del Módulo

```
src/riesgos/
├── __init__.py              # Inicialización del módulo
└── riesgos_manager.py       # Clase principal RiesgosManager
```

## Uso Básico

### Ejecución Diaria Automática

```python
from src.common.config import Config
from src.riesgos.riesgos_manager import RiesgosManager

# Cargar configuración
config = Config.from_file('config/config.json')

# Crear manager
manager = RiesgosManager(config)

# Ejecutar tareas diarias
if manager.execute_daily_task():
    print("Tareas ejecutadas exitosamente")
```

### Ejecución Forzada de Tareas Específicas

```python
# Conectar a la base de datos
if manager.connect():
    try:
        # Ejecutar tarea técnica
        if manager.execute_technical_task():
            manager.record_task_execution('TECNICA')
        
        # Ejecutar tarea de calidad
        if manager.execute_quality_task():
            manager.record_task_execution('CALIDAD')
        
        # Ejecutar tarea mensual
        if manager.execute_monthly_quality_task():
            manager.record_task_execution('CALIDADMENSUAL')
    finally:
        manager.disconnect()
```

## Script de Ejecución

El script `run_riesgos.py` proporciona una interfaz de línea de comandos:

```bash
# Ejecución normal
python run_riesgos.py

# Con configuración específica
python run_riesgos.py --config config/production.json

# Con logs detallados
python run_riesgos.py --verbose

# Forzar ejecución de tareas específicas
python run_riesgos.py --force-technical
python run_riesgos.py --force-quality
python run_riesgos.py --force-monthly
```

## Configuración

El módulo utiliza la configuración estándar del sistema. Parámetros relevantes:

```json
{
  "database_path": "ruta/a/base_datos.accdb",
  "smtp_server": "smtp.empresa.com",
  "smtp_port": 587,
  "smtp_username": "usuario@empresa.com",
  "smtp_password": "password",
  "admin_emails": ["admin@empresa.com"]
}
```

## Tipos de Tareas

### TECNICA
- **Frecuencia**: Semanal (cada 7 días)
- **Destinatarios**: Jefes de proyecto individuales
- **Contenido**: Reportes personalizados por usuario

### CALIDAD
- **Frecuencia**: Semanal (cada 7 días)
- **Destinatarios**: Administradores
- **Contenido**: Métricas de calidad generales

### CALIDADMENSUAL
- **Frecuencia**: Mensual (cada 30 días)
- **Destinatarios**: Administradores
- **Contenido**: Reportes consolidados mensuales

## Consultas de Base de Datos

El módulo ejecuta múltiples consultas SQL para obtener datos de riesgos:

1. **Ediciones que necesitan propuesta de publicación**
2. **Ediciones con propuestas rechazadas**
3. **Riesgos aceptados no motivados**
4. **Riesgos aceptados rechazados**
5. **Riesgos retirados no motivados**
6. **Riesgos retirados rechazados**
7. **Riesgos con acciones de mitigación para replanificar**
8. **Riesgos con acciones de contingencia para replanificar**

## Generación de Reportes

### Estructura de Reportes HTML

Los reportes incluyen:
- Encabezado con información del usuario/fecha
- Estilos CSS integrados
- Secciones organizadas por tipo de riesgo
- Tablas con datos detallados
- Contadores de elementos por sección

### Personalización de Estilos

Los estilos CSS se pueden personalizar modificando el método `get_css_styles()`:

```python
def get_css_styles(self) -> str:
    return """
    <style type="text/css">
    body { font-family: Arial, sans-serif; }
    table { border-collapse: collapse; width: 100%; }
    /* Más estilos... */
    </style>
    """
```

## Manejo de Errores

El módulo incluye manejo robusto de errores:

- Logging detallado de todas las operaciones
- Manejo de fallos de conexión a base de datos
- Recuperación de errores en consultas individuales
- Notificación de errores a administradores

## Logging

El sistema de logging registra:
- Inicio y fin de tareas
- Errores de base de datos
- Envío de correos electrónicos
- Métricas de ejecución

Los logs se guardan en `logs/riesgos.log`.

## Migración desde VBScript

### Equivalencias de Funciones

| VBScript | Python |
|----------|--------|
| `Lanzar()` | `execute_daily_task()` |
| `RealizarTareaTecnicos()` | `execute_technical_task()` |
| `RealizarTareaCalidadMensual()` | `execute_monthly_quality_task()` |
| `getColUsuariosDistintos()` | `get_distinct_users()` |
| `UltimaEjecucion()` | `get_last_execution()` |
| `getCSS()` | `get_css_styles()` |

### Mejoras Implementadas

1. **Manejo de errores mejorado**
2. **Logging estructurado**
3. **Configuración centralizada**
4. **Pruebas unitarias completas**
5. **Documentación detallada**
6. **Interfaz de línea de comandos**

## Pruebas

Ejecutar las pruebas unitarias:

```bash
python -m pytest tests/test_riesgos_manager.py -v
```

Las pruebas cubren:
- Inicialización del manager
- Conexión a base de datos
- Lógica de decisión de tareas
- Generación de reportes
- Manejo de errores
- Envío de notificaciones

## Programación de Tareas

### Windows Task Scheduler

Crear una tarea programada que ejecute:

```cmd
python run_riesgos.py
```

### Cron (Linux/Unix)

```bash
# Ejecutar diariamente a las 8:00 AM
0 8 * * * python3 run_riesgos.py
```

## Monitoreo y Mantenimiento

### Verificación de Estado

```python
# Verificar última ejecución
ultima_tecnica = manager.get_last_execution('TECNICA')
ultima_calidad = manager.get_last_execution('CALIDAD')
ultima_mensual = manager.get_last_execution('CALIDADMENSUAL')

# Verificar tareas pendientes
pendiente_tecnica = manager.should_execute_technical_task()
pendiente_calidad = manager.should_execute_quality_task()
pendiente_mensual = manager.should_execute_monthly_quality_task()
```

### Métricas de Rendimiento

El módulo registra métricas como:
- Tiempo de ejecución de tareas
- Número de usuarios notificados
- Cantidad de elementos en reportes
- Errores y excepciones

## Solución de Problemas

### Problemas Comunes

1. **Error de conexión a base de datos**
   - Verificar ruta del archivo .accdb
   - Comprobar permisos de lectura
   - Validar drivers ODBC

2. **Fallos en envío de correos**
   - Verificar configuración SMTP
   - Comprobar credenciales
   - Validar direcciones de correo

3. **Consultas SQL lentas**
   - Revisar índices en base de datos
   - Optimizar consultas complejas
   - Considerar paginación para grandes volúmenes

### Logs de Diagnóstico

Activar logging detallado:

```bash
python run_riesgos.py --verbose
```

## Extensibilidad

### Agregar Nuevos Tipos de Reportes

1. Crear método de consulta específico
2. Implementar generación de HTML
3. Agregar lógica de programación
4. Actualizar pruebas unitarias

### Personalizar Notificaciones

```python
def custom_notification(self, user_data, report_html):
    # Lógica personalizada de notificación
    pass
```

## Consideraciones de Seguridad

- Las credenciales se almacenan en configuración cifrada
- Validación de entrada en consultas SQL
- Sanitización de datos en reportes HTML
- Logging sin información sensible