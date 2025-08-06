# Tests Unitarios - Módulo No Conformidades

Este directorio contiene los tests unitarios para el módulo de No Conformidades.

## Estructura de Tests

### Tests Actuales

- `test_no_conformidades_manager.py`: Tests para la clase principal NoConformidadesManager
- `test_report_registrar.py`: Tests para las funciones de generación y envío de reportes
- `test_html_report_generator.py`: Tests para la generación de reportes HTML

## Ejecutar Tests

### Todos los tests unitarios del módulo:
```bash
python -m pytest tests/unit/no_conformidades/ -v
```

### Test específico:
```bash
python -m pytest tests/unit/no_conformidades/test_no_conformidades_manager.py -v
```

### Con cobertura:
```bash
python -m pytest tests/unit/no_conformidades/ --cov=src.no_conformidades --cov-report=html
```

## Notas Importantes

- Los tests utilizan mocks para las conexiones a bases de datos
- Se valida el formateo correcto de fechas para Access (formato MM/DD/YYYY)
- Los tests verifican la lógica de negocio sin depender de datos reales
- Se prueban tanto casos exitosos como manejo de errores

## Cobertura de Tests

Los tests cubren:
- ✅ Inicialización y configuración del manager
- ✅ Conexiones a bases de datos
- ✅ Obtención de datos de NC y ARAPC
- ✅ Generación de reportes HTML
- ✅ Envío de notificaciones por correo
- ✅ Registro de correos enviados
- ✅ Manejo de errores y casos edge
- ✅ Formateo de fechas y datos
- ✅ Aplicación de estilos CSS y clases

## Dependencias de Test

- pytest
- unittest.mock
- datetime
- Mocks de las clases principales del módulo