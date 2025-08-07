
Option Explicit

Dim m_CadenaCorreoAdministradores
Dim m_CadenaCorreoTramitadores


Const m_Pass = "dpddpd"
Dim m_URLBBDDTareas
Dim CnTareas
Dim m_URLBBDDEXP
Dim CnEXP
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

Public Function getCadenaCorreoTareas()

    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Correo
    Dim m_CadenaCorreo
    
    
    m_SQL = "SELECT TbUsuariosAplicaciones.CorreoUsuario " & _
                "FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesPermisos ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario " & _
                "WHERE IDAplicacion=19 " & _
                "AND EsUsuarioAdministrador='Sí';"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    If Not rcdDatos.EOF Then
        
        Do While Not rcdDatos.EOF
            m_Correo = rcdDatos.Fields("CorreoUsuario")
            If m_CadenaCorreo = Empty Then
                m_CadenaCorreo = m_Correo
            Else
                m_CadenaCorreo = m_CadenaCorreo & ";" & m_Correo
            End If
            
            rcdDatos.MoveNext
        Loop
        
    End If
    getCadenaCorreoTareas = m_CadenaCorreo
    rcdDatos.Close
    Set rcdDatos = Nothing
    
End Function

Public Function UltimaEjecucion()
    
    Dim rcdDatos
    Dim m_SQL
    
    m_SQL = "SELECT Last(TbTareas.Fecha) AS Ultima " & _
            "FROM TbTareas " & _
            "WHERE Tarea='ExpDiario' AND Realizado='Sí';"
    
    
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
    
    'm_CadenaCorreoAdministradores = ""
    'p_Destinatarios = "andres.romandelperal@telefonica.com"
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
            .Fields("Aplicacion") = "EXPEDIENTES"
            .Fields("Asunto") = p_Asunto
            .Fields("Cuerpo") = p_Cuerpo
            If InStr(1, p_Destinatarios, "@") <> 0 Then
                .Fields("Destinatarios") = p_Destinatarios
            End If
            If InStr(1, m_CadenaCorreoAdministradores, "@") <> 0 Then
                .Fields("DestinatariosConCopiaOculta") = m_CadenaCorreoAdministradores
            End If
            
            .Fields("FechaGrabacion") = Now()
        .Update
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
End Function

Public Function RegistrarTarea()
    'ExpDiario
    
    Dim rcdDatos
    
    Dim m_SQL
    
    m_SQL = "SELECT * " & _
            "FROM TbTareas " & _
            "WHERE Tarea='ExpDiario';"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            .AddNew
                .Fields("Tarea") = "ExpDiario"
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
Public Function HTMLTablaAdjudicadosTSOLSinCodS4H(p_Col)
    
    Dim dato
    
    Dim m_IDExpediente
    Dim m_mensaje
    Dim m_Resto
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_RESPONSABLECALIDAD
    Dim m_JURIDICA
    Dim m_FAdjudicacion
    Dim m_CodS4H
   
    
    
    
    
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='8' class=""ColespanArriba""> EXPEDIENTES TSOL ADJUDICADOS SIN CodS4H </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>IDExp</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>CÓDIGO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>NEMOTÉCNICO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>TÍTULO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>RESP. CALIDAD</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>JURÍDICA</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.ADJUDICACIÓN </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>CodS4H </strong></td>"
            
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        
        If p_Col.Count = 0 Then
            m_mensaje = m_mensaje & "</table>" & vbNewLine
            HTMLTablaAdjudicadosTSOLSinCodS4H = m_mensaje
            Exit Function
        End If
        For Each m_IDExpediente In p_Col
            m_Resto = p_Col(m_IDExpediente)
            dato = Split(m_Resto, "|")
            m_CodigoExp = dato(0)
            m_Nemotecnico = dato(1)
            m_TITULO = dato(2)
            m_RESPONSABLECALIDAD = dato(3)
            m_JURIDICA = dato(4)
            m_FAdjudicacion = dato(5)
            m_CodS4H = dato(6)
            
            If m_RESPONSABLECALIDAD = Empty Then m_RESPONSABLECALIDAD = "&nbsp;"
            If m_CodS4H = Empty Then m_CodS4H = "&nbsp;"
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_IDExpediente & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoExp & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_TITULO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_JURIDICA & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FAdjudicacion & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodS4H & "</td>" & vbNewLine
               
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaAdjudicadosTSOLSinCodS4H = m_mensaje
    
End Function

