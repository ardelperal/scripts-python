# Herramientas de Desarrollo

Este directorio contiene scripts y utilidades para el desarrollo, testing y mantenimiento del sistema.

## Categorías de Herramientas

### 📊 Diagnóstico y Verificación
- **`check_email_status.py`** - Verifica el estado de los correos en la base de datos
- **`check_email_structure.py`** - Valida la estructura de las tablas de correos
- **`diagnose_id_issue.py`** - Diagnostica problemas con IDs en la base de datos

### 🧪 Gestión de Datos de Prueba
- **`fix_test_email.py`** - Corrige datos de correos de prueba
- **`insert_test_email.py`** - Inserta correos de prueba en la base de datos

### 🔧 Entorno de Desarrollo
- **`setup_local_environment.py`** - Configura el entorno local de desarrollo y testing
- **`generate_coverage_report.py`** - Genera reportes de cobertura de código

## Uso

Ejecutar desde el directorio raíz del proyecto:

```bash
# Ejemplo: Verificar estado de correos
python tools/check_email_status.py

# Ejemplo: Configurar entorno de desarrollo
python tools/setup_local_environment.py

# Ejemplo: Generar reporte de cobertura
python tools/generate_coverage_report.py
```

## Notas

- Estas herramientas están diseñadas para uso en desarrollo y testing
- No deben usarse en producción
- Algunas herramientas pueden requerir configuración específica del entorno
- Consultar la documentación individual de cada script para más detalles