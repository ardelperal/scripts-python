
Option Explicit



Dim m_Destinatarios
Dim m_IDAplicacion
Dim m_Asunto
Dim m_Cuerpo


Dim m_DestinatariosEnCopia
Dim m_DestinatariosEnCopiaOculta
Dim m_URLBBDDRegistrosTareas

Dim m_URLBBDDRiesgos
Dim CnTareas
Dim CnRiesgos
Const m_Pass = "dpddpd"
Dim m_URLCSS
Dim CSS

Dim ColUsuariosAdministradores
Dim m_CadenaCorreoAdministradores

Dim ColUsuariosCalidad
Dim ColUsuariosCalidadParaExcluir
Dim m_CadenaCorreoCalidad


Const adStateClosed = 0
Const adStateOpen = 1
Const adOpenForwardOnly = 0
Const adOpenKeyset = 1
Const adOpenStatic = 3

Const adLockBatchOptimistic = 4
Const adLockOptimistic = 3
Const adLockPessimistic = 2
Const adLockReadOnly = 1

Const ForReading = 1
Const ForWriting = 2
Const ForAppending = 8

Const adOpenDynamic = 2
Const adUseClient = 3

Const adCmdText = 1

Public Function UltimaEjecucion(p_TipoTarea)
    Dim m_SQL
    'RiesgosSemanalesCalidad
    'RiesgosDiariosTecnicos
    'RiesgosMensualesCalidad
    Dim rcdDatos
    m_SQL = "SELECT Last(TbTareas.Fecha) AS Ultima " & _
            "FROM TbTareas " & _
            "WHERE Tarea='" & p_TipoTarea & "' AND Realizado='Sí';"
    
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
       
        If Not .EOF Then
           UltimaEjecucion = .Fields("Ultima")
        End If
        
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Public Function TareaTecnicaParaEjecutar()
    
    Dim m_UltimaEjecucion
   
    Dim m_Dias
    m_UltimaEjecucion = UltimaEjecucion("RiesgosDiariosTecnicos")
    If Not IsDate(m_UltimaEjecucion) Then
        TareaTecnicaParaEjecutar = True
    Else
        m_Dias = DateDiff("d", CDate(Date), m_UltimaEjecucion)
        If m_Dias < 0 Then
            m_Dias = m_Dias * -1
        End If
        If m_Dias >= 7 Then
            TareaTecnicaParaEjecutar = True
        Else
            TareaTecnicaParaEjecutar = False
        End If
    End If
End Function
Public Function TareaCalidadParaEjecutar1()
    
    Dim m_UltimaEjecucionCalidad
   
    m_UltimaEjecucionCalidad = UltimaEjecucion("RiesgosSemanalesCalidad")
    If Not IsDate(m_UltimaEjecucionCalidad) Then
        TareaCalidadParaEjecutar1 = True
    Else
        If CDate(m_UltimaEjecucionCalidad) = CDate(Date) Then
            TareaCalidadParaEjecutar1 = False
        Else
            TareaCalidadParaEjecutar1 = True
        End If
    End If
    
End Function

Public Function TareaCalidadParaEjecutar()
    
    Dim m_UltimaEjecucion
   
    Dim m_Dias
    m_UltimaEjecucion = UltimaEjecucion("RiesgosSemanalesCalidad")
    If Not IsDate(m_UltimaEjecucion) Then
        TareaCalidadParaEjecutar = True
    Else
        m_Dias = DateDiff("d", CDate(Date), m_UltimaEjecucion)
        If m_Dias < 0 Then
            m_Dias = m_Dias * -1
        End If
        If m_Dias >= 7 Then
            TareaCalidadParaEjecutar = True
        Else
            TareaCalidadParaEjecutar = False
        End If
    End If
    
End Function
Public Function TareaMensualParaEjecutar()
    
    Dim m_UltimaEjecucion
    Dim m_Dias
    m_UltimaEjecucion = UltimaEjecucion("RiesgosMensualesCalidad")
    If Not IsDate(m_UltimaEjecucion) Then
        TareaMensualParaEjecutar = True
    Else
        m_Dias = DateDiff("d", CDate(Date), m_UltimaEjecucion)
        If m_Dias < 0 Then
            m_Dias = m_Dias * -1
        End If
        If m_Dias >= 30 Then
            TareaMensualParaEjecutar = True
        Else
            TareaMensualParaEjecutar = False
        End If
    End If
    
End Function




Public Function EVE()
    
    'm_ParaPruebas = True
   
End Function

Public Function getCSS()
    Dim MiCSS
    Dim FSO
    Dim URLCSS
    
    URLCSS = "\\DATOSTE\aplicaciones_dys\Aplicaciones PpD\CSS.txt"
    Set FSO = CreateObject("Scripting.FileSystemObject")
    Set MiCSS = FSO.OpenTextFile(URLCSS, 1, False)
    getCSS = Trim(MiCSS.ReadAll)
    MiCSS.Close
    Set FSO = Nothing
   
    
    
End Function

Public Function getColusuariosTareas(p_Tipo)

    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Registro
    Dim col
    
    Set col = CreateObject("Scripting.Dictionary")
    Set getColusuariosTareas = CreateObject("Scripting.Dictionary")
    If p_Tipo = "Técnico" Then
        m_SQL = "SELECT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
                "FROM TbUsuariosAplicaciones LEFT JOIN TbUsuariosAplicacionesTareas ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesTareas.CorreoUsuario " & _
                "WHERE (((TbUsuariosAplicaciones.ParaTareasProgramadas)=True) AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) AND ((TbUsuariosAplicacionesTareas.CorreoUsuario) Is Null));"
    ElseIf p_Tipo = "Calidad" Then
        m_SQL = "SELECT UsuarioRed, Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
                "FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesPermisos " & _
                "ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario " & _
                "WHERE " & _
                "ParaTareasProgramadas=True " & _
                "AND FechaBaja Is Null " & _
                "AND ParaTareasProgramadas=True " & _
                "AND IDAplicacion=" & m_IDAplicacion & " " & _
                "AND EsUsuarioCalidad='Sí';"
    ElseIf p_Tipo = "Economía" Then
        m_SQL = "SELECT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
                "FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesTareas ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesTareas.CorreoUsuario " & _
                "WHERE (((TbUsuariosAplicaciones.ParaTareasProgramadas)=True) AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) AND ((TbUsuariosAplicacionesTareas.EsEconomia)='Sí'));"
    ElseIf p_Tipo = "Administrador" Then
        m_SQL = "SELECT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
                "FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesTareas ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesTareas.CorreoUsuario " & _
                "WHERE (((TbUsuariosAplicaciones.ParaTareasProgramadas)=True) AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) AND ((TbUsuariosAplicacionesTareas.EsAdministrador)='Sí'));"
    Else
        Exit Function
    End If
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    If Not rcdDatos.EOF Then
        
        Do While Not rcdDatos.EOF
            m_Registro = rcdDatos.Fields("UsuarioRed") & "|" & rcdDatos.Fields("Nombre") & "|" & rcdDatos.Fields("CorreoUsuario")
            
            If Not getColusuariosTareas.Exists(m_Registro) Then
                getColusuariosTareas.Add m_Registro, m_Registro
            End If
            
            rcdDatos.MoveNext
        Loop
        
    End If
    
    rcdDatos.Close
    Set rcdDatos = Nothing
    
End Function
Private Function Conn( _
                        p_URL, _
                        p_Pass _
                        )
    
    Dim m_ConnectionString
    Dim m_Provider
    
    
    m_Provider = "Microsoft.ACE.OLEDB.12.0"
    m_ConnectionString = "Data Source=" & p_URL & ";" & "Jet OLEDB:Database Password=" & p_Pass & ";"
    Set Conn = CreateObject("adodb.Connection")
    
    With Conn
        .Provider = m_Provider
        .ConnectionString = m_ConnectionString
        .Open
    End With
    
    
End Function

Private Function getIDCorreo()
    Dim m_SQL
    Dim rcdDatos
    Dim lngOrdinalMaximo
    
    
    m_SQL = "SELECT Max(TbCorreosEnviados.IDCorreo) AS Maximo " & _
            "FROM TbCorreosEnviados;"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        
        If Not .EOF Then
            If IsNumeric(.Fields("Maximo")) Then
                lngOrdinalMaximo = .Fields("Maximo")
            End If
        End If
        
    End With
    
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    getIDCorreo = lngOrdinalMaximo + 1
End Function

Public Function RegistrarCorreo(p_Asunto, p_Cuerpo, p_Destinatarios)

    Dim rcdDatos
    Dim m_SQL
    Dim m_IDCorreo
    
'    p_Destinatarios = "andres.romandelperal@telefonica.com"
'    m_CadenaCorreoAdministradores = ""
    m_IDCorreo = getIDCorreo()
    If Not IsNumeric(m_IDCorreo) Then
        Exit Function
    End If
    m_SQL = "SELECT TbCorreosEnviados.* " & _
            "FROM TbCorreosEnviados;"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
       .AddNew
            .Fields("IDCorreo") = m_IDCorreo
            .Fields("Aplicacion") = "RIESGOS"
            .Fields("Asunto") = p_Asunto
            .Fields("Cuerpo") = p_Cuerpo
            If InStr(1, p_Destinatarios, "@") <> 0 Then
                .Fields("Destinatarios") = p_Destinatarios
            End If
            .Fields("DestinatariosConCopiaOculta") = m_CadenaCorreoAdministradores
            .Fields("FechaGrabacion") = Now()
        .Update
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
End Function

