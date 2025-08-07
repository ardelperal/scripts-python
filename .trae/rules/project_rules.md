Siempre que tengas dudas de como usar los sql en pruebas o en refactorizaciones mira el archivo original de donde proviene
Siempre revisa el SQL para que sea compatible con access, SELECT TOP 5, o cosas como CASE en where no están permitidas
Antes de implementar una nueva función mira a ver si ya está en la parte común del proyecto
Los tests de integración siempre que sea posible quiero que tengan interacción real con las bases de datos, pero siempre las locales independientemente del entorno que esté en .env
Revisa las dependencias que no tengan vulnerabilidades críticas
Nunca dejes placeholders en las funcionalidades. 
Nunca hagas pruebas de sql injections en este proyecto
Recuerda que la shell que siempre uso es powher shell con lo que no funcionan concatenar acciones con &&

<Modulo de No Conformidades>
Lógica Completa para el Proceso de Notificación por Correo en Módulo de No Conformidades
1) Tareas para Miembros de Calidad
Se generan 4 consultas SQL principales que deben obtener distintos conjuntos de datos que alimentarán las tablas HTML que forman el cuerpo del correo:

1.1.a) ARs próximas a caducar o caducadas (sin fecha fin real):

sql
SELECT DISTINCT DateDiff('d',Now(),[FPREVCIERRE]) AS DiasParaCierre, 
    TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
    TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE
FROM TbNoConformidades 
INNER JOIN (TbNCAccionCorrectivas 
  INNER JOIN TbNCAccionesRealizadas 
  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) 
ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad 
WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL AND 
      DateDiff('d',Now(),[FPREVCIERRE]) < 16;
1.1.b) No Conformidades resueltas pendientes de Control de Eficacia:

sql
SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD,  
    TbNoConformidades.FECHACIERRE, TbNoConformidades.FechaPrevistaControlEficacia,
    DateDiff('d',Now(),[FechaPrevistaControlEficacia]) AS Dias
FROM TbNoConformidades
INNER JOIN (TbNCAccionCorrectivas 
  INNER JOIN TbNCAccionesRealizadas 
  ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
WHERE DateDiff('d',Now(),[FechaPrevistaControlEficacia]) < 30
  AND TbNCAccionesRealizadas.FechaFinReal IS NOT NULL
  AND TbNoConformidades.RequiereControlEficacia = 'Sí'
  AND TbNoConformidades.FechaControlEficacia IS NULL;
1.1.c) No Conformidades sin Acciones Correctivas registradas:

sql
SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico,
    TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, 
    TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE
FROM TbNoConformidades
LEFT JOIN TbNCAccionCorrectivas 
  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad
WHERE TbNCAccionCorrectivas.IDNoConformidad IS NULL;
1.1.d) ARs para Replanificar (fecha prevista cercana o pasada, sin fecha fin real):

sql
SELECT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, 
    TbNCAccionCorrectivas.AccionCorrectiva AS Accion, TbNCAccionesRealizadas.AccionRealizada AS Tarea,
    TbUsuariosAplicaciones.Nombre AS Tecnico, TbNoConformidades.RESPONSABLECALIDAD, 
    TbNCAccionesRealizadas.FechaFinPrevista,
    DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) AS Dias
FROM (TbNoConformidades 
  INNER JOIN (TbNCAccionCorrectivas 
    INNER JOIN TbNCAccionesRealizadas 
    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
LEFT JOIN TbUsuariosAplicaciones 
  ON TbNCAccionesRealizadas.Responsable = TbUsuariosAplicaciones.UsuarioRed
WHERE DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) < 16 
  AND TbNCAccionesRealizadas.FechaFinReal IS NULL;
Una vez se obtienen los datos de cada consulta, se generan tablas HTML con esa información.

El cuerpo del correo para este grupo será la concatenación (o conjunto) de estas tablas HTML.

Destinatarios: Correos electrónicos de los Miembros de Calidad responsables (se obtienen de manera común / previa).

Asunto: "Informe Tareas No Conformidades (No Conformidades)"

Finalmente, se usa la función común de registro de correos para guardar este correo en la base de datos.

2) Tareas para Técnicos
Se detectan los técnicos que tienen al menos una NC activa con AR pendiente mediante esta consulta:

sql
SELECT DISTINCT TbNoConformidades.RESPONSABLETELEFONICA
FROM (TbNoConformidades
  INNER JOIN TbNCAccionCorrectivas ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
  INNER JOIN TbNCAccionesRealizadas ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva
WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL 
  AND TbNoConformidades.Borrado = False 
  AND DateDiff('d', Now(), [FechaFinPrevista]) <= 15;
Por cada técnico (variable p_Usuario = RESPONSABLETELEFONICA) se deben generar tres consultas SQL distintas, agregando el filtro de ese usuario:

2.1.a) ARs con fecha fin prevista a 8-15 días, sin fecha fin real, y que no estén ya avisadas con IDCorreo15:

