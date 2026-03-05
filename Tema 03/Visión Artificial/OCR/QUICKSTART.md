# 🚀 Inicio Rapido: OCR Layout + Multi-OCR

## 📋 PASO 0: Prerequisitos del Sistema

Antes de instalar paquetes Python, verifica que tienes instalado:

### ✅ Verificación automática

```powershell
python check_prerequisites.py
```

Este script verificará automáticamente todos los prerequisitos y te dará instrucciones personalizadas.

### Programas necesarios:

#### 1. Python 3.10 o 3.11 (OBLIGATORIO)

**Verificar**:

```powershell
python --version
```

**Descargar**: https://www.python.org/downloads/  
⚠️ **Importante**: Marcar "Add Python to PATH" durante instalación

#### 2. Tesseract OCR 5.0+ (OBLIGATORIO)

**Windows**:

- Descargar: https://github.com/UB-Mannheim/tesseract/wiki
- Instalar `tesseract-ocr-w64-setup-5.3.x.exe`
- Marcar idioma **Español** durante instalación
- Añadir a PATH: `C:\Program Files\Tesseract-OCR`

**Linux**:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**macOS**:

```bash
brew install tesseract tesseract-lang
```

**Verificar**:

```powershell
tesseract --version
```

#### 3. Git 2.x (RECOMENDADO)

Para descargar modelos de Hugging Face automáticamente.

**Descargar**: https://git-scm.com/

**Verificar**:

```powershell
git --version
```

#### 4. GPU NVIDIA con CUDA 11.8 (OPCIONAL)

Solo si tienes tarjeta NVIDIA y quieres aceleración GPU.

**Verificar**:

```powershell
nvidia-smi
```

Si este comando falla, **NO tienes GPU NVIDIA** → Usa instalación CPU (sección siguiente)

---

## 🚀 Pasos de instalación

### 🎯 Opción Recomendada: Instalación Automática con `install.bat` (Windows)

El script `install.bat` detecta automáticamente tu hardware y realiza toda la instalación:

```powershell
install.bat
```

**El script automáticamente:**

- ✅ Verifica prerequisitos del sistema (Python, Tesseract, Git, GPU)
- ✅ Detecta si tienes GPU NVIDIA o solo CPU
- ✅ Instala la versión correcta de PyTorch (CUDA o CPU)
- ✅ Instala todas las dependencias necesarias
- ✅ Descarga el modelo DocLayout-YOLO
- ✅ Verifica que todo esté instalado correctamente

**Interactivo**: El script preguntará antes de cada paso y puedes hacer selecciones personalizadas.

⚠️ **Si install.bat detecta que falta Tesseract**, debes instalarlo primero (ver PASO 0).

---

### 📝 Instalación Manual (alternativa a install.bat)

Si prefieres instalar manualmente o usas Linux/macOS:

#### ⚡ Opción A: Con GPU NVIDIA (CUDA 11.8)

#### 1️⃣ Instalar PyTorch con CUDA (⚠️ PRIMERO)

```powershell
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
```

#### 2️⃣ Instalar resto de dependencias

```powershell
pip install -r requirements.txt
```

#### 3️⃣ Descargar modelo DocLayout-YOLO

```powershell
python download_doclayout_model.py
```

---

### Verificar prerequisitos del sistema

```powershell
python check_prerequisites.py
```

### Verificar paquetes Python instalados

```powershell
# Python
python --version

# PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA disponible: {torch.cuda.is_available()}')"

# NumPy
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"

# OpenCV
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')"

# PaddleOCR
python -c "from paddleocr import PaddleOCR; print('PaddleOCR: OK')"

# DocLayout-YOLO
python -c "from doclayout_yolo import YOLOv10; print('DocLayout-YOLO: OK')"

# Tesseract (desde Python)
python -c "import pytesseract; print(f'Tesseract: OK')"
```

**Si pytesseract no encuentra Tesseract en Windows**, configura la ruta:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

#### ⚡ Opción B: Sin GPU NVIDIA (Solo CPU)

