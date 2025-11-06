# Setup de Cámara QR - Windows

## Dependencias requeridas

La funcionalidad de escáner QR requiere:
- `opencv-python`: captura de video de la cámara
- `pyzbar`: lectura de códigos QR

## Instalación en Windows

### 1. Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### 2. Instalar librerías de sistema para pyzbar

**pyzbar** requiere la librería `zbar` nativa de Windows.

#### Opción A: Usando conda (recomendado)
```bash
conda install -c conda-forge pyzbar
```

#### Opción B: Manual
1. Descargar `zbar` para Windows desde: http://zbar.sourceforge.net/download.html
2. Extraer y copiar `libzbar-64.dll` (o `libzbar-32.dll` según tu sistema) a:
   - `C:\Windows\System32\` (requiere permisos admin)
   - O en la misma carpeta que tu script Python

#### Opción C: Usando el instalador precompilado
```bash
# Descargar wheel precompilado desde:
# https://github.com/NaturalHistoryMuseum/pyzbar/releases
pip install <archivo_wheel_descargado.whl>
```

## Verificar instalación

Ejecuta este script de prueba:
```python
import cv2
from pyzbar import pyzbar

# Verificar cámara
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✅ Cámara detectada")
    cap.release()
else:
    print("❌ No se pudo acceder a la cámara")

# Verificar pyzbar
print("✅ pyzbar instalado correctamente")
```

## Troubleshooting

### Error: "Unable to find zbar shared library"
- Instala zbar usando conda o descarga la DLL manualmente
- Asegúrate de tener la versión correcta (32 o 64 bits)

### Error: "Camera not found"
- Verifica que otra aplicación no esté usando la cámara
- Prueba cambiar el índice: `cv2.VideoCapture(1)` o `(2)`

### Permisos de cámara en Windows 10/11
1. Configuración → Privacidad → Cámara
2. Activar "Permitir que las aplicaciones accedan a la cámara"
3. Activar para aplicaciones de escritorio

## Uso en la aplicación

1. Ir a **Accesos** en el menú lateral
2. Click en **"Iniciar Escáner"**
3. Permitir acceso a la cámara si solicita
4. Mostrar código QR del socio frente a la cámara
5. El sistema validará automáticamente y mostrará el resultado

## Notas
- La cámara se libera automáticamente al detener el escáner o cerrar la vista
- El sistema evita escaneos duplicados con un delay de 3 segundos entre lecturas
