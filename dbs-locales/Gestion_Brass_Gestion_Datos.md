# Estructura de la Base de Datos y Relaciones

Este documento detalla la estructura de la base de datos de Access, incluyendo sus tablas, columnas y relaciones. Las relaciones se obtuvieron directamente del esquema de la base de datos.

## Estructura de Tablas

### Tabla: `Tb0FiltroGestion`
| Nombre de Columna |
|-------------------|
| `Datos` |
| `Fecha` |
| `ID` |
| `Usuario` |
| `Visto` |

### Tabla: `TbActividades`
| Nombre de Columna |
|-------------------|
| `ALIASTECNICO` |
| `Actividad` |
| `CodImportacion` |
| `DESCRIPCION` |
| `FechaAlta` |
| `HorasExtras` |
| `HorasLaborables` |
| `IDActividad` |
| `IDEVENTOGENERADO` |
| `IDEvento` |
| `IDExportacion` |
| `IDFacturacion` |
| `Observaciones` |
| `Ubicacion` |

### Tabla: `TbAnexos`
| Nombre de Columna |
|-------------------|
| `Descripcion` |
| `IDActividad` |
| `IDAnexo` |
| `IDEvento` |
| `IDGasto` |
| `IDMaterial` |
| `IDMaterialSeguimiento` |
| `IDSubContratacion` |
| `NombreArchivo` |
| `Titulo` |

### Tabla: `TbAuxActividad`
| Nombre de Columna |
|-------------------|
| `ALIASTECNICO` |
| `BUI` |
| `CODREGISTRODIFERENCIA` |
| `DESCRIPCION` |
| `FECHAACTIVIDAD` |
| `HORASEXTRAS` |
| `HORASLABORABLES` |
| `IDEQUIPO` |
| `IDEVENTO` |
| `NODO` |
| `SUBSISTEMA` |
| `TIPOACTIVIDAD` |
| `TIPOTECNICO` |
| `UBICACION` |

### Tabla: `TbAuxEventos`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `CAUSAFIN` |
| `CODREGISTRODIFERENCIA` |
| `CONTACTO` |
| `CRITICIDAD` |
| `DESCRIPCION` |
| `EQUIPO` |
| `FECHAALTA` |
| `FECHAFIN` |
| `HORAALTA` |
| `HORAFIN` |
| `IDEVENTO` |
| `IDEVENTOGENERADO` |
| `NODO` |
| `ORIGINADOR` |
| `PMPR` |
| `SUBSISTEMA` |
| `TIEMPORESPUESTA` |
| `TIPOEVENTO` |
| `TIPOTECNICO` |

### Tabla: `TbAuxManteniminetosPreventivosCalendario`
| Nombre de Columna |
|-------------------|
| `ANIO` |
| `BUI` |
| `FECHASREPARACIONENANIO` |
| `IDEQUIPO` |
| `IDEVENTO` |
| `MESPROG` |
| `NOMBREEQUIPO` |
| `PARTESMTOREALIZADOENANIO` |
| `SEMANAPROG` |

### Tabla: `TbAuxMateriales`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `CODREGISTRODIFERENCIA` |
| `COSTE` |
| `EQUIPO` |
| `FECHAENTREGA` |
| `IDEVENTO` |
| `MATERIAL` |
| `NODO` |
| `NS` |
| `PN` |
| `PrecioSinIVA` |
| `REPARADOPOR` |
| `SUBSISTEMA` |
| `TIPOACCION` |

### Tabla: `TbAuxPlanificacion`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `CadenaIDEventosPosibles` |
| `CadenaIDEventosUsados` |
| `DiasRestan` |
| `Equipo` |
| `FechaPrevista` |
| `IDPlanificacion` |
| `SUBSISTEMA` |

### Tabla: `TbBUI`
| Nombre de Columna |
|-------------------|
| `BUI` |

### Tabla: `TbBuiIDEvento`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `CODBUIIDVENTO` |