#### 1️⃣ Instalar PyTorch CPU (⚠️ PRIMERO)

```powershell
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu
```

#### 2️⃣ Instalar resto de dependencias

Edita `requirements.txt` primero para usar versión CPU:

1. Comenta las líneas con `+cu118` (ya instalaste versión CPU de PyTorch):

   ```diff
   - torch==2.0.1+cu118
   - torchvision==0.15.2+cu118
   - torchaudio==2.0.2+cu118
   + # torch==2.0.1+cu118  (ya instalado versión CPU)
   + # torchvision==0.15.2+cu118
   + # torchaudio==2.0.2+cu118
   ```

2. Comenta TensorFlow-GPU:

   ```diff
   - tensorflow-gpu==2.10.0
   + # tensorflow-gpu==2.10.0
   ```

3. Luego ejecuta:
   ```powershell
   pip install -r requirements.txt
   ```

#### 3️⃣ Descargar modelo DocLayout-YOLO

```powershell
python download_doclayout_model.py
```

⏱️ **Nota**: El procesamiento con YOLO será más lento en CPU (~2-5s/imagen vs ~0.24s con GPU).  
💡 **Recomendación**: Usa `--method opencv` para mejor rendimiento en CPU (~0.12s/imagen).

---

## ✅ Verificar instalación

```powershell
python -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}')"
python -c "from doclayout_yolo import YOLOv10; print('DocLayout-YOLO: OK')"
```

## 🎮 Uso básico

### Métodos de layout disponibles

- `opencv`
- `doclayout`
- `yolo11`
- `paddleocr`
- `docling`

### Detectar columnas en una imagen

```powershell
# Método DocLayout-YOLO (recomendado para documentos antiguos)
python detect_columns.py --image imgs/popurri01.jpg --method doclayout --debug

# Método OpenCV (más rápido, para documentos limpios)
python detect_columns.py --image imgs/popurri01.jpg --method opencv --debug
```

### Pipeline OCR completo con PaddleOCR

```powershell
# Procesar una imagen
python paddle-pruebas.py imgs/popurri01.jpg --method doclayout --debug

# Procesar todas las imágenes (batch)
python paddle-pruebas.py imgs/ --method doclayout
```

### Validar las 18 imágenes de popurrís

```powershell
python validate_18_popurris.py --method doclayout
```

### Validación OCR multi-motor (FASE 4)

```powershell
# Default (4 OCR): easyocr,tesseract,paddle,deepseek
python validate_ocr.py --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe" --deepseek-model-path ".\models\DeepSeek-OCR-2"

# Solo OCR sin args extra
python validate_ocr.py --ocr-engines easyocr,paddle
```

### Comparar OpenCV vs DocLayout-YOLO

```powershell
python benchmark_methods.py --num-images 5
```

## 📊 Resultados esperados

### detect_columns.py

- Genera: `column_1.png`, `column_2.png`, `column_3.png`
- Debug: `debug_columns_doclayout.png` (con cajas de colores según tipo)

### paddle-pruebas.py

- Carpeta: `resultados/popurri01_YYYYMMDD_HHMMSS/`
- Archivos: `summary.json`, `ocr_column_1.txt`, `ocr_column_2.txt`, etc.

### validate_18_popurris.py

- Archivo: `validacion_popurris.json`
- Contiene: Estadísticas de todas las 18 imágenes

### benchmark_methods.py

- Archivo: `benchmark_results.json`
- Contiene: Comparación de velocidad y precisión entre métodos

## 🎯 Resumen de argumentos

### detect_columns.py

```
--image PATH          Ruta a la imagen
--method {opencv,doclayout,yolo11,paddleocr,docling}  Metodo de deteccion (default: opencv)
--debug               Guardar imagen de depuración
--doclayout-conf 0.25 Umbral de confianza para YOLO (0-1)
--all-classes         Detectar todas las 9 clases (no solo texto)
```

### paddle-pruebas.py

