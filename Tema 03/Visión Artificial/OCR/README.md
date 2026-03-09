# OCR Layout + Multi-OCR + Ground Truth Evaluation

Proyecto de Vision Artificial orientado a documentos historicos y material impreso escaneado.
El objetivo es separar correctamente las regiones de texto, ejecutar varios motores OCR sobre
las mismas detecciones y comparar tanto el rendimiento interno del pipeline como la calidad
final frente a ground truth.

El repositorio ya cubre el flujo completo:

1. Deteccion de layout por multiples metodos.
2. Grid search de configuraciones de deteccion.
3. Ranking de configuraciones con metricas heuristicas.
4. Validacion multi-motor OCR reutilizando una sola deteccion por configuracion.
5. Ground truth OCR almacenado en JSON.
6. Comparacion OCR vs ground truth con CER, WER, accuracy de contenido y analisis de orden.

## Objetivo del proyecto

Este proyecto intenta responder tres preguntas:

1. Que metodo de layout detecta mejor las regiones utiles de texto en documentos complejos.
2. Que motor OCR extrae mejor el contenido cuando todos reciben exactamente las mismas regiones.
3. Cuanto se degrada el resultado final frente al texto real anotado manualmente.

La unidad real de evaluacion es:

`configuracion_de_layout x motor_ocr x imagen`

## Estado actual

- Layout methods implementados: `opencv`, `doclayout`, `yolo11`, `paddleocr`, `docling`
- OCR engines implementados: `easyocr`, `tesseract`, `paddle`, `deepseek`
- Grid search de layout: implementado en `experiment_models.py`
- Ranking y analisis estadistico: implementado en `analyze_experiments.py`
- Validacion OCR multi-motor: implementada en `validate_ocr.py`
- Ground truth OCR: disponible en `ground_truth/ocr_ground_truth.json`
- Comparacion OCR vs ground truth: implementada en `compare_validation_vs_ground_truth.py`

## Flujo completo del proyecto

### Fase 1. Deteccion de layout

`detect_columns.py` localiza regiones de texto o columnas dentro de una imagen.

Metodos disponibles:

- `opencv`: heuristico, rapido, sin modelos DL
- `doclayout`: DocLayout-YOLO basado en YOLOv10 y DocStructBench
- `yolo11`: modelo YOLO11 fine-tuned sobre DocLayNet
- `paddleocr`: detector de layout de PaddleOCR PP-StructureV3
- `docling`: detector de layout de IBM Docling

### Fase 2. Grid search de configuraciones

`experiment_models.py` recorre automaticamente el espacio de configuraciones de layout:

- `doclayout` y `yolo11`: `conf x nms_iou x merge_distance`
- `paddleocr` y `docling`: `nms_iou x merge_distance`
- `opencv`: `merge_distance`

El grid actual suma `164` configuraciones.

### Fase 3. Ranking de configuraciones

`analyze_experiments.py` analiza `experiment_results.json` y genera un ranking con una
heuristica que prioriza cobertura textual y penaliza solapamiento, cajas vacias,
cajas diminutas y duplicados.

Salidas principales:

- `experiment_ranking.csv`
- `experiment_top.txt`

### Fase 4. Validacion multi-motor OCR

`validate_ocr.py` toma las mejores configuraciones del ranking o una lista manual,
detecta las regiones una sola vez por imagen/configuracion y ejecuta OCR con uno o varios
motores sobre esos mismos recortes.

Esto permite comparar motores OCR de forma justa, sin introducir variabilidad en la deteccion.

### Fase 5. Ground truth

El ground truth OCR ya existe en:

- `ground_truth/ocr_ground_truth.json`

Cada entrada representa el texto de referencia por imagen.

### Fase 6. Comparacion contra ground truth

`compare_validation_vs_ground_truth.py` compara los resultados generados en `validation_results/`
contra el ground truth y calcula:

- `cer_raw`
- `wer_raw`
- `cer_content`
- `wer_content`
- `content_accuracy`
- `disorder`
- `needs_reorder`

Con esto se separan dos problemas distintos:

- error de reconocimiento del contenido
- error de orden de lectura de las regiones

## Estructura del repositorio

### Scripts nucleares

- `detect_columns.py`: detector de layout multi-metodo
- `post_processing.py`: NMS, merge y limpieza de cajas
- `output_utils.py`: gestion comun de carpetas de salida en `build/`
- `validate_ocr.py`: validacion OCR multi-motor y generacion de informes
- `compare_validation_vs_ground_truth.py`: comparacion contra ground truth

### Analisis y experimentacion

- `experiment_models.py`: grid search sobre las imagenes del dataset
- `analyze_experiments.py`: ranking de configuraciones de layout
- `benchmark_methods.py`: benchmark de tiempo y cobertura entre metodos
- `validate_18_popurris.py`: validacion base sobre las imagenes `popurri*.jpg`
- `compare_ocr_models.py`: comparativa automatizada entre OCR clasicos y DeepSeek

### Scripts OCR individuales

