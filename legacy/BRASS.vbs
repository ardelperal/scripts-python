
Option Explicit


Dim ColUsuariosAdministradores
Dim m_CadenaCorreoAdministradores


Dim m_URLBBBRASS
Dim CnBrass
Dim m_URLBBDDTareas
Dim CnTareas

Const m_Pass = "dpddpd"

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



Public Function UltimaEjecucion()
    
    Dim rcdDatos
    Dim m_SQL
    
    m_SQL = "SELECT Last(TbTareas.Fecha) AS Ultima " & _
            "FROM TbTareas " & _
            "WHERE Tarea='BRASSDiario' AND Realizado='Sí';"
    
    
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

Public Function TareaRealizada()
    
    
    Dim m_FechaUltimaEjecucion
    Dim m_FechaHoy
    
    
    m_FechaHoy = Date
    
    m_FechaUltimaEjecucion = UltimaEjecucion()
    If Not IsDate(m_FechaUltimaEjecucion) Then
        TareaRealizada = False
        Exit Function
    End If
    If CDate(m_FechaHoy) = CDate(m_FechaUltimaEjecucion) Then
        TareaRealizada = True
        
    Else
        TareaRealizada = False
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

Public Function RegistrarCorreo(p_Asunto, p_Cuerpo, p_Destinatarios)

    Dim rcdDatos
    Dim m_SQL
    Dim m_IDCorreo
    

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
            .Fields("Aplicacion") = "BRASS"
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

Public Function RegistrarTarea()
    'NCDiario
    
    Dim rcdDatos
    
    Dim m_SQL
    
    m_SQL = "SELECT * " & _
            "FROM TbTareas " & _
            "WHERE Tarea='BRASSDiario';"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            .AddNew
                .Fields("Tarea") = "BRASSDiario"
                .Fields("Fecha") = Date
                .Fields("Realizado") = "Sí"
            .Update
        Else
            '.Edit
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



Public Function HTMLTablaNecesitanCalibracion()
    
    Dim rcdDatos
    
    Dim m_SQL
    Dim m_SQLLimitante
    Dim m_mensaje
    Dim m_Resto
    Dim m_Nombre
    Dim m_NS
    Dim m_PN
    Dim m_Marca
    Dim m_Modelo
    Dim dato
    Dim m_EstadoCalibracionVigente
    Dim m_IDEquipoMedida
    
    
    m_SQL = "SELECT * " & _
            "FROM TbEquiposMedida " & _
            "WHERE FechaFinServicio Is Null;"
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnBrass, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
       
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            HTMLTablaNecesitanCalibracion = ""
            Exit Function
        End If
        .MoveFirst
        
        m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='5' class=""ColespanArriba""> EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""centrado"" > <strong>NOMBRE</strong></td>"
            m_mensaje = m_mensaje & "<td class=""centrado"" > <strong>NS</strong></td>"
            m_mensaje = m_mensaje & "<td class=""centrado"" > <strong>PN</strong></td>"
            m_mensaje = m_mensaje & "<td class=""centrado"" > <strong>MARCA</strong></td>"
            m_mensaje = m_mensaje & "<td class=""centrado"" > <strong>MODELO</strong></td>"
            
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Do While Not .EOF
            m_IDEquipoMedida = .Fields("IDEquipoMedida")
            m_EstadoCalibracionVigente = EstadoCalibracionVigente(m_IDEquipoMedida)
            If m_EstadoCalibracionVigente <> True Then
                 m_Nombre = .Fields("NOMBRE")
                m_NS = .Fields("NS")
                m_PN = .Fields("PN")
                m_Marca = .Fields("MARCA")
                m_Modelo = .Fields("MODELO")
                
                If m_Nombre = Empty Then m_Nombre = "&nbsp;"
                If m_NS = Empty Then m_NS = "&nbsp;"
                If m_PN = Empty Then m_PN = "&nbsp;"
                If m_Marca = Empty Then m_Marca = "&nbsp;"
                If m_Modelo = Empty Then m_Modelo = "&nbsp;"
                
                m_mensaje = m_mensaje & "<tr>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Nombre & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_NS & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_PN & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Marca & "</td>" & vbNewLine
                    m_mensaje = m_mensaje & "<td> " & m_Modelo & "</td>" & vbNewLine
                    
                m_mensaje = m_mensaje & "</tr>" & vbNewLine
            End If
           

            .MoveNext
        Loop
        m_mensaje = m_mensaje & "</table>" & vbNewLine
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    HTMLTablaNecesitanCalibracion = m_mensaje
    