```
IMAGE_PATH            Ruta a imagen o carpeta
--method {opencv,doclayout,yolo11,paddleocr,docling}  Metodo de deteccion (default: opencv)
--debug               Generar imágenes de depuración
--doclayout-conf 0.25 Umbral de confianza para YOLO
--outdir resultados   Carpeta de salida
--runs 1              Número de ejecuciones por imagen
```

### validate_18_popurris.py

```
--imgs-dir imgs       Directorio con las imágenes
--method doclayout    Método de detección
--conf 0.25           Umbral de confianza
--output FILE         Archivo JSON de salida
```

### benchmark_methods.py

```
--num-images 5        Número de imágenes a procesar
--methods opencv doclayout  Métodos a comparar
--conf 0.25           Umbral de confianza
--output FILE         Archivo JSON de salida
```

## 🐛 Problemas comunes

### ImportError: doclayout_yolo

```powershell
pip install doclayout-yolo
python download_doclayout_model.py
```

### CUDA no disponible

```powershell
# Verificar instalación de CUDA
nvidia-smi

# Reinstalar PyTorch con CUDA
pip uninstall torch -y
pip install torch==2.0.1+cu118 --index-url https://download.pytorch.org/whl/cu118
```

### No detecta columnas

```powershell
# Reducir umbral de confianza
python detect_columns.py --image imgs/popurri01.jpg --method doclayout --doclayout-conf 0.15 --debug

# Probar método alternativo
python detect_columns.py --image imgs/popurri01.jpg --method opencv --debug
```

## 📖 Documentacion completa

- `README.md`
- `GUIA_VALIDATE_OCR.md`

## ⚡ Rendimiento: CPU vs GPU

| Aspecto                 | CPU (sin NVIDIA)         | GPU (CUDA 11.8)       |
| ----------------------- | ------------------------ | --------------------- |
| Instalacion             | Mas simple               | Requiere CUDA + cuDNN |
| Velocidad (OpenCV)      | ~0.12s por imagen        | ~0.12s por imagen     |
| Velocidad (YOLO/layout) | ~2-5s por imagen         | ~0.24s por imagen     |
| Memoria                 | 4-8GB RAM                | 2-4GB RAM + 4GB VRAM  |
| Uso recomendado         | Pruebas y pocas imagenes | Batch processing      |

Recomendacion CPU: usar `--method opencv` cuando priorices velocidad.

## Configuracion adicional en Windows

Si Tesseract no se detecta:

1. Verifica instalacion:

```powershell
tesseract --version
```

2. Si falla, anade `C:\Program Files\Tesseract-OCR` al `PATH` de usuario y reinicia la terminal.
3. Alternativa por script:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Resumen de archivos de instalacion

| Archivo                       | Proposito                          | Uso                    |
| ----------------------------- | ---------------------------------- | ---------------------- |
| `install.bat`                 | Instalador automatico en Windows   | Recomendado            |
| `check_prerequisites.py`      | Verifica prerequisitos del sistema | Ejecutar primero       |
| `requirements.txt`            | Dependencias Python                | Instalacion manual     |
| `download_doclayout_model.py` | Descarga modelo DocLayout-YOLO     | Tras instalar paquetes |

## Ejemplo completo (paso a paso)

```powershell
# 1. Deteccion de columnas
python detect_columns.py --image imgs/popurri01.jpg --method doclayout --debug

# 2. OCR completo de una imagen
python paddle-pruebas.py imgs/popurri01.jpg --method doclayout --debug

# 3. Comparativa rapida de metodos
python benchmark_methods.py --num-images 3
```

## Consejos

- Primera ejecucion: usar `--debug` para validar cajas detectadas.
- Documento antiguo con decoraciones: `--method doclayout`.
- Documento limpio: `--method opencv`.
- Si detecta pocas regiones: baja `--doclayout-conf` (0.15-0.20).
- Si detecta demasiadas regiones: sube `--doclayout-conf` (0.35-0.40).

## Notas

- Algunos errores de import en el editor son normales antes de instalar paquetes.
- El primer uso de modelos DL puede tardar por descarga/carga de pesos.
- El modelo de DocLayout-YOLO se descarga una sola vez.