Public Function HTMLTablaAPuntoDeFinalizar(p_Col)
    
    Dim dato
    
    Dim m_IDExpediente
    Dim m_mensaje
    Dim m_Resto
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FINICIO
    Dim m_FFIN
    Dim m_FechaFinGarantia
    Dim m_GARANTIAMESES
    Dim m_FECHACERTIFICACION
    Dim m_DiasParaFin
    Dim m_RESPONSABLECALIDAD
    
    
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='11' class=""ColespanArriba""> EXPEDIENTES A PUNTO DE RECEPCIONAR/FINALIZAR </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>IDExp</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>CÓDIGO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>NEMOTÉCNICO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>TÍTULO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>RESP. CALIDAD</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.INICIO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.FIN </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.FIN GARANTÍA </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>MESES GARANTÍA </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.CERTIFICACIÓN </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>Días para el FIN</strong></td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        
        If p_Col.Count = 0 Then
            m_mensaje = m_mensaje & "</table>" & vbNewLine
            HTMLTablaAPuntoDeFinalizar = m_mensaje
            Exit Function
        End If
        For Each m_IDExpediente In p_Col
            m_Resto = p_Col(m_IDExpediente)
            dato = Split(m_Resto, "|")
            m_CodigoExp = dato(0)
            m_Nemotecnico = dato(1)
            m_TITULO = dato(2)
            m_FINICIO = dato(3)
            m_FFIN = dato(4)
            m_DiasParaFin = dato(5)
            m_FechaFinGarantia = dato(6)
            m_GARANTIAMESES = dato(7)
            m_FECHACERTIFICACION = dato(8)
            m_RESPONSABLECALIDAD = dato(9)
            If Not IsDate(m_FechaFinGarantia) Then
                m_FechaFinGarantia = "&nbsp;"
            End If
            If Not IsNumeric(m_GARANTIAMESES) Then
                m_GARANTIAMESES = "&nbsp;"
            End If
            If Not IsDate(m_FECHACERTIFICACION) Then
                m_FECHACERTIFICACION = "&nbsp;"
            End If
            If m_RESPONSABLECALIDAD = Empty Then m_RESPONSABLECALIDAD = "&nbsp;"
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_IDExpediente & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoExp & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_TITULO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FINICIO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FFIN & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FechaFinGarantia & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_GARANTIAMESES & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FECHACERTIFICACION & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_DiasParaFin & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaAPuntoDeFinalizar = m_mensaje
    
End Function
Public Function HTMLTablaHitosAPuntoDeFinalizar(p_Col)
    
    Dim dato
    
    Dim m_IDExpediente
    Dim m_mensaje
    Dim m_Resto
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FechaHito
    Dim m_DiasParaFin
    Dim m_Descripcion
    Dim m_RESPONSABLECALIDAD
    
    
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='8' class=""ColespanArriba""> HITOS DE EXPEDIENTES A PUNTO DE RECEPCIONAR </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>IDExp</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>CÓDIGO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>NEMOTÉCNICO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>TÍTULO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>RESP. CALIDAD</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>DESC.HITO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.HITO </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>Días para el FIN</strong></td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        
        If p_Col.Count = 0 Then
            m_mensaje = m_mensaje & "</table>" & vbNewLine
            HTMLTablaHitosAPuntoDeFinalizar = m_mensaje
            Exit Function
        End If
        For Each m_IDExpediente In p_Col
            m_Resto = p_Col(m_IDExpediente)
            dato = Split(m_Resto, "|")
            m_CodigoExp = dato(0)
            m_Nemotecnico = dato(1)
            m_TITULO = dato(2)
            m_FechaHito = dato(3)
            m_DiasParaFin = dato(4)
            m_Descripcion = dato(5)
            m_RESPONSABLECALIDAD = dato(6)
           
            If m_RESPONSABLECALIDAD = Empty Then m_RESPONSABLECALIDAD = "&nbsp;"
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_IDExpediente & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoExp & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_TITULO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Descripcion & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FechaHito & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_DiasParaFin & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaHitosAPuntoDeFinalizar = m_mensaje
    
