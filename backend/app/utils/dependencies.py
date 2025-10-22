"""
FastAPI Dependencies para autenticación y autorización
backend/app/utils/dependencies.py
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, RolUsuario
from app.utils.security import decode_token, verify_token_type

# Esquema de seguridad Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency para obtener el usuario actual desde el JWT token
    
    Uso en routers:
    @router.get("/protected")
    def protected_route(current_user: Usuario = Depends(get_current_user)):
        return {"user": current_user.username}
    """
    token = credentials.credentials
    
    # Decodificar token
    payload = decode_token(token)
    
    # Verificar que sea un access token
    verify_token_type(payload, "access")
    
    # Obtener username del token
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: no contiene username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuario en BD
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que esté activo
    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    # Verificar que no esté eliminado
    if usuario.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario eliminado"
        )
    
    return usuario


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependency para verificar que el usuario esté activo
    (Ya verificado en get_current_user, pero se mantiene por claridad)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


class RoleChecker:
    """
    Dependency class para verificar roles de usuario
    
    Uso:
    @router.get("/admin-only")
    def admin_route(
        current_user: Usuario = Depends(RoleChecker([RolUsuario.SUPER_ADMIN, RolUsuario.ADMINISTRADOR]))
    ):
        return {"message": "Solo admins"}
    """
    
    def __init__(self, allowed_roles: list[RolUsuario]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere uno de: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Shortcuts para roles comunes
def require_super_admin(
    current_user: Usuario = Depends(
        RoleChecker([RolUsuario.SUPER_ADMIN])
    )
) -> Usuario:
    """Requiere rol SUPER_ADMIN"""
    return current_user


def require_admin(
    current_user: Usuario = Depends(
        RoleChecker([RolUsuario.SUPER_ADMIN, RolUsuario.ADMINISTRADOR])
    )
) -> Usuario:
    """Requiere rol SUPER_ADMIN o ADMINISTRADOR"""
    return current_user


def require_operador(
    current_user: Usuario = Depends(
        RoleChecker([
            RolUsuario.SUPER_ADMIN,
            RolUsuario.ADMINISTRADOR,
            RolUsuario.OPERADOR
        ])
    )
) -> Usuario:
    """Requiere rol OPERADOR o superior"""
    return current_user


def require_portero(
    current_user: Usuario = Depends(
        RoleChecker([
            RolUsuario.SUPER_ADMIN,
            RolUsuario.ADMINISTRADOR,
            RolUsuario.OPERADOR,
            RolUsuario.PORTERO
        ])
    )
) -> Usuario:
    """Requiere rol PORTERO o superior (para control de acceso)"""
    return current_user


# ==================== PAGINACIÓN ====================
class PaginationParams:
    """
    Dependency para parámetros de paginación
    
    Uso:
    @router.get("/items")
    def get_items(pagination: PaginationParams = Depends()):
        skip = pagination.skip
        limit = pagination.limit
    """
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20
    ):
        from app.config import settings
        
        if page < 1:
            page = 1
        
        if page_size < 1:
            page_size = settings.DEFAULT_PAGE_SIZE
        
        if page_size > settings.MAX_PAGE_SIZE:
            page_size = settings.MAX_PAGE_SIZE
        
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size
        self.limit = page_size
    
    def get_metadata(self, total: int) -> dict:
        """
        Genera metadata de paginación
        
        Args:
            total: Total de registros
        
        Returns:
            Dict con metadata de paginación
        """
        import math
        
        total_pages = math.ceil(total / self.page_size)
        
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": self.page < total_pages,
            "has_prev": self.page > 1
        }


# ==================== FILTROS ====================
class SearchParams:
    """
    Dependency para parámetros de búsqueda
    
    Uso:
    @router.get("/search")
    def search(search: SearchParams = Depends()):
        query = search.q
    """
    
    def __init__(
        self,
        q: Optional[str] = None,
        order_by: Optional[str] = None,
        order_dir: str = "asc"
    ):
        self.q = q.strip() if q else None
        self.order_by = order_by
        self.order_dir = order_dir.lower() if order_dir.lower() in ["asc", "desc"] else "asc"