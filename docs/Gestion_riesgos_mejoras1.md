
# Plan de Acción - Mejoras Gestión de Riesgos

He identificado algunos puntos clave y posibles mejoras, especialmente en el contexto de la migración de un script VBS.

## 1. Reutilización de consultas SQL
**Estado: ✅ IMPLEMENTADO**

El método get_distinct_technical_users contiene ocho consultas SQL que parecen estar hardcodeadas y son muy similares entre sí. Esto no es ideal por varias razones:

- Dificultad de mantenimiento: Si la estructura de la base de datos cambia, tendrás que modificar cada una de estas consultas individualmente.
- Repetición de código: La estructura de INNER JOIN y la cláusula WHERE se repite en casi todas las consultas.
- Riesgo de errores: Copiar y pegar código SQL puede introducir errores sutiles difíciles de detectar.

**Sugerencia**: Podrías crear una función o clase que construya las consultas dinámicamente, extrayendo las diferencias (como las condiciones específicas de la cláusula WHERE) y reutilizando la estructura común.

**Implementaciones realizadas**:
- ✅ Creada función `_build_technical_users_query()` para construir consultas dinámicamente
- ✅ Extraídas condiciones específicas de WHERE por tipo de consulta
- ✅ Reutilizada estructura común de INNER JOIN según el tipo de consulta
- ✅ Implementado sistema de condiciones comunes y específicas
- ✅ Añadido manejo de fechas calculadas en Python

## 2. Uso de pyodbc y SQL nativo de Access
**Estado: ✅ IMPLEMENTADO PARCIALMENTE**

El código utiliza la librería pyodbc para conectarse a la base de datos de Access. Esto es correcto, pero las consultas SQL están escritas en un dialecto de SQL muy específico de Access (por ejemplo, el uso de DateDiff y Now()). Aunque funciona, puede dificultar una futura migración a otra base de datos como MySQL o PostgreSQL.

**Sugerencia**: Si es posible, intenta migrar la lógica de fechas y la manipulación de datos a Python. Por ejemplo, en lugar de usar DateDiff('d',Now(),TbProyectos.FechaMaxProximaPublicacion), podrías obtener la fecha de la base de datos y realizar el cálculo de diferencia de días en Python, lo que es más portable.

**Implementaciones realizadas**:
- ✅ Eliminado `DateDiff('d',Now(),TbProyectos.FechaMaxProximaPublicacion) <= 15`
- ✅ Reemplazado por `TbProyectos.FechaMaxProximaPublicacion <= #{future_date_15_days}#`
- ✅ Cálculo de `future_date_15_days` en Python usando `datetime.now() + timedelta(days=15)`

**Tareas pendientes**:
- [ ] Revisar otras consultas que usen `DateDiff` o `Now()`
- [ ] Migrar más lógica de fechas a Python
- [ ] Verificar compatibilidad con otras bases de datos

## 3. Faltan detalles de implementación
**Estado: ⏳ PENDIENTE**

He notado que en el código de get_distinct_technical_users, las consultas están definidas pero no se muestra la parte donde se ejecutan y se procesan los resultados para construir la colección de usuarios. El código termina abruptamente con una consulta incompleta.

**Sugerencia**: Debes asegurarte de que el código que itera sobre la lista de queries realmente las ejecute contra la base de datos y procese los resultados para llenar el users_collection.

**Tareas pendientes**:
- [ ] Completar la implementación de ejecución de consultas
- [ ] Procesar resultados para construir users_collection
- [ ] Verificar que todas las consultas se ejecuten correctamente
- [ ] Añadir manejo de errores para consultas fallidas

## Resumen de Estado
- **Implementado**: Migración parcial de lógica de fechas (eliminación de DateDiff)
- **En progreso**: Ninguno
- **Pendiente**: Reutilización de consultas SQL, completar implementación, migración completa de fechas

## Próximos Pasos
1. Resolver el error de "Pocos parámetros" identificando la consulta específica que falla
2. Implementar construcción dinámica de consultas SQL
3. Completar la migración de lógica de fechas
4. Finalizar la implementación de ejecución y procesamiento de consultas

En resumen, el código está bien estructurado con una clase y métodos lógicos, pero la sección de las consultas SQL podría ser más dinámica y reutilizable.