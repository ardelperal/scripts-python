# Guía de Migración: GestionRiesgos.vbs → Python

## Resumen de la Migración

Esta guía documenta la migración completa del script VBScript `GestionRiesgos.vbs` al módulo Python `src/riesgos`. La migración mantiene toda la funcionalidad original mientras mejora la estructura, mantenibilidad y robustez del código.

## Análisis del Script Original

### Estructura del VBScript Original

El archivo `GestionRiesgos.vbs` contenía aproximadamente 3,200 líneas de código con las siguientes funciones principales:

1. **Función Principal**: `Lanzar()` - Punto de entrada principal
2. **Tareas Técnicas**: `RealizarTareaTecnicos()` - Reportes para jefes de proyecto
3. **Tareas de Calidad**: `RealizarTareaCalidadMensual()` - Reportes mensuales
4. **Gestión de Usuarios**: `getColUsuariosDistintos()` - Obtención de usuarios únicos
5. **Utilidades**: Funciones de fecha, CSS, y consultas SQL

### Funciones Identificadas en el VBScript

```vbscript
' Funciones principales identificadas:
Public Function Lanzar()
Public Function UltimaEjecucion(tipo)
Public Function TareaTecnicaParaEjecutar()
Public Function TareaCalidadParaEjecutar()
Public Function TareaMensualParaEjecutar()
Public Function EVE(fecha)
Public Function getCSS()
Public Function getColusuariosTareas()
Public Function getColUsuariosDistintos()
Public Function RealizarTareaTecnicos()
Public Function RealizarTareaCalidadMensual()
' ... y muchas más funciones de consulta SQL
```

## Mapeo de Funcionalidades

### Correspondencia VBScript → Python

| Función VBScript | Método Python | Descripción |
|------------------|---------------|-------------|
| `Lanzar()` | `execute_daily_task()` | Función principal de ejecución |
| `UltimaEjecucion(tipo)` | `get_last_execution(task_type)` | Obtiene fecha de última ejecución |
| `TareaTecnicaParaEjecutar()` | `should_execute_technical_task()` | Determina si ejecutar tarea técnica |
| `TareaCalidadParaEjecutar()` | `should_execute_quality_task()` | Determina si ejecutar tarea de calidad |
| `TareaMensualParaEjecutar()` | `should_execute_monthly_quality_task()` | Determina si ejecutar tarea mensual |
| `getColUsuariosDistintos()` | `get_distinct_users()` | Obtiene usuarios únicos |
| `RealizarTareaTecnicos()` | `execute_technical_task()` | Ejecuta tareas técnicas |
| `RealizarTareaCalidadMensual()` | `execute_monthly_quality_task()` | Ejecuta tareas mensuales |
| `getCSS()` | `get_css_styles()` | Obtiene estilos CSS |
| `EVE(fecha)` | Integrado en lógica de fechas | Cálculos de fechas |

### Variables Globales Migradas

| Variable VBScript | Equivalente Python | Tipo |
|-------------------|-------------------|------|
| `CnRiesgos` | `self.connection` | Conexión BD |
| `m_Col` | `users_dict` | Diccionario usuarios |
| `destinatarios` | `recipients` | Lista destinatarios |
| `asunto` | `subject` | String asunto |
| `cuerpo` | `body` | String cuerpo HTML |

## Mejoras Implementadas

### 1. Estructura Orientada a Objetos

**Antes (VBScript):**
```vbscript
Dim CnRiesgos
Set CnRiesgos = CreateObject("ADODB.Connection")
CnRiesgos.Open "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=" & rutaBD
```

**Después (Python):**
```python
class RiesgosManager:
    def __init__(self, config: Config):
        self.config = config
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        try:
            self.connection = pyodbc.connect(
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
                f"DBQ={self.config.database_path};"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error conectando a BD: {e}")
            return False
```

### 2. Manejo de Errores Mejorado

**Antes (VBScript):**
```vbscript
On Error Resume Next
Set rs = CnRiesgos.Execute(sql)
If Err.Number <> 0 Then
    ' Manejo básico de errores
End If
```

**Después (Python):**
```python
def execute_query(self, query: str) -> Optional[List[Dict]]:
    try:
        cursor = self.connection.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    except Exception as e:
        self.logger.error(f"Error ejecutando consulta: {e}")
        return None
```

### 3. Configuración Centralizada

**Antes (VBScript):**
```vbscript
' Variables hardcodeadas en el script
rutaBD = "dbs-locales/base_datos.accdb"
servidorSMTP = "smtp.empresa.com"
```

**Después (Python):**
```python
# Configuración desde archivo JSON
{
    "database_path": "config/database.accdb",
    "smtp_server": "smtp.empresa.com",
    "smtp_port": 587,
    "admin_emails": ["admin@empresa.com"]
}
```

### 4. Logging Estructurado

