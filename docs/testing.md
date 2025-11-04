# Guía de Testing

Esta guía explica cómo ejecutar los tests del backend y cómo funciona la automatización en CI.

## Ejecutar tests localmente

Usamos SQLite para pruebas, por lo que no necesitas levantar Postgres.

### Opciones de ejecución

1) **VS Code (recomendado)**
   - Ejecuta la tarea: "backend: pytest" (sin coverage)
   - O usa: "backend: coverage (auto)" (instala pytest-cov y ejecuta con coverage)

2) **Terminal**
   ```bash
   cd backend
   ENVIRONMENT=development DATABASE_URL=sqlite:///test.db pytest -q
   ```

3) **Con cobertura**
   ```bash
   cd backend
   pytest --cov=app --cov-report=term-missing:skip-covered --cov-report=html
   # Ver reporte: open htmlcov/index.html
   ```

**Notas importantes:**
- En `ENVIRONMENT=development` la app crea las tablas automáticamente en el startup (ver `app/main.py`)
- Los tests utilizan `TestClient` de FastAPI y una DB SQLite temporal creada en `conftest.py`
- **Limitación conocida**: Algunos tests pueden fallar si se ejecutan múltiples veces en la misma sesión debido a colisiones de datos. Solución: ejecutar pytest con `--forked` o limpiar la DB entre tests

## CI (GitHub Actions)

El workflow `.github/workflows/ci.yml` ejecuta en cada push/PR contra `master`/`main`:
- **Pytest con coverage** (Python 3.10 y 3.11)
- **Umbral de cobertura**: 65% mínimo (falla el build si no se alcanza)
- **Ruff** (linting, no bloqueante)
- **mypy** (type checking, no bloqueante)
- **SQLite** para no depender de servicios externos

## Estructura de tests

### Tests existentes

- **`test_health.py`**: Pruebas de humo (`/` y `/health`)
- **`test_qr_service.py`**: Validación de `QRService` (generación y parseo de QR)
- **`test_auth_flow.py`**: Flujo completo de autenticación (register → login → me → refresh → change-password)
- **`test_miembros.py`**: CRUD de categorías y miembros, paginación, soft delete
- **`test_pagos_flow.py`**: Crear pago → listar → resumen → anular
- **`test_reportes.py`**: Endpoints de reportes (`ingresos-historicos`, `accesos-detallados`)
- **`test_usuarios_permissions.py`**: Validación de permisos por rol (SUPER_ADMIN, ADMINISTRADOR, OPERADOR)
- **`test_exports.py`**: Exportación a Excel (socios, pagos, morosidad) - verifica content-type y headers

### Fixtures disponibles (`conftest.py`)

- **`client`**: `TestClient` con lifespan completo de la app (session-scoped)
- **`make_user(username, password)`**: Helper para registrar usuarios vía API
- **`auth_tokens()`**: Crea un usuario y devuelve sus access/refresh tokens
- **`SessionLocal`**: Para acceso directo a DB (ej: elevar permisos a SUPER_ADMIN)
- **`elevate_to_super_admin(username)`**: Actualiza un usuario a rol SUPER_ADMIN vía DB

### Agregar nuevos tests

Para pruebas autenticadas reutiliza los fixtures de `conftest.py`:

```python
def test_mi_endpoint(client: TestClient, auth_tokens: dict):
    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    r = client.get("/api/mi-endpoint", headers=headers)
    assert r.status_code == 200
```

**Buenas prácticas:**
- Usa identificadores únicos (uuid) para evitar colisiones entre tests
- No asumas datos pre-existentes, créalos en el test
- Limpia recursos al final si es necesario (o usa pytest fixtures con `yield`)

## Ver cobertura

Después de ejecutar `pytest --cov=app --cov-report=html`:

```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

El reporte HTML muestra líneas cubiertas/no cubiertas por archivo.

## Calidad de código

### Ruff (linting)

```bash
cd backend
ruff check .
# Auto-fix: ruff check . --fix
```

### Mypy (type checking)

```bash
cd backend
mypy app
```

Configuraciones en `pyproject.toml` (Ruff) y `mypy.ini`.
