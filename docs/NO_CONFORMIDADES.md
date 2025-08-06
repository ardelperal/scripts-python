# Módulo de No Conformidades

## Descripción

El módulo de No Conformidades es una conversión completa del script VBScript legacy `NoConformidades.vbs` a Python. Este módulo gestiona el sistema de No Conformidades, incluyendo el seguimiento de acciones correctivas (ARAPC), notificaciones por email y generación de reportes.

## Características Principales

### 🔧 Funcionalidades Migradas

- **Gestión de No Conformidades**: Seguimiento completo del ciclo de vida de las NCs
- **Gestión de ARAPC**: Administración de Acciones de Respuesta a Auditorías, Procesos y Controles
- **Notificaciones por Email**: Sistema automatizado de notificaciones a responsables
- **Reportes HTML**: Generación de reportes detallados con estadísticas
- **Gestión de Usuarios**: Administración de usuarios de calidad, técnicos y administradores
- **Tareas Programadas**: Ejecución automática de tareas de calidad y técnicas

### 🏗️ Arquitectura del Módulo

```
src/no_conformidades/
├── __init__.py                    # Módulo principal
├── no_conformidades_manager.py    # Gestor principal de NCs
├── html_report_generator.py       # Generador de reportes HTML
└── email_notifications.py        # Gestor de notificaciones

scripts/
├── run_no_conformidades.py       # Script principal de ejecución
└── validate_no_conformidades.py  # Script de validación y tests

tests/
└── test_no_conformidades.py      # Tests unitarios completos
```

## Instalación y Configuración

### 1. Variables de Entorno

El módulo utiliza las siguientes variables de entorno (definidas en `.env`):

```bash
# Base de datos
DB_NO_CONFORMIDADES_PASSWORD=password123
LOCAL_DB_NOCONFORMIDADES=dbs-locales/NoConformidades_Datos.accdb
OFFICE_DB_NOCONFORMIDADES=\\servidor\NoConformidades_Datos.accdb

# Configuración de aplicación
APP_ID_NOCONFORMIDADES=8
NO_CONFORMIDADES_DIAS_TAREA_CALIDAD=7
NO_CONFORMIDADES_DIAS_TAREA_TECNICA=30

# Email y notificaciones
NO_CONFORMIDADES_EMAIL_SUBJECT_PREFIX=[No Conformidades]
NO_CONFORMIDADES_INCLUIR_ESTADISTICAS=true
```

### 2. Dependencias

El módulo utiliza las siguientes dependencias del proyecto:

- `src.common.config`: Configuración centralizada
- `src.common.database`: Conexiones a base de datos
- `src.common.email_sender`: Envío de emails
- `src.common.logger`: Sistema de logging

## Uso del Módulo

### Ejecución Principal

```bash
# Ejecutar el script principal
python scripts/run_no_conformidades.py

# Validar el módulo completo
python scripts/validate_no_conformidades.py
```

### Uso Programático

```python
from src.no_conformidades import (
    NoConformidadesManager, 
    HTMLReportGenerator, 
    ReportRegistrar
)

# Inicializar el gestor
manager = NoConformidadesManager()
manager.conectar_bases_datos()
manager.cargar_usuarios()

# Obtener datos
ncs_eficacia = manager.obtener_nc_pendientes_eficacia()
arapcs = manager.obtener_arapcs_pendientes()

# Generar reporte
html_generator = HTMLReportGenerator()
reporte = html_generator.generar_reporte_completo(
    ncs_eficacia, arapcs, [], []
)

# Enviar notificaciones
email_manager = ReportRegistrar()
email_manager.enviar_notificacion_calidad(
    ncs_eficacia, [], [], 
    "calidad@empresa.com", 
    "admin@empresa.com"
)
```

## Clases Principales

### NoConformidadesManager

Clase principal que gestiona todas las operaciones relacionadas con No Conformidades.

**Métodos principales:**
- `conectar_bases_datos()`: Establece conexiones a las bases de datos
- `cargar_usuarios()`: Carga usuarios de calidad, técnicos y administradores
- `obtener_nc_pendientes_eficacia()`: Obtiene NCs pendientes de control de eficacia
- `obtener_arapcs_pendientes()`: Obtiene ARAPCs pendientes
- `determinar_si_requiere_tarea_calidad()`: Determina si se debe ejecutar tarea de calidad
- `registrar_tarea_completada()`: Registra la finalización de una tarea

### HTMLReportGenerator

Generador de reportes HTML con estilos CSS integrados.

**Métodos principales:**
- `generar_reporte_completo()`: Genera un reporte HTML completo
- `generar_tabla_nc_eficacia()`: Genera tabla de NCs de eficacia
- `generar_tabla_arapcs()`: Genera tabla de ARAPCs
- `generar_resumen_estadisticas()`: Genera resumen estadístico

### EmailNotificationManager

Gestor de notificaciones por email.