- `paddle-pruebas.py`: OCR por columnas con PaddleOCR
- `easyocr-pruebas.py`: OCR por columnas con EasyOCR
- `tesseract-pruebas.py`: OCR con Tesseract, con o sin columnas
- `pruebas-deepseek.py`: OCR y parsing con DeepSeek-OCR

### Instalacion y soporte

- `install.bat`: instalacion automatica recomendada en Windows
- `check_prerequisites.py`: verificacion de prerequisitos del sistema
- `download_doclayout_model.py`: descarga del modelo de DocLayout-YOLO
- `sitecustomize.py`: shim de compatibilidad para DeepSeek-OCR

### Datos y resultados

- `imgs/`: imagenes de prueba
- `models/DeepSeek-OCR/`: modelo local DeepSeek-OCR
- `ground_truth/ocr_ground_truth.json`: verdad terreno OCR
- `validation_results/`: resultados por configuracion y motor OCR
- `experiment_results.json`: resultados crudos del grid search
- `experiment_ranking.csv`: ranking agregado de configuraciones
- `ocr_gt_comparison_report.csv`: informe agregado OCR vs ground truth
- `ocr_gt_comparison_report.json`
- `ocr_gt_comparison_report.txt`

## Requisitos

### Obligatorios

- Python `3.10` o `3.11`
- Tesseract OCR instalado en sistema si vas a usar `tesseract`

### Recomendados

- Git para descargas desde Hugging Face
- GPU NVIDIA con CUDA para `doclayout`, `docling`, `paddleocr` y especialmente `deepseek`

### Dependencias Python relevantes

El proyecto fija dependencias importantes por compatibilidad:

- `transformers==4.53.3`
- `tokenizers>=0.21.0,<0.22.0`
- `numpy>=1.24.0,<2.0`
- `doclayout-yolo>=0.0.3`
- `ultralytics>=8.2.103,<9.0.0`
- `easyocr>=1.7.0`
- `pytesseract>=0.3.10`

`requirements.txt` contiene el resto del stack.

## Instalacion

### Windows recomendado

La via recomendada es usar el instalador interactivo:

```powershell
install.bat
```

El script:

- verifica Python 3.11, Tesseract, Git y GPU
- instala PyTorch correcto para GPU o CPU
- instala PaddleOCR y Docling en el orden correcto
- instala el resto de dependencias
- descarga el modelo de DocLayout-YOLO
- copia `sitecustomize.py` a `site-packages` para compatibilidad con DeepSeek

### Verificacion rapida de prerequisitos

```powershell
py -3.11 check_prerequisites.py
```

### Instalacion manual

Si necesitas una instalacion paso a paso o quieres adaptar el entorno manualmente,
usa este README como referencia y revisa `requirements.txt`, `install.bat` y
`check_prerequisites.py`.

## Compatibilidad importante

### DeepSeek + Docling + transformers

DeepSeek-OCR y Docling no comparten de forma natural la misma rama de `transformers`.
En este proyecto la compatibilidad validada en Windows/Python 3.11 se resuelve con:

- `transformers==4.53.3`
- `sitecustomize.py` copiado a `site-packages`

Ese shim reexpone simbolos de Llama que DeepSeek espera, sin tener que modificar el
codigo del modelo remoto.

### DeepSeek en Windows

- `flash-attn` es opcional; existe fallback sin esa extension
- la configuracion estable para regiones en este proyecto es `1024 x 1024`
- `640 x 640` puede disparar un bug interno relacionado con `param_img`

### PaddleOCR en Windows

El instalador fija `paddlepaddle==3.2.2` porque versiones mas nuevas han dado problemas
de compatibilidad en Windows con este flujo.

## Uso rapido

### 1. Detectar layout en una imagen

```powershell
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method opencv --debug
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method doclayout --debug
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method yolo11 --yolo11-size nano --debug
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method paddleocr --debug
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method docling --debug
```

Parametros utiles de post-procesado:

- `--nms-iou`
- `--merge-distance`
- `--min-area`
- `--disable-nms`
- `--disable-merge`
- `--disable-filter`

### 2. Ejecutar OCR por imagen o carpeta

Ejemplo con PaddleOCR:

```powershell
py -3.11 paddle-pruebas.py imgs/popurri01.jpg --method doclayout --debug
py -3.11 paddle-pruebas.py imgs/ --method doclayout
```

Hay scripts equivalentes para EasyOCR, Tesseract y DeepSeek.

### 3. Validar las 18 imagenes de popurris

```powershell
py -3.11 validate_18_popurris.py --method doclayout
py -3.11 validate_18_popurris.py --method opencv
```

### 4. Ejecutar grid search de layout

```powershell
py -3.11 experiment_models.py
py -3.11 experiment_models.py --methods doclayout yolo11
py -3.11 experiment_models.py --resume
```

### 5. Analizar resultados y generar ranking

```powershell
py -3.11 analyze_experiments.py
py -3.11 analyze_experiments.py --input experiment_results.json --top 5
```

### 6. Validar OCR multi-motor

Ejemplo con los cuatro motores:

```powershell
py -3.11 validate_ocr.py --top 3 --ocr-engines easyocr,tesseract,paddle,deepseek --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe" --deepseek-model-path ".\models\DeepSeek-OCR"
```

