"""
Sistema de Gestión de Socios - FastAPI Backend
backend/app/main.py
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import sys
from pathlib import Path
import json
import uuid

from app.database import engine, Base, check_db_connection
from app.config import settings
from app import metrics

# Importar todos los routers
from app.routers import auth, miembros, accesos, pagos, usuarios, reportes, notificaciones, auditoria

# Configurar logging
handlers = [logging.StreamHandler(sys.stdout)]
if settings.LOG_FILE:
    # Crear directorio de logs si no existe
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(settings.LOG_FILE))
else:
    handlers.append(logging.NullHandler())

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

logger = logging.getLogger(__name__)


# ==================== LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eventos de inicio y cierre de la aplicación
    """
    # Startup
    logger.info("Iniciando Sistema de Gestión de Socios...")
    logger.info(f"Entorno: {settings.ENVIRONMENT}")
    logger.info(f"Versión: {settings.APP_VERSION}")
    # Inicializar métricas (no-op si falta prometheus_client)
    try:
        metrics.init_metrics()
        logger.info("Métricas inicializadas")
    except Exception as e:
        logger.warning(f"No se pudieron inicializar métricas: {e}")

    # Validación de configuración crítica en PRODUCCIÓN (fail-fast)
    if settings.ENVIRONMENT == "production":
        errors: list[str] = []

        # SECRET_KEY y QR_SECRET_KEY robustos (no defaults inseguros, longitud mínima)
        def _weak_key(k: str) -> bool:
            return (
                not k
                or len(k) < 32
                or "cambiala" in k.lower()
                or k.strip() in {
                    "tu-clave-secreta-super-segura-cambiala-en-produccion",
                    "clave-para-qr-cambiala-tambien",
                }
            )

        if _weak_key(settings.SECRET_KEY):
            errors.append("SECRET_KEY es débil o usa el valor por defecto del repositorio")
        if _weak_key(settings.QR_SECRET_KEY):
            errors.append("QR_SECRET_KEY es débil o usa el valor por defecto del repositorio")

        # DB debe ser Postgres (no SQLite) en producción
        if settings.DATABASE_URL.startswith("sqlite"):
            errors.append("DATABASE_URL apunta a SQLite; en producción debe usar PostgreSQL")

        # CORS: no permitir localhost/127.0.0.1 ni comodín
        bad_origins = [o for o in settings.ALLOWED_ORIGINS if (
            o == "*" or "localhost" in o or "127.0.0.1" in o
        )]
        if bad_origins:
            errors.append(
                f"ALLOWED_ORIGINS contiene orígenes no válidos para producción: {bad_origins}"
            )

        # DEBUG debe estar deshabilitado en producción
        if settings.DEBUG:
            errors.append("DEBUG debe ser False en producción")

        if errors:
            for e in errors:
                logger.error(f"[CONFIG] {e}")
            # Abortamos inicio de la app para evitar un despliegue inseguro
            raise RuntimeError(
                "Configuración insegura/incorrecta detectada en producción. Revisa las variables de entorno."
            )
    
    # Verificar conexión a base de datos
    if check_db_connection():
        logger.info("Conexión a base de datos OK")
    else:
        logger.error("Error en conexión a base de datos")
    
    # Crear tablas (solo en desarrollo, en producción usar Alembic)
    if settings.ENVIRONMENT == "development":
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Tablas de base de datos verificadas")
        except Exception as e:
            logger.error(f"Error creando tablas: {e}")      
    
    logger.info(f"[WEB] API disponible en: http://localhost:8000")
    logger.info(f"[DOCS] Documentación: http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    logger.info("Cerrando Sistema de Gestión de Socios...")


# ==================== APP ====================
# Deshabilitar documentación pública en producción
_docs_url = None if settings.ENVIRONMENT == "production" else "/docs"
_redoc_url = None if settings.ENVIRONMENT == "production" else "/redoc"

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para gestión de socios de clubes y cooperativas",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    lifespan=lifespan
)


# ==================== MIDDLEWARE ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware: asigna X-Request-ID, mide duración, registra métricas y log estructurado."""
    # Correlación: request id
    req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = req_id

    # Medición de tiempo de alta resolución
    t0 = metrics.now()

    # Procesar petición
    response = await call_next(request)

    # Calcular tiempo
    duration = max(metrics.now() - t0, 0.0)

    # Propagar header
    try:
        response.headers["X-Request-ID"] = req_id
    except Exception:
        pass

    # Path "templated" si está disponible (evita cardinalidad alta)
    path_template = getattr(getattr(request.scope, "get", lambda *_: None)("route"), "path", None)
    if not path_template:
        route = request.scope.get("route") if isinstance(request.scope, dict) else None
        path_template = getattr(route, "path", request.url.path)

    # Métricas
    try:
        metrics.track_http(request.method, path_template, response.status_code, duration)
    except Exception:
        pass

    # Log estructurado (JSON)
    log_payload = {
        "msg": "request",
        "request_id": req_id,
        "method": request.method,
        "path": request.url.path,
        "route": path_template,
        "status": response.status_code,
        "duration_ms": round(duration * 1000, 3),
        "client": getattr(request.client, "host", None),
    }
    logger.info(json.dumps(log_payload, ensure_ascii=False))

    return response


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Manejador de errores de validación Pydantic
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"[ERROR] Error de validación en {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Error de validación",
            "detail": "Los datos enviados no son válidos",
            "errors": errors,
            "request_id": getattr(getattr(request, "state", object()), "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Manejador de errores generales
    """
    logger.error(f"[ERROR] Error no manejado en {request.url.path}: {str(exc)}", exc_info=True)
    
    # En producción, no mostrar detalles del error
    detail = str(exc) if settings.DEBUG else "Error interno del servidor"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Error interno del servidor",
            "detail": detail,
            "request_id": getattr(getattr(request, "state", object()), "request_id", None)
        }
    )


# ==================== ROUTERS ====================

# Health check
@app.get("/", tags=["Sistema"])
async def root():
    """Endpoint raíz - Información básica de la API"""
    return {
        "message": "Sistema de Gestión de Socios API",
        "version": settings.APP_VERSION,
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Sistema"])
async def health_check():
    """
    Health check - Verifica estado del sistema
    """
    db_status = check_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "database": "connected" if db_status else "disconnected",
        "environment": settings.ENVIRONMENT
    }


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    """Endpoint de métricas en formato Prometheus (o mensaje si deshabilitado)."""
    payload, content_type = metrics.get_metrics_text()
    return Response(content=payload, media_type=content_type)


# Incluir routers de módulos
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["[AUTH] Autenticación"]
)

app.include_router(
    miembros.router,
    prefix="/api/miembros",
    tags=["[MEMBERS] Miembros"]
)

app.include_router(
    accesos.router,
    prefix="/api/accesos",
    tags=["[ACCESS] Control de Acceso"]
)

app.include_router(
    pagos.router,
    prefix="/api/pagos",
    tags=["[MONEY] Pagos"]
)

app.include_router(
    usuarios.router,
    prefix="/api/usuarios",
    tags=["[USER] Usuarios"]
)

app.include_router(
    reportes.router,
    prefix="/api/reportes",
    tags=["[REPORT] Reportes"]
)

app.include_router(
    notificaciones.router,
    prefix="/api/notificaciones",
    tags=["[EMAIL] Notificaciones"]
)

app.include_router(
    auditoria.router,
    prefix="/api/auditoria",
    tags=["[REPORT] Auditoría"]
)


# ==================== STARTUP ====================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )