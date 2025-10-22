"""
Sistema de Gestión de Socios - FastAPI Backend
backend/app/main.py
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import sys

from app.database import engine, Base, check_db_connection
from app.config import settings

# Importar todos los routers
from app.routers import auth, miembros, accesos, pagos, usuarios, reportes

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
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
    logger.info(" Cerrando Sistema de Gestión de Socios...")


# ==================== APP ====================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para gestión de socios de clubes y cooperativas",
    docs_url="/docs",
    redoc_url="/redoc",
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
    """Log de todas las peticiones"""
    start_time = datetime.utcnow()
    
    # Procesar petición
    response = await call_next(request)
    
    # Calcular tiempo
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Log
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
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
            "errors": errors
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
            "detail": detail
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


# Incluir routers de módulos
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["[AUTH] Autenticación"]
)

app.include_router(
    miembros.router,
    prefix="/api/miembros",
    tags=[" Miembros"]
)

app.include_router(
    accesos.router,
    prefix="/api/accesos",
    tags=[" Control de Acceso"]
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