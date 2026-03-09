# Guia de uso de `validate_ocr.py`

Esta guia documenta solo el validador OCR multi-motor. Para instalacion general y flujo
global del proyecto, consulta `README.md`.

## 1. Que hace `validate_ocr.py`

El validador ejecuta este pipeline:

1. Carga una o varias configuraciones de layout.
2. Detecta regiones de texto por imagen.
3. Ejecuta uno o varios motores OCR sobre esas mismas regiones.
4. Calcula metricas agregadas de contenido, duplicados y tiempos.
5. Guarda resultados por configuracion y por motor.

La unidad real de evaluacion es:

- `configuracion_de_layout x motor_ocr x imagen`

La ventaja principal del script es que desacopla la comparacion OCR del problema de layout:
para una configuracion dada, todos los OCR procesan exactamente los mismos recortes.

## 2. Requisitos del validador

### Comunes

Necesitas al menos:

- `detect_columns.py`
- una carpeta de imagenes, por defecto `imgs/`
- `pandas`, `numpy`, `opencv-python`

Preparacion minima:

```powershell
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install pandas numpy opencv-python
```

### EasyOCR

```powershell
py -3.11 -m pip install easyocr
```

### Tesseract

```powershell
py -3.11 -m pip install pytesseract
```

En Windows, si Tesseract no esta en PATH, usa:

```powershell
--tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### PaddleOCR

```powershell
py -3.11 -m pip install paddlepaddle paddleocr
```

Para evitar chequeos remotos de Paddle:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
```

### DeepSeek OCR local

Necesitas:

- GPU CUDA recomendada
- `torch` y `transformers`
- modelo local en `models/DeepSeek-OCR/` o en la ruta que pases por CLI

Base recomendada en este proyecto:

```powershell
py -3.11 -m pip install torch transformers
py -3.11 -m pip install --upgrade "transformers==4.53.3"
```

## 3. Modos de entrada

El script puede obtener configuraciones de layout de dos formas.

### Modo ranking

Lee las mejores configuraciones desde `experiment_ranking.csv`.

Ejemplo:

```powershell
py -3.11 validate_ocr.py --top 3
```

### Modo manual

Recibe las configuraciones por `--configs` en JSON, sin depender del ranking.

Ejemplo:

```powershell
py -3.11 validate_ocr.py --configs '[
  {"method":"doclayout","conf":0.2,"nms_iou":0.4,"merge_distance":10},
  {"method":"opencv","merge_distance":10}
]'
```

## 4. Opciones CLI reales

Estas son las opciones expuestas actualmente por `validate_ocr.py`:

```text
--top N
--method {opencv,doclayout,yolo11,paddleocr,docling}
--configs JSON
--images-dir PATH
--ranking-csv PATH
--output-dir PATH
--no-ocr
--resume
--langs es,en
--ocr-engines easyocr,tesseract,paddle,deepseek
--deepseek-model-path PATH
--deepseek-prompt TEXT
--deepseek-base-size INT
--deepseek-image-size INT
--deepseek-crop-mode
--tesseract-cmd PATH
```

Nota importante:

- `--report-only` no existe en la CLI actual

## 5. Significado de cada opcion

### Seleccion de configuraciones

- `--top N`: numero de configuraciones a tomar desde el ranking
- `--method`: filtra el ranking por un metodo concreto
- `--configs JSON`: lista manual de configuraciones
- `--ranking-csv PATH`: CSV generado por `analyze_experiments.py`

### Datos de entrada y salida

- `--images-dir PATH`: carpeta de imagenes a procesar
- `--output-dir PATH`: carpeta raiz donde se guardan los resultados

### Control de ejecucion

- `--no-ocr`: ejecuta solo deteccion, sin OCR
- `--resume`: salta imagenes ya procesadas dentro de resultados previos

### Motores OCR

- `--langs es,en`: idiomas de EasyOCR separados por coma
- `--ocr-engines ...`: lista de motores separados por coma
- `--tesseract-cmd PATH`: ruta a `tesseract.exe` si no esta en PATH

### DeepSeek

- `--deepseek-model-path PATH`: ruta local del modelo
- `--deepseek-prompt TEXT`: prompt usado por region
- `--deepseek-base-size INT`: tamaño base para `infer`
- `--deepseek-image-size INT`: tamaño de imagen para `infer`
- `--deepseek-crop-mode`: activa `crop_mode`

## 6. Configuraciones de layout admitidas

Segun `experiment_models.py`, el espacio de busqueda es:

- `methods`: `doclayout`, `yolo11`, `paddleocr`, `docling`, `opencv`
- `conf_thresholds`: `0.1, 0.2, 0.3, 0.4`
- `nms_iou`: `0.3, 0.4, 0.5, 0.6`
- `merge_distance`: `5, 10, 15, 20`

### Estructura por metodo

- `doclayout` y `yolo11`:
  - `{"method":"doclayout|yolo11","conf":X,"nms_iou":Y,"merge_distance":Z}`