Ejemplo solo deteccion:

```powershell
py -3.11 validate_ocr.py --top 5 --no-ocr
```

Ejemplo reanudando una ejecucion:

```powershell
py -3.11 validate_ocr.py --resume --ocr-engines easyocr,tesseract,paddle,deepseek --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe" --deepseek-model-path ".\models\DeepSeek-OCR"
```

Ejemplo con configuraciones manuales:

```powershell
py -3.11 validate_ocr.py --configs '[
	{"method":"doclayout","conf":0.2,"nms_iou":0.4,"merge_distance":10},
	{"method":"yolo11","conf":0.2,"nms_iou":0.4,"merge_distance":10},
	{"method":"paddleocr","nms_iou":0.4,"merge_distance":10},
	{"method":"docling","nms_iou":0.4,"merge_distance":10},
	{"method":"opencv","merge_distance":10}
]' --ocr-engines easyocr,tesseract,paddle,deepseek --deepseek-model-path ".\models\DeepSeek-OCR"
```

### 7. Comparar validacion OCR contra ground truth

```powershell
py -3.11 compare_validation_vs_ground_truth.py
```

Opcionalmente puedes personalizar rutas:

```powershell
py -3.11 compare_validation_vs_ground_truth.py --validation-dir validation_results --ground-truth ground_truth/ocr_ground_truth.json
```

## Como se interpretan los resultados

### Ranking de layout

`analyze_experiments.py` genera un score heuristico donde domina la cobertura textual.
Cuanto mas alto el score:

- mas texto util se cubre
- menos solapamiento residual queda
- menos cajas vacias o fragmentadas aparecen

### Validacion OCR interna

`validate_ocr.py` calcula por configuracion y por motor OCR:

- caracteres totales
- palabras totales
- duplicados
- imagenes sin deteccion
- tiempo de deteccion y OCR
- score interno de recuperacion

Formula actual:

`score = chars*1.0 + words*5.0 - duplicados*50.0 - imgs_sin_deteccion*20.0`

### Comparacion con ground truth

`compare_validation_vs_ground_truth.py` genera dos tipos de metricas:

- metricas raw: penalizan tanto errores de OCR como orden de lectura incorrecto
- metricas content: intentan medir si el contenido fue recuperado aunque el orden este mal

Esto es util cuando el detector encuentra bien las cajas, pero el ensamblado de lectura
necesita reordenacion posterior.

## Salidas generadas

### Salidas de deteccion y OCR por imagen

Los scripts individuales suelen crear carpetas timestampadas en `build/` usando esta forma:

- `build/<imagen>-<metodo>-YYYYMMDD-HHMM/`

Segun el script, dentro puede haber:

- imagenes de debug con cajas
- recortes por region
- textos OCR por columna
- `summary.json`

### Salidas de validacion OCR

En `validation_results/<label_config>/` se generan ficheros como:

- `results_easyocr.json`
- `results_tesseract.json`
- `results_paddle.json`
- `results_deepseek.json`

Ademas, `validate_ocr.py` genera informes globales agregados:

- `ocr_validation_report.json`
- `ocr_validation_report.csv`
- `ocr_validation_report.txt`

### Salidas de comparacion con ground truth

- `ocr_gt_comparison_report.csv`
- `ocr_gt_comparison_report.json`
- `ocr_gt_comparison_report.txt`

## Flujos recomendados

### Si quieres mejorar deteccion de layout

1. Ejecuta `detect_columns.py` con `--debug` sobre varias imagenes.
2. Corre `experiment_models.py`.
3. Analiza con `analyze_experiments.py`.
4. Valida las mejores configuraciones con `validate_ocr.py`.

### Si quieres comparar motores OCR

1. Parte de un ranking ya generado.
2. Ejecuta `validate_ocr.py` con varios motores.
3. Revisa `validation_results/` y los informes globales.
4. Corre `compare_validation_vs_ground_truth.py` si quieres calidad real frente a referencia.

### Si trabajas en CPU

- prioriza `opencv` para iterar rapido
- usa `doclayout`, `docling` o `deepseek` solo cuando necesites validar calidad

### Si trabajas en GPU

- usa `doclayout`, `yolo11`, `docling` y `deepseek` para comparativas completas
- manten la configuracion DeepSeek en `1024` para evitar problemas observados en recortes

## Troubleshooting rapido

### Tesseract no encontrado

Pasa la ruta explicita:

```powershell
--tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### DeepSeek se omite o falla al cargar

Revisa:

- que exista `models/DeepSeek-OCR/`
- que haya `torch` y `transformers` instalados
- que el entorno tenga GPU si vas a usar el flujo principal de DeepSeek
- que `sitecustomize.py` se haya copiado correctamente a `site-packages`

### `validate_ocr.py --help` tarda demasiado

El script importa dependencias pesadas de layout. Es normal que tarde mas que un CLI simple.

### Paddle intenta hacer chequeos externos

Usa esta variable de entorno:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
```

## Documentacion complementaria

- `GUIA_VALIDATE_OCR.md`: guia completa de `validate_ocr.py`