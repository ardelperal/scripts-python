# 🐳 Sistema de Gestión de Tareas - Docker Edition

> **Migración completa de VBS legacy a Python moderno con Docker**

## 🚀 Inicio Rápido (5 minutos)

### Opción 1: Script Automático
```bash
python setup.py
# Seleccionar "1" para Docker
```

### Opción 2: Manual
```bash
# 1. Construir
docker-compose build

# 2. Iniciar
docker-compose up -d app

# 3. Abrir: http://localhost:8888
```

## 🎯 Lo Que Obtienes

### ✅ Sistema Completo Dockerizado
- **BRASS**: Gestión de calibraciones completa
- **Panel Web**: Control centralizado HTML5
- **Tests**: 49 tests automatizados con 63% cobertura
- **Multi-entorno**: LOCAL y OFICINA configurables
- **Logs**: Monitoreo completo
- **Health Checks**: Supervisión automática

### 🛠️ Herramientas Incluidas
- Python 3.11 + todas las dependencias
- Base de datos ODBC integrada
- Servidor HTTP con API REST
- Sistema de testing completo
- Reportes HTML automáticos

## 📋 Scripts de Gestión

### Windows
```batch
docker-run.bat start     # Iniciar sistema
docker-run.bat test      # Ejecutar todos los tests
docker-run.bat panel     # Abrir panel web
docker-run.bat status    # Ver estado
docker-run.bat logs      # Ver logs en tiempo real
docker-run.bat stop      # Detener sistema
```

### Linux/macOS
```bash
./docker-run.sh start    # Iniciar sistema
./docker-run.sh test     # Ejecutar todos los tests
./docker-run.sh panel    # Abrir panel web
./docker-run.sh status   # Ver estado
./docker-run.sh logs     # Ver logs en tiempo real
./docker-run.sh stop     # Detener sistema
```

## 🌟 Características Destacadas

### 🔄 Dual Mode: Docker + Nativo
- **Docker**: Para producción y despliegue
- **Nativo**: Para desarrollo intensivo
- Misma base de código, diferentes entornos

### 🎛️ Panel de Control Web
- Ejecutar módulos con un clic
- Ver logs en tiempo real
- Ejecutar tests individuales
- Monitoreo de estado del sistema

### 🧪 Testing Robusto
- Tests unitarios para cada módulo
- Tests de integración con BD
- Reportes de cobertura HTML
- Ejecución en contenedores aislados

### 🔧 Multi-Entorno
```bash
# Archivo .env
ENVIRONMENT=local           # o 'oficina'
DB_PASSWORD=dpddpd
LOG_LEVEL=INFO
```

## 📊 Servicios Docker

### App Principal (Puerto 8888)
- Aplicación completa en producción
- Health checks automáticos
- Volúmenes persistentes para logs
- Acceso de solo lectura a BD

### Desarrollo (Puerto 8889)
- Entorno de desarrollo con hot-reload
- Código montado como volumen
- Herramientas adicionales de debug

### Tests On-Demand
- Contenedor específico para testing
- Aislamiento completo de dependencias
- Reportes automáticos

## 🗂️ Estructura del Proyecto

```
scripts-python/
├── 🐳 Docker Files
│   ├── Dockerfile              # Imagen producción
│   ├── Dockerfile.dev          # Imagen desarrollo
│   ├── docker-compose.yml      # Orquestación
│   ├── .dockerignore          # Exclusiones
│   ├── docker-run.sh          # Scripts Linux
│   └── docker-run.bat         # Scripts Windows
│
├── 📁 Código Fuente
│   ├── src/
│   │   ├── brass/             # Módulo BRASS migrado
│   │   ├── common/            # Utilidades compartidas
│   │   └── __init__.py
│   ├── tests/                 # Suite de tests completa
│   ├── server.py             # Servidor web
│   └── panel_control.html    # Interface web
│
├── 📊 Datos y Configuración
│   ├── dbs-locales/          # Bases datos Access
│   ├── herramientas/         # Archivos auxiliares
│   ├── .env                  # Variables entorno
│   └── requirements.txt      # Dependencias Python
│
└── 📚 Documentación
    ├── docs/
    │   ├── docker_guia.md     # Guía completa Docker
    │   └── README.md          # Documentación general
    └── README_docker.md       # Este archivo
```