Public Function getFechaParaConsulta(p_Fecha)
    If Not IsDate(p_Fecha) Then
        getFechaParaConsulta = p_Fecha
        Exit Function
    End If
    getFechaParaConsulta = Right("00" & Month(p_Fecha), 2) & "/" & _
                            Right("00" & Day(p_Fecha), 2) & "/" & _
                            Right("0000" & Year(p_Fecha), 4)
End Function
Public Function RegistrarTarea(p_TipoTarea)
    'RiesgosSemanalesCalidad
    'RiesgosDiariosTecnicos
    'RiesgosMensualesCalidad
    Dim rcdDatos
    Dim m_SQL
    
    m_SQL = "SELECT * " & _
            "FROM TbTareas " & _
            "WHERE Tarea='" & p_TipoTarea & "';"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        
        If .EOF Then
            .AddNew
                .Fields("Tarea") = p_TipoTarea
                .Fields("Fecha") = Date
                .Fields("Realizado") = "Sí"
            .Update
        Else
                .Fields("Fecha") = Date
                .Fields("Realizado") = "Sí"
            .Update
        End If
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
End Function


Public Function getCadenaCorreoAdministradores()
    Dim m_Registro
    Dim dato
    Dim m_Correo
    Dim m_Cadena
    If ColUsuariosAdministradores.Count < 1 Then
        Exit Function
    End If
    'm_Registro = rcdDatos.Fields("UsuarioRed") & "|" & rcdDatos.Fields("Nombre") & "|" & rcdDatos.Fields("CorreoUsuario")
    m_Cadena = ""
    For Each m_Registro In ColUsuariosAdministradores
        dato = Split(m_Registro, "|")
        m_Correo = dato(2)
        If m_Cadena = "" Then
            m_Cadena = m_Correo
        Else
            m_Cadena = m_Cadena & ";" & m_Correo
        End If
    Next
    getCadenaCorreoAdministradores = m_Cadena
    
    
End Function

Public Function getCadenaCorreoCalidad()
    Dim m_Registro
    Dim dato
    Dim m_Correo
    Dim m_Cadena
    If ColUsuariosCalidad.Count < 1 Then
        Exit Function
    End If
    'm_Registro = rcdDatos.Fields("UsuarioRed") & "|" & rcdDatos.Fields("Nombre") & "|" & rcdDatos.Fields("CorreoUsuario")
    m_Cadena = ""
    For Each m_Registro In ColUsuariosCalidad
        dato = Split(m_Registro, "|")
        m_Correo = dato(2)
        If m_Cadena = "" Then
            m_Cadena = m_Correo
        Else
            m_Cadena = m_Cadena & ";" & m_Correo
        End If
    Next
    getCadenaCorreoCalidad = m_Cadena
    
    
End Function

Public Function Lanzar()
    
    Dim m_TareaTecnicaParaEjecutar
    Dim m_TareaCalidadDiariaParaEjecutar
    Dim m_TareaCalidadMensualParaEjecutar
    
    m_URLBBDDRiesgos = "\\Datoste\aplicaciones_dys\Aplicaciones PpD\GESTION RIESGOS\Gestion_Riesgos_Datos.accdb"
    m_URLBBDDRegistrosTareas = "\\Datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb"
    m_IDAplicacion = 5
    Set CnTareas = Conn(m_URLBBDDRegistrosTareas, m_Pass)
    m_TareaCalidadDiariaParaEjecutar = TareaCalidadParaEjecutar()
    m_TareaTecnicaParaEjecutar = TareaTecnicaParaEjecutar()
    m_TareaCalidadMensualParaEjecutar = TareaMensualParaEjecutar()
    
    If m_TareaCalidadDiariaParaEjecutar = False And m_TareaTecnicaParaEjecutar = False And m_TareaCalidadMensualParaEjecutar = False Then
        CnTareas.Close
        Set CnTareas = Nothing
        Exit Function
    End If
    
    Set CnRiesgos = Conn(m_URLBBDDRiesgos, m_Pass)
    CSS = getCSS
    
    Set ColUsuariosAdministradores = getColusuariosTareas("Administrador")
    m_CadenaCorreoAdministradores = getCadenaCorreoAdministradores()
   
    Set ColUsuariosCalidad = getColusuariosTareas("Calidad")
    m_CadenaCorreoCalidad = getCadenaCorreoCalidad()
    
   
    If m_TareaCalidadDiariaParaEjecutar = True Then
        RealizarTareaDiariaCalidad
    End If
    
    If m_TareaTecnicaParaEjecutar = True Then
        RealizarTareaTecnicos
    End If
    
    If m_TareaCalidadMensualParaEjecutar = True Then
        RealizarTareaCalidadMensual
    End If
    CnTareas.Close
    Set CnTareas = Nothing
    CnRiesgos.Close
    Set CnRiesgos = Nothing
    
End Function

Public Function RealizarTareaTecnicos()

    Dim m_Col
    Dim m_UsurioRed
    Dim m_NombreTecnico
    Dim m_Resto
    Dim m_Correo
    Dim dato
    Dim m_mensaje
    Dim m_HTMLCabecera
    Dim m_Titulo
    
    Dim m_HTMLEDICIONESNECESITANPROPUESTAPUBLICACION
    Dim m_HTMLEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS
    Dim m_HTMLRIESGOSACEPTADOSSINMOTIVAR
    Dim m_HTMLRIESGOSACEPTADOSRECHAZADOS
    Dim m_HTMLRIESGOSRETIRADOSSINMOTIVAR
    Dim m_HTMLRIESGOSRETIRADOSRECHAZADOS
    Dim m_HTMLRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR
    Dim m_HTMLRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR
    
    Dim m_intNEDICIONESNECESITANPROPUESTAPUBLICACION
    Dim m_intNEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS
    Dim m_intNRIESGOSACEPTADOSSINMOTIVAR
    Dim m_intNRIESGOSACEPTADOSRECHAZADOS
    Dim m_intNRIESGOSRETIRADOSSINMOTIVAR
    Dim m_intNRIESGOSRETIRADOSRECHAZADOS
    Dim m_intNRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR
    Dim m_intNRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR
    
    
    Set m_Col = getColUsuariosDistintos()
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_HTMLCabecera = DameCabeceraHTML("Tareas Diarias Calidad")
    For Each m_UsurioRed In m_Col
        m_Resto = m_Col(m_UsurioRed)
        dato = Split(m_Resto, "|")
        m_Correo = dato(1)
        m_NombreTecnico = dato(0)
        
        m_Titulo = "INFORME TAREAS SEMANALES PARA <b>" & m_NombreTecnico & "</b>"
        m_HTMLEDICIONESNECESITANPROPUESTAPUBLICACION = _
            getTECNICOHTMLEDICIONESNECESITANPROPUESTAPUBLICACION(m_UsurioRed, _
                                                                m_intNEDICIONESNECESITANPROPUESTAPUBLICACION)
        
        m_HTMLEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS = _
            getTECNICOHTMLEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS(m_UsurioRed, _
                                                                        m_intNEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS)
    
        m_HTMLRIESGOSACEPTADOSSINMOTIVAR = _
            getTECNICODHTMLRIESGOSACEPTADOSSINMOTIVAR(m_UsurioRed, _
                                                                m_intNRIESGOSACEPTADOSSINMOTIVAR)
        m_HTMLRIESGOSACEPTADOSRECHAZADOS = _
            getTECNICOHTMLRIESGOSACEPTADOSRECHAZADOS(m_UsurioRed, _
                                                                m_intNRIESGOSACEPTADOSRECHAZADOS)
                                                                
        m_HTMLRIESGOSRETIRADOSSINMOTIVAR = _
            getTECNICOHTMLRIESGOSRETIRADOSSINMOTIVAR(m_UsurioRed, _
                                                                m_intNRIESGOSRETIRADOSSINMOTIVAR)
                                    
        m_HTMLRIESGOSRETIRADOSRECHAZADOS = _
            getTECNICOHTMLRIESGOSRETIRADOSRECHAZADOS(m_UsurioRed, _
                                                                m_intNRIESGOSRETIRADOSRECHAZADOS)
                                                                
        m_HTMLRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR = _
            getTECNICOHTMLRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR(m_UsurioRed, _
                                                                m_intNRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR)
        
        m_HTMLRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR = _
            getTECNICOHTMLRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR(m_UsurioRed, _
                                                                m_intNRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR)
                                                                
        
        
        m_mensaje = m_HTMLCabecera & vbNewLine
        m_mensaje = m_mensaje & m_Titulo & vbNewLine
    
        If m_intNEDICIONESNECESITANPROPUESTAPUBLICACION > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLEDICIONESNECESITANPROPUESTAPUBLICACION & vbNewLine
        End If
        If m_intNEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS & vbNewLine
        End If
        If m_intNRIESGOSACEPTADOSSINMOTIVAR > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLRIESGOSACEPTADOSSINMOTIVAR & vbNewLine
        End If
        If m_intNRIESGOSACEPTADOSRECHAZADOS > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLRIESGOSACEPTADOSRECHAZADOS & vbNewLine
        End If
        If m_intNRIESGOSRETIRADOSSINMOTIVAR > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLRIESGOSRETIRADOSSINMOTIVAR & vbNewLine
        End If
        If m_intNRIESGOSRETIRADOSRECHAZADOS > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLRIESGOSRETIRADOSRECHAZADOS & vbNewLine
        End If
        If m_intNRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR & vbNewLine
        End If
        If m_intNRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR > 0 Then
            m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
            m_mensaje = m_mensaje & m_HTMLRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR & vbNewLine
        End If
        RegistrarCorreo "Informe Tareas Para Técnicos (Gestión de Riesgos)", m_mensaje, m_Correo
        
       
                                
    Next
    RegistrarTarea "RiesgosDiariosTecnicos"
