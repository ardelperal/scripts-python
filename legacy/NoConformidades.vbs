
Option Explicit




Dim m_IDAplicacion
Dim ColUsuariosAdministradores
Dim m_CadenaCorreoAdministradores

Dim m_DiasNecesariosParaTecnicos
Dim ColUsuariosCalidad
Dim ColUsuariosCalidadParaExcluir
Dim m_CadenaCorreoCalidad


Const m_Pass = "dpddpd"
Dim m_URLBBDDTareas
Dim CnTareas
Dim m_URLBBDDNC
Dim CnNC
Dim m_URLCSS
Dim CSS
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



Public Function GenerarColParaTecnicos(p_ColTecnicosNCAPuntoDeCaducar, p_ColTecnicosNCCaducadas, p_ColTecnicosNCAccionesParaReplanificar, p_ColTecnicosNCAbiertasConTodasAccionesCerradas)
    Dim m_Usuario
    
    
    Set GenerarColParaTecnicos = CreateObject("Scripting.Dictionary")
    If p_ColTecnicosNCAPuntoDeCaducar.Count > 0 Then
        For Each m_Usuario In p_ColTecnicosNCAPuntoDeCaducar
            If Not ColUsuariosCalidadParaExcluir.Exists(m_Usuario) Then
                If Not GenerarColParaTecnicos.Exists(m_Usuario) Then
                    GenerarColParaTecnicos.Add m_Usuario, m_Usuario
                End If
            End If
            
        Next
    End If
    If p_ColTecnicosNCCaducadas.Count > 0 Then
        For Each m_Usuario In p_ColTecnicosNCCaducadas
            If Not ColUsuariosCalidadParaExcluir.Exists(m_Usuario) Then
                If Not GenerarColParaTecnicos.Exists(m_Usuario) Then
                    GenerarColParaTecnicos.Add m_Usuario, m_Usuario
                End If
            End If
            
        Next
    End If
    If p_ColTecnicosNCAccionesParaReplanificar.Count > 0 Then
        For Each m_Usuario In p_ColTecnicosNCAccionesParaReplanificar
            If Not ColUsuariosCalidadParaExcluir.Exists(m_Usuario) Then
                If Not GenerarColParaTecnicos.Exists(m_Usuario) Then
                    GenerarColParaTecnicos.Add m_Usuario, m_Usuario
                End If
            End If
            
        Next
    End If
    If p_ColTecnicosNCAbiertasConTodasAccionesCerradas.Count > 0 Then
        For Each m_Usuario In p_ColTecnicosNCAbiertasConTodasAccionesCerradas
            If Not ColUsuariosCalidadParaExcluir.Exists(m_Usuario) Then
                If Not GenerarColParaTecnicos.Exists(m_Usuario) Then
                    GenerarColParaTecnicos.Add m_Usuario, m_Usuario
                End If
            End If
        Next
    End If
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

Public Function UltimaEjecucionTecnica()
    
    Dim rcdDatos
    Dim m_SQL
    
    m_SQL = "SELECT Last(TbTareas.Fecha) AS Ultima " & _
            "FROM TbTareas " & _
            "WHERE Tarea='NCTecnico' AND Realizado='Sí';"
    
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        
        If Not .EOF Then
           UltimaEjecucionTecnica = .Fields("Ultima")
        End If
        
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Public Function UltimaEjecucionCalidad()
    
    Dim rcdDatos
    Dim m_SQL
    
    m_SQL = "SELECT Last(TbTareas.Fecha) AS Ultima " & _
            "FROM TbTareas " & _
            "WHERE Tarea='NCCalidad' AND Realizado='Sí';"
    
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        
        If Not .EOF Then
           UltimaEjecucionCalidad = .Fields("Ultima")
        End If
        
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function

Public Function RequiereTareaCalidad()
    
    
    Dim m_FechaUltimaEjecucion
    Dim m_FechaHoy
    
    
    
    m_FechaHoy = Date
    
    m_FechaUltimaEjecucion = UltimaEjecucionCalidad()
    If Not IsDate(m_FechaUltimaEjecucion) Then
        If Weekday(m_FechaHoy) = 2 Then
            RequiereTareaCalidad = True
        Else
            RequiereTareaCalidad = False
        End If
        Exit Function
    Else
        If m_FechaUltimaEjecucion = m_FechaHoy Then
            RequiereTareaCalidad = False
            Exit Function
        End If
    End If
    If Weekday(m_FechaHoy) = 2 Then
        RequiereTareaCalidad = True
    Else
        RequiereTareaCalidad = False
    End If
    
    
    
End Function

Public Function RequiereTareaTecnica()
    
    
    Dim m_FechaUltimaEjecucion
    Dim m_FechaHoy
    Dim m_DiasTranscurridos
    
    
    m_FechaHoy = Date
    
    m_FechaUltimaEjecucion = UltimaEjecucionTecnica()
    If Not IsDate(m_FechaUltimaEjecucion) Then
        RequiereTareaTecnica = True
        Exit Function
    End If
    m_DiasTranscurridos = DateDiff("d", Date, m_FechaUltimaEjecucion)
    If CLng(m_DiasTranscurridos) < 0 Then m_DiasTranscurridos = m_DiasTranscurridos * -1
    If m_DiasTranscurridos >= m_DiasNecesariosParaTecnicos Then
        RequiereTareaTecnica = True
    Else
        RequiereTareaTecnica = False
    End If
    
    
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



Public Function getIDCorreo()
    Dim rcdDatos
    Dim lngOrdinalMaximo
    Dim m_SQL
   
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
Public Function getIDAvisos()
    Dim rcdDatos
    Dim lngOrdinalMaximo
    Dim m_SQL
   
    m_SQL = "SELECT Max(TbNCARAvisos.ID) AS Maximo " & _
            "FROM TbNCARAvisos;"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If Not .EOF Then
            If IsNumeric(.Fields("Maximo")) Then
                lngOrdinalMaximo = .Fields("Maximo")
            End If
        End If
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    getIDAvisos = lngOrdinalMaximo + 1
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
            .Fields("Aplicacion") = "NC"
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

Public Function RegistrarCorreoTareaTecnica(p_Asunto, p_Cuerpo, p_Destinatarios, p_CorreoRespCalidad)

    Dim rcdDatos
    Dim m_SQL
    Dim m_IDCorreo
    
