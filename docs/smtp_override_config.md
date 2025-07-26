# Configuración SMTP Alternativa

## Descripción

Esta funcionalidad permite sobrescribir la configuración SMTP por defecto cuando no se puede acceder al servidor SMTP de oficina desde ciertas máquinas.

## Problema Resuelto

En el entorno de oficina, el servidor SMTP (`10.73.54.85:25`) solo es accesible desde máquinas específicas. Cuando trabajas desde otras máquinas en la red de oficina, puedes acceder a las bases de datos pero no al servidor SMTP.

## Solución

Se han añadido variables de entorno de sobrescritura que permiten configurar un servidor SMTP alternativo sin cambiar el entorno principal.

## Variables de Configuración

### Variables de Sobrescritura SMTP

Añade estas variables a tu archivo `.env` para usar un servidor SMTP alternativo:

```bash
# SMTP ALTERNATIVO (para cuando no se puede acceder al servidor de oficina)
SMTP_OVERRIDE_SERVER=localhost          # Servidor SMTP alternativo
SMTP_OVERRIDE_PORT=1025                 # Puerto del servidor alternativo
SMTP_OVERRIDE_USER=test@example.com     # Usuario para autenticación (opcional)
SMTP_OVERRIDE_PASSWORD=                 # Contraseña para autenticación (opcional)
SMTP_OVERRIDE_TLS=false                 # Usar TLS (true/false)
```

## Ejemplos de Uso

### 1. Servidor SMTP Local (para desarrollo/testing)

```bash
SMTP_OVERRIDE_SERVER=localhost
SMTP_OVERRIDE_PORT=1025
SMTP_OVERRIDE_USER=
SMTP_OVERRIDE_PASSWORD=
SMTP_OVERRIDE_TLS=false
```

### 2. Gmail SMTP (para envío real)

```bash
SMTP_OVERRIDE_SERVER=smtp.gmail.com
SMTP_OVERRIDE_PORT=587
SMTP_OVERRIDE_USER=tu_email@gmail.com
SMTP_OVERRIDE_PASSWORD=tu_app_password
SMTP_OVERRIDE_TLS=true
```

### 3. Outlook/Office365 SMTP

```bash
SMTP_OVERRIDE_SERVER=smtp.office365.com
SMTP_OVERRIDE_PORT=587
SMTP_OVERRIDE_USER=tu_email@empresa.com
SMTP_OVERRIDE_PASSWORD=tu_contraseña
SMTP_OVERRIDE_TLS=true
```

## Comportamiento

1. **Sin variables de sobrescritura**: Usa la configuración SMTP por defecto según el entorno (local/oficina)
2. **Con variables de sobrescritura**: Ignora la configuración por defecto y usa los valores de sobrescritura
3. **Autenticación automática**: Si se proporciona `SMTP_OVERRIDE_USER`, se activa automáticamente la autenticación

## Prioridad de Configuración

1. **Variables de sobrescritura** (`SMTP_OVERRIDE_*`) - Máxima prioridad
2. **Variables de entorno** (`LOCAL_SMTP_*` o `OFFICE_SMTP_*`) - Según entorno
3. **Valores por defecto** - Si no hay variables configuradas

## Casos de Uso

### Escenario 1: Desarrollo Local
- Usar servidor SMTP local (MailHog, etc.)
- No requiere autenticación
- Para testing de funcionalidad

### Escenario 2: Oficina - Máquina sin acceso SMTP
- Usar Gmail o Outlook personal
- Requiere autenticación
- Para envío real de correos

### Escenario 3: Oficina - Máquina con acceso SMTP
- No usar sobrescritura
- Usar servidor de oficina por defecto
- Sin autenticación

## Verificación de Configuración

Ejecuta el script de demostración para verificar tu configuración:

```bash
python examples/smtp_override_demo.py
```

Este script mostrará:
- Configuración SMTP actual
- Cómo aplicar sobrescritura
- Configuración resultante

## Notas de Seguridad

- **No commits credenciales**: Nunca hagas commit de contraseñas reales en el archivo `.env`
- **Variables locales**: Usa variables de entorno del sistema para credenciales sensibles
- **App passwords**: Para Gmail/Outlook, usa contraseñas de aplicación específicas

## Troubleshooting

### Error: "Authentication failed"
- Verifica usuario y contraseña
- Para Gmail: usa contraseña de aplicación, no la contraseña normal
- Para Outlook: habilita autenticación de aplicaciones menos seguras

### Error: "Connection refused"
- Verifica servidor y puerto
- Comprueba firewall/proxy
- Para Gmail: usa puerto 587 con TLS

### Error: "TLS required"
- Configura `SMTP_OVERRIDE_TLS=true`
- Usa puerto 587 en lugar de 25