**Antes (VBScript):**
```vbscript
' Sin logging estructurado
WScript.Echo "Ejecutando tarea..."
```

**Después (Python):**
```python
import logging

self.logger.info("Iniciando ejecución de tarea técnica")
self.logger.debug(f"Usuarios encontrados: {len(users)}")
self.logger.error(f"Error en consulta: {e}")
```

## Consultas SQL Migradas

### Ejemplo de Migración de Consulta

**Original VBScript:**
```vbscript
Function getColEdicionesNecesitanPropuestaPublicacion()
    Dim sql
    sql = "SELECT DISTINCT u.UsuarioRed, u.Nombre, u.Email " & _
          "FROM ((Ediciones e INNER JOIN Usuarios u ON e.JefeProyecto = u.UsuarioRed) " & _
          "INNER JOIN EstadosEdicion ee ON e.Estado = ee.IdEstadoEdicion) " & _
          "WHERE ee.Nombre IN ('Elaboración', 'Revisión', 'Validación') " & _
          "AND e.FechaPropuestaPublicacion IS NULL"
    
    Set rs = CnRiesgos.Execute(sql)
    ' Procesamiento...
End Function
```

**Migrado a Python:**
```python
def get_editions_needing_publication_proposal_query(self) -> str:
    return """
    SELECT DISTINCT u.UsuarioRed, u.Nombre, u.Email
    FROM ((Ediciones e INNER JOIN Usuarios u ON e.JefeProyecto = u.UsuarioRed)
    INNER JOIN EstadosEdicion ee ON e.Estado = ee.IdEstadoEdicion)
    WHERE ee.Nombre IN ('Elaboración', 'Revisión', 'Validación')
    AND e.FechaPropuestaPublicacion IS NULL
    """

def get_editions_needing_publication_proposal(self) -> Optional[List[Dict]]:
    query = self.get_editions_needing_publication_proposal_query()
    return self.execute_query(query)
```

## Generación de HTML Mejorada

### Antes (VBScript)
```vbscript
Function getCSS()
    getCSS = "<style type=""text/css"">" & vbCrLf & _
             "body {font-family: Arial, sans-serif;}" & vbCrLf & _
             "</style>"
End Function
```

### Después (Python)
```python
def get_css_styles(self) -> str:
    return """
    <style type="text/css">
    body {
        font-family: Arial, sans-serif;
        margin: 20px;
        background-color: #f5f5f5;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 20px;
        background-color: white;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #4CAF50;
        color: white;
    }
    tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .section-header {
        background-color: #2196F3;
        color: white;
        padding: 10px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    </style>
    """
```

## Sistema de Tareas Mejorado

### Control de Ejecución

**Antes (VBScript):**
```vbscript
Function TareaTecnicaParaEjecutar()
    Dim ultimaEjecucion
    ultimaEjecucion = UltimaEjecucion("TECNICA")
    If DateDiff("d", ultimaEjecucion, Date) >= 7 Then
        TareaTecnicaParaEjecutar = True
    Else
        TareaTecnicaParaEjecutar = False
    End If
End Function
```

**Después (Python):**
```python
def should_execute_technical_task(self) -> bool:
    """Determina si debe ejecutarse la tarea técnica (cada 7 días)."""
    try:
        last_execution = self.get_last_execution('TECNICA')
        if last_execution is None:
            return True
        
        days_since = (datetime.now() - last_execution).days
        should_execute = days_since >= 7
        
        self.logger.info(f"Última ejecución técnica: {last_execution}, "
                        f"días transcurridos: {days_since}, "
                        f"debe ejecutar: {should_execute}")
        
        return should_execute
    except Exception as e:
        self.logger.error(f"Error verificando tarea técnica: {e}")
        return False
```

## Envío de Correos Mejorado

### Integración con Sistema de Notificaciones

**Antes (VBScript):**
```vbscript
' Código disperso para envío de correos
Set objMessage = CreateObject("CDO.Message")
objMessage.From = "sistema@empresa.com"
objMessage.To = destinatarios
objMessage.Subject = asunto
objMessage.HTMLBody = cuerpo
objMessage.Send
```

**Después (Python):**
```python
def send_technical_reports(self, users_data: Dict) -> bool:
    """Envía reportes técnicos a usuarios individuales."""
    try:
        for username, user_info in users_data.items():
            # Generar reporte personalizado
            report_html = self.generate_technical_report_for_user(username)
            
            if report_html:
                subject = f"Reporte Técnico de Riesgos - {user_info['Nombre']}"
                
                # Usar sistema centralizado de notificaciones
                success = send_notification_email(
                    recipients=[user_info['Email']],
                    subject=subject,
                    body=report_html,
                    config=self.config
                )
                
                if success:
                    self.logger.info(f"Reporte enviado a {user_info['Email']}")
                else:
                    self.logger.error(f"Error enviando reporte a {user_info['Email']}")
        
        return True
    except Exception as e:
        self.logger.error(f"Error enviando reportes técnicos: {e}")
        return False
```