'    p_Destinatarios = "andres.romandelperal@telefonica.com"
'    m_CadenaCorreoAdministradores = ""
    m_IDCorreo = getIDCorreo()
    If Not IsNumeric(m_IDCorreo) Then
        RegistrarCorreoTareaTecnica = ""
        Exit Function
    End If
    m_SQL = "SELECT TbCorreosEnviados.* " & _
            "FROM TbCorreosEnviados;"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
       .AddNew
            .Fields("IDCorreo") = m_IDCorreo
            .Fields("Aplicacion") = "NC"
            .Fields("Asunto") = p_Asunto
            .Fields("Cuerpo") = p_Cuerpo
            If InStr(1, p_Destinatarios, "@") <> 0 Then
                .Fields("Destinatarios") = p_Destinatarios
            End If
            If InStr(1, p_CorreoRespCalidad, "@") <> 0 Then
                .Fields("DestinatariosConCopia") = p_CorreoRespCalidad
            End If
            .Fields("DestinatariosConCopiaOculta") = m_CadenaCorreoAdministradores
            .Fields("FechaGrabacion") = Now()
        .Update
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    RegistrarCorreoTareaTecnica = m_IDCorreo
End Function
Public Function MarcarCorreoEnviadoEnAR(p_IDCorreo, p_ColARAPC15, p_ColARAPC7, p_ColARAPC0)
    Dim m_ID
    Dim rcdDatos
    Dim m_SQL
    Dim m_IDAR
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    If p_ColARAPC15.Count > 0 Then
        For Each m_IDAR In p_ColARAPC15
            m_ID = getIDAvisos()
            m_SQL = "SELECT * FROM TbNCARAvisos;"
            rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
            With rcdDatos
                .Fields("ID") = m_ID
                    .Fields("IDAR") = m_IDAR
                    .Fields("IDCorreo15") = p_IDCorreo
                    .Fields("Fecha") = Date
                .Update
            End With
            rcdDatos.Close
            
        Next
    End If
    If p_ColARAPC7.Count > 0 Then
        For Each m_IDAR In p_ColARAPC7
            m_ID = getIDAvisos()
            m_SQL = "SELECT * FROM TbNCARAvisos;"
            rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
            With rcdDatos
                .AddNew
                    .Fields("ID") = m_ID
                    .Fields("IDAR") = m_IDAR
                    .Fields("IDCorreo7") = p_IDCorreo
                    .Fields("Fecha") = Date
                .Update
            End With
            rcdDatos.Close
            
        Next
    End If
    If p_ColARAPC0.Count > 0 Then
        For Each m_IDAR In p_ColARAPC0
            m_ID = getIDAvisos()
            m_SQL = "SELECT * FROM TbNCARAvisos;"
            rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
            With rcdDatos
               
                .AddNew
                    .Fields("ID") = m_ID
                    .Fields("IDAR") = m_IDAR
                    .Fields("IDCorreo0") = p_IDCorreo
                    .Fields("Fecha") = Date
                .Update
            End With
            rcdDatos.Close
            
        Next
    End If
    Set rcdDatos = Nothing
    
    
    
    
End Function
Public Function RegistrarTareaTecnica()
    'NCTecnico
    
    Dim rcdDatos
    
    Dim m_SQL
    
    m_SQL = "SELECT * " & _
            "FROM TbTareas " & _
            "WHERE Tarea='NCTecnico';"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            .AddNew
                .Fields("Tarea") = "NCTecnico"
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
Public Function RegistrarTareaCalidad()
    'NCCalidad
    
    Dim rcdDatos
    
    Dim m_SQL
    
    m_SQL = "SELECT * " & _
            "FROM TbTareas " & _
            "WHERE Tarea='NCCalidad';"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            .AddNew
                .Fields("Tarea") = "NCCalidad"
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


Public Function HTMLTablaARAPC(p_Col, p_Tipo)
    
    Dim dato
    
    Dim m_ID
    Dim m_mensaje
    Dim m_Resto
    Dim m_IDAccionRealizada
    Dim m_CodigoNoConformidad
    Dim m_AccionCorrectiva
    Dim m_AccionRealizada
    Dim m_FechaInicio
    Dim m_FechaFinPrevista
    Dim m_DiasParaCaducar
    Dim m_RespCalidad
    Dim m_Nemotecnico
    Dim m_Titulo
    
    If p_Col.Count = 0 Then
        Exit Function
    End If
    If p_Tipo = "15" Then
        m_Titulo = "TAREAS DE ACCIONES CORRECTIVAS A MENOS DE 15 DÍAS DE CADUCAR"
    ElseIf p_Tipo = "7" Then
        m_Titulo = "TAREAS DE ACCIONES CORRECTIVAS A MENOS DE 7 DÍAS DE CADUCAR"
    ElseIf p_Tipo = "0" Then
        m_Titulo = "TAREAS DE ACCIONES CORRECTIVAS CADUCADAS"
    Else
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='8' class=""ColespanArriba"">" & m_Titulo & "</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > NC</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > EXP</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > ACCIÓN CORRECTIVA</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > TAREA</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F. INICIO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.FIN PREVISTA</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > Días para Caducar</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > Resp.Calidad</td>" & vbNewLine
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_ID In p_Col
            m_Resto = p_Col(m_ID)
            dato = Split(m_Resto, "|")
            m_CodigoNoConformidad = dato(0)
            m_AccionCorrectiva = dato(1)
            m_AccionRealizada = dato(2)
            m_FechaInicio = dato(3)
            m_FechaFinPrevista = dato(4)
            m_DiasParaCaducar = dato(5)
            m_RespCalidad = dato(6)
            m_Nemotecnico = dato(7)
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoNoConformidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_AccionCorrectiva & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_AccionRealizada & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FechaInicio & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FechaFinPrevista & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_DiasParaCaducar & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RespCalidad & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaARAPC = m_mensaje
    
End Function

Public Function HTMLIndicadoresCalidad(NReplanificaciones, NCerradas, NCAbiertas)
    
    
    
    Dim m_mensaje
    Dim m_Titulo
    
    If Not IsNumeric(NReplanificaciones) Then NReplanificaciones = 0
    If Not IsNumeric(NCerradas) Then NCerradas = 0
    If Not IsNumeric(NCAbiertas) Then NCAbiertas = 0
    
    m_Titulo = "DATOS RESÚMEN DE LOS ÚLTIMOS 30 DÍAS"
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='3' class=""ColespanArriba"">" & m_Titulo & "</td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > REPLANIFICACIONES</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > CERRADAS</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > ABIERTAS</td>" & vbNewLine
           
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td> " & NReplanificaciones & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td> " & NCerradas & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td> " & NCAbiertas & "</td>" & vbNewLine
            
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLIndicadoresCalidad = m_mensaje
    
End Function

