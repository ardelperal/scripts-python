Siempre que tengas dudas de como usar los sql en pruebas o en refactorizaciones mira el archivo original de donde proviene
Siempre revisa el SQL para que sea compatible con access, SELECT TOP 5, o cosas como CASE en where no están permitidas
Antes de implementar una nueva función mira a ver si ya está en la parte común del proyecto
Los tests de integración siempre que sea posible quiero que tengan interacción real con las bases de datos, pero siempre las locales independientemente del entorno que esté en .env
Revisa las dependencias que no tengan vulnerabilidades críticas
Nunca dejes placeholders en las funcionalidades. 
Nunca hagas pruebas de sql injections en este proyecto
Recuerda que la shell que siempre uso es powher shell con lo que no funcionan concatenar acciones con &&
Los where de access que contengan fechas el formato que espera es #mm/dd/yyyy#
<IMPORTANTE>
siempre que puedas usa el MCP access-schema-extractor para obtener el nombre y el esquema de la gbase de datos, has de proporcionarle la ruta y la contraseña y te devuelve un JSON con toda la estructura
</IMPORTANTE>
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

# Estructura de la Base de Datos y Relaciones

Este documento detalla la estructura de la base de datos de Access, incluyendo sus tablas, columnas y relaciones. Las relaciones se obtuvieron directamente del esquema de la base de datos.

## Estructura de Tablas

### Tablas Locales

#### Tabla: `ProyectoRespCalidad`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Proyecto` | `Text` |
| `UsuarioCalidad` | `Text` |

#### Tabla: `TbAnexos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `EvidenciaSuministrador` | `Text` |
| `EvidenciaUTE` | `Text` |
| `FechaAnexo` | `Date` |
| `IDAnexo` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDProyecto` | `Integer` |
| `IDRiesgo` | `Integer` |
| `NombreArchivo` | `Text` |
| `Titulo` | `Text` |

#### Tabla: `TbAnexosAntigua`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodigoUnico` | `Text` |
| `Descripcion` | `Text (Long)` |
| `EvidenciaUTE` | `Text` |
| `FechaAnexo` | `Date` |
| `IDAnexo` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDProyecto` | `Integer` |
| `NombreArchivo` | `Text` |
| `Titulo` | `Text` |

#### Tabla: `TbAux`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDProyecto` | `Integer` |

#### Tabla: `TbAuxProyectosRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaDetectado` | `Date` |
| `FechaMaterializado` | `Date` |
| `IDProyecto` | `Integer` |
| `NombreProyectoCompleto` | `Text` |
| `Riesgo` | `Text` |

#### Tabla: `TbBibliotecaRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Activo` | `Text` |
| `CODIGO` | `Text` |
| `Descripcion` | `Text (Long)` |
| `Familia` | `Text` |
| `FechaAlta` | `Date` |
| `FechaModificacion` | `Date` |
| `IDRiesgoTipo` | `Integer` |
| `Tipo` | `Text` |
| `Usuario` | `Text` |

#### Tabla: `TbCambiosExplicacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Apartado` | `Text` |
| `Explicacion` | `Text (Long)` |

#### Tabla: `TbConfiguracionVisionRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDConfiguracion` | `Integer` |
| `Usuario` | `Text` |
| `VerDescripcion` | `Text` |
| `VerSoloNoRetirados` | `Text` |

#### Tabla: `TbExplicacionCarencias`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Apartado` | `Text` |
| `Explicacion` | `Text (Long)` |
| `ID` | `Integer` |

#### Tabla: `TbHerramientaDocAyuda`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `NombreArchivoAyuda` | `Text` |
| `NombreFormulario` | `Text` |

