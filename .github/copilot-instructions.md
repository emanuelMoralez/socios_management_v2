<!-- .github/copilot-instructions.md - Instrucciones para agentes de IA trabajando en este repo -->

# Instrucciones para IA (socios_management_v2)

Sistema de gestión de socios con **backend FastAPI** (Python), **frontend Flet** (Python/desktop) y **app móvil Expo** (React Native). Lee con atención estos patrones específicos del proyecto para evitar cambios riesgosos.

## 🏗️ Arquitectura y estructura

### Backend (FastAPI + PostgreSQL)
- **Entry point**: `backend/app/main.py` con lifespan context manager para startup/shutdown
  - Middleware CORS + request logging personalizado
  - Exception handlers globales (validación Pydantic + errores generales)
  - `Base.metadata.create_all()` SOLO en `ENVIRONMENT=development`
- **Config**: `app/config.py` usa Pydantic Settings con `.env`. Import: `from app.config import settings`
- **Database**: `app/database.py` configura engine diferenciado (SQLite con `StaticPool` vs PostgreSQL con pooling)
  - Dependencia: `get_db()` yield Session — usar SIEMPRE en routers
  - Health check: función `check_db_connection()` ejecuta `SELECT 1`
- **Routers**: `app/routers/` organizados por dominio (`miembros.py`, `pagos.py`, `auth.py`, `accesos.py`, `reportes.py`, `notificaciones.py`)
  - Incluidos en `main.py` con prefijos `/api/{dominio}`
  - Tags organizadas con emojis: `[AUTH]`, `[MEMBERS]`, `[MONEY]`, `[ACCESS]`, `[REPORT]`, `[EMAIL]`
- **Services**: `app/services/` contiene lógica reutilizable
  - `AuthService`: autenticación, creación usuarios, validación passwords
  - `QRService`: generación QR con formato `{ORG_PREFIX}-{ID}-{CHECKSUM}` (inmutables)
  - `email_service.py`, `pdf_service.py`, `report_service.py`, `export_service.py`
- **Schemas**: `app/schemas/` define Pydantic models para requests/responses (separados de ORM models)
- **Alembic**: `alembic/env.py` importa `Base` y TODOS los modelos de `app.models/__init__.py`

### Frontend Desktop (Flet)
- **Entry**: `frontend-desktop/src/main.py` → clase `App` maneja navegación login→dashboard
- **API Client**: `src/services/api_client.py` — clase `APIClient` con token Bearer, métodos async httpx
- **Views**: `src/views/` — cada view hereda de `ft.Column` o `ft.Container` (ej. `SociosView`, `CuotasView`, `ReportesView`)
- **Dashboard**: `DashboardView` carga vistas dinámicamente vía `load_view(view_name)`
- **State**: `api_client` singleton con `self.token` para autenticación

### Mobile App (Expo/React Native)
- **Package**: `mobile-app/package.json` usa Expo ~50, React Navigation, expo-barcode-scanner
- Screens en `src/screens/`, navegación en `src/navigation/`

## 🚀 Workflows críticos

### Desarrollo local
```bash
# 1. Levantar infra (desde raíz)
docker-compose up -d postgres redis

# 2. Backend (desde backend/)
python -m venv venv && source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env  # Editar DATABASE_URL, SECRET_KEY, etc.
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend desktop (desde frontend-desktop/)
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env  # API_URL=http://localhost:8000/api
python -m src.main  # o python src/app.py

# 4. Mobile (desde mobile-app/)
npm install
npx expo start
```

### Crear usuario admin inicial
```bash
cd backend
python scripts/create_admin.py
# Output: admin / Admin123
```

### Migraciones (Alembic)
```bash
cd backend
# Crear migración autogenerate
alembic revision --autogenerate -m "descripcion cambio"
# Aplicar migraciones
alembic upgrade head
# Rollback 1 revision
alembic downgrade -1
```

**CRÍTICO**: Si añades modelo nuevo, exportarlo en `app/models/__init__.py` para que Alembic lo detecte.

## 🔐 Seguridad y autenticación

- **JWT tokens**: `app/services/auth_service.py` + `app/utils/security.py`
  - Access token: 30 min (`ACCESS_TOKEN_EXPIRE_MINUTES`)
  - Refresh token: 7 días (`REFRESH_TOKEN_EXPIRE_DAYS`)
  - Payload incluye: `{"sub": username, "type": "access"|"refresh"}`
- **Dependencies de auth**: `app/utils/dependencies.py`
  - `get_current_user` → extrae usuario del JWT Bearer token
  - `RoleChecker([roles])` → valida roles específicos
  - Shortcuts: `require_super_admin`, `require_admin`, `require_operador`, `require_portero`
  - Ejemplo: `current_user: Usuario = Depends(require_operador)`
