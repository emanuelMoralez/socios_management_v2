"""
Tests para el script de purga de auditoría
backend/tests/test_purge_audit.py
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Actividad, Usuario
from app.config import settings
from scripts.purge_audit import purge_old_audit_records, archive_to_csv


@pytest.fixture
def test_db():
    """Crear base de datos de prueba en memoria"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    
    # Monkey-patch SessionLocal en el módulo del script
    import scripts.purge_audit
    original_session = scripts.purge_audit.SessionLocal
    scripts.purge_audit.SessionLocal = TestingSessionLocal
    
    yield TestingSessionLocal
    
    # Restaurar SessionLocal original
    scripts.purge_audit.SessionLocal = original_session


@pytest.fixture
def sample_activities(test_db):
    """Crear actividades de prueba con diferentes fechas"""
    db = test_db()
    
    # Crear usuario de prueba
    usuario = Usuario(
        username="test_user",
        nombre="Test",
        apellido="User",
        email="test@example.com",
        password_hash="fake_hash",
        rol="operador"
    )
    db.add(usuario)
    db.commit()
    
    # Actividades antiguas (100 días)
    old_date = datetime.utcnow() - timedelta(days=100)
    for i in range(10):
        actividad = Actividad(
            tipo="LOGIN_EXITOSO",
            descripcion=f"Login antiguo {i}",
            severidad="INFO",
            usuario_id=usuario.id,
            ip_address="192.168.1.1",
            fecha_hora=old_date - timedelta(hours=i)
        )
        db.add(actividad)
    
    # Actividades recientes (10 días)
    recent_date = datetime.utcnow() - timedelta(days=10)
    for i in range(5):
        actividad = Actividad(
            tipo="MIEMBRO_CREADO",
            descripcion=f"Miembro nuevo {i}",
            severidad="INFO",
            usuario_id=usuario.id,
            ip_address="192.168.1.2",
            fecha_hora=recent_date - timedelta(hours=i)
        )
        db.add(actividad)
    
    db.commit()
    db.close()
    
    return {"old_count": 10, "recent_count": 5, "total": 15}


def test_purge_audit_dry_run(test_db, sample_activities):
    """Test de purga en modo dry-run"""
    stats = purge_old_audit_records(retention_days=30, dry_run=True)
    
    # Debe detectar los 10 registros antiguos
    assert stats['total_old_records'] == 10
    # No debe eliminar nada en dry-run
    assert stats['deleted'] == 0
    assert stats['archived'] == 0
    
    # Verificar que no se eliminó nada
    db = test_db()
    total_after = db.query(Actividad).count()
    db.close()
    assert total_after == 15


def test_purge_audit_without_archive(test_db, sample_activities):
    """Test de purga sin archivar"""
    stats = purge_old_audit_records(
        retention_days=30,
        dry_run=False,
        skip_archive=True
    )
    
    # Debe detectar y eliminar los 10 registros antiguos
    assert stats['total_old_records'] == 10
    assert stats['deleted'] == 10
    assert stats['archived'] == 0
    
    # Verificar que solo quedan los 5 recientes
    db = test_db()
    total_after = db.query(Actividad).count()
    db.close()
    assert total_after == 5


