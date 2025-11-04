# 🔔 Integración de NotificationManager - Documentación

**Fecha:** 4 de noviembre de 2025  
**Archivo:** `frontend-desktop/src/main.py`

---

## 🎯 Objetivo

Integrar el sistema de notificaciones en tiempo real en la aplicación principal para:
- Mostrar alertas de nuevos socios morosos
- Notificaciones de bienvenida
- Panel lateral con historial de notificaciones
- Badge con contador de notificaciones no leídas

---

## ✅ Cambios Implementados

### 1. **Import del NotificationManager**

```python
from src.utils.notification_manager import NotificationManager
```

---

### 2. **Inicialización en App.__init__**

```python
class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = None
        self.notification_manager = None  # ← Nueva propiedad
        
        # ... configuración de página ...
        
        # Inicializar gestor de notificaciones
        self.notification_manager = NotificationManager(page)  # ← Instancia
        
        self.show_login()
```

**Beneficios:**
- ✅ Instancia única compartida en toda la app
- ✅ Disponible desde el momento de inicio
- ✅ Accesible desde cualquier método de App

---

### 3. **AppBar con Badge de Notificaciones**

```python
def show_main_layout(self):
    """Mostrar layout principal con sidebar"""
    self.page.clean()
    
    # Configurar AppBar con notificaciones
    notification_badge = self.notification_manager.create_notification_badge()
    self.page.appbar = ft.AppBar(
        title=ft.Text("Sistema de Gestión de Socios"),
        center_title=False,
        bgcolor=ft.Colors.BLUE,
        actions=[notification_badge]  # ← Badge en el AppBar
    )
    
    # ... resto del código ...
```

**Resultado visual:**

```
┌────────────────────────────────────────────────────────┐
│ Sistema de Gestión de Socios                    🔔 (3) │  ← AppBar azul
├────────────────────────────────────────────────────────┤
│ [Sidebar]  │  [Contenido principal]                    │
│            │                                            │
│ Dashboard  │  KPIs, gráficos, etc.                     │
│ Socios     │                                            │
│ ...        │                                            │
└────────────────────────────────────────────────────────┘
```

**Características del badge:**
- 🔔 Icono de campana blanco
- 🔴 Badge rojo con número de notificaciones no leídas
- 👆 Click abre panel lateral de notificaciones
- 🔄 Se actualiza automáticamente

---

### 4. **Sistema de Notificaciones en Background**

```python
async def start_notifications(self):
    """Iniciar sistema de notificaciones"""
    try:
        # Función para chequear morosos
        async def check_morosos():
            try:
                data = await api_client.get_reporte_morosidad()
                morosos = data.get("morosos", [])
                return len(morosos)
            except Exception as e:
                print(f"Error al obtener reporte de morosidad: {e}")
                return 0
        
        # Agregar notificación de bienvenida
        self.notification_manager.add_notification(
            titulo="✅ Bienvenido",
            mensaje=f"Sesión iniciada como {self.current_user.get('username', 'usuario')}",
            tipo="success"
        )
        
        # Iniciar chequeo en background de morosos (cada 5 minutos)
        await self.notification_manager.start_background_check(check_morosos)
        
    except Exception as e:
        print(f"Error al iniciar notificaciones: {e}")
```

**Flujo de trabajo:**

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario inicia sesión                                │
│    └─> show_main_layout()                               │
│        └─> page.run_task(start_notifications)           │
│                                                          │
│ 2. Notificación de bienvenida                           │
│    ✅ "Bienvenido - Sesión iniciada como admin"         │
│                                                          │
│ 3. Loop en background (cada 5 minutos)                  │
│    ├─> check_morosos()                                  │
│    │   └─> api_client.get_reporte_morosidad()          │
│    │       └─> return len(morosos)                      │
│    │                                                     │
│    └─> Si hay nuevos morosos:                           │
│        └─> add_notification(                            │
│              titulo="⚠️ Nuevos Socios Morosos",         │
│              mensaje="Se detectaron X nuevo(s) socio(s)",│
│              tipo="warning",                             │
│              accion=lambda: page.go("/reportes")        │
│            )                                             │
│                                                          │
│ 4. Usuario hace click en badge 🔔                       │
│    └─> show_notifications_panel()                       │
│        ├─> Muestra lista de notificaciones              │
│        ├─> Permite marcar como leída                    │
│        └─> Botón de acción "Ver Reportes"              │
└─────────────────────────────────────────────────────────┘
```

---

### 5. **Limpieza en Logout**

```python
def on_logout(self):
    """Callback cuando usuario cierra sesión"""
    # Detener notificaciones
    if self.notification_manager:
        self.notification_manager.stop_background_check()  # ← Detiene loop
    
    api_client.logout()
    self.current_user = None
    
    # Limpiar AppBar
    self.page.appbar = None  # ← Remueve AppBar
    
    self.show_login()
