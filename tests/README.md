# Tests del Proyecto

## 📁 Estructura Organizada

### `unit/` - Tests Unitarios
Tests que prueban funciones o métodos individuales de forma aislada.

- `brass/` - Tests del módulo brass
- `common/` - Tests de utilidades comunes
- `correos/` - Tests del módulo de correos
- `expedientes/` - Tests del módulo de expedientes

### `integration/` - Tests de Integración
Tests que prueban la interacción entre múltiples componentes.

- `brass/` - Integración del sistema brass
- `database/` - Integración con bases de datos
- `correos/` - Integración del sistema de correos

### `functional/` - Tests Funcionales
Tests que prueban flujos completos de trabajo.

- `access_sync/` - Sincronización con Access
- `correos_workflows/` - Flujos completos de correos

### `fixtures/` - Datos y Utilidades de Prueba
Scripts y datos para configurar entornos de test.

### `data/` - Bases de Datos de Test
Bases de datos SQLite para testing.

## 🚀 Comandos de Ejecución

```bash
# Todos los tests
pytest

# Solo unitarios
pytest tests/unit/

# Solo integración
pytest tests/integration/

# Solo funcionales
pytest tests/functional/

# Con cobertura
pytest --cov=src tests/

# Módulo específico
pytest tests/unit/brass/
```

## 📊 Marcadores (Markers)

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.functional` - Tests funcionales
- `@pytest.mark.slow` - Tests que tardan más tiempo
- `@pytest.mark.correos` - Tests relacionados con correos
