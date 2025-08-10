# Estructura de la Base de Datos y Relaciones

Este documento detalla la estructura de la base de datos de Access, incluyendo sus tablas, columnas y relaciones. Las relaciones se obtuvieron directamente del esquema de la base de datos.

## Estructura de Tablas

### Tablas Locales

#### Tabla: `Copia de TbNPedido`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODCONTRATOGTV` | `Text` |
| `CODPPD` | `Text` |
| `EMPRESAADJUDICATARIA` | `Text` |
| `ESORDINARIO` | `Text` |
| `FECHAANEXOCARTADIRECTORTSAP` | `Date` |
| `FECHABORRADA` | `Date` |
| `FECHACARTADIRECTORREALIZADA` | `Date` |
| `FECHACARTASUMINISTRADORREALIZADA` | `Date` |
| `FECHACOMUNICACIONCARTADIRECTOR` | `Date` |
| `FECHACOMUNICACIONCARTASUMINISTRADOR` | `Date` |
| `FECHACOMUNICACIONMARILO` | `Date` |
| `FECHACREACION` | `Date` |
| `FECHADESPACHOPEDIDO` | `Date` |
| `FECHAFINTSAP` | `Date` |
| `FECHAGRABACIONSRM` | `Date` |
| `FECHAINICIOTSAP` | `Date` |
| `FECHALIBERACIONDIRECTOR` | `Date` |
| `FECHALIBERACIONDYS` | `Date` |
| `FECHALIBERACIONTSAP` | `Date` |
| `FECHAMODIFICACION` | `Text` |
| `FECHANPEDIDO` | `Date` |
| `FECHARECHAZONPEDIDO` | `Date` |
| `FECHARECHAZOSOLPED` | `Date` |
| `FECHASOLPED` | `Date` |
| `FECHASRM` | `Date` |
| `IMPORTEADJUDICADO` | `Double` |
| `NAcreedorSAP` | `Integer` |
| `NPEDIDO` | `Text` |
| `OBSERVACIONES` | `Text` |
| `REQUIERECARTADIRECTOR` | `Boolean` |
| `REQUIERECARTANPEDIDOSUMINISTRADOR` | `Boolean` |
| `SOLPED` | `Text` |
| `SRM` | `Text` |
| `TIPOPEDIDO` | `Text` |
| `USUARIO` | `Text` |

#### Tabla: `Errores de pegado`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `F1` | `Double` |
| `F2` | `Date` |
| `F3` | `Double` |
| `F4` | `Text` |

#### Tabla: `TbAdjudicacionesEnvioAlSuministrador`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaEnvio` | `Date` |
| `IDCorreo` | `Integer` |
| `IDEnvio` | `Integer` |
| `IDSalida` | `Integer` |
| `NCarta` | `Integer` |
| `NDPD` | `Text` |
| `NSalida` | `Text` |
| `NombreTabla` | `Text` |
| `emailSuministrador` | `Text (Long)` |

#### Tabla: `TbAdjudicacionesOfertasCartas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `EMAIL` | `Text` |
| `FECHACARTA` | `Date` |
| `FechaMarcadaParaNoEnvio` | `Date` |
| `IDAnexo` | `Integer` |
| `IMPORTEOFERTA` | `Double` |
| `NAcreedor` | `Integer` |
| `NCarta` | `Integer` |
| `NDPD` | `Text` |
| `NPedido` | `Text` |
| `TEXTOOFERTA` | `Text (Long)` |
| `TEXTORECTIFICATORIO` | `Text (Long)` |

#### Tabla: `TbAmbitoConsultas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AmbitoConsulta` | `Text` |
| `IdAmbitoConsulta` | `Integer` |

#### Tabla: `TbAuxExp`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Adjudicado` | `Boolean` |
| `AñosGarantia` | `Double` |
| `Expediente` | `Text` |
| `FECHAADJUDICACION` | `Date` |
| `FechaFinTotal` | `Date` |
| `FechaRecepcion` | `Date` |
| `FirmadelContrato` | `Date` |
| `IdExpediente` | `Integer` |
| `Obs` | `Text (Long)` |
| `TITULOEXP` | `Text (Long)` |

#### Tabla: `TbAuxExpedientesUsuario`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDExpediente` | `Integer` |
| `Usuario` | `Text` |

#### Tabla: `TbAuxExpedientesVivos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDExpediente` | `Integer` |

#### Tabla: `TbAuxGTV`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text` |
| `FechaFin` | `Date` |
| `FechaInicio` | `Date` |
| `ImporteRestante` | `Double` |
| `NContrato` | `Text` |
| `NombreEmpresa` | `Text` |
| `Usuario` | `Text` |

#### Tabla: `TbAuxIDFactura`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDFactura` | `Integer` |

#### Tabla: `TbAuxPilar`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FECHASRM` | `Date` |
| `NPEDIDO` | `Text` |
| `SRM` | `Text` |

#### Tabla: `TbAuxPrado`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Cantidad` | `Double` |
| `Cesta_Contrato` | `Text` |
| `Cesta_z01` | `Text` |
| `DOCUMENTO` | `Text` |
| `DPD` | `Text` |
| `Empresa` | `Text` |
| `FECHASRM` | `Date` |
| `Fecha` | `Date` |
| `NºFactura` | `Text` |
| `SRM` | `Text` |
| `Visado Técnico` | `Text` |

#### Tabla: `TbAvalesAnexo`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodInternoAval` | `Integer` |
| `URLAval` | `Text` |

#### Tabla: `TbAvalesCancelacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodInternoAval` | `Integer` |
| `FechaDevolucionAvalTGestiona` | `Date` |
| `FechaNotificacionClienteLiberalizacionAval` | `Date` |
| `FechaOrdenCancelacionAval` | `Date` |
| `FechaRecogidaAvalCGD` | `Date` |
| `Observaciones` | `Text (Long)` |

#### Tabla: `TbAvalesDatosGenerales`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AFavorDe` | `Text` |
| `CIFCliente` | `Text` |
| `Cliente` | `Text` |
| `ConceptoAval` | `Text` |
| `CorreoContactoTGestiona` | `Text` |
| `Dependencia` | `Text` |
| `DireccionContactoCliente` | `Text` |
| `DireccionSolicitante` | `Text` |
| `EntidadAvalada` | `Text` |
| `FaxSolicitante` | `Integer` |
| `FaxTGestiona` | `Integer` |
| `GerenciaSolicitante` | `Text` |
| `NombreContactoCliente` | `Text` |
| `NombreContactoTGestiona` | `Text` |
| `NombreJefeContactoTGestiona` | `Text` |
| `NombreResponsableSolicitud` | `Text` |
| `Organismo` | `Text` |
| `TlfnoContactoCliente` | `Integer` |
| `TlfnoContactoTGestiona` | `Integer` |
| `TlfnoJefeContactoTGestiona` | `Integer` |
| `TlfnoResponsableSolicitud` | `Integer` |

#### Tabla: `TbAvalesDatosGeneralesNuevos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AFavorDe` | `Text` |
| `CIFCliente` | `Text` |
| `Cliente` | `Text` |
| `Dependencia` | `Text` |
| `DireccionSolicitante` | `Text` |
| `EntidadAvalada` | `Text` |
| `FaxTGestiona` | `Integer` |
| `NombreContactoArea` | `Text` |
| `NombreResponsableSolicitud` | `Text` |
| `NombreSolicitante` | `Text` |
| `Organismo` | `Text` |
| `TlfnoContactoArea` | `Integer` |
| `TlfnoSolicitante` | `Integer` |
| `emailContactoArea` | `Text` |
| `emailResponsable` | `Text` |
| `emailSolicitante` | `Text` |

#### Tabla: `TbAvalesFacturasClienteVinculo`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `NFactura` | `Text` |
| `codAval` | `Integer` |

#### Tabla: `TbAvalesInicio`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AFavorDe` | `Text` |
| `AreaContratante` | `Text` |
| `CIFCliente` | `Text` |
| `CODEXPLARGO` | `Text` |
| `ClaseAval` | `Text` |
| `Cliente` | `Text` |
| `CodInternoAval` | `Integer` |
| `ConceptoAval` | `Text` |
| `CorreoContactoTGestiona` | `Text` |
| `Dependencia` | `Text` |
| `DireccionContactoCliente` | `Text` |
| `DireccionSolicitante` | `Text` |
| `EntidadAvalada` | `Text` |
| `FaxSolicitante` | `Integer` |
| `FaxTGestiona` | `Integer` |
| `FechaInicioGestionAval` | `Date` |
| `FechaPrevistaLiberizacion` | `Date` |
| `FechaVencimiento` | `Date` |
| `GerenciaSolicitante` | `Text` |
| `IDExpediente` | `Integer` |
| `ImporteAval` | `Double` |
| `NombreContactoArea` | `Text` |
| `NombreContactoCliente` | `Text` |
| `NombreContactoTGestiona` | `Text` |
| `NombreJefeContactoTGestiona` | `Text` |
| `NombreResponsableSolicitud` | `Text` |
| `NombreSolicitante` | `Text` |
| `OrdenAnual` | `Text` |
| `Organismo` | `Text` |
| `TecnicoQuePideElAval` | `Text` |
| `TextoExpediente` | `Text` |
| `TlfnoAreaContratante` | `Integer` |
| `TlfnoContactoArea` | `Integer` |
| `TlfnoContactoCliente` | `Integer` |
| `TlfnoContactoTGestiona` | `Integer` |
| `TlfnoJefeContactoTGestiona` | `Integer` |
| `TlfnoResponsableSolicitud` | `Integer` |
| `TlfnoSolicitante` | `Integer` |
| `año` | `Text` |
| `emailContactoArea` | `Text` |
| `emailResponsable` | `Text` |
| `emailSolicitante` | `Text` |

