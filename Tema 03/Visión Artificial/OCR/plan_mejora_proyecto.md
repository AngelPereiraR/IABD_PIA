# Plan Detallado: Optimización de Detección de Layout con YOLO y Modelos Alternativos

## Estado actual (actualizado a marzo 2026)

- ✅ `validate_ocr.py` implementado y operativo en modo multi-motor (`easyocr,tesseract,paddle,deepseek`).
- ✅ Optimización aplicada: detección de layout reutilizada por imagen/config para todos los OCR (sin repetir detección por motor).
- ✅ Integración de argumentos requeridos en ejemplos de uso (`--tesseract-cmd`, `--deepseek-model-path`).
- ✅ Prompt por defecto de DeepSeek actualizado para OCR documental real.
- ✅ Tesseract validado en ejecución real (`chars` y `words` > 0).
- ⚠️ DeepSeek en fase de estabilización de compatibilidad `transformers`/cache (`DynamicCache`) según entorno.
- ✅ FASE 4 (validación OCR multi-motor) puede considerarse implementada a nivel de pipeline.
- ⏳ Pendiente principal: FASE 5/6 con ground truth (`ocr_ground_truth.json` + script de comparación CER/WER).

## Contexto del Problema

### Situación Actual

- **Dataset**: 18 imágenes de prueba (popurri01.jpg - popurri18.jpg) con documentos multi-columna
- **Métodos Implementados**:
  - OpenCV (projection-based): Rápido pero con MIN_CONF=0.99 que fusiona columnas incorrectamente
  - DocLayout-YOLO (YOLOv10): Mejor calidad OCR pero con problemas de duplicaciones y regiones perdidas

### Problemas Identificados

1. **DocLayout-YOLO con threshold bajo (<0.25)**: Detecta misma región 2+ veces (duplicaciones)
2. **DocLayout-YOLO con threshold alto (>0.3)**: Pierde regiones de texto válidas
3. **OpenCV MIN_CONF=0.99**: Bug crítico que impide separación correcta de columnas
4. **Falta de post-procesamiento**: No hay NMS, merging de cajas, ni filtrado de ruido

### Objetivo

Experimentar y comparar múltiples enfoques (mejorar DocLayout-YOLO + probar modelos alternativos) para encontrar la configuración óptima que minimice duplicaciones y maximice cobertura de texto.

---

## FASE 1: Implementación de Post-Procesamiento

### 1.1 Crear módulo `post_processing.py`

**Archivo**: `post_processing.py`

**Funciones a implementar**:

```python
def calculate_iou(box1, box2):
    """Calcula Intersection over Union entre dos cajas [x1,y1,x2,y2]"""
    # Implementación estándar de IoU

def apply_nms(boxes, scores, iou_threshold=0.5):
    """
    Non-Maximum Suppression para eliminar duplicados
    Args:
        boxes: List[(x1,y1,x2,y2,label)]
        scores: List[float] - confidences
        iou_threshold: float - umbral IoU para considerar duplicado
    Returns:
        indices: List[int] - índices de cajas a mantener
    """
    # Ordenar por score descendente
    # Iterar y eliminar cajas con IoU > threshold

def merge_close_boxes(boxes, distance_threshold=10, axis='vertical'):
    """
    Fusiona cajas cercanas que probablemente sean la misma región
    Args:
        boxes: List[(x1,y1,x2,y2,label)]
        distance_threshold: Distancia mínima para fusionar
        axis: 'vertical', 'horizontal', 'both'
    Returns:
        merged_boxes: List[(x1,y1,x2,y2,label)]
    """
    # Calcular distancias entre cajas
    # Fusionar cajas dentro del threshold

def filter_noise_boxes(boxes, min_area=100, min_aspect_ratio=0.1, max_aspect_ratio=50):
    """
    Filtra cajas que probablemente sean ruido
    Args:
        boxes: List[(x1,y1,x2,y2,label)]
        min_area: Área mínima en píxeles
        min/max_aspect_ratio: Ratio ancho/alto aceptable
    Returns:
        filtered_boxes: List[(x1,y1,x2,y2,label)]
    """
    # Calcular área y aspect ratio
    # Filtrar cajas fuera de rangos

def process_detections(boxes, scores,
                       nms_iou=0.5,
                       merge_distance=10,
                       min_area=100,
                       enable_nms=True,
                       enable_merge=True,
                       enable_filter=True):
    """
    Pipeline completo de post-procesamiento
    Args:
        boxes, scores: Detecciones raw del modelo
        nms_iou: Threshold para NMS
        merge_distance: Distancia para merging
        min_area: Área mínima para filtrado
        enable_*: Flags para activar/desactivar cada paso
    Returns:
        processed_boxes: Cajas procesadas listas para OCR
    """
    result = boxes.copy()

    if enable_nms:
        indices = apply_nms(result, scores, nms_iou)
        result = [result[i] for i in indices]
        scores = [scores[i] for i in indices]

    if enable_merge:
        result = merge_close_boxes(result, merge_distance)

    if enable_filter:
        result = filter_noise_boxes(result, min_area)

    return result
```

### 1.2 Integrar post-procesamiento en `detect_columns.py`

**Modificaciones**:

1. Importar módulo:

```python
import post_processing as pp
```

2. Actualizar `detect_columns_doclayout()`:

```python
def detect_columns_doclayout(image_path,
                            conf_threshold=0.25,
                            nms_iou=0.5,
                            merge_distance=10,
                            min_area=100,
                            enable_nms=True,
                            enable_merge=True,
                            enable_filter=True,
                            debug=False):
    # ... código existente hasta obtener boxes y scores ...

    # NUEVO: Aplicar post-procesamiento
    if enable_nms or enable_merge or enable_filter:
        boxes = pp.process_detections(
            boxes, scores,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter
        )

    return boxes
```

3. Añadir argumentos CLI:

```python
parser.add_argument('--nms-iou', type=float, default=0.5,
                    help='IoU threshold for NMS (default: 0.5)')
parser.add_argument('--merge-distance', type=int, default=10,
                    help='Distance threshold for merging boxes (default: 10)')
parser.add_argument('--min-area', type=int, default=100,
                    help='Minimum box area to keep (default: 100)')
parser.add_argument('--disable-nms', action='store_true',
                    help='Disable NMS post-processing')
parser.add_argument('--disable-merge', action='store_true',
                    help='Disable box merging')
parser.add_argument('--disable-filter', action='store_true',
                    help='Disable noise filtering')
```