Public Function HTMLTablaNCResueltasPteCE(p_Col)
    
    Dim dato
    
    Dim m_NC
    Dim m_mensaje
    Dim m_Resto
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_DESCRIPCION
    Dim m_RESPONSABLECALIDAD
    Dim m_FECHACIERRE
    Dim m_FechaPrevistaControlEficacia
    Dim m_Dias
    
    
    If p_Col.Count = 0 Then
        Exit Function
    End If
        
                
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='7' class=""ColespanArriba""> NO CONFORMIDADES DE PROYECTO RESUELTAS PENDIENTES DE CONTROL DE EFICACIA </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > NEMOTÉCNICO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > CÓDIGO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > DESCRIPCIÓN</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > RESP.CALIDAD</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.CIERRE</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.PREV. CE</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > DÍAS RESTANTES</td>" & vbNewLine
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_NC In p_Col
            dato = Split(p_Col(m_NC), "|")
            m_Nemotecnico = dato(0)
            m_CodigoNoConformidad = m_NC
            m_DESCRIPCION = dato(1)
            m_RESPONSABLECALIDAD = dato(2)
            m_FECHACIERRE = dato(3)
            m_FechaPrevistaControlEficacia = dato(4)
            m_Dias = dato(5)
            
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoNoConformidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_DESCRIPCION & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FECHACIERRE & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FechaPrevistaControlEficacia & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Dias & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
                
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    HTMLTablaNCResueltasPteCE = m_mensaje
End Function


Public Function getColNCResueltasPteCE()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resto
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_DESCRIPCION
    Dim m_RESPONSABLECALIDAD
    Dim m_FECHACIERRE
    Dim m_FechaPrevistaControlEficacia
    Dim m_Dias
    
    
   Set getColNCResueltasPteCE = CreateObject("Scripting.Dictionary")
    '---------------------------------
    ' Tabla registros caducados
    '---------------------------------
    m_SQL = "SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, TbNoConformidades.DESCRIPCION, " & _
            "TbNoConformidades.RESPONSABLECALIDAD,  TbNoConformidades.FECHACIERRE,TbNoConformidades.FechaPrevistaControlEficacia, " & _
            "DateDiff('d',Now(),[FechaPrevistaControlEficacia]) AS Dias " & _
            "FROM TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas " & _
            "ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) " & _
            "ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad " & _
            "WHERE (((DateDiff('d',Now(),[FechaPrevistaControlEficacia]))<30) " & _
            "AND (Not (TbNCAccionesRealizadas.FechaFinReal) Is Null) AND ((TbNoConformidades.RequiereControlEficacia)='Sí') " & _
            "AND ((TbNoConformidades.FechaControlEficacia) Is Null));"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_Nemotecnico = .Fields("Nemotecnico")
            m_CodigoNoConformidad = .Fields("CodigoNoConformidad")
            m_DESCRIPCION = .Fields("DESCRIPCION")
            m_RESPONSABLECALIDAD = .Fields("RESPONSABLECALIDAD")
            m_FECHACIERRE = .Fields("FECHACIERRE")
            m_FechaPrevistaControlEficacia = .Fields("FechaPrevistaControlEficacia")
            m_Dias = .Fields("Dias")
       
            
            If Not getColNCResueltasPteCE.Exists(m_CodigoNoConformidad) Then
                getColNCResueltasPteCE.Add m_CodigoNoConformidad, m_Nemotecnico & "|" & m_DESCRIPCION & "|" & m_RESPONSABLECALIDAD & _
                    "|" & m_FECHACIERRE & "|" & m_FechaPrevistaControlEficacia & "|" & m_Dias
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function

Public Function getColARAPC(p_Usuario, p_Tipo)
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_SQLInicial
    Dim m_Where
    
    Dim m_Resto
    Dim m_IDAccionRealizada
    Dim m_CodigoNoConformidad
    Dim m_AccionCorrectiva
    Dim m_AccionRealizada
    Dim m_FechaInicio
    Dim m_FechaFinPrevista
    Dim m_DiasParaCaducar
    Dim m_RespCalidad
    Dim m_Nemotecnico
    
    Set getColARAPC = CreateObject("Scripting.Dictionary")
    m_SQLInicial = "SELECT distinct TbNoConformidades.CodigoNoConformidad, TbNCAccionesRealizadas.IDAccionRealizada, " & _
                "TbNCAccionCorrectivas.AccionCorrectiva, TbNCAccionesRealizadas.AccionRealizada, " & _
                "TbNCAccionesRealizadas.FechaInicio, TbNCAccionesRealizadas.FechaFinPrevista, " & _
                "TbUsuariosAplicaciones.Nombre, DateDiff('d',Now(),[FechaFinPrevista]) AS DiasParaCaducar, " & _
                "TbUsuariosAplicaciones.CorreoUsuario AS CorreoCalidad, TbExpedientes.Nemotecnico " & _
                "FROM ((TbNoConformidades LEFT JOIN TbUsuariosAplicaciones " & _
                "ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed) " & _
                "INNER JOIN (TbNCAccionCorrectivas INNER JOIN (TbNCAccionesRealizadas LEFT JOIN TbNCARAvisos " & _
                "ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR) " & _
                "ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) " & _
                "ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad) " & _
                "LEFT JOIN TbExpedientes ON TbNoConformidades.IDExpediente = TbExpedientes.IDExpediente "
    If p_Tipo = "15" Then
        m_Where = "WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) " & _
                "AND ((DateDiff('d',Now(),[FechaFinPrevista]))>=8 And (DateDiff('d',Now(),[FechaFinPrevista]))<=15) " & _
                "AND ((TbNCARAvisos.IDCorreo15) Is Null) AND ((TbNoConformidades.RESPONSABLETELEFONICA)='" & p_Usuario & "'));"
        
    ElseIf p_Tipo = "7" Then
        m_Where = "WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) " & _
                "AND ((DateDiff('d',Now(),[FechaFinPrevista]))>0 And (DateDiff('d',Now(),[FechaFinPrevista]))<=7) " & _
                "AND ((TbNCARAvisos.IDCorreo7) Is Null) AND ((TbNoConformidades.RESPONSABLETELEFONICA)='" & p_Usuario & "'));"
    ElseIf p_Tipo = "0" Then
        m_Where = "WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) " & _
                "AND ((DateDiff('d',Now(),[FechaFinPrevista]))<=0) " & _
                "AND ((TbNCARAvisos.IDCorreo0) Is Null) AND ((TbNoConformidades.RESPONSABLETELEFONICA)='" & p_Usuario & "'));"
    Else
        Exit Function
    End If
    m_SQL = m_SQLInicial & m_Where
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_IDAccionRealizada = .Fields("IDAccionRealizada")
            m_CodigoNoConformidad = .Fields("CodigoNoConformidad")
            m_AccionCorrectiva = .Fields("AccionCorrectiva")
            m_AccionRealizada = .Fields("AccionRealizada")
            m_FechaInicio = .Fields("FechaInicio")
            m_FechaFinPrevista = .Fields("FechaFinPrevista")
            m_DiasParaCaducar = .Fields("DiasParaCaducar")
            m_RespCalidad = .Fields("Nombre")
            m_Nemotecnico = .Fields("Nemotecnico")
            m_Resto = m_CodigoNoConformidad & "|" & m_AccionCorrectiva & "|" & m_AccionRealizada & "|" & m_FechaInicio & _
                                        "|" & m_FechaFinPrevista & "|" & m_DiasParaCaducar & "|" & m_RespCalidad & _
                                        "|" & m_Nemotecnico
            getColARAPC.Add m_IDAccionRealizada, m_Resto
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function

