# Docker - Guía Completa

## 🚀 Inicio Rápido

### Instalación automática
```bash
# Ejecutar script de instalación
python setup.py

# Seleccionar opción 1 (Docker) cuando aparezca el menú
```

### Instalación manual
```bash
# 1. Construir imágenes
docker-compose build

# 2. Iniciar sistema
docker-compose up -d app

# 3. Abrir navegador
# http://localhost:8888
```

## 🛠️ Scripts de Gestión

### Linux/macOS
```bash
# Hacer ejecutable
chmod +x docker-run.sh

# Usar comandos
./docker-run.sh start
./docker-run.sh test
./docker-run.sh panel
```

### Windows
```batch
# Usar directamente
docker-run.bat start
docker-run.bat test
docker-run.bat panel
```

## 📋 Comandos Disponibles

### 🚀 Gestión del Sistema
| Comando | Descripción | Equivalente Docker |
|---------|-------------|-------------------|
| `start` | Iniciar sistema completo | `docker-compose up -d app` |
| `stop` | Detener sistema | `docker-compose down` |
| `restart` | Reiniciar sistema | `docker-compose restart app` |
| `status` | Ver estado contenedores | `docker-compose ps` |
| `logs` | Ver logs en tiempo real | `docker-compose logs -f app` |

### 🧪 Testing
| Comando | Descripción | Resultado |
|---------|-------------|-----------|
| `test` | Todos los tests | 49 tests + cobertura |
| `test-unit` | Solo tests unitarios | 45 tests unitarios |
| `test-integration` | Solo tests integración | 4 tests con BD |
| `test-coverage` | Tests + reporte HTML | htmlcov/index.html |

### 🔧 Desarrollo
| Comando | Descripción | Puerto |
|---------|-------------|---------|
| `dev` | Entorno desarrollo | 8889 |
| `build` | Construir imágenes | - |
| `clean` | Limpiar Docker | - |

### 🌐 Acceso y Utilidades
| Comando | Descripción | Acción |
|---------|-------------|---------|
| `panel` | Abrir panel web | Abre navegador |
| `shell` | Acceder container | Bash interactivo |
| `brass` | Ejecutar BRASS | Proceso completo |
| `backup` | Backup de BD | Copia timestamped |

## 🏗️ Arquitectura Docker

### Servicios Definidos

#### Aplicación Principal (`app`)
```yaml
Imagen: Dockerfile
Puerto: 8888
Volúmenes:
  - dbs-locales (solo lectura)
  - herramientas (solo lectura)
  - logs (persistente)
  - htmlcov (persistente)
  - .env (configuración)
```

#### Desarrollo (`dev`)
```yaml
Imagen: Dockerfile.dev
Puerto: 8889
Profile: dev
Características:
  - Código montado como volumen
  - Herramientas de desarrollo
  - Recarga automática
```

#### Tests (`tests`)
```yaml
Imagen: Dockerfile
Profile: tests
Propósito: Ejecución on-demand de tests
Salida: Reportes y cobertura
```

## 🔧 Configuración

### Variables de Entorno
```bash
# En docker-compose.yml
ENVIRONMENT=local          # local/oficina
DB_PASSWORD=dpddpd        # Contraseña BD
LOG_LEVEL=INFO            # DEBUG/INFO/ERROR
PYTHONUNBUFFERED=1        # Sin buffer Python
```

### Volúmenes Persistentes
```bash
./logs:/app/logs                    # Logs del sistema
./htmlcov:/app/htmlcov              # Reportes cobertura
./dbs-locales:/app/dbs-locales:ro   # Bases datos locales
./.env:/app/.env:ro                 # Variables entorno
```

### Mapeo de Puertos
```bash
8888:8888    # Aplicación principal
8889:8888    # Entorno desarrollo (opcional)
```

## 🚀 Casos de Uso

### Desarrollo Diario
```bash
# 1. Iniciar entorno
./docker-run.sh dev

# 2. Ejecutar tests
./docker-run.sh test-unit

# 3. Probar módulo
./docker-run.sh brass

# 4. Ver logs
./docker-run.sh logs
```

### Testing Completo
```bash
# 1. Tests unitarios
./docker-run.sh test-unit

# 2. Tests integración
./docker-run.sh test-integration

# 3. Cobertura completa
./docker-run.sh test-coverage

# 4. Ver reporte: htmlcov/index.html
```

### Producción Local
```bash
# 1. Construir imágenes
./docker-run.sh build

# 2. Iniciar sistema
./docker-run.sh start

# 3. Verificar estado
./docker-run.sh status

# 4. Abrir panel
./docker-run.sh panel
```

### Debugging
```bash
# 1. Acceder al container
./docker-run.sh shell

# 2. Ejecutar comandos internos
python run_brass.py
pytest tests/unit/brass/ -v -s

# 3. Ver archivos de log
tail -f logs/brass.log

# 4. Verificar configuración
cat .env
```

## 🔒 Seguridad

### Usuario No-Root
- Container ejecuta como usuario `app`
- Sin privilegios administrativos
- Directorio home propio

### Red Aislada
- Red bridge personalizada
- Solo puertos necesarios expuestos
- Sin acceso a red host por defecto

### Volúmenes de Solo Lectura
- Bases de datos: read-only
- Configuración: read-only
- Solo logs y reportes son escritos

## 📊 Monitoreo

### Health Checks
```bash
# Automático cada 30s
curl -f http://localhost:8888/api/status

# Manual
./docker-run.sh status
```

### Logs Centralizados
```bash
# Logs en tiempo real
./docker-run.sh logs

# Logs específicos
docker-compose logs app --tail=100
```

### Métricas de Resource
```bash
# Stats de contenedores
docker stats gestion-tareas-app

# Uso de volúmenes
docker system df
```

## 🧹 Mantenimiento

### Limpieza Regular
```bash
# Limpiar proyecto específico
./docker-run.sh clean

# Limpiar sistema Docker
docker system prune -f

# Limpiar volúmenes no utilizados
docker volume prune -f
```

### Backup y Restauración
```bash
# Backup automático
./docker-run.sh backup

# Backup manual con timestamp
docker-compose exec app tar -czf backup_$(date +%Y%m%d).tar.gz dbs-locales logs

# Restaurar desde backup
tar -xzf backup_20250122.tar.gz
```

### Actualización de Imágenes
```bash
# 1. Detener sistema
./docker-run.sh stop

# 2. Reconstruir imágenes
./docker-run.sh build

# 3. Reiniciar
./docker-run.sh start
```

## 🆚 Docker vs Nativo

### Ventajas Docker
- ✅ Entorno consistente entre máquinas
- ✅ Aislamiento de dependencias
- ✅ Fácil limpieza y reset
- ✅ Scripts de gestión integrados
- ✅ Health checks automáticos

### Ventajas Nativo
- ✅ Acceso directo al filesystem
- ✅ Menor uso de recursos
- ✅ Debugging más directo
- ✅ Sin dependencia de Docker
- ✅ Integración IDE más fácil

### Recomendación
- **Docker**: Para producción y testing automatizado
- **Nativo**: Para desarrollo intensivo y debugging