### 1.3 Prueba inicial ✅ COMPLETADO

```bash
# Sin post-procesamiento (baseline)
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method doclayout --doclayout-conf 0.2 --disable-nms --disable-merge --disable-filter --debug

# Con NMS solamente
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method doclayout --doclayout-conf 0.2 --nms-iou 0.3 --debug

# Pipeline completo
py -3.11 detect_columns.py --image imgs/popurri01.jpg --method doclayout --doclayout-conf 0.2 --nms-iou 0.3 --merge-distance 15 --min-area 200 --debug
```

**Resultado esperado**: Reducción significativa de duplicados sin perder regiones válidas.

**Resultados obtenidos**:

- ✅ Post-procesamiento integrado correctamente
- ✅ Pipeline muestra mensajes de debug informativos:
  ```
  === POST-PROCESSING PIPELINE ===
  Input: 16 boxes
  After NMS (iou=0.4): 16 boxes
  After merging (dist=10): 16 boxes (0 merged)
  After filtering (min_area=100): 16 boxes (0 removed)
  Final output: 16 boxes
  ```
- ✅ Argumentos CLI funcionando correctamente
- ✅ Sin errores en ejecución
- 📝 Nota: popurri01.jpg no presenta duplicaciones con conf>=0.1, lo cual es positivo

---

## ✅ FASE 1 COMPLETADA - Post-Procesamiento Implementado

**Archivos creados:**

- ✅ `post_processing.py` (314 líneas)
  - `calculate_iou()` - Cálculo de Intersection over Union
  - `apply_nms()` - Non-Maximum Suppression
  - `merge_close_boxes()` - Fusión de cajas cercanas
  - `filter_noise_boxes()` - Filtrado de ruido
  - `process_detections()` - Pipeline completo

**Archivos modificados:**

- ✅ `detect_columns.py` (+50 líneas aprox.)
  - Import de `post_processing` module
  - Parámetros de post-procesamiento en `detect_columns_doclayout()`
  - Integración del pipeline de post-procesamiento
  - 6 nuevos argumentos CLI (--nms-iou, --merge-distance, --min-area, --disable-nms, --disable-merge, --disable-filter)
  - Actualizado `detect_columns()` wrapper
  - Actualizado `process_single_image()`

**Completado:** FASE 2.2 - Nuevos modelos alternativos (YOLO11 ✅ → PaddleOCR ✅ → Docling ✅ → ~~LayoutParser~~ ❌)

---

## FASE 2: Integración de Modelos Alternativos

### ⚠️ 2.1 Método 1: PaddleOCR Layout Detection - **PENDIENTE/DESCARTAR**

**Estado:** ❌ Problemas de compatibilidad detectados

**Problema identificado:**

- Error de compatibilidad con PaddlePaddle y oneDNN en Windows
- `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]`
- La versión instalada de PaddleOCR usa una API diferente (LayoutDetection en vez de PPStructure)
- Requiere dependencias adicionales y configuración compleja

**Decisión:** Se descarta PaddleOCR por ahora debido a problemas de estabilidad. Se procederá directamente con Surya Vision Transformer que tiene mejor soporte y es más moderno.

---

### ⚠️ 2.2 Método 2: Surya Vision Transformer - **DESCARTADO**

**Estado:** ❌ No funcional en las imágenes del dataset

**Trabajo realizado:**

- ✅ `surya-ocr 0.17.1` instalado correctamente
- ✅ API investigada: `FoundationPredictor(device='cpu')` + `LayoutPredictor(foundation)` + `layout([PIL_images])`
- ✅ `detect_columns_surya()` implementada (~140 líneas)
- ✅ CLI integrada (`--method surya`, `--surya-conf`)
- ✅ Incompatibilidad con `transformers 5.2.0` resuelta (degradado a 4.57.6)
- ✅ El modelo carga y ejecuta sin errores (~30-45s/imagen en CPU)

**Problema identificado:**

- En todas las imágenes probadas (popurri01.jpg, popurri03.jpg), Surya detecta **exactamente 1 bbox** con coordenadas casi idénticas: `(400, 294, 1200, 879)` → 25% del área central de la imagen
- Labels detectados: `Picture` (conf=0.566) y `SectionHeader` (conf=0.820) respectivamente
- **0 regiones de texto** detectadas en ninguna imagen
- `top_k` muestra que el modelo no ve texto: `Text: 0.036`, resto distribuido entre Picture/SectionHeader
- El bbox idéntico en imágenes distintas indica que el modelo devuelve un **anchor por defecto** al no poder analizar correctamente el documento escaneado

**Conclusión:** Surya Layout Predictor está diseñado para documentos PDF renderizados digitalmente, no para imágenes escaneadas/fotografiadas de periódicos o revistas. El modelo falla sistemáticamente en este dataset.

**Limpieza realizada:**

- ✅ Todo el código Surya eliminado de `detect_columns.py`
- ✅ `test_surya.py` eliminado
- ✅ Importaciones `Any` eliminadas de typing

---

## ❗ FASE 2 - Primera Ronda: PaddleOCR y Surya Descartados

**Resumen:** Los dos primeros candidatos fueron investigados y descartados por incompatibilidad con el dataset.

- ❌ **PaddleOCR (v1):** Bug PIR/oneDNN en PaddlePaddle 3.3.0+ en Windows. Causa raíz identificada: `enable_mkldnn=False` como fix — se retomará en FASE 2.2.
- ❌ **Surya Vision Transformer:** Devuelve 1 bbox genérico idéntico en todas las imágenes (anchor por defecto). Diseñado para PDFs digitales, no funciona con imágenes escaneadas.

**Limpieza realizada:** Código Surya eliminado de `detect_columns.py`, `test_surya.py` eliminado.

---

## ✅ FASE 2.2 COMPLETADA: Nuevos Métodos Alternativos

> ✅ **Fase completada el 2 de marzo de 2026.** Resultados: YOLO11 ✅ | PaddleOCR ✅ (16 regiones) | Docling ✅ (15 regiones) | ~~LayoutParser~~ ❌

---

### ✅ 2.3 Método 3: YOLO11 Fine-tuned (DocLayNet) — Prioridad 🥇

**Estado:** ✅ COMPLETADO · Funcionando correctamente

**Ventajas:**

- API idéntica a la ya implementada DocLayout-YOLO (ambas Ultralytics)
- Entrenado en **DocLayNet** (IBM), 11 clases
- Resolución óptima 1280×1280 (vs 1024 de DocLayout-YOLO)
- Compatible Windows 11 / Python 3.11 sin fricción
- 3 variantes: `nano` (~10–15s CPU), `small`, `medium`

