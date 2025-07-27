# Tests Manuales

Esta carpeta contiene tests manuales para verificar la funcionalidad específica de diferentes módulos del sistema.

## Archivos de Test

### test_brass.py
Test para el módulo BRASS adaptado. Verifica:
- Conexión a las bases de datos
- Obtención de usuarios administradores
- Generación de cadenas de correo

### test_noconformidades.py
Test básico para el módulo de No Conformidades. Verifica:
- Conexiones a bases de datos
- Validaciones de días entre semana
- Obtención de usuarios por tipo
- Generación de correos

### test_noconformidades_completo.py
Test completo y exhaustivo para el módulo de No Conformidades. Incluye:
- Todas las funcionalidades del test básico
- Pruebas adicionales de métodos internos
- Manejo de errores más detallado

### test_noconformidades_simple.py
Test simplificado que solo verifica las conexiones básicas a las bases de datos.

### test_user_functions.py
Test para las funciones comunes de usuarios. Verifica:
- Obtención de usuarios por tipo (calidad, técnicos, administradores)
- Funciones genéricas de usuarios
- Métodos de configuración

## Ejecución

Para ejecutar cualquier test, navega al directorio raíz del proyecto y ejecuta:

```bash
python tests/manual/test_nombre.py
```

## Logs

Los tests generan logs en la carpeta `logs/` del directorio raíz del proyecto.

## Notas

- Estos tests están diseñados para ser ejecutados manualmente durante el desarrollo
- Requieren acceso a las bases de datos configuradas en el entorno
- Algunos tests pueden requerir configuración específica del entorno