Public Function getColUsuariosARsAPC()
    
    Dim rcdDatos
    
    Dim m_SQL
    Dim m_SQLInicial
    Dim m_RESPONSABLETELEFONICA
    
    
    
    Set getColUsuariosARsAPC = CreateObject("Scripting.Dictionary")
    m_SQLInicial = "SELECT TbNoConformidades.RESPONSABLETELEFONICA " & _
                    "FROM (TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas " & _
                    "ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) " & _
                    "ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad) LEFT JOIN TbNCARAvisos " & _
                    "ON TbNCAccionesRealizadas.IDAccionRealizada = TbNCARAvisos.IDAR "
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    'los de <=0 sin correo previo
    
    m_SQL = m_SQLInicial & _
                "WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) " & _
                "And ((DateDiff('d', NOw(), [FechaFinPrevista])) <= 0) " & _
                "And ((TbNCARAvisos.IDCorreo0) Is Null)) " & _
                "GROUP BY TbNoConformidades.RESPONSABLETELEFONICA " & _
                "HAVING ((Not (TbNoConformidades.RESPONSABLETELEFONICA) Is Null));"
    
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If Not .EOF Then
           Do While Not .EOF
            m_RESPONSABLETELEFONICA = .Fields("RESPONSABLETELEFONICA")
                If Not getColUsuariosARsAPC.Exists(m_RESPONSABLETELEFONICA) Then
                    getColUsuariosARsAPC.Add m_RESPONSABLETELEFONICA, m_RESPONSABLETELEFONICA
                End If
                .MoveNext
            Loop
        End If
        
        
       
    End With
    rcdDatos.Close
    'los entre 7 y 1 sin correo previo
    
    m_SQL = m_SQLInicial & _
                "WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) " & _
                "AND ((DateDiff('d',Now(),[FechaFinPrevista]))>0 And (DateDiff('d',Now(),[FechaFinPrevista]))<8) " & _
                "AND ((TbNCARAvisos.IDCorreo7) Is Null)) " & _
                "GROUP BY TbNoConformidades.RESPONSABLETELEFONICA " & _
                "HAVING ((Not (TbNoConformidades.RESPONSABLETELEFONICA) Is Null));"
    
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If Not .EOF Then
             Do While Not .EOF
                m_RESPONSABLETELEFONICA = .Fields("RESPONSABLETELEFONICA")
                If Not getColUsuariosARsAPC.Exists(m_RESPONSABLETELEFONICA) Then
                    getColUsuariosARsAPC.Add m_RESPONSABLETELEFONICA, m_RESPONSABLETELEFONICA
                End If
                .MoveNext
            Loop
        End If
        
       
       
    End With
    rcdDatos.Close
    'los entre 15 y 8 sin correo previo
    
    m_SQL = m_SQLInicial & _
                "WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) " & _
                "AND ((DateDiff('d',Now(),[FechaFinPrevista]))>7 And (DateDiff('d',Now(),[FechaFinPrevista]))<16) " & _
                "AND ((TbNCARAvisos.IDCorreo15) Is Null)) " & _
                "GROUP BY TbNoConformidades.RESPONSABLETELEFONICA " & _
                "HAVING ((Not (TbNoConformidades.RESPONSABLETELEFONICA) Is Null));"
    
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If Not .EOF Then
            Do While Not .EOF
                m_RESPONSABLETELEFONICA = .Fields("RESPONSABLETELEFONICA")
                If Not getColUsuariosARsAPC.Exists(m_RESPONSABLETELEFONICA) Then
                    getColUsuariosARsAPC.Add m_RESPONSABLETELEFONICA, m_RESPONSABLETELEFONICA
                End If
                .MoveNext
            Loop
        End If
        
        
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function

Public Function getColUsuariosNCCaducados()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_RESPONSABLETELEFONICA
    
    
    
    Set getColUsuariosNCCaducados = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbNoConformidades.RESPONSABLETELEFONICA " & _
            "FROM TbNoConformidades " & _
            "WHERE (((TbNoConformidades.FECHACIERRE) Is Null) " & _
            "AND ((DateDiff('d',Now(),[FPREVCIERRE])) <0) AND ((TbNoConformidades.Borrado)=False));"
     
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            Exit Function
        End If
        
        Do While Not .EOF
            
            m_RESPONSABLETELEFONICA = .Fields("RESPONSABLETELEFONICA")
            If Not getColUsuariosNCCaducados.Exists(m_RESPONSABLETELEFONICA) Then
                getColUsuariosNCCaducados.Add m_RESPONSABLETELEFONICA, m_RESPONSABLETELEFONICA
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function

Public Function getColUsuariosNCRequierenReplanificacion()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_RESPONSABLETELEFONICA
    
    
    
    Set getColUsuariosNCRequierenReplanificacion = CreateObject("Scripting.Dictionary")
    m_SQL = "SELECT DISTINCT TbUsuariosAplicaciones.UsuarioRed AS Tecnico " & _
            "FROM ((TbNoConformidades LEFT JOIN TbUsuariosAplicaciones " & _
            "ON TbNoConformidades.RESPONSABLETELEFONICA = TbUsuariosAplicaciones.UsuarioRed) " & _
            "LEFT JOIN TbUsuariosAplicaciones AS TbUsuariosAplicaciones_1 " & _
            "ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones_1.UsuarioRed) " & _
            "RIGHT JOIN (TbNCAccionCorrectivas RIGHT JOIN TbNCAccionesRealizadas " & _
            "ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) " & _
            "ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad " & _
            "WHERE (((TbNoConformidades.FECHACIERRE) Is Null) And ((TbNoConformidades.Borrado) = False) " & _
            "And ((TbNCAccionesRealizadas.FechaFinPrevista) < now()) " & _
            "And ((TbNCAccionesRealizadas.FechaFinReal) Is Null));"
     
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            Exit Function
        End If
        
        Do While Not .EOF
            
            m_RESPONSABLETELEFONICA = .Fields("Tecnico")
            If Not getColUsuariosNCRequierenReplanificacion.Exists(m_RESPONSABLETELEFONICA) Then
                getColUsuariosNCRequierenReplanificacion.Add m_RESPONSABLETELEFONICA, m_RESPONSABLETELEFONICA
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function



