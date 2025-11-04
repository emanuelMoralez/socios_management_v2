#!/usr/bin/env python3
"""
Script para migrar automáticamente las vistas al nuevo error handler
frontend-desktop/scripts/migrate_views_to_error_handler.py

Este script actualiza todas las vistas para usar el nuevo sistema
de error handling centralizado.
"""
import re
from pathlib import Path
from typing import List, Tuple


def backup_file(file_path: Path) -> Path:
    """Crear backup del archivo antes de modificar"""
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
    print(f"   📁 Backup creado: {backup_path.name}")
    return backup_path


def check_if_already_migrated(content: str) -> bool:
    """Verificar si el archivo ya fue migrado"""
    return 'from src.utils.error_handler import' in content


def add_import(content: str) -> Tuple[str, bool]:
    """Agregar import del error_handler si no existe"""
    if 'from src.utils.error_handler import' in content:
        return content, False  # Ya tiene el import
    
    # Buscar la línea de import del api_client
    api_client_import = r'from src\.services\.api_client import api_client'
    
    if re.search(api_client_import, content):
        # Agregar después del import de api_client
        new_import = 'from src.services.api_client import api_client\nfrom src.utils.error_handler import handle_api_error, show_success, show_info'
        content = re.sub(api_client_import, new_import, content, count=1)
        return content, True
    
    # Si no encuentra import de api_client, buscar último import de flet
    flet_import = r'(import flet as ft\n)'
    if re.search(flet_import, content):
        new_import = r'\1from src.services.api_client import api_client\nfrom src.utils.error_handler import handle_api_error, show_success, show_info\n'
        content = re.sub(flet_import, new_import, content, count=1)
        return content, True
    
    return content, False


def migrate_exception_handling(content: str, view_name: str) -> Tuple[str, int]:
    """Migrar bloques except Exception a usar handle_api_error"""
    changes_count = 0
    
    # Patrón 1: except Exception as e: con show_snackbar o print
    # Este es el más común
    pattern1 = r'except Exception as (e|ex|error):\s*\n\s*(import traceback.*\n\s*traceback\.print_exc\(\).*\n\s*)?self\.show_snackbar\(f?"([^"]*)[:{].*?[}"].*?(error=True)?\)'
    
    def replace_pattern1(match):
        nonlocal changes_count
        exc_var = match.group(1)
        error_msg = match.group(3)
        
        # Intentar extraer contexto del mensaje de error
        context = ""
        if "Error" in error_msg:
            context = error_msg.replace("Error", "").replace(":", "").strip().lower()
        
        replacement = f'except Exception as {exc_var}:\n                handle_api_error(self.page, {exc_var}, "{context}")'
        changes_count += 1
        return replacement
    
    content = re.sub(pattern1, replace_pattern1, content)
    
    # Patrón 2: self.show_snackbar("Éxito...") → show_success
    pattern2 = r'self\.show_snackbar\("([^"]*exitoso[^"]*?)"\)'
    
    def replace_pattern2(match):
        nonlocal changes_count
        msg = match.group(1)
        replacement = f'show_success(self.page, "{msg}")'
        changes_count += 1
        return replacement
    
    content = re.sub(pattern2, replace_pattern2, content, flags=re.IGNORECASE)
    
    # Patrón 3: except Exception sin variable
    pattern3 = r'except Exception:\s*\n\s*self\.show_snackbar\("([^"]*)"\s*,\s*error=True\)'
    
    def replace_pattern3(match):
        nonlocal changes_count
        msg = match.group(1)
        replacement = f'except Exception as e:\n                handle_api_error(self.page, e, "")'
        changes_count += 1
        return replacement
    
    content = re.sub(pattern3, replace_pattern3, content)
    
    return content, changes_count