End Function
Public Function HTMLTablaConEstadoDesconocido(p_Col)
    
    Dim dato
    
    Dim m_IDExpediente
    Dim m_mensaje
    Dim m_Resto
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FINICIO
    Dim m_FFIN
    Dim m_GARANTIAMESES
    Dim m_Estado
    Dim m_RESPONSABLECALIDAD
    
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='9' class=""ColespanArriba""> EXPEDIENTES CON ESTADO DESCONOCIDO </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>IDExp</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>CÓDIGO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>NEMOTÉCNICO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>TÍTULO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>RESP. CALIDAD</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.INICIO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.FIN </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>GARANTIAMESES </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>Estado</strong></td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        If p_Col.Count = 0 Then
            m_mensaje = m_mensaje & "</table>" & vbNewLine
            HTMLTablaConEstadoDesconocido = m_mensaje
            Exit Function
        End If
        For Each m_IDExpediente In p_Col
            m_Resto = p_Col(m_IDExpediente)
            dato = Split(m_Resto, "|")
            m_CodigoExp = dato(0)
            m_Nemotecnico = dato(1)
            m_TITULO = dato(2)
            m_FINICIO = dato(3)
            m_FFIN = dato(4)
            m_GARANTIAMESES = dato(5)
            m_Estado = dato(6)
            m_RESPONSABLECALIDAD = dato(7)
            
            If m_Nemotecnico = Empty Then m_Nemotecnico = "&nbsp;"
            If m_RESPONSABLECALIDAD = Empty Then m_RESPONSABLECALIDAD = "&nbsp;"
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_IDExpediente & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoExp & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_TITULO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FINICIO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FFIN & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_GARANTIAMESES & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Estado & "</td>" & vbNewLine
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaConEstadoDesconocido = m_mensaje
    
End Function
Public Function HTMLTablaAdjudicadosSinContrato(p_Col)
    
    Dim dato
    
    Dim m_IDExpediente
    Dim m_mensaje
    Dim m_Resto
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FINICIO
    Dim m_FFIN
    Dim m_FECHAADJUDICADO
    
    Dim m_RESPONSABLECALIDAD
    
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='8' class=""ColespanArriba""> EXPEDIENTES ADJUDICADOS SIN DATOS DE CONTRATO </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>IDExp</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>CÓDIGO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>NEMOTÉCNICO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>TÍTULO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>RESP. CALIDAD</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.INICIO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.FIN </strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.ADJUDICACIÓN </strong></td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        If p_Col.Count = 0 Then
            m_mensaje = m_mensaje & "</table>" & vbNewLine
            HTMLTablaAdjudicadosSinContrato = m_mensaje
            Exit Function
        End If
        For Each m_IDExpediente In p_Col
            m_Resto = p_Col(m_IDExpediente)
            dato = Split(m_Resto, "|")
            m_CodigoExp = dato(0)
            m_Nemotecnico = dato(1)
            m_TITULO = dato(2)
            m_FINICIO = dato(3)
            m_FFIN = dato(4)
            m_FECHAADJUDICADO = dato(5)
            m_RESPONSABLECALIDAD = dato(6)
            
            If m_RESPONSABLECALIDAD = Empty Then m_RESPONSABLECALIDAD = "&nbsp;"
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_IDExpediente & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoExp & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_TITULO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FINICIO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FFIN & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FECHAADJUDICADO & "</td>" & vbNewLine
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaAdjudicadosSinContrato = m_mensaje
    
End Function

Public Function HTMLTablaEnFaseOfertaPorMuchoTiempo(p_Col)
    
    Dim dato
    
    Dim m_IDExpediente
    Dim m_mensaje
    Dim m_Resto
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FECHAOFERTA
   
    
    Dim m_RESPONSABLECALIDAD
    
    m_mensaje = m_mensaje & "<table>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td colspan='6' class=""ColespanArriba""> EXPEDIENTES EN FASE DE OFERTA SIN RESOLUCIÓN EN MÁS DE 45 DÍAS </td>"
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        m_mensaje = m_mensaje & "<tr>" & vbNewLine
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>IDExp</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>CÓDIGO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>NEMOTÉCNICO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>TÍTULO</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>RESP. CALIDAD</strong></td>"
            m_mensaje = m_mensaje & "<td class=""Cabecera"" > <strong>F.OFERTA</strong></td>"
           
        m_mensaje = m_mensaje & "</tr>" & vbNewLine
        If p_Col.Count = 0 Then
            m_mensaje = m_mensaje & "</table>" & vbNewLine
            HTMLTablaEnFaseOfertaPorMuchoTiempo = m_mensaje
            Exit Function
        End If
        For Each m_IDExpediente In p_Col
            m_Resto = p_Col(m_IDExpediente)
            dato = Split(m_Resto, "|")
            m_CodigoExp = dato(0)
            m_Nemotecnico = dato(1)
            m_TITULO = dato(2)
            m_FECHAOFERTA = dato(3)
           m_RESPONSABLECALIDAD = dato(4)
            
            If m_RESPONSABLECALIDAD = Empty Then m_RESPONSABLECALIDAD = "&nbsp;"
            m_mensaje = m_mensaje & "<tr>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_IDExpediente & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_CodigoExp & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_Nemotecnico & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_TITULO & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_RESPONSABLECALIDAD & "</td>" & vbNewLine
                m_mensaje = m_mensaje & "<td> " & m_FECHAOFERTA & "</td>" & vbNewLine
                
                
            m_mensaje = m_mensaje & "</tr>" & vbNewLine
        Next
    m_mensaje = m_mensaje & "</table>" & vbNewLine
    
    
    HTMLTablaEnFaseOfertaPorMuchoTiempo = m_mensaje
    
