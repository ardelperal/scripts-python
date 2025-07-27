# Funciones de Usuarios Comunes

Este documento describe las funciones comunes para obtener usuarios de diferentes tipos desde la base de datos Lanzadera.

## Configuración

### Variables de Entorno (.env)

Se han agregado las siguientes configuraciones al archivo `.env`:

```env
# Base de datos Lanzadera - Entorno LOCAL
LOCAL_DB_LANZADERA=dbs-locales/Lanzadera_Datos.accdb

# Base de datos Lanzadera - Entorno OFICINA
OFFICE_DB_LANZADERA=\\datoste\Aplicaciones_dys\Aplicaciones PpD\0Lanzadera\Lanzadera_Datos.accdb

# IDs de Aplicaciones
APP_ID_AGEDYS=3
APP_ID_BRASS=6
APP_ID_NOCONFORMIDADES=8
APP_ID_EXPEDIENTES=19
```

### Métodos de Configuración

La clase `Config` ahora incluye:

```python
# Propiedades para IDs de aplicaciones
config.app_id_agedys          # 3
config.app_id_brass           # 6
config.app_id_noconformidades # 8
config.app_id_expedientes     # 19

# Métodos útiles
config.get_app_id('agedys')                    # Retorna 3
config.get_all_app_ids()                       # Retorna dict con todos los IDs
config.get_db_lanzadera_connection_string()    # Cadena de conexión a Lanzadera
```

## Funciones Disponibles

### 1. Función Principal

```python
from common.utils import get_application_users
from common.config import Config

config = Config()
users = get_application_users(application_id, user_type, config, logger=None)
```

**Parámetros:**
- `application_id` (int): ID de la aplicación (3=AGEDYS, 6=BRASS, 8=NoConformidades, 19=Expedientes)
- `user_type` (str): Tipo de usuario ('quality', 'technical', 'admin')
- `config`: Objeto de configuración
- `logger` (opcional): Logger para registrar eventos

**Retorna:** Lista de usuarios que cumplen los criterios

### 2. Funciones Específicas

#### Usuarios de Calidad
```python
from common.utils import get_quality_users

users = get_quality_users(application_id, config, logger=None)
```

#### Usuarios Técnicos
```python
from common.utils import get_technical_users

users = get_technical_users(application_id, config, logger=None)
```

#### Usuarios Administradores
```python
from common.utils import get_admin_users

users = get_admin_users(config, logger=None)
```

## Ejemplos de Uso

### Ejemplo 1: Obtener usuarios de calidad para BRASS

```python
from common.config import Config
from common.utils import get_quality_users

config = Config()
brass_id = config.app_id_brass  # 6
users = get_quality_users(brass_id, config)

for user in users:
    print(f"Usuario: {user.get('NombreUsuario')} - Email: {user.get('CorreoUsuario')}")
```

### Ejemplo 2: Obtener usuarios técnicos para No Conformidades

```python
from common.config import Config
from common.utils import get_technical_users

config = Config()
nc_id = config.get_app_id('noconformidades')  # 8
users = get_technical_users(nc_id, config)

print(f"Encontrados {len(users)} usuarios técnicos para No Conformidades")
```

### Ejemplo 3: Obtener todos los administradores

```python
from common.config import Config
from common.utils import get_admin_users

config = Config()
admins = get_admin_users(config)

admin_emails = [user.get('CorreoUsuario') for user in admins]
print(f"Emails de administradores: {admin_emails}")
```

### Ejemplo 4: Usar la función genérica

```python
from common.config import Config
from common.utils import get_application_users

config = Config()

# Obtener usuarios de calidad para AGEDYS
agedys_quality = get_application_users(config.app_id_agedys, 'quality', config)

# Obtener usuarios técnicos para Expedientes
expedientes_technical = get_application_users(config.app_id_expedientes, 'technical', config)

# Obtener administradores (ID no importa para admin)
admins = get_application_users(0, 'admin', config)
```

## Estructura de Datos Retornada

Cada usuario retornado es un diccionario con las siguientes claves principales:

```python
{
    'NombreUsuario': 'Nombre del usuario',
    'CorreoUsuario': 'email@telefonica.com',
    'EsAdministrador': 'Sí/No',
    # ... otros campos de la tabla TbUsuariosAplicaciones
}
```

## Consultas SQL Utilizadas

### Usuarios de Calidad
```sql
SELECT TbUsuariosAplicaciones.* 
FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesPermisos 
ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario 
WHERE TbUsuariosAplicacionesPermisos.IDAplicacion = ? 
AND TbUsuariosAplicacionesPermisos.EsUsuarioCalidad = 'Sí'
```

### Usuarios Técnicos
```sql
SELECT TbUsuariosAplicaciones.* 
FROM TbUsuariosAplicaciones INNER JOIN TbUsuariosAplicacionesPermisos 
ON TbUsuariosAplicaciones.CorreoUsuario = TbUsuariosAplicacionesPermisos.CorreoUsuario 
WHERE TbUsuariosAplicacionesPermisos.IDAplicacion = ? 
AND TbUsuariosAplicacionesPermisos.EsUsuarioTecnico = 'Sí'
```

### Usuarios Administradores
```sql
SELECT TbUsuariosAplicaciones.* 
FROM TbUsuariosAplicaciones 
WHERE TbUsuariosAplicaciones.EsAdministrador = 'Sí'
```

## Manejo de Errores

Las funciones incluyen manejo de errores y logging:

- Si hay un error de conexión, se retorna una lista vacía
- Los errores se registran en el logger si se proporciona
- Se cierran automáticamente las conexiones de base de datos

## Pruebas

Para probar las funciones, ejecuta:

```bash
python test_user_functions.py
```

Este script prueba todas las funciones con diferentes aplicaciones y tipos de usuario.