#### Tabla: `TbAvalesInicioNuevo`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodInternoAval` | `Integer` |
| `DATOS_AVAL_AREA_CONTRATANTE_CONTACTO` | `Text (Long)` |
| `DATOS_AVAL_CIF_NIF` | `Text` |
| `DATOS_AVAL_CLASE` | `Text` |
| `DATOS_AVAL_CLIENTE_BENEFICIARIO` | `Text (Long)` |
| `DATOS_AVAL_DIVISA` | `Text` |
| `DATOS_AVAL_FECHA_PREVISTA_LIBERALIZACION` | `Date` |
| `DATOS_AVAL_FIRMAS_LEGITIMADAS` | `Text` |
| `DATOS_AVAL_IC_FECHA` | `Date` |
| `DATOS_AVAL_IC_LUGAR_RECOGIDA` | `Text` |
| `DATOS_AVAL_IC_SIADE` | `Text` |
| `DATOS_AVAL_IC_SOLICITANTE` | `Text` |
| `DATOS_AVAL_IMPORTE` | `Double` |
| `DATOS_AVAL_INTERVENIDO` | `Text` |
| `DATOS_AVAL_SEGUN_MODELO` | `Text` |
| `DATOS_AVAL_TEXTO_CONCEPTO` | `Text (Long)` |
| `FechaInicioGestionAval` | `Date` |
| `IDEXPEDIENTE` | `Integer` |
| `MOTIVO_NO_TRAMITACION` | `Text (Long)` |
| `OTRAS_SOCIEDADES_AVALADAS` | `Text (Long)` |
| `OrdenAnual` | `Text` |
| `SOCIEDAD_AVALADA` | `Text` |
| `SOLICITUD_DIRECCION_Y_AREA` | `Text (Long)` |
| `SOLICITUD_PERSONA_CONTACTO_AREA_EMAIL` | `Text` |
| `SOLICITUD_PERSONA_CONTACTO_AREA_NOMBRE` | `Text` |
| `SOLICITUD_PERSONA_CONTACTO_AREA_TELEFONO` | `Text` |
| `SOLICITUD_PERSONA_RESPONABLE_AREA_NOMBRE` | `Text` |
| `SOLICITUD_PERSONA_RESPONSABLE_AREA_EMAIL` | `Text` |
| `SOLICITUD_PERSONA_RESPONSABLE_AREA_TELEFONO` | `Text` |
| `SOLICITUD_SOLICITANTE_EMAIL` | `Text` |
| `SOLICITUD_SOLICITANTE_NOMBRE` | `Text` |
| `SOLICITUD_SOLICITANTE_TELEFONO` | `Text` |
| `TRAMITADO` | `Text` |
| `año` | `Text` |

#### Tabla: `TbAvalesObtencionAvalYDeposito`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodInternoAval` | `Integer` |
| `DireccionEntidadBancaria` | `Text` |
| `Entidad Bancaria` | `Text` |
| `FechaDeposito` | `Date` |
| `FechaEntregaAlCliente` | `Date` |
| `FechaRecogidaPrevista` | `Date` |
| `FechaRecogidaReal` | `Date` |
| `NAval` | `Text` |
| `NREGISTROCGD` | `Text` |

#### Tabla: `TbAvalesSolicitudSIADE`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodInternoAval` | `Integer` |
| `FechaAprovacion` | `Date` |
| `FechaSolicitudSIADE` | `Date` |
| `SIADE` | `Text` |

#### Tabla: `TbBloqueos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `BLOQUEADO` | `Boolean` |
| `BLOQUEANTE` | `Text` |
| `CODPROYECTOS` | `Text` |
| `OBSERVACIONES` | `Text (Long)` |

#### Tabla: `TbCSS`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text` |
| `HTML` | `Text (Long)` |
| `IDCSS` | `Integer` |

#### Tabla: `TbCalendarioProvisiones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaFinalProvision` | `Date` |
| `FechaInicialProvision` | `Date` |
| `IdProvision` | `Integer` |
| `Observaciones` | `Text (Long)` |

#### Tabla: `TbCalendarioProvisionesDetalle`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Cesta` | `Text` |
| `Empresa` | `Text` |
| `Expediente` | `Text` |
| `FNPedido` | `Date` |
| `FechaCesta` | `Date` |
| `IDProvision` | `Integer` |
| `IDProvisionDetalle` | `Integer` |
| `ImporteAdjudicado` | `Double` |
| `ImporteSolicitado` | `Double` |
| `NContrato` | `Text` |
| `NDPD` | `Text` |
| `NPedido` | `Text` |
| `Peticionario` | `Text` |
| `Posicion` | `Text` |
| `Pte_Facturar` | `Double` |
| `Responsables` | `Text (Long)` |

#### Tabla: `TbCestasAnexosOrdinaria`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Cesta` | `Text` |
| `IDCestaAnexo` | `Integer` |
| `IDTipoAnexoOrdinaria` | `Integer` |
| `URLFinal` | `Text` |
| `URLLocal` | `Text` |

#### Tabla: `TbCestasTiposDocumentos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaAlta` | `Date` |
| `FechaBaja` | `Date` |
| `ID` | `Integer` |
| `NombreDocumento` | `Text` |

#### Tabla: `TbComunicados`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Emisor` | `Text` |
| `FechaComunicado` | `Date` |
| `IDComunicado` | `Integer` |
| `TextoComunicado` | `Text (Long)` |
| `Titulo` | `Text` |
| `URLDocumentoAmplicacion` | `Text` |

#### Tabla: `TbComunicadosUsuario`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDComunicado` | `Integer` |
| `Mostrar` | `Text` |
| `strUsuario` | `Text` |

#### Tabla: `TbConexiones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Exitoso` | `Text` |
| `InstaladoFW3` | `Text` |
| `InstaladoFW4` | `Text` |
| `UltimaConexion` | `Date` |
| `UltimaDesconexion` | `Date` |
| `Usuario` | `Text` |

#### Tabla: `TbConexionesAGEDYSECO`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Exitoso` | `Text` |
| `InstaladoFW3` | `Text` |
| `InstaladoFW4` | `Text` |
| `UltimaConexion` | `Date` |
| `UltimaDesconexion` | `Date` |
| `Usuario` | `Text` |

#### Tabla: `TbConexionesAGEDYSTEC`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Exitoso` | `Text` |
| `InstaladoFW3` | `Text` |
| `InstaladoFW4` | `Text` |
| `UltimaConexion` | `Date` |
| `UltimaDesconexion` | `Date` |
| `Usuario` | `Text` |

#### Tabla: `TbConsultasDetalle`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Compleja` | `Integer` |
| `DescripcionConsulta` | `Text (Long)` |
| `IDCategoria` | `Integer` |
| `IDConsulta` | `Integer` |
| `NombreConsulta` | `Text` |
| `SQLConsulta` | `Text (Long)` |
| `SQLSimple` | `Text (Long)` |
| `TbAux` | `Text` |

#### Tabla: `TbConsultasOpciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ClaveNodo` | `Text` |
| `ClavePadre` | `Text` |
| `DescripcionNodo` | `Text (Long)` |
| `IdElemento` | `Integer` |
| `ImagenNodo` | `SmallInt` |
| `NombreNodo` | `Text` |
| `Observaciones` | `Text` |
| `SQLNodo` | `Text (Long)` |

#### Tabla: `TbConsultasPrincipal`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DescripcionCategoria` | `Text (Long)` |
| `IDCategoria` | `Integer` |
| `NombreCategoria` | `Text` |

#### Tabla: `TbCorreoDiferidoNotas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaEnvio` | `Date` |
| `FechaNota` | `Date` |
| `IDCorreo` | `Integer` |
| `IDEvento` | `Integer` |
| `Observaciones` | `Text (Long)` |

#### Tabla: `TbCriteriosSuministrador`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Condiciones` | `Text` |
| `Criterio` | `Text` |
| `IDCriterio` | `Integer` |

