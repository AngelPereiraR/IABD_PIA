# Guia de uso de `validate_ocr.py`

Esta guia cubre:

- Preparacion del entorno
- Todas las opciones CLI disponibles
- Todas las configuraciones de deteccion por metodo
- Ejecucion por todos los motores OCR (EasyOCR, Tesseract, Paddle, DeepSeek)
- Formato de resultados y troubleshooting

## 1. Que hace el validador

`validate_ocr.py` ejecuta validacion en este orden:

1. Detecta VBoxes/columnas con una configuracion de layout (`method`, `conf`, `nms_iou`, `merge_distance`)
2. Aplica OCR por cada region detectada
3. Calcula metricas (chars, words, dups, tiempos, score)
4. Repite para cada imagen y para cada motor OCR solicitado

La unidad real de evaluacion es:

- `configuracion_de_layout x motor_ocr x imagen`

## 2. Requisitos y preparacion

### 2.1 Requisitos comunes

Desde la carpeta `Tema 03/Visión Artificial/OCR`:

```powershell
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install pandas numpy opencv-python
```

Asegura que existan:

- `detect_columns.py`
- Carpeta de imagenes (por defecto `imgs/`)

### 2.2 EasyOCR

```powershell
py -3.11 -m pip install easyocr
```

### 2.3 Tesseract

1. Instalar binario Tesseract (Windows):
   - Ruta tipica: `C:\Program Files\Tesseract-OCR\tesseract.exe`
2. Instalar wrapper Python:

```powershell
py -3.11 -m pip install pytesseract
```

Si no esta en PATH, pasar `--tesseract-cmd`.

### 2.4 PaddleOCR

```powershell
py -3.11 -m pip install paddlepaddle paddleocr
```

Opcional para evitar chequeos de red de Paddle:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
```

### 2.5 DeepSeek OCR local

Requisitos minimos:

- GPU CUDA disponible
- `torch`, `transformers`
- Modelo descargado localmente (ruta para `--deepseek-model-path`)

Instalacion base:

```powershell
py -3.11 -m pip install torch transformers
```

Ejemplo de uso en este proyecto: ver `pruebas-deepseek.py`.

## 3. Opciones CLI de `validate_ocr.py`

```text
--top N
--method {opencv,doclayout,yolo11,paddleocr,docling}
--configs JSON
--images-dir PATH
--ranking-csv PATH
--output-dir PATH
--no-ocr
--resume
--report-only
--langs es,en
--ocr-engines easyocr,tesseract,paddle,deepseek
--deepseek-model-path PATH
--deepseek-prompt "<image>\nFree OCR."
--tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## 4. Configuraciones de deteccion (layout) posibles

Segun `experiment_models.py`:

- `methods`: `doclayout`, `yolo11`, `paddleocr`, `docling`, `opencv`
- `conf_thresholds`: `0.1, 0.2, 0.3, 0.4`
- `nms_iou`: `0.3, 0.4, 0.5, 0.6`
- `merge_distance`: `5, 10, 15, 20`

### 4.1 Estructura por metodo

- `doclayout` y `yolo11`:
  - `{"method":"doclayout|yolo11","conf":X,"nms_iou":Y,"merge_distance":Z}`
- `paddleocr` y `docling`:
  - `{"method":"paddleocr|docling","nms_iou":Y,"merge_distance":Z}`
- `opencv`:
  - `{"method":"opencv","merge_distance":Z}`

### 4.2 Conteo total de configuraciones

- `doclayout`: `4 x 4 x 4 = 64`
- `yolo11`: `4 x 4 x 4 = 64`
- `paddleocr`: `4 x 4 = 16`
- `docling`: `4 x 4 = 16`
- `opencv`: `4 = 4`

Total: `164` configuraciones de layout.

## 5. Motores OCR posibles

`--ocr-engines` acepta combinaciones de:

- `easyocr`
- `tesseract`
- `paddle`
- `deepseek`

Ejemplos:

- Solo uno: `--ocr-engines easyocr`
- Dos: `--ocr-engines easyocr,tesseract`
- Todos: `--ocr-engines easyocr,tesseract,paddle,deepseek`

## 6. Ejemplos de uso

### 6.1 Top-3 del ranking con los 4 motores

```powershell
py -3.11 validate_ocr.py --top 3 --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path "E:\Modelos\DeepSeek-OCR" --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 6.2 Solo metodo `opencv` con los 4 motores

```powershell
py -3.11 validate_ocr.py --method opencv --top 4 --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path "E:\Modelos\DeepSeek-OCR"
```

### 6.3 Configs manuales para todos los metodos de layout

```powershell
py -3.11 validate_ocr.py --configs '[
  {"method":"doclayout","conf":0.2,"nms_iou":0.4,"merge_distance":10},
  {"method":"yolo11","conf":0.2,"nms_iou":0.4,"merge_distance":10},
  {"method":"paddleocr","nms_iou":0.4,"merge_distance":10},
  {"method":"docling","nms_iou":0.4,"merge_distance":10},
  {"method":"opencv","merge_distance":10}
]' --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path "E:\Modelos\DeepSeek-OCR"
```

### 6.4 Solo deteccion (sin OCR)

```powershell
py -3.11 validate_ocr.py --top 5 --no-ocr
```

### 6.5 Reanudar ejecucion

```powershell
py -3.11 validate_ocr.py --top 5 --resume --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path "E:\Modelos\DeepSeek-OCR"
```

### 6.6 Solo regenerar informes

```powershell
py -3.11 validate_ocr.py --report-only
```

## 7. Salidas generadas

### 7.1 Por configuracion y motor OCR

En `validation_results/<label_config>/`:

- `results_easyocr.json`
- `results_tesseract.json`
- `results_paddle.json`
- `results_deepseek.json`

(Se generan segun motores activos en `--ocr-engines`.)

### 7.2 Informes globales

- `ocr_validation_report.json`
- `ocr_validation_report.csv`
- `ocr_validation_report.txt`

Incluyen campo/columna `ocr_engine` para comparar motores.

## 8. Formula de score

`score = chars*1.0 + words*5.0 - duplicados*50.0 - imgs_sin_deteccion*20.0`

Donde:

- `chars`: total de caracteres OCR
- `words`: total de palabras OCR
- `duplicados`: cajas superpuestas detectadas
- `imgs_sin_deteccion`: imagenes sin regiones

## 9. Matriz de ejecucion esperada

Si ejecutas:

- `N` configuraciones de layout
- `M` motores OCR
- `K` imagenes

El total de evaluaciones es:

- `N x M x K`

Ejemplo tipico:

- `N=5` (un representante por metodo)
- `M=4` (easyocr,tesseract,paddle,deepseek)
- `K=18`

Total: `5 x 4 x 18 = 360` evaluaciones.

## 10. Troubleshooting rapido

### 10.1 `--help` tarda o falla por imports pesados

`validate_ocr.py` importa `detect_columns.py`, que a su vez puede inicializar librerias pesadas.
Acciones:

- usar entorno limpio de Python 3.11
- verificar instalacion de dependencias de layout
- exportar `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'`

### 10.2 DeepSeek se omite

Causas comunes:

- No hay CUDA
- Falta `--deepseek-model-path`
- Faltan paquetes `torch`/`transformers`

### 10.3 Tesseract no encontrado

Pasa `--tesseract-cmd` con la ruta del ejecutable.

### 10.4 Paddle no disponible

Instalar `paddlepaddle` + `paddleocr` y revisar conectividad inicial de modelos.
