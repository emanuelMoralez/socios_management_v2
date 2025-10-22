"""
Router de administración de usuarios del sistema
backend/app/routers/usuarios.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListItem,
    CambiarRolRequest,
    ToggleActiveRequest
)
from app.schemas.common import MessageResponse
from app.models.usuario import Usuario, RolUsuario
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UsuarioResponse)
async def obtener_perfil(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener perfil del usuario actual
    """
    return current_user


@router.get("", response_model=List[UsuarioListItem])
async def listar_usuarios(
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Listar todos los usuarios del sistema
    
    Solo accesible para administradores.
    """
    usuarios = db.query(Usuario).filter(
        Usuario.is_deleted == False
    ).all()
    
    items = [
        UsuarioListItem(
            id=u.id,
            username=u.username,
            email=u.email,
            nombre_completo=u.nombre_completo,
            rol=u.rol,
            is_active=u.is_active,
            last_login=u.last_login,
            created_at=u.created_at
        )
        for u in usuarios
    ]
    
    return items


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtener detalles de un usuario específico
    """
    usuario = db.query(Usuario).filter(
        Usuario.id == usuario_id,
        Usuario.is_deleted == False
    ).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Actualizar datos de un usuario
    
    Solo administradores pueden cambiar roles.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar campos
    update_data = usuario_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    db.commit()
    db.refresh(usuario)
    
    logger.info(f"[EDIT] Usuario actualizado: {usuario.username}")
    
    return usuario


@router.post("/cambiar-rol", response_model=UsuarioResponse)
async def cambiar_rol_usuario(
    cambio: CambiarRolRequest,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Cambiar el rol de un usuario
    
    Solo super_admin puede crear otros super_admin.
    """
    # Solo SUPER_ADMIN puede cambiar roles a SUPER_ADMIN
    if cambio.nuevo_rol == RolUsuario.SUPER_ADMIN:
        if current_user.rol != RolUsuario.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo SUPER_ADMIN puede asignar ese rol"
            )
    
    usuario = AuthService.cambiar_rol(
        db=db,
        usuario_id=cambio.usuario_id,
        nuevo_rol=cambio.nuevo_rol
    )
    
    return usuario


@router.post("/toggle-active", response_model=MessageResponse)
async def activar_desactivar_usuario(
    toggle: ToggleActiveRequest,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Activar o desactivar un usuario
    
    No se puede desactivar a sí mismo.
    """
    if toggle.usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivarte a ti mismo"
        )
    
    usuario = AuthService.activar_desactivar_usuario(
        db=db,
        usuario_id=toggle.usuario_id,
        activar=toggle.activar
    )
    
    accion = "activado" if toggle.activar else "desactivado"
    
    return MessageResponse(
        message=f"Usuario {accion} correctamente",
        detail=f"Usuario {usuario.username} {accion}"
    )


@router.delete("/{usuario_id}", response_model=MessageResponse)
async def eliminar_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Eliminar usuario (soft delete)
    
    No se puede eliminar a sí mismo.
    """
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo"
        )
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Soft delete
    usuario.soft_delete()
    usuario.is_active = False
    
    db.commit()
    
    logger.warning(f"[DELETE] Usuario eliminado: {usuario.username}")
    
    return MessageResponse(
        message="Usuario eliminado correctamente",
        detail=f"Usuario {usuario.username} dado de baja"
    )