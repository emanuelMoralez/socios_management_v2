#!/usr/bin/env python3
"""
Script para encontrar uso de métodos obsoletos del api_client
frontend-desktop/scripts/find_deprecated_api_methods.py

Uso: python scripts/find_deprecated_api_methods.py
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Métodos obsoletos y sus reemplazos
DEPRECATED_METHODS = {
    "obtener_historial_accesos": "get_accesos",
    "obtener_resumen_accesos": "get_resumen_accesos",
    "obtener_estadisticas_accesos": "get_estadisticas_accesos",
}

# Colores para terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def find_method_usage(directory: str, method_name: str) -> List[Tuple[str, int, str]]:
    """
    Busca el uso de un método en archivos .py
    
    Returns:
        Lista de tuplas (archivo, línea, contenido)
    """
    results = []
    pattern = re.compile(rf'\b{method_name}\s*\(')
    
    for root, dirs, files in os.walk(directory):
        # Ignorar directorios
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # Saltar el propio api_client.py
                if 'api_client.py' in filepath:
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                results.append((filepath, line_num, line.strip()))
                except Exception as e:
                    print(f"{RED}Error leyendo {filepath}: {e}{RESET}")
    
    return results


def main():
    """Buscar todos los métodos obsoletos"""
    
    # Directorio raíz del frontend
    frontend_dir = Path(__file__).parent.parent
    src_dir = frontend_dir / "src"
    
    if not src_dir.exists():
        print(f"{RED}Error: Directorio src/ no encontrado{RESET}")
        return
    
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🔍 BUSCANDO MÉTODOS OBSOLETOS DEL API_CLIENT{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    total_found = 0
    
    for deprecated, replacement in DEPRECATED_METHODS.items():
        print(f"{YELLOW}Buscando: {deprecated}(){RESET}")
        print(f"{GREEN}Reemplazar por: {replacement}(){RESET}\n")
        
        results = find_method_usage(str(src_dir), deprecated)
        
        if results:
            total_found += len(results)
            for filepath, line_num, line_content in results:
                # Hacer path relativo
                rel_path = os.path.relpath(filepath, frontend_dir)
                print(f"  📄 {rel_path}:{line_num}")
                print(f"     {line_content}")
                print()
        else:
            print(f"  {GREEN}✅ No se encontraron usos{RESET}\n")
        
        print(f"{'-'*70}\n")
    
    # Resumen
    print(f"{BLUE}{'='*70}{RESET}")
    if total_found == 0:
        print(f"{GREEN}✅ ¡Excelente! No se encontraron métodos obsoletos{RESET}")
        print(f"{GREEN}   El código ya está actualizado.{RESET}")
    else:
        print(f"{YELLOW}⚠️  Se encontraron {total_found} usos de métodos obsoletos{RESET}")
        print(f"{YELLOW}   Acción requerida: Actualizar los archivos listados arriba{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    # Ejemplos de reemplazo
    if total_found > 0:
        print(f"{BLUE}📝 EJEMPLOS DE MIGRACIÓN:{RESET}\n")
        
        print(f"{YELLOW}# ANTES:{RESET}")
        print(f"accesos = await api_client.obtener_historial_accesos(")
        print(f"    miembro_id=123,")
        print(f"    fecha_inicio='2025-01-01',")
        print(f"    page=1")
        print(f")\n")
        
        print(f"{GREEN}# DESPUÉS:{RESET}")
        print(f"accesos = await api_client.get_accesos(")
        print(f"    miembro_id=123,")
        print(f"    fecha_inicio='2025-01-01',")
        print(f"    page=1")
        print(f")\n")
        
        print(f"{BLUE}💡 TIP: Los parámetros son iguales, solo cambia el nombre del método{RESET}\n")


if __name__ == "__main__":
    main()
