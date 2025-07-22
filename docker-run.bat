@echo off
REM Script para gestionar el sistema con Docker en Windows
REM Uso: docker-run.bat [comando]

setlocal EnableDelayedExpansion

REM Configuración de colores (limitada en CMD)
set "INFO=echo [INFO]"
set "SUCCESS=echo [SUCCESS]"
set "WARNING=echo [WARNING]"
set "ERROR=echo [ERROR]"

REM Función para mostrar header
call :print_header

REM Verificar Docker
call :check_docker
if errorlevel 1 exit /b 1

REM Procesar comando
set "CMD=%~1"
if "%CMD%"=="" set "CMD=help"

if "%CMD%"=="start" call :start_system
if "%CMD%"=="stop" call :stop_system
if "%CMD%"=="restart" call :restart_system
if "%CMD%"=="status" call :show_status
if "%CMD%"=="logs" call :show_logs
if "%CMD%"=="test" call :run_tests
if "%CMD%"=="test-unit" call :run_unit_tests
if "%CMD%"=="test-integration" call :run_integration_tests
if "%CMD%"=="test-coverage" call :run_coverage_tests
if "%CMD%"=="dev" call :start_dev
if "%CMD%"=="build" call :build_images
if "%CMD%"=="clean" call :clean_docker
if "%CMD%"=="panel" call :open_panel
if "%CMD%"=="shell" call :access_shell
if "%CMD%"=="brass" call :run_brass
if "%CMD%"=="backup" call :backup_databases
if "%CMD%"=="help" call :show_help

goto :eof

:print_header
echo.
echo 🐳 Sistema de Gestión de Tareas - Docker
echo ========================================
echo.
goto :eof

:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    %ERROR% Docker no está instalado o no está en el PATH
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    %ERROR% Docker no está ejecutándose o no tienes permisos
    exit /b 1
)
goto :eof

:show_help
echo Comandos disponibles:
echo.
echo 🚀 Gestión del Sistema:
echo   start          - Iniciar el sistema completo
echo   stop           - Detener el sistema
echo   restart        - Reiniciar el sistema
echo   status         - Ver estado de los contenedores
echo   logs           - Ver logs del sistema
echo.
echo 🧪 Testing:
echo   test           - Ejecutar todos los tests
echo   test-unit      - Ejecutar solo tests unitarios
echo   test-integration - Ejecutar solo tests de integración
echo   test-coverage  - Ejecutar tests con reporte de cobertura
echo.
echo 🔧 Desarrollo:
echo   dev            - Iniciar entorno de desarrollo
echo   build          - Construir imágenes Docker
echo   clean          - Limpiar contenedores e imágenes
echo.
echo 🌐 Acceso:
echo   panel          - Abrir panel de control en navegador
echo   shell          - Acceder al shell del contenedor
echo.
echo 📊 Utilidades:
echo   brass          - Ejecutar módulo BRASS
echo   backup         - Hacer backup de bases de datos
echo.
goto :eof

:start_system
%INFO% Iniciando sistema...
docker-compose up -d app
%SUCCESS% Sistema iniciado en http://localhost:8888
goto :eof

:stop_system
%INFO% Deteniendo sistema...
docker-compose down
%SUCCESS% Sistema detenido
goto :eof

:restart_system
%INFO% Reiniciando sistema...
docker-compose restart app
%SUCCESS% Sistema reiniciado
goto :eof

:show_status
%INFO% Estado de los contenedores:
docker-compose ps
goto :eof

:show_logs
%INFO% Logs del sistema (Ctrl+C para salir):
docker-compose logs -f app
goto :eof

:run_tests
%INFO% Ejecutando todos los tests...
docker-compose run --rm tests
%SUCCESS% Tests completados
goto :eof

:run_unit_tests
%INFO% Ejecutando tests unitarios...
docker-compose run --rm tests python -m pytest tests/unit/ -v
%SUCCESS% Tests unitarios completados
goto :eof

:run_integration_tests
%INFO% Ejecutando tests de integración...
docker-compose run --rm tests python -m pytest tests/integration/ -v
%SUCCESS% Tests de integración completados
goto :eof

:run_coverage_tests
%INFO% Ejecutando tests con cobertura...
docker-compose run --rm tests python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
%SUCCESS% Tests con cobertura completados. Ver htmlcov/index.html
goto :eof

:start_dev
%INFO% Iniciando entorno de desarrollo...
docker-compose --profile dev up -d dev
%SUCCESS% Entorno de desarrollo iniciado en http://localhost:8889
goto :eof

:build_images
%INFO% Construyendo imágenes Docker...
docker-compose build
%SUCCESS% Imágenes construidas
goto :eof

:clean_docker
%WARNING% Esto eliminará contenedores e imágenes del proyecto
set /p "REPLY=¿Continuar? (y/N): "
if /i "%REPLY%"=="y" (
    %INFO% Limpiando Docker...
    docker-compose down --rmi all --volumes --remove-orphans
    %SUCCESS% Limpieza completada
) else (
    %INFO% Limpieza cancelada
)
goto :eof

:open_panel
%INFO% Abriendo panel de control...
start http://localhost:8888
goto :eof

:access_shell
%INFO% Accediendo al shell del contenedor...
docker-compose exec app bash
goto :eof

:run_brass
%INFO% Ejecutando módulo BRASS...
docker-compose exec app python run_brass.py
%SUCCESS% Módulo BRASS ejecutado
goto :eof

:backup_databases
%INFO% Creando backup de bases de datos...
set "BACKUP_DIR=backup\%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BACKUP_DIR=%BACKUP_DIR: =0%"
mkdir "%BACKUP_DIR%" 2>nul
docker-compose exec app cp -r dbs-locales "/app/%BACKUP_DIR%/"
%SUCCESS% Backup creado en %BACKUP_DIR%
goto :eof
