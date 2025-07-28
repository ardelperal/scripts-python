# Estructura del Proyecto

## Directorio Raíz
```
scripts-python/
├── src/                    # Código fuente principal
├── tests/                  # Tests organizados por tipo
├── scripts/                # Scripts de ejecución y producción
├── tools/                  # Herramientas de desarrollo
├── examples/               # Ejemplos y demos
├── legacy/                 # Código legacy (VBS, etc.)
├── herramientas/          # Recursos y configuraciones
├── logs/                  # Archivos de log
├── .coveragerc            # Configuración de cobertura
├── .gitignore             # Archivos ignorados por Git
├── requirements.txt       # Dependencias Python
└── PROJECT_STRUCTURE.md   # Este archivo
```

## Estructura Detallada

### `/src` - Código Fuente Principal
- **`common/`** - Módulos compartidos (configuración, logging, utilidades)
- **`correos/`** - Gestión de correos electrónicos
- **`expedientes/`** - Gestión de expedientes
- **`riesgos/`** - Gestión de riesgos

### `/tests` - Tests Organizados
- **`unit/`** - Tests unitarios organizados por módulo
  - `common/`, `correos/`, `expedientes/`, `riesgos/`
- **`manual/`** - Tests manuales y de integración

### `/scripts` - Scripts de Ejecución
- **`run_master.py`** - Script maestro de producción (reemplaza script-continuo.vbs)
- **`run_EnviarCorreo.py`** - Ejecutor de correos
- **`run_brass.py`** - Ejecutor BRASS
- **`run_expedientes.py`** - Ejecutor de expedientes
- **`run_riesgos.py`** - Ejecutor de riesgos
- **`run_tests.py`** - Ejecutor de tests

### `/tools` - Herramientas de Desarrollo
- Scripts para diagnóstico, testing y mantenimiento
- No son parte del código de producción

### `/examples` - Ejemplos y Demos
- Scripts de demostración y ejemplos de uso
- Documentación práctica del sistema

## Cambios Realizados en la Reorganización

### Archivos Movidos
1. **8 scripts de herramientas** → `tools/`
   - `check_email_status.py`, `check_email_structure.py`, `diagnose_id_issue.py`
   - `fix_test_email.py`, `insert_test_email.py`, `generate_coverage_report.py`
   - `setup_local_environment.py`

2. **1 test manual** → `tests/manual/`
   - `test_insertar_correo.py`

3. **1 ejemplo/demo** → `examples/`
   - `demo_metodo_correcto.py`

4. **Script maestro** → `scripts/`
   - `continuous_runner.py` → `run_master.py` (renombrado y adaptado)

### Archivos Eliminados
- `setup_local_environment.py` (duplicado en raíz)
- `test_riesgos_manager_old.py` (versión obsoleta)

### Archivos Creados
- `tools/README.md` - Documentación de herramientas
- `examples/README.md` - Documentación de ejemplos
- `PROJECT_STRUCTURE.md` - Este archivo

## Beneficios de la Nueva Estructura

1. **Separación Clara de Responsabilidades**
   - Código fuente en `/src`
   - Scripts de producción en `/scripts`
   - Herramientas de desarrollo en `/tools`
   - Ejemplos en `/examples`

2. **Tests Organizados**
   - Tests unitarios separados por módulo
   - Tests manuales en directorio específico

3. **Documentación Mejorada**
   - README específicos para cada directorio
   - Estructura documentada

4. **Mantenibilidad**
   - Fácil localización de archivos
   - Estructura estándar de proyecto Python

## Estado Actual del Proyecto

✅ **Tests Unitarios**: 296 tests pasando  
✅ **Cobertura de Código**: 79% general  
✅ **Sin Rutas Absolutas**: Código portable  
✅ **Estructura Profesional**: Organización estándar  
✅ **Documentación**: READMEs actualizados  
✅ **Script Maestro**: Adaptado de legacy VBS a Python

El repositorio está ahora listo para producción con una estructura limpia y profesional.