#### Tabla: `TbDPDCartaSolicitudOfertaDatos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ARCHIVOPARACARTA` | `Text` |
| `ATTPARACARTA` | `Text` |
| `CLASEOBRAPARACARTA` | `Text` |
| `CODUNIDADRESPONSABLE` | `Text` |
| `CPDYS` | `Text` |
| `DESCRIPCIONPARACARTA` | `Text` |
| `DESTINOPARACARTA` | `Text` |
| `DIRDys` | `Text` |
| `EMAILGERENCIA` | `Text` |
| `FAXGERENCIA` | `Text` |
| `FFINAL` | `Date` |
| `FINICIAL` | `Date` |
| `FORMAPAGODIAS` | `Text` |
| `FechaCarta` | `Date` |
| `FechaComunicacionSecretaria` | `Date` |
| `FechaRegistro` | `Date` |
| `GENERALPARACARTA` | `Text (Long)` |
| `GERENCIA` | `Text` |
| `MOTIVOOBRAPARACARTA` | `Text` |
| `NAcreedor` | `Integer` |
| `NDPD` | `Text` |
| `NOMBREPERSONACONTACTO1PARACARTA` | `Text` |
| `NOMBREPERSONACONTACTO2PARACARTA` | `Text` |
| `NombreDireccionDys` | `Text` |
| `PETICIONARIOPARACARTA` | `Text` |
| `PedidoPropiedadDelCliente` | `Boolean` |
| `RB01` | `Text` |
| `RB02` | `Text` |
| `RS01` | `Text` |
| `TELGERENCIA` | `Text` |
| `TELPERSONACONTACTO1PARACARTA` | `Text` |
| `TELPERSONACONTACTO2PARACARTA` | `Text` |
| `TEXTOEQUIPAMIENTOPARACARTA` | `Text (Long)` |
| `TEXTOREQUISITOSOTAN` | `Text (Long)` |
| `TEXTOTRAMITACIONFACTURAS` | `Text (Long)` |
| `TipoDPD` | `Text` |
| `TipoMaterial` | `Text` |
| `URLEXCELEQUIPAMIENTOPARACARTA` | `Text` |
| `UsuarioQueRegistra` | `Text` |

#### Tabla: `TbDPDComiteOfertas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODDPD` | `Text` |
| `COMITEOFERTA` | `Text` |
| `FECHACOMITEOFERTA` | `Date` |
| `FechaRegistro` | `Date` |
| `UsuarioRegistro` | `Text` |

#### Tabla: `TbDPDOfertaSuministrador`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FECHACONVERSIONAPDFSOLICITUD` | `Date` |
| `FECHAREALIZACIONCARTASOLICITUD` | `Date` |
| `FECHARECEPCIONOFERTASUMINISTRADOR` | `Date` |
| `NDPD` | `Text` |
| `OBSERVACIONESRECEPCIONOFERTA` | `Text (Long)` |
| `OBSERVACIONESSOLICITUDOFERTA` | `Text (Long)` |

#### Tabla: `TbDPDPlantillasParaCartaSolicitudDeOFerta`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `NombrePlantilla` | `Text` |
| `Observaciones` | `Text (Long)` |
| `RequisitoBasico` | `Text` |

#### Tabla: `TbDatosEconomicosExpedientes`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CosteExternoPrevisto` | `Double` |
| `CosteInternoPrevisto` | `Double` |
| `GastoMaximoPrevisto` | `Double` |
| `IDExpediente` | `Integer` |
| `InversionPrevista` | `Double` |
| `MontoTotal` | `Double` |
| `Observaciones` | `Text` |

#### Tabla: `TbDireccionesSuministradores`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `LineaDireccion1` | `Text` |
| `LineaDireccion2` | `Text` |
| `LineaDireccion3` | `Text` |
| `LineaDireccion4` | `Text` |
| `LineaDireccion5` | `Text` |
| `Suministrador` | `Text` |

#### Tabla: `TbDpDAsuntoDefensa`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AsuntoDefensa` | `Boolean` |
| `CODPROYECTO` | `Text` |

#### Tabla: `TbDpDCartaSolicitudOfertaDatosFijos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODUNIDADRESPONSABLE` | `Text` |
| `CPDYS` | `Text` |
| `DIRDys` | `Text` |
| `EMAILGERENCIA` | `Text` |
| `FAXGERENCIA` | `Text` |
| `FORMAPAGODIAS` | `Text` |
| `GERENCIA` | `Text` |
| `NombreDireccionDys` | `Text` |
| `TELGERENCIA` | `Text` |
| `TEXTOREQUISITOSOTAN` | `Text (Long)` |
| `TEXTOTRAMITACIONFACTURAS` | `Text (Long)` |

#### Tabla: `TbDpDCartaSolicitudOfertaPlantillasSegunReqBasicos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ClaseObra` | `Text` |
| `Observaciones` | `Text (Long)` |
| `Pagina3Nombre` | `Text` |
| `ParaDefensa` | `Boolean` |
| `RequiereRB01` | `Boolean` |
| `RequiereRB02` | `Boolean` |
| `RequiereRS01` | `Boolean` |
| `TipoDPD` | `Text` |
| `TipoMaterial` | `Text` |

#### Tabla: `TbDpDDocAnexada`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DESCRIPCIONDOC` | `Text (Long)` |
| `FechaAnexion` | `Date` |
| `IDDocumento` | `Integer` |
| `NCartaAdjudicacion` | `Text` |
| `NDPD` | `Text` |
| `NRegistroCompletoEntrada` | `Text` |
| `NRegistroCompletoSalida` | `Text` |
| `ObservacionesDocAnexada` | `Text (Long)` |
| `QUIENLOGENERA` | `Text` |
| `TIPODOC` | `Text` |
| `TITULODOC` | `Text` |
| `URLDOC` | `Text` |
| `URLFINAL` | `Text (Long)` |

#### Tabla: `TbDpDInformeCondicionamiento`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodProyecto` | `Text` |
| `CorreoComprador` | `Text` |
| `CorreoDireccionAsunto` | `Text` |
| `CorreoDireccionCC` | `Text` |
| `CorreoDireccionCuerpo` | `Text (Long)` |
| `CorreoDireccionPara` | `Text` |
| `FechaCartaCondRealizada` | `Date` |
| `FechaCausasEscritas` | `Date` |
| `FechaQuitaObligacionInformeCond` | `Date` |
| `FechaRequiereInformeCond` | `Date` |
| `Observaciones` | `Text (Long)` |
| `RequiereInformeCond` | `Text` |
| `URLCartaAutorizacion` | `Text` |
| `URLCartaCondicionamientoRealizada` | `Text` |
| `URLCausasCondicionamiento` | `Text` |
| `UsuarioQuitaObligacionInformeCond` | `Text` |

#### Tabla: `TbDpDPrepCartaOfAcepDetalle`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FECHACARTA` | `Date` |
| `IMPORTEOFERTA` | `Double` |
| `NAcreedor` | `Integer` |
| `NCarta` | `Integer` |
| `NDPD` | `Text` |
| `NPEDIDO` | `Text` |
| `TEXTOOFERTA` | `Text` |

#### Tabla: `TbDpDPrepCartaOfAcepPrincipal`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ATT` | `Text` |
| `AnexadaCarta` | `Boolean` |
| `CPCarta` | `Text` |
| `CodExpediente` | `Text` |
| `DireccionCarta` | `Text` |
| `NAcreedor` | `Integer` |
| `NCarta` | `Integer` |
| `NDPD` | `Text` |
| `NREFERENCIA` | `Text` |
| `PoblacionCarta` | `Text` |

#### Tabla: `TbExpedientes`
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

#### Tabla: `TbExpedientesAnualidades`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Año` | `SmallInt` |
| `BIEXENTA` | `Double` |
| `BIIGIC` | `Double` |
| `BIIPSI` | `Double` |
| `BIIVA` | `Double` |
| `IDAnualidad` | `Integer` |
| `IDExpediente` | `Integer` |
| `IGIC` | `Double` |
| `IPSI` | `Double` |
| `IVA` | `Double` |
| `PeriodoFacturacion` | `Text` |

#### Tabla: `TbExpedientesAutorizaciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AutorizadoPor` | `Text` |
| `FechaAutorizacion` | `Date` |
| `IDAutorizacion` | `Integer` |
| `IDExpediente` | `Integer` |
| `MargenAnterior` | `Double` |
| `MargenNuevo` | `Double` |
| `Motivo` | `Text (Long)` |
| `NombreAdjunto` | `Text` |

#### Tabla: `TbExpedientesCodigoCompras`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CodCompras` | `Text` |
| `ID` | `Integer` |
| `IDExpediente` | `Integer` |

#### Tabla: `TbExpedientesDocRequeridos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaPrevista` | `Date` |
| `FechaRealizado` | `Date` |
| `IDDocRequerido` | `Integer` |
| `IDDocumento` | `Integer` |
| `IDExpediente` | `Integer` |
| `NombreDocumento` | `Text` |

#### Tabla: `TbExpedientesProrrogas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `BIEXENTA` | `Double` |
| `BIIGIC` | `Double` |
| `BIIPSI` | `Double` |
| `BIIVA` | `Double` |
| `FechaFin` | `Date` |
| `FechaInicio` | `Date` |
| `IDExpediente` | `Integer` |
| `IDProrroga` | `Integer` |
| `IGIC` | `Double` |
| `IPSI` | `Double` |
| `IVA` | `Double` |
| `Observaciones` | `Text (Long)` |
| `PeriodoFacturacion` | `Text` |

