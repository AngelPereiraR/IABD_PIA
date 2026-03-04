# Detección de Columnas con DocLayout-YOLO

Este proyecto implementa detección de columnas de texto en documentos antiguos (letras de Carnaval) usando dos métodos:

- **OpenCV**: Detección manual mediante proyecciones y morfología
- **DocLayout-YOLO**: Modelo pre-entrenado de detección de layout de documentos

## 🎯 Características

- ✅ Dos métodos de detección intercambiables (OpenCV y DocLayout-YOLO)
- ✅ Integración con PaddleOCR para extracción de texto por columnas
- ✅ Modelo pre-entrenado en 300k documentos (DocStructBench dataset)
- ✅ Distingue entre texto y decoraciones/imágenes
- ✅ Soporte para GPU (CUDA 11.8)
- ✅ Scripts de validación y benchmark incluidos
- ✅ Visualización con imágenes de depuración

## 📋 Requisitos

- **Python**: 3.10 o 3.11
- **GPU**: NVIDIA con CUDA 11.8
- **Hardware recomendado**: RTX 4060 Ti o superior, 16GB VRAM
- **Sistema operativo**: Windows/Linux

## 🚀 Instalación

### 1. Instalar PyTorch con CUDA

⚠️ **IMPORTANTE**: Instalar PyTorch PRIMERO para evitar conflictos de numpy

```bash
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
```

### 2. Instalar resto de dependencias

```bash
pip install -r requirements.txt
```

### 3. Descargar modelo DocLayout-YOLO

```bash
python download_doclayout_model.py
```

Esto descargará el modelo pre-entrenado (~40MB) desde Hugging Face:

- **Repo**: `juliozhao/DocLayout-YOLO-DocStructBench`
- **Ubicación**: `models/doclayout_yolo/doclayout_yolo_docstructbench_imgsz1024.pt`
- **Dataset**: 300k documentos anotados

### 5. Instalar Tesseract OCR (externo)

- **Windows**: https://github.com/UB-Mannheim/tesseract/wiki
- **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-spa`
- **macOS**: `brew install tesseract tesseract-lang`

## 🧪 Verificación post-instalación

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "import tensorflow as tf; print(f'TensorFlow: {tf.__version__}, GPU: {len(tf.config.list_physical_devices(\"GPU\"))}')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "from doclayout_yolo import YOLOv10; print('DocLayout-YOLO: OK')"
```

## 📖 Uso

### Detección de columnas standalone

#### OpenCV (método manual)

```bash
python detect_columns.py --image imgs/popurri01.jpg --method opencv --debug
```

#### DocLayout-YOLO (modelo pre-entrenado)

```bash
python detect_columns.py --image imgs/popurri01.jpg --method doclayout --debug
```

#### Ajustar umbral de confianza

```bash
python detect_columns.py --image imgs/popurri01.jpg --method doclayout --doclayout-conf 0.3 --debug
```

#### Detectar todas las clases (no solo texto)

```bash
python detect_columns.py --image imgs/popurri01.jpg --method doclayout --all-classes --debug
```

### Pipeline OCR completo (PaddleOCR)

#### Procesar una imagen con OpenCV

```bash
python paddle-pruebas.py imgs/popurri01.jpg --method opencv --debug
```

#### Procesar una imagen con DocLayout-YOLO

```bash
python paddle-pruebas.py imgs/popurri01.jpg --method doclayout --debug
```

#### Procesar carpeta completa

```bash
python paddle-pruebas.py imgs/ --method doclayout --doclayout-conf 0.3
```

### Scripts de validación

#### Validar las 18 imágenes de popurrís

```bash
# Con DocLayout-YOLO
python validate_18_popurris.py

# Con OpenCV
python validate_18_popurris.py --method opencv

# Con umbral personalizado
python validate_18_popurris.py --method doclayout --conf 0.3
```

**Salida**: `validacion_popurris.json` con estadísticas completas

#### Benchmark comparativo

```bash
# Comparar OpenCV vs DocLayout-YOLO en 5 imágenes
python benchmark_methods.py

# Comparar en 10 imágenes
python benchmark_methods.py --num-images 10

# Comparar con umbral personalizado
python benchmark_methods.py --conf 0.3
```

**Salida**: `benchmark_results.json` con métricas comparativas

## 🔍 Clases detectadas por DocLayout-YOLO

El modelo distingue 9 tipos de elementos:

| ID  | Clase     | Descripción                    | Color (debug) | Se extrae? |
| --- | --------- | ------------------------------ | ------------- | ---------- |
| 0   | text      | Párrafos de texto (columnas)   | Verde         | ✅         |
| 1   | title     | Títulos y encabezados          | Magenta       | ✅         |
| 2   | figure    | Imágenes y figuras decorativas | Rojo          | ❌         |
| 3   | table     | Tablas                         | Cyan          | ❌         |
| 4   | caption   | Pies de figura/tabla           | Naranja       | ❌         |
| 5   | header    | Encabezados de página          | Púrpura       | ✅         |
| 6   | footer    | Pies de página                 | Gris          | ❌         |
| 7   | reference | Referencias bibliográficas     | Blanco        | ✅         |
| 8   | equation  | Ecuaciones matemáticas         | Amarillo      | ❌         |