sql
SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada,
    TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada,
    TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista,
    TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar,
    TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico
FROM ((TbNoConformidades 
  LEFT JOIN TbUsuariosAplicaciones ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed)
  INNER JOIN (TbNCAccionCorrectivas 
    INNER JOIN (TbNCAccionesRealizadas 
      LEFT JOIN TbNCARAvisos ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR)
    ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva)
  ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad)
LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente
WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
  AND DateDiff('d',Now(),[FechaFinPrevista]) BETWEEN 8 AND 15
  AND TbNCARAvisos.IDCorreo15 IS NULL
  AND TbNoConformidades.RESPONSABLETELEFONICA = '" & p_Usuario & "';
2.1.b) ARs con fecha fin prevista a 1-7 días, sin fecha fin real, sin aviso previo IDCorreo7:

Misma consulta que 2.1.a cambiando el rango y campo de control a IDCorreo7:

sql
WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
  AND DateDiff('d',Now(),[FechaFinPrevista]) > 0 AND DateDiff('d',Now(),[FechaFinPrevista]) <= 7
  AND TbNCARAvisos.IDCorreo7 IS NULL
  AND TbNoConformidades.RESPONSABLETELEFONICA = '" & p_Usuario & "';
2.1.c) ARs con fecha fin prevista 0 o negativa, sin fecha fin real, sin aviso previo IDCorreo0:

sql
WHERE TbNCAccionesRealizadas.FechaFinReal IS NULL
  AND DateDiff('d',Now(),[FechaFinPrevista]) <= 0
  AND TbNCARAvisos.IDCorreo0 IS NULL
  AND TbNoConformidades.RESPONSABLETELEFONICA = '" & p_Usuario & "';
Después de ejecutar estas consultas para el usuario, generas las tablas HTML correspondientes (una tabla para cada consulta, si hay resultados).

Condiciones del registro de correo para técnicos:

Si no hay registros en ninguna de las 3 consultas, no se registra correo.
el campo Aplicacion =NoConformidades
El caxmpo Asunto=Tareas de Acciones Correctivas a punto de caducar o caducadas (No Conformidades)
El cuerpo del correo es la concatenación de las tablas HTML generadas.

Destinatario: Correo del usuario técnico (p_Usuario).

Destinatarios en copia solo si existen datos en consultas 2.1.b y 2.1.c para ese usuario.

Para ello, se debe obtener los correos electrónicos de los responsables de calidad relacionados con esas NC y AR que aparecen en esas consultas.

Registro de correo:

Se usa la función de registro común para crear el correo (que te devuelve un IDCorreo).

Para cada conjunto de resultados (2.1.a, 2.1.b y 2.1.c) que haya registrado datos, debes crear un registro en TbNCARAvisos asociando:

El IDCorreo generado

El ID de AR correspondiente

El tipo de aviso (IDCorreo15, IDCorreo7 o IDCorreo0) para evitar que se reenvíe nuevamente el mismo aviso.

Al finalizar el bucle para cada usuario (técnico), guardar en la tabla correspondiente (me imagino que con los datos del envío y posibles estados para seguimiento).

Recomendación de Pasos para Implementación o Para Dar Instrucciones a la IA
Obtener y generar el correo para Miembros de Calidad:

Ejecutar las 4 consultas (1.1.a a 1.1.d).

Crear las tablas HTML para cada resultado no vacío.

Si hay al menos una tabla, componer el cuerpo del correo concatenando estas tablas.

Enviar/Registrar el correo con todos los Miembros de Calidad como destinatarios.

Para técnicos:

Ejecutar la consulta de técnicos con NC activas.

Para cada técnico obtenido:

Ejecutar las 3 consultas específicas con filtro por ese técnico.

Crear tablas HTML para los resultados de cada consulta.

Componer cuerpo concatenando las tablas no vacías.

Si no hay tablas vacías, no registrar correo y pasar al siguiente técnico.

Si se registra correo:

Añadir en copia a responsables de calidad si hay datos en 2.1.b o 2.1.c.

Registrar en TbNCARAvisos la relación entre el correo y las ARs para las categorías correspondientes (no duplicar avisos).

Finalizar ciclo de técnicos:

Guardar log o estado que indique que se ha procesado el envío.

</Modulo de Expedientes>
 Análisis del Script: TareaExpedientes.vbs
Resumen General
Este script tiene como objetivo principal realizar una tarea diaria de supervisión (ExpDiario) sobre una base de datos de expedientes. Su función es identificar y recopilar información sobre expedientes que cumplen ciertas condiciones críticas (próximos a vencer, con datos incompletos, en fases estancadas, etc.).

