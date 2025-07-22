# Directorio dbs-locales - Entorno Local

Este directorio contiene las bases de datos y archivos de configuración para el **entorno local**.

## 📁 Archivos requeridos para entorno local:

### **Bases de Datos (.accdb)**
> ⚠️ **Nota**: Los archivos .accdb no se incluyen en Git por su tamaño.
> Cópialos manualmente desde el entorno de producción.

- `Tareas_datos1.accdb` - Base de datos principal de tareas
- `Gestion_Brass_Gestion_Datos.accdb` - Base de datos del sistema BRASS
- `Gestion_Riesgos_Datos.accdb` - Base de datos de gestión de riesgos
- `Correos_datos.accdb` - Base de datos de correos

### **Archivos de Configuración (.txt)**
> ✅ **Incluidos en Git** - Se sincronizan automáticamente

- `CSS.txt` - Estilos CSS para reportes HTML
- `Festivos.txt` - Lista de días festivos

## 🔄 **Configuración del Entorno Local**

1. **Obtener las bases de datos**:
   ```powershell
   # Copiar desde el entorno de red (en oficina)
   Copy-Item "\\datoste\aplicaciones_dys\Aplicaciones PpD\00Recursos\Tareas_datos1.accdb" .\dbs-locales\
   Copy-Item "\\datoste\aplicaciones_dys\Aplicaciones PpD\BRASS\Gestion_Brass_Gestion_Datos.accdb" .\dbs-locales\
   # ... (resto de bases de datos)
   ```

2. **Activar entorno local**:
   ```powershell
   .\tools\Switch-Environment.ps1 local
   ```

3. **Verificar configuración**:
   ```powershell
   .\tools\Switch-Environment.ps1 status
   ```

## 🔐 **Autenticación**

El entorno local usa:
- **Tipo**: Password específico
- **Password**: `dpddpd` (configurable en `config.json`)
- **Descripción**: Para bases de datos locales con protección

## 📋 **Verificación de Funcionamiento**

```powershell
# Ejecutar tests para verificar que todo funciona
Invoke-Pester .\tests\BRASS.Simple.Tests.ps1

# Resultado esperado: 10/10 tests pasando ✅
```

---
**💡 Consejo**: Para desarrollo local, mantén las bases de datos actualizadas periódicamente desde producción.
- `CSS.txt` - Estilos CSS para los informes
- `Festivos.txt` - Lista de días festivos

## Uso:
1. Copia las bases de datos originales a esta carpeta
2. El sistema **prioriza OFICINA** si hay conectividad de red
3. Para forzar el entorno local: `.\tools\Switch-Environment.ps1 local`

## 🔄 Detección automática (nueva lógica):
- **1ª PRIORIDAD**: Si hay conectividad a red corporativa → **OFICINA**
- **2ª PRIORIDAD**: Sin red + bases locales disponibles → **LOCAL**  
- **3ª PRIORIDAD**: Sin ninguna → **OFICINA** (fallback)

## 🔧 Forzado manual:
```powershell
.\tools\Switch-Environment.ps1 oficina  # Fuerza OFICINA (ignora bases locales)
.\tools\Switch-Environment.ps1 local    # Fuerza LOCAL (ignora conectividad)
.\tools\Switch-Environment.ps1 auto     # Vuelve a detección automática
```

**IMPORTANTE:** Esta carpeta está en .gitignore para no subir bases de datos al repositorio.