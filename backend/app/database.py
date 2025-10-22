"""
Configuración de SQLAlchemy y sesión de base de datos
backend/app/database.py
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Configuración del engine según el tipo de BD
if settings.DATABASE_URL.startswith("sqlite"):
    # Configuración para SQLite
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DATABASE_ECHO,
    )
else:
    # Configuración para PostgreSQL
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DATABASE_ECHO,
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base declarativa
Base = declarative_base()


# ==================== DEPENDENCY ====================
def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos en FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== EVENTOS ====================
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Configuración específica para SQLite
    Habilita foreign keys
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ==================== UTILIDADES ====================
def init_db():
    """
    Inicializa la base de datos creando todas las tablas
    Solo para desarrollo, en producción usar Alembic
    """
    try:
        from app.models import (
            Usuario, Miembro, Categoria, Pago, 
            MovimientoCaja, Acceso, EventoAcceso, AccesoEvento
        )
        
        Base.metadata.create_all(bind=engine)
        logger.info("[OK] Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"[ERROR] Error inicializando base de datos: {e}")
        raise


def drop_db():
    """
    PELIGRO: Elimina todas las tablas
    Solo para testing o desarrollo
    """
    if settings.ENVIRONMENT == "production":
        raise Exception("[ERROR] No se puede eliminar DB en producción")
    
    Base.metadata.drop_all(bind=engine)
    logger.warning("[WARN] Todas las tablas eliminadas")


def get_db_context():
    """
    Context manager para usar DB fuera de FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Verifica si la conexión a DB está funcionando
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("[OK] Conexión a base de datos OK")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Error en conexión DB: {e}")
        return False