- `paddleocr` y `docling`:
  - `{"method":"paddleocr|docling","nms_iou":Y,"merge_distance":Z}`
- `opencv`:
  - `{"method":"opencv","merge_distance":Z}`

Conteo total:

- `doclayout`: `64`
- `yolo11`: `64`
- `paddleocr`: `16`
- `docling`: `16`
- `opencv`: `4`

Total: `164` configuraciones.

## 7. Motores OCR soportados

`--ocr-engines` acepta combinaciones de:

- `easyocr`
- `tesseract`
- `paddle`
- `deepseek`

Ejemplos:

- `--ocr-engines easyocr`
- `--ocr-engines easyocr,tesseract`
- `--ocr-engines easyocr,tesseract,paddle,deepseek`

## 8. Ejemplos de uso

### Top-3 del ranking con los cuatro motores

```powershell
py -3.11 validate_ocr.py --top 3 --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path ".\models\DeepSeek-OCR" --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Solo `opencv` con los cuatro motores

```powershell
py -3.11 validate_ocr.py --method opencv --top 4 --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path ".\models\DeepSeek-OCR"
```

### Configuraciones manuales para varios metodos

```powershell
py -3.11 validate_ocr.py --configs '[
  {"method":"doclayout","conf":0.2,"nms_iou":0.4,"merge_distance":10},
  {"method":"yolo11","conf":0.2,"nms_iou":0.4,"merge_distance":10},
  {"method":"paddleocr","nms_iou":0.4,"merge_distance":10},
  {"method":"docling","nms_iou":0.4,"merge_distance":10},
  {"method":"opencv","merge_distance":10}
]' --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path ".\models\DeepSeek-OCR"
```

### Solo deteccion, sin OCR

```powershell
py -3.11 validate_ocr.py --top 5 --no-ocr
```

### Reanudar ejecucion interrumpida

```powershell
py -3.11 validate_ocr.py --top 5 --resume --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path ".\models\DeepSeek-OCR"
```

### DeepSeek con prompt oficial y tamaños seguros

```powershell
py -3.11 validate_ocr.py --ocr-engines deepseek --deepseek-model-path ".\models\DeepSeek-OCR" --deepseek-prompt "<image>
<|grounding|>Convert the document to markdown." --deepseek-base-size 1024 --deepseek-image-size 1024
```

## 9. Salidas generadas

Por cada configuracion de layout se crea un directorio dentro de `validation_results/`:

- `validation_results/<label_config>/results_easyocr.json`
- `validation_results/<label_config>/results_tesseract.json`
- `validation_results/<label_config>/results_paddle.json`
- `validation_results/<label_config>/results_deepseek.json`

Cada archivo contiene, entre otros datos:

- metricas agregadas del motor
- resultados por imagen
- resultados por region
- tiempos de deteccion y OCR

## 10. Score interno

La formula actual es:

`score = chars*1.0 + words*5.0 - duplicados*50.0 - imgs_sin_deteccion*20.0`

Donde:

- `chars`: total de caracteres OCR
- `words`: total de palabras OCR
- `duplicados`: pares de cajas superpuestas o redundantes
- `imgs_sin_deteccion`: imagenes sin regiones detectadas

Este score es util para comparacion interna rapida, pero no sustituye a la comparacion
contra ground truth.

## 11. Dimension esperada de una ejecucion

Si ejecutas:

- `N` configuraciones de layout
- `M` motores OCR
- `K` imagenes

El total de evaluaciones es:

- `N x M x K`

Ejemplo:

- `N=5`
- `M=4`
- `K=18`

Total: `360` evaluaciones.

## 12. Recomendaciones practicas

### Para iterar rapido

- usa `--ocr-engines easyocr,paddle`
- usa `--method opencv` o un `--top` pequeno
- prueba primero con pocas imagenes en `imgs/`

### Para comparativa final seria

- genera primero el ranking con `experiment_models.py` + `analyze_experiments.py`
- ejecuta `validate_ocr.py` con varios motores
- despues ejecuta `compare_validation_vs_ground_truth.py`

### Para DeepSeek

- mantente en `1024 x 1024` para recortes
- usa el modelo local `models/DeepSeek-OCR`
- no asumas que `flash-attn` estara disponible en Windows

## 13. Troubleshooting

### `--help` tarda mucho o falla por imports pesados

`validate_ocr.py` importa `detect_columns.py`, que puede inicializar librerias de layout costosas.

### DeepSeek se omite

Causas comunes:

- no hay CUDA
- falta `--deepseek-model-path`
- faltan `torch` o `transformers`
- hay incompatibilidad en `transformers` por no respetar la version fijada

### Tesseract no encontrado

Pasa `--tesseract-cmd` con la ruta del ejecutable.

### Paddle no disponible

Instala `paddlepaddle` y `paddleocr` y revisa la variable:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
```

### El validador no encuentra imagenes

Revisa `--images-dir`. El script solo procesa extensiones de imagen soportadas.
