#!/bin/bash
# Script para gestionar el sistema con Docker
# Uso: ./docker-run.sh [comando]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de utilidad
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "🐳 Sistema de Gestión de Tareas - Docker"
    echo "========================================"
    echo -e "${NC}"
}

# Verificar que Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado o no está en el PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker no está ejecutándose o no tienes permisos"
        exit 1
    fi
}

# Mostrar ayuda
show_help() {
    print_header
    echo "Comandos disponibles:"
    echo ""
    echo "🚀 Gestión del Sistema:"
    echo "  start          - Iniciar el sistema completo"
    echo "  stop           - Detener el sistema"
    echo "  restart        - Reiniciar el sistema"
    echo "  status         - Ver estado de los contenedores"
    echo "  logs           - Ver logs del sistema"
    echo ""
    echo "🧪 Testing:"
    echo "  test           - Ejecutar todos los tests"
    echo "  test-unit      - Ejecutar solo tests unitarios"
    echo "  test-integration - Ejecutar solo tests de integración"
    echo "  test-coverage  - Ejecutar tests con reporte de cobertura"
    echo ""
    echo "🔧 Desarrollo:"
    echo "  dev            - Iniciar entorno de desarrollo"
    echo "  build          - Construir imágenes Docker"
    echo "  clean          - Limpiar contenedores e imágenes"
    echo ""
    echo "🌐 Acceso:"
    echo "  panel          - Abrir panel de control en navegador"
    echo "  shell          - Acceder al shell del contenedor"
    echo ""
    echo "📊 Utilidades:"
    echo "  brass          - Ejecutar módulo BRASS"
    echo "  backup         - Hacer backup de bases de datos"
    echo ""
}

# Funciones principales
start_system() {
    print_info "Iniciando sistema..."
    docker-compose up -d app
    print_success "Sistema iniciado en http://localhost:8888"
}

stop_system() {
    print_info "Deteniendo sistema..."
    docker-compose down
    print_success "Sistema detenido"
}

restart_system() {
    print_info "Reiniciando sistema..."
    docker-compose restart app
    print_success "Sistema reiniciado"
}

show_status() {
    print_info "Estado de los contenedores:"
    docker-compose ps
}

show_logs() {
    print_info "Logs del sistema (Ctrl+C para salir):"
    docker-compose logs -f app
}

run_tests() {
    print_info "Ejecutando todos los tests..."
    docker-compose run --rm tests
    print_success "Tests completados"
}

run_unit_tests() {
    print_info "Ejecutando tests unitarios..."
    docker-compose run --rm tests python -m pytest tests/unit/ -v
    print_success "Tests unitarios completados"
}

run_integration_tests() {
    print_info "Ejecutando tests de integración..."
    docker-compose run --rm tests python -m pytest tests/integration/ -v
    print_success "Tests de integración completados"
}

run_coverage_tests() {
    print_info "Ejecutando tests con cobertura..."
    docker-compose run --rm tests python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
    print_success "Tests con cobertura completados. Ver htmlcov/index.html"
}

start_dev() {
    print_info "Iniciando entorno de desarrollo..."
    docker-compose --profile dev up -d dev
    print_success "Entorno de desarrollo iniciado en http://localhost:8889"
}

build_images() {
    print_info "Construyendo imágenes Docker..."
    docker-compose build
    print_success "Imágenes construidas"
}

clean_docker() {
    print_warning "Esto eliminará contenedores e imágenes del proyecto"
    read -p "¿Continuar? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Limpiando Docker..."
        docker-compose down --rmi all --volumes --remove-orphans
        print_success "Limpieza completada"
    else
        print_info "Limpieza cancelada"
    fi
}

open_panel() {
    print_info "Abriendo panel de control..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8888
    elif command -v open &> /dev/null; then
        open http://localhost:8888
    elif command -v start &> /dev/null; then
        start http://localhost:8888
    else
        print_warning "No se pudo abrir automáticamente. Visita: http://localhost:8888"
    fi
}

access_shell() {
    print_info "Accediendo al shell del contenedor..."
    docker-compose exec app bash
}

run_brass() {
    print_info "Ejecutando módulo BRASS..."
    docker-compose exec app python run_brass.py
    print_success "Módulo BRASS ejecutado"
}

backup_databases() {
    print_info "Creando backup de bases de datos..."
    BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    docker-compose exec app cp -r dbs-locales "/app/$BACKUP_DIR/"
    print_success "Backup creado en $BACKUP_DIR"
}

# Función principal
main() {
    print_header
    check_docker
    
    case "${1:-help}" in
        "start")
            start_system
            ;;
        "stop")
            stop_system
            ;;
        "restart")
            restart_system
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "test")
            run_tests
            ;;
        "test-unit")
            run_unit_tests
            ;;
        "test-integration")
            run_integration_tests
            ;;
        "test-coverage")
            run_coverage_tests
            ;;
        "dev")
            start_dev
            ;;
        "build")
            build_images
            ;;
        "clean")
            clean_docker
            ;;
        "panel")
            open_panel
            ;;
        "shell")
            access_shell
            ;;
        "brass")
            run_brass
            ;;
        "backup")
            backup_databases
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Ejecutar función principal
main "$@"