Public Function getColARsParaReplanificar()
    
    Dim rcdDatos
    
    Dim m_SQL
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_Accion
    Dim m_Tarea
    Dim m_RESPONSABLECALIDAD
    Dim m_RESPONSABLETELEFONICA
    Dim m_FechaFinPrevista
    Dim m_Dias
    
    
    
    Set getColARsParaReplanificar = CreateObject("Scripting.Dictionary")
     m_SQL = "SELECT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, TbNCAccionCorrectivas.AccionCorrectiva AS Accion, " & _
            "TbNCAccionesRealizadas.AccionRealizada AS Tarea, TbUsuariosAplicaciones.Nombre AS Tecnico, " & _
            "TbNoConformidades.RESPONSABLECALIDAD, TbNCAccionesRealizadas.FechaFinPrevista,  " & _
            "DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]) AS Dias " & _
            "FROM (TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas " & _
            "ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) " & _
            "ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad) LEFT JOIN TbUsuariosAplicaciones " & _
            "ON TbNCAccionesRealizadas.Responsable = TbUsuariosAplicaciones.UsuarioRed " & _
            "WHERE (((DateDiff('d',Now(),[TbNCAccionesRealizadas].[FechaFinPrevista]))<16) " & _
            "AND ((TbNCAccionesRealizadas.FechaFinReal) Is Null));"
    
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_Nemotecnico = .Fields("Nemotecnico")
            m_CodigoNoConformidad = .Fields("CodigoNoConformidad")
            m_Accion = .Fields("Accion")
            m_Tarea = .Fields("Tarea")
            m_RESPONSABLECALIDAD = .Fields("RESPONSABLECALIDAD")
            m_RESPONSABLETELEFONICA = .Fields("Tecnico")
            m_FechaFinPrevista = .Fields("FechaFinPrevista")
            m_Dias = .Fields("Dias")
            
            
            
            If Not getColARsParaReplanificar.Exists(m_CodigoNoConformidad) Then
                getColARsParaReplanificar.Add m_CodigoNoConformidad, m_Nemotecnico & "|" & m_Accion & "|" & _
                                        m_Tarea & "|" & m_RESPONSABLECALIDAD & "|" & _
                                        m_RESPONSABLETELEFONICA & "|" & m_FechaFinPrevista & "|" & m_Dias
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function



Public Function HTMLARsPendientesDeReplanificacion(p_Col)
    
    
    Dim m_mensaje
    Dim m_Resto
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_Accion
    Dim m_Tarea
    Dim m_RESPONSABLECALIDAD
    Dim m_RESPONSABLETELEFONICA
    Dim m_FechaFinPrevista
    Dim m_Dias
   
    Dim dato
    
    If p_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='8' class=""ColespanArriba""> TAREAS QUE REQUIEREN REPLANIFICACIÓN </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > NEMOTÉCNICO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > CÓDIGO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > ACCIÓIN</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > TAREA</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > TÉCNICO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > RESP. CALIDAD</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.PREV.FIN</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > DÍAS CADUCADO</td>" & vbNewLine
           
            
            
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_CodigoNoConformidad In p_Col
            m_Resto = p_Col(m_CodigoNoConformidad)
            dato = Split(m_Resto, "|")
            m_Nemotecnico = dato(0)
            m_Accion = dato(1)
            m_Tarea = dato(2)
            m_RESPONSABLECALIDAD = dato(3)
            m_RESPONSABLETELEFONICA = dato(4)
            m_FechaFinPrevista = dato(5)
            m_Dias = dato(6)
            
             m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoNoConformidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Accion & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Tarea & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLETELEFONICA & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FechaFinPrevista & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Dias & "</td>" & vbNewLine
                
                
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
        
    
    HTMLARsPendientesDeReplanificacion = m_mensaje
End Function
Public Function RealizarTareaCalidad()
    
    Dim m_mensaje
    Dim m_HTMLTablaNCAPtoCaducarOCaducadas
    Dim m_HTMLTablaNCResueltasPteCE
    Dim m_HTMLTablaNCRegistradas 'sin acciones
    Dim m_HTMLARsPendientesDeReplanificacion
    
    Dim m_Titulo
    Dim m_HTMLCabecera
    Dim m_ColNCAPtoCaducarOCaducadas
    Dim m_ColNCResueltasPteCE
    Dim m_ColNCRegistradas
    Dim m_ColARsPendientesDeReplanificacion
    Dim m_NReplanificaciones
    Dim m_NCerradas
    Dim m_NAbiertas
    
    
    
    m_Titulo = "INFORME DE AVISOS DE NO CONFORMIDADES"
    m_HTMLCabecera = DameCabeceraHTML(m_Titulo)
    
    Set m_ColNCAPtoCaducarOCaducadas = getColNCAPtoCaducarOCaducadas()
    If m_ColNCAPtoCaducarOCaducadas.Count > 0 Then
        m_HTMLTablaNCAPtoCaducarOCaducadas = HTMLTablaNCAPtoCaducarOCaducadas(m_ColNCAPtoCaducarOCaducadas)
    End If
    Set m_ColNCResueltasPteCE = getColNCResueltasPteCE()
    If m_ColNCResueltasPteCE.Count > 0 Then
        m_HTMLTablaNCResueltasPteCE = HTMLTablaNCResueltasPteCE(m_ColNCResueltasPteCE)
    End If
    Set m_ColNCRegistradas = getColNCRegistradas()
    If m_ColNCRegistradas.Count > 0 Then
        m_HTMLTablaNCRegistradas = HTMLTablaNCRegistradas(m_ColNCRegistradas)
    End If
    Set m_ColARsPendientesDeReplanificacion = getColARsParaReplanificar()
    If m_ColARsPendientesDeReplanificacion.Count > 0 Then
        m_HTMLARsPendientesDeReplanificacion = HTMLARsPendientesDeReplanificacion(m_ColARsPendientesDeReplanificacion)
    End If
    
    If m_ColNCAPtoCaducarOCaducadas.Count = 0 And _
        m_ColNCResueltasPteCE.Count = 0 And _
        m_ColNCResueltasPteCE.Count = 0 And _
        m_ColARsPendientesDeReplanificacion.Count = 0 Then
        RegistrarTareaCalidad
        Exit Function
    End If
    m_NReplanificaciones = getNReplanificaciones
    m_NCerradas = getNCerradas
    m_NAbiertas = getNCAbiertas
    m_mensaje = m_HTMLCabecera & vbNewLine
    m_mensaje = m_mensaje & "<STRONG>" & m_Titulo & "</STRONG>" & vbNewLine
    
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    m_mensaje = m_mensaje & HTMLIndicadoresCalidad(m_NReplanificaciones, m_NCerradas, m_NAbiertas) & vbNewLine
    m_mensaje = m_mensaje & "<br>" & vbNewLine
    If m_ColNCAPtoCaducarOCaducadas.Count > 0 Then
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMLTablaNCAPtoCaducarOCaducadas & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    
    If m_ColNCResueltasPteCE.Count > 0 Then
        m_mensaje = m_mensaje & "<p></p>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMLTablaNCResueltasPteCE & vbNewLine
        m_mensaje = m_mensaje & "<p></p>" & vbNewLine
    End If
    If m_ColNCRegistradas.Count > 0 Then
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMLTablaNCRegistradas & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    If m_ColARsPendientesDeReplanificacion.Count > 0 Then
        m_mensaje = m_mensaje & "<br>" & vbNewLine
        m_mensaje = m_mensaje & m_HTMLARsPendientesDeReplanificacion & vbNewLine
        m_mensaje = m_mensaje & "<br>" & vbNewLine
    End If
    
    m_mensaje = m_mensaje & "</body>" & vbNewLine
    m_mensaje = m_mensaje & "</html>" & vbNewLine
    
    
    
    RegistrarCorreo "Informe Tareas No Conformidades (No Conformidades)", m_mensaje, m_CadenaCorreoCalidad
    RegistrarTareaCalidad