**Instalación:**

```bash
pip install ultralytics huggingface_hub
```

**API básica:**

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

model_path = hf_hub_download(
    repo_id="Armaggheddon/yolo11-document-layout",
    filename="yolo11n_doc_layout.pt",
    local_dir="./models"
)
model = YOLO(model_path)

results = model("document.jpg", imgsz=1280)
for result in results:
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = box.conf[0].item()
        cls_name = model.names[int(box.cls[0])]
```

**Clases (DocLayNet, 11 clases):**

```python
YOLO11_TEXT_LABELS = {"Text", "Title", "Section-header", "Caption", "List-item", "Footnote"}
```

**Función:** `detect_columns_yolo11()` · **CLI:** `--method yolo11 --yolo11-size nano|small|medium`

**Estado:** completado

**Resultados obtenidos:**

- ✅ `ultralytics 8.2.103` + `huggingface_hub 0.36.2` instalados
- ✅ Modelo `yolo11n_doc_layout.pt` descargado de Hugging Face en `./models/`
- ✅ `detect_columns_yolo11()` implementada y funcional
- ✅ CLI: `--method yolo11 --yolo11-size nano|small|medium --yolo11-conf --all-classes`
- ✅ 1 región detectada con conf≥0.25 (solo texto); 19+ regiones con `--all-classes --yolo11-conf 0.1`
- ✅ Fixes aplicados: `nms_iou` (no `nms_iou_threshold`), campo `label` en `ColumnBox`

**Consideraciones:**

- ⚠️ Modelo community (no oficial Ultralytics)
- ⚠️ CPU nano a imgsz=1280: ~10–15s/imagen (vs ~3s de DocLayout-YOLO)
- ✅ Reutiliza exactamente el patrón de `detect_columns_doclayout()`

---

### ✅ 2.4 Método 4: PaddleOCR PP-StructureV3 (retry) — Prioridad 🥈

**Estado:** ✅ COMPLETADO · 16 regiones detectadas en popurri01.jpg

**Causa del fallo anterior:**
Bug en PaddlePaddle 3.3.0+ con executor PIR y backend oneDNN. PaddleX fuerza internamente `run_mode="mkldnn"` ignorando variables de entorno (`FLAGS_use_mkldnn=0` no funciona). Fix confirmado: `enable_mkldnn=False` en el constructor de `PaddleOCR`.

> ⚠️ `PPStructure` fue eliminado en PaddleOCR 3.x. El módulo correcto es `PaddleOCR.predict()` con la pipeline `pp_structurev3`.

**Instalación:**

```bash
pip install paddlepaddle==3.2.2
pip install "paddleocr[doc-parser]"
```

**API real (v3.x) — LayoutDetection:**

```python
import os
os.environ.setdefault('PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK', 'True')
from paddleocr import LayoutDetection  # ⚠️ NO es PaddleOCR — clase eliminada en v3.x

engine = LayoutDetection(enable_mkldnn=False)  # FIX CRÍTICO
for det_result in engine.predict("documento.png"):
    boxes_raw = det_result.json["res"]["boxes"]  # ⚠️ NO det_result["res"]
    for item in boxes_raw:
        label = item["label"]       # str, ej. "text"
        score = item["score"]
        x1, y1, x2, y2 = item["coordinate"]
```

> ⚠️ **Correcciones críticas aplicadas respecto al plan original:**
>
> - `PaddleOCR` no existe en v3.x → usar `LayoutDetection`
> - `det_result["res"]` lanza `KeyError` → usar `det_result.json["res"]["boxes"]`
> - `use_doc_orientation_classify` no existe en `LayoutDetection` → eliminado
> - `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` necesario para deshabilitar checks de red

**Función:** `detect_columns_paddleocr()` · **CLI:** `--method paddleocr`

**Resultados obtenidos:**

- ✅ `paddlepaddle 3.2.2` + `paddleocr[doc-parser]` instalados
- ✅ Modelo `PP-DocLayout_plus-L` descargado automáticamente en `~/.paddlex/`
- ✅ **16 regiones detectadas** en popurri01.jpg
- ✅ `detect_columns_paddleocr()` implementada y funcional

**Consideraciones:**

- ✅ Fix `enable_mkldnn=False` confirmado y funcional
- ✅ `paddlepaddle==3.2.2` estable (sin bug PIR)
- ⚠️ `PaddleOCR-VL` descartada: no disponible sin GPU ≥12 GB VRAM

| Solución                               | Eficacia                |
| -------------------------------------- | ----------------------- |
| `enable_mkldnn=False` en constructor   | ✅ Funciona             |
| Downgrade a `paddlepaddle==3.2.2`      | ✅ Funciona             |
| `os.environ['FLAGS_use_mkldnn'] = '0'` | ❌ PaddleX lo ignora    |
| `use_mkldnn=False` en init             | ❌ No existe en API 3.x |

---

### ✅ 2.5 Método 5: Docling (IBM / Linux Foundation AI) — Prioridad 🥉

**Estado:** ✅ COMPLETADO · 15 regiones detectadas en popurri01.jpg

**Ventajas:**

- Combina layout detection + OCR en un solo pipeline (RT-DETR)
- 13 clases: `TEXT`, `TITLE`, `SECTION_HEADER`, `TABLE`, `PICTURE`, `CAPTION`, `LIST_ITEM`, `FORMULA`, `PAGE_HEADER`, `PAGE_FOOTER`, `FOOTNOTE`, `CODE`, `DOCUMENT_INDEX`
- Compatible Windows 11 / Python 3.11 sin fricción
- Activamente mantenido (v2.76.0, marzo 2026)
- Acepta imágenes directamente (JPEG, PNG, TIFF, BMP, WEBP)

**Instalación:**

```bash
pip install docling
# Descarga automática de modelos (~500 MB) en primera ejecución
```

**API básica:**

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("imagen.jpg")
doc = result.document

for item, level in doc.iterate_items():
    if hasattr(item, 'prov') and item.prov:
        for prov in item.prov:  # ⚠️ Hay que iterar TODOS los prov, no solo prov[0]
            page = prov.page_no
            h = result.pages[page - 1].size.height  # Altura en píxeles
            # ⚠️ Coordenadas son PÍXELES ABSOLUTOS (NO normalizadas 0-1)
            # ⚠️ Origen es BOTTOMLEFT → transformar con to_top_left_origin()
            bbox_tl = prov.bbox.to_top_left_origin(h)
            x1, y1, x2, y2 = bbox_tl.l, bbox_tl.t, bbox_tl.r, bbox_tl.b
            label = item.label.value.upper()  # ej. "TEXT", "TITLE"
```

