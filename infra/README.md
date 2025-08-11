# Infraestructura de Observabilidad y Análisis

Este directorio agrupa todos los recursos auxiliares (no de negocio) relacionados con monitorización, logging centralizado y análisis de código.

## Componentes

| Componente | Ruta | Propósito |
|------------|------|-----------|
| Loki | `infra/loki/` | Almacenamiento de logs (back-end). |
| Grafana | `infra/grafana/` | Visualización de dashboards y exploración de logs. |
| Promtail | `infra/promtail/` | Agente que lee los logs locales y los envía a Loki. |
| SonarQube | (contenedor) | Análisis estático de calidad de código. |
| code-analyzer | `infra/analysis/Dockerfile` | Contenedor auxiliar para lanzar análisis (ej. Sonar scanner). |

## Requisitos Previos
- Docker + Docker Compose instalados.
- Puerto disponibles: 3000 (Grafana), 3100 (Loki), 9000 (SonarQube), 9080 (Promtail HTTP interno opcional).

## Estructura de Rutas en docker-compose
`docker-compose.yml` en la raíz referencia ahora las rutas dentro de `infra/`:
- Loki config: `./infra/loki/loki-config.yml:/etc/loki/local-config.yaml`
- Grafana provisioning: `./infra/grafana/provisioning:/etc/grafana/provisioning`
- Promtail config: `./infra/promtail/promtail-config.yml:/etc/promtail/config.yml`

Los logs de la aplicación se escriben en `logs/app.log` y se montan en el contenedor de Promtail vía `./logs:/var/log/app`.

## Puesta en Marcha
Desde la raíz del proyecto:

```powershell
# Arrancar stack de observabilidad y análisis
docker compose up -d loki grafana promtail

# (Opcional) Sonar + code analyzer
docker compose up -d sonarqube
# Esperar unos segundos a que inicialice SonarQube antes de usar el analizador
```

Verificar estado:
```powershell
docker compose ps
```

## Accesos Web
- Grafana: http://localhost:3000  (usuario: admin / contraseña inicial: Arm1833a)
- SonarQube: http://localhost:9000

## Dashboards y Logs
En Grafana:
1. Añadir Loki como data source si no aparece (URL: `http://loki:3100`).
2. Explorar logs (Explore) filtrando por etiqueta `job="scripts-python"`.

## Ajustes Promtail
Archivo: `infra/promtail/promtail-config.yml`
- Cambiar glob de rutas si añades nuevos archivos de log.
- Añadir labels adicionales para separar entornos (`environment`, etc.).

Ejemplo de ampliación de `scrape_configs`:
```yaml
scrape_configs:
  - job_name: app_logs
    static_configs:
      - targets: [localhost]
        labels:
          job: scripts-python
          environment: local
          __path__: /var/log/app/*.log
```

## Análisis de Código (SonarQube)
1. Exportar token en variable de entorno: `SONAR_TOKEN`.
2. Levantar SonarQube (ver pasos arriba).
3. (Pendiente) Integrar scanner dentro de `code-analyzer` (ver Dockerfile base en `infra/analysis/`).

## Mantenimiento
- Limpiar contenedores/parar stack: `docker compose down`.
- Actualizar imágenes: `docker compose pull`.
- Limpiar volúmenes (destruye datos persistentes): `docker compose down -v`.

## Seguridad / Producción
- Cambiar credenciales por defecto de Grafana.
- Restringir puertos expuestos si se despliega fuera de entorno controlado.
- Aplicar backups a volúmenes si se desea conservar dashboards y datos.

## Roadmap Opcional
- Añadir alertas (Alerting en Grafana o Loki Ruler).
- Integrar métricas (Prometheus) si se requiere más adelante.
- Pipeline CI para subir resultados de análisis automáticamente.

---
Este directorio es independiente de la lógica de negocio: moverlo o modificarlo no afecta la ejecución de `run_master.py` salvo la parte de logging centralizado.