#### Tabla: `TbFacturaInformeMatFalsicado`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DD` | `Text` |
| `DDDañoEquipo` | `Text` |
| `DDDañosEmbalaje` | `Text` |
| `DDEntregaIncompleta` | `Text` |
| `DDFaltanRegistros` | `Text` |
| `DDIncumplimientoReq` | `Text` |
| `DDInsuficienteDoc` | `Text` |
| `DDRetrasoPlazos` | `Text` |
| `DOC` | `Text` |
| `EF` | `Text` |
| `EFIC` | `Text` |
| `EFIR` | `Text` |
| `EM` | `Text` |
| `EQ` | `Text` |
| `ET` | `Text` |
| `FechaInspeccion` | `Date` |
| `IDMF` | `Integer` |
| `InspectorNombre` | `Text` |
| `JPNombre` | `Text` |
| `NFactura` | `Text` |
| `NPedido` | `Text` |
| `Observaciones` | `Text (Long)` |
| `PH` | `Text` |

#### Tabla: `TbFacturasCliente`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `BASEEXENTA` | `Double` |
| `BASEIMPONIBLE` | `Double` |
| `CODEXP` | `Text` |
| `FECHAEMISION` | `Date` |
| `FechaGrabacion` | `Date` |
| `Grabador` | `Text` |
| `IDExpediente` | `Integer` |
| `NFACTURA` | `Text` |
| `OBSERVACIONES` | `Text (Long)` |
| `TIPOFACTURA` | `Text` |
| `TIPOIMPOSITIVO` | `Double` |
| `URLFactura` | `Text` |

#### Tabla: `TbFacturasDetalle`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ExpAdjudicado` | `Text` |
| `FechaAceptacion` | `Date` |
| `FechaContabilizacion` | `Date` |
| `FechaFactura` | `Date` |
| `FechaGrabacion` | `Date` |
| `Grabador` | `Text` |
| `IDDocumentoIV02` | `Integer` |
| `IDFactura` | `Integer` |
| `ImporteFactura` | `Double` |
| `NDOCUMENTO` | `Text` |
| `NDPD` | `Text` |
| `NFactura` | `Text` |
| `NPEDIDO` | `Text` |
| `Observaciones` | `Text (Long)` |
| `SOLPED` | `Text` |
| `URLFACTURA` | `Text` |

#### Tabla: `TbFacturasDetalleNoDYS`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaContabilizacion` | `Date` |
| `FechaFactura` | `Date` |
| `IDFacturaNoDYS` | `Integer` |
| `ImporteFactura` | `Double` |
| `NAcreedorSAP` | `Integer` |
| `NDOCUMENTO` | `Text` |
| `NFactura` | `Text` |
| `NPEDIDO` | `Text` |
| `NombreArchivo` | `Text` |
| `Observaciones` | `Text (Long)` |

#### Tabla: `TbFacturasDetalleSinPedido`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ExpAdjudicado` | `Text` |
| `FechaFactura` | `Date` |
| `FechaGrabacion` | `Date` |
| `FechaGrabacionNPedidoTSAP` | `Date` |
| `FechaNPedidoPorTecnico` | `Date` |
| `Grabador` | `Text` |
| `IDFactura` | `Integer` |
| `ImporteFactura` | `Double` |
| `NAcreedor` | `Integer` |
| `NDOCUMENTO` | `Text` |
| `NFactura` | `Text` |
| `NPEDIDO` | `Text` |
| `Observaciones` | `Text (Long)` |
| `ObservacionesEconomicas` | `Text (Long)` |
| `ObservacionesTecnicas` | `Text (Long)` |
| `URLFACTURA` | `Text` |
| `UsuarioRedDestinatario` | `Text` |

#### Tabla: `TbFacturasPrincipal`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Estado` | `Text` |
| `FechaEstado` | `Date` |
| `NDPD` | `Text` |
| `NPedido` | `Text` |
| `SOLPED` | `Text` |

#### Tabla: `TbGTV`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODARTICULO` | `Text` |
| `DESCRIPCIONGTV` | `Text` |
| `FECHAFINAL` | `Date` |
| `FECHAGRABACION` | `Date` |
| `FECHAINICIAL` | `Date` |
| `FECHASOLPED` | `Date` |
| `FECHASRM` | `Date` |
| `IDGTV` | `Integer` |
| `IMPORTESOLICITADO` | `Double` |
| `ObservacionesGTV` | `Text (Long)` |
| `SOLPED` | `Text` |
| `SRM` | `Text` |
| `URLSolicitud` | `Text` |

#### Tabla: `TbGTVContratos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODOFERTA` | `Text` |
| `IDGTV` | `Integer` |
| `IDGTVContrato` | `Integer` |
| `IMPORTEADJUDICADO` | `Double` |
| `NAcreedor` | `Integer` |
| `NCONTRATOGTV` | `Text` |
| `POSICION` | `Integer` |
| `URLOferta` | `Text` |

#### Tabla: `TbGTVContratosExpedientes`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ID` | `Integer` |
| `IDExpediente` | `Integer` |
| `IDGTVContrato` | `Integer` |

#### Tabla: `TbGTV_Temp`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DescripcionGTVTemp` | `Text (Long)` |
| `FechaFinalTemp` | `Date` |
| `FechaInicialTemp` | `Date` |
| `Id` | `Integer` |
| `ImporteInicialTemp` | `Double` |
| `ImporteRestanteTemp` | `Double` |
| `NAcreedorTemp` | `Integer` |
| `NContratoTemp` | `Text` |
| `NombreSuministradorTemp` | `Text` |
| `ObservacionesTemp` | `Text (Long)` |
| `PosicionTemp` | `Integer` |

#### Tabla: `TbHerramientaDocAyuda`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `NombreArchivoAyuda` | `Text` |
| `NombreFormulario` | `Text` |

#### Tabla: `TbLog`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Accion` | `Text (Long)` |
| `FechaAccion` | `Date` |
| `ID` | `Integer` |
| `IDGTV` | `Integer` |
| `NDPD` | `Text` |
| `Titulo` | `Text` |

#### Tabla: `TbNPedido`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODCONTRATOGTV` | `Text` |
| `CODPPD` | `Text` |
| `EMPRESAADJUDICATARIA` | `Text` |
| `ESORDINARIO` | `Text` |
| `FECHAANEXOCARTADIRECTORTSAP` | `Date` |
| `FECHABORRADA` | `Date` |
| `FECHACARTADIRECTORREALIZADA` | `Date` |
| `FECHACARTASUMINISTRADORREALIZADA` | `Date` |
| `FECHACOMUNICACIONCARTADIRECTOR` | `Date` |
| `FECHACOMUNICACIONCARTASUMINISTRADOR` | `Date` |
| `FECHACOMUNICACIONMARILO` | `Date` |
| `FECHACREACION` | `Date` |
| `FECHADESPACHOPEDIDO` | `Date` |
| `FECHAFINTSAP` | `Date` |
| `FECHAGRABACIONSRM` | `Date` |
| `FECHAINICIOTSAP` | `Date` |
| `FECHALIBERACIONDIRECTOR` | `Date` |
| `FECHALIBERACIONDYS` | `Date` |
| `FECHALIBERACIONTSAP` | `Date` |
| `FECHAMODIFICACION` | `Text` |
| `FECHANPEDIDO` | `Date` |
| `FECHARECHAZONPEDIDO` | `Date` |
| `FECHARECHAZOSOLPED` | `Date` |
| `FECHASOLPED` | `Date` |
| `FECHASRM` | `Date` |
| `IMPORTEADJUDICADO` | `Double` |
| `NAcreedorSAP` | `Integer` |
| `NPEDIDO` | `Text` |
| `OBSERVACIONES` | `Text` |
| `REQUIERECARTADIRECTOR` | `Boolean` |
| `REQUIERECARTANPEDIDOSUMINISTRADOR` | `Boolean` |
| `SOLPED` | `Text` |
| `SRM` | `Text` |
| `TIPOPEDIDO` | `Text` |
| `USUARIO` | `Text` |

#### Tabla: `TbNPedidoAntes`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODCONTRATOGTV` | `Text` |
| `CODPPD` | `Text` |
| `EMPRESAADJUDICATARIA` | `Text` |
| `FECHAANEXOCARTADIRECTORTSAP` | `Date` |
| `FECHABORRADA` | `Date` |
| `FECHACARTADIRECTORREALIZADA` | `Date` |
| `FECHACARTASUMINISTRADORREALIZADA` | `Date` |
| `FECHACOMUNICACIONCARTADIRECTOR` | `Date` |
| `FECHACOMUNICACIONCARTASUMINISTRADOR` | `Date` |
| `FECHACOMUNICACIONMARILO` | `Date` |
| `FECHACREACION` | `Date` |
| `FECHADESPACHOPEDIDO` | `Date` |
| `FECHAFINTSAP` | `Date` |
| `FECHAINICIOTSAP` | `Date` |
| `FECHALIBERACIONDIRECTOR` | `Date` |
| `FECHALIBERACIONDYS` | `Date` |
| `FECHALIBERACIONTSAP` | `Date` |
| `FECHAMODIFICACION` | `Text` |
| `FECHANPEDIDO` | `Date` |
| `FECHARECHAZONPEDIDO` | `Date` |
| `FECHARECHAZOSOLPED` | `Date` |
| `FECHASOLPED` | `Date` |
| `IDEmpresaAdjudicataria` | `Integer` |
| `IMPORTEADJUDICADO` | `Double` |
| `NPEDIDO` | `Text` |
| `OBSERVACIONES` | `Text` |
| `REQUIERECARTADIRECTOR` | `Boolean` |
| `REQUIERECARTANPEDIDOSUMINISTRADOR` | `Boolean` |
| `SOLPED` | `Text` |
| `TIPOPEDIDO` | `Text` |
| `USUARIO` | `Text` |