End Function
Public Function HTMLTablaNCAPtoCaducarOCaducadas(p_Col)
    
    Dim dato
    
    Dim m_NC
    Dim m_mensaje
    Dim m_Resto
    
    
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_DESCRIPCION
    Dim m_RESPONSABLECALIDAD
    Dim m_FECHAAPERTURA
    Dim m_FPREVCIERRE
    Dim m_DiasParaCierre
    
    
    If p_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='7' class=""ColespanArriba""> NO CONFORMIDADES PRÓXIMAS A CADUCAR en 15 DÍAS </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > NEMOTÉCNICO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > CÓDIGO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > DESCRIPCIÓN</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > RESP.CALIDAD</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.APERTURA</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.Prev. Cierre</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > Días para el cierre</td>" & vbNewLine
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_NC In p_Col
            m_Resto = p_Col(m_NC)
            dato = Split(m_Resto, "|")
            m_CodigoNoConformidad = m_NC
            m_Nemotecnico = dato(0)
            m_CodigoNoConformidad = m_NC
            m_DESCRIPCION = dato(1)
            m_RESPONSABLECALIDAD = dato(2)
            m_FECHAAPERTURA = dato(3)
            m_FPREVCIERRE = dato(4)
            m_DiasParaCierre = dato(5)
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoNoConformidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_DESCRIPCION & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FECHAAPERTURA & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FPREVCIERRE & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_DiasParaCierre & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaNCAPtoCaducarOCaducadas = m_mensaje
    
End Function
Public Function HTMLTablaNCRegistradas(p_Col)
    
    Dim dato
    
    Dim m_NC
    Dim m_mensaje
    Dim m_Resto
    
    
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_DESCRIPCION
    Dim m_RESPONSABLECALIDAD
    Dim m_FECHAAPERTURA
    Dim m_FPREVCIERRE
    
    
    
    If p_Col.Count = 0 Then
        Exit Function
    End If
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> NO CONFORMIDADES REGISTRADAS (Sin Acciones) </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > NEMOTÉCNICO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > CÓDIGO</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > DESCRIPCIÓN</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > RESP.CALIDAD</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.APERTURA</td>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > F.Prev. Cierre</td>" & vbNewLine
            
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        For Each m_NC In p_Col
            m_Resto = p_Col(m_NC)
            dato = Split(m_Resto, "|")
            m_CodigoNoConformidad = m_NC
            m_Nemotecnico = dato(0)
            
            m_DESCRIPCION = dato(1)
            m_RESPONSABLECALIDAD = dato(2)
            m_FECHAAPERTURA = dato(3)
            m_FPREVCIERRE = dato(4)
            
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoNoConformidad & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_DESCRIPCION & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FECHAAPERTURA & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FPREVCIERRE & "</td>" & vbNewLine
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaNCRegistradas = m_mensaje
    
End Function
Public Function RealizarTareaTecnicos()
    'la tarea consiste en mandar tres tipos de correos
    '1) Aquellos que la acción a realizar ya está caducada y no se haya enviado antes
    '2) Aquellos en que la acción a realizar le quede entre 7 y 0 días y no haya sido enviado antes
    '3) Aquellos en que la acción a realizar le quede entre 15 y 7 días y no haya sido enviado antes
    ' se ha de agrupar por técnico
    
    Dim m_ColUsuariosARsAPC '-->Entre 15 y negativos
    Dim m_ColARAPC15
    Dim m_ColARAPC7
    Dim m_ColARAPC0
    Dim m_Tecnico
    Dim m_CorreoTecnico
    Dim m_CorreoRespCalidad
    Dim m_mensaje
    
    Dim m_HTMLTablaARsAPC15
    Dim m_HTMLTablaARsAPC7
    Dim m_HTMLTablaARsAPC0
    
    
    Dim m_Titulo
    Dim m_HTMLCabecera
    Dim m_IDCorreo
    
    Set m_ColUsuariosARsAPC = getColUsuariosARsAPC()
    
    
    If m_ColUsuariosARsAPC.Count = 0 Then
        Exit Function
    End If
    
    For Each m_Tecnico In m_ColUsuariosARsAPC
        m_CorreoTecnico = getCorreo(m_Tecnico)
        
         m_Titulo = "INFORME DE AVISOS DE NO CONFORMIDADES"
         m_HTMLCabecera = DameCabeceraHTML(m_Titulo)
         m_mensaje = m_HTMLCabecera & vbNewLine
         m_mensaje = m_mensaje & m_Titulo & vbNewLine
         m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
         
         Set m_ColARAPC15 = getColARAPC(m_Tecnico, "15")
         If m_ColARAPC15.Count > 0 Then
             m_HTMLTablaARsAPC15 = HTMLTablaARAPC(m_ColARAPC15, "15")
             m_mensaje = m_mensaje & m_HTMLTablaARsAPC15 & vbNewLine
             m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
         End If
         
         Set m_ColARAPC7 = getColARAPC(m_Tecnico, "7")
         If m_ColARAPC7.Count > 0 Then
             m_HTMLTablaARsAPC7 = HTMLTablaARAPC(m_ColARAPC7, "7")
             m_mensaje = m_mensaje & m_HTMLTablaARsAPC7 & vbNewLine
             m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
         End If
         Set m_ColARAPC0 = getColARAPC(m_Tecnico, "0")
         If m_ColARAPC0.Count > 0 Then
             m_HTMLTablaARsAPC0 = HTMLTablaARAPC(m_ColARAPC0, "0")
             m_mensaje = m_mensaje & m_HTMLTablaARsAPC0 & vbNewLine
             m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
         End If
         If m_ColARAPC7.Count > 0 Or m_ColARAPC0.Count > 0 Then
            m_CorreoRespCalidad = getCorreosCalidad(m_ColARAPC7, m_ColARAPC0)
         Else
            m_CorreoRespCalidad = ""
         End If
         m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
         m_mensaje = m_mensaje & "<p><strong> Por favor, hable con el responsable de Calidad para replanificar las tareas lo antes posible.</strong> </p>" & vbNewLine
         m_mensaje = m_mensaje & "</body>" & vbNewLine
         m_mensaje = m_mensaje & "</html>" & vbNewLine
         m_IDCorreo = RegistrarCorreoTareaTecnica("Tareas de Acciones Correctivas a punto de caducar o caducadas (No Conformidades)", _
         m_mensaje, m_CorreoTecnico, m_CorreoRespCalidad)
         If m_IDCorreo <> "" Then
            MarcarCorreoEnviadoEnAR m_IDCorreo, m_ColARAPC15, m_ColARAPC7, m_ColARAPC0
         End If
    Next
    RegistrarTareaTecnica
    
    
