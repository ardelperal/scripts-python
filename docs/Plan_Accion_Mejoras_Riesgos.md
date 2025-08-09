# Plan de Acción - Mejoras Módulo Gestión de Riesgos

## Resumen Ejecutivo
Este plan de acción implementa las mejoras identificadas en el análisis del módulo de Gestión de Riesgos, priorizando la corrección de bugs críticos, optimización de rendimiento y refactorización del código para mejorar la mantenibilidad.

---

## ✅ PROGRESO ACTUAL - TAREAS COMPLETADAS

### Fase 1: Corrección de Bugs Críticos 🚨 - **COMPLETADA PARCIALMENTE**

#### 1.1 Corrección de Inconsistencias en Tablas HTML ✅ **COMPLETADO**
- [x] **Auditar todas las funciones `_generate_*_table`**
  - [x] Revisar `_generate_editions_need_publication_table`
  - [x] Verificar correspondencia entre cabeceras HTML y claves de datos
  - [x] Identificar otras funciones con el mismo problema
  - [x] Documentar todas las inconsistencias encontradas

- [x] **Corregir las inconsistencias identificadas**
  - [x] Alinear cabeceras HTML con las claves de datos reales
  - [x] Verificar que los datos se muestren correctamente
  - [ ] Crear tests unitarios para validar la generación de tablas
  - [ ] Probar con datos reales para confirmar la corrección

**✅ RESULTADO:** Se identificó y corrigió un bug crítico en `_generate_editions_need_publication_table` donde había 6 celdas de datos pero solo 5 cabeceras. La función ahora muestra correctamente los datos alineados con las cabeceras.

#### 1.2 Eliminación de Riesgos de Inyección SQL ✅ **COMPLETADO**
- [x] **Identificar todas las consultas con f-strings**
  - [x] `_build_technical_users_query` - Identificadas vulnerabilidades en líneas 361, 368
  - [x] `_get_editions_need_publication_data` - Corregida línea 1085
  - [x] `_get_expired_editions_data` - Corregida línea 1501
  - [x] Otras funciones que construyan SQL dinámicamente

- [x] **Refactorizar consultas para usar parámetros**
  - [x] Convertir f-strings a consultas parametrizadas
  - [x] Adaptar el formato de fechas para Access (`#mm/dd/yyyy#`)
  - [x] Verificar que todas las consultas funcionen correctamente
  - [x] Crear tests para validar las consultas parametrizadas

**✅ RESULTADO:** Se eliminaron todas las vulnerabilidades de inyección SQL:
- Corregida `_get_editions_need_publication_data`: Reemplazado `#{future_date_15_days}#` por parámetro seguro
- Corregida `_get_expired_editions_data`: Reemplazado `#{current_date}#` por parámetro seguro
- Corregidas líneas 361 y 368 en consultas de planes de mitigación y contingencia mediante consultas parametrizadas

#### 1.3 Mejorar Manejo de Errores Silenciosos - **PENDIENTE**
- [ ] **Revisar función `get_distinct_technical_users`**
  - [ ] Analizar el manejo actual de excepciones
  - [ ] Implementar logging más detallado para errores
  - [ ] Considerar estrategias de recuperación de errores
  - [ ] Alertar cuando falten usuarios en el procesamiento

- [ ] **Implementar validaciones adicionales**
  - [ ] Verificar que se obtengan todos los usuarios esperados
  - [ ] Añadir métricas de completitud en los logs
  - [ ] Crear alertas para fallos parciales

---

## 📋 TAREAS PENDIENTES

### Fase 1: Corrección de Bugs Críticos 🚨 - **PENDIENTE DE COMPLETAR**

#### 1.2 Eliminación de Riesgos de Inyección SQL ✅ **COMPLETADO**
- [x] **Corregir vulnerabilidades restantes identificadas**
  - [x] Línea 361: `f"TbRiesgosPlanMitigacionDetalle.FechaFinPrevista <= #{current_date}#"` - Convertido a consulta parametrizada
  - [x] Línea 368: `f"TbRiesgosPlanContingenciaDetalle.FechaFinPrevista <= #{current_date}#"` - Convertido a consulta parametrizada
  - [x] Verificar que no existan otras vulnerabilidades similares

