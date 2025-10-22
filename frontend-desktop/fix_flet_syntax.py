import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazos
    content = content.replace('ft.colors.', 'ft.Colors.')
    content = content.replace('ft.icons.', 'ft.Icons.')
    content = content.replace('ft.colors', 'ft.Colors')
    content = content.replace('page.window_width', 'page.window.width')
    content = content.replace('page.window_height', 'page.window.height')
    content = content.replace('page.window_min_width', 'page.window.min_width')
    content = content.replace('page.window_min_height', 'page.window.min_height')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Corregido: {filepath}")

# Corregir todos los archivos Python en src/
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            fix_file(filepath)

print("\n[OK] Todos los archivos corregidos para Flet 0.28.3")
