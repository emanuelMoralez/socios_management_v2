"""add_soft_delete_indexes

Revision ID: 9d5e401eb1d6
Revises: 227616866937
Create Date: 2025-11-05 00:57:29.171751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d5e401eb1d6'
down_revision = '227616866937'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agregar índices compuestos para optimizar queries con soft deletes.
    
    Mejora performance de queries como:
    - SELECT * FROM usuarios WHERE is_deleted = false
    - SELECT * FROM miembros WHERE is_deleted = false AND estado = 'activo'
    
    Los índices compuestos (is_deleted, id) permiten que PostgreSQL/SQLite
    use el índice para filtrar is_deleted y obtener el id sin escanear toda la tabla.
    """
    # Índice para usuarios (is_deleted, id)
    op.create_index(
        'idx_usuarios_is_deleted_id',
        'usuarios',
        ['is_deleted', 'id'],
        unique=False
    )
    
    # Índice para miembros (is_deleted, id)
    op.create_index(
        'idx_miembros_is_deleted_id',
        'miembros',
        ['is_deleted', 'id'],
        unique=False
    )
    
    # Índice para miembros (is_deleted, estado) para queries combinadas
    op.create_index(
        'idx_miembros_is_deleted_estado',
        'miembros',
        ['is_deleted', 'estado'],
        unique=False
    )


def downgrade() -> None:
    """Revertir índices de soft deletes"""
    op.drop_index('idx_miembros_is_deleted_estado', table_name='miembros')
    op.drop_index('idx_miembros_is_deleted_id', table_name='miembros')
    op.drop_index('idx_usuarios_is_deleted_id', table_name='usuarios')