Por defecto, solo se extraen las clases de texto (0, 1, 5, 7). Usa `--all-classes` para detectar todas.

## 📊 Estructura de salida

### detect_columns.py

```
column_1.png      # Recorte de la columna 1
column_2.png      # Recorte de la columna 2
column_3.png      # Recorte de la columna 3
debug_columns_opencv.png     # (si --debug y --method opencv)
debug_columns_doclayout.png  # (si --debug y --method doclayout)
```

### paddle-pruebas.py

```
resultados/
└── popurri01_20240115_143022/
    ├── summary.json                # Métricas del procesamiento
    ├── ocr_column_1.txt            # Texto extraído de columna 1
    ├── ocr_column_2.txt            # Texto extraído de columna 2
    ├── temp_col_1.jpg              # Recorte de columna 1
    ├── temp_col_2.jpg              # Recorte de columna 2
    ├── debug_columns_doclayout.png # (si --debug)
    └── debug_columns_raw.png       # (si --debug y OpenCV)
```

### validate_18_popurris.py

```json
{
  "method": "doclayout",
  "doclayout_conf_threshold": 0.25,
  "statistics": {
    "num_images_processed": 18,
    "total_columns_detected": 54,
    "avg_columns_per_image": 3.0,
    "avg_detection_time_seconds": 0.245
  },
  "results": [...]
}
```

### benchmark_methods.py

```json
{
  "methods_compared": ["opencv", "doclayout"],
  "aggregated_statistics": {
    "opencv": {
      "avg_time_seconds": 0.123,
      "avg_columns": 3.2
    },
    "doclayout": {
      "avg_time_seconds": 0.234,
      "avg_columns": 2.8
    }
  },
  "detailed_results": [...]
}
```

## 🐛 Solución de problemas

### Error: "DocLayout-YOLO no está disponible"

```bash
pip install doclayout-yolo
python download_doclayout_model.py
```

### Error: "Modelo no encontrado"

Ejecuta el script de descarga:

```bash
python download_doclayout_model.py
```

### Error: numpy version conflict

Verifica que instalaste PyTorch 2.0.1 ANTES que TensorFlow:

```bash
pip uninstall torch numpy tensorflow -y
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

### CUDA no disponible

Verifica tu instalación de CUDA:

```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### Ninguna columna detectada

- **OpenCV**: Intenta con el método `doclayout`
- **DocLayout-YOLO**: Reduce el umbral de confianza con `--doclayout-conf 0.15`

## 📚 Referencias

- **DocLayout-YOLO**: https://huggingface.co/juliozhao/DocLayout-YOLO-DocStructBench
- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **PyTorch**: https://pytorch.org/

## 📝 Notas técnicas

### Resolución del conflicto numpy

- **Problema**: TensorFlow 2.10 requiere numpy<2.0, pero versiones recientes de PyTorch usan numpy>=2.0
- **Solución**: Usar PyTorch 2.0.1 (compatible con numpy 1.24-1.26)
- **Verificado con**: DeepSeek-VL2 oficial (torch==2.0.1, transformers==4.38.2)

### Ventajas de DocLayout-YOLO vs OpenCV

| Aspecto           | OpenCV                  | DocLayout-YOLO         |
| ----------------- | ----------------------- | ---------------------- |
| Velocidad         | Más rápido (~0.12s)     | Más lento (~0.24s)     |
| Precisión         | Depende de heurísticas  | Pre-entrenado en 300k  |
| Robustez          | Sensible a decoraciones | Distingue texto/figura |
| Configuración     | Muchos parámetros       | Un solo umbral         |
| Generalización    | Baja                    | Alta                   |
| Clases detectadas | Solo columnas           | 9 tipos de elementos   |

### Recomendaciones

- **Documentos limpios y regulares**: Usa OpenCV (más rápido)
- **Documentos antiguos con decoraciones**: Usa DocLayout-YOLO (más robusto)
- **Aprendizaje/educación**: Prueba ambos métodos y compara con `benchmark_methods.py`

## 🎓 Propósito educativo

Este proyecto fue desarrollado con fines de aprendizaje para entender:

- ✅ Transfer learning con modelos YOLO pre-entrenados
- ✅ Detección de objetos aplicada a documentos
- ✅ Integración de Deep Learning en pipelines de OCR
- ✅ Comparación de métodos tradicionales (OpenCV) vs Deep Learning

## 📄 Licencia

Este proyecto es libre para uso educativo y personal.

## 🤝 Contribuciones

Sugerencias y mejoras son bienvenidas. Este es un proyecto educativo en desarrollo.