Una vez recopilados los datos, el script genera un informe consolidado en formato HTML igual que lo hiciste con el móduo de No Conformidades y lo registra en una base de datos para su posterior envío por correo electrónico a un grupo de usuarios definidos como "tramitadores".

Flujo de Ejecución
La ejecución del script es controlada por la función Lanzar, que actúa como el punto de entrada principal.

1. Punto de Entrada: Lanzar()
Esta función orquesta todo el proceso y sigue los siguientes pasos lógicos:

Define Rutas y Contraseñas: Establece las rutas de red a las bases de datos de Access (.accdb) y la contraseña de acceso (m_Pass).

Conexión a BBDD de Tareas: Se conecta a la base de datos Tareas_datos1.accdb para gestionar el estado de la ejecución.

Verificación de Tarea: Llama a la función TareaRealizada() para comprobar si la tarea ExpDiario ya se ha ejecutado en el día actual.

Si la tarea ya fue realizada, el script finaliza su ejecución para evitar duplicidad.

Si no se ha realizado, el script continúa.

Ejecución de la Tarea Principal:

Se conecta a la base de datos principal de expedientes: Expedientes_datos.accdb.

Carga los estilos CSS desde un archivo externo (CSS.txt) para dar formato al informe HTML.

Obtiene las listas de correos electrónicos de los administradores (getCadenaCorreoAdministradores) y de los tramitadores (getCadenaCorreoTareas).

Llama a la función RealizarTarea() para que genere el informe.

Una vez que RealizarTarea finaliza, cierra la conexión a la base de datos de expedientes.

Registro de Tarea Completada: Llama a RegistrarTarea() para actualizar la base de datos de tareas, marcando ExpDiario como completada para la fecha actual.

Cierre de Conexiones: Finaliza la conexión con la base de datos de tareas.

Núcleo del Proceso: RealizarTarea()
Esta es la función central donde se recopilan todos los datos y se construye el informe HTML.

Recopilación de Datos: La función llama a varias sub-rutinas (getCol...) para ejecutar consultas SQL específicas contra la base de datos de expedientes. Cada una de estas funciones devuelve un diccionario (Scripting.Dictionary) con los expedientes que cumplen una condición. Las comprobaciones realizadas son:

getColAPuntoDeFinalizar: Busca expedientes cuyo contrato finaliza en los próximos 15 días.

getColHitosAPuntoDeFinalizar: Busca hitos de expedientes cuya fecha está programada para los próximos 15 días.

getColEstadoDesconocido: Identifica expedientes cuyo campo Estado es 'Desconocido'.

getColAdjudicadosSinContrato: Localiza expedientes marcados como adjudicados pero que no tienen datos de contrato (fecha de inicio, fin o meses de garantía).

getColAdjudicadosTSOLSinCodS4H: Busca expedientes adjudicados a la entidad jurídica 'TSOL' que no tienen asignado un código CodS4H.

getColsEnFaseOfertaPorMuchoTiempo: Detecta expedientes que llevan más de 45 días en fase de oferta sin haber sido adjudicados, perdidos o desestimados.

Construcción del Informe HTML:

Crea una cabecera HTML básica usando DameCabeceraHTML.

Para cada diccionario de datos obtenido en el paso anterior, llama a una función HTMLTabla... correspondiente (ej: HTMLTablaAPuntoDeFinalizar).

Cada función HTMLTabla... genera una tabla HTML con los datos del diccionario, incluyendo cabeceras y filas formateadas.

Todas las tablas HTML se concatenan en una única variable de texto (m_mensaje), separadas por saltos de línea.

Registro del Correo:

Finalmente, la función llama a RegistrarCorreo, pasándole el asunto del informe, el cuerpo HTML (m_mensaje) y la lista de destinatarios (tramitadores). Esta función inserta un nuevo registro en la tabla TbCorreosEnviados de la base de datos de tareas.

Funciones Auxiliares Clave
Conn(p_URL, p_Pass): Función genérica que establece y abre una conexión ADODB a una base de datos Access utilizando el proveedor Microsoft.ACE.OLEDB.12.0.

TareaRealizada() / UltimaEjecucion() / RegistrarTarea(): Conjunto de funciones que gestionan el ciclo de vida de la tarea. Comprueban la última fecha de ejecución en TbTareas y la actualizan para asegurar que el proceso se ejecute solo una vez al día.

getCadenaCorreo...(): Funciones que ejecutan consultas SQL sobre la tabla TbUsuariosAplicaciones para obtener cadenas de correos electrónicos separadas por punto y coma (;), ya sea de administradores o de usuarios específicos de la aplicación.

getCol...(): Funciones de consulta. Cada una tiene una consulta SQL específica para filtrar expedientes según las reglas de negocio descritas anteriormente.