- **Passwords**: `hash_password()` usa bcrypt, `verify_password()` para check
- **Roles**: enum `RolUsuario` (SUPER_ADMIN, ADMINISTRADOR, OPERADOR, PORTERO)

## 📊 Patrones de código específicos

### 1. Crear endpoint protegido con paginación
```python
from app.utils.dependencies import get_current_user, PaginationParams

@router.get("/items", response_model=PaginatedResponse[ItemResponse])
async def listar_items(
    current_user: Usuario = Depends(get_current_user),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    query = db.query(Item).filter(...)
    total = query.count()
    items = query.offset(pagination.skip).limit(pagination.limit).all()
    
    return {
        "data": items,
        "pagination": pagination.get_metadata(total)
    }
```

### 2. Llamar a servicios desde routers
```python
# Generar QR para miembro
from app.services.qr_service import QRService

qr_data = QRService.generar_qr_miembro(
    miembro_id=miembro.id,
    numero_documento=miembro.numero_documento,
    numero_miembro=miembro.numero_miembro,
    nombre_completo=f"{miembro.nombre} {miembro.apellido}"
)
# qr_data contiene: qr_code, qr_hash, image_bytes, timestamp
```

### 3. Manejo de transacciones críticas (pagos)
Ver `backend/app/routers/pagos.py` líneas 38-137:
- Actualizar `Miembro.saldo_cuenta` en misma transacción que `Pago`
- Crear `MovimientoCaja` correspondiente
- Usar `Pago.calcular_monto_final()` para aplicar recargos/descuentos
- Generar `numero_comprobante` con formato auto-increment

### 4. Exception handling estándar
`app/main.py` define handlers globales:
- `RequestValidationError` → 422 con lista de errores por campo
- `Exception` general → 500 con `detail` oculto en producción si `DEBUG=False`

### 5. Config según entorno
```python
from app.config import settings

if settings.ENVIRONMENT == "production":
    # no logs verbosos, no crear tablas
if settings.DEBUG:
    # mostrar stack traces
```

## 🧪 Testing

- Framework: pytest + pytest-asyncio (ver `backend/requirements.txt`)
- Estructura: `backend/tests/` (actualmente con stubs)
- Test DB: usar `DATABASE_URL=sqlite:///test.db` para tests rápidos
- Ejecutar: `cd backend && pytest`

## ⚠️ Side-effects y gotchas

1. **Modelos + Alembic**: Siempre exportar nuevos modelos en `app/models/__init__.py` Y en `alembic/env.py`
2. **QR codes inmutables**: No modificar `QRService.generar_qr_miembro()` sin actualizar checksum logic
3. **Soft deletes**: Muchos modelos usan `is_deleted` (no eliminar físicamente)
4. **Estados de acceso**: `ESTADOS_ACCESO_PERMITIDO` en `app/config.py` define qué estados permiten acceso
5. **SMTP deshabilitado**: Si faltan credenciales SMTP, notificaciones fallarán silently — validar en desarrollo
6. **Redis opcional**: App funciona sin Redis, pero algunas features (cache, rate limiting) pueden estar deshabilitadas

## 🎯 Reglas para agentes IA

1. **Cambios mínimos**: Edita solo lo necesario, no refactorices sin razón
2. **Servicios > Routers**: Extrae lógica compleja a `app/services/` para reusabilidad
3. **Nunca hardcodear**: Usa `settings.VARIABLE` para configs, no strings mágicos
4. **Migraciones obligatorias**: Cambio en modelo → `alembic revision --autogenerate -m "..."` → verificar SQL generado
5. **Logs informativos**: Usa `logger.info("[OK] ...")` y `logger.error("[ERROR] ...")` con contexto
6. **Documentación inline**: Docstrings estilo Google en funciones complejas (ver `auth_service.py`)
7. **Validación de permisos**: Siempre usar `Depends(require_*)` en endpoints críticos (pagos, usuarios, reportes)

## 📝 Referencias rápidas

- API docs: http://localhost:8000/docs (Swagger UI con auth Bearer)
- Formato QR: `{ORG_PREFIX}-{ID}-{CHECKSUM}` (ej: `CLUB-123-a1b2c3d4e5f6`)
- Roles hierarchy: SUPER_ADMIN > ADMINISTRADOR > OPERADOR > PORTERO
- Paginación default: 20 items, max 100 (`settings.DEFAULT_PAGE_SIZE`, `settings.MAX_PAGE_SIZE`)
- Logs: `backend/logs/app.log` (si `LOG_FILE` configurado)

---
**Última actualización**: 2025-11-03 | Para feedback o expansión de ejemplos, abrir issue en repo.
