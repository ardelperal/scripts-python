# Usar una imagen base de Python
FROM python:3.9-slim

# Variables de entorno para las versiones de las herramientas
ENV SONAR_SCANNER_VERSION=4.7.0.2747
ENV DEPENDENCY_CHECK_VERSION=7.1.1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    unzip \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# Instalar SonarScanner
RUN apt-get update && apt-get install -y wget && \
    wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip && \
    unzip sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip && \
    mv sonar-scanner-${SONAR_SCANNER_VERSION}-linux /opt/sonar-scanner && \
    rm sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux.zip
ENV PATH="/opt/sonar-scanner/bin:${PATH}"

# Instalar OWASP Dependency-Check
RUN wget https://github.com/jeremylong/DependencyCheck/releases/download/v${DEPENDENCY_CHECK_VERSION}/dependency-check-${DEPENDENCY_CHECK_VERSION}-release.zip && \
    unzip dependency-check-${DEPENDENCY_CHECK_VERSION}-release.zip && \
    mv dependency-check /opt/dependency-check && \
    rm dependency-check-${DEPENDENCY_CHECK_VERSION}-release.zip
ENV PATH="/opt/dependency-check/bin:${PATH}"

# Establecer el directorio de trabajo
WORKDIR /usr/src

# --- CORRECCIÓN AÑADIDA AQUÍ ---
# Copiar el script de análisis desde su ubicación correcta (analysis/run-analysis.sh)
COPY analysis/run-analysis.sh .
RUN chmod +x run-analysis.sh

# Comando por defecto que se ejecutará al iniciar el contenedor
CMD ["./run-analysis.sh"]
