# Documentación API

## Auditoría

Endpoints para consultar actividades registradas por el sistema.

### GET /api/auditoria

Lista actividades con filtros y paginación.

Parámetros de query (opcionales):
- `tipo`: Tipo de actividad (ej: LOGIN_EXITOSO, MIEMBRO_CREADO, PAGO_REGISTRADO, ACCESO_PERMITIDO, ACCESO_DENEGADO, etc.)
- `severidad`: INFO | WARNING | ERROR | CRITICAL
- `usuario_id`: ID del usuario que ejecutó la acción
- `entidad_tipo`: Ej: "miembro", "pago", "acceso"
- `entidad_id`: ID de la entidad
- `q`: Búsqueda textual en descripción
- `page`, `page_size`: Paginación (por defecto 20, máx 100)

Respuesta (200):
```
{
	"items": [
		{
			"id": 123,
			"fecha_hora": "2025-11-05T12:34:56Z",
			"tipo": "MIEMBRO_CREADO",
			"severidad": "INFO",
			"descripcion": "Nuevo socio registrado: CLUB-000123 - Juan Pérez",
			"usuario_id": 1,
			"entidad_tipo": "miembro",
			"entidad_id": 456
		}
	],
	"pagination": {
		"page": 1,
		"page_size": 20,
		"total_items": 42,
		"total_pages": 3
	}
}
```

Notas:
- Requiere permisos de administrador.
- El tiempo está en UTC ISO-8601.

### GET /api/auditoria/{id}

Obtiene el detalle de una actividad.

Respuesta (200):
```
{
	"id": 123,
	"fecha_hora": "2025-11-05T12:34:56Z",
	"tipo": "MIEMBRO_CREADO",
	"severidad": "INFO",
	"descripcion": "Nuevo socio registrado: CLUB-000123 - Juan Pérez",
	"usuario_id": 1,
	"entidad_tipo": "miembro",
	"entidad_id": 456,
	"datos_adicionales": {
		"nombre": "CLUB-000123 - Juan Pérez"
	},
	"ip_address": "127.0.0.1",
	"user_agent": "Mozilla/5.0 ..."
}
```

Errores comunes:
- 404 si no existe el ID.
- 401/403 si no tiene permisos.

### Observabilidad relacionada

- `GET /metrics`: métricas en texto Prometheus (o mensaje de fallback si no instalaste `prometheus-client`).
- `X-Request-ID`: todas las respuestas incluyen esta cabecera para correlación; puedes enviarla desde el cliente para mantener el ID.