> ⚠️ **Correcciones críticas respecto al plan original:**
>
> - Bboxes son **píxeles absolutos**, NO normalizadas 0–1 (el plan original era incorrecto)
> - Origen es `CoordOrigin.BOTTOMLEFT` → hay que usar `bbox.to_top_left_origin(h)` o invertir Y manualmente
> - Iteración sobre todos `item.prov` (no solo `prov[0]`)

**Clases de interés:**

```python
DOCLING_TEXT_LABELS = {"TEXT", "TITLE", "SECTION_HEADER", "CAPTION", "LIST_ITEM", "FOOTNOTE"}
```

**Función:** `detect_columns_docling()` · **CLI:** `--method docling`

**Resultados obtenidos:**

- ✅ `docling` instalado (con conflictos de deps menores no bloqueantes)
- ✅ Modelo RT-DETR descargado automáticamente en primera ejecución
- ✅ **15 regiones detectadas** en popurri01.jpg
- ✅ `detect_columns_docling()` implementada y funcional

**Consideraciones:**

- ✅ Funciona bien con imágenes escaneadas (contrariamente a lo esperado)
- ⚠️ Primera descarga ~500 MB (modelos RT-DETR + TableFormer)
- ✅ Modelos alternativos: `docling-layout-egret-medium/large/xlarge` (mayor precisión)

---

### ⚠️ 2.6 Método 6: LayoutParser (backend EfficientDet) — **DESCARTADO**

**Estado:** ❌ No funcional en Windows — código eliminado del proyecto

**Trabajo realizado:**

- ✅ `layoutparser[effdet] 0.3.4` instalado correctamente
- ✅ Fix aplicado: `import torch` antes de `import layoutparser` para precargar DLLs (evita `WinError 127`)
- ✅ `detect_columns_layoutparser()` implementada con degradación graceful (`try/except OSError`)
- ❌ **Bug insalvable** en Windows: `EfficientDetLayoutModel` descarga modelos de Dropbox con URLs tipo `...pth.tar?dl=1` — el carácter `?` es inválido en nombres de archivo Windows → `OSError: Invalid argument`
- ❌ **0 regiones** en todos los tests — la biblioteca no puede cargar ningún modelo

**Conclusión:** LayoutParser (abandonado desde abril 2022) tiene un bug crítico e irresoluble en Windows relacionado con nombres de archivo inválidos al descargar modelos de Dropbox. Al no producir ninguna detección útil, se descarta de igual forma que Surya.

**Limpieza realizada:**

- ✅ Todo el código LayoutParser eliminado de `detect_columns.py`
  - Eliminado: import block (`import torch as _torch_preload`, `import layoutparser as lp_module`)
  - Eliminado: constantes `LAYOUTPARSER_MODELS`, `LAYOUTPARSER_TEXT_LABELS`
  - Eliminado: caché global `_layoutparser_models`
  - Eliminada: función `detect_columns_layoutparser()` completa
  - Eliminado: `elif method == "layoutparser"` del wrapper `detect_columns()`
  - Eliminados: parámetro `lp_model` de `detect_columns()`, `process_single_image()` y `main()`
  - Eliminado: argumento `--lp-model` de la CLI
  - Eliminado: `layoutparser` de la lista `choices` de `--method`
- ✅ `layoutparser[effdet]` comentado en `requirements.txt` (marcado como DESCARTADO)
- ✅ Paso de instalación eliminado de `install.bat`

---

### Tabla resumen FASE 2.2 — **RESULTADOS FINALES**

| Método                    | Estado        | Regiones (popurri01) | Fix aplicado                               | Mantenimiento      |
| ------------------------- | ------------- | -------------------- | ------------------------------------------ | ------------------ |
| YOLO11 fine-tuned         | ✅ Funcional  | 1–19+ (según conf)   | `nms_iou` param fix, label field           | ⚠️ Community       |
| PaddleOCR LayoutDetection | ✅ Funcional  | **16 regiones**      | `LayoutDetection`, `.json["res"]`          | ✅ Activo          |
| Docling                   | ✅ Funcional  | **15 regiones**      | coords BOTTOMLEFT → `to_top_left_origin()` | ✅ Activo v2.76.0  |
| LayoutParser (effdet)     | ❌ DESCARTADO | 0 (ninguna)          | Bug `?dl=1` insalvable — código eliminado  | ❌ Abandonado 2022 |

---

## ✅ FASE 2.2 COMPLETADA - Modelos Alternativos Implementados

**Fecha de completado:** 2 de marzo de 2026

**Archivos modificados:**

- ✅ `detect_columns.py` (~1430 líneas totales)
  - `detect_columns_yolo11()` — funcional, modelo Armaggheddon/yolo11-document-layout
  - `detect_columns_paddleocr()` — funcional, `LayoutDetection` con `enable_mkldnn=False`
  - `detect_columns_docling()` — funcional, coords BOTTOMLEFT corregidas
  - Wrapper `detect_columns()` actualizado con elif branches para 3 nuevos métodos
  - CLI actualizado: `--yolo11-conf`, `--yolo11-size nano|small|medium`

**Test comparativo (popurri01.jpg):**

```
yolo11      → 1 región  (conf≥0.25, solo texto; 19+ con --all-classes --yolo11-conf 0.1)
opencv      → baseline
doclayout   → baseline
paddle ocr  → 16 regiones ✅
docling     → 15 regiones ✅
```

**Scripts de diagnóstico temporales eliminados:** `_test_paddle.py`, `_test_paddle2.py`, `_test_docling.py`

**Próximo paso:** FASE 3 — Ejecutar grid search (`py -3.11 experiment_models.py`) y analizar con `analyze_experiments.py`

> **FASE 3.1 completada** ✅ `experiment_models.py` y `analyze_experiments.py` creados y verificados sin errores estáticos.

---

## FASE 3: Experimentación Sistemática con Grid Search

### 3.1 Crear script `experiment_models.py`

**Objetivo**: Probar todas las combinaciones de [modelos × parámetros] sobre las 18 imágenes.

**Espacio de búsqueda** (ampliar con métodos que pasen las pruebas de FASE 2.2):

