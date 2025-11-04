from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.models.usuario import Usuario, RolUsuario


def elevate_to_super_admin(username: str):
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.username == username).first()
        assert u is not None
        u.rol = RolUsuario.SUPER_ADMIN
        db.commit()
    finally:
        db.close()


def login_headers(client: TestClient, username: str, password: str):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_permissions_and_role_changes(client: TestClient):
    import uuid
    # Usar nombres únicos para evitar colisiones entre tests
    admin_name = f"admin_{uuid.uuid4().hex[:8]}"
    user_name = f"user_{uuid.uuid4().hex[:8]}"
    
    # Create would-be admin
    r = client.post(
        "/api/auth/register",
        json={
            "username": admin_name,
            "email": f"{admin_name}@example.com",
            "password": "Admin1234",
            "confirm_password": "Admin1234",
            "nombre": "Admin",
            "apellido": "Test",
        },
    )
    assert r.status_code == 201, r.text

    # Elevate directly in DB to SUPER_ADMIN to bootstrap permissions
    elevate_to_super_admin(admin_name)
    admin_headers = login_headers(client, admin_name, "Admin1234")

    # Create a normal operator user
    r = client.post(
        "/api/auth/register",
        json={
            "username": user_name,
            "email": f"{user_name}@example.com",
            "password": "Admin1234",
            "confirm_password": "Admin1234",
            "nombre": "User",
            "apellido": "Perm",
        },
    )
    assert r.status_code == 201, r.text

    # Listar usuarios como operador (debe fallar 403 porque require_admin solo permite SUPER_ADMIN y ADMINISTRADOR)
    op_headers = login_headers(client, user_name, "Admin1234")
    r = client.get("/api/usuarios", headers=op_headers)
    # require_admin solo permite SUPER_ADMIN y ADMINISTRADOR, por defecto user_name es OPERADOR
    assert r.status_code == 403

    # Obtener IDs de los usuarios para tests posteriores
    db = SessionLocal()
    try:
        target = db.query(Usuario).filter(Usuario.username == user_name).first()
        admin_user = db.query(Usuario).filter(Usuario.username == admin_name).first()
        assert target is not None and admin_user is not None
        target_id = target.id
        admin_id = admin_user.id
    finally:
        db.close()

    # toggle-active: operador no puede (403) porque require_admin solo permite SUPER_ADMIN/ADMINISTRADOR
    # operador intentando desactivar al admin -> 403
    r = client.post(
        "/api/usuarios/toggle-active",
        headers=op_headers,
        json={"usuario_id": admin_id, "activar": False},
    )
    assert r.status_code == 403

    # Cambiar rol del user_name a administrador usando admin
    r = client.post(
        "/api/usuarios/cambiar-rol",
        headers=admin_headers,
        json={"usuario_id": target_id, "nuevo_rol": "administrador"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["rol"] == "administrador"

    # Ahora admin puede desactivar al usuario (ya es ADMINISTRADOR después del cambio de rol)
    r = client.post(
        "/api/usuarios/toggle-active",
        headers=admin_headers,
        json={"usuario_id": target_id, "activar": False},
    )
    assert r.status_code == 200

    # el propio usuario no puede desactivarse a sí mismo (400 self-deactivation)
    # admin_id ya fue obtenido arriba con los demás IDs
    r = client.post(
        "/api/usuarios/toggle-active",
        headers=admin_headers,
        json={"usuario_id": admin_id, "activar": False},
    )
    assert r.status_code == 400
