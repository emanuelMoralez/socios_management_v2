# Plan de Correcciones Frontend Desktop

## 🔴 Problemas Críticos Detectados

### 1. **MainLayout - Sidebar no se muestra correctamente**
**Archivo:** `frontend-desktop/src/views/main_layout.py` (línea 195)

**Problema:**
```python
sidebar = ft.Container(
    content=ft.Column(...),
    width=200,
    bgcolor=ft.Colors.BLUE_800,
    # NO usar expand aquí - el width fijo se respeta sin expand
)
```

**Solución:**
```python
sidebar = ft.Container(
    content=ft.Column(
        [...],
        spacing=0,
        expand=True  # ← La columna DEBE expandirse verticalmente
    ),
    width=250,  # Ancho fijo del sidebar
    bgcolor=ft.Colors.BLUE_800,
    expand=False,  # El container NO debe expandirse horizontalmente
)
```

---

### 2. **DashboardView - Gráficos no cargan al inicio**
**Archivo:** `frontend-desktop/src/views/dashboard_view.py`

**Problema:** El método `did_mount()` no existe, los datos no se cargan automáticamente.

**Solución:** Agregar método `did_mount()`:
```python
def did_mount(self):
    """Llamado cuando el control se monta en la página"""
    if self.page:
        self.page.run_task(self._load_dashboard_data)
```

---

### 3. **ErrorBanner - Animación puede fallar**
**Archivo:** `frontend-desktop/src/components/error_banner.py` (línea 111)

**Problema:** El método `show_error()` usa `asyncio` pero no siempre está disponible.

**Solución:**
```python
def show_error(self, message: str, auto_hide: bool = False, duration: int = 5000):
    self.message_text.value = message
    self.visible = True
    
    if self.page:
        self.page.update()
    
    # Auto-hide solo si está habilitado Y hay página
    if auto_hide and self.page:
        def hide_delayed():
            import time
            time.sleep(duration / 1000)
            self.hide()
        
        import threading
        threading.Thread(target=hide_delayed, daemon=True).start()
```

---

### 4. **SociosView - Foto no se muestra en preview**
**Archivo:** `frontend-desktop/src/views/socios_view.py`

**Problema:** El contexto de cámara no se asigna correctamente después de crear el diálogo.

**Solución:** Mover la asignación después de `page.overlay.append()`:
```python
self.page.overlay.append(dialogo)
dialogo.open = True

# Asignar contexto DESPUÉS de agregar el diálogo
if 'camara_context' in photo:
    photo['camara_context']['dialogo_principal'] = dialogo

self.page.update()
```

---

### 5. **CuotasView - Modal de "Anular Pago" puede fallar**
**Archivo:** `frontend-desktop/src/views/cuotas_view.py`

**Problema:** El loop `while dialogo_confirm.open` puede ser infinito si hay error.

**Solución:** Agregar timeout:
```python
import asyncio
timeout = 30  # 30 segundos
elapsed = 0
while dialogo_confirm.open and elapsed < timeout:
    await asyncio.sleep(0.1)
    elapsed += 0.1

if not resultado["confirmed"]:
    return
```

---

### 6. **AccesosQRView - Stack no se actualiza correctamente**
**Archivo:** `frontend-desktop/src/views/accesos_qr_view.py` (líneas 80-150)

**Problema:** Los controles del Stack (guía QR, instrucciones) tienen `visible=False` pero no se actualizan.

**Solución:** Guardar referencias y actualizar explícitamente:
```python
# Crear referencias
self.qr_guide = ft.Container(
    content=ft.Container(
        width=250,
        height=250,
        border=ft.border.all(4, ft.Colors.GREEN_400),
        border_radius=20,
    ),
    alignment=ft.alignment.center,
    visible=False
)

self.qr_instruction = ft.Container(
    content=ft.Text(
        "Centra el código QR en el recuadro",
        size=14,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
    ),
    alignment=ft.alignment.top_center,
    padding=15,
    visible=False
)

# En start_scanner():
self.qr_guide.visible = True
self.qr_instruction.visible = True
self.qr_guide.update()
self.qr_instruction.update()
```