End Function

Public Function RealizarTareaCalidadMensual()

    Dim m_mensaje
    Dim m_HTMLCabecera
    Dim m_Titulo
    
    Dim m_HTMLEDICIONESPREPARADASPARAPUBLICAR
    Dim m_HTMLEDICIONESACTIVAS
    Dim m_HTMLEDICIONESCERRADASELULTIMOMES
    
    
    Dim m_intNEDICIONESPREPARADASPARAPUBLICAR
    Dim m_intNEDICIONESACTIVAS
    Dim m_intNEDICIONESCERRADASELULTIMOMES
    
    
    m_HTMLCabecera = DameCabeceraHTML("Informe Mensual Calidad")
    m_Titulo = "INFORME MENSUAL PARA CALIDAD"
    m_HTMLEDICIONESPREPARADASPARAPUBLICAR = getCALIDADHTMLEDICIONESPREPARADASPARAPUBLICAR("", _
                                            m_intNEDICIONESPREPARADASPARAPUBLICAR)
    
    m_HTMLEDICIONESACTIVAS = getHTMLEDICIONESACTIVAS(m_intNEDICIONESACTIVAS)
    m_HTMLEDICIONESCERRADASELULTIMOMES = getHTMLEDICIONESCERRADASELULTIMOMES(m_intNEDICIONESCERRADASELULTIMOMES)
        
    m_mensaje = m_HTMLCabecera & vbNewLine
    m_mensaje = m_mensaje & m_Titulo & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    m_mensaje = m_mensaje & m_HTMLEDICIONESPREPARADASPARAPUBLICAR & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    m_mensaje = m_mensaje & m_HTMLEDICIONESACTIVAS & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    m_mensaje = m_mensaje & m_HTMLEDICIONESCERRADASELULTIMOMES & vbNewLine
   
    RegistrarCorreo "Informe Mensual Calidad (Gestión de Riesgos)", m_mensaje, m_CadenaCorreoCalidad
        
    RegistrarTarea "RiesgosMensualesCalidad"
End Function

Public Function getHTMLTablasMiembroCalidad(p_NombreCalidad)
    
    
    Dim m_CALIDADHTMLEDICIONESPREPARADASPARAPUBLICAR
    Dim m_intCALIDADNEDICIONESPREPARADASPARAPUBLICAR
    Dim m_CALIDADHTMLEDICIONESAPUNTODECADUCAR
    Dim m_intCALIDADNEDICIONESAPUNTODECADUCAR
    Dim m_CALIDADHTMLEDICIONESCADUCADAS
    Dim m_intCALIDADNEDICIONESCADUCADAS
    
    
    Dim m_CALIDADHTMLRIESGOSPARARETIPIFICAR
    Dim m_intCALIDADNRIESGOSPARARETIPIFICAR
    Dim m_CALIDADHTMLRIESGOSACEPTADOSPORVISAR
    Dim m_intCALIDADNRIESGOSACEPTADOSPORVISAR
    Dim m_CALIDADHTMLRIESGOSRETIRADOSPORVISAR
    Dim m_intCALIDADNRIESGOSRETIRADOSPORVISAR
    Dim m_CALIDADHTMLRIESGOSMATERIALIZADOSPORDECIDIR
    Dim m_intCALIDADNRIESGOSMATERIALIZADOSPORDECIDIR
    Dim m_mensaje
    Dim m_TituloCalidad
    
    
    m_CALIDADHTMLEDICIONESPREPARADASPARAPUBLICAR = _
        getCALIDADHTMLEDICIONESPREPARADASPARAPUBLICAR(p_NombreCalidad, m_intCALIDADNEDICIONESPREPARADASPARAPUBLICAR)
        
   m_CALIDADHTMLEDICIONESAPUNTODECADUCAR = _
        getCALIDADHTMLEDICIONESAPUNTODECADUCAR(p_NombreCalidad, m_intCALIDADNEDICIONESAPUNTODECADUCAR)
        
    m_CALIDADHTMLEDICIONESCADUCADAS = _
        getCALIDADHTMLEDICIONESCADUCADAS(p_NombreCalidad, m_intCALIDADNEDICIONESCADUCADAS)

    m_CALIDADHTMLRIESGOSPARARETIPIFICAR = _
            getCALIDADHTMLRIESGOSPARARETIPIFICAR(p_NombreCalidad, m_intCALIDADNRIESGOSPARARETIPIFICAR)
    
    m_CALIDADHTMLRIESGOSACEPTADOSPORVISAR = _
            getCALIDADHTMLRIESGOSACEPTADOSPORVISAR(p_NombreCalidad, m_intCALIDADNRIESGOSACEPTADOSPORVISAR)
    
    m_CALIDADHTMLRIESGOSRETIRADOSPORVISAR = _
            getCALIDADHTMLRIESGOSRETIRADOSPORVISAR(p_NombreCalidad, m_intCALIDADNRIESGOSRETIRADOSPORVISAR)
    
    m_CALIDADHTMLRIESGOSMATERIALIZADOSPORDECIDIR = _
            getCALIDADHTMLRIESGOSMATERIALIZADOSPORDECIDIR(p_NombreCalidad, m_intCALIDADNRIESGOSMATERIALIZADOSPORDECIDIR)
    
    m_TituloCalidad = "INFORME TAREAS SEMANAL CALIDAD PARA <b>" & p_NombreCalidad & "</b>"
    m_mensaje = m_TituloCalidad & vbNewLine
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    If m_intCALIDADNEDICIONESPREPARADASPARAPUBLICAR > 0 Then
        m_mensaje = m_mensaje & m_CALIDADHTMLEDICIONESPREPARADASPARAPUBLICAR & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    If m_intCALIDADNEDICIONESAPUNTODECADUCAR > 0 Then
        m_mensaje = m_mensaje & m_CALIDADHTMLEDICIONESAPUNTODECADUCAR & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    If m_intCALIDADNEDICIONESCADUCADAS > 0 Then
        m_mensaje = m_mensaje & m_CALIDADHTMLEDICIONESCADUCADAS & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    If m_intCALIDADNRIESGOSPARARETIPIFICAR > 0 Then
        m_mensaje = m_mensaje & m_CALIDADHTMLRIESGOSPARARETIPIFICAR & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    If m_intCALIDADNRIESGOSACEPTADOSPORVISAR > 0 Then
        m_mensaje = m_mensaje & m_CALIDADHTMLRIESGOSACEPTADOSPORVISAR & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    If m_intCALIDADNRIESGOSRETIRADOSPORVISAR > 0 Then
        m_mensaje = m_mensaje & m_CALIDADHTMLRIESGOSRETIRADOSPORVISAR & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    If m_intCALIDADNRIESGOSMATERIALIZADOSPORDECIDIR > 0 Then
        m_mensaje = m_mensaje & m_CALIDADHTMLRIESGOSMATERIALIZADOSPORDECIDIR & vbNewLine
        m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    End If
    getHTMLTablasMiembroCalidad = m_mensaje
End Function