def migrate_view_file(file_path: Path, dry_run: bool = False) -> bool:
    """Migrar un archivo de vista"""
    print(f"\n🔍 Analizando: {file_path.name}")
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"   ❌ Error leyendo archivo: {e}")
        return False
    
    # Verificar si ya fue migrado
    if check_if_already_migrated(content):
        print(f"   ✅ Ya migrado anteriormente")
        return True
    
    # Crear backup
    if not dry_run:
        backup_file(file_path)
    
    original_content = content
    
    # 1. Agregar import
    content, import_added = add_import(content)
    if import_added:
        print(f"   ✅ Import agregado")
    
    # 2. Migrar exception handling
    content, changes_count = migrate_exception_handling(content, file_path.stem)
    
    if changes_count > 0:
        print(f"   ✅ {changes_count} bloques de error migrados")
    else:
        print(f"   ℹ️ No se encontraron patrones para migrar")
    
    # Guardar cambios
    if not dry_run and content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"   💾 Archivo actualizado")
        return True
    elif dry_run:
        print(f"   🔍 DRY RUN: No se guardaron cambios")
        if content != original_content:
            print(f"   📊 Se realizarían cambios")
        return True
    else:
        print(f"   ⚠️ No se encontraron cambios necesarios")
        return False
        
    return True


def find_view_files() -> List[Path]:
    """Encontrar todos los archivos de vistas"""
    views_dir = Path(__file__).parent.parent / "src" / "views"
    
    if not views_dir.exists():
        print(f"❌ Directorio de vistas no encontrado: {views_dir}")
        return []
    
    view_files = list(views_dir.glob("*_view.py"))
    
    # Excluir socios_view.py porque ya está migrado
    view_files = [f for f in view_files if f.name != "socios_view.py"]
    
    return sorted(view_files)


def main():
    """Ejecutar migración"""
    print("=" * 70)
    print("🚀 MIGRACIÓN AUTOMÁTICA A ERROR HANDLER")
    print("=" * 70)
    
    print("\n📋 Este script migrará automáticamente las vistas para usar:")
    print("   - handle_api_error() para excepciones")
    print("   - show_success() para mensajes de éxito")
    print("   - show_info() para mensajes informativos")
    
    view_files = find_view_files()
    
    if not view_files:
        print("\n❌ No se encontraron archivos de vistas para migrar")
        return
    
    print(f"\n📁 Archivos encontrados: {len(view_files)}")
    for f in view_files:
        print(f"   - {f.name}")
    
    print("\n⚠️ ADVERTENCIA:")
    print("   - Se crearán backups con extensión .backup")
    print("   - Los cambios son automáticos pero deberías revisarlos")
    print("   - Ejecuta primero en modo DRY RUN para ver qué cambiaría")
    
    respuesta = input("\n¿Ejecutar en modo DRY RUN (ver cambios sin aplicar)? (s/n): ")
    dry_run = respuesta.lower() == 's'
    
    if not dry_run:
        respuesta = input("\n⚠️ ¿CONFIRMAR migración real? (escribe 'SI' para confirmar): ")
        if respuesta != 'SI':
            print("\n❌ Migración cancelada")
            return
    
    print("\n" + "=" * 70)
    print(f"{'🔍 MODO DRY RUN' if dry_run else '🚀 EJECUTANDO MIGRACIÓN'}")
    print("=" * 70)
    
    success_count = 0
    for file_path in view_files:
        if migrate_view_file(file_path, dry_run=dry_run):
            success_count += 1
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    print(f"Archivos procesados: {success_count}/{len(view_files)}")
    
    if dry_run:
        print("\nℹ️ Modo DRY RUN - No se guardaron cambios")
        print("   Ejecuta sin DRY RUN para aplicar cambios reales")
    else:
        print("\n✅ Migración completada")
        print("\n⚠️ SIGUIENTE PASO:")
        print("   1. Revisar cambios con: git diff src/views/")
        print("   2. Probar cada vista manualmente")
        print("   3. Si algo falla, restaurar desde archivos .backup")
        print("   4. Eliminar backups: rm src/views/*.backup")
    
    print("\n💾 Backups creados en: frontend-desktop/src/views/*.backup")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Migración interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