```python
EXPERIMENT_GRID = {
    # ✅ Actualizado tras FASE 2.2: yolo11, paddleocr y docling son viables
    # ✅ opencv incluido como método base de referencia (sin modelo DL)
    # ❌ layoutparser descartado (bug Windows ?dl=1 insalvable)
    # ❌ surya descartado (1 bbox genérico en imágenes escaneadas)
    'methods': ['doclayout', 'yolo11', 'paddleocr', 'docling', 'opencv'],
    'conf_thresholds': [0.1, 0.2, 0.3, 0.4],
    'nms_iou': [0.3, 0.4, 0.5, 0.6],
    'merge_distance': [5, 10, 15, 20],
}
```

**Total configuraciones** (valores reales del código):

- DocLayout: 4 conf × 4 nms × 4 merge = 64 configs
- YOLO11: 4 conf × 4 nms × 4 merge = 64 configs
- PaddleOCR: 4 nms × 4 merge = 16 configs (sin conf_threshold)
- Docling: 4 nms × 4 merge = 16 configs (sin conf_threshold)
- OpenCV: 4 merge = 4 configs (sin conf_threshold ni nms_iou)
- ~~Surya: DESCARTADO~~ · ~~LayoutParser: DESCARTADO (Windows bug)~~
- **Total**: 164 configuraciones × 18 imágenes = **2.952 experimentos**

**Código**:

```python
import itertools
import json
import time
from pathlib import Path
from detect_columns import detect_columns
from output_utils import get_output_dir

def run_single_experiment(image_path, method, config):
    """Ejecuta un experimento y retorna métricas"""
    start_time = time.time()

    try:
        if method == 'doclayout':
            boxes = detect_columns(
                image_path,
                method=method,
                conf_threshold=config['conf'],
                nms_iou=config.get('nms_iou', 0.5),
                merge_distance=config.get('merge_distance', 10),
                debug=False
            )
        else:
            boxes = detect_columns(
                image_path,
                method=method,
                conf_threshold=config['conf'],
                debug=False
            )

        elapsed = time.time() - start_time

        # Calcular métricas
        num_boxes = len(boxes)
        avg_area = sum((b[2]-b[0])*(b[3]-b[1]) for b in boxes) / num_boxes if num_boxes > 0 else 0

        # Detectar posibles duplicados (IoU > 0.7)
        duplicates = 0
        for i, box1 in enumerate(boxes):
            for box2 in boxes[i+1:]:
                if calculate_iou(box1[:4], box2[:4]) > 0.7:
                    duplicates += 1

        return {
            'success': True,
            'num_boxes': num_boxes,
            'avg_area': avg_area,
            'duplicates': duplicates,
            'time_ms': elapsed * 1000,
            'boxes': boxes  # Guardar para inspección
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def run_grid_search(images_dir='imgs', output_file='experiment_results.json'):
    """Ejecuta grid search completo"""
    images = sorted(Path(images_dir).glob('popurri*.jpg'))

    results = []
    total_experiments = 0

    # Calcular total
    for method in EXPERIMENT_GRID['methods']:
        confs = EXPERIMENT_GRID['conf_thresholds']
        if method == 'doclayout':
            total_experiments += len(confs) * len(EXPERIMENT_GRID['nms_iou']) * len(EXPERIMENT_GRID['merge_distance']) * len(images)
        else:
            total_experiments += len(confs) * len(images)

    print(f"Total experimentos: {total_experiments}")

    experiment_id = 0

    # Iterar sobre métodos
    for method in EXPERIMENT_GRID['methods']:
        for conf in EXPERIMENT_GRID['conf_thresholds']:

            if method == 'doclayout':
                # Grid completo para DocLayout
                for nms_iou in EXPERIMENT_GRID['nms_iou']:
                    for merge_dist in EXPERIMENT_GRID['merge_distance']:
                        config = {
                            'conf': conf,
                            'nms_iou': nms_iou,
                            'merge_distance': merge_dist
                        }

                        for img_path in images:
                            experiment_id += 1
                            print(f"[{experiment_id}/{total_experiments}] {method} | conf={conf} nms={nms_iou} merge={merge_dist} | {img_path.name}")

                            result = run_single_experiment(img_path, method, config)

                            results.append({
                                'experiment_id': experiment_id,
                                'image': img_path.name,
                                'method': method,
                                'config': config,
                                'metrics': result
                            })
            else:
                # Para métodos sin conf_threshold configurable
                config = {'conf': conf}

                for img_path in images:
                    experiment_id += 1
                    print(f"[{experiment_id}/{total_experiments}] {method} | conf={conf} | {img_path.name}")

                    result = run_single_experiment(img_path, method, config)

                    results.append({
                        'experiment_id': experiment_id,
                        'image': img_path.name,
                        'method': method,
                        'config': config,
                        'metrics': result
                    })

    # Guardar resultados
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados en {output_file}")
    return results

if __name__ == '__main__':
    results = run_grid_search()
```

### 3.2 Análisis de resultados

**Script**: `analyze_experiments.py`

```python
import json
import pandas as pd

def analyze_results(results_file='experiment_results.json'):
    """Analiza resultados de experimentos"""

    with open(results_file) as f:
        results = json.load(f)

    # Convertir a DataFrame
    df = pd.json_normalize(results)

    # Filtrar solo experimentos exitosos
    df_success = df[df['metrics.success'] == True].copy()

    # Calcular métricas agregadas por configuración
    groupby_cols = ['method', 'config.conf']
    if 'config.nms_iou' in df_success.columns:
        groupby_cols.extend(['config.nms_iou', 'config.merge_distance'])

    agg_results = df_success.groupby(groupby_cols).agg({
        'metrics.num_boxes': ['mean', 'std'],
        'metrics.duplicates': ['mean', 'sum'],
        'metrics.time_ms': 'mean'
    }).reset_index()

    # Calcular score compuesto
    # Score = -duplicates_total + boxes_mean (queremos pocas duplicaciones, suficientes boxes)
    agg_results['score'] = (
        -agg_results[('metrics.duplicates', 'sum')] * 10 +  # Penalizar duplicados
        agg_results[('metrics.num_boxes', 'mean')] * 2      # Premiar cobertura
    )

    # Ordenar por score
    agg_results = agg_results.sort_values('score', ascending=False)

    # Mostrar top 10
    print("=== TOP 10 CONFIGURACIONES ===")
    print(agg_results.head(10).to_string())

    # Guardar ranking completo
    agg_results.to_csv('experiment_ranking.csv', index=False)
    print(f"\nRanking completo guardado en experiment_ranking.csv")

    return agg_results

if __name__ == '__main__':
    analyze_results()
```

