#!/usr/bin/env python3
"""
Script para eliminar emojis de archivos Python
Reemplaza emojis comunes con equivalentes en texto
"""
import re
import os
from pathlib import Path

# Mapeo de emojis a texto
EMOJI_REPLACEMENTS = {
    '🚀': '[INIT]',
    '📌': '[INFO]',
    '✅': '[OK]',
    '❌': '[ERROR]',
    '⚠️': '[WARN]',
    '🔧': '[CONFIG]',
    '📊': '[DATA]',
    '💾': '[SAVE]',
    '🔍': '[SEARCH]',
    '📝': '[LOG]',
    '🔐': '[AUTH]',
    '🔑': '[KEY]',
    '👤': '[USER]',
    '📧': '[EMAIL]',
    '📱': '[PHONE]',
    '🏠': '[HOME]',
    '🌐': '[WEB]',
    '📚': '[DOCS]',
    '🗑️': '[DELETE]',
    '✏️': '[EDIT]',
    '➕': '[ADD]',
    '➖': '[REMOVE]',
    '🔄': '[REFRESH]',
    '💰': '[MONEY]',
    '💳': '[PAYMENT]',
    '📅': '[DATE]',
    '⏰': '[TIME]',
    '✔️': '[CHECK]',
    '❎': '[CANCEL]',
    '🎯': '[TARGET]',
    '📈': '[CHART]',
    '💡': '[IDEA]',
}

def remove_emojis_from_text(text):
    """Reemplaza emojis conocidos y elimina desconocidos"""
    # Primero reemplazar emojis conocidos
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        text = text.replace(emoji, replacement)
    
    # Eliminar cualquier emoji restante (caracteres Unicode de emoji)
    # Rango de emojis en Unicode
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
        u"\U00002600-\U000026FF"  # Miscellaneous Symbols
        "]+", 
        flags=re.UNICODE
    )
    text = emoji_pattern.sub(r'', text)
    
    return text

def process_file(filepath):
    """Procesar un archivo y eliminar emojis"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content = remove_emojis_from_text(content)
        
        if original_content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, "Modificado"
        else:
            return False, "Sin cambios"
            
    except Exception as e:
        return False, f"Error: {e}"

def process_directory(directory, extensions=['.py']):
    """Procesar todos los archivos en un directorio"""
    directory = Path(directory)
    modified_files = []
    
    print(f"Procesando directorio: {directory}")
    print("=" * 60)
    
    for filepath in directory.rglob('*'):
        if filepath.is_file() and filepath.suffix in extensions:
            # Ignorar venv, __pycache__, etc.
            if any(part in filepath.parts for part in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            modified, status = process_file(filepath)
            relative_path = filepath.relative_to(directory)
            
            if modified:
                modified_files.append(str(relative_path))
                print(f"✓ {relative_path} - {status}")
            else:
                print(f"  {relative_path} - {status}")
    
    print("=" * 60)
    print(f"\nArchivos modificados: {len(modified_files)}")
    if modified_files:
        print("\nLista de archivos modificados:")
        for f in modified_files:
            print(f"  - {f}")
    
    return modified_files

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python remove_emojis.py <directorio>")
        print("Ejemplo: python remove_emojis.py ./backend")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    
    if not os.path.exists(target_dir):
        print(f"Error: El directorio '{target_dir}' no existe")
        sys.exit(1)
    
    print("Script para eliminar emojis de archivos Python")
    print(f"Directorio objetivo: {target_dir}\n")
    
    # Confirmar antes de proceder
    response = input("¿Continuar? (s/n): ")
    if response.lower() != 's':
        print("Operación cancelada")
        sys.exit(0)
    
    print()
    modified = process_directory(target_dir)
    
    print("\n¡Proceso completado!")
    if modified:
        print("\nRecuerda revisar los cambios con git diff antes de commitear.")