Public Function RealizarTareaDiariaCalidad()
    Dim m_CorreoCalidad1
    Dim m_CorreoCalidad2
    Dim m_CorreoCalidad3
    Dim m_CorreoCalidad4
    Dim m_CorreoCalidad5
    
    Dim m_NombreCalidad1
    Dim m_NombreCalidad2
    Dim m_NombreCalidad3
    Dim m_NombreCalidad4
    Dim m_NombreCalidad5
   
    
    Dim m_HTMTCalidad1
    Dim m_HTMTCalidad2
    Dim m_HTMTCalidad3
    Dim m_HTMTCalidad4
    Dim m_HTMTCalidad5
    
    
    
    Dim m_mensaje
    Dim m_HTMLCabecera
    
    
    
    m_CorreoCalidad1 = "sergio.garciamontalvo@telefonica.com"
    m_CorreoCalidad2 = "beatriz.novalgutierrez@telefonica.com"
    m_CorreoCalidad3 = "anamaria.rubiocanales@telefonica.com"
    m_CorreoCalidad4 = "natalia.casangarcia@telefonica.com"
    m_CorreoCalidad5 = "mario.martinabad@telefonica.com"
    
    
    
    m_NombreCalidad1 = "SERGIO GARCÍA MONTALVO"
    m_NombreCalidad2 = "BEATRIZ NOVAL GUTIÉRREZ"
    m_NombreCalidad3 = "ANA RUBIO CANALES"
    m_NombreCalidad4 = "NATALIA CASÁN GARCÍA"
    m_NombreCalidad5 = "MARIO MARTÍN ABAD"
    
    m_HTMTCalidad1 = getHTMLTablasMiembroCalidad(m_NombreCalidad1)
    m_HTMTCalidad2 = getHTMLTablasMiembroCalidad(m_NombreCalidad2)
    m_HTMTCalidad3 = getHTMLTablasMiembroCalidad(m_NombreCalidad3)
    m_HTMTCalidad4 = getHTMLTablasMiembroCalidad(m_NombreCalidad4)
    m_HTMTCalidad5 = getHTMLTablasMiembroCalidad(m_NombreCalidad5)
    
    
    m_HTMLCabecera = DameCabeceraHTML("Tareas Diarias Calidad")
    
    
   'PARA m_NombreCalidad1
    
    
    m_mensaje = m_HTMLCabecera & vbNewLine
    
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad1 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad2 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad3 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad4 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad5 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "</body>" & vbNewLine
    m_mensaje = m_mensaje & "</html>" & vbNewLine
    
    RegistrarCorreo "Informe Tareas Calidad (Gestión de Riesgos)", m_mensaje, m_CorreoCalidad1
    
    'PARA m_NombreCalidad2
    
    m_mensaje = m_HTMLCabecera & vbNewLine
    
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad2 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad1 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad3 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad4 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad5 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "</body>" & vbNewLine
    m_mensaje = m_mensaje & "</html>" & vbNewLine
    
    RegistrarCorreo "Informe Tareas Calidad (Gestión de Riesgos)", m_mensaje, m_CorreoCalidad2
    
    
    'PARA m_NombreCalidad3
    
    m_mensaje = m_HTMLCabecera & vbNewLine
    
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad3 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad1 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad2 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
   
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad4 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad5 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "</body>" & vbNewLine
    m_mensaje = m_mensaje & "</html>" & vbNewLine
    
    RegistrarCorreo "Informe Tareas Calidad (Gestión de Riesgos)", m_mensaje, m_CorreoCalidad3
    
    'PARA m_NombreCalidad4
    
    m_mensaje = m_HTMLCabecera & vbNewLine
    
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad4 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad1 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad2 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
   
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad3 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad5 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    
    m_mensaje = m_mensaje & "</body>" & vbNewLine
    m_mensaje = m_mensaje & "</html>" & vbNewLine
    
    RegistrarCorreo "Informe Tareas Calidad (Gestión de Riesgos)", m_mensaje, m_CorreoCalidad4
    
    'PARA m_NombreCalidad5
    
    m_mensaje = m_HTMLCabecera & vbNewLine
    
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad5 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad1 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad2 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad3 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "<div>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMTCalidad4 & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & "<hr size='2px' color='black' />" & vbNewLine
    m_mensaje = m_mensaje & "</div>" & vbNewLine
    
    m_mensaje = m_mensaje & "</body>" & vbNewLine
    m_mensaje = m_mensaje & "</html>" & vbNewLine
    
    RegistrarCorreo "Informe Tareas Calidad (Gestión de Riesgos)", m_mensaje, m_CorreoCalidad5

    
    RegistrarTarea "RiesgosSemanalesCalidad"
End Function




Public Function getCALIDADHTMLEDICIONESAPUNTODECADUCAR(p_UsuarioCalidad, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    Dim m_IDEdicion
    Dim m_Resto
    Dim dato
    Dim m_Proyecto
    Dim m_Nombre
    Dim m_Juridica
    Dim m_Edicion
    Dim m_FechaEdicion
    Dim m_FechaMaxProximaPublicacion
    Dim m_Dias
    
    Dim m_FechaPrevistaCierre
    Dim m_RespCalidad
    
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,TbProyectos.FechaPrevistaCierre, " & _
            "TbProyectosEdiciones.IDEdicion,TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion, " & _
            "TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad," & _
            "DateDiff('d',now(),[TbProyectosEdiciones].[FechaMaxProximaPublicacion]) AS Días " & _
            "FROM TbProyectos INNER JOIN TbProyectosEdiciones " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbProyectos.NombreUsuarioCalidad)='" & p_UsuarioCalidad & "') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((DateDiff('d',now(),[TbProyectosEdiciones].[FechaMaxProximaPublicacion]))<=15) " & _
            "AND ((DateDiff('d',now(),[TbProyectosEdiciones].[FechaMaxProximaPublicacion]))>-1));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
    Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDEdicion").Value) Then
            m_Col.Add rcdDatos.Fields("IDEdicion").Value, _
                    rcdDatos.Fields("Proyecto").Value & "||" & _
                    rcdDatos.Fields("NombreProyecto").Value & "||" & _
                    rcdDatos.Fields("Juridica").Value & "||" & _
                    rcdDatos.Fields("Edicion").Value & "||" & _
                    rcdDatos.Fields("FechaEdicion").Value & "||" & _
                    rcdDatos.Fields("FechaPrevistaCierre").Value & "||" & _
                    rcdDatos.Fields("FechaMaxProximaPublicacion").Value & "||" & _
                    rcdDatos.Fields("Días").Value & "||" & _
                    rcdDatos.Fields("NombreUsuarioCalidad").Value
        End If
        
        
        

        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='9' class=""ColespanArriba""> EDICIONES CON FECHA DE PUBLICACIÓN A PUNTO DE SER SUPERADA</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Nombre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Jurídica</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Últ Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Últ Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Prevista Cierre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Máx.Próx Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Faltan (Días)</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_IDEdicion In m_Col
                m_Resto = m_Col(m_IDEdicion)
                dato = Split(m_Resto, "||")
                m_Proyecto = dato(0)
                m_Nombre = dato(1)
                m_Juridica = dato(2)
                m_Edicion = dato(3)
                m_FechaEdicion = dato(4)
                m_FechaPrevistaCierre = dato(5)
                m_FechaMaxProximaPublicacion = dato(6)
                m_Dias = dato(7)
                m_RespCalidad = dato(8)
                 
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Proyecto & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nombre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Juridica & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Edicion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaEdicion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaPrevistaCierre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaMaxProximaPublicacion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Dias & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getCALIDADHTMLEDICIONESAPUNTODECADUCAR = m_mensaje
    
End Function
Public Function getCALIDADHTMLEDICIONESCADUCADAS(p_UsuarioCalidad, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    Dim m_IDEdicion
    Dim m_Resto
    Dim dato
    Dim m_Proyecto
    Dim m_Nombre
    Dim m_Juridica
    Dim m_Edicion
    Dim m_FechaEdicion
    Dim m_FechaMaxProximaPublicacion
    Dim m_Dias
    
    Dim m_FechaPrevistaCierre
    Dim m_RespCalidad
    
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,TbProyectos.FechaPrevistaCierre, " & _
            "TbProyectosEdiciones.IDEdicion,TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion, " & _
            "TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad," & _
            "DateDiff('d',now(),[TbProyectosEdiciones].[FechaMaxProximaPublicacion]) AS Días " & _
            "FROM TbProyectos INNER JOIN TbProyectosEdiciones " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbProyectos.NombreUsuarioCalidad)='" & p_UsuarioCalidad & "') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((DateDiff('d',now(),[TbProyectosEdiciones].[FechaMaxProximaPublicacion]))<0));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
    Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDEdicion").Value) Then
            m_Col.Add rcdDatos.Fields("IDEdicion").Value, _
                    rcdDatos.Fields("Proyecto").Value & "||" & _
                    rcdDatos.Fields("NombreProyecto").Value & "||" & _
                    rcdDatos.Fields("Juridica").Value & "||" & _
                    rcdDatos.Fields("Edicion").Value & "||" & _
                    rcdDatos.Fields("FechaEdicion").Value & "||" & _
                    rcdDatos.Fields("FechaPrevistaCierre").Value & "||" & _
                    rcdDatos.Fields("FechaMaxProximaPublicacion").Value & "||" & _
                    rcdDatos.Fields("Días").Value & "||" & _
                    rcdDatos.Fields("NombreUsuarioCalidad").Value
        End If
        
        
        

        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='9' class=""ColespanArriba""> EDICIONES CON FECHA DE PUBLICACIÓN SUPERADA</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Nombre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Jurídica</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Últ Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Últ Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Prevista Cierre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Máx.Próx Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Días Caducado </td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_IDEdicion In m_Col
                m_Resto = m_Col(m_IDEdicion)
                dato = Split(m_Resto, "||")
                m_Proyecto = dato(0)
                m_Nombre = dato(1)
                m_Juridica = dato(2)
                m_Edicion = dato(3)
                m_FechaEdicion = dato(4)
                m_FechaPrevistaCierre = dato(5)
                m_FechaMaxProximaPublicacion = dato(6)
                m_Dias = -1 * dato(7)
                m_RespCalidad = dato(8)
                 
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Proyecto & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nombre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Juridica & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Edicion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaEdicion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaPrevistaCierre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaMaxProximaPublicacion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Dias & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getCALIDADHTMLEDICIONESCADUCADAS = m_mensaje
    
End Function

