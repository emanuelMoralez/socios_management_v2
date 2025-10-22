<!-- .github/copilot-instructions.md - Instrucciones para agentes de IA trabajando en este repo -->

# Instrucciones rápidas para IA (socios_management_v2)

Este repo contiene un backend en FastAPI (Python), un frontend de escritorio en Flet (Python) y una app móvil en Expo (React Native). Sigue estas reglas prácticas para ser productivo sin introducir cambios riesgosos.

- Arquitectura clave:
  - `backend/` — FastAPI app con `app/main.py` (lifespan, middleware, routers). Configuración central en `app/config.py`. DB: SQLAlchemy (`app/database.py`) y migrations con Alembic (`alembic/`).
  - `backend/app/routers/` — routers por dominio (ej. `miembros.py`, `pagos.py`, `auth.py`). Cada router usa dependencias: `get_db()` (Session) y `get_current_user` / `require_operador` (auth) desde `app/utils/dependencies.py`.
  - `backend/app/services/` — lógica de negocio reutilizable (ej. `auth_service.py`, `qr_service.py`). Prefer usar servicios para operaciones complejas en lugar de duplicar lógica en routers.
  - `frontend-desktop/` — UI en Python (Flet). Entry: `src/main.py` / `app.py`.

- Cómo ejecutar (desarrollar localmente):
  - Levantar infra: `docker-compose up -d postgres redis` (usa `docker-compose.yml`).
  - Backend (local): desde `backend/`: crear venv, instalar `requirements.txt`, copiar `.env.example` → `.env`, luego `uvicorn app.main:app --reload`.
  - Backend (docker): `docker-compose up --build backend` expone puerto 8000.
  - Migraciones: desde `backend/`: `alembic upgrade head` (Alembic está configurado en `alembic/env.py`, importa `app.models` para detectar modelos).

- Patrones y convenciones del código:
  - Configuración centralizada con Pydantic Settings: `app/config.py`. Usa `settings = get_settings()`; respetar variables de entorno `.env`.
  - DB: usar la dependencia `get_db()` (en `app/database.py`) en routers para obtener la sesión. No abrir engines directos fuera de `database.py`.
  - Modelos: `app/models/__init__.py` importa todos los modelos — necesario para Alembic. Si añades un modelo, exportarlo ahí.
  - Responses y validaciones: los routers retornan modelos Pydantic definidos en `app/schemas/` (ej. `MiembroResponse`, `PagoResponse`). Mantener la compatibilidad de campos.
  - Seguridad: JWT + passwords en `app/services/auth_service.py` y utilidades en `app/utils/security.py`. No intentes modificar tokens sin entender `create_access_token` / `decode_token`.
  - QR / archivos: servicios de generación en `app/services/qr_service.py` y almacenamiento en `UPLOAD_DIR` (configurable).

- Tests y desarrollo local:
  - Tests con pytest en `backend/tests/` (usar `pytest` y `pytest-asyncio`). `backend/requirements.txt` lista `pytest` y `httpx`.
  - Para pruebas rápidas sin Docker puedes usar SQLite: `DATABASE_URL` acepta `sqlite:///file.db` y `database.py` adapta el engine (usa `StaticPool`).

- Integraciones y side-effects a revisar:
  - Redis (opcional) y MercadoPago (variables `MP_*` en `app/config.py`). Estas integraciones están preparadas pero pueden estar deshabilitadas si no hay credenciales.
  - Email/SMTP: credenciales en `SMTP_*` — deshabilita en desarrollo si no están configuradas.

- Cómo cambiar cosas de forma segura:
  - Cambios en modelos → crear/actualizar migración Alembic (`alembic revision --autogenerate -m "msg"`) y luego `alembic upgrade head`.
  - Evita usar `Base.metadata.create_all()` en producción; el proyecto lo ejecuta en `development` en `app/main.py` solo para conveniencia.
  - Para refactors grandes, actualiza `app/models/__init__.py` y `alembic/env.py` si introduces nuevos paquetes.

- Ejemplos concretos de patrones a seguir:
  - Crear miembro: ver `backend/app/routers/miembros.py` → lógica de generación de `numero_miembro`, creación inicial y posterior generación de QR vía `QRService.generar_qr_miembro()`.
  - Registrar pago: ver `backend/app/routers/pagos.py` → actualizar `Miembro.saldo_cuenta`, crear `MovimientoCaja`, usar `Pago.calcular_monto_final()` y `generar_numero_comprobante()`.

- Reglas para agentes IA:
  - Haz cambios mínimos y localizados. Prefiere extraer lógica a `services/` cuando sea necesario.
  - Siempre respetar `settings` para valores por defecto; no hardcodear credenciales.
  - Cuando cambies modelos, añade migración Alembic y prueba las migraciones.
  - Referencia archivos clave en la PR description (ej. `app/main.py`, `app/models/X.py`, `alembic/versions/`).

Si algo de lo anterior está incompleto o necesitas más ejemplos (tests, CI, flujos de datos), dímelo y ajusto este fichero.