**Métodos principales:**
- `enviar_notificacion_calidad()`: Envía notificación a equipo de calidad
- `enviar_notificacion_tecnica()`: Envía notificación a equipo técnico
- `enviar_notificacion_individual_arapc()`: Envía notificación individual de ARAPC
- `marcar_email_como_enviado()`: Registra el envío de email en base de datos

## Modelos de Datos

### NoConformidad

```python
@dataclass
class NoConformidad:
    codigo: str
    nemotecnico: str
    descripcion: str
    responsable_calidad: str
    fecha_apertura: datetime
    fecha_prev_cierre: datetime
    dias_para_cierre: int = 0
    fecha_cierre_real: Optional[datetime] = None
```

### ARAPC

```python
@dataclass
class ARAPC:
    id_accion: int
    codigo_nc: str
    descripcion: str
    responsable: str
    fecha_fin_prevista: datetime
    fecha_fin_real: Optional[datetime] = None
```

### Usuario

```python
@dataclass
class Usuario:
    usuario_red: str
    nombre: str
    correo: str
```

## Tests y Validación

### Ejecutar Tests

```bash
# Tests unitarios completos
python -m pytest tests/test_no_conformidades.py -v

# Validación completa del módulo
python scripts/validate_no_conformidades.py
```

### Cobertura de Tests

Los tests cubren:

- ✅ Instanciación de todas las clases
- ✅ Conexión a bases de datos (mocked)
- ✅ Generación de reportes HTML
- ✅ Envío de notificaciones (mocked)
- ✅ Lógica de determinación de tareas
- ✅ Manejo de datos vacíos
- ✅ Formateo de cadenas de correos
- ✅ Generación de estadísticas

## Logging y Monitoreo

El módulo utiliza el sistema de logging centralizado:

```python
# Configuración en .env
NO_CONFORMIDADES_LOG_LEVEL=INFO
NO_CONFORMIDADES_LOG_FILE=logs/no_conformidades.log

# Logs generados
- Conexiones a base de datos
- Ejecución de consultas SQL
- Envío de emails
- Errores y excepciones
- Estadísticas de ejecución
```

## Migración desde VBScript

### Funcionalidades Migradas

| VBScript Original | Python Equivalente | Estado |
|------------------|-------------------|---------|
| `ConectarBD()` | `conectar_bases_datos()` | ✅ Migrado |
| `ObtenerUsuario()` | `cargar_usuarios()` | ✅ Migrado |
| `DeterminarSiRequiereTareaCalidad()` | `determinar_si_requiere_tarea_calidad()` | ✅ Migrado |
| `EnviarCorreo()` | `enviar_notificacion_*()` | ✅ Migrado |
| `GenerarHTML()` | `generar_reporte_completo()` | ✅ Migrado |
| `RegistrarTarea()` | `registrar_tarea_completada()` | ✅ Migrado |
| `ObtenerNCsPendientesEficacia()` | `obtener_nc_pendientes_eficacia()` | ✅ Migrado |
| `ObtenerARAPCs()` | `obtener_arapcs_pendientes()` | ✅ Migrado |

### Mejoras Implementadas

- **Arquitectura modular**: Separación clara de responsabilidades
- **Configuración centralizada**: Uso de variables de entorno
- **Logging estructurado**: Sistema de logs detallado
- **Tests unitarios**: Cobertura completa de funcionalidades
- **Manejo de errores**: Gestión robusta de excepciones
- **Documentación**: Documentación completa del código
- **Tipado estático**: Uso de type hints para mejor mantenibilidad

## Troubleshooting

### Problemas Comunes

1. **Error de conexión a base de datos**
   ```
   Solución: Verificar rutas en .env y permisos de acceso
   ```

2. **Error de envío de email**
   ```
   Solución: Verificar configuración SMTP en .env
   ```

3. **Tests fallan**
   ```
   Solución: Ejecutar validate_no_conformidades.py para diagnóstico
   ```

### Logs de Diagnóstico

```bash
# Verificar logs
tail -f logs/no_conformidades.log

# Ejecutar en modo debug
NO_CONFORMIDADES_DEBUG_SQL=true python scripts/run_no_conformidades.py
```

## Roadmap

### Próximas Mejoras

- [ ] Interfaz web para gestión de NCs
- [ ] API REST para integración con otros sistemas
- [ ] Dashboard de métricas en tiempo real
- [ ] Notificaciones push y SMS
- [ ] Integración con sistemas de calidad externos
- [ ] Automatización de flujos de trabajo

## Contribución

Para contribuir al módulo:

1. Crear una rama feature desde `feature/no-conformidades-migration`
2. Implementar cambios con tests correspondientes
3. Ejecutar `validate_no_conformidades.py` para verificar
4. Crear pull request con descripción detallada

## Soporte

Para soporte técnico:
- Revisar logs en `logs/no_conformidades.log`
- Ejecutar script de validación
- Consultar documentación de APIs utilizadas
- Contactar al equipo de desarrollo