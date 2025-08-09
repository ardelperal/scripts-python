# Estructura de la Base de Datos y Relaciones

Este documento detalla la estructura de la base de datos de Access, incluyendo sus tablas, columnas y relaciones. Las relaciones se obtuvieron directamente del esquema de la base de datos.

## Estructura de Tablas

### Tabla: `ProyectoRespCalidad`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Proyecto` | `Text` |
| `UsuarioCalidad` | `Text` |

### Tabla: `TbAnexos`
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

### Tabla: `TbAnexosAntigua`
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

### Tabla: `TbAplicaciones`
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

### Tabla: `TbAux`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDProyecto` | `Integer` |

### Tabla: `TbAuxProyectosRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaDetectado` | `Date` |
| `FechaMaterializado` | `Date` |
| `IDProyecto` | `Integer` |
| `NombreProyectoCompleto` | `Text` |
| `Riesgo` | `Text` |

### Tabla: `TbBibliotecaRiesgos`
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

### Tabla: `TbCambiosExplicacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Apartado` | `Text` |
| `Explicacion` | `Text (Long)` |

### Tabla: `TbConfiguracionVisionRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDConfiguracion` | `Integer` |
| `Usuario` | `Text` |
| `VerDescripcion` | `Text` |
| `VerSoloNoRetirados` | `Text` |

### Tabla: `TbDPD`
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

### Tabla: `TbDocumentos`
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

### Tabla: `TbDocumentosID`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDDocumento` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbExpedientes`
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

### Tabla: `TbExpedientes1`
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

### Tabla: `TbExpedientesResponsables`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CorreoSiempre` | `Text` |
| `EsJefeProyecto` | `Text` |
| `IDExpedienteResponsable` | `Integer` |
| `IdExpediente` | `Integer` |
| `IdUsuario` | `Integer` |

### Tabla: `TbExpedientesSuministradores`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ContratistaPrincipal` | `Text` |
| `Descripcon` | `Text (Long)` |
| `IDExpediente` | `Integer` |
| `IDExpedienteSuministrador` | `Integer` |
| `IDSuministrador` | `Integer` |
| `SubContratista` | `Text` |

### Tabla: `TbExplicacionCarencias`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Apartado` | `Text` |
| `Explicacion` | `Text (Long)` |
| `ID` | `Integer` |

### Tabla: `TbHerramientaDocAyuda`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `NombreArchivoAyuda` | `Text` |
| `NombreFormulario` | `Text` |

### Tabla: `TbIDAccionPlanContingencia`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDAccionContingencia` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDAccionPlanMitigacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDAccionMitigacion` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDAnexos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDAnexo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDBibliotecaRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDRiesgoTipo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDCorreosEnviados`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDCorreo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDDocumentos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDDocumento` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDEdiciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDEdicion` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDLog`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDLog` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDPlanContingencia`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDContingencia` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDPlanMitigacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDMitigacion` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDProyectos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDProyecto` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDRiesgos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDRiesgo` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDRiesgosAIntegrar`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDRiesgoExt` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbIDTareas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCreacion` | `Date` |
| `FechaEliminacion` | `Date` |
| `IDtarea` | `Integer` |
| `UsuarioCrea` | `Text` |
| `UsuarioElimina` | `Text` |

### Tabla: `TbLog`
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

### Tabla: `TbLogPublicaciones`
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

### Tabla: `TbNoConformidades`
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

### Tabla: `TbOrigenesRiesgosDetalles`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `Origen` | `Text` |

### Tabla: `TbProyectoEdicionesCorreoRevision`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaCorreoRevision` | `Date` |
| `IDCorreo` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDEnvioCorreoTecnico` | `Integer` |
| `UsuarioCalidad` | `Text` |

### Tabla: `TbProyectos`
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

### Tabla: `TbProyectos1`
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

### Tabla: `TbProyectosEdiciones`
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

### Tabla: `TbProyectosEdicionesSuministradores`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ID` | `Integer` |
| `IDAnexo` | `Integer` |
| `IDEdicion` | `Integer` |
| `IDSuministrador` | `Integer` |

### Tabla: `TbProyectosEdicionesSuministradores1`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ID` | `Integer` |
| `IDAnexo` | `Integer` |
| `IDEdicion` | `Integer` |
| `Suministrador` | `Text` |

