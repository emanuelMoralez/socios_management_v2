"""
Caché de categorías para evitar cargas repetitivas
frontend-desktop/src/utils/category_cache.py
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.services.api_client import api_client


class CategoryCache:
    """Caché simple para categorías con TTL"""
    
    _categorias: Optional[List[Dict[str, Any]]] = None
    _last_update: Optional[datetime] = None
    _ttl: int = 300  # 5 minutos
    
    @classmethod
    async def get_categorias(cls) -> List[Dict[str, Any]]:
        """
        Obtener categorías del caché o del servidor
        
        Returns:
            Lista de categorías
        """
        now = datetime.now()
        
        # Si no hay datos o el caché expiró, recargar
        if (cls._categorias is None or 
            cls._last_update is None or 
            (now - cls._last_update).seconds > cls._ttl):
            cls._categorias = await api_client.get_categorias()
            cls._last_update = now
        
        return cls._categorias
    
    @classmethod
    def invalidate(cls):
        """Invalidar caché (llamar después de crear/editar/eliminar categoría)"""
        cls._categorias = None
        cls._last_update = None
    
    @classmethod
    def set_ttl(cls, seconds: int):
        """Cambiar tiempo de vida del caché"""
        cls._ttl = seconds
