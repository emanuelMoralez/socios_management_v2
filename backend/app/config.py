"""
Configuración de la aplicación con Pydantic Settings
backend/app/config.py
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación"""
    
    # ==================== APLICACIÓN ====================
    APP_NAME: str = "Sistema de Gestión de Socios"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    PROJECT_NAME: str = "Sistema de Gestión de Socios"  # Para emails
    
    # ==================== BASE DE DATOS ====================
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/gestion_socios"
    DATABASE_ECHO: bool = False  # True para ver queries SQL
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # ==================== SEGURIDAD ====================
    SECRET_KEY: str = "tu-clave-secreta-super-segura-cambiala-en-produccion"
    QR_SECRET_KEY: str = "clave-para-qr-cambiala-tambien"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ==================== ORGANIZACIÓN ====================
    ORG_PREFIX: str = "CLUB"  # Prefijo para QR: CLUB-ID-CHECKSUM
    ORG_NAME: str = "Mi Organización"
    ORG_TYPE: str = "generico"  # generico, club, cooperativa
    
    # ==================== CORS ====================
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    ALLOW_CREDENTIALS: bool = True
    ALLOWED_METHODS: List[str] = ["*"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # ==================== REDIS ====================
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_DECODE_RESPONSES: bool = True
    
    # ==================== EMAIL / SMTP ====================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Sistema de Gestión"
    SMTP_TLS: bool = True  # ← NUEVO: Para usar STARTTLS
    
    # ==================== ARCHIVOS ====================
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "pdf"]
    
    # ==================== QR ====================
    QR_VERSION: int = 1
    QR_ERROR_CORRECTION: str = "H"  # L, M, Q, H
    QR_BOX_SIZE: int = 10
    QR_BORDER: int = 4
    
    # ==================== PAGINACIÓN ====================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # ==================== LOGS ====================
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: str = "logs/app.log"
    
    # ==================== AUDITORÍA ====================
    # Días de retención de auditoría (90 días por defecto)
    AUDIT_RETENTION_DAYS: int = 90
    # Directorio para archivos de auditoría
    AUDIT_ARCHIVE_DIR: str = "archives/audit"
    
    # ==================== INTEGRACIONES (Fase 3) ====================
    # MercadoPago
    MP_ACCESS_TOKEN: Optional[str] = None
    MP_PUBLIC_KEY: Optional[str] = None
    MP_WEBHOOK_SECRET: Optional[str] = None
    
    # Sentry (monitoreo de errores)
    SENTRY_DSN: Optional[str] = None
    
    # ==================== MIEMBROS ====================
    # Formato de número de miembro
    NUMERO_MIEMBRO_PREFIX: str = "M"  # M-00001
    NUMERO_MIEMBRO_LENGTH: int = 5  # Padding con ceros
    
    # Estados que permiten acceso
    ESTADOS_ACCESO_PERMITIDO: List[str] = ["activo"]
    
    # Días de gracia antes de marcar como moroso
    DIAS_GRACIA_MOROSIDAD: int = 5
    
    # Monto máximo de deuda para advertencia (no bloqueo)
    DEUDA_MAXIMA_ADVERTENCIA: float = 500.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instancia singleton de Settings (con caché)
    Uso: settings = get_settings()
    """
    return Settings()


# Instancia global (opcional, para imports simples)
settings = get_settings()