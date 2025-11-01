# VideoToFrame

Extractor de frames nativos desde videos con interfaz gráfica. Permite extraer frames en diferentes formatos (PNG, JPG, WebP, BMP, TIFF, GIF) y recortar fragmentos de video.

## 📋 Requisitos

### Dependencias del Sistema

1. **Python 3.8+**
   - Verifica tu versión: `python3 --version` o `python --version`
   - La aplicación usa únicamente librerías estándar de Python

2. **FFmpeg y FFprobe**
   - Herramientas necesarias para procesar videos
   - Deben estar instaladas y disponibles en el PATH del sistema

3. **Tkinter** (GUI)
   - Generalmente viene incluido con Python
   - En Linux puede requerir instalación adicional

## 🔧 Instalación

### 1. Instalar FFmpeg y FFprobe

#### Linux (Arch/Manjaro)
```bash
sudo pacman -S ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install ffmpeg
```

#### macOS (Homebrew)
```bash
brew install ffmpeg
```

#### Windows
- Descarga FFmpeg desde: https://ffmpeg.org/download.html
- Extrae el archivo y agrega la carpeta `bin` al PATH del sistema
- O instala usando [Chocolatey](https://chocolatey.org/): `choco install ffmpeg`

### 2. Verificar instalación de FFmpeg

Abre una terminal y ejecuta:
```bash
ffmpeg -version
ffprobe -version
```

Si ambos comandos muestran información de versión, están correctamente instalados.

### 3. Instalar Tkinter (solo si es necesario)

#### Linux (Ubuntu/Debian)
```bash
sudo apt install python3-tk
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install python3-tkinter
```

#### Linux (Arch/Manjaro)
```bash
sudo pacman -S tk
```

#### macOS
- Tkinter generalmente viene incluido con Python en macOS

#### Windows
- Tkinter viene incluido con Python en Windows

### 4. Verificar Tkinter

Prueba si Tkinter está disponible:
```bash
python3 -c "import tkinter; print('Tkinter OK')"
```

## 🚀 Ejecución

```bash
python3 VideoToFrame.py
```

O si tienes Python como `python`:
```bash
python VideoToFrame.py
```

## 📖 Tutorial de Uso

### Paso 1: Cargar un Video

1. Haz clic en el botón **"Elegir…"** junto al campo "Video de entrada"
2. Selecciona el archivo de video que deseas procesar
3. La aplicación detectará automáticamente la duración del video

### Paso 2: Seleccionar Rango de Tiempo

Tienes dos formas de seleccionar el rango de frames a extraer:

**Opción A: Usar los sliders (deslizadores)**
- Arrastra el slider **"Inicio"** para establecer el punto inicial
- Arrastra el slider **"Final"** para establecer el punto final
- Los campos de texto se actualizarán automáticamente

**Opción B: Editar campos de tiempo manualmente**
- Formato: `HH:MM:SS.mmm` (por ejemplo: `00:01:30.500`)
- O simplemente segundos como `90.5`
- Edita los campos **"Inicio"**, **"Final"** o **"Duración"**
- Presiona Tab o haz clic fuera para sincronizar

### Paso 3: Configurar Parámetros de Extracción

1. **Carpeta de frames**: Ruta donde se guardarán los frames (por defecto: `frames_out`)
2. **Prefijo**: Nombre base de los archivos (por defecto: `frame`)
   - Los archivos se numerarán automáticamente: `frame_000001.png`, `frame_000002.png`, etc.
3. **Formato**: Selecciona el formato de imagen deseado
   - **PNG**: Sin pérdida, recomendado para calidad máxima
   - **JPG/JPEG**: Comprimido, menor tamaño
   - **WebP**: Excelente compresión
   - **BMP**: Sin compresión, archivos grandes
   - **TIFF**: Sin pérdida, usado en producción
   - **GIF**: Formato animado básico
4. **Calidad** (solo para JPG, JPEG y WebP):
   - Rango: 2-31 (donde 2 = mejor calidad, 31 = menor calidad)
   - Solo aparece habilitado para formatos que lo soportan

### Paso 4: Opciones Adicionales

- **Generar archivo recortado (MP4)**: Si está marcado, creará un video MP4 del fragmento seleccionado
  - Puedes cambiar el nombre del archivo con el botón **"Guardar como…"**
- **Usar PTS en nombre de archivos**: Usa timestamps reales del video en lugar de números secuenciales

### Paso 5: Extraer Frames

1. Haz clic en el botón **"Extraer frames"**
2. El botón cambiará a **"Extrayendo..."** y se deshabilitará durante el proceso
3. Puedes monitorear el progreso en el área de **Log**
4. Al finalizar, aparecerá un mensaje con la ubicación de los frames extraídos

### Paso 6: Cargar Otro Video (Opcional)

1. Espera a que termine la extracción actual (el botón volverá a su estado normal)
2. Haz clic en **"Elegir…"** nuevamente para cargar otro video
3. La aplicación limpiará automáticamente el estado anterior

## 💡 Consejos

- **Extracción completa**: Para extraer todos los frames del video, establece el inicio en `00:00:00.000` y el final al tiempo total del video
- **Mejor calidad**: Usa formato PNG o TIFF si necesitas máxima calidad
- **Menor tamaño**: Usa formato JPG o WebP con calidad ajustada
- **Frames específicos**: Usa el campo de duración para extraer exactamente el número de segundos que necesitas
- **Varios videos**: Puedes procesar múltiples videos sin necesidad de reiniciar la aplicación

## ⚠️ Notas Importantes

- La extracción de frames puede tardar varios minutos dependiendo de la longitud del video y la resolución
- Durante la extracción, la aplicación permanece funcional y puede mostrar el progreso en el log
- No cierres la aplicación mientras hay una extracción en progreso
- Los frames se guardan en la carpeta especificada con nombres secuenciales o PTS según tu elección

## 🐛 Solución de Problemas

**Error: "Se requieren ffmpeg y ffprobe en el PATH"**
- Verifica que FFmpeg esté instalado: `ffmpeg -version`
- Asegúrate de que el directorio de FFmpeg esté en el PATH del sistema
- Reinicia la terminal después de instalar FFmpeg

**La aplicación no inicia**
- Verifica que Tkinter esté instalado: `python3 -c "import tkinter"`
- Asegúrate de tener Python 3.8 o superior

**La extracción falla**
- Verifica que el archivo de video sea válido
- Asegúrate de tener permisos de escritura en la carpeta de salida
- Revisa el log para mensajes de error específicos

---

**Desarrollado por Alanito** 