End Function

Public Function getColAPuntoDeFinalizar()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resto
    Dim m_IDExpediente
    Dim m_mensaje
    
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FINICIO
    Dim m_FFIN
    Dim m_DiasParaFin
    Dim m_FechaFinGarantia
    Dim m_GARANTIAMESES
    Dim m_FECHACERTIFICACION
    Dim m_RESPONSABLECALIDAD
    
   Set getColAPuntoDeFinalizar = CreateObject("Scripting.Dictionary")
    
    m_SQL = "SELECT IDExpediente, CodExp, Nemotecnico, " & _
                "Titulo, FechaInicioContrato, FechaFinContrato, " & _
                "DateDiff('d',Date(),[FechaFinContrato]) AS Dias,FECHACERTIFICACION,GARANTIAMESES,FechaFinGarantia,Nombre " & _
                "FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
                "WHERE (((DateDiff('d',Date(),[FechaFinContrato]))>-1 " & _
                "And (DateDiff('d',Date(),[FechaFinContrato]))<15) " & _
                "AND ((TbExpedientes.EsBasado)='Sí')) OR (((DateDiff('d',Date(),[FechaFinContrato]))>-1 " & _
                "And (DateDiff('d',Date(),[FechaFinContrato]))<15) AND ((TbExpedientes.EsExpediente)='Sí'));"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnEXP, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_IDExpediente = .Fields("IDExpediente")
            m_CodigoExp = .Fields("CodExp")
            m_Nemotecnico = .Fields("Nemotecnico")
            m_TITULO = .Fields("Titulo")
            m_RESPONSABLECALIDAD = .Fields("Nombre")
            m_FINICIO = .Fields("FechaInicioContrato")
            m_FFIN = .Fields("FechaFinContrato")
            m_DiasParaFin = .Fields("Dias")
            m_FechaFinGarantia = .Fields("FechaFinGarantia")
            m_GARANTIAMESES = .Fields("GARANTIAMESES")
            m_FECHACERTIFICACION = .Fields("FECHACERTIFICACION")
            If IsDate(m_FINICIO) Then
                m_FINICIO = Day(m_FINICIO) & "/" & Month(m_FINICIO) & "/" & Year(m_FINICIO)
            End If
            
            If IsDate(m_FFIN) Then
                m_FFIN = Day(m_FFIN) & "/" & Month(m_FFIN) & "/" & Year(m_FFIN)
            End If
            
            If m_CodigoExp = "" Then m_CodigoExp = "&nbsp;"
            If m_Nemotecnico = "" Then m_Nemotecnico = "&nbsp;"
            If m_TITULO = "" Then m_TITULO = "&nbsp;"
            m_Resto = m_CodigoExp & "|" & m_Nemotecnico & "|" & m_TITULO & "|" & _
                    m_FINICIO & "|" & m_FFIN & "|" & m_DiasParaFin & "|" & _
                    m_FechaFinGarantia & "|" & m_GARANTIAMESES & "|" & m_FECHACERTIFICACION & "|" & m_RESPONSABLECALIDAD
            
            If Not getColAPuntoDeFinalizar.Exists(m_IDExpediente) Then
                getColAPuntoDeFinalizar.Add m_IDExpediente, m_Resto
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Public Function getColHitosAPuntoDeFinalizar()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resto
    Dim m_IDExpediente
    Dim m_mensaje
    
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FechaHito
    Dim m_Descripcion
    Dim m_DiasParaFin
    
    
    Dim m_RESPONSABLECALIDAD
    
   Set getColHitosAPuntoDeFinalizar = CreateObject("Scripting.Dictionary")
    
    m_SQL = "SELECT TbExpedientesHitos.IDExpediente, CodExp, Nemotecnico, " & _
                "Titulo, TbExpedientesHitos.Descripcion, FechaHito, " & _
                "DateDiff('d',Date(),[FechaHito]) AS Dias,Nombre " & _
                "FROM (TbExpedientesHitos INNER JOIN TbExpedientes " & _
                "ON TbExpedientesHitos.IDExpediente = TbExpedientes.IDExpediente) " & _
                "LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
                "WHERE (((DateDiff('d',Date(),[FechaHito]))>-1 And (DateDiff('d',Date(),[FechaHito]))<15));"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnEXP, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_IDExpediente = .Fields("IDExpediente")
            m_CodigoExp = .Fields("CodExp")
            m_Nemotecnico = .Fields("Nemotecnico")
            m_TITULO = .Fields("Titulo")
            m_RESPONSABLECALIDAD = .Fields("Nombre")
            m_FechaHito = .Fields("FechaHito")
            m_Descripcion = .Fields("Descripcion")
            m_DiasParaFin = .Fields("Dias")
            
            
            If m_CodigoExp = "" Then m_CodigoExp = "&nbsp;"
            If m_Nemotecnico = "" Then m_Nemotecnico = "&nbsp;"
            If m_TITULO = "" Then m_TITULO = "&nbsp;"
            m_Resto = m_CodigoExp & "|" & m_Nemotecnico & "|" & m_TITULO & "|" & _
                    m_FechaHito & "|" & m_DiasParaFin & "|" & _
                    m_Descripcion & "|" & m_RESPONSABLECALIDAD
            
            If Not getColHitosAPuntoDeFinalizar.Exists(m_IDExpediente) Then
                getColHitosAPuntoDeFinalizar.Add m_IDExpediente, m_Resto
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function

