# Dockerfile para solución ligera con SQLite
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Scripts Python - Access to SQLite Migration"
LABEL description="Lightweight Docker image with Access database migration to SQLite"

# Instalar herramientas del sistema necesarias
RUN apt-get update && apt-get install -y \
    # Herramientas básicas
    curl \
    git \
    # mdbtools para leer Access en Linux
    mdbtools \
    # Herramientas de desarrollo (opcional para debug)
    nano \
    # Limpiar cache
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt ./requirements.txt

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias adicionales para migración
RUN pip install --no-cache-dir pandas || echo "pandas ya instalado"

# Nota: sqlite3 viene incluido con Python

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p dbs-sqlite logs

# Ejecutar migración/creación de bases de datos durante el build
RUN python create_demo_databases.py || echo "Bases de datos demo creadas"

# Script para la migración real si hay archivos Access disponibles
RUN python migrate_databases.py || echo "No hay archivos Access para migrar - usando datos demo"

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 5000

# Variables de entorno
ENV PYTHONPATH=/app/src:/app
ENV FLASK_APP=server.py
ENV FLASK_ENV=production
ENV DATABASE_MODE=sqlite
ENV ENVIRONMENT=docker
ENV DOCKER_CONTAINER=true

# Comando por defecto - ejecutar scripts de forma continua
CMD ["python", "continuous_runner.py"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/status || exit 1