### Tabla: `TbCausaFin`
| Nombre de Columna |
|-------------------|
| `CAUSAFIN` |

### Tabla: `TbCodActividad`
| Nombre de Columna |
|-------------------|
| `ACTIVIDADNOPROGRAMADA` |
| `CODIGO` |

### Tabla: `TbCriticidad`
| Nombre de Columna |
|-------------------|
| `CRITICIDAD` |
| `DESCRIPCION` |

### Tabla: `TbEquipos`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `Descripcion` |
| `Equipo` |
| `FechaObsoleto` |
| `IDEquipo` |
| `NODO` |
| `SUBSISTEMA` |

### Tabla: `TbEquiposCalibrables`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `Equipo` |
| `FechaBajaParaCalibracion` |
| `IDEquipoCalibrable` |
| `Modelo` |
| `NS` |
| `Observaciones` |

### Tabla: `TbEquiposCalibrablesFechas`
| Nombre de Columna |
|-------------------|
| `FechaCalibrado` |
| `FechaComunicacionCliente` |
| `FechaFinCalibrado` |
| `IDCalibracion` |
| `IDEquipoCalibrable` |
| `URLDocumentosAnexados` |

### Tabla: `TbEquiposMedida`
| Nombre de Columna |
|-------------------|
| `Descripcion` |
| `FechaFinServicio` |
| `FechaInicioServicio` |
| `IDEquipoMedida` |
| `Marca` |
| `Modelo` |
| `NS` |
| `Nombre` |
| `PN` |

### Tabla: `TbEquiposMedidaCalibraciones`
| Nombre de Columna |
|-------------------|
| `EmpresaCalibradora` |
| `FechaCalibracion` |
| `FechaFinCalibracion` |
| `IDCalibracion` |
| `IDEquipoMedida` |
| `Observaciones` |

### Tabla: `TbEventos`
| Nombre de Columna |
|-------------------|
| `ALIASTECNICO` |
| `BUI` |
| `CAUSAFIN` |
| `CONTACTO` |
| `CRITICIDAD` |
| `CodImportacion` |
| `DESCRIPCION` |
| `FECHAALTAEVENTO` |
| `FechaEnInformeRAC` |
| `FechaFinal` |
| `FechaRegistroAlta` |
| `FechaRegistroModificacion` |
| `Franqueado` |
| `HORAFINALEVENTO` |
| `HORAINICIALEVENTO` |
| `IDEquipo` |
| `IDEvento` |
| `IDExportacion` |
| `IDParte` |
| `NODO` |
| `Notas` |
| `ORIGINADOR` |
| `PMPR` |
| `SUBSISTEMA` |
| `TIEMPORESPUESTAEVENTO` |
| `TIPOEVENTO` |

### Tabla: `TbEventosEquipoMedida`
| Nombre de Columna |
|-------------------|
| `IDCalibracion` |
| `IDEquipoMedida` |
| `IDEvento` |
| `IDEventoEquipoMedida` |

### Tabla: `TbEventosEquipoMedida_antes`
| Nombre de Columna |
|-------------------|
| `IDEquipoMedida` |
| `IDEvento` |
| `IDEventoEquipoMedida` |

### Tabla: `TbFacturaActividadesInvolucradas`
| Nombre de Columna |
|-------------------|
| `ALIASTECNICO` |
| `BUI` |
| `DESCRIPCION` |
| `EQUIPO` |
| `FECHAALTA` |
| `HORASEXTRAS` |
| `HORASLABORABLES` |
| `IDActividad` |
| `IDEVENTO` |
| `IDFactura` |
| `NODO` |
| `PERFIL` |
| `PrecioHoraExtraPerfil` |
| `PrecioHoraLaborablePerfil` |
| `SUBSISTEMA` |
| `TIPOACTIVIDAD` |
| `TIPOTECNICO` |
| `UBICACION` |