#### Tabla: `TbIDAccionPlanContingencia`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDAccionContingencia` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDAccionPlanMitigacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDAccionMitigacion` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDAnexos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDAnexo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDBibliotecaRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDRiesgoTipo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDCorreosEnviados`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDCorreo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDDocumentos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDDocumento` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDEdiciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDEdicion` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDLog`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDLog` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDPlanContingencia`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDContingencia` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDPlanMitigacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDMitigacion` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDProyectos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDProyecto` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDRiesgo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDRiesgosAIntegrar`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDRiesgoExt` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbIDTareas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDtarea` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbLog`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Fecha` | `Date` |
| `IDAccionContingencia` | `Integer` |
| `IDAccionMitigacion` | `Integer` |
| `IDContingencia` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDLog` | `Integer` |
| `IDMitigacion` | `Integer` |
| `IDProyecto` | `Integer` |
| `IDRiesgo` | `Integer` |
| `Linea` | `Text (Long)` |
| `Titulo` | `Text` |
| `Usuario` | `Text` |

#### Tabla: `TbLogPublicaciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaPreparadaParaPublicar` | `Date` |
| `FechaPreparadaParaPublicarQuitar` | `Date` |
| `FechaPublicacion` | `Date` |
| `FechaRegistro` | `Date` |
| `ID` | `Integer` |
| `IDEdicion` | `Integer` |
| `PropuestaRechazadaPorCalidadFecha` | `Date` |
| `PropuestaRechazadaPorCalidadMotivo` | `Text (Long)` |
| `UsuarioFechaPreparadaParaPublicar` | `Text` |
| `UsuarioFechaPreparadaParaPublicarQuitar` | `Text` |
| `UsuarioFechaPublicacion` | `Text` |

#### Tabla: `TbOrigenesRiesgosDetalles`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `Origen` | `Text` |

#### Tabla: `TbProyectoEdicionesCorreoRevision`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCorreoRevision` | `Date` |
| `IDCorreo` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDEnvioCorreoTecnico` | `Integer` |
| `UsuarioCalidad` | `Text` |

#### Tabla: `TbProyectos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Aprobado` | `Text` |
| `CadenaNombreAutorizados` | `Text (Long)` |
| `Cliente` | `Text` |
| `CodigoDocumento` | `Text` |
| `CorreoRAC` | `Text` |
| `Elaborado` | `Text` |
| `EnUTE` | `Text` |
| `FechaCierre` | `Date` |
| `FechaFirmaContrato` | `Text` |
| `FechaMaxProximaPublicacion` | `Date` |
| `FechaPrevistaCierre` | `Date` |
| `FechaRegistroInicial` | `Date` |
| `IDExpediente` | `Integer` |
| `IDProyecto` | `Integer` |
| `Juridica` | `Text` |
| `NombreParaNodo` | `Text` |
| `NombreProyecto` | `Text` |
| `NombreUsuarioCalidad` | `Text` |
| `Ordinal` | `Integer` |
| `ParaInformeAvisos` | `Text` |
| `Proyecto` | `Text` |
| `RequiereRiesgoDeBiblioteca` | `Text` |
| `Revisado` | `Text` |
| `RiesgosDeLaOferta` | `Text` |
| `RiesgosDelSubContratista` | `Text` |

#### Tabla: `TbProyectosEdiciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Aprobado` | `Text` |
| `Comentarios` | `Text (Long)` |
| `Edicion` | `SmallInt` |
| `Elaborado` | `Text` |
| `EntregadoAClienteORAC` | `Text` |
| `FechaEdicion` | `Date` |
| `FechaMaxProximaPublicacion` | `Date` |
| `FechaPreparadaParaPublicar` | `Date` |
| `FechaPublicacion` | `Date` |
| `FechaUltimoCambio` | `Date` |
| `IDDocumentoAGEDO` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDProyecto` | `Integer` |
| `NombreArchivoInforme` | `Text` |
| `NotasCalidadParaPublicar` | `Text (Long)` |
| `PermitidoImprimirExcel` | `Text` |
| `PropuestaRechazadaPorCalidadFecha` | `Date` |
| `PropuestaRechazadaPorCalidadMotivo` | `Text (Long)` |
| `Revisado` | `Text` |
| `UsuarioCalidadRechazaPropuesta` | `Text` |
| `UsuarioProponePublicar` | `Text` |
| `UsuarioUltimoCambio` | `Text` |

#### Tabla: `TbProyectosEdicionesSuministradores`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ID` | `Integer` |
| `IDAnexo` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDSuministrador` | `Integer` |

#### Tabla: `TbProyectosEdicionesSuministradores1`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ID` | `Integer` |
| `IDAnexo` | `Integer` |
| `IDEdicion` | `Integer` |
| `Suministrador` | `Text` |

#### Tabla: `TbProyectosJefesDeProyecto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `EnvioCorreos` | `Text` |
| `EsJefeProyecto` | `Text` |
| `IDProyecto` | `Integer` |
| `Usuario` | `Text` |

#### Tabla: `TbProyectosResponsablesCalidad`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDProyecto` | `Integer` |
| `UsuarioCalidad` | `Text` |

#### Tabla: `TbProyectosSuministradores`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `GestionCalidad` | `Text` |
| `ID` | `Integer` |
| `IDProyecto` | `Integer` |
| `IDSuministrador` | `Integer` |

#### Tabla: `TbProyectosSuministradores1`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `GestionCalidad` | `Text` |
| `ID` | `Integer` |
| `IDProyecto` | `Integer` |
| `Suministrador` | `Text` |

#### Tabla: `TbProyectosTipo`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `IDTipoProyecto` | `Integer` |
| `TipoProyecto` | `Text` |

