"""
Servicio de autenticación y gestión de usuarios
backend/app/services/auth_service.py
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.models.usuario import Usuario, RolUsuario
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    validate_password_strength
)

logger = logging.getLogger(__name__)


class AuthService:
    """Servicio de autenticación y gestión de usuarios"""
    
    @staticmethod
    def autenticar_usuario(
        db: Session,
        username: str,
        password: str
    ) -> Optional[Usuario]:
        """
        Autentica un usuario por username/email y contraseña
        
        Args:
            db: Sesión de base de datos
            username: Username o email
            password: Contraseña en texto plano
        
        Returns:
            Usuario si las credenciales son correctas, None si no
        """
        # Buscar por username o email
        usuario = db.query(Usuario).filter(
            (Usuario.username == username) | (Usuario.email == username)
        ).first()
        
        if not usuario:
            logger.warning(f"Intento de login con usuario inexistente: {username}")
            return None
        
        # Verificar contraseña
        if not verify_password(password, usuario.password_hash):
            logger.warning(f"Contraseña incorrecta para usuario: {username}")
            return None
        
        # Verificar que el usuario esté activo
        if not usuario.is_active:
            logger.warning(f"Intento de login con usuario inactivo: {username}")
            return None
        
        # Verificar que no esté eliminado (soft delete)
        if usuario.is_deleted:
            logger.warning(f"Intento de login con usuario eliminado: {username}")
            return None
        
        # Actualizar último login
        usuario.last_login = datetime.utcnow().isoformat()
        db.commit()
        
        logger.info(f"[OK] Login exitoso: {username}")
        return usuario
    
    @staticmethod
    def crear_usuario(
        db: Session,
        username: str,
        email: str,
        password: str,
        nombre: str,
        apellido: str,
        rol: RolUsuario = RolUsuario.OPERADOR,
        telefono: Optional[str] = None
    ) -> Usuario:
        """
        Crea un nuevo usuario en el sistema
        
        Args:
            db: Sesión de base de datos
            username: Nombre de usuario único
            email: Email único
            password: Contraseña en texto plano
            nombre: Nombre del usuario
            apellido: Apellido del usuario
            rol: Rol del usuario
            telefono: Teléfono (opcional)
        
        Returns:
            Usuario creado
        
        Raises:
            HTTPException: Si hay conflictos o validaciones fallidas
        """
        # Validar que el username no exista
        if db.query(Usuario).filter(Usuario.username == username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya existe"
            )
        
        # Validar que el email no exista
        if db.query(Usuario).filter(Usuario.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Validar fortaleza de contraseña
        try:
            validate_password_strength(password)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Hashear contraseña
        password_hash = hash_password(password)
        
        # Crear usuario
        nuevo_usuario = Usuario(
            username=username,
            email=email,
            password_hash=password_hash,
            nombre=nombre,
            apellido=apellido,
            rol=rol,
            telefono=telefono,
            is_active=True,
            is_verified=False
        )
        
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        logger.info(f"[OK] Usuario creado: {username} ({rol.value})")
        return nuevo_usuario
    
    @staticmethod
    def generar_tokens(usuario: Usuario) -> Dict[str, str]:
        """
        Genera access token y refresh token para un usuario
        
        Args:
            usuario: Usuario autenticado
        
        Returns:
            Dict con access_token y refresh_token
        """
        # Datos a incluir en el token
        token_data = {
            "sub": usuario.username,
            "user_id": usuario.id,
            "rol": usuario.rol.value,
            "email": usuario.email
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": usuario.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def cambiar_contraseña(
        db: Session,
        usuario_id: int,
        password_actual: str,
        password_nueva: str
    ) -> bool:
        """
        Cambia la contraseña de un usuario
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            password_actual: Contraseña actual
            password_nueva: Nueva contraseña
        
        Returns:
            True si se cambió correctamente
        
        Raises:
            HTTPException: Si la contraseña actual es incorrecta
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar contraseña actual
        if not verify_password(password_actual, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual es incorrecta"
            )
        
        # Validar nueva contraseña
        try:
            validate_password_strength(password_nueva)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Actualizar contraseña
        usuario.password_hash = hash_password(password_nueva)
        db.commit()
        
        logger.info(f"[OK] Contraseña cambiada para usuario: {usuario.username}")
        return True
    
    @staticmethod
    def activar_desactivar_usuario(
        db: Session,
        usuario_id: int,
        activar: bool
    ) -> Usuario:
        """
        Activa o desactiva un usuario
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            activar: True para activar, False para desactivar
        
        Returns:
            Usuario actualizado
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        usuario.is_active = activar
        db.commit()
        db.refresh(usuario)
        
        accion = "activado" if activar else "desactivado"
        logger.info(f"[OK] Usuario {accion}: {usuario.username}")
        
        return usuario
    
    @staticmethod
    def cambiar_rol(
        db: Session,
        usuario_id: int,
        nuevo_rol: RolUsuario
    ) -> Usuario:
        """
        Cambia el rol de un usuario
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            nuevo_rol: Nuevo rol
        
        Returns:
            Usuario actualizado
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        rol_anterior = usuario.rol.value
        usuario.rol = nuevo_rol
        db.commit()
        db.refresh(usuario)
        
        logger.info(
            f"[OK] Rol cambiado para {usuario.username}: "
            f"{rol_anterior} → {nuevo_rol.value}"
        )
        
        return usuario