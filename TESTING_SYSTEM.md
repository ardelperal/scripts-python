# 🧪 Sistema Completo de Testing

Este documento describe el sistema completo de testing implementado para el proyecto scripts-python, que incluye tests unitarios, de integración, de email, y reportes detallados de cobertura.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación y Configuración](#instalación-y-configuración)
- [Ejecución de Tests](#ejecución-de-tests)
- [Reportes y Cobertura](#reportes-y-cobertura)
- [Dashboard Ejecutivo](#dashboard-ejecutivo)
- [Comandos Útiles](#comandos-útiles)

## ✨ Características

- **Tests Unitarios**: Verificación de componentes individuales
- **Tests de Integración**: Verificación de interacciones entre componentes
- **Tests de Email**: Verificación específica de funcionalidad de correos
- **Cobertura de Código**: Análisis detallado de cobertura con reportes HTML y XML
- **Reportes Visuales**: Tablas de resultados y dashboard ejecutivo
- **Configuración Automática**: Scripts de setup para preparar el entorno
- **Integración con MailHog**: Testing de emails en entorno local

## 📁 Estructura del Proyecto

```
tests/
├── unit/                    # Tests unitarios
│   ├── common/             # Tests para módulos comunes
│   ├── brass/              # Tests para módulo BRASS
│   ├── correos/            # Tests para módulo de correos
│   └── expedientes/        # Tests para módulo de expedientes
├── integration/            # Tests de integración
├── emails/                 # Tests específicos de email
├── fixtures/               # Datos de prueba
├── data/                   # Bases de datos de test
├── config.py              # Configuración de tests
└── conftest.py            # Configuración global de pytest

# Scripts de testing
run_tests.py               # Script principal de ejecución
test_dashboard.py          # Dashboard ejecutivo
setup_test_environment.py # Configuración inicial
setup_testing.py          # Configuración avanzada

# Reportes generados
test-report.html          # Reporte de tests en HTML
htmlcov/                  # Reporte de cobertura HTML
coverage.xml              # Reporte de cobertura XML
```

## 🚀 Instalación y Configuración

### 1. Configuración Automática

Ejecuta el script de configuración inicial:

```bash
python setup_test_environment.py
```

Este script:
- ✅ Verifica la versión de Python
- 📦 Instala dependencias faltantes
- 📁 Crea estructura de directorios
- 🗄️ Configura base de datos de pruebas
- 🐳 Verifica Docker y MailHog
- ⚙️ Crea archivos de configuración

### 2. Configuración Manual

Si prefieres configurar manualmente:

```bash
# Instalar dependencias
pip install pytest pytest-cov tabulate

# Crear directorios
mkdir -p tests/{unit,integration,emails,fixtures,data}

# Configurar MailHog (opcional)
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

## 🧪 Ejecución de Tests

### Script Principal

```bash
# Ejecutar todos los tests con reporte completo
python run_tests.py

# Solo tests unitarios
python run_tests.py --unit

# Solo tests de integración
python run_tests.py --integration

# Solo tests de email
python run_tests.py --emails

# Tests de un módulo específico
python run_tests.py --module common

# Con reporte de cobertura detallado
python run_tests.py --coverage

# Generar reporte HTML
python run_tests.py --html
```

### Pytest Directo

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ -v --cov=src --cov-report=html

# Solo tests marcados
pytest tests/ -m "unit"
pytest tests/ -m "emails"
pytest tests/ -m "integration"
```

## 📊 Reportes y Cobertura

### Tipos de Reportes

1. **Reporte de Tests HTML** (`test-report.html`)
   - Resultados detallados de cada test
   - Tiempos de ejecución
   - Mensajes de error

2. **Reporte de Cobertura HTML** (`htmlcov/index.html`)
   - Cobertura por archivo
   - Líneas cubiertas/no cubiertas
   - Navegación interactiva

3. **Reporte de Cobertura XML** (`coverage.xml`)
   - Formato estándar para CI/CD
   - Integración con herramientas externas

### Visualización de Reportes

```bash
# Abrir reporte de tests
start test-report.html

# Abrir reporte de cobertura
start htmlcov/index.html

# En Linux/Mac
open test-report.html
open htmlcov/index.html
```

## 📈 Dashboard Ejecutivo

Ejecuta el dashboard para obtener un resumen completo:

```bash
python test_dashboard.py
```

El dashboard muestra:
- ✅ Estado general de los tests
- 📊 Cobertura de código actual
- 📁 Estructura de tests
- 📄 Reportes generados
- 💡 Recomendaciones de mejora

### Ejemplo de Salida

```
🚀 DASHBOARD DEL SISTEMA DE TESTING - SCRIPTS PYTHON
================================================================================
📅 Fecha: 2025-01-25 14:30:15

📊 ESTADO DE LOS TESTS
----------------------------------------
✅ Estado: TODOS LOS TESTS PASARON
📝 Resumen: 25 passed in 2.34s

📈 COBERTURA DE CÓDIGO
----------------------------------------
🎯 Cobertura Total: 75.2%
⚠️  Estado: BUENO (60-79%)

📁 ESTRUCTURA DE TESTS
----------------------------------------
+----------------------+------------+----------+
| Tipo de Test         |   Archivos | Estado   |
+======================+============+==========+
| Tests Unitarios      |          8 | ✅        |
| Tests de Integración |          2 | ✅        |
| Tests de Email       |          3 | ✅        |
+----------------------+------------+----------+
```

## 🛠️ Comandos Útiles

### Testing

```bash
# Ejecutar tests con diferentes niveles de verbosidad
pytest tests/ -v                    # Verbose
pytest tests/ -vv                   # Extra verbose
pytest tests/ -q                    # Quiet

# Ejecutar tests específicos
pytest tests/unit/common/           # Solo tests de common
pytest tests/emails/test_correos_mailhog.py  # Un archivo específico

# Ejecutar tests con filtros
pytest tests/ -k "test_email"       # Tests que contengan "test_email"
pytest tests/ -m "not slow"         # Excluir tests marcados como "slow"

# Parar en el primer fallo
pytest tests/ -x

# Mostrar tests más lentos
pytest tests/ --durations=10
```

### Cobertura

```bash
# Cobertura con umbral mínimo
pytest tests/ --cov=src --cov-fail-under=80

# Cobertura solo de archivos modificados
pytest tests/ --cov=src --cov-report=term-missing

# Cobertura con exclusiones
pytest tests/ --cov=src --cov-report=html --cov-config=.coveragerc
```

### Debugging

```bash
# Ejecutar con pdb en fallos
pytest tests/ --pdb

# Capturar salida
pytest tests/ -s

# Mostrar warnings
pytest tests/ -W ignore::DeprecationWarning
```

## 🔧 Configuración Avanzada

### Marcadores de Tests

Los tests están organizados con marcadores:

- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.integration`: Tests de integración
- `@pytest.mark.emails`: Tests de funcionalidad de email
- `@pytest.mark.slow`: Tests que tardan más tiempo
- `@pytest.mark.smoke`: Tests de validación rápida

### Fixtures Disponibles

- `test_db`: Base de datos de pruebas
- `clean_db`: Base de datos limpia para cada test
- `smtp_config`: Configuración SMTP para tests

### Variables de Entorno

```bash
# Para tests de base de datos Access
export DB_PASSWORD="tu_password"

# Para configuración de email
export SMTP_HOST="localhost"
export SMTP_PORT="1025"
```

## 🎯 Objetivos de Cobertura

- **Objetivo Mínimo**: 60%
- **Objetivo Recomendado**: 80%
- **Objetivo Excelente**: 90%+

## 🚨 Solución de Problemas

### Problemas Comunes

1. **Error de importación de módulos**
   ```bash
   # Verificar PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **Base de datos no encontrada**
   ```bash
   # Ejecutar configuración
   python setup_test_environment.py
   ```

3. **MailHog no disponible**
   ```bash
   # Iniciar MailHog
   docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
   ```

4. **Dependencias faltantes**
   ```bash
   # Instalar todas las dependencias
   pip install -r requirements.txt
   ```

## 📝 Contribuir

Para añadir nuevos tests:

1. Crear archivo `test_*.py` en el directorio apropiado
2. Usar fixtures disponibles
3. Añadir marcadores apropiados
4. Ejecutar tests para verificar
5. Actualizar documentación si es necesario

## 📞 Soporte

Si encuentras problemas:

1. Ejecuta `python test_dashboard.py` para diagnóstico
2. Revisa los logs de error en los reportes
3. Verifica la configuración con `python setup_test_environment.py`
4. Consulta la documentación de pytest: https://docs.pytest.org/

---

**¡El sistema de testing está listo para usar! 🎉**