End Function
Public Function EstadoCalibracionVigente(p_IDEquipoMedida)
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_FechaFinCalibracion
    
    m_SQL = "SELECT FechaFinCalibracion " & _
            "FROM TbEquiposMedidaCalibraciones " & _
            "WHERE IDEquipoMedida =" & p_IDEquipoMedida & " " & _
            "ORDER BY IDCalibracion DESC;"
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnBrass, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
       
        If .EOF Then
            EstadoCalibracionVigente = False
            Exit Function
        End If
        
        .MoveFirst
        
            m_FechaFinCalibracion = .Fields("FechaFinCalibracion")
            If Not IsDate(m_FechaFinCalibracion) Then
                EstadoCalibracionVigente = False
            Else
                If CDate(Date) < CDate(m_FechaFinCalibracion) Then
                    EstadoCalibracionVigente = True
                Else
                    EstadoCalibracionVigente = False
                End If
            End If
            
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
    
End Function

Public Function RealizarTarea()
    
    Dim m_mensaje
    Dim m_HTMLTablaNecesitanCalibracion
    
    Dim m_Titulo
    Dim m_HTMLCabecera
    
    
    m_Titulo = "INFORME DE AVISOS DE NO EQUIPOS DE MEDIDA FUERA DE CALIBRACIÓN"
    m_HTMLCabecera = DameCabeceraHTML(m_Titulo)
    
    m_HTMLTablaNecesitanCalibracion = HTMLTablaNecesitanCalibracion()
    If m_HTMLTablaNecesitanCalibracion = "" Then
        RegistrarTarea
        Exit Function
    End If
    m_mensaje = m_HTMLCabecera & vbNewLine
    m_mensaje = m_mensaje & m_Titulo & vbNewLine
    If m_HTMLTablaNecesitanCalibracion <> "" Then
        m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
        m_mensaje = m_mensaje & m_HTMLTablaNecesitanCalibracion & vbNewLine
    End If
    
    
    m_mensaje = m_mensaje & "</body>" & vbNewLine
    m_mensaje = m_mensaje & "</html>" & vbNewLine
    
    
   
    
    RegistrarCorreo "Informe Equipos de Medida fuera de calibración (BRASS)", m_mensaje, "felix.sanchezpimentel@telefonica.com"
    RegistrarTarea
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
        m_SQL = "SELECT TbUsuariosAplicaciones.UsuarioRed, TbUsuariosAplicaciones.Nombre, TbUsuariosAplicaciones.CorreoUsuario " & _
                "FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesTareas ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesTareas.CorreoUsuario " & _
                "WHERE (((TbUsuariosAplicaciones.ParaTareasProgramadas)=True) AND ((TbUsuariosAplicaciones.FechaBaja) Is Null) AND ((TbUsuariosAplicacionesTareas.EsCalidad)='Sí'));"
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

Public Function Lanzar()
    
    
    
    Dim m_TareaHecha
    m_URLBBDDTareas = "\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb"
    Set CnTareas = Conn(m_URLBBDDTareas, m_Pass)
    m_TareaHecha = TareaRealizada()
    If m_TareaHecha = False Then
        m_URLBBBRASS = "\\datoste\aplicaciones_dys\Aplicaciones PpD\BRASS\Gestion_Brass_Gestion_Datos.accdb"
        Set CnBrass = Conn(m_URLBBBRASS, m_Pass)
        CSS = getCSS
        
        Set ColUsuariosAdministradores = getColusuariosTareas("Administrador")
        m_CadenaCorreoAdministradores = getCadenaCorreoAdministradores()
        RealizarTarea
        
        CnBrass.Close
        Set CnBrass = Nothing
    End If
    CnTareas.Close
    Set CnTareas = Nothing
   
    
    
End Function


Lanzar



