def test_purge_audit_with_archive(test_db, sample_activities, tmp_path):
    """Test de purga con archivado"""
    # Configurar directorio temporal para archivos
    import scripts.purge_audit
    original_archive_dir = settings.AUDIT_ARCHIVE_DIR
    settings.AUDIT_ARCHIVE_DIR = str(tmp_path / "archives")
    
    try:
        stats = purge_old_audit_records(
            retention_days=30,
            dry_run=False,
            skip_archive=False
        )
        
        # Debe detectar, archivar y eliminar los 10 registros antiguos
        assert stats['total_old_records'] == 10
        assert stats['archived'] == 10
        assert stats['deleted'] == 10
        assert len(stats['errors']) == 0
        
        # Verificar que se creó el archivo CSV
        archive_files = list(Path(settings.AUDIT_ARCHIVE_DIR).glob("*.csv"))
        assert len(archive_files) >= 1
        
        # Verificar contenido del CSV
        with open(archive_files[0], 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Header + 10 registros = 11 líneas
            assert len(lines) == 11
            assert 'Login antiguo' in ''.join(lines)
        
        # Verificar que solo quedan los 5 recientes
        db = test_db()
        total_after = db.query(Actividad).count()
        db.close()
        assert total_after == 5
        
    finally:
        # Restaurar configuración
        settings.AUDIT_ARCHIVE_DIR = original_archive_dir


def test_purge_audit_no_old_records(test_db):
    """Test cuando no hay registros antiguos"""
    # Crear solo actividades recientes
    db = test_db()
    usuario = Usuario(
        username="test_user",
        nombre="Test",
        apellido="User",
        email="test@example.com",
        password_hash="fake_hash",
        rol="operador"
    )
    db.add(usuario)
    db.commit()
    
    for i in range(3):
        actividad = Actividad(
            tipo="LOGIN_EXITOSO",
            descripcion=f"Login reciente {i}",
            severidad="INFO",
            usuario_id=usuario.id,
            fecha_hora=datetime.utcnow() - timedelta(hours=i)
        )
        db.add(actividad)
    db.commit()
    db.close()
    
    # Intentar purgar con 30 días de retención
    stats = purge_old_audit_records(retention_days=30)
    
    assert stats['total_old_records'] == 0
    assert stats['deleted'] == 0
    assert stats['archived'] == 0


def test_archive_to_csv(tmp_path):
    """Test de archivado a CSV"""
    # Crear actividades de prueba
    activities = []
    for i in range(5):
        act = Actividad(
            id=i+1,
            tipo="LOGIN_EXITOSO",
            descripcion=f"Test {i}",
            severidad="INFO",
            usuario_id=1,
            ip_address="192.168.1.1",
            fecha_hora=datetime.utcnow()
        )
        activities.append(act)
    
    # Archivar
    archive_path = tmp_path / "test_archive.csv"
    result = archive_to_csv(activities, archive_path)
    
    assert result is True
    assert archive_path.exists()
    
    # Verificar contenido
    with open(archive_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) == 6  # header + 5 records
        assert 'Test 0' in ''.join(lines)
        assert 'LOGIN_EXITOSO' in ''.join(lines)


def test_purge_with_different_retention(test_db):
    """Test con diferentes períodos de retención"""
    db = test_db()
    
    # Crear usuario
    usuario = Usuario(
        username="test_user",
        nombre="Test",
        apellido="User",
        email="test@example.com",
        password_hash="fake_hash",
        rol="operador"
    )
    db.add(usuario)
    db.commit()
    
    # Actividades a 150 días
    for i in range(5):
        act = Actividad(
            tipo="LOGIN_EXITOSO",
            descripcion=f"Muy antiguo {i}",
            severidad="INFO",
            usuario_id=usuario.id,
            fecha_hora=datetime.utcnow() - timedelta(days=150)
        )
        db.add(act)
    
    # Actividades a 60 días
    for i in range(3):
        act = Actividad(
            tipo="LOGIN_EXITOSO",
            descripcion=f"Antiguo {i}",
            severidad="INFO",
            usuario_id=usuario.id,
            fecha_hora=datetime.utcnow() - timedelta(days=60)
        )
        db.add(act)
    
    # Actividades a 10 días
    for i in range(2):
        act = Actividad(
            tipo="LOGIN_EXITOSO",
            descripcion=f"Reciente {i}",
            severidad="INFO",
            usuario_id=usuario.id,
            fecha_hora=datetime.utcnow() - timedelta(days=10)
        )
        db.add(act)
    
    db.commit()
    db.close()
    
    # Test 1: Retención de 90 días (debe eliminar las 5 muy antiguas)
    stats = purge_old_audit_records(retention_days=90, skip_archive=True)
    assert stats['deleted'] == 5
    
    db = test_db()
    assert db.query(Actividad).count() == 5  # 3 + 2
    db.close()
    
    # Test 2: Retención de 30 días (debe eliminar las 3 antiguas)
    stats = purge_old_audit_records(retention_days=30, skip_archive=True)
    assert stats['deleted'] == 3
    
    db = test_db()
    assert db.query(Actividad).count() == 2  # Solo las 2 recientes
    db.close()