#### Tabla: `TbNPedidosHistorica`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODCONTRATOGTV` | `Text` |
| `CODPPD` | `Text` |
| `EMPRESAADJUDICATARIA` | `Text` |
| `FECHAANEXOCARTADIRECTORTSAP` | `Date` |
| `FECHABORRADA` | `Date` |
| `FECHACARTADIRECTORREALIZADA` | `Date` |
| `FECHACARTASUMINISTRADORREALIZADA` | `Date` |
| `FECHACOMUNICACIONCARTADIRECTOR` | `Date` |
| `FECHACOMUNICACIONCARTASUMINISTRADOR` | `Date` |
| `FECHACOMUNICACIONMARILO` | `Date` |
| `FECHACREACION` | `Date` |
| `FECHADESPACHOPEDIDO` | `Date` |
| `FECHAFINTSAP` | `Date` |
| `FECHAINICIOTSAP` | `Date` |
| `FECHALIBERACIONDIRECTOR` | `Date` |
| `FECHALIBERACIONDYS` | `Date` |
| `FECHALIBERACIONTSAP` | `Date` |
| `FECHAMODIFICACION` | `Text` |
| `FECHANPEDIDO` | `Date` |
| `FECHARECHAZONPEDIDO` | `Date` |
| `FECHARECHAZOSOLPED` | `Date` |
| `FECHASOLPED` | `Date` |
| `IMPORTEADJUDICADO` | `Double` |
| `NAcreedorSAP` | `Integer` |
| `NPEDIDO` | `Text` |
| `OBSERVACIONES` | `Text` |
| `REQUIERECARTADIRECTOR` | `Boolean` |
| `REQUIERECARTANPEDIDOSUMINISTRADOR` | `Boolean` |
| `SOLPED` | `Text` |
| `TIPOPEDIDO` | `Text` |
| `USUARIO` | `Text` |

#### Tabla: `TbNuevosProductos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Articulo` | `Text` |
| `Cod` | `Text` |
| `FechaObsoleto` | `Date` |

#### Tabla: `TbOrdinariasTipoAnexos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDTipoAnexo` | `Integer` |
| `Nombre` | `Text` |
| `ParaMasDe10K` | `Text` |
| `ParaMenosDe10K` | `Text` |
| `RecursoInterno` | `Text` |
| `URLRecurso` | `Text` |

#### Tabla: `TbProductos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Codigo` | `Text` |
| `Descripcion` | `Text (Long)` |
| `Nombre` | `Text` |

#### Tabla: `TbProductosObsoletos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CODARTICULO` | `Text` |

#### Tabla: `TbProductosParaBusqueda`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Codigo` | `Text` |
| `Observaciones` | `Text (Long)` |
| `PalabraClave` | `Text` |

#### Tabla: `TbProductos_antes`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Codigo` | `Text` |
| `Descripcion` | `Text (Long)` |
| `Nombre` | `Text` |

#### Tabla: `TbProyectos`
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

#### Tabla: `TbProyectosDocumentosParaPedidoOrdinario`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Cesta` | `Text` |
| `FechaEntregado` | `Date` |
| `FechaSolicitado` | `Date` |
| `IDTipoDocumento` | `Integer` |
| `NDPD` | `Text` |
| `Observaciones` | `Text (Long)` |
| `URLFinal` | `Text` |

#### Tabla: `TbProyectosHistoricos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `AnexoOfertaSuministrador` | `Text` |
| `AntesDeVersion2` | `Boolean` |
| `AÑOPRESUPUESTO` | `Integer` |
| `CENTRO` | `Text` |
| `CODARTICULO` | `Text` |
| `CODCENTRO` | `Text` |
| `CODCONTRATOGTV` | `Text` |
| `CODOFERTASUMINISTRADOR` | `Text` |
| `CODPROYECTOS` | `Text` |
| `CONTINUAENVERSIONDOS` | `Boolean` |
| `CRITERIOCOMPRAS` | `Text` |
| `DEPENDENCIA` | `Text` |
| `DESCRIPCION` | `Text` |
| `ELIMINADO` | `Boolean` |
| `EXPEDIENTE` | `Text` |
| `FACTURAPAGADA` | `Boolean` |
| `FECHACERTIFICADOCONFORMIDAD` | `Date` |
| `FECHAOBRAENTREGASINREPAROS` | `Date` |
| `FECHAPETICION` | `Date` |
| `FECHARECEPCIONECONOMICA` | `Date` |
| `FECHAREPAROSSUBSANADOS` | `Date` |
| `FELIMINADO` | `Date` |
| `FFINNECESIDAD` | `Date` |
| `FINICIONECESIDAD` | `Date` |
| `FIRMADELTECNICO` | `Text` |
| `FREGISTRO` | `Date` |
| `FechaAnexoOfertaSuministrador` | `Date` |
| `IDSuministrador` | `Integer` |
| `ID_PROYECTOS` | `Integer` |
| `IMPORTESINIVA` | `Double` |
| `NAcreedorSAP` | `Integer` |
| `NOMBRECENTRO` | `Text` |
| `OBRAREPAROS` | `Boolean` |
| `OBSERVACIONES` | `Text (Long)` |
| `OBSERVACIONESCALIDAD` | `Text` |
| `OBSERVACIONESECONOMICAS` | `Text (Long)` |
| `OFERTAACEPTADA` | `Boolean` |
| `OFERTAACEPTADAFECHA` | `Date` |
| `OFERTARECIBIDA` | `Boolean` |
| `OFERTARECIBIDAFECHA` | `Date` |
| `PETICIONARIO` | `Text` |
| `REPAROSSUBSANADOS` | `Boolean` |
| `TEXTOCERTIFICADOCONFORMIDAD` | `Text` |
| `TIPOPEDIDO` | `Text` |

#### Tabla: `TbRequisitosSTG`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `A0` | `Text` |
| `A1` | `Text` |
| `A2` | `Text` |
| `A3` | `Text` |
| `A4` | `Text` |
| `B00` | `Text` |
| `B01` | `Text` |
| `B02` | `Text` |
| `B03` | `Text` |
| `B1` | `Text` |
| `B2` | `Text` |
| `B21` | `Text` |
| `B22` | `Text` |
| `B23` | `Text` |
| `B24` | `Text` |
| `B25` | `Text` |
| `B26` | `Text` |
| `C0` | `Text` |
| `C1` | `Text` |
| `C2` | `Text` |
| `C3` | `Text` |
| `D0` | `Text` |
| `D1` | `Text` |
| `D2` | `Text` |
| `D3` | `Text` |
| `D4` | `Text` |
| `E0` | `Text` |
| `E1` | `Text` |
| `E2` | `Text` |
| `E3` | `Text` |
| `F0` | `Text` |
| `F1` | `Text` |
| `F2` | `Text` |
| `F3` | `Text` |
| `F4` | `Text` |
| `F5` | `Text` |
| `F6` | `Text` |
| `F7` | `Text` |
| `G0` | `Text` |
| `G1` | `Text` |
| `G2` | `Text` |
| `G3` | `Text` |
| `H0` | `Text` |
| `I0` | `Text` |
| `I1` | `Text` |
| `I2` | `Text` |
| `I3` | `Text` |
| `I4` | `Text` |
| `J0` | `Text` |
| `J1` | `Text` |
| `J2` | `Text` |
| `J3` | `Text` |
| `J4` | `Text` |
| `J5` | `Text` |
| `K0` | `Text` |
| `K1` | `Text` |
| `K2` | `Text` |
| `K3` | `Text` |
| `K4` | `Text` |
| `L0` | `Text` |
| `L1` | `Text` |
| `L2` | `Text` |
| `L3` | `Text` |
| `L4` | `Text` |
| `M0` | `Text` |
| `M1` | `Text` |
| `M2` | `Text` |
| `M3` | `Text` |
| `M4` | `Text` |
| `M5` | `Text` |
| `M6` | `Text` |
| `M7` | `Text` |
| `NDPD` | `Text` |

#### Tabla: `TbResponsablesExpedientes`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CorreoSiempre` | `Text` |
| `IdExpediente` | `Integer` |
| `IdUsuario` | `Integer` |

#### Tabla: `TbSTGParametrosParaFormulario`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Letras` | `Text` |
| `Nombre` | `Text` |
| `NombreMarco` | `Text` |
| `NumeroCasillas` | `TinyInt` |

#### Tabla: `TbSolicitudesEnvioAlSuministrador`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaEnvio` | `Date` |
| `IDCorreo` | `Integer` |
| `IDEnvio` | `Integer` |
| `IDSO` | `Integer` |
| `IDSalida` | `Integer` |
| `NDPD` | `Text` |
| `NSalida` | `Text` |
| `NombreTabla` | `Text` |
| `emailSuministrador` | `Text (Long)` |