## 🔒 Seguridad y Mejores Prácticas

### 🛡️ Aislamiento
- Usuario no-root en contenedores
- Red aislada con puertos específicos
- Volúmenes de solo lectura para datos

### 📋 Monitoreo
- Health checks automáticos cada 30s
- Logs centralizados en `./logs/`
- Métricas de recursos disponibles

### 🧹 Mantenimiento
- Script de limpieza integrado
- Backup automático de datos
- Rotación de logs configurable

## 🆚 Comparación Docker vs Nativo

| Aspecto | Docker | Nativo |
|---------|--------|--------|
| **Instalación** | Un comando | Manual compleja |
| **Consistencia** | ✅ Garantizada | ⚠️ Depende del sistema |
| **Aislamiento** | ✅ Completo | ❌ Sistema global |
| **Recursos** | ⚠️ Overhead mínimo | ✅ Acceso directo |
| **Debugging** | ⚠️ Pasos extra | ✅ Directo |
| **Limpieza** | ✅ Un comando | ❌ Manual |
| **Despliegue** | ✅ Portátil | ⚠️ Configuración manual |

## 🚀 Casos de Uso Típicos

### Desarrollo Diario
```bash
# Modo desarrollo con hot-reload
docker-run.bat dev

# Ejecutar tests unitarios rápidos
docker-run.bat test-unit

# Ver logs en tiempo real
docker-run.bat logs
```

### Testing y QA
```bash
# Suite completa de tests
docker-run.bat test

# Solo tests de integración
docker-run.bat test-integration

# Generar reporte de cobertura
docker-run.bat test-coverage
```

### Producción Local
```bash
# Iniciar sistema completo
docker-run.bat start

# Verificar que todo funciona
docker-run.bat status

# Abrir panel de control
docker-run.bat panel
```

### Mantenimiento
```bash
# Backup de datos
docker-run.bat backup

# Limpiar Docker
docker-run.bat clean

# Reiniciar sistema
docker-run.bat restart
```

## 🔧 Configuración Avanzada

### Variables de Entorno Personalizadas
```bash
# En docker-compose.yml
environment:
  - ENVIRONMENT=oficina
  - DB_PASSWORD=tu_password
  - LOG_LEVEL=DEBUG
  - CUSTOM_PORT=9999
```

### Volúmenes Adicionales
```yaml
volumes:
  - ./custom-data:/app/custom-data
  - ./extra-tools:/app/tools:ro
```

### Red Personalizada
```yaml
networks:
  gestion-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🆘 Troubleshooting

### Problemas Comunes

#### Puerto 8888 en Uso
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8889:8888"  # Usar 8889 en lugar de 8888
```

#### Permisos de Archivos
```bash
# En Windows/Linux
docker-run.bat shell
chown app:app /app/logs
```

#### Base de Datos No Accesible
```bash
# Verificar mounting de volúmenes
docker-compose config
```

#### Tests Fallan
```bash
# Ejecutar en modo verbose
docker-compose run --rm tests pytest -v -s
```

### Logs de Diagnóstico
```bash
# Logs detallados del sistema
docker-run.bat logs

# Logs específicos de un servicio
docker-compose logs app --tail=100

# Entrar al contenedor para debug
docker-run.bat shell
```

## 📞 Soporte

### Comandos de Diagnóstico
```bash
# Verificar estado completo
docker-run.bat status

# Información del sistema
docker system info

# Uso de recursos
docker stats gestion-tareas-app
```

### Reportar Problemas
1. Ejecutar `docker-run.bat logs > debug.log`
2. Adjuntar `debug.log` junto con:
   - Versión de Docker
   - Sistema operativo
   - Comando que falló
   - Mensaje de error completo

---

## 🏆 Migración Exitosa Completada

✅ **Legacy VBS → Python Moderno**  
✅ **Sistema Robusto con Testing**  
✅ **Multi-entorno (Local/Oficina)**  
✅ **Panel Web de Control**  
✅ **Dockerización Completa**  
✅ **Compatibilidad Nativa Mantenida**

**🎯 Objetivo Cumplido: Sistema profesional, testeable y desplegable en cualquier entorno**
