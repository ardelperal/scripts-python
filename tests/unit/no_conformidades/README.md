# Tests para No Conformidades

Esta carpeta contiene los tests unitarios para el módulo de No Conformidades.

## Estructura

- `test_no_conformidades_manager.py`: Tests para el manager principal y las clases de datos (NoConformidad, ARAPC, Usuario)
- `test_email_notifications.py`: Tests para las notificaciones por email
- `test_html_report_generator.py`: Tests para el generador de reportes HTML

## Ejecutar tests

Para ejecutar todos los tests de no_conformidades:
```bash
pytest tests/unit/no_conformidades/ -v
```

Para ejecutar un archivo específico:
```bash
pytest tests/unit/no_conformidades/test_email_notifications.py -v
```

Para ejecutar con cobertura:
```bash
pytest tests/unit/no_conformidades/ --cov=src.no_conformidades --cov-report=html
```

## Notas importantes

- Los tests utilizan mocks para simular las conexiones a base de datos
- Se verifica el formato de fecha correcto para Access (#mm/dd/yyyy#)
- Se valida el uso de la función `get_max_id` para obtener el siguiente IDCorreo
- Los tests están organizados por funcionalidad para facilitar el mantenimiento