```

**Beneficios:**
- ✅ Evita memory leaks deteniendo el loop
- ✅ Limpia la interfaz al volver a login
- ✅ Libera recursos correctamente

---

## 📊 Tipos de Notificaciones

### 1. **Success (Verde)**
```python
self.notification_manager.add_notification(
    titulo="✅ Operación exitosa",
    mensaje="El pago se registró correctamente",
    tipo="success"
)
```
- **Color:** Verde 🟢
- **Icono:** CHECK_CIRCLE ✅
- **Uso:** Confirmaciones, operaciones exitosas

### 2. **Info (Azul)**
```python
self.notification_manager.add_notification(
    titulo="ℹ️ Información",
    mensaje="Nueva funcionalidad disponible",
    tipo="info"
)
```
- **Color:** Azul 🔵
- **Icono:** INFO ℹ️
- **Uso:** Información general, tips

### 3. **Warning (Naranja)**
```python
self.notification_manager.add_notification(
    titulo="⚠️ Advertencia",
    mensaje="Nuevos socios morosos detectados",
    tipo="warning",
    accion=lambda: self.page.go("/reportes"),
    accion_texto="Ver Reportes"
)
```
- **Color:** Naranja 🟠
- **Icono:** WARNING ⚠️
- **Uso:** Alertas importantes, morosos
- **Extra:** Snackbar automático + acción

### 4. **Error (Rojo)**
```python
self.notification_manager.add_notification(
    titulo="❌ Error",
    mensaje="No se pudo conectar con el servidor",
    tipo="error"
)
```
- **Color:** Rojo 🔴
- **Icono:** ERROR ❌
- **Uso:** Errores críticos
- **Extra:** Snackbar automático

---

## 🎨 Panel de Notificaciones

### Ejemplo Visual

```
╔════════════════════════════════════════════════════════╗
║ 🔔 Notificaciones                              [X]     ║
╠════════════════════════════════════════════════════════╣
║ [Marcar todas como leídas]                             ║
╠════════════════════════════════════════════════════════╣
║ ┌────────────────────────────────────────────────┐    ║
║ │ ⚠️  Nuevos Socios Morosos            [✓] [Ver] │    ║
║ │     Se detectaron 3 nuevo(s) socio(s)          │    ║
║ │     Hace 2 minutos                              │    ║
║ └────────────────────────────────────────────────┘    ║
║                                                         ║
║ ┌────────────────────────────────────────────────┐    ║
║ │ ✅  Bienvenido                      [✓leída]    │    ║
║ │     Sesión iniciada como admin                  │    ║
║ │     Hace 15 minutos                             │    ║
║ └────────────────────────────────────────────────┘    ║
║                                                         ║
║ ┌────────────────────────────────────────────────┐    ║
║ │ ℹ️  Información                     [✓leída]    │    ║
║ │     Sistema actualizado a v2.1                  │    ║
║ │     Hace 1 hora                                 │    ║
║ └────────────────────────────────────────────────┘    ║
╚════════════════════════════════════════════════════════╝
```

### Características:
- ✅ Scroll para ver más notificaciones (máximo 20)
- ✅ Diferencia visual entre leídas/no leídas (fondo gris vs blanco)
- ✅ Botones de acción personalizables
- ✅ Formato de tiempo relativo ("Hace X minutos")
- ✅ Icono ✓ para marcar como leída
- ✅ Botón "Marcar todas como leídas"

---

## ⚙️ Configuración

### Intervalo de Chequeo

Por defecto, el sistema verifica morosos cada **5 minutos** (300 segundos):

```python
class NotificationManager:
    def __init__(self, page: ft.Page):
        # ...
        self.check_interval = 300  # 5 minutos
```

**Para cambiar:**

```python
# En main.py, después de crear NotificationManager
self.notification_manager.check_interval = 600  # 10 minutos
# o
self.notification_manager.check_interval = 60   # 1 minuto (testing)
```

---

## 🧪 Testing

### Test Automatizado

```bash
cd frontend-desktop
PYTHONPATH=. python test_notification_integration.py
```

**Verifica:**
- ✅ Import correcto
- ✅ Inicialización en App.__init__
- ✅ Badge agregado al AppBar
- ✅ Chequeo en background configurado
- ✅ Notificación de bienvenida
- ✅ Limpieza en logout

### Test Manual

1. **Iniciar aplicación:**
   ```bash
   cd frontend-desktop
   PYTHONPATH=. python src/main.py
   ```

2. **Iniciar sesión:**
   - Usuario: `admin`
   - Contraseña: `Admin123`

3. **Verificar notificación de bienvenida:**
   - Badge 🔔 debe aparecer en AppBar con contador (1)
   - Click en badge debe mostrar:
     ```
     ✅ Bienvenido
     Sesión iniciada como admin
     Hace unos segundos
     ```

4. **Simular morosos (opcional):**
   - Ir a "Socios"
   - Cambiar estado de un socio a "MOROSO"
   - Esperar 5 minutos
   - Debe aparecer notificación: "⚠️ Nuevos Socios Morosos"

5. **Verificar panel de notificaciones:**
   - Click en badge 🔔
   - Debe abrir panel lateral
   - Probar botón "Ver Reportes"
   - Probar marcar como leída (✓)
   - Probar "Marcar todas como leídas"

---

## 🚀 Casos de Uso

### 1. **Notificación Manual desde Vista**

Si quieres agregar notificaciones desde otras vistas (ej. DashboardView, SociosView):

```python
# En cualquier vista que tenga acceso a page
from src.main import App

