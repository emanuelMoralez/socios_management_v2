# Changelog - APIClient Improvements

## 📅 Fecha: 3 de noviembre de 2025

## 🎯 Resumen
Refactorización completa del `api_client.py` para mejorar manejo de errores, auto-renovación de tokens, y eliminar código duplicado.

---

## ✅ MEJORAS IMPLEMENTADAS

### 1. 🔐 Auto-Refresh de Tokens (CRÍTICO)

**Problema anterior:**
```python
# Cuando el access_token expiraba (30 min), lanzaba excepción inmediata
if response.status_code == 401:
    raise Exception("Sesión expirada")
    # Usuario debía hacer login completo de nuevo
```

**Solución implementada:**
```python
# Ahora intenta renovar automáticamente con refresh_token
if response.status_code == 401 and self.refresh_token:
    await self.refresh_access_token()  # Renueva token
    return await self._request(...)     # Reintenta petición
# Solo lanza error si refresh_token también expiró
```

**Beneficio:** 
- UX mejorada: el usuario NO tiene que volver a iniciar sesión cada 30 minutos
- El token se renueva transparentemente en background
- Solo pide login si ambos tokens expiraron (después de 7 días sin actividad)

**Método nuevo:**
- `async def refresh_access_token()` - Renueva access_token usando refresh_token

---

### 2. 🚨 Excepciones Personalizadas

**Problema anterior:**
```python
raise Exception("Error genérico")  # Difícil de manejar en UI
```

**Solución implementada:**
```python
# Excepciones específicas por tipo de error
class AuthenticationError(APIException):  # 401 - Token inválido
class ValidationError(APIException):      # 422 - Datos inválidos
class NotFoundError(APIException):        # 404 - No encontrado
class APITimeoutError(APIException):      # Timeout
class APIException(Exception):            # Base para otros
```

**Beneficio:**
```python
# Ahora puedes manejar errores específicamente en la UI:
try:
    await api_client.get_miembros()
except AuthenticationError:
    # Mostrar login
except ValidationError as e:
    # Resaltar campos inválidos
except APITimeoutError:
    # Mostrar "reintenta más tarde"
```

---

### 3. 🔧 Métodos Duplicados Eliminados

**Antes (DUPLICADOS):**
```python
async def get_accesos(...)              # Versión 1 - pocos filtros
async def obtener_historial_accesos(...)  # Versión 2 - más filtros (DUPLICADO)
async def obtener_resumen_accesos(...)    # Versión 3 (DUPLICADO)
async def get_estadisticas_accesos(...)   # Sin timeout
async def obtener_estadisticas_accesos(...) # Con timeout (DUPLICADO)
async def exportar_accesos_excel(...)     # En sección reportes (DUPLICADO)
```

**Después (UNIFICADO):**
```python
async def get_accesos(...)              # Versión única con TODOS los filtros
async def get_resumen_accesos(...)      # Con timeout
async def get_estadisticas_accesos(...) # Con timeout
async def exportar_accesos_excel(...)   # En sección exportación
```

**Eliminados:** 3 métodos duplicados  
**Beneficio:** Código más limpio, sin confusión sobre cuál usar

---

### 4. ➕ Métodos Nuevos Agregados

#### 4.1 Dashboard
```python
async def get_dashboard() -> Dict[str, Any]:
    """
    Obtener KPIs del dashboard principal
    Returns: total_socios, ingresos_mes, morosidad, accesos_hoy, gráficos
    """
```
**Uso:** Cargar panel principal con estadísticas clave

#### 4.2 Cambiar Estado de Miembro
```python
async def cambiar_estado_miembro(miembro_id, nuevo_estado, motivo):
    """
    Cambiar estado: activo, inactivo, suspendido, baja
    Con registro de motivo para auditoría
    """
```
**Uso:** Suspender o dar de baja socios con trazabilidad

#### 4.3 Estado Financiero Detallado
```python
async def get_miembro_estado_financiero(miembro_id):
    """
    Returns: saldo, última_cuota, días_mora, histórico
    """
```
**Uso:** Vista detallada del estado de cuenta

#### 4.4 Registro de Acceso Manual
```python
async def registrar_acceso_manual(miembro_id, ubicacion, observaciones):
    """
    Registrar acceso sin QR (backup cuando scanner no funciona)
    """
```
**Uso:** Fallback cuando cámara/scanner falla

#### 4.5 Preview de Emails Masivos
```python
async def preview_morosos(solo_morosos, dias_mora_minimo):
    """
    Vista previa de quiénes recibirán recordatorios
    ANTES de enviar emails masivos
    """
```
**Uso:** Validar lista de destinatarios antes de enviar

#### 4.6 Exportar Accesos a Excel
```python
async def exportar_accesos_excel(fecha_inicio, fecha_fin):
    """
    Exportar reporte de accesos (estaba duplicado, ahora unificado)
    """
```

---

### 5. 📝 Documentación Mejorada

**Antes:**
```python
async def get_miembros(...):
    """Obtener lista de miembros"""
```