End Function
Public Function getCorreo(p_Usuario)
    
    Dim rcdDatos
    Dim m_SQL
    
     m_SQL = "SELECT TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM TbUsuariosAplicaciones " & _
            "WHERE (((TbUsuariosAplicaciones.UsuarioRed)='" & p_Usuario & "'));"
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            getCorreo = ""
            Exit Function
        End If
        getCorreo = .Fields("CorreoUsuario")
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
End Function
Public Function getCorreoCalidad(p_NC)
    
    Dim rcdDatos
    Dim m_SQL
    
     m_SQL = "SELECT TbUsuariosAplicaciones.CorreoUsuario " & _
            "FROM TbNoConformidades LEFT JOIN TbUsuariosAplicaciones " & _
            "ON TbNoConformidades.RESPONSABLECALIDAD = TbUsuariosAplicaciones.UsuarioRed " & _
            "WHERE (((TbNoConformidades.CodigoNoConformidad)='" & p_NC & "'));"
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            getCorreoCalidad = ""
            Exit Function
        End If
        getCorreoCalidad = .Fields("CorreoUsuario")
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
End Function
Public Function getCorreosCalidad(p_ColARs7, p_ColARs0)
    
    Dim m_Resto
    Dim m_ID
    Dim dato
    Dim m_NC
    Dim m_Correo
    Dim m_Col
    Dim m_Cadena
    
    Set m_Col = CreateObject("Scripting.Dictionary")
    If p_ColARs7.Count > 0 Then
        For Each m_ID In p_ColARs7
            m_Resto = p_ColARs7(m_ID)
            dato = Split(m_Resto, "|")
            m_NC = dato(0)
            m_Correo = getCorreoCalidad(m_NC)
            If m_Correo <> "" Then
                If Not m_Col.Exists(m_Correo) Then
                    m_Col.Add m_Correo, m_Correo
                End If
            End If
        Next
    End If
    If p_ColARs0.Count > 0 Then
        For Each m_ID In p_ColARs0
            m_Resto = p_ColARs0(m_ID)
            dato = Split(m_Resto, "|")
            m_NC = dato(0)
            m_Correo = getCorreoCalidad(m_NC)
            If m_Correo <> "" Then
                If Not m_Col.Exists(m_Correo) Then
                    m_Col.Add m_Correo, m_Correo
                End If
            End If
        Next
    End If
    If m_Col.Count = 0 Then
        m_Cadena = ""
    Else
        For Each m_Correo In m_Col
            If m_Cadena = "" Then
                m_Cadena = m_Correo
            Else
                m_Cadena = m_Cadena & ";" & m_Correo
            End If
        Next
        
    End If
    getCorreosCalidad = m_Cadena
End Function


Public Function EsDiaEntreSemana()
    
    If Weekday(Date) = 1 Or Weekday(Date) = 7 Then
        EsDiaEntreSemana = False
    Else
        EsDiaEntreSemana = True
    End If
    
    
End Function
Public Function getColusuariosCalidadParaExcluir(p_ColUsuariosCalidad)
    Dim m_Registro
    Dim dato
    Set getColusuariosCalidadParaExcluir = CreateObject("Scripting.Dictionary")
    If p_ColUsuariosCalidad.Count = 0 Then
        Exit Function
    End If
    For Each m_Registro In p_ColUsuariosCalidad
        dato = Split(m_Registro, "|")
        getColusuariosCalidadParaExcluir.Add dato(0), dato(0)
    Next
End Function
Public Function getNReplanificaciones()
    
    Dim rcdDatos
    Dim m_Cuenta
    Dim m_SQL
    
   
    m_SQL = "SELECT Count(TbReplanificacionesProyecto.IDReplanificacion) AS Cuenta " & _
            "FROM TbReplanificacionesProyecto " & _
            "WHERE (((DateDiff('d',[FechaReprogramacion],Now())) Between 0 And 30));"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            getNReplanificaciones = 0
            
            Exit Function
        End If
        m_Cuenta = .Fields("Cuenta")
        If Not IsNumeric(m_Cuenta) Then
            m_Cuenta = 0
        End If
        
        
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    getNReplanificaciones = m_Cuenta
    
End Function

Public Function getNCerradas()
    
    Dim rcdDatos
    Dim m_Cuenta
    Dim m_SQL
    
   
    m_SQL = "SELECT Count(TbNoConformidades.IDNoConformidad) AS Cuenta " & _
            "FROM TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas " & _
            "ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) " & _
            "ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad " & _
            "WHERE ((Not (TbNCAccionesRealizadas.FechaFinReal) Is Null) AND ((DateDiff('d',[FECHACIERRE],Now())) Between 0 And 30));"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            getNCerradas = 0
            
            Exit Function
        End If
        m_Cuenta = .Fields("Cuenta")
        If Not IsNumeric(m_Cuenta) Then
            m_Cuenta = 0
        End If
        
        
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    getNCerradas = m_Cuenta
    
End Function
Public Function getNCAbiertas()
    
    Dim rcdDatos
    Dim m_Cuenta
    Dim m_SQL
    
   
    m_SQL = "SELECT Count(TbNoConformidades.IDNoConformidad) AS Cuenta " & _
            "FROM TbNoConformidades " & _
            "WHERE (((DateDiff('d',[FECHAAPERTURA],Now())) Between 0 And 30)) " & _
            "ORDER BY Count(TbNoConformidades.IDNoConformidad) DESC;"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            getNCAbiertas = 0
            
            Exit Function
        End If
        m_Cuenta = .Fields("Cuenta")
        If Not IsNumeric(m_Cuenta) Then
            m_Cuenta = 0
        End If
        
        
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    getNCAbiertas = m_Cuenta
    
