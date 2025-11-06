# Guía de Desarrollo

## Arquitectura de Auditoría

La auditoría registra actividades clave (login, creación/edición/baja de miembros, pagos, accesos) en la tabla `actividad` a través de `app/services/audit_service.py`.

Puntos clave:
- Los routers del dominio llaman a `AuditService.registrar_*` después de operaciones importantes.
- Los eventos incluyen: `tipo`, `severidad`, `descripcion`, `usuario_id` (si aplica), `entidad_tipo`, `entidad_id`, `datos_adicionales`, `ip_address`, `user_agent`.
- Los errores al registrar auditoría no interrumpen la operación principal (se registran logs y se hace rollback de la transacción de auditoría).
- Observabilidad: cada evento incrementa el contador `audit_events_total{tipo,severidad}` (si Prometheus está habilitado).

### Flujo típico (crear miembro)
1. Validación de entrada y unicidad.
2. Creación del `Miembro` con número único (con retry ante `IntegrityError`).
3. Generación y persistencia del QR inmutable.
4. Registro de auditoría con `AuditService.registrar_miembro_creado(...)`.

### Observabilidad
- Middleware HTTP agrega `X-Request-ID` y mide la duración de cada request.
- Métricas expuestas en `/metrics` (Prometheus):
	- `http_requests_total{method,path,status}`
	- `http_request_duration_seconds{method,path}` (histograma)
	- `audit_events_total{tipo,severidad}`
- Logs estructurados en JSON por request con: `request_id`, método, ruta, status, duración y cliente.

Ver `docs/observabilidad.md` para setup de Prometheus/Grafana y dashboard listo.
