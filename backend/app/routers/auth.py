"""
Router de autenticación - Login, registro, tokens
backend/app/routers/auth.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    ChangePasswordRequest,
    RefreshTokenRequest
)
from app.schemas.usuario import UsuarioCreate, UsuarioResponse
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user
from app.models.usuario import Usuario
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login de usuario
    
    - **username**: Username o email del usuario
    - **password**: Contraseña
    
    Retorna access_token y refresh_token
    """
    # Autenticar usuario
    usuario = AuthService.autenticar_usuario(
        db=db,
        username=credentials.username,
        password=credentials.password
    )
    
    if not usuario:
        logger.warning(f"Intento de login fallido: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar tokens
    tokens = AuthService.generar_tokens(usuario)
    
    # Agregar datos del usuario a la respuesta
    tokens["user"] = {
        "id": usuario.id,
        "username": usuario.username,
        "email": usuario.email,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol.value,
        "is_active": usuario.is_active
    }
    
    tokens["expires_in"] = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    logger.info(f"[OK] Login exitoso: {usuario.username}")
    
    return tokens


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Registro de nuevo usuario
    
    Crea un usuario en el sistema con rol OPERADOR por defecto.
    Solo usuarios con rol ADMINISTRADOR pueden crear usuarios con otros roles.
    """
    try:
        nuevo_usuario = AuthService.crear_usuario(
            db=db,
            username=usuario_data.username,
            email=usuario_data.email,
            password=usuario_data.password,
            nombre=usuario_data.nombre,
            apellido=usuario_data.apellido,
            rol=usuario_data.rol,
            telefono=usuario_data.telefono
        )
        
        logger.info(f"[OK] Usuario registrado: {nuevo_usuario.username}")
        return nuevo_usuario
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"[ERROR] Error en registro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear usuario"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refrescar access token usando refresh token
    
    - **refresh_token**: Token de refresco válido
    
    Retorna un nuevo access_token
    """
    from app.utils.security import decode_token, verify_token_type, create_access_token
    
    try:
        # Decodificar refresh token
        payload = decode_token(refresh_data.refresh_token)
        
        # Verificar que sea un refresh token
        verify_token_type(payload, "refresh")
        
        # Obtener username
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Buscar usuario
        usuario = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not usuario or not usuario.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no válido"
            )
        
        # Generar nuevo access token
        token_data = {
            "sub": usuario.username,
            "user_id": usuario.id,
            "rol": usuario.rol.value,
            "email": usuario.email
        }
        
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_data.refresh_token,  # Mantener el mismo
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error refrescando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambiar contraseña del usuario actual
    
    Requiere autenticación.
    """
    try:
        AuthService.cambiar_contraseña(
            db=db,
            usuario_id=current_user.id,
            password_actual=password_data.current_password,
            password_nueva=password_data.new_password
        )
        
        logger.info(f"[OK] Contraseña cambiada: {current_user.username}")
        
        return {
            "success": True,
            "message": "Contraseña actualizada correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error cambiando contraseña: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cambiar contraseña"
        )


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener información del usuario actual
    
    Requiere autenticación.
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Logout del usuario
    
    En una implementación con JWT, el logout se maneja en el cliente
    eliminando los tokens. Este endpoint es opcional y puede usarse
    para invalidar tokens en una blacklist (implementación futura).
    """
    logger.info(f" Logout: {current_user.username}")
    
    return {
        "success": True,
        "message": "Logout exitoso"
    }


@router.get("/validate-token")
async def validate_token(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Validar si el token actual es válido
    
    Útil para verificar autenticación sin obtener datos completos.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "rol": current_user.rol.value
    }