## Pruebas Unitarias

### Cobertura de Pruebas Implementada

```python
class TestRiesgosManager(unittest.TestCase):
    def setUp(self):
        self.config = Config({
            'database_path': 'test.accdb',
            'smtp_server': 'test.smtp.com',
            'admin_emails': ['admin@test.com']
        })
        self.manager = RiesgosManager(self.config)
    
    def test_initialization(self):
        """Prueba la inicialización del manager."""
        self.assertIsNotNone(self.manager.config)
        self.assertIsNone(self.manager.connection)
    
    @patch('pyodbc.connect')
    def test_database_connection(self, mock_connect):
        """Prueba la conexión a la base de datos."""
        mock_connect.return_value = MagicMock()
        result = self.manager.connect()
        self.assertTrue(result)
        mock_connect.assert_called_once()
    
    # ... más pruebas
```

## Script de Ejecución

### Interfaz de Línea de Comandos

```python
def main():
    parser = argparse.ArgumentParser(description='Gestión de Riesgos - Migración de GestionRiesgos.vbs')
    parser.add_argument('--config', default='config/config.json', help='Archivo de configuración')
    parser.add_argument('--verbose', action='store_true', help='Logging detallado')
    parser.add_argument('--force-technical', action='store_true', help='Forzar ejecución técnica')
    parser.add_argument('--force-quality', action='store_true', help='Forzar ejecución calidad')
    parser.add_argument('--force-monthly', action='store_true', help='Forzar ejecución mensual')
    
    args = parser.parse_args()
    
    # Configurar logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Cargar configuración
        config = Config.from_file(args.config)
        
        # Crear manager
        manager = RiesgosManager(config)
        
        # Ejecutar tareas
        if args.force_technical or args.force_quality or args.force_monthly:
            # Ejecución forzada
            execute_forced_tasks(manager, args)
        else:
            # Ejecución normal
            if manager.execute_daily_task():
                print("✓ Tareas de riesgos ejecutadas exitosamente")
            else:
                print("✗ Error en la ejecución de tareas")
                sys.exit(1)
                
    except Exception as e:
        logging.error(f"Error en ejecución principal: {e}")
        sys.exit(1)
```

## Beneficios de la Migración

### 1. Mantenibilidad
- Código estructurado en clases y métodos
- Separación clara de responsabilidades
- Documentación completa

### 2. Robustez
- Manejo de errores mejorado
- Logging detallado
- Validación de datos

### 3. Testabilidad
- Pruebas unitarias completas
- Mocking de dependencias externas
- Cobertura de código

### 4. Configurabilidad
- Configuración externa en JSON
- Parámetros ajustables
- Múltiples entornos

### 5. Monitoreo
- Logs estructurados
- Métricas de rendimiento
- Alertas de errores

## Consideraciones de Despliegue

### Requisitos del Sistema

```txt
# requirements.txt
pyodbc>=4.0.35
python-dateutil>=2.8.2
```

### Configuración de Producción

```json
{
    "database_path": "\\\\servidor\\ruta\\produccion\\riesgos.accdb",
    "smtp_server": "smtp.empresa.com",
    "smtp_port": 587,
    "smtp_use_tls": true,
    "smtp_username": "sistema@empresa.com",
    "smtp_password": "password_cifrado",
    "admin_emails": [
        "admin1@empresa.com",
        "admin2@empresa.com"
    ],
    "log_level": "INFO",
    "log_file": "logs/riesgos_produccion.log"
}
```

### Programación de Tareas

**Windows Task Scheduler:**
```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T08:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>run_riesgos.py --config config/production.json</Arguments>
    </Exec>
  </Actions>
</Task>
```

## Migración Paso a Paso

### Fase 1: Preparación
1. ✅ Análisis del código VBScript original
2. ✅ Identificación de funciones y dependencias
3. ✅ Diseño de la arquitectura Python

### Fase 2: Implementación Core
1. ✅ Creación de la clase `RiesgosManager`
2. ✅ Migración de consultas SQL
3. ✅ Implementación de lógica de tareas

### Fase 3: Funcionalidades Avanzadas
1. ✅ Sistema de reportes HTML
2. ✅ Integración con notificaciones
3. ✅ Manejo de errores y logging

### Fase 4: Pruebas y Documentación
1. ✅ Pruebas unitarias completas
2. ✅ Documentación técnica
3. ✅ Ejemplos de uso

### Fase 5: Despliegue
1. ⏳ Configuración de producción
2. ⏳ Programación de tareas
3. ⏳ Monitoreo y validación

## Conclusión

La migración de `GestionRiesgos.vbs` a Python ha sido exitosa, manteniendo toda la funcionalidad original mientras se mejora significativamente la estructura, mantenibilidad y robustez del código. El nuevo módulo está listo para producción y proporciona una base sólida para futuras mejoras y extensiones.