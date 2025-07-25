# Tests de Sincronización Access ↔ SQLite

Este directorio contiene todas las pruebas relacionadas con la sincronización bidireccional entre Access y SQLite.

## Archivos

### Pruebas de Conexión
- `test_access_simple.py` - Prueba básica de conexión a Access con contraseña
- `test_access_drivers.py` - Diagnóstico de drivers ODBC para Access
- `test_access_bidirectional.py` - Prueba inicial de sincronización bidireccional

### Análisis de Estructura
- `inspect_access_structure.py` - Inspecciona y compara estructuras Access vs SQLite
- `test_bidirectional_sync.py` - Demuestra necesidad de sincronización bidireccional

### Implementación Funcional
- `sync_bidirectional_final.py` - **⭐ IMPLEMENTACIÓN PRINCIPAL** - Sincronización completa y funcional
- `test_final_bidirectional.py` - Test final con configuración completa

## Uso

### Verificar Conexión Access
```bash
python tests/access_sync/test_access_simple.py
```

### Ejecutar Sincronización Completa
```bash
python tests/access_sync/sync_bidirectional_final.py
```

### Inspeccionar Estructuras
```bash
python tests/access_sync/inspect_access_structure.py
```

## Configuración Requerida

- Contraseña Access en `.env`: `DB_PASSWORD=dpddpd`
- Archivos Access en `dbs-locales/`
- Archivos SQLite en `dbs-sqlite/`

## Resultado Esperado

✅ **Problema Resuelto**: Previene ciclos infinitos en envío de correos
- Access = Fuente de verdad para nuevos registros
- SQLite = Actualiza estados de procesamiento
- Sincronización bidireccional mantiene coherencia
