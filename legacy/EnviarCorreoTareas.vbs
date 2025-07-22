
Option Explicit



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
Dim cn

Private Function EVE()
    Set cn = Conn()
End Function

Private Function Conn()
    
    Dim m_ConnectionString
    Dim m_Provider
    Dim m_URL
    Dim m_Pass
    
    m_URL = "\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb"
    m_Pass = "dpddpd"
    Set Conn = CreateObject("adodb.Connection")
    
    m_Provider = "Microsoft.ACE.OLEDB.12.0"
    m_ConnectionString = "Data Source=" & m_URL & ";" & "Jet OLEDB:Database Password=" & m_Pass & ";"
    With Conn
        .Provider = m_Provider
        .ConnectionString = m_ConnectionString
        .CursorLocation = adUseClient
        .Open
    End With
    
    
End Function


Public Function EnviarCorreosNoEnviados()
    Dim rcdDatos
    Dim m_SQL
    Dim m_FechaEnvio
    Dim m_Destinatarios
    Dim m_DestinatariosConCopia
    Dim m_Asunto
    Dim m_Cuerpo
    Dim Aplicacion
    Dim m_ID
    
     m_SQL = "SELECT TbCorreosEnviados.* " & _
                 "FROM TbCorreosEnviados " & _
                 "WHERE TbCorreosEnviados.FechaEnvio Is Null;"
     Set rcdDatos = CreateObject("ADODB.Recordset")
     rcdDatos.Open m_SQL, cn, adOpenDynamic, adLockPessimistic, adCmdText

     With rcdDatos
         If Not .EOF Then
             Do While Not .EOF
                 Aplicacion = .Fields("Aplicacion")
                 m_Destinatarios = .Fields("Destinatarios")
                 m_DestinatariosConCopia = .Fields("DestinatariosConCopia")
                 m_Asunto = .Fields("Asunto")
                 m_Cuerpo = .Fields("Cuerpo")
                 m_ID = .Fields("IDCorreo")
                 m_FechaEnvio = EnviarCorreo(Aplicacion, m_Asunto, m_Cuerpo, m_Destinatarios, m_DestinatariosConCopia)
                 If IsDate(m_FechaEnvio) Then
                    m_SQL = "UPDATE TbCorreosEnviados SET TbCorreosEnviados.FechaEnvio = Now() " & _
                            "WHERE (((TbCorreosEnviados.IDCorreo)=" & m_ID & ") AND ((TbCorreosEnviados.FechaEnvio) Is Null));"
                    cn.Execute m_SQL
     
                 End If
                 
                 .MoveNext
             Loop
         
         End If
         .Close
     End With
     Set rcdDatos = Nothing
     
        

End Function
Public Function RegistrarCorreoEnviado(p_ID)
    
    
    Dim m_SQL
    
   
    
     
     m_SQL = "UPDATE TbCorreosEnviados SET TbCorreosEnviados.FechaEnvio = Now() " & _
            "WHERE (((TbCorreosEnviados.IDCorreo)=" & p_ID & ") AND ((TbCorreosEnviados.FechaEnvio) Is Null));"
    cn.Execute m_SQL
     
        

End Function
Public Function EnviarCorreo( _
                                p_Aplicacion, _
                                p_Asunto, _
                                p_Mensaje, _
                                p_Destinatarios, _
                                p_DestinatariosConCopia _
                                )
    
    Dim m_From
    Dim MiMensaje
    Dim MiConfiguracion
    Dim m_DestinatarioOculto
    Dim m_IPServidorCorreo
    Dim strFechaEnvio
    m_IPServidorCorreo = "10.73.54.85"
    
    m_From = p_Aplicacion & ".DySN@telefonica.com"
    m_DestinatarioOculto = "Andres.RomandelPeral@telefonica.com"
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
        .FROM = m_From
        If InStr(1, p_Destinatarios, "@") <> 0 Then
            .To = p_Destinatarios
        End If
        If InStr(1, p_DestinatariosConCopia, "@") <> 0 Then
            .Cc = p_DestinatariosConCopia
        End If
        If InStr(1, m_DestinatarioOculto, "@") <> 0 Then
            .BCC = m_DestinatarioOculto
        End If
        
        
       
        
        .Subject = p_Asunto
        .HTMLBody = p_Mensaje
        
        
        On Error Resume Next
       .Send
       If Err.Number = 0 Then
            strFechaEnvio = Now()
            EnviarCorreo = strFechaEnvio
         Else
            
            EnviarCorreo = ""
        End If
    End With
    
    Set MiMensaje = Nothing
    Set MiConfiguracion = Nothing
    
    
End Function

Public Function Lanzar()
    EVE
    EnviarCorreosNoEnviados
    cn.Close
     Set cn = Nothing
    
End Function
Lanzar