Public Function getHTMLEDICIONESACTIVAS(m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    Dim m_IDEdicion
    Dim m_Resto
    Dim dato
    Dim m_Proyecto
    Dim m_Nombre
    Dim m_Juridica
    Dim m_Edicion
    Dim m_FechaEdicion
    Dim m_FechaMaxProximaPublicacion
    Dim m_Dias
    
    Dim m_FechaPrevistaCierre
    Dim m_RespCalidad
    
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,TbProyectos.FechaPrevistaCierre, " & _
            "TbProyectosEdiciones.IDEdicion,TbProyectosEdiciones.Edicion, TbProyectosEdiciones.FechaEdicion, " & _
            "TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectos.NombreUsuarioCalidad," & _
            "DateDiff('d',now(),[TbProyectosEdiciones].[FechaMaxProximaPublicacion]) AS Días " & _
            "FROM TbProyectos INNER JOIN TbProyectosEdiciones " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
    Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDEdicion").Value) Then
            m_Col.Add rcdDatos.Fields("IDEdicion").Value, _
                    rcdDatos.Fields("Proyecto").Value & "||" & _
                    rcdDatos.Fields("NombreProyecto").Value & "||" & _
                    rcdDatos.Fields("Juridica").Value & "||" & _
                    rcdDatos.Fields("Edicion").Value & "||" & _
                    rcdDatos.Fields("FechaEdicion").Value & "||" & _
                    rcdDatos.Fields("FechaPrevistaCierre").Value & "||" & _
                    rcdDatos.Fields("FechaMaxProximaPublicacion").Value & "||" & _
                    rcdDatos.Fields("Días").Value & "||" & _
                    rcdDatos.Fields("NombreUsuarioCalidad").Value
        End If
        
        
        

        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='9' class=""ColespanArriba""> EDICIONES CON FECHA DE PUBLICACIÓN SUPERADA O A PUNTO DE HACERLO</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Nombre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Jurídica</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Últ Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Últ Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Prevista Cierre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Máx.Próx Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Faltan (Días)</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_IDEdicion In m_Col
                m_Resto = m_Col(m_IDEdicion)
                dato = Split(m_Resto, "||")
                m_Proyecto = dato(0)
                m_Nombre = dato(1)
                m_Juridica = dato(2)
                m_Edicion = dato(3)
                m_FechaEdicion = dato(4)
                m_FechaPrevistaCierre = dato(5)
                m_FechaMaxProximaPublicacion = dato(6)
                m_Dias = dato(7)
                m_RespCalidad = dato(8)
                 
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Proyecto & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nombre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Juridica & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Edicion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaEdicion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaPrevistaCierre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaMaxProximaPublicacion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Dias & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getHTMLEDICIONESACTIVAS = m_mensaje
    
End Function
Public Function getHTMLEDICIONESCERRADASELULTIMOMES(m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    Dim m_Resto
    Dim dato
    Dim m_Proyecto
    Dim m_Nombre
    Dim m_Juridica
    Dim m_FechaCierre
    Dim m_IDEdicion
    
    
    Dim m_RespCalidad
    
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT TbProyectosEdiciones.IDEdicion,TbProyectos.Proyecto, TbProyectos.NombreProyecto, TbProyectos.Juridica,TbProyectos.FechaCierre, " & _
            "TbProyectos.NombreUsuarioCalidad " & _
            "FROM TbProyectos INNER JOIN TbProyectosEdiciones " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND (Not(TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((DateDiff('d',[FechaCierre],Now()))<=30) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
    Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDEdicion").Value) Then
            m_Col.Add rcdDatos.Fields("IDEdicion").Value, _
                    rcdDatos.Fields("Proyecto").Value & "||" & _
                    rcdDatos.Fields("NombreProyecto").Value & "||" & _
                    rcdDatos.Fields("Juridica").Value & "||" & _
                    rcdDatos.Fields("FechaCierre").Value & "||" & _
                    rcdDatos.Fields("NombreUsuarioCalidad").Value
        End If
        
        
        

        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='5' class=""ColespanArriba""> EDICIONES CERRADAS EN LOS ÚLTIMOS 30 DÍAS</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Nombre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Jurídica</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Cierre</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_IDEdicion In m_Col
                m_Resto = m_Col(m_IDEdicion)
                dato = Split(m_Resto, "||")
                m_Proyecto = dato(0)
                m_Nombre = dato(1)
                m_Juridica = dato(2)
                m_FechaCierre = dato(3)
                m_RespCalidad = dato(4)
                 
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Proyecto & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nombre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Juridica & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaCierre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getHTMLEDICIONESCERRADASELULTIMOMES = m_mensaje
    
End Function
Public Function getCALIDADHTMLEDICIONESPREPARADASPARAPUBLICAR(p_UsuarioCalidad, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDEdicion
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_Edicion
    Dim m_FechaMaxProximaPublicacion
    Dim m_FechaPreparadaParaPublicar
    Dim m_Dias
    Dim m_NombreUsuarioCalidad
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    If p_UsuarioCalidad = "" Then
        m_SQL = "SELECT DISTINCT TbExpedientes1.Nemotecnico,TbProyectosEdiciones.IDEdicion, TbProyectosEdiciones.Edicion, TbProyectos.FechaMaxProximaPublicacion, " & _
                "TbProyectosEdiciones.FechaPreparadaParaPublicar, DateDiff('d',Now(),[TbProyectos].[FechaMaxProximaPublicacion]) AS Dias, " & _
                "TbUsuariosAplicaciones.Nombre AS NombreUsuarioCalidad " & _
                "FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
                "INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) " & _
                "LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
                "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
                "AND ((TbProyectos.FechaCierre) Is Null) " & _
                "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
                "AND ((TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha) Is Null)) " & _
                "ORDER BY DateDiff('d',Now(),[TbProyectos].[FechaMaxProximaPublicacion]);"
    Else
        m_SQL = "SELECT DISTINCT TbExpedientes1.Nemotecnico,TbProyectosEdiciones.IDEdicion, TbProyectosEdiciones.Edicion, TbProyectos.FechaMaxProximaPublicacion, " & _
                "TbProyectosEdiciones.FechaPreparadaParaPublicar, DateDiff('d',Now(),[TbProyectos].[FechaMaxProximaPublicacion]) AS Dias, " & _
                "TbUsuariosAplicaciones.Nombre AS NombreUsuarioCalidad " & _
                "FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
                "INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) " & _
                "LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
                "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
                "AND ((TbUsuariosAplicaciones.Nombre)='" & p_UsuarioCalidad & "') " & _
                "AND ((TbProyectos.FechaCierre) Is Null) " & _
                "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
                "AND ((TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha) Is Null)) " & _
                "ORDER BY DateDiff('d',Now(),[TbProyectos].[FechaMaxProximaPublicacion]);"
    End If
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDEdicion").Value) Then
            m_Col.Add rcdDatos.Fields("IDEdicion").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("Edicion").Value & "||" & _
                    rcdDatos.Fields("FechaMaxProximaPublicacion").Value & "||" & _
                    rcdDatos.Fields("FechaPreparadaParaPublicar").Value & "||" & _
                    rcdDatos.Fields("Dias").Value & "||" & _
                    rcdDatos.Fields("NombreUsuarioCalidad").Value
        End If
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> EDICIONES PROPUESTAS PARA PUBLICAR</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Últ Ed</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Máx.Próx Ed.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Propuesta para Publicación</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Faltan (días)</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDEdicion In m_Col
                m_Resto = m_Col(m_IDEdicion)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_Edicion = dato(1)
                m_FechaMaxProximaPublicacion = dato(2)
                m_FechaPreparadaParaPublicar = dato(3)
                m_Dias = dato(4)
                m_NombreUsuarioCalidad = dato(5)
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Edicion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaMaxProximaPublicacion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaPreparadaParaPublicar & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Dias & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_NombreUsuarioCalidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getCALIDADHTMLEDICIONESPREPARADASPARAPUBLICAR = m_mensaje
    
End Function

Public Function getCALIDADHTMLRIESGOSPARARETIPIFICAR(p_UsuarioCalidad, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDRiesgo
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_FechaRiesgoParaRetipificar
    Dim m_UsuarioCalidad
       
    
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, " & _
            "TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad, TbRiesgos.FechaRiesgoParaRetipificar " & _
            "FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbUsuariosAplicaciones_1.Nombre)='" & p_UsuarioCalidad & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)<>'Aceptar') " & _
            "AND ((TbRiesgos.FechaRetirado) Is Null) " & _
            "AND (Not (TbRiesgos.FechaRiesgoParaRetipificar) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
            m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("FechaRiesgoParaRetipificar").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        

        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> RIESGOS QUE HAY QUE ASIGNAR UN CÓDIGO DE BIBLIOTECA</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa raíz</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha para retific.</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_FechaRiesgoParaRetipificar = dato(4)
                m_UsuarioCalidad = dato(5)
                
                
                
                
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td>" & m_Nemotecnico & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaRiesgoParaRetipificar & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_UsuarioCalidad & "</td>" & vbNewLine
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getCALIDADHTMLRIESGOSPARARETIPIFICAR = m_mensaje
    
End Function

Public Function getCALIDADHTMLRIESGOSACEPTADOSPORVISAR(p_UsuarioCalidad, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDRiesgo
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_FechaJustificacionAceptacionRiesgo
    Dim m_UsuarioCalidad
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, " & _
            "TbRiesgos.FechaJustificacionAceptacionRiesgo, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad " & _
            "FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE ((Not (TbRiesgos.FechaJustificacionAceptacionRiesgo) Is Null) " & _
            "AND ((TbUsuariosAplicaciones_1.Nombre)='" & p_UsuarioCalidad & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbRiesgos.FechaAprobacionAceptacionPorCalidad) Is Null) " & _
            "AND ((TbRiesgos.FechaRechazoAceptacionPorCalidad) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
            m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("FechaJustificacionAceptacionRiesgo").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> RIESGOS ACEPTADOS POR EL TÉCNICO A FALTA DE VISADO POR CALIDAD</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Aceptación</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_FechaJustificacionAceptacionRiesgo = dato(4)
                m_UsuarioCalidad = dato(5)
              
                
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaJustificacionAceptacionRiesgo & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_UsuarioCalidad & "</td>" & vbNewLine
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getCALIDADHTMLRIESGOSACEPTADOSPORVISAR = m_mensaje
    
End Function
Public Function getCALIDADHTMLRIESGOSRETIRADOSPORVISAR(p_UsuarioCalidad, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDRiesgo
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_FechaJustificacionRetiroRiesgo
    Dim m_UsuarioCalidad
    
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, " & _
            "TbRiesgos.CausaRaiz, TbRiesgos.FechaJustificacionRetiroRiesgo, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad " & _
            "FROM ((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE ((Not (TbRiesgos.FechaJustificacionRetiroRiesgo) Is Null) " & _
            "AND ((TbUsuariosAplicaciones_1.Nombre)='" & p_UsuarioCalidad & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbRiesgos.FechaAprobacionRetiroPorCalidad) Is Null) " & _
            "AND ((TbRiesgos.FechaRechazoRetiroPorCalidad) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
            m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("FechaJustificacionRetiroRiesgo").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
               
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> RIESGOS RETIRADOS POR EL TÉCNICO A FALTA DE VISADO POR CALIDAD</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Retirado</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
               
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_FechaJustificacionRetiroRiesgo = dato(4)
                m_UsuarioCalidad = dato(5)
               
                
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaJustificacionRetiroRiesgo & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_UsuarioCalidad & "</td>" & vbNewLine
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getCALIDADHTMLRIESGOSRETIRADOSPORVISAR = m_mensaje
    
End Function

Public Function getCALIDADHTMLRIESGOSMATERIALIZADOSPORDECIDIR(p_UsuarioCalidad, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    Dim m_IDRiesgo
   
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_FechaMaterializado
    Dim m_UsuarioCalidad
    
    
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, " & _
            "TbRiesgos.CausaRaiz, TbRiesgos.FechaMaterializado, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad, TbRiesgosNC.FechaDecison " & _
            "FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosNC ON TbRiesgos.IDRiesgo = TbRiesgosNC.IDRiesgo " & _
            "WHERE ((Not (TbRiesgos.FechaMaterializado) Is Null) " & _
            "AND ((TbUsuariosAplicaciones_1.Nombre)='" & p_UsuarioCalidad & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbRiesgosNC.FechaDecison) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
                m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("FechaMaterializado").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
       
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> RIESGOS MATERIALIZADOS SIN DECIDIR SI SE CONVERTIRÁ O NO EN NC POR CALIDAD</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Materializado</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>" & vbNewLine
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_FechaMaterializado = dato(4)
                m_UsuarioCalidad = dato(5)
               
                
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_FechaMaterializado & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_UsuarioCalidad & "</td>" & vbNewLine
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getCALIDADHTMLRIESGOSMATERIALIZADOSPORDECIDIR = m_mensaje
    
End Function




Public Function DameCabeceraHTML(p_Titulo)
    
    Dim m_mensaje
    m_mensaje = "<!DOCTYPE html>" & vbNewLine
    m_mensaje = m_mensaje & "<html lang=""es"">" & vbNewLine
    m_mensaje = m_mensaje & "<head>" & vbNewLine
        m_mensaje = m_mensaje & "<title>" & p_Titulo & "</title>" & vbNewLine
        m_mensaje = m_mensaje & "<meta charset=""ISO-8859-1"" />" & vbNewLine
        'm_mensaje = m_mensaje & "<meta charset=""UTF-8"">" & vbnewline
        m_mensaje = m_mensaje & "<style type=""text/css"">" & vbNewLine
            m_mensaje = m_mensaje & CSS & vbNewLine
        m_mensaje = m_mensaje & "</style>" & vbNewLine
    m_mensaje = m_mensaje & "</head>" & vbNewLine
    m_mensaje = m_mensaje & "<body>" & vbNewLine
    DameCabeceraHTML = m_mensaje
End Function

Public Function getTECNICOHTMLEDICIONESNECESITANPROPUESTAPUBLICACION(p_UsuarioTecnico, m_intN)
    
    Dim m_Col
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDEdicion
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_Edicion
    Dim m_FechaMaxProximaPublicacion
    Dim m_FechaPreparadaParaPublicar
    Dim m_RespCalidad
    Dim m_Dias
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbExpedientes1.Nemotecnico, TbProyectosEdiciones.Edicion, TbProyectosEdiciones.IDEdicion, " & _
            "TbProyectosEdiciones.FechaMaxProximaPublicacion, TbProyectosEdiciones.FechaPreparadaParaPublicar, " & _
            "TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad,DateDiff('d',Now(),[TbProyectos].[FechaMaxProximaPublicacion]) as Dias " & _
            "FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id " & _
            "WHERE (((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((DateDiff('d',Now(),[TbProyectos].[FechaMaxProximaPublicacion]))<=15) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbProyectosEdiciones.FechaPreparadaParaPublicar) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDEdicion").Value) Then
            m_Col.Add rcdDatos.Fields("IDEdicion").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("Edicion").Value & "||" & _
                    rcdDatos.Fields("FechaMaxProximaPublicacion").Value & "||" & _
                    rcdDatos.Fields("FechaPreparadaParaPublicar").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value & "||" & _
                    rcdDatos.Fields("Dias").Value
        End If
        
        
        

        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> EDICIONES QUE NECESITAN PROPUESTA PARA PUBLICAR</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Últ Ed</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Máx.Próx Ed.</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Propuesta para Publicación</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Faltan (días)</td>"
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDEdicion In m_Col
                m_Resto = m_Col(m_IDEdicion)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_Edicion = dato(1)
                m_FechaMaxProximaPublicacion = dato(2)
                m_FechaPreparadaParaPublicar = dato(3)
                m_RespCalidad = dato(4)
                m_Dias = dato(5)
               m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Edicion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaMaxProximaPublicacion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaPreparadaParaPublicar & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Dias & "</td>"
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICOHTMLEDICIONESNECESITANPROPUESTAPUBLICACION = m_mensaje
    
