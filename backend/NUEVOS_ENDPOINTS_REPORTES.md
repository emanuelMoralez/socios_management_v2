# Nuevos Endpoints de Reportes - Backend

## Endpoints Agregados

### 1. `/api/reportes/ingresos-historicos`

**Método:** GET  
**Autenticación:** Requerida  
**Descripción:** Obtiene histórico de ingresos y egresos mensuales para gráficos

**Query Parameters:**
- `meses` (opcional, default: 6): Cantidad de meses hacia atrás

**Respuesta:**
```json
{
  "historico": [
    {
      "mes": "Jun",
      "anio": 2024,
      "mes_numero": 6,
      "ingresos": 15000.00,
      "egresos": 8000.00,
      "balance": 7000.00,
      "fecha_inicio": "2024-06-01",
      "fecha_fin": "2024-06-30"
    },
    {
      "mes": "Jul",
      "anio": 2024,
      "mes_numero": 7,
      "ingresos": 18000.00,
      "egresos": 9500.00,
      "balance": 8500.00,
      "fecha_inicio": "2024-07-01",
      "fecha_fin": "2024-07-31"
    }
    // ... más meses
  ],
  "total_meses": 6,
  "fecha_consulta": "2024-11-04"
}
```

**Uso:** Ideal para gráficos de barras o líneas mostrando evolución financiera

---

### 2. `/api/reportes/accesos-detallados`

**Método:** GET  
**Autenticación:** Requerida  
**Descripción:** Obtiene accesos agrupados por hora del día para análisis detallado

**Query Parameters:**
- `fecha` (opcional, default: hoy): Fecha en formato YYYY-MM-DD

**Respuesta:**
```json
{
  "fecha": "2024-11-04",
  "accesos_por_hora": [
    {
      "hora": "00:00",
      "total": 0,
      "permitidos": 0,
      "rechazados": 0,
      "advertencias": 0
    },
    {
      "hora": "08:00",
      "total": 15,
      "permitidos": 13,
      "rechazados": 2,
      "advertencias": 0
    },
    {
      "hora": "18:00",
      "total": 45,
      "permitidos": 40,
      "rechazados": 3,
      "advertencias": 2
    }
    // ... 24 horas
  ],
  "estadisticas": {
    "total": 120,
    "permitidos": 110,
    "rechazados": 8,
    "hora_pico": "18:00",
    "accesos_hora_pico": 45
  }
}
```

**Uso:** Ideal para gráficos de barras mostrando horarios de mayor afluencia

---

## Cambios Realizados

### Archivo Modificado: `backend/app/routers/reportes.py`

1. **Import agregado:**
   ```python
   from dateutil.relativedelta import relativedelta
   ```

2. **Ubicación de endpoints:**
   - Insertados después de `/dashboard`
   - Antes de los endpoints de exportación
   - Nueva sección: `# ==================== HISTÓRICOS PARA GRÁFICOS ====================`

3. **Dependencias:**
   - ✅ `python-dateutil==2.9.0.post0` ya estaba en requirements.txt
   - ✅ No requiere instalación adicional

---

## Testing

### Verificar endpoints con curl:

```bash
# 1. Login para obtener token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!"

# 2. Ingresos históricos (últimos 6 meses)
curl -X GET "http://localhost:8000/api/reportes/ingresos-historicos?meses=6" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Ingresos históricos (últimos 12 meses)
curl -X GET "http://localhost:8000/api/reportes/ingresos-historicos?meses=12" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Accesos detallados de hoy
curl -X GET "http://localhost:8000/api/reportes/accesos-detallados" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. Accesos de fecha específica
curl -X GET "http://localhost:8000/api/reportes/accesos-detallados?fecha=2024-11-03" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Verificar en Swagger UI:

1. Abrir: http://localhost:8000/docs
2. Hacer clic en "Authorize" (candado verde)
3. Login con: admin / Admin123!
4. Buscar los nuevos endpoints en la sección "reportes"
5. Probar con "Try it out"

---

## Estado del Backend

✅ **Backend recargado automáticamente**  
- El watch mode detectó los cambios
- Servidor reiniciado exitosamente
- Endpoints disponibles en: http://localhost:8000

**Logs de recarga:**
```
WARNING:  WatchFiles detected changes in 'app\routers\reportes.py'. Reloading...
INFO:     Application startup complete.
```

---

## Integración con Frontend

Para usar estos endpoints desde el frontend desktop, agregar en `api_client.py`:

```python
async def get_ingresos_historicos(self, meses: int = 6):
    """Obtener histórico de ingresos"""
    return await self.get(f"reportes/ingresos-historicos?meses={meses}")

async def get_accesos_detallados(self, fecha: str = None):
    """Obtener accesos detallados por hora"""
    params = f"?fecha={fecha}" if fecha else ""
    return await self.get(f"reportes/accesos-detallados{params}")
```

Luego usar en `dashboard_view.py` para crear gráficos reales en lugar de los placeholders actuales.

---

## Próximos Pasos Sugeridos

1. ✅ Endpoints agregados y funcionando
2. ⏳ Actualizar `api_client.py` con nuevos métodos
3. ⏳ Implementar gráficos reales en `dashboard_view.py`
4. ⏳ Usar bibliotecas de gráficos (matplotlib, plotly o flet charts)
5. ⏳ Agregar cache para mejorar performance en consultas históricas

---

**Documentación completa en:** http://localhost:8000/docs
