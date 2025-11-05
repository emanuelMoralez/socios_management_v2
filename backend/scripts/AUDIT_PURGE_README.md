# Configuración de Limpieza Automática de Auditoría

## 📋 Resumen

El script `purge_audit.py` permite purgar registros antiguos de auditoría y archivarlos en CSV antes de eliminarlos de la base de datos.

## ⚙️ Configuración

### Variables de entorno (.env)

```bash
# Días de retención de auditoría (default: 90)
AUDIT_RETENTION_DAYS=90

# Directorio para archivos CSV (default: archives/audit)
AUDIT_ARCHIVE_DIR=archives/audit
```

## 🚀 Uso Manual

### Básico (usar config de .env)
```bash
cd backend
python -m scripts.purge_audit
```

### Con parámetros
```bash
# Retención de 30 días
python -m scripts.purge_audit --days 30

# Modo dry-run (simular sin eliminar)
python -m scripts.purge_audit --dry-run

# Solo eliminar sin archivar (no recomendado)
python -m scripts.purge_audit --no-archive --days 30
```

## ⏰ Automatización con Cron (Linux/macOS)

### 1. Editar crontab
```bash
crontab -e
```

### 2. Añadir tarea programada

#### Ejecutar cada domingo a las 2:00 AM
```cron
0 2 * * 0 cd /ruta/al/backend && /ruta/al/venv/bin/python -m scripts.purge_audit >> /var/log/audit_purge.log 2>&1
```

#### Ejecutar el primer día del mes a las 3:00 AM
```cron
0 3 1 * * cd /ruta/al/backend && /ruta/al/venv/bin/python -m scripts.purge_audit >> /var/log/audit_purge.log 2>&1
```

#### Ejemplo con retención de 60 días
```cron
0 2 * * 0 cd /home/usuario/socios_management_v2/backend && /home/usuario/socios_management_v2/backend/venv/bin/python -m scripts.purge_audit --days 60 >> /var/log/audit_purge.log 2>&1
```

### 3. Verificar crontab
```bash
crontab -l
```

### 4. Ver logs de ejecución
```bash
tail -f /var/log/audit_purge.log
```

## 🪟 Automatización con Task Scheduler (Windows)

### 1. Abrir Task Scheduler (Programador de tareas)
- Presionar `Win + R`
- Escribir `taskschd.msc` y Enter

### 2. Crear Tarea Básica
- Clic derecho en "Biblioteca del Programador de tareas" → "Crear tarea básica"
- **Nombre**: "Purga Auditoría"
- **Descripción**: "Limpia registros antiguos de auditoría"

### 3. Configurar Desencadenador
- **Frecuencia**: Semanal (o Mensual)
- **Día**: Domingo (o primer día del mes)
- **Hora**: 02:00 AM

### 4. Configurar Acción
- **Acción**: Iniciar un programa
- **Programa**: `D:\Desarrollo\socios_management_v2\backend\venv\Scripts\python.exe`
- **Argumentos**: `-m scripts.purge_audit --days 90`
- **Iniciar en**: `D:\Desarrollo\socios_management_v2\backend`

### 5. Opciones Avanzadas
- ✅ Ejecutar con privilegios más altos (si es necesario)
- ✅ Ejecutar aunque el usuario no haya iniciado sesión
- ✅ Registrar historial de tareas

### 6. Verificar ejecución
- Ver "Historial" en Task Scheduler
- Logs en `backend/logs/app.log` o archivo especificado

## 🐳 Automatización con Docker/Kubernetes

### Docker Compose con servicio cron

```yaml
# docker-compose.yml
services:
  audit-purge:
    image: python:3.11-slim
    volumes:
      - ./backend:/app
    working_dir: /app
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - AUDIT_RETENTION_DAYS=90
    command: >
      sh -c "
        pip install -q -r requirements.txt &&
        while true; do
          python -m scripts.purge_audit &&
          sleep 604800
        done
      "
    restart: unless-stopped
```

### Kubernetes CronJob

```yaml
# k8s/audit-purge-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: audit-purge
spec:
  schedule: "0 2 * * 0"  # Cada domingo 2:00 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: purge
            image: tu-registry/backend:latest
            command: ["python", "-m", "scripts.purge_audit"]
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: url
            - name: AUDIT_RETENTION_DAYS
              value: "90"
          restartPolicy: OnFailure
```