#### Tabla: `TbSolicitudesOfertasPrevias`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DPD` | `Text` |
| `FechaModificacion` | `Date` |
| `FechaRegistro` | `Date` |
| `IDCorreo` | `Integer` |
| `IDSO` | `Integer` |
| `IDSalida` | `Integer` |
| `NAcreedor` | `Integer` |
| `NombreArchivo` | `Text` |
| `NombreTabla` | `Text` |
| `UsuarioRegistra` | `Text` |
| `email` | `Text` |

#### Tabla: `TbSuministradoresDireccion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IdSuministrador` | `Integer` |
| `LineaDireccion1` | `Text` |
| `LineaDireccion2` | `Text` |
| `LineaDireccion3` | `Text` |
| `LineaDireccion4` | `Text` |

#### Tabla: `TbSuministradoresListaFavoritos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `NAcreedor` | `Text` |
| `NombreLista` | `Text` |
| `UsuarioRed` | `Text` |
| `email` | `Text` |

#### Tabla: `TbSuministradoresNotasReferencia`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Nota` | `Text` |
| `PuntuacionMaxima` | `Integer` |
| `PuntuacionMinima` | `Integer` |

#### Tabla: `TbSuministradoresPuntuacion`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FechaPuntuacion` | `Date` |
| `IDPuntuacion` | `Integer` |
| `IDSuministradorSAP` | `Integer` |
| `NDPD` | `Text` |
| `NFactura` | `Text` |
| `NPedido` | `Text` |
| `PuntuacionCalidad` | `SmallInt` |
| `PuntuacionServicio` | `SmallInt` |
| `Usuario` | `Text` |

#### Tabla: `TbSuministradoresPuntuacionConDetalle`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CA` | `SmallInt` |
| `CB` | `SmallInt` |
| `FechaPuntuacion` | `Date` |
| `IDPuntuacion` | `Integer` |
| `IDSuministradorSAP` | `Integer` |
| `IDVisado` | `Integer` |
| `NDOCUMENTO` | `Text` |
| `NDPD` | `Text` |
| `NFactura` | `Text` |
| `NPedido` | `Text` |
| `ObservacionesPuntuacion` | `Text (Long)` |
| `PuntuacionCalidad` | `Text` |
| `PuntuacionServicio` | `Text` |
| `SA` | `Integer` |
| `SB` | `SmallInt` |
| `SC` | `SmallInt` |
| `SD` | `SmallInt` |
| `SE` | `SmallInt` |
| `SF` | `SmallInt` |
| `SG` | `SmallInt` |
| `SH` | `SmallInt` |
| `Usuario` | `Text` |

#### Tabla: `TbSuministradoresSAP`
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

#### Tabla: `TbTareasTecnicasExplicaciones`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Explicacion` | `Text (Long)` |
| `NodoTarea` | `Text` |
| `TituloTarea` | `Text` |

#### Tabla: `TbTempDPDHTML`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ADFechaEnvio` | `Date` |
| `ADFechaEnvioSecretaria` | `Date` |
| `ADFechaRealiza` | `Date` |
| `CODCONTRATOGTV` | `Text` |
| `DESCRIPCION` | `Text (Long)` |
| `ESTADOPEDIDO` | `Text` |
| `EXPEDIENTE` | `Text` |
| `FECHANPEDIDO` | `Date` |
| `FECHAPETICION` | `Date` |
| `FECHARECEPCIONECONOMICA` | `Date` |
| `FECHASOLPED` | `Date` |
| `FELIMINADO` | `Date` |
| `FechaCausasEscritas` | `Date` |
| `FechaFinAgendaTecnica` | `Date` |
| `FechaMarcadaParaNoEnvio` | `Date` |
| `IMPORTEADJUDICADO` | `Currency` |
| `IMPORTEPORFACTURAR` | `Currency` |
| `IMPORTERESTANTEENCONTRATO` | `Currency` |
| `IMPORTESOLICITADO` | `Currency` |
| `NDPD` | `Text` |
| `NPEDIDO` | `Text` |
| `PETICIONARIO` | `Text` |
| `POSICIONCONTRATOGTV` | `Text` |
| `ROFechaRealiza` | `Date` |
| `ROFechaRechazo` | `Date` |
| `ROFechaVisado` | `Date` |
| `ROObservacionesRechazo` | `Text (Long)` |
| `ROObservacionesVisado` | `Text (Long)` |
| `RequiereInformeCond` | `Text` |
| `SOFechaEnvio` | `Date` |
| `SOFechaEnvioSecretaria` | `Date` |
| `SOFechaRealiza` | `Date` |
| `SOLPED` | `Text` |
| `SUMINISTRADORADJUDICADO` | `Text` |
| `SUMINISTRADORADJUDICADOCIF` | `Text` |
| `SUMINISTRADORADJUDICADOEMAIL` | `Text` |
| `SUMINISTRADORSOLICITADO` | `Text` |
| `SUMINISTRADORSOLICITADOCIF` | `Text` |
| `SUMINISTRADORSOLICITADOEMAIL` | `Text` |
| `TIPOPEDIDO` | `Text` |
| `URLCausasCondicionamiento` | `Text` |

#### Tabla: `TbTemp_PedidosEstado`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `EstadoPedido` | `Text` |
| `NDPD` | `Text` |

#### Tabla: `TbTipoDocumento`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `SiglaParaDocumentacion` | `Text` |
| `TipoDocumento` | `Text` |
| `TituloDocumentoPorDefecto` | `Text` |
| `Unico` | `Boolean` |
| `ordinal` | `Integer` |

#### Tabla: `TbTiposImpositivos`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text` |
| `TipoImpositivo` | `Double` |

#### Tabla: `TbTiposPedido`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DescripcionTipoPedido` | `Text` |
| `TipoPedido` | `Text` |

#### Tabla: `TbTmp_DPDs`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `EstadoDPD_Temp` | `Text` |
| `NDPD_Temp` | `Text` |

#### Tabla: `TbTmp_Facturas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CadenaIDCorreosNotasDeCalidad` | `Text` |
| `CodDPDTemp` | `Text` |
| `CodExpTmp` | `Text` |
| `DescripcionDPDTemp` | `Text` |
| `EstadoTmp` | `Text` |
| `FECHAPETICIONTemp` | `Date` |
| `FRECHAZOCALIDADTemp` | `Date` |
| `FRECHAZOECONOMICOTemp` | `Date` |
| `FRECHAZOTECNICOTemp` | `Date` |
| `FVISADOCALIDADTemp` | `Date` |
| `FVISADOECONOMICOTemp` | `Date` |
| `FVISADOTECNICOTemp` | `Date` |
| `FechaEnvioCorreo` | `Date` |
| `FechaFacturaTemp` | `Date` |
| `FechaGrabacionTemp` | `Date` |
| `GrabadorTemp` | `Text` |
| `IDFacturaTmp` | `Integer` |
| `ImporteFacturaTemp` | `Text` |
| `NAcreedorSAP` | `Integer` |
| `NDocumentoTemp` | `Text` |
| `NFacturaTmp` | `Text` |
| `NPedidoTmp` | `Text` |
| `ObsRechazoCalidad` | `Text (Long)` |
| `ObsRechazoTecnico` | `Text (Long)` |
| `ObservacionesTmp` | `Text (Long)` |
| `PeticionarioLargoTemp` | `Text` |
| `PeticionarioTemp` | `Text` |
| `RistraResponsablesExpTemp` | `Text` |
| `URLFacturaTemp` | `Text` |

#### Tabla: `TbUsuariosEnvioTareas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DiasEnvioTareas` | `Text` |
| `Usuario` | `Text` |

#### Tabla: `TbVisadoFacturas`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DevueltoPorCalidad` | `Boolean` |
| `FRECHAZOTECNICO` | `Date` |
| `FVISADOTECNICO` | `Date` |
| `FechaVisadoCalidad` | `Date` |
| `NDOCUMENTOFACTURA` | `Text` |
| `NDPD` | `Text` |
| `NFactura` | `Text` |
| `NPEDIDO` | `Text` |
| `OBSERVACIONESRECHAZO` | `Text (Long)` |
| `OBSERVACIONESVISADOFACTURA` | `Text (Long)` |
| `ObservacionesVisadoCalidad` | `Text (Long)` |
| `USUARIOQUERECHAZA` | `Text` |
| `USUARIOQUEVISA` | `Text` |
| `UsuarioCalidad` | `Text` |