---

### 7. **ReportesView - Gráfico de accesos vacío**
**Archivo:** `frontend-desktop/src/views/reportes_view.py`

**Problema:** `_create_accesos_chart()` puede retornar sin actualizar el container.

**Solución:** Agregar fallback:
```python
def _create_accesos_chart(self, accesos_por_hora: list):
    if not accesos_por_hora:
        return ft.Container(
            content=ft.Text(
                "No hay datos de accesos para mostrar",
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            ),
            padding=20,
            alignment=ft.alignment.center
        )
    
    # ... resto del código ...
```

---

### 8. **CategoriasView - Campo "características" incorrecto**
**Archivo:** `frontend-desktop/src/views/categorias_view.py`

**Problema:** El backend espera `caracteristicas: str`, pero el form envía una lista.

**Solución en `show_nueva_categoria_dialog()`:**
```python
data = {
    "nombre": nombre_field.value.strip(),
    "descripcion": descripcion_field.value.strip() if descripcion_field.value else "",
    "cuota_base": float(cuota),
    "tiene_cuota_fija": tiene_cuota_fija.value,
    "caracteristicas": caracteristicas_field.value.strip() if caracteristicas_field.value else "",  # ← STRING
    "modulo_tipo": "generico"
}
```

---

## 🟡 Problemas Menores (UX)

### 9. **Paginación inconsistente**
Algunos views tienen paginación, otros no. Estandarizar:

```python
def _create_pagination_controls(self, pagination: dict):
    """Crear controles de paginación estandarizados"""
    page = pagination.get("page", 1)
    total = pagination.get("total_pages", 1)
    has_prev = pagination.get("has_prev", False)
    has_next = pagination.get("has_next", False)
    
    return ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.FIRST_PAGE,
                disabled=not has_prev,
                on_click=lambda _: self.go_to_page(1)
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                disabled=not has_prev,
                on_click=lambda _: self.go_to_page(page - 1)
            ),
            ft.Text(f"Página {page} de {total}"),
            ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                disabled=not has_next,
                on_click=lambda _: self.go_to_page(page + 1)
            ),
            ft.IconButton(
                icon=ft.Icons.LAST_PAGE,
                disabled=not has_next,
                on_click=lambda _: self.go_to_page(total)
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5
    )
```

---

### 10. **Loading indicators sin timeout**
Los `ProgressRing` pueden quedarse infinitos si hay error de red.

**Solución:** Agregar timeout en `api_client.py`:
```python
async def _request(self, method: str, endpoint: str, **kwargs):
    timeout = kwargs.pop('timeout', self.timeout)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # ... request ...
    except httpx.TimeoutException:
        raise APITimeoutError(f"Timeout después de {timeout}s")
```

---

## 🟢 Mejoras Recomendadas

### 11. **Modo oscuro**
Agregar soporte para tema oscuro en `main.py`:

```python
# En App.__init__()
self.page.theme_mode = ft.ThemeMode.LIGHT
self.page.theme = ft.Theme(
    color_scheme_seed=ft.Colors.BLUE,
)

# Dark theme
self.page.dark_theme = ft.Theme(
    color_scheme_seed=ft.Colors.BLUE,
)

# Botón para toggle
def toggle_theme(e):
    self.page.theme_mode = (
        ft.ThemeMode.DARK 
        if self.page.theme_mode == ft.ThemeMode.LIGHT 
        else ft.ThemeMode.LIGHT
    )
    self.page.update()
```

---

### 12. **Caché de categorías**
Las categorías se cargan en cada vista. Implementar caché:

```python
# En App o MainLayout
class CategoryCache:
    _categorias = None
    _last_update = None
    _ttl = 300  # 5 minutos
    
    @classmethod
    async def get_categorias(cls):
        now = datetime.now()
        if (cls._categorias is None or 
            cls._last_update is None or 
            (now - cls._last_update).seconds > cls._ttl):
            cls._categorias = await api_client.get_categorias()
            cls._last_update = now
        return cls._categorias
    
    @classmethod
    def invalidate(cls):
        cls._categorias = None
        cls._last_update = None
```

