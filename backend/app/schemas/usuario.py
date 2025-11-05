"""
Schemas para modelo Usuario
backend/app/schemas/usuario.py
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

from app.models.usuario import RolUsuario
from app.schemas.common import TimestampMixin


# ==================== BASE ====================
class UsuarioBase(BaseModel):
    """Schema base de Usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    rol: RolUsuario = RolUsuario.OPERADOR


# ==================== CREATE ====================
class UsuarioCreate(UsuarioBase):
    """Schema para crear usuario"""
    password: str = Field(
        ...,
        min_length=8,
        description="Mínimo 8 caracteres, debe contener mayúscula, minúscula y número"
    )
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v


# ==================== UPDATE ====================
class UsuarioUpdate(BaseModel):
    """Schema para actualizar usuario"""
    email: Optional[EmailStr] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    rol: Optional[RolUsuario] = None
    is_active: Optional[bool] = None


# ==================== RESPONSE ====================
class UsuarioResponse(UsuarioBase, TimestampMixin):
    """Schema para respuesta de usuario (sin password)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_verified: bool
    last_login: Optional[str] = None
    is_deleted: bool = False


class UsuarioListItem(BaseModel):
    """Schema para lista de usuarios (simplificado)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    nombre_completo: str
    rol: RolUsuario
    is_active: bool
    last_login: Optional[str] = None
    created_at: datetime


# ==================== PROFILE ====================
class UsuarioProfile(UsuarioResponse):
    """Schema para perfil completo de usuario"""
    # Agregar campos adicionales si es necesario
    pass


class UpdateProfile(BaseModel):
    """Schema para actualizar perfil propio"""
    email: Optional[EmailStr] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)


# ==================== CAMBIO DE ROL ====================
class CambiarRolRequest(BaseModel):
    """Request para cambiar rol de usuario"""
    usuario_id: int
    nuevo_rol: RolUsuario


# ==================== ACTIVAR/DESACTIVAR ====================
class ToggleActiveRequest(BaseModel):
    """Request para activar/desactivar usuario"""
    usuario_id: int
    activar: bool