### 3.3 Ejecución

```bash
# Ejecutar grid search
py -3.11 experiment_models.py

# Analizar resultados
py -3.11 analyze_experiments.py
```

---

## FASE 4: Validación con OCR Completo

### 4.1 Seleccionar top 10 configuraciones

Según ranking de `analyze_experiments.py`, seleccionar las 10 mejores configuraciones.

**Candidatos esperados** (según resultados de FASE 2.2):

1. `paddleocr` — 16 regiones en popurri01.jpg
2. `docling` — 15 regiones en popurri01.jpg
3. `doclayout` con `conf=0.2, nms_iou=0.4, merge_distance=15`
4. `yolo11` con `--all-classes --yolo11-conf 0.1`
5. `opencv` — método base de referencia (proyección de histograma de columnas, sin modelo DL)

### 4.2 Ejecutar OCR completo

Para cada configuración, ejecutar pipeline completo y comparar calidad del texto extraído.

```bash
# Crear directorio de validación
mkdir validation_results

# PaddleOCR (mejor candidato, 16 regiones)
py -3.11 detect_columns.py --image imgs/ --method paddleocr --base-dir validation_results/paddleocr
py -3.11 easyocr-pruebas.py --image imgs/ --base-dir validation_results/paddleocr

# Docling (segundo candidato, 15 regiones)
py -3.11 detect_columns.py --image imgs/ --method docling --base-dir validation_results/docling
py -3.11 easyocr-pruebas.py --image imgs/ --base-dir validation_results/docling

# DocLayout mejorado (método original con post-process)
py -3.11 detect_columns.py --image imgs/ --method doclayout --doclayout-conf 0.2 --nms-iou 0.4 --merge-distance 15 --base-dir validation_results/doclayout_improved
py -3.11 easyocr-pruebas.py --image imgs/ --base-dir validation_results/doclayout_improved
```

### 4.3 Comparar resultados OCR

**Script**: `compare_ocr_quality.py`

```python
import json
from pathlib import Path

def compare_ocr_outputs(dirs):
    """Compara outputs de OCR de múltiples configuraciones"""

    results = {}

    for dir_path in dirs:
        config_name = Path(dir_path).name
        results[config_name] = {}

        # Buscar archivos summary.json
        for img_dir in Path(dir_path).iterdir():
            if img_dir.is_dir():
                summary_file = img_dir / 'summary.json'
                if summary_file.exists():
                    with open(summary_file) as f:
                        data = json.load(f)
                        results[config_name][img_dir.name] = {
                            'total_chars': data.get('total_chars', 0),
                            'total_words': data.get('total_words', 0),
                            'num_columns': len(data.get('columns', []))
                        }

    # Comparar
    print("=== COMPARACIÓN OCR ===\n")

    for config in results:
        total_chars = sum(img['total_chars'] for img in results[config].values())
        total_words = sum(img['total_words'] for img in results[config].values())
        avg_cols = sum(img['num_columns'] for img in results[config].values()) / len(results[config])

        print(f"{config}:")
        print(f"  Total caracteres: {total_chars}")
        print(f"  Total palabras: {total_words}")
        print(f"  Columnas promedio: {avg_cols:.1f}")
        print()

if __name__ == '__main__':
    dirs = [
        'validation_results/docling',
        'validation_results/doclayout_improved'
    ]
    compare_ocr_outputs(dirs)
```

### 4.4 Revisión manual

Seleccionar 3-5 imágenes representativas y revisar manualmente:

- ¿Se perdió texto?
- ¿Hay duplicaciones en el output?
- ¿El orden de lectura es correcto?
- ¿La calidad del texto es coherente?

---

## FASE 5: Definición de Ground Truth y Criterio de Decisión Final

> **Cambio de estrategia**: FASE 5 y FASE 6 quedan centradas en comparar los resultados reales de `validate_ocr.py` (todos los motores OCR ejecutados) contra un archivo de texto real por imagen (ground truth), que actualmente no existe y debe crearse primero.

### 5.1 Crear archivo de verdad terreno (ground truth)

**Nuevo archivo**: `ground_truth/ocr_ground_truth.json`

**Formato propuesto**:

```json
{
  "popurri01.jpg": {
    "text": "...transcripción real completa...",
    "notes": "Opcional: observaciones de lectura"
  },
  "popurri02.jpg": {
    "text": "..."
  }
}
```

**Reglas para crear el ground truth**:

1. Transcripción manual fiel del texto visible de cada imagen.
2. Normalizar saltos de línea y espacios duplicados.
3. Mantener signos de puntuación relevantes.
4. Guardar un único bloque de texto por imagen (sin segmentación por caja).

### 5.2 Criterios de evaluación final (basados en ground truth)

**Métricas obligatorias**:

1. **CER** (Character Error Rate) — principal
2. **WER** (Word Error Rate) — principal
3. **Tiempo medio por imagen** — secundario
4. **Duplicados de detección** — secundario

**Score final recomendado**:

```text
score_final = (1 - CER) * 50 + (1 - WER) * 35 - (time_per_image_ms / 1000) * 10 - (dup_promedio) * 5
```

> Si no hay ground truth completo para las 18 imágenes, usar subset mínimo de 5 imágenes representativas (cabeceras, multicolumna densa, publicidad, texto pequeño, contraste bajo).

### 5.3 Decisión final de stack (layout + OCR)

La decisión final ya no se toma solo por heurísticas de caracteres/palabras.
Se elige la combinación:

`configuración de layout + motor OCR`

que minimice CER/WER frente a `ground_truth/ocr_ground_truth.json`.

### 5.4 Actualizar defaults y documentación

1. Actualizar default de layout en `detect_columns.py` (si aplica).
2. Documentar motor OCR ganador en `README.md`.
3. Generar informe final con tabla de CER/WER por combinación.

### 5.5 Documentación

Crear `LAYOUT_DETECTION_EXPERIMENTS.md`:

````markdown
# Experimentos de Detección de Layout

## Fecha

26 de febrero de 2026

## Objetivo

Optimizar detección de columnas para minimizar duplicaciones y pérdida de texto

## Modelos Evaluados

1. DocLayout-YOLO + post-processing
2. ~~Surya Vision Transformer~~ (DESCARTADO: 1 bbox genérico en imágenes escaneadas)
3. YOLO11 fine-tuned (DocLayNet, Armaggheddon) ✅
4. PaddleOCR LayoutDetection (PP-DocLayout_plus-L) ✅
5. Docling (RT-DETR, IBM/Linux Foundation AI) ✅
6. OpenCV (proyección de histograma de columnas, método base de referencia) ✅
7. ~~LayoutParser EfficientDet~~ (DESCARTADO: bug `?dl=1` insalvable en Windows)

