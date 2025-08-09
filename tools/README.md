# Herramientas de Desarrollo

Este directorio contiene scripts y utilidades para el desarrollo, testing y mantenimiento del sistema.

## Categorías de Herramientas

### 📊 Diagnóstico y Verificación
- **`check_email_status.py`** - Verifica el estado de los correos en la base de datos
- **`check_email_structure.py`** - Valida la estructura de las tablas de correos
- **`check_email_recipients.py`** - Verifica los destinatarios de correos
- **`check_last_emails.py`** - Muestra los últimos correos registrados
- **`check_riesgos_emails.py`** - Verifica correos específicos del módulo de riesgos
- **`check_table_structure.py`** - Verifica la estructura de tablas de la base de datos
- **`test_db_connection.py`** - Prueba la conexión a las bases de datos

### 🧪 Gestión de Datos de Prueba
- **`prepare_test_emails.py`** - Prepara correos de prueba en la base de datos

### 🔧 Testing y Desarrollo
- **`test_individual_queries.py`** - Prueba consultas SQL individuales para diagnóstico
- **`test_monthly_report.py`** - Prueba la generación de informes mensuales
- **`test_riesgos_queries.py`** - Prueba específica de consultas del módulo de riesgos

### 🏗️ Entorno de Desarrollo
- **`setup_local_environment.py`** - Configura el entorno local de desarrollo y testing
- **`generate_coverage_report.py`** - Genera reportes de cobertura de código
- **`generate_full_coverage_report.py`** - Genera reportes completos de cobertura
- **`check_coverage_dependencies.py`** - Verifica dependencias para cobertura de código
- **`continuous_runner.py`** - Ejecutor continuo para desarrollo
- **`database_schemas.py`** - Herramientas para esquemas de base de datos

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