### Tabla: `TbFacturaEventosInvolucrados`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `CAUSAFIN` |
| `CONTACTO` |
| `CRITICIDAD` |
| `DESCRIPCION` |
| `EQUIPO` |
| `FECHAALTA` |
| `FECHAFIN` |
| `HORAALTA` |
| `HORAFIN` |
| `IDEVENTOSGENERADOS` |
| `IDEvento` |
| `IDFactura` |
| `NODO` |
| `ORIGINADOR` |
| `PMPR` |
| `ParaRegularizar` |
| `SUBSISTEMA` |
| `TIEMPORESPUESTA` |
| `TIPOEVENTO` |
| `TIPOTECNICO` |

### Tabla: `TbFacturaGastosInvolucrados`
| Nombre de Columna |
|-------------------|
| `ALIAS` |
| `FechaImputacionGasto` |
| `IDFactura` |
| `IDGasto` |
| `ImporteUnitario` |
| `NumeroUnidades` |
| `Observaciones` |
| `TipoGasto` |

### Tabla: `TbFacturaMaterialesInvolucrados`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `DESCRIPCIONEQUIPO` |
| `EQUIPO` |
| `FECHAENTREGA` |
| `IDEvento` |
| `IDFactura` |
| `IDMaterial` |
| `Material` |
| `NODO` |
| `NS` |
| `PN` |
| `PRECIOSINIVA` |
| `ReparadoPor` |
| `SUBSISTEMA` |
| `TIPOACCION` |

### Tabla: `TbFacturaPrincipal`
| Nombre de Columna |
|-------------------|
| `FechaFactura` |
| `FechaFinalEventos` |
| `IDFactura` |
| `ImporteAFacturar` |
| `NombreFacturaAnexa` |
| `PrecioBaseImponible` |
| `PrecioDietasYGastos` |
| `PrecioHoras` |
| `PrecioImpuestos` |
| `PrecioIncurrido` |
| `PrecioSubcontrataciones` |
| `PrecioSubcontratacionesConRecargo` |
| `PrecioSuministro` |
| `PrecioSuministroConRecargo` |
| `Recargo` |
| `TipoImpositivo` |
| `Titulo1` |
| `Titulo2` |
| `Titulo3` |

### Tabla: `TbFacturaPrincipalPerfiles`
| Nombre de Columna |
|-------------------|
| `IDFactura` |
| `IDFacturaPerfil` |
| `NHorasExt` |
| `NHorasLab` |
| `Perfil` |
| `PrecioHoraExt` |
| `PrecioHoraLab` |

### Tabla: `TbFacturaSubcontratacionesInvolucradas`
| Nombre de Columna |
|-------------------|
| `Descripcion` |
| `Empresa` |
| `FechaAlta` |
| `FechaFin` |
| `IDFactura` |
| `IDSubcontratacion` |
| `Importe` |

### Tabla: `TbGastos`
| Nombre de Columna |
|-------------------|
| `ALIAS` |
| `FechaImputacionGasto` |
| `IDGasto` |
| `ImporteUnitario` |
| `NumeroUnidades` |
| `Observaciones` |
| `TipoGasto` |

### Tabla: `TbGastosImportePorTipo`
| Nombre de Columna |
|-------------------|
| `FechaFinalImporte` |
| `FechaValorFinal` |
| `FechaValorInicial` |
| `ImporteUnitario` |
| `Observaciones` |
| `TipoGasto` |

### Tabla: `TbGuiaConciliaciones`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `EquipoID` |
| `IDEvento` |
| `IDGuia` |
| `Nodo` |
| `Parte` |
| `SubSistema` |

### Tabla: `TbHerramientaDocAyuda`
| Nombre de Columna |
|-------------------|
| `NombreArchivoAyuda` |
| `NombreFormulario` |

### Tabla: `TbMaterial`
| Nombre de Columna |
|-------------------|
| `COSTE` |
| `CodImportacion` |
| `Descripcion` |
| `EsReparacion` |
| `FechaEntrega` |
| `FechaIncio` |
| `Garantia` |
| `IDActividad` |
| `IDEquipo` |
| `IDMaterial` |
| `Material` |
| `NS` |
| `PN` |
| `ReparadoPor` |
| `TipoAccion` |

