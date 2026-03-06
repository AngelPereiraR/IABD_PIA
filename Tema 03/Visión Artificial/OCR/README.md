# OCR Layout + Multi-OCR Validation

Proyecto de Vision Artificial para detectar regiones de texto (layout) en documentos
y extraer texto con multiples motores OCR, incluyendo validacion comparativa por
configuracion de layout x motor OCR x imagen.

## Estado actual

- Layout methods: `opencv`, `doclayout`, `yolo11`, `paddleocr`, `docling`
- OCR engines: `easyocr`, `tesseract`, `paddle`, `deepseek`
- Validacion FASE 4: implementada en `validate_ocr.py`
- Pipeline optimizado: una sola deteccion por imagen/configuracion, reutilizada en todos los OCR

## Estructura rapida

- `detect_columns.py`: deteccion de regiones/columnas por metodo de layout
- `post_processing.py`: NMS, merge y limpieza de cajas
- `paddle-pruebas.py`: pipeline OCR principal por imagen/carpeta
- `validate_ocr.py`: validacion multi-motor (FASE 4)
- `experiment_models.py`: grid search de configuraciones de layout
- `analyze_experiments.py`: ranking de configuraciones
- `benchmark_methods.py`: benchmark de metodos de deteccion
- `validate_18_popurris.py`: validacion base sobre el dataset de 18 imagenes

## Documentacion

- `QUICKSTART.md`: instalacion y primeros comandos
- `GUIA_VALIDATE_OCR.md`: guia completa de `validate_ocr.py`

## Requisitos

- Python `3.10` o `3.11`
- Tesseract OCR instalado en sistema (si usas motor `tesseract`)
- GPU CUDA recomendada para DeepSeek y metodos DL

## Instalacion recomendada (Windows)

```powershell
install.bat
```

Instalacion manual: consulta `QUICKSTART.md`.

## Comandos base

### Deteccion de layout

```powershell
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method doclayout --debug
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method opencv --debug
```

### OCR completo por imagen/carpeta

```powershell
py -3.11 paddle-pruebas.py imgs/popurri01.jpg --method doclayout --debug
py -3.11 paddle-pruebas.py imgs/ --method doclayout
```

### Validacion multi-motor OCR (FASE 4)

```powershell
py -3.11 validate_ocr.py --ocr-engines easyocr,tesseract,paddle,deepseek --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe" --deepseek-model-path ".\models\DeepSeek-OCR"
```

## Notas DeepSeek

- Modelo local recomendado: `.\models\DeepSeek-OCR`
- Rango recomendado de `transformers`:

```powershell
py -3.11 -m pip install --upgrade "transformers>=4.51.1,<4.56.0"
```

## Proximos pasos del roadmap

- FASE 5: crear `ground_truth/ocr_ground_truth.json`
- FASE 6: comparar resultados OCR vs ground truth (CER/WER)
