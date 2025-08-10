## Reglas del Proyecto AGEDYS (Refactor)

Esta guía consolida las normas para mantener y ampliar el módulo refactorizado de **AGEDYS** evitando errores de código y SQL.

---
### 1. Fuentes de Verdad
* Estructura de datos: `dbs-locales/AGEDYS_DATOS.md` (consultar antes de cualquier cambio de SQL).
* Código VBScript legacy de referencia histórica: `legacy/AGEDYS.VBS` (solo para contrastar lógica; NO copiar literalmente).
* Patrón validado: **Task -> Manager -> Common Framework** (logging, DB, HTML, email).

---
### 2. Principios Arquitectónicos
1. El `Task` orquesta: decide si ejecutar, agrupa usuarios, registra correos.
2. El `Manager` encapsula TODA la lógica de negocio y consultas SQL (ningún SQL en el Task).
3. El **framework común** (carpeta `common/`): logging, acceso BBDD (`AccessDatabase`), utilidades HTML, email.
4. Ningún método debe devolver `None`; usar lista vacía o dict controlado.
5. Evitar side-effects fuera de Task (no enviar/registrar correos en Manager).

---
### 3. Convenciones de SQL (MS Access / Jet)
* Paréntesis en JOIN complejos: anidar como `(((A INNER JOIN B ...) LEFT JOIN C ...) INNER JOIN D ...)`.
* Booleanos: usar `True` / `False` (o `= False` en condiciones existentes) según ya estandarizado.
* NULL: siempre `IS NULL` / `IS NOT NULL` (no comparar con `= ''` salvo campos texto).
* Orden recomendado de filtros: primero `ELIMINADO=False`, luego condiciones de estado y finally nulos.
* Usar alias cortos (`p`, `np`, `fd`, `vf`, `vg`) consistentes entre consultas.
* Cuando se combinan múltiples subconsultas para usuarios: mantener consistencia de alias para facilitar refactor.
* Para consultas parametrizadas futuras: utilizar `?` y pasar tupla de parámetros desde `_execute_section`.

Errores comunes evitados:
| Problema | Causa | Prevención |
|---------|-------|-----------|
| Syntax error in JOIN | Paréntesis mal balanceados | Copiar patrón de otras consultas válidas y validar counts de `(`/`)` |
| Campo no encontrado | Nombre distinto a esquema | Verificar en `AGEDYS_DATOS.md` antes de ejecutar |
| Resultados duplicados | Falta de `DISTINCT` | Añadir `SELECT DISTINCT` en queries de usuarios |
| Facturas mal enlazadas | JOIN por campo incorrecto (`IDFactura` vs `NFactura` + `NPEDIDO`) | Seguir firma usada en consultas consolidadas |

---
### 4. Logging
* Usar `self.logger.info` con `extra={'event': 'agedys_section_fetch', 'section': <nombre>, 'rows': len(rows)}` para consultas.
* Errores de subconsultas: `self.logger.error(f"Error subconsulta usuarios({idx}): {e}")` y continuar (fail-soft).
* Nunca silenciar excepciones: capturar, loggear, devolver estructura vacía.
* Prefijo de logger del Task: `Task.AGEDYS`; del manager reutiliza ese logger inyectado.

---
### 5. Estilo de Código Python
* Tipado: anotar retornos (`List[Dict[str, Any]]`, `str | None`) salvo casos triviales.
* Métodos internos con `_` (`_execute_section`, `_run_merge_queries`).
* Evitar lógica duplicada: factorizar bloques repetidos.
* Mantener nombres descriptivos alineados con el correo generado (secciones HTML).

---
### 6. Generación de Informes
* El Manager solo devuelve estructuras de datos; la Task decide si generar HTML vacío o no.
* Evitar generar múltiples informes técnicos vacíos: filtrar usuarios sin ninguna sección poblada (pendiente de micro-optimización opcional).
* Secciones alias (compatibilidad): mantener wrappers `pragma: no cover` cuando se renombre un método público.

---
### 7. Checklist Antes de Confirmar Cambios
1. ¿La nueva consulta respeta alias y patrón de JOIN?  
2. ¿Campos verificados contra `AGEDYS_DATOS.md`?  
3. ¿Logging añadido (INFO para éxito, ERROR para fallo)?  
4. ¿Retornos sin `None`?  
5. ¿Tests necesitan actualización (nombres de métodos o estructura de retorno)?  
6. ¿Cobertura sigue >= objetivo tras nuevos métodos (cuando se ejecute)?

---
### 8. Ejemplo de Plantilla de Nueva Sección
```python
def get_dpds_ejemplo_agrupado(self) -> List[Dict[str, Any]]:
	query = """
		SELECT p.CODPROYECTOS, p.PETICIONARIO
		FROM TbProyectos p
		WHERE p.ELIMINADO = False AND p.AlgunaCondicion IS NOT NULL
	"""
	return self._execute_section(query, 'dpds_ejemplo_agrupado')
```

---
### 9. Roadmap de Mejoras Pendientes (Opcional)
* Filtrar usuarios sin datos antes de generar informe técnico.
* Añadir parametrización y tests para nuevas variantes de usuario (si se requiere 100% paridad VBScript).
* Normalizar formato de importes (centralizar en util).
* Instrumentación de métricas (contadores por sección) para observabilidad futura.

---
### 10. Resumen
Sigue este documento para minimizar errores de SQL y mantener coherencia arquitectónica. Cualquier desviación debe justificarse en el PR con referencia a un caso de negocio o limitación de Access.