#### Tabla: `TbRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Calidad` | `Text` |
| `CausaRaiz` | `Text (Long)` |
| `CodRiesgoBiblioteca` | `Text` |
| `CodigoRiesgo` | `Text` |
| `CodigoUnico` | `Text` |
| `ColorIcono` | `Text` |
| `Contingencia` | `Text` |
| `Coste` | `Text` |
| `Descripcion` | `Text (Long)` |
| `DetectadoPor` | `Text` |
| `DiasSinRespuestaCalidadAceptacion` | `Text` |
| `DiasSinRespuestaCalidadRetipificacion` | `Text` |
| `DiasSinRespuestaCalidadRetiro` | `Text` |
| `EntidadDetecta` | `Text` |
| `Estado` | `Text` |
| `FechaAprobacionAceptacionPorCalidad` | `Date` |
| `FechaAprobacionRetiroPorCalidad` | `Date` |
| `FechaCerrado` | `Date` |
| `FechaDetectado` | `Date` |
| `FechaEstado` | `Text` |
| `FechaJustificacionAceptacionRiesgo` | `Date` |
| `FechaJustificacionRetiroRiesgo` | `Date` |
| `FechaMaterializado` | `Date` |
| `FechaMitigacionAceptar` | `Date` |
| `FechaRechazoAceptacionPorCalidad` | `Date` |
| `FechaRechazoRetiroPorCalidad` | `Date` |
| `FechaRetirado` | `Date` |
| `FechaRiesgoParaRetipificar` | `Date` |
| `FechaRiesgoRetipificado` | `Date` |
| `HayErrorEnRiesgo` | `Text` |
| `IDEdicion` | `Integer` |
| `IDRiesgo` | `Integer` |
| `ImpactoGlobal` | `Text` |
| `JustificacionAceptacionRiesgo` | `Text (Long)` |
| `JustificacionRetiroRiesgo` | `Text (Long)` |
| `Mitigacion` | `Text` |
| `NombreIcono` | `Text` |
| `NombreNodoDesc` | `Text` |
| `NombreNodoEstado` | `Text` |
| `Origen` | `Text` |
| `Plazo` | `Text` |
| `Priorizacion` | `SmallInt` |
| `RequierePlanContingencia` | `Text` |
| `RequiereRiesgoDeBiblioteca` | `Text` |
| `RiesgoPendienteRetipificacion` | `Text` |
| `Valoracion` | `Text` |
| `Vulnerabilidad` | `Text` |

#### Tabla: `TbRiesgosAIntegrar`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CausaRaiz` | `Text` |
| `CausaRiesgoPedido` | `Text (Long)` |
| `CodRiesgo` | `Text` |
| `CodRiesgoBiblioteca` | `Text` |
| `Descripcion` | `Text (Long)` |
| `FechaAltaRegistro` | `Date` |
| `FechaDetectado` | `Date` |
| `FechaMotivo` | `Date` |
| `IDEdicion` | `Integer` |
| `IDRiesgo` | `Integer` |
| `IDRiesgoExt` | `Integer` |
| `MotivoNoIntegrado` | `Text (Long)` |
| `Origen` | `Text` |
| `Pedido` | `Text` |
| `ProveedorPedido` | `Text` |
| `RequiereRiesgoDeBiblioteca` | `Text` |
| `RiesgoPendienteRetipificacion` | `Text` |
| `Suministrador` | `Text` |
| `Trasladar` | `Text` |
| `UsuarioRegistra` | `Text` |

#### Tabla: `TbRiesgosAreasImpacto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `Indice` | `Text` |
| `Tipo` | `Text` |
| `ordinal` | `TinyInt` |

#### Tabla: `TbRiesgosMaterializaciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodigoRiesgo` | `Text` |
| `EsMaterializacion` | `Text` |
| `Estado` | `Text` |
| `Fecha` | `Date` |
| `FechaDecison` | `Date` |
| `ID` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDNC` | `Integer` |
| `IDProyecto` | `Integer` |
| `ParaNC` | `Text` |

#### Tabla: `TbRiesgosNC`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaDecison` | `Date` |
| `FechaRegistro` | `Date` |
| `ID` | `Integer` |
| `IDNC` | `Integer` |
| `IDRiesgo` | `Integer` |
| `ParaNC` | `Text` |

#### Tabla: `TbRiesgosPlanContingenciaDetalle`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Accion` | `Text (Long)` |
| `CodAccion` | `Text` |
| `EsUltimaAccion` | `Text` |
| `Estado` | `Text` |
| `FechaFinPrevista` | `Date` |
| `FechaFinReal` | `Date` |
| `FechaInicio` | `Date` |
| `IDAccionContingencia` | `Integer` |
| `IDContingencia` | `Integer` |
| `NombreIcono` | `Text` |
| `ResponsableAccion` | `Text` |

#### Tabla: `TbRiesgosPlanContingenciaDetalleReversa`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Estado` | `Text` |
| `FechaFinPrevista` | `Date` |
| `FechaFinReal` | `Date` |
| `FechaInicio` | `Date` |
| `IDAccionContingencia` | `Integer` |
| `IDEdicion` | `Integer` |

#### Tabla: `TbRiesgosPlanContingenciaPpal`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodContingencia` | `Text` |
| `DisparadorDelPlan` | `Text (Long)` |
| `Estado` | `Text` |
| `FechaDeActivacion` | `Date` |
| `FechaDesactivacion` | `Date` |
| `IDContingencia` | `Integer` |
| `IDRiesgo` | `Integer` |
| `NombreIcono` | `Text` |

#### Tabla: `TbRiesgosPlanMitigacionDetalle`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Accion` | `Text (Long)` |
| `CodAccion` | `Text` |
| `EsUltimaAccion` | `Text` |
| `Estado` | `Text` |
| `FechaFinPrevista` | `Date` |
| `FechaFinReal` | `Date` |
| `FechaInicio` | `Date` |
| `IDAccionMitigacion` | `Integer` |
| `IDMitigacion` | `Integer` |
| `NombreIcono` | `Text` |
| `ResponsableAccion` | `Text` |

#### Tabla: `TbRiesgosPlanMitigacionDetalleReversa`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Estado` | `Text` |
| `FechaFinPrevista` | `Date` |
| `FechaFinReal` | `Date` |
| `FechaInicio` | `Date` |
| `IDAccionMitigacion` | `Integer` |
| `IDEdicion` | `Integer` |

