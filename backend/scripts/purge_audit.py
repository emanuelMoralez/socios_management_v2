"""
Script para purgar registros antiguos de auditoría
backend/scripts/purge_audit.py

Uso:
    # Usar AUDIT_RETENTION_DAYS del config
    python -m scripts.purge_audit
    
    # Especificar días de retención
    python -m scripts.purge_audit --days 30
    
    # Modo dry-run (sin eliminar)
    python -m scripts.purge_audit --dry-run
    
    # Sin archivar (solo eliminar)
    python -m scripts.purge_audit --no-archive
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import csv
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func
from app.database import SessionLocal
from app.models import Actividad
from app.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def archive_to_csv(activities: list, archive_path: Path) -> bool:
    """
    Archivar actividades a CSV
    
    Args:
        activities: Lista de objetos Actividad
        archive_path: Path al archivo CSV
        
    Returns:
        True si se archivó correctamente
    """
    try:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(archive_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'tipo', 'descripcion', 'severidad',
                'usuario_id',
                'entidad_tipo', 'entidad_id',
                'ip_address', 'user_agent',
                'datos_adicionales', 'fecha_hora'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for act in activities:
                writer.writerow({
                    'id': act.id,
                    'tipo': act.tipo,
                    'descripcion': act.descripcion,
                    'severidad': act.severidad,
                    'usuario_id': act.usuario_id,
                    'entidad_tipo': act.entidad_tipo,
                    'entidad_id': act.entidad_id,
                    'ip_address': act.ip_address,
                    'user_agent': act.user_agent,
                    'datos_adicionales': str(act.datos_adicionales) if act.datos_adicionales else '',
                    'fecha_hora': act.fecha_hora.isoformat() if act.fecha_hora else ''
                })
        
        logger.info(f"✅ Archivado {len(activities)} registros en {archive_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al archivar: {e}")
        return False


def purge_old_audit_records(
    retention_days: int,
    dry_run: bool = False,
    skip_archive: bool = False
) -> dict:
    """
    Purgar registros de auditoría antiguos
    
    Args:
        retention_days: Días de retención
        dry_run: Si True, solo muestra lo que se eliminaría
        skip_archive: Si True, no archiva antes de eliminar
        
    Returns:
        Dict con estadísticas: {
            'total_old_records': int,
            'archived': int,
            'deleted': int,
            'errors': list
        }
    """
    db = SessionLocal()
    stats = {
        'total_old_records': 0,
        'archived': 0,
        'deleted': 0,
        'errors': []
    }
    
    try:
        # Calcular fecha límite
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        logger.info(f"📅 Fecha límite: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Contar registros a purgar
        count_query = db.query(func.count(Actividad.id)).filter(
            Actividad.fecha_hora < cutoff_date
        )
        total_old = count_query.scalar()
        stats['total_old_records'] = total_old
        
        if total_old == 0:
            logger.info("✅ No hay registros antiguos para purgar")
            return stats
        
        logger.info(f"🔍 Encontrados {total_old} registros más antiguos que {retention_days} días")
        
        if dry_run:
            logger.info("🔸 Modo DRY-RUN: no se realizarán cambios")
            # Mostrar resumen por severidad
            severities = db.query(
                Actividad.severidad,
                func.count(Actividad.id)
            ).filter(
                Actividad.fecha_hora < cutoff_date
            ).group_by(Actividad.severidad).all()
            
            logger.info("📊 Resumen por severidad:")
            for sev, count in severities:
                logger.info(f"  - {sev}: {count}")
            
            return stats
        
        # Obtener registros a purgar (en lotes para no saturar memoria)
        BATCH_SIZE = 1000
        offset = 0
        total_archived = 0
        total_deleted = 0
        
        while True:
            # Obtener lote
            batch = db.query(Actividad).filter(
                Actividad.fecha_hora < cutoff_date
            ).limit(BATCH_SIZE).offset(offset).all()
            
            if not batch:
                break
            
            logger.info(f"📦 Procesando lote {offset // BATCH_SIZE + 1} ({len(batch)} registros)")
            
            # Archivar lote si corresponde
            if not skip_archive:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                batch_num = offset // BATCH_SIZE + 1
                archive_dir = Path(settings.AUDIT_ARCHIVE_DIR)
                archive_file = archive_dir / f"audit_archive_{timestamp}_batch{batch_num}.csv"
                
                if archive_to_csv(batch, archive_file):
                    total_archived += len(batch)
                else:
                    stats['errors'].append(f"Error al archivar lote {batch_num}")
                    # Continuar con siguiente lote sin eliminar este
                    offset += BATCH_SIZE
                    continue
            
            # Eliminar lote
            batch_ids = [act.id for act in batch]
            deleted_count = db.query(Actividad).filter(
                Actividad.id.in_(batch_ids)
            ).delete(synchronize_session=False)
            
            db.commit()
            total_deleted += deleted_count
            logger.info(f"🗑️  Eliminados {deleted_count} registros")
            
            # No aumentar offset porque al eliminar, los siguientes suben
            # Solo aumentar si hay más registros después
            if len(batch) < BATCH_SIZE:
                break
        
        stats['archived'] = total_archived
        stats['deleted'] = total_deleted
        
        logger.info(f"""
╔════════════════════════════════════════════════╗
║          RESUMEN DE PURGA DE AUDITORÍA         ║
╠════════════════════════════════════════════════╣
║ Registros antiguos:     {total_old:>8}           ║
║ Archivados:             {total_archived:>8}           ║
║ Eliminados:             {total_deleted:>8}           ║
║ Errores:                {len(stats['errors']):>8}           ║
╚════════════════════════════════════════════════╝
        """)
        
        if stats['errors']:
            logger.warning("⚠️  Errores durante la purga:")
            for error in stats['errors']:
                logger.warning(f"  - {error}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error en purga: {e}", exc_info=True)
        stats['errors'].append(str(e))
    
    finally:
        db.close()
    
    return stats


def main():
    """Punto de entrada del script"""
    parser = argparse.ArgumentParser(
        description='Purgar registros antiguos de auditoría',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Usar config por defecto (90 días)
  python -m scripts.purge_audit
  
  # Retención de 30 días
  python -m scripts.purge_audit --days 30
  
  # Modo dry-run (ver qué se eliminaría)
  python -m scripts.purge_audit --dry-run
  
  # Solo eliminar (sin archivar)
  python -m scripts.purge_audit --no-archive --days 30
        """
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=settings.AUDIT_RETENTION_DAYS,
        help=f'Días de retención (default: {settings.AUDIT_RETENTION_DAYS})'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo simulación (no elimina registros)'
    )
    
    parser.add_argument(
        '--no-archive',
        action='store_true',
        help='No archivar antes de eliminar'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Iniciando script de purga de auditoría")
    logger.info(f"⚙️  Config: retention_days={args.days}, dry_run={args.dry_run}, skip_archive={args.no_archive}")
    
    stats = purge_old_audit_records(
        retention_days=args.days,
        dry_run=args.dry_run,
        skip_archive=args.no_archive
    )
    
    # Exit code basado en errores
    if stats['errors']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