Public Function getColEstadoDesconocido()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resto
    Dim m_IDExpediente
    Dim m_mensaje
    
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FINICIO
    Dim m_FFIN
    Dim m_GARANTIAMESES
    Dim m_Estado
    Dim m_RESPONSABLECALIDAD
    
    
   Set getColEstadoDesconocido = CreateObject("Scripting.Dictionary")
    
    m_SQL = "SELECT IDExpediente, CodExp, Nemotecnico, " & _
                "Titulo, FechaInicioContrato, FechaFinContrato,GARANTIAMESES, Estado,Nombre " & _
                "FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
                "WHERE Estado='Desconocido';"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnEXP, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_IDExpediente = .Fields("IDExpediente")
            m_CodigoExp = .Fields("CodExp")
            m_Nemotecnico = .Fields("Nemotecnico")
            m_TITULO = .Fields("Titulo")
            m_FINICIO = .Fields("FechaInicioContrato")
            m_FFIN = .Fields("FechaFinContrato")
            m_GARANTIAMESES = .Fields("GARANTIAMESES")
            m_Estado = .Fields("Estado")
            m_RESPONSABLECALIDAD = .Fields("Nombre")
            
            If IsDate(m_FINICIO) Then
                m_FINICIO = Day(m_FINICIO) & "/" & Month(m_FINICIO) & "/" & Year(m_FINICIO)
            End If
            
            If IsDate(m_FFIN) Then
                m_FFIN = Day(m_FFIN) & "/" & Month(m_FFIN) & "/" & Year(m_FFIN)
            End If
            
            If m_CodigoExp = Empty Then m_CodigoExp = "&nbsp;"
            If m_Nemotecnico = Empty Then m_Nemotecnico = "&nbsp;"
            If m_TITULO = Empty Then m_TITULO = "&nbsp;"
            If Not IsNumeric(m_GARANTIAMESES) Then m_GARANTIAMESES = "&nbsp;"
            m_Resto = m_CodigoExp & "|" & m_Nemotecnico & "|" & m_TITULO & "|" & m_FINICIO & "|" & _
                    m_FFIN & "|" & m_GARANTIAMESES & "|" & m_Estado & "|" & m_RESPONSABLECALIDAD
            
            If Not getColEstadoDesconocido.Exists(m_IDExpediente) Then
                getColEstadoDesconocido.Add m_IDExpediente, m_Resto
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Public Function getColAdjudicadosTSOLSinCodS4H()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resto
    Dim m_IDExpediente
    Dim m_mensaje
    
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_RESPONSABLECALIDAD
    Dim m_JURIDICA
    Dim m_FAdjudicacion
    Dim m_CodS4H
    
    
   Set getColAdjudicadosTSOLSinCodS4H = CreateObject("Scripting.Dictionary")
    
    m_SQL = "SELECT TbExpedientes.IDExpediente, TbExpedientes.CodExp, TbExpedientes.Nemotecnico, " & _
            "TbExpedientes.Titulo,TbUsuariosAplicaciones.Nombre, CadenaJuridicas, TbExpedientes.FECHAADJUDICACION, " & _
            "TbExpedientes.CodS4H " & _
            "FROM (TbExpedientes LEFT JOIN TbExpedientesConEntidades " & _
            "ON TbExpedientes.IDExpediente = TbExpedientesConEntidades.IDExpediente) " & _
            "LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
            "WHERE (((TbExpedientesConEntidades.CadenaJuridicas)='TSOL') " & _
            "AND ((TbExpedientes.Adjudicado)='Sí')  " & _
            "AND ((TbExpedientes.CodS4H) Is Null) " & _
            "AND ((TbExpedientes.AplicaTareaS4H) <>'No'));"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnEXP, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_IDExpediente = .Fields("IDExpediente")
            m_CodigoExp = .Fields("CodExp")
            m_Nemotecnico = .Fields("Nemotecnico")
            m_TITULO = .Fields("Titulo")
            m_RESPONSABLECALIDAD = .Fields("Nombre")
            m_JURIDICA = .Fields("CadenaJuridicas")
            m_FAdjudicacion = .Fields("FECHAADJUDICACION")
            m_CodS4H = .Fields("CodS4H")
            
            
            
            If m_CodigoExp = Empty Then m_CodigoExp = "&nbsp;"
            If m_Nemotecnico = Empty Then m_Nemotecnico = "&nbsp;"
            If m_TITULO = Empty Then m_TITULO = "&nbsp;"
            If m_CodS4H = Empty Then m_CodS4H = "&nbsp;"
            
            m_Resto = m_CodigoExp & "|" & m_Nemotecnico & "|" & m_TITULO & "|" & m_RESPONSABLECALIDAD & "|" & _
                    m_JURIDICA & "|" & m_FAdjudicacion & "|" & m_CodS4H
            
            If Not getColAdjudicadosTSOLSinCodS4H.Exists(m_IDExpediente) Then
                getColAdjudicadosTSOLSinCodS4H.Add m_IDExpediente, m_Resto
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Public Function getColAdjudicadosSinContrato()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resto
    Dim m_IDExpediente
    Dim m_mensaje
    
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FINICIO
    Dim m_FFIN
    Dim m_FECHAADJUDICADO
    Dim m_RESPONSABLECALIDAD
    
    
   Set getColAdjudicadosSinContrato = CreateObject("Scripting.Dictionary")
    
    m_SQL = "SELECT IDExpediente, CodExp, Nemotecnico, " & _
                "Titulo, FechaInicioContrato, FechaFinContrato,FECHAADJUDICACION,Nombre " & _
                "FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
                "WHERE FechaInicioContrato Is Null AND GARANTIAMESES Is Null AND FechaFinContrato Is Null " & _
                "AND Not FECHAADJUDICACION is Null AND APLICAESTADO<>'No';"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnEXP, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_IDExpediente = .Fields("IDExpediente")
            m_CodigoExp = .Fields("CodExp")
            m_Nemotecnico = .Fields("Nemotecnico")
            m_TITULO = .Fields("Titulo")
            m_FINICIO = .Fields("FechaInicioContrato")
            m_FFIN = .Fields("FechaFinContrato")
            m_FECHAADJUDICADO = .Fields("FECHAADJUDICACION")
            m_RESPONSABLECALIDAD = .Fields("Nombre")
            
            If IsDate(m_FINICIO) Then
                m_FINICIO = Day(m_FINICIO) & "/" & Month(m_FINICIO) & "/" & Year(m_FINICIO)
            Else
                m_FINICIO = "&nbsp;"
            End If
            
            If IsDate(m_FFIN) Then
                m_FFIN = Day(m_FFIN) & "/" & Month(m_FFIN) & "/" & Year(m_FFIN)
            Else
                m_FFIN = "&nbsp;"
            End If
            
            If m_CodigoExp = Empty Then m_CodigoExp = "&nbsp;"
            If m_Nemotecnico = Empty Then m_Nemotecnico = "&nbsp;"
            If m_TITULO = Empty Then m_TITULO = "&nbsp;"
            If m_FECHAADJUDICADO = Empty Then m_FECHAADJUDICADO = "&nbsp;"
            
            m_Resto = m_CodigoExp & "|" & m_Nemotecnico & "|" & m_TITULO & "|" & m_FINICIO & "|" & _
                    m_FFIN & "|" & m_FECHAADJUDICADO & "|" & m_RESPONSABLECALIDAD
            
            If Not getColAdjudicadosSinContrato.Exists(m_IDExpediente) Then
                getColAdjudicadosSinContrato.Add m_IDExpediente, m_Resto
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Public Function RealizarTarea()
    
    
    
    
    Dim m_ColAPuntoDeFinalizar
    Dim m_ColHitosAPuntoDeFinalizar
    Dim m_ColEstadoDesconocido
    Dim m_ColAdjudicadosSinContrato
    Dim m_ColAdjudicadosTSOLSinCodS4H
    Dim m_ColEnFaseOfertaPorMuchoTiempo
    Dim m_Tecnico
    Dim m_mensaje
   
   
    
    Dim m_HTMLTablaAPuntoDeFinalizar
    Dim m_HTMLTablaHitosAPuntoDeFinalizar
    Dim m_HTMLTablaEstadoDesconocido
    Dim m_HTMLTablaAdjudicadosSinContrato
    Dim m_HTMLTablaAdjudicadosTSOLSinCodS4H
    Dim m_HTMLTablaEnFaseOfertaPorMuchoTiempo
    
    Dim m_TITULO
    Dim m_HTMLCabecera
    
    Set m_ColAPuntoDeFinalizar = getColAPuntoDeFinalizar()
    Set m_ColHitosAPuntoDeFinalizar = getColHitosAPuntoDeFinalizar()
    Set m_ColEstadoDesconocido = getColEstadoDesconocido()
    Set m_ColAdjudicadosSinContrato = getColAdjudicadosSinContrato()
    Set m_ColAdjudicadosTSOLSinCodS4H = getColAdjudicadosTSOLSinCodS4H()
    Set m_ColEnFaseOfertaPorMuchoTiempo = getColsEnFaseOfertaPorMuchoTiempo()
    
    
    m_TITULO = "INFORME DE AVISOS DE NO EXPEDIENTES"
    m_HTMLCabecera = DameCabeceraHTML(m_TITULO)
    m_mensaje = m_HTMLCabecera & vbNewLine
    m_mensaje = m_mensaje & m_TITULO & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
     
    m_HTMLTablaAPuntoDeFinalizar = HTMLTablaAPuntoDeFinalizar(m_ColAPuntoDeFinalizar)
    m_mensaje = m_mensaje & m_HTMLTablaAPuntoDeFinalizar & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    
    m_HTMLTablaHitosAPuntoDeFinalizar = HTMLTablaHitosAPuntoDeFinalizar(m_ColHitosAPuntoDeFinalizar)
    m_mensaje = m_mensaje & m_HTMLTablaHitosAPuntoDeFinalizar & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
     
    m_HTMLTablaEstadoDesconocido = HTMLTablaConEstadoDesconocido(m_ColEstadoDesconocido)
    m_mensaje = m_mensaje & m_HTMLTablaEstadoDesconocido & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    
    m_HTMLTablaAdjudicadosSinContrato = HTMLTablaAdjudicadosSinContrato(m_ColAdjudicadosSinContrato)
    m_mensaje = m_mensaje & m_HTMLTablaAdjudicadosSinContrato & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    
    m_HTMLTablaAdjudicadosTSOLSinCodS4H = HTMLTablaAdjudicadosTSOLSinCodS4H(m_ColAdjudicadosTSOLSinCodS4H)
    m_mensaje = m_mensaje & m_HTMLTablaAdjudicadosTSOLSinCodS4H & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    
    m_HTMLTablaEnFaseOfertaPorMuchoTiempo = HTMLTablaEnFaseOfertaPorMuchoTiempo(m_ColEnFaseOfertaPorMuchoTiempo)
    m_mensaje = m_mensaje & m_HTMLTablaEnFaseOfertaPorMuchoTiempo & vbNewLine
    m_mensaje = m_mensaje & "<br /><br />" & vbNewLine
    
    RegistrarCorreo "Informe Tareas De Expedientes (Expedientes)", m_mensaje, m_CadenaCorreoTramitadores
    
    
    
    
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
Public Function Lanzar()
    
    
    
    Dim m_TareaHecha
    
    m_URLBBDDTareas = "\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb"
    Set CnTareas = Conn(m_URLBBDDTareas, m_Pass)
    m_TareaHecha = TareaRealizada()
    If m_TareaHecha = False Then
        m_URLBBDDEXP = "\\datoste\APLICACIONES_DYS\Aplicaciones PpD\EXPEDIENTES\Expedientes_datos.accdb"
        Set CnEXP = Conn(m_URLBBDDEXP, m_Pass)
        CSS = getCSS
        m_CadenaCorreoAdministradores = getCadenaCorreoAdministradores()
        If InStr(1, m_CadenaCorreoAdministradores, "@") = 0 Then
            Exit Function
        End If
        m_CadenaCorreoTramitadores = getCadenaCorreoTareas()
        If InStr(1, m_CadenaCorreoTramitadores, "@") = 0 Then
            Exit Function
        End If
        RealizarTarea
        
        CnEXP.Close
        Set CnEXP = Nothing
        RegistrarTarea
    End If
    
    CnTareas.Close
    Set CnTareas = Nothing
    
