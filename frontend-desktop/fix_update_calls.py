import os

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar .update() por self.update() o self.page.update()
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # Si la línea tiene self.algo.update() y no es self.update() o self.page.update()
        if '.update()' in line and 'self.update()' not in line and 'self.page.update()' not in line:
            if 'self.loading.update()' in line:
                line = line.replace('self.loading.update()', 'self.update()')
            elif 'self.data_table.update()' in line:
                line = line.replace('self.data_table.update()', 'self.update()')
            elif 'self.pagination.update()' in line:
                line = line.replace('self.pagination.update()', 'self.update()')
            elif 'self.error_text.update()' in line:
                line = line.replace('self.error_text.update()', 'self.update()')
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Corregido: {filepath}")

# Corregir archivos en src/views/
for file in ['socios_view.py', 'pagos_view.py', 'accesos_view.py', 'login_view.py']:
    filepath = f'src/views/{file}'
    if os.path.exists(filepath):
        fix_file(filepath)

print("\n[OK] Correcciones aplicadas")