## Resultados

### Grid Search

- Total experimentos: 2.952 (164 configs × 18 imágenes)
- Configuraciones probadas: 164

### Top 10 Configuraciones

1. [Modelo] con [parámetros]: Score X/100
2. [Modelo] con [parámetros]: Score X/100
3. [Modelo] con [parámetros]: Score X/100

### Ganador: [Modelo Seleccionado]

- Configuración: [parámetros]
- Justificación: [razones]
- Limitaciones conocidas: [si aplica]

## Uso

```bash
# Procesamiento con configuración óptima
py -3.11 detect_columns.py --image imgs/ --method [ganador] --conf X.XX
```
````

---

## FASE 6: Comparación de Resultados de Validación contra Ground Truth

> Esta fase reemplaza el benchmark heurístico: en vez de comparar por métricas indirectas, se comparan **todos los resultados de validación OCR ya generados** contra un archivo de texto real por imagen.

### 6.1 Prerrequisitos

1. Haber ejecutado `validate_ocr.py` con los motores OCR deseados.
2. Disponer de resultados en:
   - `validation_results/<layout_config>/results_easyocr.json`
   - `validation_results/<layout_config>/results_tesseract.json`
   - `validation_results/<layout_config>/results_paddle.json`
   - `validation_results/<layout_config>/results_deepseek.json` (si aplica)
3. Crear el archivo de ground truth:
   - `ground_truth/ocr_ground_truth.json`

### 6.2 Script de comparación (nuevo flujo)

**Nuevo archivo**: `compare_validation_vs_ground_truth.py`

**Entrada**:

1. `validation_results/` completo (todas las configuraciones y motores OCR)
2. `ground_truth/ocr_ground_truth.json`

**Salida**:

1. `ocr_gt_comparison_report.csv`
2. `ocr_gt_comparison_report.json`
3. `ocr_gt_comparison_report.txt`

### 6.3 Lógica de comparación

```
Para cada configuración de layout en validation_results/:
    Para cada motor OCR disponible (results_*.json):
        Para cada imagen del dataset:
            1. Reconstruir texto OCR (concatenación per_region en orden)
            2. Cargar texto real desde ground_truth/ocr_ground_truth.json
            3. Calcular CER y WER
            4. Guardar métricas por imagen
        5. Agregar métricas globales por (layout_config, ocr_engine)
6. Rankear combinaciones por menor CER/WER
```

### 6.4 Métricas obligatorias

| Métrica             | Descripción                                              | Objetivo |
| ------------------- | -------------------------------------------------------- | -------- |
| `CER`               | Character Error Rate vs ground truth                     | Menor    |
| `WER`               | Word Error Rate vs ground truth                          | Menor    |
| `time_per_image_ms` | Tiempo promedio por imagen (de resultados de validación) | Menor    |
| `dup_mean`          | Duplicados medios de detección (layout)                  | Menor    |

**Score global recomendado**:

```
score = (1 - CER) * 50 + (1 - WER) * 35 - (time_per_image_ms / 1000) * 10 - dup_mean * 5
```

### 6.5 Tabla de salida esperada

```
====================================================================================================
COMPARATIVA OCR VS GROUND TRUTH
====================================================================================================
    Layout Config                      OCR Engine   CER      WER      Time/img(ms)   Dups    SCORE
    ---------------------------------  ----------   ------   ------   ------------   ----    -----
    doclayout_conf0.20_nms0.40_mg15    easyocr      0.082    0.141          820       0.3     79.4
    doclayout_conf0.20_nms0.40_mg15    tesseract    0.097    0.169          640       0.3     74.8
    paddleocr_nms0.40_mg10             paddle       0.089    0.152          710       0.5     77.2
    opencv_mg10                        deepseek      0.061    0.118         1450       1.1     81.6
====================================================================================================
Ganador: [layout_config + ocr_engine] con menor CER/WER y mejor score global
```

### 6.6 Selección final del stack completo

Al concluir esta fase se selecciona:

1. Configuración de layout ganadora
2. Motor OCR ganador
3. Configuración reproducible final en `README.md`

Pipeline final:

```
Imagen de documento
        ↓
[Layout config ganador]
        ↓
[OCR engine ganador]
        ↓
Texto final validado contra ground truth
```

---

## TIMELINE

### Día 1 - ✅ FASE 1 COMPLETADA

- [x] FASE 1 - Post-procesamiento completo
  - [x] Crear `post_processing.py`
  - [x] Integrar en `detect_columns.py`
  - [x] Pruebas iniciales pendientes
- [x] FASE 2.1 — PaddleOCR y Surya ❌ Descartados (primera ronda)
  - ❌ PaddleOCR v1: Bug oneDNN en Windows (causa raíz identificada, fix conocido)
  - ❌ Surya: Devuelve bbox genérico — no funciona con imágenes escaneadas

### Día 2 — ✅ FASE 2.2 COMPLETADA

- [x] FASE 2.2.1 — YOLO11 fine-tuned ✅
  - [x] Instalar `ultralytics 8.2.103` + `huggingface_hub 0.36.2`
  - [x] Implementar `detect_columns_yolo11()`
  - [x] Probar en imgs/popurri01.jpg → 1–19+ regiones ✅
- [x] FASE 2.2.2 — PaddleOCR retry ✅
  - [x] Instalar `paddlepaddle 3.2.2` + `paddleocr[doc-parser]`
  - [x] Implementar `detect_columns_paddleocr()` con `LayoutDetection(enable_mkldnn=False)`
  - [x] Probar en imgs/popurri01.jpg → **16 regiones** ✅
- [x] FASE 2.2.3 — Docling ✅
  - [x] Instalar `docling` (modelos RT-DETR descargados automáticamente)
  - [x] Implementar `detect_columns_docling()` con corrección BOTTOMLEFT→TOPLEFT
  - [x] Probar en imgs/popurri01.jpg → **15 regiones** ✅

### Día 3 — ✅ FASE 2.2 (cont.) completada

- [x] FASE 2.2.4 — LayoutParser ❌ (evaluado y descartado — bug `?dl=1` insalvable en Windows)
- [x] Actualizar `EXPERIMENT_GRID` con métodos viables ✅
  - [x] Añadidos: `yolo11`, `paddleocr`, `docling` · Descartados: `surya`, `layoutparser`

