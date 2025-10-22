"""
Script para crear usuario administrador inicial
backend/scripts/create_admin.py
"""
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.services.auth_service import AuthService
from app.models.usuario import RolUsuario

def create_admin():
    db = SessionLocal()
    
    try:
        # Verificar si ya existe
        from app.models.usuario import Usuario
        admin_exists = db.query(Usuario).filter(
            Usuario.username == "admin"
        ).first()
        
        if admin_exists:
            print("[WARN]  El usuario 'admin' ya existe")
            print(f"   Username: {admin_exists.username}")
            print(f"   Email: {admin_exists.email}")
            print(f"   Rol: {admin_exists.rol.value}")
            return
        
        # Crear super admin
        admin = AuthService.crear_usuario(
            db=db,
            username="admin",
            email="admin@sistema.com",
            password="Admin123",
            nombre="Administrador",
            apellido="Sistema",
            rol=RolUsuario.SUPER_ADMIN,
            telefono="1234567890"
        )
        
        print("[OK] Usuario administrador creado exitosamente:")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Password: Admin123")
        print(f"   Rol: {admin.rol.value}")
        print(f"\n[AUTH] Usa estas credenciales para hacer login en http://localhost:8000/docs")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()