#### Tabla: `TbVisadoFacturas_Nueva`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `FRECHAZOCALIDAD` | `Date` |
| `FRECHAZOECONOMICO` | `Date` |
| `FRECHAZOTECNICO` | `Date` |
| `FVISADOCALIDAD` | `Date` |
| `FVISADOECONOMICO` | `Date` |
| `FVISADOTECNICO` | `Date` |
| `IDFactura` | `Integer` |
| `IDVisado` | `Integer` |
| `NDOCUMENTO` | `Text` |
| `NDPD` | `Text` |
| `NFactura` | `Text` |
| `NPEDIDO` | `Text` |
| `OBSERVACIONESCALIDADPARAECONOMIA` | `Text (Long)` |
| `OBSERVACIONESCALIDADRECHAZA` | `Text (Long)` |
| `OBSERVACIONESCALIDADVISA` | `Text (Long)` |
| `OBSERVACIONESECONOMICORECHAZA` | `Text (Long)` |
| `OBSERVACIONESECONOMICOVISA` | `Text (Long)` |
| `OBSERVACIONESTECNICASRECHAZA` | `Text (Long)` |
| `OBSERVACIONESTECNICASVISA` | `Text (Long)` |
| `USUARIOCALIDADRECHAZA` | `Text` |
| `USUARIOCALIDADVISA` | `Text` |
| `USUARIOECONOMICORECHAZA` | `Text` |
| `USUARIOECONOMICOVISA` | `Text` |
| `USUARIOTECNICORECHAZA` | `Text` |
| `USUARIOTECNICOVISA` | `Text` |

#### Tabla: `TbVisadosGenerales`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ADFechaActualiza` | `Date` |
| `ADFechaEnvioSecretaria` | `Date` |
| `ADFechaEnvioSuministrador` | `Date` |
| `ADFechaRealiza` | `Date` |
| `ADFechaRechazo` | `Date` |
| `ADFechaVisado` | `Date` |
| `ADIDCorreoAlSuministrador` | `Integer` |
| `ADObservacionesRechazo` | `Text (Long)` |
| `ADObservacionesVisado` | `Text (Long)` |
| `ADRevisadoNoEnvio` | `Text` |
| `ADUsuarioRealiza` | `Text` |
| `ADUsuarioRechazo` | `Text` |
| `ADUsuarioVisado` | `Text` |
| `EstadoVisadoAD` | `Text` |
| `EstadoVisadoRO` | `Text` |
| `EstadoVisadoSO` | `Text` |
| `NDPD` | `Text` |
| `ROFechaActualiza` | `Date` |
| `ROFechaRealiza` | `Date` |
| `ROFechaRechazo` | `Date` |
| `ROFechaVisado` | `Date` |
| `ROObservacionesRechazo` | `Text (Long)` |
| `ROObservacionesVisado` | `Text (Long)` |
| `ROUsuarioRealiza` | `Text` |
| `ROUsuarioRechazo` | `Text` |
| `ROUsuarioVisado` | `Text` |
| `SOFechaActualiza` | `Date` |
| `SOFechaEnvioSecretaria` | `Date` |
| `SOFechaEnvioSuministrador` | `Date` |
| `SOFechaRealiza` | `Date` |
| `SOFechaRechazo` | `Date` |
| `SOFechaVisado` | `Date` |
| `SOIDCorreoAlSuministrador` | `Integer` |
| `SOObservacionesRechazo` | `Text (Long)` |
| `SOObservacionesVisado` | `Text (Long)` |
| `SORevisadoNoEnvio` | `Text` |
| `SOUsuarioRealiza` | `Text` |
| `SOUsuarioRechazo` | `Text` |
| `SOUsuarioVisado` | `Text` |

### Tablas Vinculadas (Accesibles)

✅ **Las siguientes tablas están vinculadas a bases de datos externas y son accesibles:**

#### Tabla: `Salidas (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Registro_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Anexo` | `Text` |
| `ArchivadoPor` | `Text` |
| `Clase` | `Text` |
| `DPD` | `Text` |
| `Destino` | `Text` |
| `Encriptado` | `Text` |
| `Expediente` | `Text` |
| `Extracto` | `Text` |
| `FDocumento` | `Date` |
| `FSalida` | `Date` |
| `IDSalida` | `Integer` |
| `NSalida` | `Text` |
| `Observaciones` | `Text (Long)` |

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

#### Tabla: `TbCPV (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CPV` | `Text` |
| `DESCRIPCION` | `Text (Long)` |
| `IDCPV` | `Integer` |

#### Tabla: `TbComerciales (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Comercial` | `Text` |
| `Descripcion` | `Text (Long)` |
| `IDComercial` | `Integer` |

#### Tabla: `TbConexionesRegistro (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Lanzadera_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ConContraseña` | `Boolean` |
| `EnOficina` | `Boolean` |
| `FechaCierre` | `Date` |
| `FechaConexion` | `Date` |
| `Horizontal` | `Integer` |
| `IDConexion` | `Integer` |
| `Usuario` | `Text` |
| `UsuarioSSID` | `Text` |
| `Vertical` | `Integer` |

#### Tabla: `TbDocExpProceso (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDO20_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ACCIONCORRECTIVA1` | `Text (Long)` |
| `ACCIONCORRECTIVA2` | `Text (Long)` |
| `ACCIONCORRECTIVA3` | `Text (Long)` |
| `ApruebaDocPrincipal` | `Text` |
| `ApruebaDocPrincipalCargo` | `Text` |
| `AreaDocAsociado1` | `Text` |
| `AreaDocAsociado2` | `Text` |
| `AreaDocAsociado3` | `Text` |
| `AreaDocPrincipal` | `Text` |
| `CARTAEnvios` | `Text (Long)` |
| `CadenaArchivosCD` | `Text (Long)` |
| `CartaATT` | `Text (Long)` |
| `CartaCP` | `Text` |
| `CartaDIRECCION` | `Text` |
| `CartaEMPLAZAMIENTO1` | `Text (Long)` |
| `CartaEMPLAZAMIENTO2` | `Text (Long)` |
| `CartaFecha` | `Date` |
| `CartaNCDS` | `SmallInt` |
| `CartaNPAPEL` | `SmallInt` |
| `CartaPARACORREO` | `Text` |
| `CartaPOBLACION` | `Text` |
| `CartaURL` | `Text (Long)` |
| `CartaUsuarioFirma` | `Text` |
| `Centro` | `Text` |
| `ClasificacionDocPrincipal` | `Text` |
| `CodDocAsociado1` | `Text` |
| `CodDocAsociado2` | `Text` |
| `CodDocAsociado3` | `Text` |
| `CodDocPrincipal` | `Text` |
| `CodExp` | `Text` |
| `ComentariosDocAsociado1` | `Text (Long)` |
| `ComentariosDocAsociado2` | `Text (Long)` |
| `ComentariosDocAsociado3` | `Text (Long)` |
| `CorreoCD` | `Text` |
| `DocAsociado1ParaTecnico` | `Text` |
| `DocAsociado2ParaTecnico` | `Text` |
| `DocAsociado3ParaTecnico` | `Text` |
| `Estado` | `Text` |
| `FACTUALIZACIONT1` | `Date` |
| `FACTUALIZACIONT2` | `Date` |
| `FACTUALIZACIONT3` | `Date` |
| `FApruebaDocPrincipal` | `Date` |
| `FECHABORRADOALMACEN` | `Date` |
| `FEnvioSecretaria` | `Date` |
| `FFINPROCESO` | `Date` |
| `FREALIZACIONT1` | `Date` |
| `FREALIZACIONT2` | `Date` |
| `FREALIZACIONT3` | `Date` |
| `FRECHAZO1` | `Date` |
| `FRECHAZO2` | `Date` |
| `FRECHAZO3` | `Date` |
| `FREVISION` | `Date` |
| `FRevisaDocPrincipal` | `Date` |
| `FVISADO1` | `Date` |
| `FVISADO2` | `Date` |
| `FVISADO3` | `Date` |
| `FechaEnvioCorreoCD` | `Date` |
| `FechaRealizacionCD` | `Date` |
| `IDDocumentoDocPrincipal` | `Integer` |
| `IDDocumentoLDocAsociado1` | `Integer` |
| `IDDocumentoLDocAsociado2` | `Integer` |
| `IDDocumentoLDocAsociado3` | `Integer` |
| `IDProceso` | `Integer` |
| `MODIFICACIONCONTADOR1` | `SmallInt` |
| `MODIFICACIONCONTADOR2` | `SmallInt` |
| `MODIFICACIONCONTADOR3` | `SmallInt` |
| `ModeloDocAsociado1` | `SmallInt` |
| `ModeloDocAsociado2` | `SmallInt` |
| `ModeloDocAsociado3` | `SmallInt` |
| `NombreProceso` | `Text` |
| `OBSRECHAZO1` | `Text (Long)` |
| `OBSRECHAZO2` | `Text (Long)` |
| `OBSRECHAZO3` | `Text (Long)` |
| `OBST1` | `Text (Long)` |
| `OBST2` | `Text (Long)` |
| `OBSVISADO1` | `Text (Long)` |
| `OBSVISADO2` | `Text (Long)` |
| `OBSVISADO3` | `Text (Long)` |
| `ObservacionesGenerales` | `Text (Long)` |
| `RECHAZOSCONTADOR1` | `SmallInt` |
| `RECHAZOSCONTADOR2` | `SmallInt` |
| `RECHAZOSCONTADOR3` | `SmallInt` |
| `RegistroSalidaDocPrincipal` | `Text` |
| `RevisaDocPrincipal` | `Text` |
| `RevisaDocPrincipalCargo` | `Text` |
| `TipoDocAsociado1` | `Text` |
| `TipoDocAsociado2` | `Text` |
| `TipoDocAsociado3` | `Text` |
| `TipoDocPrincipal` | `Text` |
| `TituloDocAsociado1` | `Text` |
| `TituloDocAsociado2` | `Text` |
| `TituloDocAsociado3` | `Text` |
| `TituloDocPrincipal` | `Text` |
| `URLCarpeta` | `Text (Long)` |
| `URLCarpetaAGEDODocAsociado1` | `Text (Long)` |
| `URLCarpetaAGEDODocAsociado2` | `Text (Long)` |
| `URLCarpetaAGEDODocAsociado3` | `Text (Long)` |
| `URLCarpetaAGEDODocPrincipal` | `Text (Long)` |
| `URLCarpetaLocal` | `Text (Long)` |
| `URLDocAsociado1` | `Text (Long)` |
| `URLDocAsociado2` | `Text (Long)` |
| `URLDocAsociado3` | `Text (Long)` |
| `URLDocPrincipal` | `Text (Long)` |
| `URLDocPrincipalFirmado` | `Text (Long)` |
| `URLDocRechazo1` | `Text (Long)` |
| `URLPlantillaDocAsociado1` | `Text (Long)` |
| `URLPlantillaDocAsociado2` | `Text (Long)` |
| `URLPlantillaDocAsociado3` | `Text (Long)` |
| `USUARIOCALIDAD1` | `Text` |
| `USUARIOCALIDAD2` | `Text` |
| `USUARIOCALIDAD3` | `Text` |
| `USUARIOMONTAJET` | `Text` |
| `USUARIOSALIDAT` | `Text` |
| `USUARIOTECNICO` | `Text` |
| `UsuarioRealizaCD` | `Text` |
| `VersionDocPrincipal` | `Text` |
| `VersionableDocPrincipal` | `Text` |

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