### Día 5

- [x] FASE 3.1 - Crear `experiment_models.py` ✅
  - Script de grid search con todos los métodos viables de FASE 2.2
  - API correcta: `detect_columns(img: np.ndarray, ...)`, desempaquetado `_size, boxes = ...`
    - Grid: doclayout/yolo11 (128), paddleocr/docling (32), opencv (4) = 164 configs
  - Checkpoint por método + `--resume` para reanudar
- [x] FASE 3.3 - Crear `analyze_experiments.py` ✅
  - Aplanado manual de JSON, groupby con `dropna=False` para paddleocr/docling (conf=NaN)
  - Genera `experiment_ranking.csv` + `experiment_top.txt`
  - Fórmula: `score = mean_boxes*2.0 - total_duplicates*10.0`

### Día 6 — ✅ COMPLETADO

- [x] FASE 3.2 - Ejecutar grid search
    - Correr `py -3.11 experiment_models.py` (≈2952 experimentos)
    - Monitorear progreso con checkpoints por método
- [x] FASE 3.3 - Análisis
    - Correr `py -3.11 analyze_experiments.py`
    - Seleccionar top 3 configuraciones por método

### Día 7

- [ ] FASE 4 - Validación OCR
    - Ejecutar OCR con top 10 configs
  - Comparación automática
- [ ] FASE 4 - Revisión manual
  - Inspección de resultados
  - Scoring final

### Día 8

- [ ] FASE 5 — Crear ground truth
  - Crear `ground_truth/ocr_ground_truth.json` con texto real por imagen
  - Validar cobertura mínima (ideal 18/18 imágenes; mínimo 5 representativas)
- [ ] FASE 5 — Criterio de decisión final
  - Definir score final basado en CER/WER
  - Preparar plantilla de informe final

### Día 9

- [ ] FASE 6 — Comparación vs ground truth
  - Crear `compare_validation_vs_ground_truth.py`
  - Procesar todos los `results_*.json` de `validation_results/`
  - Calcular CER/WER por imagen y por combinación (layout + OCR)
- [ ] FASE 6 — Informe final y selección
  - Generar `ocr_gt_comparison_report.txt/csv/json`
  - Seleccionar stack final (layout + OCR)
  - Actualizar `README.md` con configuración ganadora

- Día 1: FASE 1 ✅
- Días 2–3: FASE 2.2 ✅
- Días 4–5: FASE 3.1 + scripts ✅
- Día 6: FASE 3.2–3.3 ✅ (grid search + análisis)
- Día 7: FASE 4 (validación OCR layout, top 10)
- Día 8: FASE 5 (ground truth + criterio final)
- Día 9: FASE 6 (comparación vs ground truth)

---

## ARCHIVOS A CREAR/MODIFICAR

### Nuevos archivos

- [x] `post_processing.py` - Módulo de post-procesamiento ✅ COMPLETADO
- [x] `experiment_models.py` - Grid search automático ✅ COMPLETADO
- [x] `analyze_experiments.py` - Análisis de resultados ✅ COMPLETADO
- [x] `validate_ocr.py` - Validación OCR top-N configuraciones (FASE 4) ✅ COMPLETADO
- [x] `ground_truth/ocr_ground_truth.json` - Esqueleto inicial creado (FASE 5)
- [x] `compare_validation_vs_ground_truth.py` - Esqueleto inicial creado (FASE 6)
- [ ] `LAYOUT_DETECTION_EXPERIMENTS.md` - Documentación de experimentos

### Archivos a modificar

- [x] `detect_columns.py` - Post-processing integrado ✅ COMPLETADO
  - [x] Añadir `detect_columns_yolo11()` (FASE 2.2.1) ✅
  - [x] Añadir `detect_columns_paddleocr()` (FASE 2.2.2) ✅
  - [x] Añadir `detect_columns_docling()` (FASE 2.2.3) ✅
- [ ] `benchmark_methods.py` - Añadir nuevos métodos al benchmark
- [x] `requirements.txt` - Actualizado con dependencias de métodos viables ✅
- [ ] `README.md` - Actualizar con nuevos métodos y resultados

---

## MÉTRICAS DE ÉXITO

### Objetivos cuantitativos — Layout Detection (FASES 1–5)

- [ ] Reducir duplicaciones en >80% vs baseline DocLayout 0.25
- [ ] Mantener cobertura >95% (no perder texto vs ground truth)
- [ ] Tiempo de procesamiento <2x vs método más rápido

### Objetivos cuantitativos — OCR Benchmark (FASE 6)

- [ ] Ground truth disponible para 18 imágenes (o mínimo 5 representativas)
- [ ] Motor/stack ganador con `WER < 15%` y `CER < 8%`
- [ ] Diferencia clara (> 3 puntos de score final) entre el ganador y el segundo
- [ ] Tiempo medio por imagen dentro de umbral operativo acordado

### Objetivos cualitativos

- [ ] Texto extraído coherente (orden correcto)
- [ ] Mínimas intervenciones manuales necesarias
- [ ] Configuración reproducible y documentada
- [ ] Pipeline completo documentado: modelo layout + motor OCR óptimos

---

## CONTINGENCIAS

### Si grid search toma demasiado tiempo

- Reducir espacio de búsqueda: 3 valores por parámetro en vez de 4-7
- Usar subset de imágenes (6 en vez de 18) para búsqueda inicial
- Paralelizar con multiprocessing

### Si ningún modelo alcanza score >75

- Considerar enfoque híbrido: reglas para seleccionar modelo según características de imagen
- Evaluar fine-tuning de DocLayout-YOLO en dataset específico
- Implementar sistema de voting (combinar detecciones de múltiples modelos)

### Si hay limitaciones de GPU/RAM

- Procesar en batches más pequeños
- Usar versiones "light" de modelos (ejemplo: DocLayout-Base en vez de Large)
- Ejecutar en Google Colab con GPU T4 gratuita

---

## NOTAS ADICIONALES

### Consideraciones técnicas

- Todos los experimentos deben usar misma versión de dependencias
- Guardar configuración exacta (versions, random seeds si aplica)
- Usar imágenes originales sin pre-procesamiento para comparación justa

### Validación estadística

- Si diferencias entre top configs son <5%, considerar empate técnico
- En caso de empate, preferir modelo más simple/rápido

### Aprendizajes esperados

- Identificar qué parámetros tienen mayor impacto
- Entender trade-offs entre modelos
- Crear framework reutilizable para futuros experimentos

```

```