### Tabla: `TbMaterialSeguimiento`
| Nombre de Columna |
|-------------------|
| `DescripcionAnexo` |
| `Destino` |
| `FechaFinIntervencion` |
| `FechaInicioIntervencion` |
| `IDMaterial` |
| `IDSeguimiento` |
| `Motivo` |
| `NombreArchivoAnexo` |
| `Resultado` |
| `TituloAnexo` |
| `UltimaIntervencion` |

### Tabla: `TbNodoBUI`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `NODO` |

### Tabla: `TbNodos`
| Nombre de Columna |
|-------------------|
| `NODO` |

### Tabla: `TbOriginador`
| Nombre de Columna |
|-------------------|
| `ORIGINADOR` |

### Tabla: `TbPartesDetalle`
| Nombre de Columna |
|-------------------|
| `AliasCreador` |
| `CausaFin` |
| `Descripcion` |
| `Equipo` |
| `FechaAlta` |
| `FechaFin` |
| `HoraAlta` |
| `HoraFin` |
| `IDEvento` |
| `IDParte` |
| `Originador` |
| `PMPR` |
| `SubSistema` |
| `TiempoRespuesta` |

### Tabla: `TbPartesPpal`
| Nombre de Columna |
|-------------------|
| `Centro` |
| `Descripcion` |
| `FechaFinal` |
| `FechaInicial` |
| `FechaObtencion` |
| `IDFactura` |
| `IDParte` |
| `NombreArchivoAdjunto` |

### Tabla: `TbPlanificacion`
| Nombre de Columna |
|-------------------|
| `ANIO` |
| `FechaCierre` |
| `FechaPrevistaCierre` |
| `FechaRegistro` |
| `IDEquipo` |
| `IDEvento` |
| `IDNoEvento` |
| `IDNuevaPlanificacion` |
| `IDPlanificacion` |
| `Mes` |
| `MotivacionReprogramacion` |
| `MotivoCierre` |
| `Semana` |

### Tabla: `TbPlanificacionAnexos`
| Nombre de Columna |
|-------------------|
| `FechaAnexo` |
| `IDAnexoPlanificacion` |
| `IDPlanificacion` |
| `NombreAnexo` |
| `URLAnexo` |
| `UsuarioAnexa` |

### Tabla: `TbPlanificacionEquipos`
| Nombre de Columna |
|-------------------|
| `Alias` |
| `FechaAltaParaPlanificacion` |
| `FechabajaParaPlanificacion` |
| `IDEquipo` |
| `PeriodicidadEnMesesRecomendada` |

### Tabla: `TbPlanificacionRegistrada`
| Nombre de Columna |
|-------------------|
| `FechaMantoRealizado` |
| `ID` |
| `IDEquipo` |
| `NombreAnexo` |
| `Observaciones` |

### Tabla: `TbRepuestosTipo`
| Nombre de Columna |
|-------------------|
| `TIPOREPUESTOS` |

### Tabla: `TbResultadoVerificacion`
| Nombre de Columna |
|-------------------|
| `RESULTADOVERIFICACION` |

### Tabla: `TbSistema`
| Nombre de Columna |
|-------------------|
| `SISTEMA` |

### Tabla: `TbSubcontrataciones`
| Nombre de Columna |
|-------------------|
| `Descripcion` |
| `Empresa` |
| `FechaAlta` |
| `FechaFin` |
| `IDSubcontratacion` |
| `Importe` |
| `Observaciones` |

### Tabla: `TbSubsistemaBui`
| Nombre de Columna |
|-------------------|
| `BUI` |
| `SUBSISTEMA` |

### Tabla: `TbTecnicos`
| Nombre de Columna |
|-------------------|
| `ALIAS` |
| `DNI` |
| `EMAIL` |
| `FECHAALTA` |
| `FECHABAJA` |
| `NOMBRE` |
| `TELEFONO` |
| `TIPO` |