#### Tabla: `TbEjercitos (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `Ejercito` | `Text` |
| `IDEjercito` | `Integer` |

#### Tabla: `TbEntradas_RES (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Registro_Ent_Salida_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Asunto` | `Text` |
| `Destinatario` | `Text` |
| `Encriptado` | `Text` |
| `ExpActividad` | `Text` |
| `FDocumento` | `Date` |
| `FEntrada` | `Date` |
| `IDEntrada` | `Integer` |
| `Juridica` | `Text` |
| `NDPD` | `Text` |
| `NEntrada` | `Text` |
| `NRef` | `Text` |
| `NombreAnexo` | `Text` |
| `Notas` | `Text (Long)` |
| `Remitente` | `Text` |
| `Soporte` | `Text` |
| `UbicacionFisica` | `Text` |
| `UsuarioRegistro` | `Text` |
| `Verificado` | `Text` |
| `emailInteresado` | `Text` |

#### Tabla: `TbEstados (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DESCRIPCION` | `Text (Long)` |
| `Estado` | `Text` |
| `IDEstado` | `Integer` |

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

#### Tabla: `TbExpedientesAnexos (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDDocumento` | `Integer` |
| `IDExpediente` | `Integer` |
| `NombreDocumento` | `Text` |

#### Tabla: `TbExpedientesAnualidades1 (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Año` | `SmallInt` |
| `BIEXENTA` | `Double` |
| `BIIGIC` | `Double` |
| `BIIPSI` | `Double` |
| `BIIVA` | `Double` |
| `IDAnualidad` | `Integer` |
| `IDExpediente` | `Integer` |
| `IGIC` | `Double` |
| `IPSI` | `Double` |
| `IVA` | `Double` |
| `PeriodoFacturacion` | `Text` |

#### Tabla: `TbExpedientesCPVs (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDCPV` | `Integer` |
| `IDCPVExpediente` | `Integer` |
| `IDExpediente` | `Integer` |

#### Tabla: `TbExpedientesComerciales (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDComercial` | `Integer` |
| `IDComercialExpediente` | `Integer` |
| `IDExpediente` | `Integer` |

#### Tabla: `TbExpedientesJefaturas (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDExpediente` | `Integer` |
| `IDJefatura` | `Integer` |
| `IDJefaturaExpediente` | `Integer` |

#### Tabla: `TbExpedientesJuridicas (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `ContratistaPrincipal` | `Text` |
| `IDExpediente` | `Integer` |
| `IDExpedienteJuridica` | `Integer` |
| `IDJuridica` | `Integer` |
| `IDSuministrador` | `Integer` |
| `SubContratista` | `Text` |

#### Tabla: `TbExpedientesLugaresEjecucion (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDExpediente` | `Integer` |
| `IDExpedienteLugarEjecucion` | `Integer` |
| `IDLugarEjecucion` | `Integer` |

#### Tabla: `TbExpedientesPECAL (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDExpediente` | `Integer` |
| `IDPECAL` | `Integer` |
| `IDPECALExpediente` | `Integer` |

#### Tabla: `TbExpedientesRACS (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `IDExpediente` | `Integer` |
| `IDRAC` | `Integer` |
| `IDRacExpediente` | `Integer` |

#### Tabla: `TbExpedientesResponsables (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CorreoSiempre` | `Text` |
| `EsJefeProyecto` | `Text` |
| `IDExpedienteResponsable` | `Integer` |
| `IdExpediente` | `Integer` |
| `IdUsuario` | `Integer` |

#### Tabla: `TbGradosClasificacion (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `GradoClasificacion` | `Text` |
| `IdGradoClasificacion` | `Integer` |

#### Tabla: `TbJefaturas (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DESCRIPCION` | `Text (Long)` |
| `IDJefatura` | `Integer` |
| `Jefatura` | `Text` |

#### Tabla: `TbJuridicas (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DESCRIPCION` | `Text (Long)` |
| `IDJuridica` | `Integer` |
| `IDSuministrador` | `Integer` |
| `Juridica` | `Text` |

#### Tabla: `TbLugaresEjecucion (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `IDLugarEjecucion` | `Integer` |
| `LugarEjecucion` | `Text (Long)` |

#### Tabla: `TbOficinasPrograma (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `IDOficinaPrograma` | `Integer` |
| `OficinaPrograma` | `Text` |

#### Tabla: `TbOrganosContratacion (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Descripcion` | `Text (Long)` |
| `IDOrganoContratacion` | `Integer` |
| `OrganoContratacion` | `Text` |

#### Tabla: `TbPECAL (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DESCRIPCION` | `Text (Long)` |
| `IDPECAL` | `Integer` |
| `PECAL` | `Text` |

#### Tabla: `TbRACS (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Expedientes_datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `CORREO` | `Text` |
| `DESCRIPCION` | `Text (Long)` |
| `IDRAC` | `Integer` |
| `RAC` | `Text` |

#### Tabla: `TbSalidas_RES (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\Registro_Ent_Salida_Datos.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `Asunto` | `Text` |
| `CodAGEDO` | `Text` |
| `Destinatario` | `Text` |
| `Encriptado` | `Text` |
| `ExpActividad` | `Text` |
| `FDocumento` | `Date` |
| `FSalida` | `Date` |
| `IDSalida` | `Integer` |
| `Juridica` | `Text` |
| `MedioEnvio` | `Text` |
| `NDPD` | `Text` |
| `NRef` | `Text` |
| `NSalida` | `Text` |
| `NombreAnexo` | `Text` |
| `Notas` | `Text (Long)` |
| `Remitente` | `Text` |
| `Soporte` | `Text` |
| `UbicacionFisica` | `Text` |
| `UsuarioRegistro` | `Text` |
| `Verificado` | `Text` |
| `emailRemitente` | `Text` |

#### Tabla: `TbSolicitudesOfertasPrevias1 (VINCULADA ACCESIBLE - c:\Proyectos\scripts-python\dbs-locales\AGEDYS_DATOS.accdb)`
| Nombre de Columna | Tipo de Dato |
|-------------------|--------------|
| `DPD` | `Text` |
| `FechaModificacion` | `Date` |
| `FechaRegistro` | `Date` |
| `IDCorreo` | `Integer` |
| `IDSO` | `Integer` |
| `IDSalida` | `Integer` |
| `NAcreedor` | `Integer` |
| `NombreArchivo` | `Text` |
| `NombreTabla` | `Text` |
| `UsuarioRegistra` | `Text` |
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

### Tablas Vinculadas (No Accesibles)

⚠️ **Las siguientes tablas están vinculadas a bases de datos externas que no están disponibles:**

#### Tabla: `TbCorreosEnviados (VINCULADA NO ACCESIBLE - C:\Users\adm1\Desktop\Proyectos\scripts-python\dbs-locales\correos_datos.accdb)`
| Información | Detalle |
|-------------|----------|
| Tipo | Tabla Vinculada |
| Ruta Esperada | `C:\Users\adm1\Desktop\Proyectos\scripts-python\dbs-locales\correos_datos.accdb` |
| Estado | NO ACCESIBLE |

## Relaciones entre Tablas

Las siguientes relaciones fueron encontradas en el esquema de la base de datos:

- La tabla `TbSuministradoresPuntuacionConDetalle.IDVisado` se relaciona con `TbVisadoFacturas_Nueva.IDVisado`.
- La tabla `TbVisadoFacturas_Nueva.IDFactura` se relaciona con `TbFacturasDetalle.IDFactura`.
