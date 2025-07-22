# Tests Structure

Este proyecto utiliza una estructura de tests organizada por módulos y tipos de prueba.

## Estructura

```
tests/
├── unit/                    # Tests unitarios (componentes aislados)
│   ├── common/             # Tests para módulos comunes reutilizables
│   │   ├── test_common_config.py      # Tests configuración multi-entorno
│   │   ├── test_common_database.py    # Tests capa abstracción BD
│   │   └── test_common_utils.py       # Tests utilidades HTML/logging
│   └── brass/              # Tests específicos del módulo BRASS
│       ├── test_brass_manager.py      # Tests gestor principal BRASS
│       └── test_brass_utils.py        # Tests utilidades específicas BRASS
└── integration/            # Tests de integración (componentes interconectados)
    └── brass/              # Tests integración BRASS con BD real
        └── test_brass_integration.py  # Tests flujo completo BRASS
```

## Convenciones de nomenclatura

### Para tests unitarios:
- `test_[módulo]_[componente].py` - Tests de funciones específicas
- `test_[módulo]_manager.py` - Tests del gestor principal del módulo
- `test_[módulo]_utils.py` - Tests de utilidades específicas del módulo

### Para tests de integración:
- `test_[módulo]_integration.py` - Tests del flujo completo del módulo

### Para módulos futuros:
Cuando se migren otros módulos VBS, seguir el patrón:

```
tests/unit/[modulo]/
├── test_[modulo]_manager.py
├── test_[modulo]_utils.py
└── __init__.py

tests/integration/[modulo]/
├── test_[modulo]_integration.py
└── __init__.py
```

## Ejecución de tests

```bash
# Todos los tests
pytest tests/ -v

# Solo tests unitarios
pytest tests/unit/ -v

# Solo tests de integración
pytest tests/integration/ -v

# Tests de un módulo específico
pytest tests/unit/brass/ -v
pytest tests/integration/brass/ -v

# Tests con cobertura
pytest tests/ -v --cov=src --cov-report=html
```

## Módulos preparados

- ✅ **BRASS** - Gestión equipos de medida (migración completada)
- 🔄 **NoConformidades** - Gestión de no conformidades (pendiente)
- 🔄 **GestionRiesgos** - Gestión de riesgos (pendiente)  
- 🔄 **Expedientes** - Gestión de expedientes (pendiente)
- 🔄 **AGEDYS** - Sistema AGEDYS (pendiente)

## Cobertura actual

- **Total**: 61% de cobertura
- **Common**: 100% config, 81% database, 52% utils
- **BRASS**: 47% manager

La infraestructura común (`common/`) está completamente testada y lista para ser reutilizada por los próximos módulos VBS a migrar.