HTMLTabla...(): Funciones de formato. Toman un diccionario de datos y lo transforman en una cadena de texto que representa una tabla HTML, aplicando clases CSS para el estilo.

RegistrarCorreo(...): Inserta los detalles del correo generado (destinatarios, asunto, cuerpo) en la tabla TbCorreosEnviados. Obtiene un nuevo ID para el correo usando la función getIDCorreo.
<Modulo Expedientes>

<Gestión de Riesgos>
Lógica de Negocio del Proceso Automatizado de Gestión de Riesgos
Objetivo Principal del Proceso
El propósito de este proceso automatizado es actuar como un supervisor digital del sistema de Gestión de Riesgos. Su función es asegurar que las tareas, revisiones y plazos clave no se pasen por alto, garantizando que tanto los responsables de los proyectos (Técnicos) como el equipo de supervisión (Calidad) cumplan con sus responsabilidades de manera oportuna.

El sistema se encarga de enviar recordatorios y resúmenes de estado por correo electrónico para mantener el flujo de trabajo activo y evitar cuellos de botella.

Audiencias y Frecuencia de los Informes
El proceso identifica dos roles de negocio principales y les envía informes con distinta periodicidad y contenido:

Técnicos (Responsables de Proyecto): Reciben un informe semanal. Este informe es personalizado y solo contiene las tareas que están bajo la responsabilidad directa de cada técnico.

Equipo de Calidad: Reciben dos tipos de informes:

Un informe semanal detallado con las tareas pendientes de revisión y aprobación, desglosado por cada miembro del equipo.

Un informe mensual de alto nivel que ofrece una visión general del estado de todos los proyectos para todo el equipo de Calidad.

Lógica de Negocio por Audiencia
1. Para los Técnicos (Informe Semanal Personalizado)
El objetivo de este informe es impulsar al técnico a completar las acciones que tiene pendientes para que los proyectos avancen. Se le notifica sobre:

Proyectos que necesitan acción inmediata:

Ediciones de proyectos que están listas y deben ser propuestas a Calidad para su publicación oficial.

Propuestas de publicación que el equipo de Calidad ha rechazado, indicando que el técnico debe revisarlas y corregirlas.

Decisiones sobre riesgos que requieren justificación:

Riesgos que el técnico ha decidido "aceptar", pero para los cuales no ha documentado una justificación clara.

Riesgos que ha decidido "retirar", pero sin explicar el motivo del retiro.

Acciones rechazadas que necesitan ser reevaluadas:

Notificaciones de que una justificación para aceptar o retirar un riesgo ha sido rechazada por Calidad, lo que obliga al técnico a proponer una nueva solución.

Planes de acción vencidos:

Alertas sobre planes de mitigación o contingencia cuyas fechas de finalización ya han pasado y que, por tanto, deben ser replanificados.

2. Para el Equipo de Calidad (Informe Semanal Detallado)
Este informe está diseñado para que el equipo de Calidad pueda supervisar y validar el trabajo de los técnicos, asegurando el cumplimiento de los estándares. Cada miembro de Calidad recibe un resumen de:

Tareas de revisión pendientes:

Proyectos que los técnicos han propuesto para publicar y que están esperando el visto bueno de Calidad.

Riesgos que los técnicos han aceptado o retirado y que están pendientes de ser visados (aprobados) por Calidad.

Riesgos que se han materializado (han ocurrido) y sobre los cuales Calidad debe decidir si se abren como una "No Conformidad" formal.

Riesgos identificados por los técnicos que necesitan ser clasificados ("retipificados") usando la biblioteca oficial de riesgos de la empresa.

Alertas críticas sobre plazos:

Proyectos cuya fecha límite para ser publicados está a punto de vencer (en los próximos 15 días).

Proyectos cuya fecha límite de publicación ya ha sido superada, requiriendo atención urgente.

3. Para el Equipo de Calidad (Informe Mensual General)
Este informe tiene un propósito más estratégico y de reporte. No se enfoca en tareas individuales, sino en dar una visión global del estado de la gestión de riesgos. Contiene:

Un resumen de todos los proyectos que están actualmente en proceso de revisión por parte de Calidad.

Una fotografía general de todos los proyectos activos, indicando cuáles están en riesgo por plazos ajustados o ya vencidos.

Un listado de los proyectos que han sido cerrados satisfactoriamente en los últimos 30 días, sirviendo como un reporte de actividad completada.

Conclusión de la Lógica
En esencia, este proceso automatizado implementa las reglas de negocio de la compañía para la gestión de riesgos. Actúa como un mecanismo de control que:

Asigna y recuerda responsabilidades a cada rol.

Vigila los plazos para evitar retrasos.

Asegura la trazabilidad al exigir justificaciones y aprobaciones formales.

Proporciona visibilidad del estado de los proyectos a los diferentes niveles de la organización.
</Gestión de Riesgos>