### Tabla: `TbProyectosJefesDeProyecto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `EnvioCorreos` | `Text` |
| `EsJefeProyecto` | `Text` |
| `IDProyecto` | `Integer` |
| `Usuario` | `Text` |

### Tabla: `TbProyectosResponsablesCalidad`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDProyecto` | `Integer` |
| `UsuarioCalidad` | `Text` |

### Tabla: `TbProyectosSuministradores`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `GestionCalidad` | `Text` |
| `ID` | `Integer` |
| `IDProyecto` | `Integer` |
| `IDSuministrador` | `Integer` |

### Tabla: `TbProyectosSuministradores1`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `GestionCalidad` | `Text` |
| `ID` | `Integer` |
| `IDProyecto` | `Integer` |
| `Suministrador` | `Text` |

### Tabla: `TbProyectosTipo`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `IDTipoProyecto` | `Integer` |
| `TipoProyecto` | `Text` |

### Tabla: `TbResponsablesExpedientes`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CorreoSiempre` | `Text` |
| `IdExpediente` | `Integer` |
| `IdUsuario` | `Integer` |

### Tabla: `TbRiesgos`
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

### Tabla: `TbRiesgosAIntegrar`
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

### Tabla: `TbRiesgosAreasImpacto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `Indice` | `Text` |
| `Tipo` | `Text` |
| `ordinal` | `TinyInt` |

### Tabla: `TbRiesgosMaterializaciones`
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

### Tabla: `TbRiesgosNC`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaDecison` | `Date` |
| `FechaRegistro` | `Date` |
| `ID` | `Integer` |
| `IDNC` | `Integer` |
| `IDRiesgo` | `Integer` |
| `ParaNC` | `Text` |

### Tabla: `TbRiesgosPlanContingenciaDetalle`
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

### Tabla: `TbRiesgosPlanContingenciaDetalleReversa`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Estado` | `Text` |
| `FechaFinPrevista` | `Date` |
| `FechaFinReal` | `Date` |
| `FechaInicio` | `Date` |
| `IDAccionContingencia` | `Integer` |
| `IDEdicion` | `Integer` |

### Tabla: `TbRiesgosPlanContingenciaPpal`
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

### Tabla: `TbRiesgosPlanMitigacionDetalle`
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

### Tabla: `TbRiesgosPlanMitigacionDetalleReversa`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Estado` | `Text` |
| `FechaFinPrevista` | `Date` |
| `FechaFinReal` | `Date` |
| `FechaInicio` | `Date` |
| `IDAccionMitigacion` | `Integer` |
| `IDEdicion` | `Integer` |

### Tabla: `TbRiesgosPlanMitigacionPpal`
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

### Tabla: `TbRiesgosPorTipoProyecto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDCatalogoRiesgo` | `Integer` |
| `IDTipoProyecto` | `Integer` |

### Tabla: `TbRiesgosValoracion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Impacto` | `Text` |
| `Valoracion` | `Text` |
| `Vulnerabilidad` | `Text` |

### Tabla: `TbSuministradores`
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

### Tabla: `TbSuministradoresSAP`
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

### Tabla: `TbTablas`
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

### Tabla: `TbTareas`
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

### Tabla: `TbTareasExplicaciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Explicacion` | `Text (Long)` |
| `NodoTarea` | `Text` |
| `TituloTarea` | `Text` |

### Tabla: `TbUltimoProyecto`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Fecha` | `Date` |
| `IDProyecto` | `Integer` |
| `IDUltimoProyecto` | `Integer` |
| `Usuario` | `Text` |

### Tabla: `TbUsuariosAplicaciones`
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

### Tabla: `TbUsuariosAplicacionesPermisos`
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

### Tabla: `TbValoresPosiblesContingencia`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

### Tabla: `TbValoresPosiblesEstadoRiesgo`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

### Tabla: `TbValoresPosiblesMitigacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Explicacion` | `Text (Long)` |
| `Valores` | `Text` |

### Tabla: `TbValoresPosiblesPlazoCalidadCosteVulnerabilidad`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

### Tabla: `TbValoresPosiblesValoracion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Valores` | `Text` |

### Tabla: `tbCambios`
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

### Tabla: `tbCambiosParaPublicacion`
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