#### Tabla: `TbRiesgosPlanMitigacionPpal`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodMitigacion` | `Text` |
| `DisparadorDelPlan` | `Text (Long)` |
| `Estado` | `Text` |
| `FechaDeActivacion` | `Date` |
| `FechaDesactivacion` | `Date` |
| `IDMitigacion` | `Integer` |
| `IDRiesgo` | `Integer` |
| `NombreIcono` | `Text` |

#### Tabla: `TbRiesgosPorTipoProyecto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDCatalogoRiesgo` | `Integer` |
| `IDTipoProyecto` | `Integer` |

#### Tabla: `TbRiesgosValoracion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Impacto` | `Text` |
| `Valoracion` | `Text` |
| `Vulnerabilidad` | `Text` |

#### Tabla: `TbTablas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `EsTablaID` | `Text` |
| `Nombre` | `Text` |
| `NombreID1` | `Text` |
| `NombreID2` | `Text` |
| `NombreTablaOrigenID` | `Text` |
| `Orden` | `Integer` |
| `Origen` | `Text` |
| `RequiereID` | `Text` |
| `TablaID` | `Text` |

#### Tabla: `TbTareas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodRiesgo` | `Text` |
| `EstadoTarea` | `Text` |
| `FechaAccion` | `Date` |
| `FechaJustificacion` | `Date` |
| `FechaRechazo` | `Date` |
| `FechaVisado` | `Date` |
| `IDProyecto` | `Integer` |
| `IDRiesgo` | `Integer` |
| `IDtarea` | `Integer` |
| `Justificacion` | `Text (Long)` |
| `TipoTarea` | `Text` |

#### Tabla: `TbTareasExplicaciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Explicacion` | `Text (Long)` |
| `NodoTarea` | `Text` |
| `TituloTarea` | `Text` |

#### Tabla: `TbUltimoProyecto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Fecha` | `Date` |
| `IDProyecto` | `Integer` |
| `IDUltimoProyecto` | `Integer` |
| `Usuario` | `Text` |

#### Tabla: `TbValoresPosiblesContingencia`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

#### Tabla: `TbValoresPosiblesEstadoRiesgo`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

#### Tabla: `TbValoresPosiblesMitigacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Explicacion` | `Text (Long)` |
| `Valores` | `Text` |

#### Tabla: `TbValoresPosiblesPlazoCalidadCosteVulnerabilidad`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

#### Tabla: `TbValoresPosiblesValoracion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

#### Tabla: `tbCambios`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `EdicionFinal` | `SmallInt` |
| `EdicionInicial` | `SmallInt` |
| `FechaRegistro` | `Date` |
| `IDCambio` | `Integer` |
| `IDProyecto` | `Integer` |
| `NombreCampo` | `Text` |
| `Riesgo` | `Text` |

#### Tabla: `tbCambiosParaPublicacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `EdicionFinal` | `SmallInt` |
| `EdicionInicial` | `SmallInt` |
| `FechaRegistro` | `Date` |
| `IDCambio` | `Integer` |
| `IDProyecto` | `Integer` |
| `NombreCampo` | `Text` |
| `Riesgo` | `Text` |

### Tablas Vinculadas (Accesibles)

✅ **Las siguientes tablas están vinculadas a bases de datos externas y son accesibles:**

#### Tabla: `TbAplicaciones (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Lanzadera_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Comando` | `Text (Long)` |
| `ConIconoEnLanzadera` | `Text` |
| `EjecucionEnOficina` | `Text` |
| `EnPruebas` | `Text` |
| `IDAplicacion` | `Integer` |
| `NombreAplicacion` | `Text` |
| `NombreArchivoDatos` | `Text` |
| `NombreCarpeta` | `Text` |
| `NombreCarpetaDocumentacion` | `Text` |
| `NombreCarpetaTemporal` | `Text` |
| `NombreCorto` | `Text` |
| `NombreDirectorioAyuda` | `Text` |
| `NombreDirectorioIconos` | `Text` |
| `NombreDirectorioRecursos` | `Text` |
| `NombreEjecutable` | `Text` |
| `NombreFuncionPublicacion` | `Text` |
| `NombreIcono` | `Text` |
| `NombreIconoLanzadera` | `Text` |
| `NombreIconoParaArbol` | `Text` |
| `Pass` | `Text` |
| `TituloAplicacion` | `Text` |
| `URLDIrectorioIconoAplicacion` | `Text` |

