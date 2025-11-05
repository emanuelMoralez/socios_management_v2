"""
Schemas de autenticación y tokens
backend/app/schemas/auth.py
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


# ==================== LOGIN ====================
class LoginRequest(BaseModel):
    """Request para login"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username o email"
    )
    password: str = Field(
        ...,
        min_length=4,
        description="Contraseña"
    )


class TokenResponse(BaseModel):
    """Respuesta con tokens JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        default=1800,
        description="Segundos hasta que expire el token"
    )
    user: Optional[dict] = None


class RefreshTokenRequest(BaseModel):
    """Request para refrescar token"""
    refresh_token: str


# ==================== CAMBIO DE CONTRASEÑA ====================
class ChangePasswordRequest(BaseModel):
    """Request para cambiar contraseña"""
    current_password: str = Field(..., min_length=4)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v


class ResetPasswordRequest(BaseModel):
    """Request para resetear contraseña (con token)"""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v


class ForgotPasswordRequest(BaseModel):
    """Request para solicitar reset de contraseña"""
    email: EmailStr


# ==================== VERIFICACIÓN ====================
class VerifyEmailRequest(BaseModel):
    """Request para verificar email"""
    token: str


class ResendVerificationRequest(BaseModel):
    """Request para reenviar email de verificación"""
    email: EmailStr


# ==================== TOKEN PAYLOAD ====================
class TokenPayload(BaseModel):
    """Payload del JWT token"""
    sub: str  # username
    user_id: int
    rol: str
    email: str
    exp: Optional[int] = None
    iat: Optional[int] = None
    type: str = "access"  # access o refresh