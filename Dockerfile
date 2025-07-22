# Dockerfile para Sistema de Gestión de Tareas
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Sistema de Gestión de Tareas"
LABEL description="Migración VBS a Python con Panel de Control Web"
LABEL version="1.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=local
ENV FLASK_ENV=production

# Crear usuario no-root por seguridad
RUN useradd --create-home --shell /bin/bash app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # Para ODBC Access (si se necesita en producción)
    unixodbc \
    unixodbc-dev \
    # Para compilar algunas dependencias Python
    gcc \
    g++ \
    # Utilidades básicas
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs htmlcov static

# Cambiar ownership a usuario app
RUN chown -R app:app /app

# Cambiar a usuario no-root
USER app

# Exponer puerto del servidor web
EXPOSE 8888

# Comando por defecto - servidor web
CMD ["python", "server.py"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/api/status || exit 1