**Después:**
```python
async def get_miembros(
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = None,
    estado: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtener lista de miembros con filtros
    
    Args:
        page: Número de página (default 1)
        page_size: Items por página (default 20, max 100)
        q: Búsqueda por nombre, documento o email
        estado: Filtrar por estado (activo, inactivo, etc.)
    
    Returns:
        Dict con:
        - data: Lista de miembros
        - pagination: Metadata (total, page, has_next, etc.)
    
    Raises:
        AuthenticationError: Token expirado
        ValidationError: Parámetros inválidos
        APIException: Otros errores
    """
```

**Beneficio:** Autocompletado en IDE + documentación inline

---

### 6. ⏱️ Timeouts Apropiados

| Operación | Timeout | Justificación |
|-----------|---------|---------------|
| CRUD normal | 30s | Operaciones rápidas |
| Exportar Excel | 60s | Puede procesar miles de registros |
| Envío emails masivos | 120s | Puede enviar a cientos de socios |

**Implementado en:**
- `get_dashboard()` → 30s
- `get_resumen_accesos()` → 30s
- `exportar_*_excel()` → 60s
- `enviar_recordatorios_masivos()` → 120s
- `test_email_config()` → 30s

---

## 📊 ESTADÍSTICAS

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| **Métodos públicos** | 48 | 45 | -3 (eliminados duplicados) |
| **Excepciones** | 1 genérica | 5 específicas | +4 |
| **Líneas de código** | ~556 | ~680 | +124 (docs + features) |
| **Métodos duplicados** | 3 | 0 | -3 ✅ |
| **Métodos nuevos** | - | 6 | +6 |
| **Auto-refresh** | ❌ No | ✅ Sí | ✅ |

---

## 🎯 IMPACTO EN UX

### Antes
```
Usuario trabaja 30 minutos → Token expira → ❌ "Sesión expirada"
→ Debe hacer login completo → ❌ Pierde trabajo sin guardar
```

### Después
```
Usuario trabaja 30 minutos → Token expira → 🔄 Auto-renueva en background
→ ✅ Sigue trabajando sin interrupciones → Solo pide login después de 7 días
```

---

## 🔍 BREAKING CHANGES

### ⚠️ Cambios que pueden afectar código existente:

1. **Excepciones diferentes:**
   ```python
   # ANTES
   except Exception as e:
       # Capturaba todo
   
   # DESPUÉS (recomendado)
   except AuthenticationError:
       # Manejo específico de autenticación
   except ValidationError:
       # Manejo específico de validación
   except APIException as e:
       # Otros errores de API
   ```

2. **Métodos eliminados (usar reemplazos):**
   - ❌ `obtener_historial_accesos()` → ✅ `get_accesos()`
   - ❌ `obtener_resumen_accesos()` → ✅ `get_resumen_accesos()`
   - ❌ `obtener_estadisticas_accesos()` → ✅ `get_estadisticas_accesos()`

3. **Parámetro nuevo en `_request()`:**
   ```python
   # Si llamas directamente a _request() (no recomendado):
   await self._request(method, endpoint, retry_auth=False)
   # Por defecto retry_auth=True
   ```

---

## 📚 ARCHIVOS NUEVOS CREADOS

1. **`api_client_usage_examples.py`**
   - 7 ejemplos completos de uso
   - Manejo de errores por caso de uso
   - Patrones recomendados

2. **`CHANGELOG_API_CLIENT.md`** (este archivo)
   - Documentación de cambios
   - Guía de migración

---

## 🚀 SIGUIENTES PASOS RECOMENDADOS

### Inmediato (esta semana)
1. ✅ Actualizar vistas que usen `obtener_*` → `get_*`
2. ✅ Agregar manejo de `AuthenticationError` en vistas críticas
3. ✅ Probar auto-refresh en sesión real (esperar 30 min)

### Mediano plazo (próximas 2 semanas)
4. Agregar `preview_morosos()` en vista de notificaciones
5. Usar `get_dashboard()` en vista principal
6. Implementar `registrar_acceso_manual()` como fallback en QR scanner

### Largo plazo
7. Crear tests unitarios para excepciones
8. Agregar retry automático para `APITimeoutError` (exponential backoff)
9. Persistir tokens en disco para sobrevivir reinicios de app

---

## 🐛 TESTING

### Escenarios a probar:

1. **Auto-refresh:**
   ```bash
   # Hacer login → Esperar 31 minutos → Hacer una petición
   # Debe: Renovar token automáticamente sin pedir login
   ```

2. **Refresh token expirado:**
   ```bash
   # Hacer login → Esperar 8 días → Hacer una petición
   # Debe: Lanzar AuthenticationError y pedir login
   ```

3. **Validación:**
   ```bash
   # Crear miembro con email inválido
   # Debe: Lanzar ValidationError con detalles
   ```

4. **Timeout:**
   ```bash
   # Exportar Excel con 10,000 registros
   # Debe: Completar en <60s o lanzar APITimeoutError
   ```

5. **Not Found:**
   ```bash
   # GET /miembros/999999 (ID inexistente)
   # Debe: Lanzar NotFoundError
   ```

---

## 📞 CONTACTO

Si encuentras problemas o tienes sugerencias:
- Abrir issue en GitHub
- Revisar `api_client_usage_examples.py` para ejemplos

---

**Autor:** Sistema de mejora continua  
**Fecha:** 3 de noviembre de 2025  
**Versión API:** 2.0.0  
**Branch:** master
