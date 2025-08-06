GEMINI_MODEL=gemini-2.5-pro

Siempre has de hablar en español

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

</Modulo de No Conformidades>