#### Tabla: `TbDPD (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDYS_DATOS.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODARTICULO` | `Text` |
| `CODCONTRATOGTV` | `Text` |
| `CODOFERTASUMINISTRADOR` | `Text` |
| `CODPROYECTOS` | `Text` |
| `CRITERIOCOMPRAS` | `Text` |
| `DESCRIPCION` | `Text` |
| `ELIMINADO` | `Boolean` |
| `ELIMINADOOBSERVACIONES` | `Text (Long)` |
| `EXPEDIENTE` | `Text` |
| `EstadoCorto` | `Text` |
| `EstadoLargo` | `Text` |
| `FECHAPETICION` | `Date` |
| `FECHARECEPCIONECONOMICA` | `Date` |
| `FELIMINADO` | `Date` |
| `FFINNECESIDAD` | `Date` |
| `FINICIONECESIDAD` | `Date` |
| `FREGISTRO` | `Date` |
| `FechaFinAgendaTecnica` | `Date` |
| `FechaPreparadoParaVisadoOferta` | `Date` |
| `FechaRechazoOferta` | `Date` |
| `FechaVisadoOferta` | `Date` |
| `IDExpediente` | `Integer` |
| `ID_PROYECTOS` | `Integer` |
| `IMPORTESINIVA` | `Double` |
| `NAcreedorSAP` | `Integer` |
| `OBSERVACIONES` | `Text (Long)` |
| `OBSERVACIONESCALIDAD` | `Text` |
| `OBSERVACIONESECONOMICAS` | `Text (Long)` |
| `OFERTARECIBIDAFECHA` | `Date` |
| `PETICIONARIO` | `Text` |
| `PETICIONARIOREAL` | `Text` |
| `POSICIONCONTRATOGTV` | `Integer` |
| `RistraResponsablesExpTemp` | `Text` |
| `TIPOPEDIDO` | `Text` |
| `email` | `Text` |

#### Tabla: `TbDocumentos (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDO20_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AdjuntoEncriptado` | `Text` |
| `Archivo` | `Text` |
| `Area` | `Text` |
| `CLASE` | `Text` |
| `CadenaNombreArchivos` | `Text (Long)` |
| `Centro` | `Text` |
| `Clasificacion` | `Text` |
| `CodExp` | `Text` |
| `Codigo` | `Text` |
| `Edicion` | `Integer` |
| `Estado` | `Text` |
| `FENTRADAENVIGOR` | `Date` |
| `FEdicion` | `Date` |
| `FechaAlta` | `Date` |
| `FechaCaducidad` | `Date` |
| `FechaDeComienzoNuevaVersion` | `Date` |
| `IDDocumento` | `Integer` |
| `IDDocumentoNuevaVersion` | `Integer` |
| `IDDocumentoRevision` | `Integer` |
| `NCABIERTACERRADA` | `Text` |
| `NCPARAINDICADOR` | `Text` |
| `Observaciones` | `Text (Long)` |
| `Registrador` | `Text` |
| `RegistroEntrada` | `Text` |
| `RegistroSalida` | `Text` |
| `ResponsableEdicion` | `Text` |
| `Tipo` | `Text` |
| `Titulo` | `Text` |
| `URLCarpetaAGEDO` | `Text (Long)` |
| `URLCarpetaArchivosLocales` | `Text (Long)` |
| `UltimaVersion` | `Text` |
| `Versionable` | `Text` |

#### Tabla: `TbDocumentosID (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDO20_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDDocumento` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

#### Tabla: `TbExpedientes (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDYS_DATOS.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AcuerdoMarco` | `Text` |
| `Adjudicado` | `Boolean` |
| `AñosGarantia` | `Double` |
| `CLASIFICACION` | `Text` |
| `CarpetaArchivo` | `Text` |
| `CodExpedienteLargo` | `Text` |
| `Comentarios` | `Text (Long)` |
| `ContratoBasadoDe` | `Text` |
| `EnPeriodoDeAdjudicacion` | `Boolean` |
| `Estado` | `Text` |
| `Expediente` | `Text` |
| `FECHAADJUDICACION` | `Date` |
| `FechaAvisoVerificacionDisenio` | `Date` |
| `FechaEntradaContrato` | `Date` |
| `FechaFinAvisoVerificacionDisenio` | `Date` |
| `FechaFinExp` | `Date` |
| `FechaPrimerModificado` | `Date` |
| `FechaRecepcion` | `Date` |
| `FechaRegistro` | `Date` |
| `FechaSegundoModificado` | `Date` |
| `FirmadelContrato` | `Date` |
| `Generico` | `Text` |
| `IDAdjudicacion` | `Integer` |
| `IDDocumentoContrato` | `Integer` |
| `IDDocumentoPCAP` | `Integer` |
| `IDDocumentoPPT` | `Integer` |
| `IDDocumentoProrrogas` | `Integer` |
| `IDDocumentoRAC` | `Integer` |
| `IDDocumentoRecepcion` | `Integer` |
| `IMPORTEEXP` | `Double` |
| `INTECDEF` | `Text` |
| `IdExpediente` | `Integer` |
| `Informe` | `Boolean` |
| `Margen` | `Double` |
| `OFICINADELPROGRAMA` | `Text` |
| `Observaciones` | `Text (Long)` |
| `PCAP` | `Text` |
| `PPT` | `Text` |
| `ParaHacerPedidos` | `Text` |
| `Pcal` | `Text` |
| `PcalTipo` | `Text` |
| `RAC` | `Text` |
| `ResponsableCalidad` | `Text` |
| `RistraResponsablesTemp` | `Text` |
| `Situacion` | `Text` |
| `TITULOEXP` | `Text (Long)` |
| `TieneVerificacionDisenio` | `Text` |
| `URLADJUDICACION` | `Text (Long)` |
| `URLRAC` | `Text (Long)` |
| `año` | `Integer` |

