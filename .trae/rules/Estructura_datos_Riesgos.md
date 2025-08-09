### Tablas Locales

#### Tabla: `ProyectoRespCalidad`
| Nombre de Columna | Tipo de Dato |FechaAprobacionAceptacionPorCalidad
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
