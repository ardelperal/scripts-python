# Tests de Sistema de Correos

Este directorio contiene todas las pruebas relacionadas con el envío de correos electrónicos.

## Archivos

### Pruebas con MailHog
- `test_correos_mailhog.py` - **⭐ TEST PRINCIPAL** - Envío de correos HTML a MailHog
- `setup_smtp_local.py` - Configuración de servidor SMTP local

### Pruebas Básicas
- `test_email_simple.py` - Prueba básica de envío de correos
- `create_test_emails.py` - Creador de correos de prueba

## Uso

### Probar Envío de Correos HTML
```bash
# 1. Iniciar MailHog
docker-compose up -d

# 2. Ejecutar test
python tests/emails/test_correos_mailhog.py

# 3. Ver correos en http://localhost:8025
```

### Test Básico
```bash
python tests/emails/test_email_simple.py
```

## Configuración

### MailHog (Recomendado)
- **SMTP**: localhost:1025
- **Web UI**: http://localhost:8025
- **Docker**: `docker-compose up -d`

### Variables de Entorno
```env
SMTP_USE_LOCAL=true
SMTP_SERVER=localhost
SMTP_PORT=1025
```

## Funcionalidades Probadas

✅ **Envío HTML**: Correos con estilos CSS completos
✅ **Múltiples Destinatarios**: Para, CC, CCO
✅ **Codificación**: UTF-8 correcta 
✅ **Responsive**: CSS que funciona en clientes de correo
✅ **MailHog**: Interceptación y visualización local

## Resultados Esperados

- 📧 Correos enviados exitosamente
- 🎨 HTML renderizado correctamente  
- 📱 Estilos CSS aplicados
- 🔍 Visible en MailHog UI