### Tabla: `TbTecnicosAusencias`
| Nombre de Columna |
|-------------------|
| `Alias` |
| `FechaLibranza` |
| `IDAusencia` |
| `Motivo` |
| `Observaciones` |
| `horas` |

### Tabla: `TbTecnicosFiestas`
| Nombre de Columna |
|-------------------|
| `FechaFiesta` |
| `Observaciones` |

### Tabla: `TbTipoAccion`
| Nombre de Columna |
|-------------------|
| `ESTADOREPARABLE` |

### Tabla: `TbTipoAsistencia`
| Nombre de Columna |
|-------------------|
| `TIPOASISTENCIA` |

### Tabla: `TbTipoEvento`
| Nombre de Columna |
|-------------------|
| `TIPOEVENTO` |

### Tabla: `TbTipoTecnico`
| Nombre de Columna |
|-------------------|
| `TIPO` |

### Tabla: `TbTipoTecnicoPrecios`
| Nombre de Columna |
|-------------------|
| `FechaFinal` |
| `FechaInicial` |
| `IDTipoTecnicoFecha` |
| `PrecioHoraExtra` |
| `PrecioHoraLab` |
| `TIPOTECNICO` |

### Tabla: `TbUbicacion`
| Nombre de Columna |
|-------------------|
| `UBICACION` |

## Relaciones entre Tablas

Las siguientes relaciones fueron encontradas en el esquema de la base de datos:

- La tabla `MSysNavPaneGroups` se relaciona con `MSysNavPaneGroupCategories`.
- La tabla `TbActividades` se relaciona con `TbEventos`.
- La tabla `TbEquipos` se relaciona con `TbBUI`.
- La tabla `TbEquipos` se relaciona con `TbNodos`.
- La tabla `TbEventos` se relaciona con `TbBUI`.
- La tabla `TbEventos` se relaciona con `TbEquipos`.
- La tabla `TbEventos` se relaciona con `TbNodos`.
- La tabla `TbFacturaActividadesInvolucradas` se relaciona con `TbActividades`.
- La tabla `TbFacturaActividadesInvolucradas` se relaciona con `TbFacturaPrincipal`.
- La tabla `TbFacturaActividadesInvolucradas` se relaciona con `TbTecnicos`.
- La tabla `TbFacturaActividadesInvolucradas` se relaciona con `TbTipoTecnico`.
- La tabla `TbFacturaEventosInvolucrados` se relaciona con `TbEventos`.
- La tabla `TbFacturaEventosInvolucrados` se relaciona con `TbFacturaPrincipal`.
- La tabla `TbFacturaGastosInvolucrados` se relaciona con `TbFacturaPrincipal`.
- La tabla `TbFacturaGastosInvolucrados` se relaciona con `TbGastos`.
- La tabla `TbFacturaGastosInvolucrados` se relaciona con `TbTecnicos`.
- La tabla `TbFacturaMaterialesInvolucrados` se relaciona con `TbFacturaPrincipal`.
- La tabla `TbFacturaMaterialesInvolucrados` se relaciona con `TbMaterial`.
- La tabla `TbFacturaPrincipalPerfiles` se relaciona con `TbFacturaPrincipal`.
- La tabla `TbFacturaSubcontratacionesInvolucradas` se relaciona con `TbFacturaPrincipal`.
- La tabla `TbFacturaSubcontratacionesInvolucradas` se relaciona con `TbSubcontrataciones`.
- La tabla `TbMaterial` se relaciona con `TbActividades`.
- La tabla `TbMaterialSeguimiento` se relaciona con `TbMaterial`.
- La tabla `TbNodoBUI` se relaciona con `TbNodos`.
- La tabla `TbSubsistemaBui` se relaciona con `TbBUI`.
- La tabla `TbTecnicos` se relaciona con `TbTipoTecnico`.
- La tabla `TbTecnicosAusencias` se relaciona con `TbTecnicos`.
- La tabla `TbTipoTecnicoPrecios` se relaciona con `TbTipoTecnico`.