#### Tabla: `TbExpedientes1 (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AGEDYSAplica` | `Text` |
| `AGEDYSGenerico` | `Text` |
| `APLICAESTADO` | `Text` |
| `AccesoSharepoint` | `Text (Long)` |
| `Adjudicado` | `Text` |
| `Ambito` | `Text` |
| `AplicaTareaS4H` | `Text` |
| `CadenaPecal` | `Text` |
| `CodExp` | `Text` |
| `CodExpLargo` | `Text` |
| `CodProyecto` | `Text` |
| `CodS4H` | `Text` |
| `CodigoActividad` | `Text` |
| `ContratistaPrincipal` | `Text` |
| `ESTADO` | `Text` |
| `EnPeriodoDeAdjudicacion` | `Text` |
| `EsAM` | `Text` |
| `EsBasado` | `Text` |
| `EsExpediente` | `Text` |
| `EsLote` | `Text` |
| `FECHAADJUDICACION` | `Date` |
| `FECHACERTIFICACION` | `Date` |
| `FECHADESESTIMADA` | `Date` |
| `FECHAFIRMACONTRATO` | `Date` |
| `FECHAINICIOLICITACION` | `Date` |
| `FECHAOFERTA` | `Date` |
| `FECHAPERDIDA` | `Date` |
| `FechaCreacion` | `Date` |
| `FechaFinContrato` | `Date` |
| `FechaFinGarantia` | `Date` |
| `FechaInicioContrato` | `Date` |
| `FechaUltimoCambio` | `Date` |
| `GARANTIAMESES` | `Text` |
| `HPSAplica` | `Text` |
| `IDEjercito` | `Integer` |
| `IDEstado` | `Integer` |
| `IDExpediente` | `Integer` |
| `IDExpedientePadre` | `Integer` |
| `IDOficinaPrograma` | `Integer` |
| `IDOrganoContratacion` | `Integer` |
| `IDResponsableCalidad` | `Integer` |
| `IDUsuarioCreacion` | `Text` |
| `IDUsuarioUltimoCambio` | `Text` |
| `IdGradoClasificacion` | `Integer` |
| `ImporteContratacion` | `Double` |
| `ImporteLicitacion` | `Double` |
| `NPedido` | `Text` |
| `Nemotecnico` | `Text` |
| `Observaciones` | `Text (Long)` |
| `Ordinal` | `Text` |
| `POSTAGEDO` | `Text` |
| `Pecal` | `Text` |
| `Tipo` | `Text` |
| `TipoInforme` | `Text` |
| `Titulo` | `Text (Long)` |

#### Tabla: `TbExpedientesResponsables (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CorreoSiempre` | `Text` |
| `EsJefeProyecto` | `Text` |
| `IDExpedienteResponsable` | `Integer` |
| `IdExpediente` | `Integer` |
| `IdUsuario` | `Integer` |

#### Tabla: `TbExpedientesSuministradores (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ContratistaPrincipal` | `Text` |
| `Descripcon` | `Text (Long)` |
| `IDExpediente` | `Integer` |
| `IDExpedienteSuministrador` | `Integer` |
| `IDSuministrador` | `Integer` |
| `SubContratista` | `Text` |

#### Tabla: `TbNoConformidades (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\NoConformidades_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ACR` | `Text (Long)` |
| `Borrado` | `Boolean` |
| `CAUSA` | `Text (Long)` |
| `CausaYAnalisRaiz` | `Text (Long)` |
| `Cerrada` | `Text` |
| `CodConcesionAsociada` | `Text` |
| `CodExp` | `Text` |
| `CodigoNoConformidad` | `Text` |
| `CodigoNoConformidadAsociada` | `Text` |
| `CodigoRiesgo` | `Text` |
| `ConformeControlEficacia` | `Text` |
| `ControlEficacia` | `Text (Long)` |
| `DESCRIPCION` | `Text (Long)` |
| `DetectadoPor` | `Text` |
| `ENTIDADRESPONSABLE` | `Text` |
| `ESTADO` | `Text` |
| `EXPEDIENTE` | `Text` |
| `EsNoConformidad` | `Boolean` |
| `FECHAAPERTURA` | `Date` |
| `FECHACIERRE` | `Date` |
| `FPREVCIERRE` | `Date` |
| `FechaControlEficacia` | `Date` |
| `FechaPrevistaControlEficacia` | `Date` |
| `IDExpediente` | `Integer` |
| `IDNCAsociada` | `Integer` |
| `IDNoConformidad` | `Integer` |
| `IDProyecto` | `Integer` |
| `IDTipo` | `Integer` |
| `Juridica` | `Text` |
| `JuridicaExp` | `Text` |
| `MotivoBorrado` | `Text (Long)` |
| `NOTAS` | `Text (Long)` |
| `Nemotecnico` | `Text` |
| `PROYECTO` | `Text` |
| `RESPONSABLECALIDAD` | `Text` |
| `RESPONSABLECALIDADExp` | `Text` |
| `RESPONSABLETELEFONICA` | `Text` |
| `RequiereACR` | `Boolean` |
| `RequiereControlEficacia` | `Text` |
| `ResponsableEjecucion` | `Text` |
| `ResultadoControlEficacia` | `Text (Long)` |
| `TIPO` | `Text` |
| `Tipologia` | `Text` |
| `VEHICULO` | `Text` |