# Dentro de un método de la vista
app_instance = self.page.data.get("app")  # Si guardaste referencia
if app_instance and app_instance.notification_manager:
    app_instance.notification_manager.add_notification(
        titulo="📊 Reporte Generado",
        mensaje="El reporte de pagos está listo",
        tipo="success"
    )
```

**Mejor práctica:** Pasar `notification_manager` como parámetro al crear las vistas.

### 2. **Notificar Después de Registrar Pago**

```python
async def registrar_pago(self, ...):
    try:
        # ... lógica de registro ...
        
        # Notificar éxito
        self.notification_manager.add_notification(
            titulo="💰 Pago Registrado",
            mensaje=f"Pago de ${monto} registrado para {socio_nombre}",
            tipo="success"
        )
    except Exception as e:
        # Notificar error
        self.notification_manager.add_notification(
            titulo="❌ Error al Registrar Pago",
            mensaje=str(e),
            tipo="error"
        )
```

### 3. **Alertas de Vencimientos Próximos**

Agregar en `start_notifications()`:

```python
async def check_vencimientos():
    try:
        # Obtener socios con cuotas próximas a vencer (dentro de 3 días)
        fecha_limite = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        # ... lógica para obtener socios ...
        return cantidad_socios_con_vencimiento
    except:
        return 0

# Iniciar chequeo adicional
self.page.run_task(
    lambda: self.notification_manager.start_background_check(check_vencimientos)
)
```

---

## 📝 API del NotificationManager

### Métodos Principales

#### `create_notification_badge() -> ft.Container`
Crea el badge para agregar al AppBar.

#### `add_notification(titulo, mensaje, tipo, accion, accion_texto)`
Agrega nueva notificación.
- **titulo:** Título de la notificación
- **mensaje:** Mensaje descriptivo
- **tipo:** `"success"`, `"info"`, `"warning"`, `"error"`
- **accion:** Callback a ejecutar (opcional)
- **accion_texto:** Texto del botón de acción (default: "Ver")

#### `show_notifications_panel()`
Muestra panel lateral con todas las notificaciones.

#### `update_badge_count(count)`
Actualiza contador del badge manualmente.

#### `start_background_check(check_callback)`
Inicia loop de chequeo en background.
- **check_callback:** Función async que retorna número de items a monitorear

#### `stop_background_check()`
Detiene el loop de chequeo.

#### `clear_notifications()`
Limpia todas las notificaciones.

---

## 🔧 Troubleshooting

### El badge no aparece
- ✅ Verificar que `show_main_layout()` crea el AppBar
- ✅ Verificar que `notification_badge` se agrega a `actions=[]`
- ✅ Revisar consola para errores

### Las notificaciones no se actualizan
- ✅ Verificar que `start_notifications()` se llama con `page.run_task()`
- ✅ Verificar que el backend está corriendo
- ✅ Revisar logs: `print()` statements en `check_morosos()`

### El badge no muestra contador
- ✅ Verificar que hay notificaciones no leídas
- ✅ Llamar a `update_badge_count()` después de agregar notificación
- ✅ Verificar que `self.notification_badge` no es None

### El panel lateral no se abre
- ✅ Verificar que `self.page.drawer` se asigna correctamente
- ✅ Revisar que `panel.open = True` se ejecuta
- ✅ Llamar a `self.page.update()` después de abrir

---

## 🎯 Próximas Mejoras

- [ ] Notificaciones push (usando websockets)
- [ ] Persistencia de notificaciones (SQLite local)
- [ ] Filtros por tipo de notificación
- [ ] Sonidos de alerta personalizables
- [ ] Modo "No molestar"
- [ ] Notificaciones de cumpleaños de socios
- [ ] Alertas de cuotas próximas a vencer (3 días antes)
- [ ] Notificaciones de pagos pendientes
- [ ] Integración con email para notificaciones importantes

---

## 📚 Referencias

- **NotificationManager:** `frontend-desktop/src/utils/notification_manager.py`
- **Integración:** `frontend-desktop/src/main.py`
- **Test:** `frontend-desktop/test_notification_integration.py`
- **Flet Docs:** https://flet.dev/docs/controls/badge