---

### 13. **Validación de campos mejorada**
Crear validadores reutilizables:

```python
# frontend-desktop/src/utils/validators.py
def validar_email(email: str) -> tuple[bool, str]:
    import re
    if not email:
        return False, "Email es obligatorio"
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        return False, "Email inválido"
    return True, ""

def validar_documento(doc: str, tipo: str = "dni") -> tuple[bool, str]:
    if not doc or not doc.strip():
        return False, "Documento es obligatorio"
    if tipo == "dni" and (len(doc) < 7 or len(doc) > 8):
        return False, "DNI debe tener 7-8 dígitos"
    if not doc.isdigit():
        return False, "Documento debe ser numérico"
    return True, ""

def validar_telefono(tel: str) -> tuple[bool, str]:
    if not tel:
        return True, ""  # Opcional
    if len(tel) < 8 or len(tel) > 15:
        return False, "Teléfono debe tener 8-15 dígitos"
    return True, ""
```

---

### 14. **Feedback visual mejorado**
Agregar animaciones sutiles:

```python
# En botones importantes
ft.ElevatedButton(
    "Guardar",
    icon=ft.Icons.SAVE,
    on_click=...,
    animate_scale=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
    style=ft.ButtonStyle(
        animation_duration=300
    )
)

# En containers de loading
ft.Container(
    content=ft.ProgressRing(),
    animate_opacity=200,
    opacity=1.0 if loading else 0.0
)
```

---

## 📋 Checklist de Implementación

### Prioridad Alta (Crítico)
- [ ] Corregir MainLayout sidebar expand
- [ ] Agregar did_mount() a DashboardView
- [ ] Corregir ErrorBanner auto-hide con threading
- [ ] Fix SociosView camera context timing
- [ ] Agregar timeout a loops de confirmación
- [ ] Corregir Stack update en AccesosQRView

### Prioridad Media (Importante)
- [ ] Estandarizar paginación en todos los views
- [ ] Agregar timeout global a loading indicators
- [ ] Implementar CategoryCache
- [ ] Mejorar validación de campos con validators.py

### Prioridad Baja (Nice to have)
- [ ] Agregar modo oscuro
- [ ] Agregar animaciones a botones críticos
- [ ] Crear componente reutilizable de paginación
- [ ] Agregar búsqueda debounced en tablas

---

## 🚀 Orden de Implementación Sugerido

1. **Día 1:** Corregir problemas críticos (1-6)
2. **Día 2:** Estandarizar paginación y loading
3. **Día 3:** Implementar validators y caché
4. **Día 4:** Mejoras visuales y modo oscuro
5. **Día 5:** Testing y ajustes finales

---

## 📝 Notas Adicionales

### Convenciones de código
- Usar `async def` para métodos que llaman al API
- Siempre usar `handle_api_error()` o `handle_api_error_with_banner()`
- Validar campos antes de enviar al backend
- Usar `ft.Colors` en lugar de strings para colores
- Mantener imports en orden: stdlib, third-party, local

### Testing checklist
- [ ] Probar cada vista en modo light y dark
- [ ] Verificar responsividad en ventana mínima (1024x768)
- [ ] Probar flujo completo: login → dashboard → cada vista
- [ ] Verificar que errores se muestren correctamente
- [ ] Probar offline mode (sin conexión al backend)

---

## 🔧 Herramientas Útiles

### Para debugging
```python
# Agregar logging temporal
import sys
print(f"DEBUG: {variable}", file=sys.stderr)

# Verificar que un control está montado
if self.page:
    print(f"Page exists: {self.page}")
else:
    print("Warning: page is None!")
```

### Para performance
```python
# Medir tiempo de carga
import time
start = time.time()
await self.load_socios()
print(f"Carga de socios: {time.time() - start:.2f}s")
```

