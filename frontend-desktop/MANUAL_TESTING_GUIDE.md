# 🧪 GUÍA DE TESTING MANUAL - API CLIENT V2.0

**Para:** Testing del auto-refresh y nuevas features  
**Duración estimada:** 15-20 minutos  
**Requisitos:** Backend + Frontend corriendo

---

## ⚡ TEST RÁPIDO AUTOMATIZADO (RECOMENDADO)

**Antes de testing manual, ejecuta este script para validar la integración:**

```bash
cd frontend-desktop
python test_error_handling.py
```

Este script verifica:
- ✅ 6 métodos nuevos existen
- ✅ 3 métodos obsoletos eliminados
- ✅ Auto-refresh funciona correctamente
- ✅ Login y renovación de token

**Si todos los tests pasan (✅), continúa con testing manual.**

**Si algún test falla (❌), revisar implementación antes de continuar.**

---

## 📋 PREPARACIÓN

### 1. Levantar Backend
```bash
# Terminal 1
cd d:/Desarrollo/socios_management_v2/backend

# Activar venv
source venv/Scripts/activate  # Git Bash
# o
venv\Scripts\activate  # CMD/PowerShell

# Iniciar servidor
uvicorn app.main:app --reload
```

**Verificar que esté corriendo:**
- Abrir: http://localhost:8000/health
- Debería mostrar: `{"status":"healthy",...}`

### 2. Levantar Frontend Desktop
```bash
# Terminal 2
cd d:/Desarrollo/socios_management_v2/frontend-desktop

# Activar venv
source venv/Scripts/activate  # Git Bash

# Iniciar app
python -m src.main
```

---

## 🧪 TEST 1: AUTO-REFRESH DE TOKENS (CRÍTICO)

### Objetivo
Verificar que el token se renueva automáticamente sin interrumpir al usuario.

### Método 1: Test Rápido (Recomendado)

#### Paso 1: Modificar timeout para test rápido
```bash
# Editar: backend/app/config.py
# Cambiar línea 26:
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1  # Era 30, ahora 1 minuto
```

#### Paso 2: Reiniciar backend
```bash
# En Terminal 1, presiona Ctrl+C
# Luego vuelve a ejecutar:
uvicorn app.main:app --reload
```

#### Paso 3: Hacer login en el frontend
```
Usuario: admin
Password: Admin123
```

#### Paso 4: Esperar 90 segundos
```bash
# Puedes usar un cronómetro o:
sleep 90  # En otra terminal
```

#### Paso 5: Intentar cargar lista de socios
```
1. Click en "Socios" en el menú lateral
2. Esperar que cargue la lista
```

#### ✅ Resultado Esperado:
- ✅ La lista se carga sin problemas
- ✅ NO aparece mensaje de "Sesión expirada"
- ✅ NO te redirige al login
- ✅ Todo funciona como si nada hubiera pasado

#### ❌ Si falla:
- ❌ Aparece error "Sesión expirada"
- ❌ Te redirige al login
- **Acción:** Revisar logs del backend para ver si el refresh falló

---

### Método 2: Test Realista (Opcional)

Si prefieres probar con el timeout real (30 min):

#### Paso 1: Dejar configuración normal
```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

#### Paso 2: Hacer login

#### Paso 3: Esperar 31 minutos
```
🕐 Puedes hacer otras cosas mientras esperas
   (Pero deja la app abierta)
```

#### Paso 4: Volver y cargar algo
```
Click en cualquier sección que haga petición al backend
```

#### ✅ Resultado Esperado:
- ✅ Carga sin pedir login nuevamente

---

## 🧪 TEST 2: MANEJO DE EXCEPCIONES

### 2.1: ValidationError (✅ IMPLEMENTADO EN socios_view.py)

#### Objetivo
Verificar que errores de validación se muestran apropiadamente.

#### Pasos:
```
1. Ir a "Socios" > "Nuevo Socio"
2. Llenar formulario con datos válidos EXCEPTO email:
   Nombre: "Test"
   Apellido: "Usuario"
   Documento: "12345678"
   Categoría: (cualquiera)
   Email: "test@"  (sin dominio - INVÁLIDO)