End Function
Public Function Lanzar()
    
    
    
    Dim m_RequiereTareaTecnica
    Dim m_RequiereTareaCalidad
    If Not EsDiaEntreSemana() Then
        Exit Function
    End If
    
    m_IDAplicacion = 8
    m_DiasNecesariosParaTecnicos = 1
    
    m_URLBBDDTareas = "\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb"
    Set CnTareas = Conn(m_URLBBDDTareas, m_Pass)
    m_RequiereTareaTecnica = RequiereTareaTecnica()
    m_RequiereTareaCalidad = RequiereTareaCalidad()
    If m_RequiereTareaTecnica = False And m_RequiereTareaCalidad = False Then
        
        CnTareas.Close
        Set CnTareas = Nothing
        Exit Function
    End If
    m_URLBBDDNC = "\\datoste\aplicaciones_dys\Aplicaciones PpD\No Conformidades\NoConformidades_Datos.accdb"
    If m_RequiereTareaTecnica = True Or m_RequiereTareaCalidad Then
        Set CnNC = Conn(m_URLBBDDNC, m_Pass)
        CSS = getCSS
        Set ColUsuariosCalidad = getColusuariosTareas("Calidad")
        Set ColUsuariosCalidadParaExcluir = getColusuariosCalidadParaExcluir(ColUsuariosCalidad)
        Set ColUsuariosAdministradores = getColusuariosTareas("Administrador")
        m_CadenaCorreoAdministradores = getCadenaCorreoAdministradores()
        m_CadenaCorreoCalidad = getCadenaCorreoCalidad()
    End If
    If m_RequiereTareaTecnica Then
        RealizarTareaTecnicos
    End If
    If m_RequiereTareaCalidad Then
        RealizarTareaCalidad
    End If
    
    CnNC.Close
    Set CnNC = Nothing
    CnTareas.Close
    Set CnTareas = Nothing
    
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

Public Function getColNCAPtoCaducarOCaducadas()
    
    Dim rcdDatos
    
    Dim m_SQL
    Dim m_Resto
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_DESCRIPCION
    Dim m_RESPONSABLECALIDAD
    Dim m_FECHAAPERTURA
    Dim m_FPREVCIERRE
    Dim m_DiasParaCierre
    
    
    
   Set getColNCAPtoCaducarOCaducadas = CreateObject("Scripting.Dictionary")
    '---------------------------------
    ' Tabla registros a punto de caducar
    '---------------------------------
    m_SQL = "SELECT distinct DateDiff('d',Now(),[FPREVCIERRE]) AS DiasParaCierre, " & _
                "TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, " & _
                "TbNoConformidades.DESCRIPCION, TbNoConformidades.RESPONSABLECALIDAD, " & _
                "TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE " & _
                "FROM TbNoConformidades INNER JOIN (TbNCAccionCorrectivas INNER JOIN TbNCAccionesRealizadas " & _
                "ON TbNCAccionCorrectivas.IDAccionCorrectiva = TbNCAccionesRealizadas.IDAccionCorrectiva) " & _
                "ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad " & _
                "WHERE (((TbNCAccionesRealizadas.FechaFinReal) Is Null) AND ((DateDiff('d',Now(),[FPREVCIERRE])) <16));"
     
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_Nemotecnico = .Fields("Nemotecnico")
            m_CodigoNoConformidad = .Fields("CodigoNoConformidad")
            m_DESCRIPCION = .Fields("DESCRIPCION")
            m_RESPONSABLECALIDAD = .Fields("RESPONSABLECALIDAD")
            
            m_FECHAAPERTURA = .Fields("FECHAAPERTURA")
            If IsDate(m_FECHAAPERTURA) Then
                m_FECHAAPERTURA = Day(m_FECHAAPERTURA) & "/" & Month(m_FECHAAPERTURA) & "/" & Year(m_FECHAAPERTURA)
            End If
            m_FPREVCIERRE = .Fields("FPREVCIERRE")
            If IsDate(m_FPREVCIERRE) Then
                m_FPREVCIERRE = Day(m_FPREVCIERRE) & "/" & Month(m_FPREVCIERRE) & "/" & Year(m_FPREVCIERRE)
            End If
            m_DiasParaCierre = .Fields("DiasParaCierre")
           
            If m_Nemotecnico = "" Then m_Nemotecnico = "&nbsp;"
            If m_DESCRIPCION = "" Then m_DESCRIPCION = "&nbsp;"
            If m_RESPONSABLECALIDAD = "" Then m_RESPONSABLECALIDAD = "&nbsp;"
            If m_FECHAAPERTURA = "" Then m_FECHAAPERTURA = "&nbsp;"
            If m_FPREVCIERRE = "" Then m_FPREVCIERRE = "&nbsp;"
            If m_DiasParaCierre = "" Then m_DiasParaCierre = "&nbsp;"
            
            
            If Not getColNCAPtoCaducarOCaducadas.Exists(m_CodigoNoConformidad) Then
                getColNCAPtoCaducarOCaducadas.Add m_CodigoNoConformidad, _
                    m_Nemotecnico & "|" & m_DESCRIPCION & "|" & m_RESPONSABLECALIDAD & "|" & m_FECHAAPERTURA & "|" & m_FPREVCIERRE & "|" & m_DiasParaCierre
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function

Public Function getColNCRegistradas()
    
    Dim rcdDatos
    
    Dim m_SQL
    Dim m_Resto
    Dim m_Nemotecnico
    Dim m_CodigoNoConformidad
    Dim m_DESCRIPCION
    Dim m_RESPONSABLECALIDAD
    Dim m_FECHAAPERTURA
    Dim m_FPREVCIERRE
    
    
    
    
   Set getColNCRegistradas = CreateObject("Scripting.Dictionary")
    '---------------------------------
    ' Tabla registros que no tienen acciones
    '---------------------------------
    m_SQL = "SELECT DISTINCT TbNoConformidades.CodigoNoConformidad, TbNoConformidades.Nemotecnico, TbNoConformidades.DESCRIPCION, " & _
            "TbNoConformidades.RESPONSABLECALIDAD, TbNoConformidades.FECHAAPERTURA, TbNoConformidades.FPREVCIERRE " & _
            "FROM TbNoConformidades LEFT JOIN TbNCAccionCorrectivas ON TbNoConformidades.IDNoConformidad = TbNCAccionCorrectivas.IDNoConformidad " & _
            "WHERE (((TbNCAccionCorrectivas.IDNoConformidad) Is Null));"
     
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnNC, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_Nemotecnico = .Fields("Nemotecnico")
            m_CodigoNoConformidad = .Fields("CodigoNoConformidad")
            m_DESCRIPCION = .Fields("DESCRIPCION")
            m_RESPONSABLECALIDAD = .Fields("RESPONSABLECALIDAD")
            
            m_FECHAAPERTURA = .Fields("FECHAAPERTURA")
            If IsDate(m_FECHAAPERTURA) Then
                m_FECHAAPERTURA = Day(m_FECHAAPERTURA) & "/" & Month(m_FECHAAPERTURA) & "/" & Year(m_FECHAAPERTURA)
            End If
            m_FPREVCIERRE = .Fields("FPREVCIERRE")
            
            
            
            If Not getColNCRegistradas.Exists(m_CodigoNoConformidad) Then
                getColNCRegistradas.Add m_CodigoNoConformidad, _
                    m_Nemotecnico & "|" & m_DESCRIPCION & "|" & m_RESPONSABLECALIDAD & "|" & m_FECHAAPERTURA & "|" & m_FPREVCIERRE
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function




Lanzar







