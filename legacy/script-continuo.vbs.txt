Option Explicit


Public Function EsNoche()
    Dim Hora
    Dim HoraCompleta
    HoraCompleta = Now()
    Hora = Hour(HoraCompleta)
    If Hora >= 20 And Hora <= 24 Then
        EsNoche = True
    ElseIf Hora >= 0 And Hora < 7 Then
        EsNoche = True
    Else
        EsNoche = False
    End If
End Function
Function EsLaborable(fecha)
    Dim fso, archivo, linea,rutaScript, dirPadre, rutaFestivos


    
    
    ' Si es s�bado o domingo, no es laborable
    If Weekday(fecha, vbMonday) > 5 Then
        EsLaborable = False
        Exit Function
    End If
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    rutaScript = fso.GetParentFolderName(WScript.ScriptFullName)
    dirPadre = fso.GetParentFolderName(rutaScript)  ' Un directorio atrás
    rutaFestivos = fso.BuildPath(dirPadre, "herramientas\\Festivos.txt")


    Set archivo = fso.OpenTextFile(rutaFestivos, 1)
    
    Do While Not archivo.AtEndOfStream
        linea = archivo.ReadLine
        ' Busca la fecha al principio de la línea (puede estar entre paréntesis)
        ' Extrae solo la parte de la fecha
        If InStr(1, linea, fecha) <> 0 Then
            archivo.Close
            Set archivo = Nothing
            Set fso = Nothing
            EsLaborable = False
            Exit Function
        End If
       
    Loop
    archivo.Close
    Set archivo = Nothing
    Set fso = Nothing
    
    EsLaborable = True
End Function
Public Function getTiempo(m_EsNoche, EsLaborableDia)
    Dim minutosLaborablesDia
    Dim minutosNoLaborablesDia
    Dim minutosLaborablesNoche
    Dim minutosNoLaborablesNoche
    Dim minutos
    Dim segundos

    minutosNoLaborablesDia = 60
    minutosLaborablesDia = 5
    minutosLaborablesNoche = 60
    minutosNoLaborablesNoche = 120

    If EsLaborableDia Then
        If m_EsNoche Then
            minutos = minutosLaborablesNoche
        Else
            minutos = minutosLaborablesDia
        End If
    Else
        If m_EsNoche Then
            minutos = minutosNoLaborablesNoche
        Else
            minutos = minutosNoLaborablesDia
        End If
    End If
    segundos = minutos * 60
    getTiempo = minutos & "|" & segundos * 1000
End Function

Public Function main()
    Dim objShell
    Dim minutos
    Dim flag
    Dim Tiempo
    Dim dato
    Dim DiaActual
    Dim DiaRealizacionTareas
    Dim TiempotareaNC
    Dim TiempoTareaBrass
    Dim TiempoTareaTareas
    Dim TiempoTareaRiesgos
    Dim EsLaborableHoy
	Dim TareasHechas
	Dim fso, scriptDir

    TiempotareaNC = 30000
    TiempoTareaBrass = 30000
    TiempoTareaTareas = 120000
    TiempoTareaRiesgos = 60000
    Set objShell = WScript.CreateObject("WScript.Shell")
    DiaRealizacionTareas = Date

    EsLaborableHoy = EsLaborable(Date)
    TareasHechas = False
    Set fso = CreateObject("Scripting.FileSystemObject")
    scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
    Do While True
        objShell.CurrentDirectory =scriptDir
        DiaActual = Date

        ' Verificar si la fecha ha cambiado para recalcular EsLaborableHoy
        If DiaActual <> DiaRealizacionTareas Then
            EsLaborableHoy = EsLaborable(DiaActual) ' Recalcular solo si el día ha cambiado
            TareasHechas = False
        End If

        flag = getTiempo(EsNoche(), EsLaborableHoy)
        dato = Split(flag, "|")
        minutos = dato(0)
        Tiempo = dato(1)

        If EsLaborableHoy And TareasHechas = False Then
            If Hour(Now()) > 6 Then
                debug.WriteLine "1/7 Iniciando NoConformidades "  & Now()
                objShell.Run "NoConformidades.vbs"
                WScript.Sleep TiempotareaNC
                
                debug.WriteLine "2/7 Iniciando GestionRiesgos_bat "  & Now()
                objShell.Run "GestionRiesgos.vbs"
                WScript.Sleep TiempoTareaRiesgos
  
                debug.WriteLine "3/7 Iniciando BRASS.vbs "  & Now()
                objShell.Run "BRASS.vbs"
                WScript.Sleep TiempoTareaBrass
                debug.WriteLine "4/7 Iniciando Expedientes.vbs "  & Now()
                objShell.Run "Expedientes.vbs"
                WScript.Sleep TiempoTareaBrass
                debug.WriteLine "5/7 Iniciando AGEDYS "  & Now()
                objShell.Run "AGEDYS.VBS"
                WScript.Sleep TiempoTareaTareas
                debug.WriteLine "Pasa Por tareas diarias"
                DiaRealizacionTareas = Date ' Actualizar la fecha de última ejecución de las tareas diarias
                TareasHechas=true
            End If
        Else
            debug.WriteLine "No Pasa Por tareas diarias"
        End If
        
        debug.WriteLine "6/7 Iniciando Correos de Tareas "  & Now()
        objShell.Run "EnviarCorreoTareas.vbs"
        debug.WriteLine "7/7 Iniciando Correos Resto "  & Now()
        objShell.Run "EnviarCorreoNoEnviado.vbs"
        debug.WriteLine "Próximo ciclo en " &  minutos & " minutos" & " " & DateAdd("n", minutos, Now())
        debug.WriteLine "--------------------------------------------------------------------------"
        WScript.Sleep Tiempo
    Loop
End Function
main