3. Click "Guardar"
```

#### ✅ Resultado Esperado:
- ✅ Snackbar **naranja** aparece en la parte inferior
- ✅ Mensaje: "⚠️ Datos inválidos al crear socio"
- ✅ Submensaje: "• email: value is not a valid email address" (o similar)
- ✅ **Formulario NO se cierra** (CRÍTICO)
- ✅ Usuario puede corregir email a "test@example.com" y guardar exitosamente
- ✅ Snackbar verde: "✅ Socio creado exitosamente"

#### ❌ Si falla:
- Si solo aparece error en consola: Error handler no está integrado
- Si formulario se cierra: Revisar que no haya `dialogo.open = False` en el except
- Si mensaje es genérico: Verificar que esté usando `handle_api_error()`

#### 🔧 Debug:
```bash
# Verificar que socios_view.py importa error_handler:
cd frontend-desktop
grep -n "from src.utils.error_handler" src/views/socios_view.py

# Debe mostrar:
# 6:from src.utils.error_handler import handle_api_error, show_success
```

---

### 2.2: NotFoundError

#### Objetivo
Verificar manejo de recursos no encontrados.

#### Pasos:
```
1. En navegador, ir a: http://localhost:8000/api/miembros/99999
   (ID que no existe)
2. Observar respuesta
```

#### ✅ Resultado Esperado:
- ✅ Error 404
- ✅ Mensaje claro de "no encontrado"

---

### 2.3: AuthenticationError

#### Objetivo
Verificar que sesión expirada redirige al login.

#### Pasos:
```
1. Hacer login
2. Cerrar backend (Ctrl+C en Terminal 1)
3. En frontend, intentar cargar socios
```

#### ✅ Resultado Esperado:
- ✅ Snackbar rojo: "Error de comunicación con la API"
- ✅ O mensaje apropiado de error de conexión

---

## 🧪 TEST 3: MÉTODOS NUEVOS

### 3.1: get_dashboard()

#### Objetivo
Verificar que el dashboard carga KPIs correctamente.

#### Pasos:
```
1. Ir a Dashboard (página principal después de login)
2. Observar si carga:
   - Total socios (activos/inactivos)
   - Ingresos del mes
   - Morosidad total
   - Accesos del día
```

#### ✅ Resultado Esperado:
- ✅ Todos los KPIs se muestran
- ✅ Carga en <3 segundos
- ✅ Sin errores en consola

#### ⚠️ Nota:
Si el dashboard NO usa `get_dashboard()` todavía, esto es normal.
Es un método nuevo que falta integrar en la UI.

---

### 3.2: preview_morosos()

#### Objetivo
Verificar vista previa antes de enviar emails.

#### Pasos:
```
1. Ir a "Notificaciones" o "Reportes"
2. Buscar opción de "Recordatorios" o "Enviar Emails"
3. Buscar botón "Vista Previa" o similar
4. Click
```

#### ✅ Resultado Esperado:
- ✅ Muestra lista de socios morosos
- ✅ Indica cuántos tienen email
- ✅ Muestra deuda de cada uno
- ✅ Opción de confirmar/cancelar

#### ⚠️ Nota:
Si no existe la UI para esto todavía, es esperado.
Es un método nuevo que falta integrar.

---

### 3.3: cambiar_estado_miembro()

#### Objetivo
Verificar cambio de estado con motivo.

#### Pasos:
```
1. Ir a lista de socios
2. Seleccionar un socio
3. Buscar opción "Cambiar Estado" o "Suspender"
4. Cambiar estado (ej: Activo → Suspendido)
5. Ingresar motivo (si hay campo)
6. Guardar
```

#### ✅ Resultado Esperado:
- ✅ Estado cambia correctamente
- ✅ Se registra motivo (si la UI lo soporta)
- ✅ Sin errores

---

### 3.4: registrar_acceso_manual()

#### Objetivo
Verificar registro manual de acceso (sin QR).

#### Pasos:
```
1. Ir a "Accesos" o "Control de Acceso"
2. Buscar opción "Registro Manual" o similar
3. Seleccionar un socio
4. Registrar acceso manualmente
```

#### ✅ Resultado Esperado:
- ✅ Acceso se registra correctamente
- ✅ Aparece en historial
- ✅ Sin errores

#### ⚠️ Nota:
Si la UI no tiene esta opción todavía, es esperado.
Es útil como fallback cuando el scanner QR no funciona.

---

## 🧪 TEST 4: EXPORTACIONES

### Objetivo
Verificar que exportaciones Excel funcionan con timeouts apropiados.

#### Pasos:
```
1. Ir a "Reportes"
2. Seleccionar "Exportar Socios a Excel" (o similar)
3. Click "Exportar"
4. Esperar descarga
```

#### ✅ Resultado Esperado:
- ✅ Archivo se descarga correctamente
- ✅ No timeout (tiene 60s de límite)
- ✅ Archivo contiene datos correctos

#### Test de Timeout:
```
Si tienes MUCHOS socios (>10,000), prueba:
1. Exportar todos
2. Verificar que no da timeout
3. Si da timeout, es porque necesitas más de 60s
   → Considerar aumentar timeout o paginar exportación
