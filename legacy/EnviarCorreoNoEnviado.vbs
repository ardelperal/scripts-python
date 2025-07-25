Dim dato


Const adStateClosed = 0
Const adStateOpen = 1
Const adOpenForwardOnly = 0
Const adOpenKeyset = 1
Const adOpenStatic = 3

Const adLockBatchOptimistic = 4
Const adLockOptimistic = 3
Const adLockPessimistic = 2
Const adLockReadOnly = 1

Const adOpenDynamic = 2
Const adUseClient = 3

Const adCmdText = 1

Dim CnCorreo
Dim CnCorreoPrueba
Dim m_URLCorreo
Dim m_URLCorreoPrueba


Private Function Conn( _
                        p_URL, _
                        p_Pass _
                        )
    
    Dim m_ConnectionString
    Dim m_Provider
    
    Set Conn = CreateObject("adodb.Connection")
    
    m_Provider = "Microsoft.ACE.OLEDB.12.0"
    m_ConnectionString = "Data Source=" & p_URL & ";" & "Jet OLEDB:Database Password=" & p_Pass & ";"
    
    
    With Conn
        .Provider = m_Provider
        .ConnectionString = m_ConnectionString
        .CursorLocation = adUseClient
        .Open
    End With
    
    
End Function


Public Function EnviarCorreosNoEnviados(Cn)
    Dim rcdDatos
    Dim strNombreTablaRemota
    Dim strTieneCampoAdjunto
    Dim strFrom
    Dim intNumeroRegistros
    Dim strFechaEnvio
    Dim strNumTareas
    Dim strUsuario
    Dim strTitulo
    Dim strIDCorreo
    Dim strOriginador
    Dim strDestinatarios
    Dim strDestinatariosConCopia
    Dim strDestinatariosConCopiaOculta
    Dim strAsunto
    Dim strCuerpo
    Dim strURLAdjunto
    Dim Aplicacion

    strSQL = "SELECT TbCorreosEnviados.* " & _
                 "FROM TbCorreosEnviados " & _
                 "WHERE TbCorreosEnviados.FechaEnvio Is Null;"
     Set rcdDatos = CreateObject("ADODB.Recordset")
     rcdDatos.Open strSQL, Cn, adOpenDynamic, adLockPessimistic, adCmdText

     With rcdDatos
         If Not .EOF Then
             Do While Not .EOF
                 strIDCorreo = .Fields("IDCorreo")
                 Aplicacion = .Fields("Aplicacion")
                 strDestinatarios = .Fields("Destinatarios")
                 strDestinatariosConCopia = .Fields("DestinatariosConCopia")
                 strDestinatariosConCopiaOculta = .Fields("DestinatariosConCopiaOculta")
                 strAsunto = .Fields("Asunto")
                 strCuerpo = .Fields("Cuerpo")
                 strURLAdjunto = .Fields("URLAdjunto")
                 
                 
                 'If InStr(1, strURLAdjunto, ":\") = 0 Then Stop
                 strFechaEnvio = EnviarCorreo(Aplicacion, strAsunto, strCuerpo, strDestinatarios, strDestinatariosConCopia, strDestinatariosConCopiaOculta, strURLAdjunto)
                 If IsDate(strFechaEnvio) Then
                     .Fields("FechaEnvio") = strFechaEnvio
                     .Update
                    
                 End If
                 .MoveNext
             Loop
         
         End If
         .Close
     End With
     Set rcdDatos = Nothing
        
        

End Function

Public Function EnviarCorreo( _
                                strQue, _
                                strAsunto, _
                                strMensaje, _
                                strCadenaDestinatarios, _
                                strCadenaDestinatariosEnCopia, _
                                strCadenaDestinatariosOcultos, _
                                strCadenaURLs _
                                )
    
    Dim strFrom, strFechaEnvio, strURL, varItem, dato, MiMensaje, MiConfiguracion, FSO
    Dim m_IPServidorCorreo
    On Error Resume Next
    Set FSO = CreateObject("Scripting.FileSystemObject")
    strFrom = strQue & ".DySN@telefonica.com"
    
    If InStr(1, strCadenaDestinatariosOcultos, "Andres.RomandelPeral@telefonica.com") = 0 Then
        If strCadenaDestinatariosOcultos = "" Then
            strCadenaDestinatariosOcultos = "Andres.RomandelPeral@telefonica.com"
        Else
            strCadenaDestinatariosOcultos = strCadenaDestinatariosOcultos & ";" & "Andres.RomandelPeral@telefonica.com"
        End If
    End If
    m_IPServidorCorreo = "10.73.54.85"

    Set MiConfiguracion = CreateObject("CDO.Configuration")
    With MiConfiguracion
        .Fields("http://schemas.microsoft.com/cdo/configuration/smtpserver") = m_IPServidorCorreo
        .Fields("http://schemas.microsoft.com/cdo/configuration/smtpserverport") = 25
        .Fields("http://schemas.microsoft.com/cdo/configuration/sendusing") = 2
        .Fields("http://schemas.microsoft.com/cdo/configuration/smtpconnectiontimeout") = 5
        .Fields.Update
    End With
    Set MiMensaje = CreateObject("CDO.Message")
    With MiMensaje
        Set .Configuration = MiConfiguracion
        .FROM = strFrom
        If InStr(1, strCadenaDestinatarios, "@") <> 0 Then
            .To = strCadenaDestinatarios
        End If
        If InStr(1, strCadenaDestinatariosEnCopia, "@") <> 0 Then
            .Cc = strCadenaDestinatariosEnCopia
        End If
        If strCadenaDestinatariosOcultos <> "" Then
            .BCC = strCadenaDestinatariosOcultos
        End If
        .Subject = strAsunto
      .HTMLBody = strMensaje
        If Not IsNull(strCadenaURLs) Then
            If InStr(1, strCadenaURLs, ";") <> 0 Then
                dato = Split(strCadenaURLs, ";")
                For Each varItem In dato
                    strURL = CStr(varItem)
                    If FSO.FileExists(strURL) Then
                        .AddAttachment strURL
                    End If
                Next
            Else
                If FSO.FileExists(strCadenaURLs) Then
                    .AddAttachment strCadenaURLs
                End If
            End If
        End If
        
        On Error Resume Next
       .Send
       'strFechaEnvio = Now()
        If Err.Number = 0 Then
            strFechaEnvio = Now()
            EnviarCorreo = strFechaEnvio
         Else
            
            EnviarCorreo = ""
        End If
        
    End With
    Set FSO = Nothing
    Set MiMensaje = Nothing
    Set MiConfiguracion = Nothing
    EnviarCorreo = strFechaEnvio
    Exit Function
End Function

Public Sub Lanzar()
    Dim FSO
    
    Const m_Pass = "dpddpd"
    
    
    Set FSO = CreateObject("Scripting.FileSystemObject")
    
    m_URLCorreo = "\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Correos_datos.accdb"
    If FSO.FileExists(m_URLCorreo) Then
        Set CnCorreo = Conn(m_URLCorreo, m_Pass)
        EnviarCorreosNoEnviados CnCorreo
        CnCorreo.Close
        Set CnCorreo = Nothing
    End If
    
    
    
End Sub
Lanzar

