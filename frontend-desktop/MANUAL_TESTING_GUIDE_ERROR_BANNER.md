# Guía de Prueba Manual - ErrorBanner en Socios

## 📋 Resumen de Cambios

Se implementó el componente reutilizable `ErrorBanner` en el modal de creación de socios para mostrar errores de validación directamente en el contexto del formulario, mejorando la experiencia de usuario.

### Cambios Realizados

1. **Nuevo componente**: `frontend-desktop/src/components/error_banner.py`
   - `ErrorBanner`: Banner para errores/advertencias/validaciones
   - `SuccessBanner`: Banner para mensajes de éxito
   - Soporte para 3 tipos de errores (validation, error, warning)
   - Auto-hide opcional con duración configurable
   - Botón de cerrar integrado

2. **Actualización de error_handler.py**
   - Nueva función: `handle_api_error_with_banner()`
   - Maneja errores y los muestra en banner en lugar de snackbar global

3. **Actualización de socios_view.py**
   - Integrado `ErrorBanner` y `SuccessBanner` en `show_nuevo_socio_dialog()`
   - Los errores ahora se muestran dentro del modal
   - El modal NO se cierra en caso de error (permite correcciones)

---

## 🧪 Casos de Prueba

### ✅ Test 1: Validación de campos obligatorios

**Pasos:**
1. Ejecutar app: `cd frontend-desktop && python -m src.main`
2. Login con credenciales válidas (admin / Admin123)
3. Ir a vista "Socios"
4. Click en botón "Nuevo Socio"
5. Dejar campos vacíos y click en "Guardar"

**Resultado esperado:**
- ✅ Aparece banner naranja en la parte superior del modal
- ✅ Mensaje: "⚠️ Completa los campos obligatorios (*)"
- ✅ El modal permanece abierto
- ✅ NO aparece snackbar en la página

---

### ✅ Test 2: Validación de email inválido

**Pasos:**
1. En el diálogo "Nuevo Socio", completar:
   - Nombre: Juan
   - Apellido: Pérez
   - Documento: 12345678
   - Email: `invalid` (sin @)
   - Categoría: Seleccionar cualquiera
2. Click en "Guardar"

**Resultado esperado:**
- ✅ Aparece banner naranja con errores de validación
- ✅ Mensaje muestra: "Errores de validación:" seguido de lista con viñetas
- ✅ Incluye: "• email: formato de email inválido" (o similar)
- ✅ El modal permanece abierto
- ✅ El usuario puede corregir el campo sin reabrir el modal

---

### ✅ Test 3: Múltiples errores de validación

**Pasos:**
1. En el diálogo "Nuevo Socio", completar:
   - Nombre: Juan
   - Apellido: Pérez
   - Documento: 12345678
   - Email: `bad-email`
   - Teléfono: `abc` (si backend valida formato)
   - Categoría: Seleccionar cualquiera
2. Click en "Guardar"

**Resultado esperado:**
- ✅ Aparece banner naranja con múltiples errores
- ✅ Cada error en una línea con viñeta (•)
- ✅ Lista todos los campos con error
- ✅ El modal permanece abierto

---

### ✅ Test 4: Creación exitosa

**Pasos:**
1. En el diálogo "Nuevo Socio", completar con datos válidos:
   - Nombre: Carlos
   - Apellido: González
   - Documento: 98765432
   - Email: `carlos@example.com`
   - Categoría: Seleccionar cualquiera
2. Click en "Guardar"

**Resultado esperado:**
- ✅ El modal se cierra
- ✅ Aparece snackbar verde en la página: "Socio creado exitosamente"
- ✅ La tabla de socios se actualiza con el nuevo registro
- ✅ NO aparece banner en el modal (ya cerrado)

---

### ✅ Test 5: Cerrar banner manualmente

**Pasos:**
1. Provocar un error de validación (email inválido)
2. Ver que aparece el banner naranja
3. Click en el botón "X" del banner

**Resultado esperado:**
- ✅ El banner desaparece con animación suave
- ✅ El modal permanece abierto
- ✅ Los campos mantienen sus valores

---

### ✅ Test 6: Corrección de errores

**Pasos:**
1. Provocar error de validación (email inválido: `bad`)
2. Ver banner naranja con error
3. Corregir el email a `valid@example.com`
4. Click en "Guardar" nuevamente

**Resultado esperado:**
- ✅ El banner de error desaparece (se limpia en `guardar_socio()`)
- ✅ El modal se cierra
- ✅ Snackbar verde: "Socio creado exitosamente"
- ✅ Tabla actualizada

---

### ✅ Test 7: Error de red/servidor

**Pasos:**
1. Detener el backend: Ctrl+C en terminal del backend
2. En frontend, intentar crear socio con datos válidos
3. Click en "Guardar"