End Function

Public Function getTECNICOHTMLEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS(p_UsuarioTecnico, m_intN)
    
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDEdicion
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_Edicion
    Dim m_FechaMaxProximaPublicacion
    Dim m_FechaPreparadaParaPublicar
    Dim m_PropuestaRechazadaPorCalidadFecha
    Dim m_PropuestaRechazadaPorCalidadMotivo
    Dim m_UsuarioCalidad
    
    
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbExpedientes1.Nemotecnico, TbProyectosEdiciones.Edicion, TbProyectosEdiciones.IDEdicion, " & _
            "TbProyectosEdiciones.FechaMaxProximaPublicacion, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad, " & _
            "TbProyectosEdiciones.FechaPreparadaParaPublicar, TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha, " & _
            "TbProyectosEdiciones.PropuestaRechazadaPorCalidadMotivo " & _
            "FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id " & _
            "WHERE (((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND (Not (TbProyectosEdiciones.FechaPreparadaParaPublicar) Is Null) " & _
            "AND (Not (TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDEdicion").Value) Then
            m_Col.Add rcdDatos.Fields("IDEdicion").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("Edicion").Value & "||" & _
                    rcdDatos.Fields("FechaMaxProximaPublicacion").Value & "||" & _
                    rcdDatos.Fields("FechaPreparadaParaPublicar").Value & "||" & _
                    rcdDatos.Fields("PropuestaRechazadaPorCalidadFecha").Value & "||" & _
                    rcdDatos.Fields("PropuestaRechazadaPorCalidadMotivo").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='7' class=""ColespanArriba"">EDICIONES CON PROPUESTA DE PUBLICACIÓN RECHAZADA</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Últ Ed</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Máx.Próx Ed.</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Propuesta para Publicación</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.Rechazo</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Motivo Rechazo de Propuesta</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDEdicion In m_Col
                m_Resto = m_Col(m_IDEdicion)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_Edicion = dato(1)
                m_FechaMaxProximaPublicacion = dato(2)
                m_FechaPreparadaParaPublicar = dato(3)
                m_PropuestaRechazadaPorCalidadFecha = dato(4)
                m_PropuestaRechazadaPorCalidadMotivo = dato(5)
                m_UsuarioCalidad = dato(6)
               
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Edicion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaMaxProximaPublicacion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaPreparadaParaPublicar & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_PropuestaRechazadaPorCalidadFecha & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_PropuestaRechazadaPorCalidadMotivo & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_UsuarioCalidad & "</td>"
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICOHTMLEDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS = m_mensaje
    
