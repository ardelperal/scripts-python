# Panel de Control Web - Guía de Usuario

## 🚀 Inicio Rápido

### 1. Iniciar el servidor
```bash
python server.py
```

### 2. Abrir navegador
- URL: `http://localhost:8888`
- Compatible con Chrome, Firefox, Edge, Safari

## 🎛️ Funcionalidades

### Panel Principal
- **Estado del sistema**: Entorno activo, módulos migrados
- **Indicador de conexión**: Estado en tiempo real
- **Información de entorno**: Local vs Oficina

### Módulos Disponibles

#### ✅ BRASS (Migrado)
- **Ejecutar BRASS**: Lanza el proceso completo de gestión de equipos
- **Tests Unitarios**: Ejecuta tests específicos del módulo BRASS
- **Tests Integración**: Pruebas con bases de datos reales

#### ⏳ Módulos Pendientes
- NoConformidades
- GestionRiesgos  
- Expedientes
- AGEDYS

### Sistema de Tests

#### Tests Globales
- **Ejecutar Todos los Tests**: 49 tests completos del sistema
- **Tests + Cobertura**: Genera reporte HTML de cobertura
- **Solo Tests Unitarios**: Tests aislados (45 tests)
- **Solo Tests Integración**: Tests con BD real (4 tests)

#### Consola Integrada
- **Logs en tiempo real**: Salida de procesos y tests
- **Timestamps**: Marca temporal de cada operación
- **Códigos de color**: ✅ Éxito, ❌ Error, ℹ️ Información
- **Botón limpiar**: Reinicia la consola

## 🔧 Uso Típico

### Desarrollador - Flujo de Trabajo
1. **Iniciar servidor**: `python server.py`
2. **Abrir panel**: http://localhost:8888
3. **Verificar entorno**: Confirmar Local/Oficina
4. **Ejecutar tests**: Verificar que todo funciona
5. **Ejecutar módulo**: Probar funcionalidad
6. **Monitorear logs**: Revisar salida en consola

### Testing Automatizado
```bash
# Secuencia recomendada desde el panel:
1. "Solo Tests Unitarios" - Verificar lógica
2. "Solo Tests Integración" - Verificar BD
3. "Tests + Cobertura" - Generar reporte
4. "Ejecutar BRASS" - Probar funcionalidad real
```

### Debugging
- **Logs detallados**: Cada acción se registra con timestamp
- **Errores específicos**: Distinción entre errores de código y conexión
- **Salida completa**: stdout/stderr de procesos
- **Estado persistente**: El servidor mantiene historial

## 🌐 API Endpoints

### GET Endpoints
- `/` - Panel principal HTML
- `/api/status` - Estado del sistema JSON
- `/api/environment` - Información del entorno

### POST Endpoints
- `/api/execute` - Ejecutar módulo
  ```json
  {"module": "brass"}
  ```
- `/api/test` - Ejecutar tests
  ```json
  {"type": "unit|integration|coverage|all", "module": "brass"}
  ```

## 🔒 Seguridad

### Red Local
- Servidor binding solo a `localhost`
- No accesible desde red externa
- Autenticación: No requerida (entorno desarrollo)

### Ejecución de Comandos
- Sandbox: Solo scripts del proyecto
- Timeout: 5min módulos, 10min tests
- Validación: Módulos permitidos únicamente

## 🐛 Troubleshooting

### Puerto ocupado
```bash
# Cambiar puerto en server.py línea ~293:
PORT = 8889  # o cualquier puerto libre
```

### Error de permisos
```bash
# Ejecutar como administrador o cambiar puerto > 1024
```

### Módulos no disponibles
- Solo BRASS está migrado
- Otros módulos se habilitarán cuando se migren

### Tests fallan
- Verificar entorno en .env
- Confirmar acceso a bases de datos
- Revisar permisos ODBC

## 📊 Monitoring

### Métricas Disponibles
- **Tests**: 49 tests totales, 63% cobertura
- **Módulos**: 1/5 migrados (BRASS)
- **Entornos**: Local + Oficina soportados
- **Tiempo de ejecución**: Monitoreo en tiempo real

### Estado de Salud
- 🟢 Verde: Sistema operativo
- 🟡 Amarillo: Advertencias menores  
- 🔴 Rojo: Errores críticos

El panel se actualiza automáticamente cada 30 segundos.
