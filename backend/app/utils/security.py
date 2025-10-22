"""
Utilidades de seguridad: JWT, hashing, validaciones
backend/app/utils/security.py
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config import settings

# ==================== PASSWORD HASHING ====================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt
    
    NOTA: bcrypt tiene un límite de 72 bytes, pero eso es suficiente
    para contraseñas normales
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        Hash de la contraseña
    """
    # Truncar a 72 bytes si es necesario (bcrypt limitation)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash almacenado
    
    Returns:
        True si coinciden, False si no
    """
    # Truncar a 72 bytes igual que en hash_password
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT TOKENS ====================
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un JWT access token
    
    Args:
        data: Datos a incluir en el token (ej: {"sub": "username"})
        expires_delta: Tiempo de expiración (opcional)
    
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un JWT refresh token
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración (opcional)
    
    Returns:
        Refresh token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica y valida un JWT token
    
    Args:
        token: Token JWT a decodificar
    
    Returns:
        Payload del token
    
    Raises:
        HTTPException: Si el token es inválido o expiró
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token_type(payload: Dict[str, Any], expected_type: str):
    """
    Verifica que el token sea del tipo esperado
    
    Args:
        payload: Payload del token
        expected_type: Tipo esperado ("access" o "refresh")
    
    Raises:
        HTTPException: Si el tipo no coincide
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de tipo incorrecto. Se esperaba {expected_type}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== VALIDACIONES ====================
def validate_password_strength(password: str) -> bool:
    """
    Valida que la contraseña cumpla requisitos mínimos
    
    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    
    Args:
        password: Contraseña a validar
    
    Returns:
        True si es válida
    
    Raises:
        ValueError: Con mensaje específico del problema
    """
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    
    if not any(c.isupper() for c in password):
        raise ValueError("La contraseña debe contener al menos una mayúscula")
    
    if not any(c.islower() for c in password):
        raise ValueError("La contraseña debe contener al menos una minúscula")
    
    if not any(c.isdigit() for c in password):
        raise ValueError("La contraseña debe contener al menos un número")
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo para prevenir path traversal
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        Nombre de archivo sanitizado
    """
    import re
    import os
    
    # Remover path separators y caracteres peligrosos
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = filename.replace(' ', '_')
    
    return filename


# ==================== GENERACIÓN DE CÓDIGOS ====================
def generate_secure_code(length: int = 32) -> str:
    """
    Genera un código aleatorio seguro
    
    Args:
        length: Longitud del código
    
    Returns:
        Código hexadecimal aleatorio
    """
    import secrets
    return secrets.token_hex(length // 2)


def generate_numeric_code(length: int = 6) -> str:
    """
    Genera un código numérico aleatorio (para OTP, etc)
    
    Args:
        length: Longitud del código
    
    Returns:
        Código numérico como string
    """
    import secrets
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])