End Function

Public Function getTECNICODHTMLRIESGOSACEPTADOSSINMOTIVAR(p_UsuarioTecnico, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDRiesgo
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_RespCalidad
        
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgos.IDRiesgo, TbExpedientes1.Nemotecnico, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, " & _
            "TbRiesgos.CausaRaiz, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad " & _
            "FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)='Aceptar') " & _
            "AND ((TbRiesgos.FechaJustificacionAceptacionRiesgo) Is Null) " & _
            "AND ((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "'));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
            m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='5' class=""ColespanArriba""> RIESGOS ACEPTADOS SIN MOTIVACIÓN</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_RespCalidad = dato(4)
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>"
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICODHTMLRIESGOSACEPTADOSSINMOTIVAR = m_mensaje
    
End Function
Public Function getTECNICOHTMLRIESGOSACEPTADOSRECHAZADOS(p_UsuarioTecnico, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDRiesgo
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_FechaRechazoAceptacionPorCalidad
    Dim m_RespCalidad
    
    
        
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, " & _
            "TbRiesgos.CausaRaiz, TbRiesgos.FechaRechazoAceptacionPorCalidad, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad " & _
            "FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 " & _
            "ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)='Aceptar') " & _
            "AND ((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "') " & _
            "AND (Not (TbRiesgos.FechaRechazoAceptacionPorCalidad) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
            m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("FechaRechazoAceptacionPorCalidad").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> RIESGOS ACEPTADOS RECHAZADOS POR CALIDAD</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Rechazo</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_FechaRechazoAceptacionPorCalidad = dato(4)
                m_RespCalidad = dato(5)
               
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaRechazoAceptacionPorCalidad & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>"
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICOHTMLRIESGOSACEPTADOSRECHAZADOS = m_mensaje
    
End Function

Public Function getTECNICOHTMLRIESGOSRETIRADOSSINMOTIVAR(p_UsuarioTecnico, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDRiesgo
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_FechaRetirado
    Dim m_RespCalidad
        
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT  TbRiesgos.FechaRetirado, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad, " & _
        "TbExpedientes1.Nemotecnico, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz " & _
        "FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
        "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
        "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
        "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
        "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 " & _
        "ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id " & _
        "WHERE (((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "') " & _
        "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
        "AND ((TbProyectos.FechaCierre) Is Null) " & _
        "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
        "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
        "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
        "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
        "AND (Not (TbRiesgos.FechaRetirado) Is Null) " & _
        "AND ((TbRiesgos.JustificacionRetiroRiesgo) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
            m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("FechaRetirado").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> RIESGOS RETIRADOS SIN MOTIVACIÓN</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.Retirado</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_FechaRetirado = dato(4)
                m_RespCalidad = dato(5)
                
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaRetirado & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>"
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICOHTMLRIESGOSRETIRADOSSINMOTIVAR = m_mensaje
    
End Function

Public Function getTECNICOHTMLRIESGOSRETIRADOSRECHAZADOS(p_UsuarioTecnico, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    
    Dim m_IDRiesgo
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_FechaRetirado
    Dim m_FechaRechazoRetiroPorCalidad
    Dim m_RespCalidad
        
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgos.FechaRetirado, TbRiesgos.FechaRechazoRetiroPorCalidad, TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, " & _
            "TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, TbExpedientes1.Nemotecnico,TbUsuariosAplicaciones.Nombre as UsuarioCalidad " & _
            "FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 " & _
            "ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id " & _
            "WHERE (((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND (Not (TbRiesgos.FechaRetirado) Is Null) " & _
            "AND (Not (TbRiesgos.FechaRechazoRetiroPorCalidad) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDRiesgo").Value) Then
            m_Col.Add rcdDatos.Fields("IDRiesgo").Value, _
                    rcdDatos.Fields("Nemotecnico").Value & "||" & _
                    rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                    rcdDatos.Fields("Descripcion").Value & "||" & _
                    rcdDatos.Fields("CausaRaiz").Value & "||" & _
                    rcdDatos.Fields("FechaRetirado").Value & "||" & _
                    rcdDatos.Fields("FechaRechazoRetiroPorCalidad").Value & "||" & _
                    rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='7' class=""ColespanArriba""> RIESGOS RETIRADOS RECHAZADOS POR CALIDAD</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Retirado</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Rechazo</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_IDRiesgo In m_Col
                m_Resto = m_Col(m_IDRiesgo)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_FechaRetirado = dato(4)
                m_FechaRechazoRetiroPorCalidad = dato(5)
                m_RespCalidad = dato(6)
               
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaRetirado & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaRechazoRetiroPorCalidad & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>"
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICOHTMLRIESGOSRETIRADOSRECHAZADOS = m_mensaje
    
End Function

Public Function getTECNICOHTMLRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR(p_UsuarioTecnico, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    Dim m_ID
   
    Dim m_Resto
    Dim dato
    
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_DisparadorDelPlan
    Dim m_Accion
    Dim m_FechaInicio
    Dim m_FechaFinPrevista
    Dim m_RespCalidad
    
    
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgosPlanMitigacionDetalle.IDAccionMitigacion,TbUsuariosAplicaciones.UsuarioRed, TbRiesgosPlanMitigacionDetalle.FechaFinPrevista, " & _
            "TbRiesgosPlanMitigacionDetalle.FechaInicio, TbExpedientes1.Nemotecnico, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad, " & _
            "TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, " & _
            "TbRiesgosPlanMitigacionPpal.DisparadorDelPlan, TbRiesgosPlanMitigacionDetalle.Accion " & _
            "FROM ((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN ((TbProyectosEdiciones INNER JOIN (TbRiesgos INNER JOIN TbRiesgosPlanMitigacionPpal " & _
            "ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "INNER JOIN TbRiesgosPlanMitigacionDetalle ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 " & _
            "ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id " & _
            "WHERE (((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "') " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND ((TbRiesgos.FechaRetirado) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)<>'Aceptar') " & _
            "AND ((TbRiesgosPlanMitigacionDetalle.FechaFinReal) Is Null) " & _
            "AND ((TbRiesgosPlanMitigacionDetalle.FechaFinPrevista)<=Date()));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
        If Not m_Col.Exists(rcdDatos.Fields("IDAccionMitigacion").Value) Then
            m_Col.Add rcdDatos.Fields("IDAccionMitigacion").Value, _
                rcdDatos.Fields("Nemotecnico").Value & "||" & _
                rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                rcdDatos.Fields("Descripcion").Value & "||" & _
                rcdDatos.Fields("CausaRaiz").Value & "||" & _
                rcdDatos.Fields("DisparadorDelPlan").Value & "||" & _
                rcdDatos.Fields("Accion").Value & "||" & _
                rcdDatos.Fields("FechaInicio").Value & "||" & _
                rcdDatos.Fields("FechaFinPrevista").Value & "||" & _
                rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        

        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='9' class=""ColespanArriba""> RIESGOS CON ACCIONES DE PLANES DE MITIGACIÓN POR REPLANIFICAR</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Disparador</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Acción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Inicio</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Fin Prevista</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_ID In m_Col
                m_Resto = m_Col(m_ID)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_DisparadorDelPlan = dato(4)
                m_Accion = dato(5)
                m_FechaInicio = dato(6)
                m_FechaFinPrevista = dato(7)
                m_RespCalidad = dato(8)
               
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_DisparadorDelPlan & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Accion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaInicio & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaFinPrevista & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>"
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICOHTMLRIESGOSCONACCIONESMITIGACIONPORREPLANIFICAR = m_mensaje
    
End Function

Public Function getTECNICOHTMLRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR(p_UsuarioTecnico, m_intN)
    Dim m_Col
    Dim rcdDatos
    Dim m_SQL
    Dim m_mensaje
    Dim m_ID
    
    Dim m_Resto
    Dim dato
    Dim m_Nemotecnico
    Dim m_CodigoRiesgo
    Dim m_Descripcion
    Dim m_CausaRaiz
    Dim m_DisparadorDelPlan
    Dim m_Accion
    Dim m_FechaInicio
    Dim m_FechaFinPrevista
    Dim m_RespCalidad
    m_intN = 0
    Set m_Col = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbRiesgosPlanContingenciaDetalle.IDAccionContingencia,TbUsuariosAplicaciones.UsuarioRed, TbRiesgosPlanContingenciaDetalle.FechaFinPrevista, " & _
            "TbRiesgosPlanContingenciaDetalle.FechaInicio, TbExpedientes1.Nemotecnico, TbUsuariosAplicaciones_1.Nombre AS UsuarioCalidad, " & _
            "TbRiesgos.IDRiesgo, TbRiesgos.CodigoRiesgo, TbRiesgos.Descripcion, TbRiesgos.CausaRaiz, " & _
            "TbRiesgosPlanContingenciaPpal.DisparadorDelPlan, TbRiesgosPlanContingenciaDetalle.Accion " & _
            "FROM ((((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 ON TbExpedientes1.IDResponsableCalidad = TbUsuariosAplicaciones_1.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanContingenciaPpal " & _
            "ON TbRiesgos.IDRiesgo = TbRiesgosPlanContingenciaPpal.IDRiesgo) INNER JOIN TbRiesgosPlanContingenciaDetalle " & _
            "ON TbRiesgosPlanContingenciaPpal.IDContingencia = TbRiesgosPlanContingenciaDetalle.IDContingencia " & _
            "WHERE (((TbUsuariosAplicaciones.UsuarioRed)='" & p_UsuarioTecnico & "') " & _
            "AND ((TbRiesgosPlanContingenciaDetalle.FechaFinPrevista)<=Date()) " & _
            "AND ((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND ((TbRiesgos.FechaRetirado) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)<>'Aceptar'));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If rcdDatos.EOF Then
        rcdDatos.Close
        Set rcdDatos = Nothing
        Exit Function
    End If
    rcdDatos.MoveFirst
     Do While Not rcdDatos.EOF
       
        If Not m_Col.Exists(rcdDatos.Fields("IDAccionContingencia").Value) Then
            m_Col.Add rcdDatos.Fields("IDAccionContingencia").Value, _
                rcdDatos.Fields("Nemotecnico").Value & "||" & _
                rcdDatos.Fields("CodigoRiesgo").Value & "||" & _
                rcdDatos.Fields("Descripcion").Value & "||" & _
                rcdDatos.Fields("CausaRaiz").Value & "||" & _
                rcdDatos.Fields("DisparadorDelPlan").Value & "||" & _
                rcdDatos.Fields("Accion").Value & "||" & _
                rcdDatos.Fields("FechaInicio").Value & "||" & _
                rcdDatos.Fields("FechaFinPrevista").Value & "||" & _
                rcdDatos.Fields("UsuarioCalidad").Value
        End If
        
        
        
        
        rcdDatos.MoveNext
    Loop
    rcdDatos.Close
    Set rcdDatos = Nothing
    m_intN = m_Col.Count
    If m_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='9' class=""ColespanArriba""> RIESGOS CON ACCIONES DE PLANES DE CONTINGENCIA POR REPLANIFICAR</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Proyecto</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Código</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Descripción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Causa Raíz</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Disparador</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Acción</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Inicio</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Fecha Fin Prevista</td>"
                m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp. Calidad</td>"
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
            For Each m_ID In m_Col
                m_Resto = m_Col(m_ID)
                dato = Split(m_Resto, "||")
                m_Nemotecnico = dato(0)
                m_CodigoRiesgo = dato(1)
                m_Descripcion = dato(2)
                m_CausaRaiz = dato(3)
                m_DisparadorDelPlan = dato(4)
                m_Accion = dato(5)
                m_FechaInicio = dato(6)
                m_FechaFinPrevista = dato(7)
                m_RespCalidad = dato(8)
               
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CodigoRiesgo & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_CausaRaiz & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_DisparadorDelPlan & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_Accion & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaInicio & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_FechaFinPrevista & "</td>"
                    m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>"
                   
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    getTECNICOHTMLRIESGOSCONACCIONESCONTINGENCIAPORREPLANIFICAR = m_mensaje
    
End Function
Public Function getColUsuariosDistintos()
    
    Dim m_Col
    Dim m_Resto
    Dim m_UsuarioRed
    Dim m_Correo
    Dim m_Nombre
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resp
    
    Set m_Col = CreateObject("Scripting.Dictionary")
    
    'EDICIONESNECESITANPROPUESTAPUBLICACION
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "And ((TbProyectos.FechaCierre) Is Null) " & _
            "And ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "And ((DateDiff('d',Now(),TbProyectos.FechaMaxProximaPublicacion))<=15) " & _
            "And ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "And ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbProyectosEdiciones.FechaPreparadaParaPublicar) Is Null) " & _
            "And ((TbUsuariosAplicaciones.FechaBaja) Is Null));"

    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
        rcdDatos.Close
        Set rcdDatos = Nothing
    End If
    
    'EDICIONESCONPROPUESTADEPUBLICACIONRECHAZADAS
    
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN TbProyectosEdiciones ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND (Not (TbProyectosEdiciones.FechaPreparadaParaPublicar) Is Null) " & _
            "AND (Not (TbProyectosEdiciones.PropuestaRechazadaPorCalidadFecha) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
    End If
    
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
    'RIESGOSACEPTADOSNOMOTIVADOS
    
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND (Not (TbRiesgos.FechaRetirado) Is Null) " & _
            "AND ((TbRiesgos.JustificacionRetiroRiesgo) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
        rcdDatos.Close
        Set rcdDatos = Nothing
    End If
    
    
    'RIESGOSACEPTADOSRECHAZADOS
    
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)='Aceptar') " & _
            "AND (Not (TbRiesgos.FechaRechazoAceptacionPorCalidad) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
        rcdDatos.Close
        Set rcdDatos = Nothing
    End If
    
    
    'RIESGOSRETIRADOSNOMOTIVADOS
    
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND (Not (TbRiesgos.FechaRetirado) Is Null) " & _
            "AND ((TbRiesgos.JustificacionRetiroRiesgo) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
        rcdDatos.Close
        Set rcdDatos = Nothing
    End If
    
    'RIESGOSRETIRADOSRECHAZADOS
    
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND (Not (TbRiesgos.FechaRetirado) Is Null) " & _
            "AND (Not (TbRiesgos.FechaRechazoRetiroPorCalidad) Is Null));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
        rcdDatos.Close
        Set rcdDatos = Nothing
    End If
    
    'RIESGOSCONACCIONESMITIGACIONPARAREPLANIFICAR
    
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanMitigacionPpal " & _
            "ON TbRiesgos.IDRiesgo = TbRiesgosPlanMitigacionPpal.IDRiesgo) INNER JOIN TbRiesgosPlanMitigacionDetalle " & _
            "ON TbRiesgosPlanMitigacionPpal.IDMitigacion = TbRiesgosPlanMitigacionDetalle.IDMitigacion " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND ((TbRiesgos.FechaRetirado) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)<>'Aceptar') " & _
            "AND ((TbRiesgosPlanMitigacionDetalle.FechaFinReal) Is Null) " & _
            "AND ((TbRiesgosPlanMitigacionDetalle.FechaFinPrevista)<=Date()));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
        rcdDatos.Close
        Set rcdDatos = Nothing
    End If
    
    
    'RIESGOSCONACCIONESCONTINGENCIAPARAREPLANIFICAR
    
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM (((((TbProyectos INNER JOIN TbExpedientes1 ON TbProyectos.IDExpediente = TbExpedientes1.IDExpediente) " & _
            "INNER JOIN TbExpedientesResponsables ON TbExpedientes1.IDExpediente = TbExpedientesResponsables.IdExpediente) " & _
            "INNER JOIN TbUsuariosAplicaciones ON TbExpedientesResponsables.IdUsuario = TbUsuariosAplicaciones.Id) " & _
            "INNER JOIN (TbProyectosEdiciones INNER JOIN TbRiesgos ON TbProyectosEdiciones.IDEdicion = TbRiesgos.IDEdicion) " & _
            "ON TbProyectos.IDProyecto = TbProyectosEdiciones.IDProyecto) INNER JOIN TbRiesgosPlanContingenciaPpal " & _
            "ON TbRiesgos.IDRiesgo = TbRiesgosPlanContingenciaPpal.IDRiesgo) INNER JOIN TbRiesgosPlanContingenciaDetalle " & _
            "ON TbRiesgosPlanContingenciaPpal.IDContingencia = TbRiesgosPlanContingenciaDetalle.IDContingencia " & _
            "WHERE (((TbProyectos.ParaInformeAvisos)<>'No') " & _
            "AND ((TbProyectos.FechaCierre) Is Null) " & _
            "AND ((TbProyectosEdiciones.FechaPublicacion) Is Null) " & _
            "AND ((TbExpedientesResponsables.EsJefeProyecto)='Sí') " & _
            "AND ((TbExpedientesResponsables.CorreoSiempre)='Sí') " & _
            "AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) " & _
            "AND ((TbRiesgos.FechaRetirado) Is Null) " & _
            "AND ((TbRiesgos.Mitigacion)<>'Aceptar') " & _
            "AND ((TbRiesgosPlanContingenciaDetalle.FechaFinReal) Is Null) " & _
            "AND ((TbRiesgosPlanContingenciaDetalle.FechaFinPrevista)<=Date()));"
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnRiesgos, adOpenDynamic, adLockPessimistic, adCmdText
    
    If Not rcdDatos.EOF Then
        rcdDatos.MoveFirst
         Do While Not rcdDatos.EOF
            m_UsuarioRed = rcdDatos.Fields("UsuarioRed").Value
            m_Nombre = rcdDatos.Fields("Nombre").Value
            m_Correo = rcdDatos.Fields("CorreoUsuario").Value
            
            If Not m_Col.Exists(m_UsuarioRed) Then
                m_Col.Add m_UsuarioRed, m_Nombre & "|" & m_Correo
            End If
            
            
            rcdDatos.MoveNext
        Loop
        rcdDatos.Close
        Set rcdDatos = Nothing
    End If
    Set getColUsuariosDistintos = m_Col
End Function

Lanzar