#### Tabla: `TbProyectos1 (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Gestion_Riesgos_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Aprobado` | `Text` |
| `CadenaNombreAutorizados` | `Text (Long)` |
| `Cliente` | `Text` |
| `CodigoDocumento` | `Text` |
| `CorreoRAC` | `Text` |
| `Elaborado` | `Text` |
| `EnUTE` | `Text` |
| `FechaCierre` | `Date` |
| `FechaFirmaContrato` | `Text` |
| `FechaMaxProximaPublicacion` | `Date` |
| `FechaPrevistaCierre` | `Date` |
| `FechaRegistroInicial` | `Date` |
| `IDExpediente` | `Integer` |
| `IDProyecto` | `Integer` |
| `Juridica` | `Text` |
| `NombreParaNodo` | `Text` |
| `NombreProyecto` | `Text` |
| `NombreUsuarioCalidad` | `Text` |
| `Ordinal` | `Integer` |
| `ParaInformeAvisos` | `Text` |
| `Proyecto` | `Text` |
| `RequiereRiesgoDeBiblioteca` | `Text` |
| `Revisado` | `Text` |
| `RiesgosDeLaOferta` | `Text` |
| `RiesgosDelSubContratista` | `Text` |

#### Tabla: `TbResponsablesExpedientes (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDYS_DATOS.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CorreoSiempre` | `Text` |
| `IdExpediente` | `Integer` |
| `IdUsuario` | `Integer` |

#### Tabla: `TbSuministradores (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CIF` | `Text` |
| `CP` | `Text` |
| `Ciudad` | `Text` |
| `DESCRIPCION` | `Text (Long)` |
| `Direccion` | `Text (Long)` |
| `IDSuministrador` | `Integer` |
| `Nemotecnico` | `Text` |
| `Nombre` | `Text` |
| `TramitadoraHPS` | `Text` |

#### Tabla: `TbSuministradoresSAP (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDYS_DATOS.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AcreedorSAP` | `Integer` |
| `CP` | `Text` |
| `ConceptoBusqueda` | `Text (Long)` |
| `Direccion` | `Text` |
| `IDSuministrador` | `Integer` |
| `NifComunitario` | `Text` |
| `PerteneceAlGrupo` | `Text` |
| `Poblacion` | `Text` |
| `Suministrador` | `Text` |
| `email` | `Text` |

#### Tabla: `TbUsuariosAplicaciones (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Lanzadera_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Activado` | `Boolean` |
| `CorreoUsuario` | `Text` |
| `EsAdministrador` | `Text` |
| `FechaAlta` | `Date` |
| `FechaBaja` | `Date` |
| `FechaBloqueo` | `Date` |
| `FechaProximoCambioContrasenia` | `Date` |
| `FechaUltimaConexion` | `Date` |
| `Id` | `SmallInt` |
| `JefeDelUsuario` | `Text` |
| `MantenerLanzaderaAbierta` | `Boolean` |
| `Matricula` | `Text` |
| `Movil` | `Text` |
| `Nombre` | `Text` |
| `Observaciones` | `Text (Long)` |
| `ParaTareasProgramadas` | `Boolean` |
| `PassIncialPlana` | `Text` |
| `Password` | `Text` |
| `PasswordNuncaCaduca` | `Boolean` |
| `PermisoPruebas` | `Text` |
| `PermisosAsignados` | `Boolean` |
| `Telefono` | `Text` |
| `TieneQueCambiarLaContrasenia` | `Boolean` |
| `UsuarioImborrable` | `Boolean` |
| `UsuarioRed` | `Text` |
| `UsuarioSSID` | `Text` |

#### Tabla: `TbUsuariosAplicacionesPermisos (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Lanzadera_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CorreoUsuario` | `Text` |
| `EsUsuarioAdministrador` | `Text` |
| `EsUsuarioCalidad` | `Text` |
| `EsUsuarioCalidadAvisos` | `Text` |
| `EsUsuarioEconomia` | `Text` |
| `EsUsuarioSecretaria` | `Text` |
| `EsUsuarioSinAcceso` | `Text` |
| `EsUsuarioTecnico` | `Text` |
| `IDAplicacion` | `Integer` |

## Relaciones entre Tablas

Las siguientes relaciones fueron encontradas en el esquema de la base de datos:

- La tabla `TbAnexosAntigua.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `tbCambios.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `TbLogPublicaciones.IDEdicion` se relaciona con `TbProyectosEdiciones.IDEdicion`.
- La tabla `TbProyectosEdiciones.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `TbProyectosEdicionesSuministradores.IDEdicion` se relaciona con `TbProyectosEdiciones.IDEdicion`.
- La tabla `TbProyectosJefesDeProyecto.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `TbProyectosResponsablesCalidad.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `TbProyectosSuministradores.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `TbRiesgos.IDEdicion` se relaciona con `TbProyectosEdiciones.IDEdicion`.
- La tabla `TbRiesgosAIntegrar.IDEdicion` se relaciona con `TbProyectosEdiciones.IDEdicion`.
- La tabla `TbRiesgosMaterializaciones.IDEdicion` se relaciona con `TbProyectosEdiciones.IDEdicion`.
- La tabla `TbRiesgosMaterializaciones.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `TbRiesgosPlanContingenciaDetalle.IDContingencia` se relaciona con `TbRiesgosPlanContingenciaPpal.IDContingencia`.
- La tabla `TbRiesgosPlanContingenciaPpal.IDRiesgo` se relaciona con `TbRiesgos.IDRiesgo`.
- La tabla `TbRiesgosPlanMitigacionDetalle.IDMitigacion` se relaciona con `TbRiesgosPlanMitigacionPpal.IDMitigacion`.
- La tabla `TbRiesgosPlanMitigacionPpal.IDRiesgo` se relaciona con `TbRiesgos.IDRiesgo`.
- La tabla `TbRiesgosPorTipoProyecto.IDTipoProyecto` se relaciona con `TbProyectosTipo.IDTipoProyecto`.
- La tabla `TbTareas.IDProyecto` se relaciona con `TbProyectos.IDProyecto`.
- La tabla `TbTareas.IDRiesgo` se relaciona con `TbRiesgos.IDRiesgo`.


## Resumen de la lógica identificada:
### 1. Tareas Semanales Técnicas
- Destinatarios : Individualizados (un correo por técnico)
- Contenido : Personalizado para cada técnico con sus tareas pendientes
- Proceso :
  1. 1.
     Obtener lista de técnicos con tareas pendientes
  2. 2.
     Para cada técnico, generar tablas HTML específicas
  3. 3.
     Registrar un correo individual por técnico
### 2. Tareas Semanales Calidad
- Destinatarios : Individualizados (un correo por miembro de calidad)
- Contenido : Personalizado pero con información completa
- Proceso :
  1. 1.
     Obtener miembros de calidad (como en No Conformidades, no hardcodeado)
  2. 2.
     Para cada miembro de calidad, generar un correo donde:
     - Sus tareas aparecen primero en el mensaje
     - Luego se incluyen las tareas del resto de miembros de calidad
  3. 3.
     Un correo individual por miembro de calidad
### 3. Tareas Mensuales Calidad
- Destinatarios : Todos los miembros de calidad (un solo correo)
- Contenido : Mismo HTML para todos
- Proceso :
  1. 1.
     Obtener miembros de calidad (calculado, no hardcodeado)
  2. 2.
     Generar un único HTML con información general
  3. 3.
     Enviar un correo a todos los miembros de calidad

    puedes ver la estructura de datos en Gestion_Brass_Gestion_Datos.md
</Gestión de Riesgos>

<BRASS>
Informe de Lógica del Script: BRASS.vbs
Propósito General
El objetivo principal de este script es realizar una comprobación diaria automatizada sobre el estado de calibración de los equipos de medida registrados en una base de datos. Si detecta equipos cuya calibración ha expirado, genera y registra un correo electrónico de notificación con un listado de dichos equipos.

Flujo de Ejecución
La lógica del script se puede resumir en los siguientes pasos:

Verificación de Tarea Diaria: Al iniciarse, el script primero consulta una base de datos de control de tareas para verificar si la comprobación "BRASSDiario" ya se ha realizado en el día actual. Si la tarea ya figura como completada para hoy, el script finaliza su ejecución para evitar duplicados.

Conexión a Bases de Datos: Si la tarea no se ha realizado, el script procede a conectarse a dos bases de datos principales:

Una base de datos de Tareas, que gestiona el estado de las ejecuciones de los scripts y contiene información de los usuarios.

Una base de datos BRASS, que almacena los datos específicos de los equipos de medida y sus calibraciones.

Comprobación de Calibraciones:

El script consulta la base de datos BRASS para obtener una lista de todos los equipos de medida que no han sido dados de baja.

Para cada equipo, revisa su historial de calibraciones y localiza la fecha de fin de la calibración más reciente.

Compara esta fecha de fin de calibración con la fecha actual. Si la fecha actual es posterior a la fecha de fin, el equipo se considera "fuera de calibración".

Generación del Informe (si es necesario):

Si se encuentra al menos un equipo fuera de calibración, el script construye un informe en formato HTML.

Este informe consiste en una tabla que lista los detalles (Nombre, NS, PN, Marca, Modelo) de todos los equipos no conformes.

Si ningún equipo está fuera de calibración, el script no genera el informe, pero igualmente marca la tarea como realizada y finaliza.

Registro del Correo Electrónico:

Si se generó un informe, el script prepara un correo electrónico.

El cuerpo del correo contiene la tabla HTML creada.

Obtiene la lista de correos de los administradores de la base de datos de Tareas para incluirlos en copia oculta (BCC).

En lugar de enviar el correo directamente, registra todos los detalles (destinatario, asunto, cuerpo, copia oculta) en una tabla de la base de datos de Tareas. Se asume que otro proceso se encarga del envío real de los correos registrados en esta tabla.

Finalización y Registro de Tarea:

Como último paso, el script actualiza la base de datos de Tareas para marcar la comprobación "BRASSDiario" como realizada con la fecha actual. Esto asegura que no se vuelva a ejecutar en el mismo día.

Finalmente, cierra todas las conexiones a las bases de datos.
</BRASS>