```

---

## 🧪 TEST 5: OPERACIONES CRUD

### Objetivo
Verificar que CRUD básico funciona sin errores.

#### Pasos:
```
1. Crear socio nuevo
2. Editar socio existente
3. Ver detalles de socio
4. Eliminar socio (soft delete)
5. Crear pago
6. Ver historial de accesos
```

#### ✅ Resultado Esperado:
- ✅ Todas las operaciones funcionan
- ✅ Sin errores de conexión
- ✅ Auto-refresh funciona si el token expiró

---

## 📊 CHECKLIST DE VALIDACIÓN

Usa esta lista para marcar lo que has probado:

### Auto-Refresh
- [ ] Test rápido (1 min timeout) completado
- [ ] Token se renovó automáticamente
- [ ] Sin interrupciones al usuario
- [ ] O test realista (30 min) completado

### Excepciones
- [ ] ValidationError muestra mensaje apropiado
- [ ] AuthenticationError redirige a login
- [ ] APITimeoutError muestra mensaje de timeout
- [ ] NotFoundError maneja recursos inexistentes

### Métodos Nuevos
- [ ] get_dashboard() carga KPIs (si está integrado)
- [ ] preview_morosos() funciona (si está integrado)
- [ ] cambiar_estado_miembro() funciona
- [ ] registrar_acceso_manual() funciona (si está integrado)

### Operaciones Generales
- [ ] Login funciona
- [ ] CRUD de socios funciona
- [ ] Pagos se registran correctamente
- [ ] Exportaciones Excel funcionan
- [ ] Accesos se registran
- [ ] Sin métodos obsoletos en uso

---

## 🐛 SI ENCUENTRAS PROBLEMAS

### Problema: Token no se renueva automáticamente

**Síntomas:**
- Error "Sesión expirada" después de timeout
- Usuario debe hacer login de nuevo

**Debug:**
```bash
# 1. Verificar que refresh_access_token() existe:
cd frontend-desktop
grep -n "def refresh_access_token" src/services/api_client.py

# 2. Verificar que _request() tiene retry_auth:
grep -n "retry_auth" src/services/api_client.py

# 3. Ver logs del backend:
# Debe aparecer algo sobre renovación de token
```

**Solución:**
El código ya está implementado. Si falla, revisar que el backend
tenga el endpoint `/api/auth/refresh` funcional.

---

### Problema: Excepciones no se capturan correctamente

**Síntomas:**
- Errores genéricos en lugar de mensajes específicos
- Crash de la aplicación

**Solución:**
Las vistas deben usar try/except específicos:
```python
try:
    data = await api_client.get_miembros()
except ValidationError as e:
    # Mostrar error de validación
except AuthenticationError:
    # Redirigir a login
except APIException as e:
    # Error genérico
```

---

### Problema: Métodos nuevos no funcionan

**Síntomas:**
- Error "método no encontrado"
- AttributeError

**Debug:**
```bash
# Verificar que el método existe:
cd frontend-desktop
python -c "from src.services.api_client import api_client; print(hasattr(api_client, 'get_dashboard'))"
# Debe imprimir: True
```

**Solución:**
Ya están implementados. Si no existen, verifica que estés usando
el archivo actualizado de api_client.py

---

## ✅ DESPUÉS DEL TESTING

### Si todo funciona:
1. ✅ Revertir timeout a 30 minutos en `backend/app/config.py`
2. ✅ Reiniciar backend
3. ✅ Marcar como "LISTO PARA PRODUCCIÓN"

### Si algo falla:
1. Documentar el problema
2. Revisar logs (backend y frontend)
3. Verificar configuración
4. Solicitar ayuda si es necesario

---

## 📞 SOPORTE

**Documentación de referencia:**
- `TESTING_REPORT_API_CLIENT.md` - Reporte de tests automatizados
- `CHANGELOG_API_CLIENT.md` - Changelog completo
- `api_client_usage_examples.py` - Ejemplos de código
- `RESUMEN_MEJORAS_API_CLIENT.md` - Resumen ejecutivo

**Tests automatizados:**
```bash
cd frontend-desktop
pytest tests/ -v
```

---

**Creado:** 3 de noviembre de 2025  
**Versión:** API Client v2.0  
**Duración estimada:** 15-20 minutos  
**Status:** Lista para usar 🚀