**Resultado esperado:**
- ✅ Aparece banner rojo (error tipo "error", no "validation")
- ✅ Mensaje: "❌ Error al crear socio" o similar
- ✅ Puede incluir detalles técnicos (timeout, connection refused, etc.)
- ✅ El modal permanece abierto

---

## 🎨 Validación Visual

### Colores del Banner

- **Validación** (tipo="validation"): 🟠 Naranja (`ft.Colors.ORANGE_700`)
- **Error** (tipo="error"): 🔴 Rojo (`ft.Colors.RED_700`)
- **Advertencia** (tipo="warning"): 🟡 Naranja claro (`ft.Colors.ORANGE_400`)
- **Éxito** (SuccessBanner): 🟢 Verde (`ft.Colors.GREEN_700`)

### Estructura del Banner

```
┌─────────────────────────────────────────────┐
│ ⚠️  Mensaje de error aquí                 ✕ │
│ • Detalle 1                                 │
│ • Detalle 2                                 │
└─────────────────────────────────────────────┘
```

- **Icono izquierdo**: Según tipo (⚠️ warning, ❌ error, ℹ️ info)
- **Mensaje**: Texto blanco, tamaño 13
- **Botón X**: Esquina derecha, tooltip "Cerrar"
- **Animación**: Fade in/out suave (200ms)

---

## 📊 Verificación de No-Regresiones

### Funcionalidad Existente que NO debe cambiar:

1. ✅ Snackbar verde de éxito sigue apareciendo al crear socio correctamente
2. ✅ Carga de categorías en dropdown funciona igual
3. ✅ Captura de foto (cámara/archivo) no se ve afectada
4. ✅ Navegación entre vistas funciona normal
5. ✅ Otros modales (editar socio, etc.) siguen funcionando (si no tienen ErrorBanner aún)

---

## 🐛 Problemas Conocidos (Resueltos)

### ❌ ~~Snackbars no aparecían~~
- **Problema**: `page.show_snack_bar()` no existe
- **Solución**: Usar `page.overlay.append(snackbar)` + `snackbar.open = True`

### ❌ ~~ValidationError mostraba mensaje genérico~~
- **Problema**: `__init__()` no aceptaba keyword args
- **Solución**: Añadir `__init__(self, message, status_code, details)` a todas las excepciones

### ❌ ~~`ft.animation.Animation` no existe~~
- **Problema**: API de Flet cambió en versiones recientes
- **Solución**: Usar `animate_opacity=200` en lugar de `ft.animation.Animation()`

---

## 🔄 Próximos Pasos

### Integración en otras vistas:

1. **socios_view.py**:
   - ✅ `show_nuevo_socio_dialog()` (COMPLETADO)
   - ⏳ `show_editar_socio_dialog()` (PENDIENTE)

2. **cuotas_view.py**:
   - ⏳ Modales de registro de pago

3. **usuarios_view.py**:
   - ⏳ Modal de crear/editar usuario

4. **categorias_view.py**:
   - ⏳ Modal de crear/editar categoría

5. **Otros 7 views**:
   - ⏳ Migrar gradualmente según prioridad

### Script de migración automática:

Ejecutar cuando estemos listos:
```bash
cd frontend-desktop
python scripts/migrate_views_to_error_handler.py
```

---

## 📝 Notas Técnicas

### Formatos de error soportados:

El `ErrorBanner.show_validation_errors()` soporta 3 formatos de backend:

1. **Formato dict de campos**:
```json
{
  "email": ["Email inválido"],
  "telefono": ["Formato incorrecto"]
}
```

2. **Formato con key "errors"**:
```json
{
  "errors": [
    {"field": "email", "message": "Email inválido"}
  ]
}
```

3. **Formato con key "detail" array**:
```json
{
  "detail": [
    {"loc": ["body", "email"], "msg": "Email inválido"}
  ]
}
```

### Métodos disponibles:

```python
# ErrorBanner
error_banner.show_error(message)           # Error único
error_banner.show_errors([msg1, msg2])    # Lista de errores
error_banner.show_validation_errors(dict) # Errores de validación
error_banner.hide()                        # Ocultar

# SuccessBanner
success_banner.show(message)              # Mostrar éxito
success_banner.hide()                     # Ocultar
```

---

## ✅ Checklist Final

Antes de considerar completa esta feature:

- [x] ErrorBanner creado con 3 tipos
- [x] SuccessBanner creado
- [x] handle_api_error_with_banner() implementado
- [x] Integrado en show_nuevo_socio_dialog()
- [x] Tests automáticos pasando (7/7)
- [x] Animación corregida (animate_opacity)
- [ ] **Testing manual completado** ← PRÓXIMO PASO
- [ ] Integrar en show_editar_socio_dialog()
- [ ] Documentar en AI instructions (.github/copilot-instructions.md)
- [ ] Migrar resto de vistas

---

**Fecha**: 2025-01-XX  
**Autor**: GitHub Copilot + Usuario  
**Versión**: 1.0
