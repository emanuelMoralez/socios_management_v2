"""
Test de Integración ErrorBanner - categorias_view.py
Valida que ErrorBanner está correctamente integrado en los modales de categorías
"""
import re

def test_categorias_view_integration():
    """Test de integración de ErrorBanner en categorias_view.py"""
    
    print("🧪 TESTING: ErrorBanner en categorias_view.py")
    print("=" * 70)
    
    with open('src/views/categorias_view.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Lista de checks
    checks = []
    errores = []
    
    # ============================================================================
    # CHECK 1: Imports correctos
    # ============================================================================
    if 'from src.components.error_banner import ErrorBanner, SuccessBanner' in content:
        checks.append("✅ Imports de ErrorBanner y SuccessBanner")
    else:
        errores.append("❌ Faltan imports de ErrorBanner/SuccessBanner")
    
    if 'from src.utils.error_handler import handle_api_error_with_banner, show_success' in content:
        checks.append("✅ Imports de error_handler")
    else:
        errores.append("❌ Faltan imports de error_handler")
    
    # ============================================================================
    # CHECK 2: show_nueva_categoria_dialog - Estructura
    # ============================================================================
    if 'def show_nueva_categoria_dialog(self):' in content:
        checks.append("✅ Función show_nueva_categoria_dialog existe")
        
        # Buscar instanciación de banners
        nueva_cat_match = re.search(
            r'def show_nueva_categoria_dialog\(self\):.*?'
            r'(error_banner = ErrorBanner\(\).*?success_banner = SuccessBanner\(\))',
            content,
            re.DOTALL
        )
        
        if nueva_cat_match:
            checks.append("✅ Banners instanciados en show_nueva_categoria_dialog")
        else:
            errores.append("❌ Banners NO instanciados en show_nueva_categoria_dialog")
    else:
        errores.append("❌ show_nueva_categoria_dialog no encontrada")
    
    # ============================================================================
    # CHECK 3: show_nueva_categoria_dialog - Validaciones
    # ============================================================================
    validaciones_nueva = [
        (r"error_banner\.show_error\(['\"]El nombre de la categoría es obligatorio['\"]", 
         "Validación: nombre obligatorio"),
        (r"error_banner\.show_error\(['\"]La cuota base es obligatoria['\"]", 
         "Validación: cuota_base obligatoria"),
        (r"error_banner\.show_error\(['\"]La cuota base no puede ser negativa['\"]", 
         "Validación: cuota >= 0"),
        (r"error_banner\.show_error\(['\"]La cuota base debe ser un número válido['\"]", 
         "Validación: cuota numérica"),
    ]
    
    for pattern, desc in validaciones_nueva:
        if re.search(pattern, content):
            checks.append(f"✅ {desc}")
        else:
            errores.append(f"❌ Falta: {desc}")
    
    # ============================================================================
    # CHECK 4: show_nueva_categoria_dialog - Layout con banners
    # ============================================================================
    if re.search(r'def show_nueva_categoria_dialog.*?ft\.Column\(\s*\[.*?error_banner,.*?success_banner,', 
                 content, re.DOTALL):
        checks.append("✅ Banners agregados al layout de nueva categoría")
    else:
        errores.append("❌ Banners NO agregados al layout de nueva categoría")
    
    # ============================================================================
    # CHECK 5: show_edit_categoria_dialog - Estructura
    # ============================================================================
    if 'def show_edit_categoria_dialog(self, categoria: dict):' in content:
        checks.append("✅ Función show_edit_categoria_dialog existe")
        
        # Buscar instanciación de banners
        edit_cat_match = re.search(
            r'def show_edit_categoria_dialog\(self, categoria: dict\):.*?'
            r'(error_banner = ErrorBanner\(\).*?success_banner = SuccessBanner\(\))',
            content,
            re.DOTALL
        )
        
        if edit_cat_match:
            checks.append("✅ Banners instanciados en show_edit_categoria_dialog")
        else:
            errores.append("❌ Banners NO instanciados en show_edit_categoria_dialog")
    else:
        errores.append("❌ show_edit_categoria_dialog no encontrada")
    
    # ============================================================================
    # CHECK 6: show_edit_categoria_dialog - Validaciones
    # ============================================================================
    validaciones_edit = [
        (r"error_banner\.show_error\(['\"]El nombre de la categoría es obligatorio['\"]", 
         "Editar - Validación: nombre obligatorio"),
        (r"error_banner\.show_error\(['\"]La cuota base es obligatoria['\"]", 
         "Editar - Validación: cuota_base obligatoria"),
        (r"error_banner\.show_error\(['\"]La cuota base no puede ser negativa['\"]", 
         "Editar - Validación: cuota >= 0"),
        (r"error_banner\.show_error\(['\"]La cuota base debe ser un número válido['\"]", 
         "Editar - Validación: cuota numérica"),
    ]
    
    for pattern, desc in validaciones_edit:
        if re.search(pattern, content):
            checks.append(f"✅ {desc}")
        else:
            errores.append(f"❌ Falta: {desc}")
    
    # ============================================================================
    # CHECK 7: show_edit_categoria_dialog - Layout con banners
    # ============================================================================
    if re.search(r'def show_edit_categoria_dialog.*?ft\.Column\(\s*\[.*?error_banner,.*?success_banner,', 
                 content, re.DOTALL):
        checks.append("✅ Banners agregados al layout de editar categoría")
    else:
        errores.append("❌ Banners NO agregados al layout de editar categoría")
    
    # ============================================================================
    # CHECK 8: handle_api_error_with_banner en excepciones
    # ============================================================================
    if content.count('handle_api_error_with_banner') >= 2:
        checks.append("✅ handle_api_error_with_banner usado en ambos modales")
    else:
        errores.append("❌ handle_api_error_with_banner no encontrado en todos los modales")
    
    # ============================================================================
    # CHECK 9: show_success para mensajes exitosos
    # ============================================================================
    if content.count('show_success') >= 2:
        checks.append("✅ show_success usado para mensajes exitosos")
    else:
        errores.append("❌ show_success no encontrado suficientes veces")
    
    # ============================================================================
    # RESULTADOS
    # ============================================================================
    print("\n📋 CHECKS PASADOS:")
    for check in checks:
        print(f"  {check}")
    
    if errores:
        print("\n❌ ERRORES ENCONTRADOS:")
        for error in errores:
            print(f"  {error}")
    
    print("\n" + "=" * 70)
    total_checks = len(checks) + len(errores)
    print(f"📊 RESULTADO: {len(checks)}/{total_checks} checks pasaron")
    
    if not errores:
        print("✅ TODOS LOS TESTS PASARON - categorias_view.py integrado correctamente")
        return True
    else:
        print(f"⚠️  {len(errores)} errores encontrados - revisar integración")
        return False

if __name__ == "__main__":
    success = test_categorias_view_integration()
    exit(0 if success else 1)