End Function
Public Function getCadenaCorreoAdministradores()
    Dim rcdDatos
    Dim m_SQL
    Dim m_Correo
    
    Dim m_CadenaCorreo
    
    
    
    m_SQL = "SELECT TbUsuariosAplicaciones.CorreoUsuario " & _
                "FROM TbUsuariosAplicaciones " & _
                "WHERE EsAdministrador='Sí';"
    
    Set rcdDatos = CreateObject("ADODB.Recordset")
    rcdDatos.Open m_SQL, CnTareas, adOpenDynamic, adLockPessimistic, adCmdText
    If Not rcdDatos.EOF Then
        
        Do While Not rcdDatos.EOF
            m_Correo = rcdDatos.Fields("CorreoUsuario")
            If m_CadenaCorreo = Empty Then
                m_CadenaCorreo = m_Correo
            Else
                m_CadenaCorreo = m_CadenaCorreo & ";" & m_Correo
            End If
            
            rcdDatos.MoveNext
        Loop
        
    End If
    getCadenaCorreoAdministradores = m_CadenaCorreo
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Public Function getColsEnFaseOfertaPorMuchoTiempo()
    
    Dim rcdDatos
    Dim m_SQL
    Dim m_Resto
    Dim m_IDExpediente
    Dim m_mensaje
    
    Dim m_CodigoExp
    Dim m_Nemotecnico
    Dim m_TITULO
    Dim m_FECHAOFERTA
    
    Dim m_RESPONSABLECALIDAD
    
   Set getColsEnFaseOfertaPorMuchoTiempo = CreateObject("Scripting.Dictionary")
    
    m_SQL = "SELECT TbExpedientes.IDExpediente, TbExpedientes.CodExp, TbExpedientes.Nemotecnico, TbExpedientes.Titulo, " & _
            "TbExpedientes.FechaInicioContrato, TbExpedientes.FECHAOFERTA, TbUsuariosAplicaciones.Nombre " & _
            "FROM TbExpedientes LEFT JOIN TbUsuariosAplicaciones " & _
            "ON TbExpedientes.IDResponsableCalidad = TbUsuariosAplicaciones.Id " & _
            "WHERE ((Not (TbExpedientes.FECHAOFERTA) Is Null) AND ((DateDiff('d',[FECHAOFERTA],Date()))>=45) " & _
            "AND ((TbExpedientes.FECHAPERDIDA) Is Null) AND ((TbExpedientes.FECHAADJUDICACION) Is Null) " & _
            "AND ((TbExpedientes.FECHADESESTIMADA) Is Null));"
    
    Set rcdDatos = CreateObject("ADODB.RecordSet")
    rcdDatos.Open m_SQL, CnEXP, adOpenDynamic, adLockPessimistic, adCmdText
    With rcdDatos
        If .EOF Then
            rcdDatos.Close
            Set rcdDatos = Nothing
            
            
            Exit Function
        End If
        
        Do While Not .EOF
            m_IDExpediente = .Fields("IDExpediente")
            m_CodigoExp = .Fields("CodExp")
            m_Nemotecnico = .Fields("Nemotecnico")
            m_TITULO = .Fields("Titulo")
            m_RESPONSABLECALIDAD = .Fields("Nombre")
            m_FECHAOFERTA = .Fields("FECHAOFERTA")
            
            If IsDate(m_FECHAOFERTA) Then
                m_FECHAOFERTA = Day(m_FECHAOFERTA) & "/" & Month(m_FECHAOFERTA) & "/" & Year(m_FECHAOFERTA)
            End If
            
            
            
            If m_CodigoExp = "" Then m_CodigoExp = "&nbsp;"
            If m_Nemotecnico = "" Then m_Nemotecnico = "&nbsp;"
            If m_TITULO = "" Then m_TITULO = "&nbsp;"
            m_Resto = m_CodigoExp & "|" & m_Nemotecnico & "|" & m_TITULO & "|" & _
                    m_FECHAOFERTA & "|" & m_RESPONSABLECALIDAD
            
            If Not getColsEnFaseOfertaPorMuchoTiempo.Exists(m_IDExpediente) Then
                getColsEnFaseOfertaPorMuchoTiempo.Add m_IDExpediente, m_Resto
            End If
            
            
            .MoveNext
        Loop
       
    End With
    rcdDatos.Close
    Set rcdDatos = Nothing
    
    
End Function
Lanzar


















