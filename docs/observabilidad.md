## Observabilidad: métricas, correlación y logging

Este documento explica cómo aprovechar la observabilidad integrada del backend:

- Correlación por request con cabecera X-Request-ID
- Métricas en formato Prometheus en `/metrics` (con fallback seguro)
- Logging estructurado en JSON para cada request


### Componentes incluidos

- Middleware HTTP (en `app/main.py`):
  - Genera/propaga `X-Request-ID`.
  - Mide la duración del request con alta resolución.
  - Publica métricas HTTP y emite un log JSON por request.
- Módulo de métricas (`app/metrics.py`):
  - Integra opcionalmente con `prometheus_client` si está instalado.
  - Métricas disponibles:
    - `http_requests_total{method, path, status}` (Counter)
    - `http_request_duration_seconds{method, path}` (Histogram)
    - `audit_events_total{tipo, severidad}` (Counter)
- Servicio de auditoría (`app/services/audit_service.py`):
  - Incrementa `audit_events_total` por cada evento registrado.


## Habilitar métricas de Prometheus

Sin instalar dependencias extra, `/metrics` responde un mensaje de fallback. Para habilitar métricas reales:

Opcional (documentación):
```
pip install prometheus-client
```

Luego visita `http://localhost:8000/metrics`. Deberías ver líneas que comienzan con `# HELP` / `# TYPE` y series como:

```
http_requests_total{method="GET",path="/api/miembros",status="200"} 42
```

Notas:
- La etiqueta `path` intenta usar la ruta "templated" (por ejemplo, `/api/miembros/{miembro_id}`) para evitar cardinalidad alta.
- Los buckets del histograma están definidos en segundos: `(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)`.


## Configuración de Prometheus (scrape)

Ejemplo de `prometheus.yml` para scrappear el backend local:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "socios-backend"
    static_configs:
      - targets: ["host.docker.internal:8000"]  # si Prometheus corre en Docker en Windows
        labels:
          app: "socios-backend"
```

Alternativas de `targets` según tu entorno:
- Prometheus y backend en la misma máquina (host): `"localhost:8000"`.
- Ambos en Docker, misma red: usar el nombre de servicio del backend.


## Consultas PromQL útiles

- Requests por segundo por estado (promedio 5m):
```
sum by (status) (rate(http_requests_total[5m]))
```

- Error rate (5xx) de toda la API (5m):
```
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m]))
```

- Latencia p95 por ruta (usar buckets del histograma):
```
histogram_quantile(
  0.95,
  sum by (le, path) (rate(http_request_duration_seconds_bucket[5m]))
)
```

- Latencia media por ruta (aprox):
```
sum by (path) (rate(http_request_duration_seconds_sum[5m]))
/ sum by (path) (rate(http_request_duration_seconds_count[5m]))
```

- Eventos de auditoría por tipo (1m):
```
sum by (tipo) (rate(audit_events_total[1m]))
```


## Reglas de alerta (ejemplos)

Guárdalas en tu archivo de alertas de Prometheus (o a través de Alertmanager):

```yaml
groups:
  - name: socios_backend
    rules:
      - alert: AltaTasaErrores5xx
        expr: |
          (sum(rate(http_requests_total{status=~"5.."}[5m]))
           / sum(rate(http_requests_total[5m]))) > 0.05
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Error rate > 5% por 10m"
          description: "{{ $value | printf "%.2f" }} de las requests terminan en 5xx."

      - alert: LatenciaP95Alta
        expr: |
          histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[10m]))) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "p95 de latencia > 500ms"
          description: "La latencia p95 superó 0.5s durante 10m."
```

Ajusta los umbrales a tus SLOs.


## Grafana (ideas rápidas de paneles)

Sugerencias de paneles:
- Timeseries: RPS total y por status (usar `sum by (status) (rate(http_requests_total[1m]))`).
- Timeseries: p50/p95/p99 (usar `histogram_quantile` con buckets del histograma).
- Bar gauge: Top rutas por error rate (5xx) en 5–15 minutos.
- Stat: Eventos de auditoría por minuto (sum(rate(audit_events_total[1m]))).

Tip: etiqueta el dashboard con `app=socios-backend` si usas esa label en Prometheus.

### Dashboard listo para importar

Incluimos un dashboard JSON para Grafana con los paneles anteriores:

- Archivo: `docs/grafana/socios_backend_dashboard.json`

Pasos para importarlo:
1. Abre Grafana → Dashboards → Import.
2. Haz clic en “Upload JSON file” y selecciona `docs/grafana/socios_backend_dashboard.json`.
3. Selecciona tu datasource de Prometheus y guarda.

## Stack local opcional (Docker Compose)

Para levantar Prometheus y Grafana localmente con configuración mínima:

- Compose: `ops/observabilidad/docker-compose.yml`
- Prometheus config: `ops/observabilidad/prometheus/prometheus.yml`
- Provisioning Grafana:
  - Datasource: `ops/observabilidad/grafana/provisioning/datasources/datasource.yml`
  - Dashboards: `ops/observabilidad/grafana/provisioning/dashboards/dashboard.yml` (carga archivos desde `docs/grafana/`)

Notas:
- En Windows, `host.docker.internal:8000` apunta al backend corriendo en el host (ajústalo si cambias el puerto).
- Grafana quedará en `http://localhost:3000` (usuario: admin, pass: admin).
- Prometheus en `http://localhost:9090`.


## Correlación (X-Request-ID)

- El backend genera un `X-Request-ID` si el cliente no lo envía. Ese ID se agrega en la respuesta.
- Recomendación: los clientes (frontend Flet y móvil) pueden reenviar el header para mantener la trazabilidad en hops.
- Útil para debug: busca `request_id` en logs y correlaciónalo con eventos de auditoría.

Ejemplo de envío desde un cliente HTTP:

```python
headers = {"X-Request-ID": "<uuid-hex>"}
client.get("/api/miembros", headers=headers)
```


## Logging estructurado

El middleware emite una línea JSON por request con forma aproximada:

```json
{
  "msg": "request",
  "request_id": "3f5b1c...",
  "method": "GET",
  "path": "/api/miembros",
  "route": "/api/miembros",
  "status": 200,
  "duration_ms": 12.345,
  "client": "127.0.0.1"
}
```

Si `settings.LOG_FILE` está definido, los logs también se escriben en ese archivo además de stdout.


## Notas de producción

- Proxy/ingress: asegura que `X-Request-ID` se preserve o se genere en el edge (Nginx, Envoy, Traefik). Si confías poco en clientes externos, puedes regenerarlo en el backend ignorando el header entrante.
- Cardinalidad de etiquetas: el middleware intenta usar la ruta "templated" para `path`. Evita etiquetas que crezcan sin control (por ejemplo, IDs como parte de `path`).
- Seguridad: no incluyas datos sensibles en etiquetas o mensajes de log.


## Troubleshooting

- `/metrics` muestra "metrics disabled": instala `prometheus-client` en el entorno del backend.
- No ves series de auditoría: verifica que se generen eventos (logins, creación de socios, pagos, accesos).
- Cardinalidad alta en `path`: revisa que tu despliegue preserve `route.path` (ASGI/routers). Como último recurso, mapea rutas a categorías (p. ej. "api_miembros") antes de etiquetar.