### Fase 2: Optimización de Rendimiento 🚀

#### 2.1 Optimización de Consultas a Base de Datos
- [x] **Refactorizar `get_distinct_technical_users`** ✅ **COMPLETADO**
  - [x] Analizar las 8 consultas actuales
  - [x] Diseñar una consulta UNION que las combine
  - [x] Adaptar la consulta UNION para Access
  - [x] Probar rendimiento antes y después
  - [x] Validar que se obtengan los mismos resultados
  - [x] Implementar método de fallback con las 8 consultas originales

- [x] **Optimizar filtrado por fechas** ✅ **COMPLETADO**
  - [x] Identificar funciones que filtran en Python
    - [x] `_get_mitigation_actions_reschedule_data`
    - [x] `_get_contingency_actions_reschedule_data`
  - [x] Mover filtros de fecha a cláusulas WHERE
  - [x] Usar parámetros para las fechas
  - [x] Medir mejora en rendimiento
  - [x] Convertido filtrado de fecha de Python a SQL usando formato Access (#mm/dd/yyyy#)
  - [x] Añadido parámetro `current_date` a las consultas SQL
  - [x] Eliminado procesamiento posterior de fechas en Python
  - [x] Mantenida compatibilidad con formato de fechas de Access

- [x] **Implementar caché** ✅ **COMPLETADO**
  - [x] Añadir atributos de caché para usuarios técnicos, calidad y administradores
  - [x] Implementar caché en `get_distinct_technical_users()`
  - [x] Crear funciones `get_quality_users()` y `get_admin_users()` con caché
  - [x] Sistema de caché similar al implementado en `brass_manager.py` y `no_conformidades_manager.py`


### Fase 3: Refactorización y Mejora de Código 🔧

#### 3.1 Creación de Sistema Genérico de Tablas HTML
- [ ] **Diseñar función genérica de tablas**
  - [ ] Definir interfaz: `_generate_generic_table(title, headers, data, data_keys)`
  - [ ] Implementar lógica genérica para generar HTML
  - [ ] Incluir soporte para clases CSS (días, estados, etc.)
  - [ ] Manejar casos especiales (enlaces, formateo de fechas)

- [ ] **Migrar funciones existentes**
  - [ ] Listar todas las funciones `_generate_*_table` actuales
  - [ ] Migrar una por una a la función genérica
  - [ ] Validar que el HTML generado sea idéntico
  - [ ] Eliminar funciones obsoletas



#### 3.2 Centralización de Lógica de Ejecución
- [ ] **Simplificar `main.py`**
  - [ ] Analizar lógica duplicada entre `main.py` y `RiesgosManager`
  - [ ] Mover toda la lógica de ejecución a `RiesgosManager`
  - [ ] Simplificar `main.py` para solo parsear argumentos
  - [ ] Usar `run_daily_tasks()` como punto de entrada principal

- [ ] **Mejorar método `run_daily_tasks`**
  - [ ] Añadir parámetros para flags `force`
  - [ ] Centralizar toda la lógica de decisión de ejecución
  - [ ] Mejorar logging y reportes de estado

### Fase 4: Mejoras de Calidad y Mantenibilidad 📋

#### 4.1 Limpieza de Código
- [ ] **Eliminar comentarios confusos**
  - [ ] Revisar comentarios como `// ========== FUNCIONES FALTANTES ==========`
  - [ ] Actualizar o eliminar comentarios obsoletos
  - [ ] Añadir documentación clara donde sea necesario

- [ ] **Estandarizar aplicación de clases CSS**
  - [ ] Revisar uso inconsistente de `_get_dias_class`
  - [ ] Estandarizar aplicación de clases en todas las tablas
  - [ ] Documentar convenciones de CSS

#### 4.2 Mejora de Estructura del Proyecto
- [ ] **Evaluar estructura de paquetes**
  - [ ] Revisar uso de `sys.path.insert(0, ...)`
  - [ ] Considerar reestructurar como paquete instalable
  - [ ] Actualizar imports si es necesario

#### 4.3 Testing y Validación
- [ ] **Crear tests unitarios**
  - [ ] Tests para generación de tablas HTML
  - [ ] Tests para consultas SQL parametrizadas
  - [ ] Tests para lógica de fechas y filtros
  - [ ] Tests para manejo de errores

- [ ] **Tests de integración**
  - [ ] Probar con bases de datos locales
  - [ ] Validar generación completa de informes
  - [ ] Verificar envío de correos (mock)

### Fase 5: Documentación y Despliegue 📚

#### 5.1 Documentación
- [ ] **Actualizar documentación técnica**
  - [ ] Documentar nuevas funciones genéricas
  - [ ] Actualizar diagramas de flujo si existen
  - [ ] Documentar cambios en la base de datos

- [ ] **Crear guía de migración**
  - [ ] Documentar cambios realizados
  - [ ] Crear checklist de validación post-migración
  - [ ] Documentar rollback si es necesario

#### 5.2 Despliegue y Validación
- [ ] **Pruebas en entorno de desarrollo**
  - [ ] Ejecutar todas las tareas con datos reales
  - [ ] Validar generación de informes
  - [ ] Verificar rendimiento mejorado

- [ ] **Despliegue gradual**
  - [ ] Desplegar en entorno de pruebas
  - [ ] Monitorear logs y errores
  - [ ] Validar con usuarios finales
  - [ ] Desplegar en producción

---

## 📊 Métricas de Éxito

### Rendimiento
- [ ] **Tiempo de ejecución reducido en al menos 30%**
- [ ] **Reducción de consultas SQL de 8 a 1 en `get_distinct_technical_users`**
- [ ] **Eliminación de filtrado en Python para consultas de fecha**

### Calidad de Código
- [ ] **Reducción de líneas de código duplicado en al menos 50%**
- [ ] **Cobertura de tests unitarios > 80%**
- [x] **Eliminación completa de riesgos de SQL injection** - **COMPLETADO** ✅

### Mantenibilidad
- [ ] **Función genérica de tablas implementada y en uso**
- [ ] **Lógica de ejecución centralizada en `RiesgosManager`**
- [ ] **Documentación actualizada y completa**

---

## 🎯 RESUMEN DE LOGROS HASTA LA FECHA

### ✅ Completado:
1. **Bug crítico corregido**: Inconsistencia en tabla HTML de ediciones que necesitan publicación
2. **Vulnerabilidades de seguridad eliminadas**: Todas las 4 vulnerabilidades de inyección SQL corregidas ✅
3. **Código más seguro**: Implementación completa de consultas parametrizadas para fechas
4. **Tests unitarios**: Creados para validar las consultas parametrizadas

### 🔄 En progreso:
1. **Optimización de rendimiento**: Preparando Fase 2 del plan de mejoras
2. **Refactorización**: Planificando sistema genérico de tablas HTML

### 📈 Próximos pasos prioritarios:
1. Optimizar rendimiento de consultas (Fase 2) - Refactorizar `get_distinct_technical_users`
2. Implementar sistema genérico de tablas HTML (Fase 3)
3. Mejorar manejo de errores silenciosos

---

## Notas y Consideraciones

### Dependencias
- Verificar compatibilidad con Access para consultas UNION
- Evaluar impacto en rendimiento de la base de datos
- Considerar limitaciones de memoria para cache

### Riesgos
- Cambios en consultas SQL pueden afectar resultados
- Refactorización de HTML puede cambiar apariencia
- Centralización de lógica puede introducir nuevos bugs

### Cronograma Estimado
- **Fase 1 (Crítica)**: 1-2 semanas - **✅ COMPLETADO**
- **Fase 2 (Optimización)**: 1 semana  
- **Fase 3 (Refactorización)**: 2-3 semanas
- **Fase 4 (Calidad)**: 1 semana
- **Fase 5 (Documentación)**: 1 semana

**Total estimado**: 6-8 semanas
**Progreso actual**: ~35% completado

---

*Última actualización: Diciembre 2024*
*Estado: En progreso - Fase 1 parcialmente completada*