## 📊 Monitoreo y Alertas

### 1. Verificar ejecución exitosa
```bash
# Verificar última ejecución del script
grep "RESUMEN DE PURGA" /var/log/audit_purge.log | tail -n 20
```

### 2. Alertas por email (añadir al script)
```python
# En purge_audit.py, añadir al final de main():
if stats['errors']:
    # Enviar email de error
    send_alert_email(stats)
```

### 3. Alertas con Healthchecks.io
```bash
# Añadir al cron job
curl -fsS -m 10 --retry 5 -o /dev/null https://hc-ping.com/your-uuid && \
cd /ruta/al/backend && python -m scripts.purge_audit
```

## 🔍 Ejemplo de Output

```
2025-11-05 02:00:01 - __main__ - INFO - 🚀 Iniciando script de purga de auditoría
2025-11-05 02:00:01 - __main__ - INFO - ⚙️  Config: retention_days=90, dry_run=False, skip_archive=False
2025-11-05 02:00:01 - __main__ - INFO - 📅 Fecha límite: 2025-08-07 02:00:01
2025-11-05 02:00:02 - __main__ - INFO - 🔍 Encontrados 1543 registros más antiguos que 90 días
2025-11-05 02:00:02 - __main__ - INFO - 📦 Procesando lote 1 (1000 registros)
2025-11-05 02:00:03 - __main__ - INFO - ✅ Archivado 1000 registros en archives/audit/audit_archive_20251105_020003_batch1.csv
2025-11-05 02:00:04 - __main__ - INFO - 🗑️  Eliminados 1000 registros
2025-11-05 02:00:04 - __main__ - INFO - 📦 Procesando lote 2 (543 registros)
2025-11-05 02:00:05 - __main__ - INFO - ✅ Archivado 543 registros en archives/audit/audit_archive_20251105_020005_batch2.csv
2025-11-05 02:00:06 - __main__ - INFO - 🗑️  Eliminados 543 registros
2025-11-05 02:00:06 - __main__ - INFO - 
╔════════════════════════════════════════════════╗
║          RESUMEN DE PURGA DE AUDITORÍA         ║
╠════════════════════════════════════════════════╣
║ Registros antiguos:         1543               ║
║ Archivados:                 1543               ║
║ Eliminados:                 1543               ║
║ Errores:                       0               ║
╚════════════════════════════════════════════════╝
```

## 📁 Gestión de Archivos CSV

### Estructura de archivos
```
archives/audit/
├── audit_archive_20251105_020003_batch1.csv
├── audit_archive_20251105_020005_batch2.csv
└── audit_archive_20251201_020001_batch1.csv
```

### Formato CSV
```csv
id,tipo,descripcion,severidad,usuario_id,usuario_username,entidad_tipo,entidad_id,ip_address,user_agent,datos_adicionales,fecha_hora
1,LOGIN_EXITOSO,Login exitoso,INFO,1,admin,Usuario,1,192.168.1.100,Mozilla/5.0...,{},2025-05-10T08:30:00
```

### Limpieza de archivos antiguos (opcional)
```bash
# Eliminar CSV con más de 1 año
find archives/audit/ -name "*.csv" -mtime +365 -delete
```

## ⚠️ Consideraciones

### 1. Performance
- El script procesa en **lotes de 1000** para no saturar memoria
- En bases de datos grandes, puede tomar varios minutos
- Ejecutar en horarios de baja actividad (madrugada)

### 2. Espacio en disco
- Cada archivo CSV ocupa ~500 KB por cada 1000 registros
- 10,000 registros ≈ 5 MB
- Monitorear espacio en disco en `/archives`

### 3. Backups
- Los archivos CSV son un respaldo, pero **no reemplazan backups de BD**
- Mantener backups regulares de PostgreSQL

### 4. Compliance
- Consultar regulaciones locales sobre retención de logs (GDPR, etc.)
- Ajustar `AUDIT_RETENTION_DAYS` según requisitos legales

## 🧪 Testing

### Dry-run antes de producción
```bash
# Ver qué se eliminaría sin hacer cambios
python -m scripts.purge_audit --dry-run
```

### Probar con retención corta
```bash
# Eliminar registros con más de 7 días (para testing)
python -m scripts.purge_audit --days 7 --dry-run
```

---

**Última actualización**: 2025-11-05
