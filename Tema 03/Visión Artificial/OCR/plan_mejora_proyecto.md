# Plan Detallado: Optimización de Detección de Layout con YOLO y Modelos Alternativos

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

## FASE 1: Implementación de Post-Procesamiento (4-6 horas)

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

## FASE 2: Integración de Modelos Alternativos (4-6 horas)

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

**Estimación:** ~2–3 horas

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

## FASE 3: Experimentación Sistemática con Grid Search (8-12 horas)

### 3.1 Crear script `experiment_models.py`

**Objetivo**: Probar todas las combinaciones de [modelos × parámetros] sobre las 18 imágenes.

**Espacio de búsqueda** (ampliar con métodos que pasen las pruebas de FASE 2.2):

```python
EXPERIMENT_GRID = {
    # ✅ Actualizado tras FASE 2.2: yolo11, paddleocr y docling son viables
    # ❌ layoutparser descartado (bug Windows ?dl=1 insalvable)
    # ❌ surya descartado (1 bbox genérico en imágenes escaneadas)
    'methods': ['doclayout', 'yolo11', 'paddleocr', 'docling'],
    'conf_thresholds': [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
    'nms_iou': [0.3, 0.4, 0.5, 0.6],
    'merge_distance': [5, 10, 15, 20],
}
```

**Total configuraciones** (estimado actualizado):

- DocLayout: 7 conf × 4 nms × 4 merge = 112 configs
- YOLO11: 7 conf × 4 nms × 4 merge = 112 configs
- PaddleOCR: 4 nms × 4 merge = 16 configs (sin conf_threshold)
- Docling: 4 nms × 4 merge = 16 configs (sin conf_threshold)
- ~~Surya: DESCARTADO~~ · ~~LayoutParser: DESCARTADO (Windows bug)~~
- **Total**: ~256 configuraciones × 18 imágenes = **~4,608 experimentos**

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
                # Para métodos adicionales (actualmente ninguno - Surya y PaddleOCR descartados)
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
# Ejecutar grid search (puede tomar 2-4 horas)
py -3.11 experiment_models.py

# Analizar resultados
py -3.11 analyze_experiments.py
```

---

## FASE 4: Validación con OCR Completo (4-6 horas)

### 4.1 Seleccionar top 3 configuraciones

Según ranking de `analyze_experiments.py`, seleccionar las 3 mejores configuraciones.

**Candidatos esperados** (según resultados de FASE 2.2):

1. `paddleocr` — 16 regiones en popurri01.jpg
2. `docling` — 15 regiones en popurri01.jpg
3. `doclayout` con `conf=0.2, nms_iou=0.4, merge_distance=15`
4. `yolo11` con `--all-classes --yolo11-conf 0.1`

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
        'validation_results/surya_025',
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

## FASE 5: Decisión Final y Deployment (2-3 horas)

### 5.1 Scoring final

**Criterios de evaluación** (pesos):

1. **Calidad OCR** (40%): Más palabras/caracteres extraídos sin duplicaciones
2. **No duplicaciones** (25%): Mínimas duplicaciones en detección
3. **Cobertura** (20%): No perder regiones de texto
4. **Velocidad** (10%): Tiempo de procesamiento
5. **Mantenibilidad** (5%): Complejidad de dependencias

**Matriz de decisión** (por rellenar tras grid search):

| Configuración | OCR Quality | No Dups | Coverage | Speed | Maintain | **TOTAL** |
| ------------- | ----------- | ------- | -------- | ----- | -------- | --------- |
| PaddleOCR     | ?/40        | ?/25    | ?/20     | ?/10  | ?/5      | ?/100     |
| Docling       | ?/40        | ?/25    | ?/20     | ?/10  | ?/5      | ?/100     |
| DocLayout+PP  | ?/40        | ?/25    | ?/20     | ?/10  | ?/5      | ?/100     |
| YOLO11        | ?/40        | ?/25    | ?/20     | ?/10  | ?/5      | ?/100     |

### 5.2 Decisión

**Si score ganador > 85**: Usar esa configuración como default

**Si score ganador 75-85**: Usar ganador pero documentar limitaciones

**Si todos < 75**: Considerar enfoque híbrido (ejemplo: Surya para layouts complejos, DocLayout para simples)

### 5.3 Actualizar defaults en `detect_columns.py`

```python
# Ejemplo: si gana PaddleOCR
DEFAULT_METHOD = 'paddleocr'

# O si gana Docling
DEFAULT_METHOD = 'docling'

# O si gana DocLayout mejorado
DEFAULT_METHOD = 'doclayout'
DEFAULT_CONF = 0.2
DEFAULT_NMS_IOU = 0.4
DEFAULT_MERGE_DISTANCE = 15
```

### 5.4 Documentación

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
6. ~~LayoutParser EfficientDet~~ (DESCARTADO: bug `?dl=1` insalvable en Windows)

## Resultados

### Grid Search

- Total experimentos: 2,268
- Configuraciones probadas: 126
- Duración: X horas

### Top 3 Configuraciones

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

## Próximos Pasos

- [ ] Evaluar en dataset de producción
- [ ] Medir métricas de negocio (si aplica)
- [ ] Considerar fine-tuning si score < 80

```

---

## TIMELINE ESTIMADO

### Día 1 (8 horas) - ✅ FASE 1 COMPLETADA
- [x] **Mañana (4h)**: FASE 1 - Post-procesamiento completo
  - [x] Crear `post_processing.py`
  - [x] Integrar en `detect_columns.py`
  - [x] Pruebas iniciales pendientes
- [x] **Tarde (4h)**: FASE 2.1 — PaddleOCR y Surya ❌ Descartados (primera ronda)
  - ❌ PaddleOCR v1: Bug oneDNN en Windows (causa raíz identificada, fix conocido)
  - ❌ Surya: Devuelve bbox genérico — no funciona con imágenes escaneadas

### Día 2 (9 horas) — ✅ FASE 2.2 COMPLETADA
- [x] **Mañana (2h)**: FASE 2.2.1 — YOLO11 fine-tuned ✅
  - [x] Instalar `ultralytics 8.2.103` + `huggingface_hub 0.36.2`
  - [x] Implementar `detect_columns_yolo11()`
  - [x] Probar en imgs/popurri01.jpg → 1–19+ regiones ✅
- [x] **Media mañana (3h)**: FASE 2.2.2 — PaddleOCR retry ✅
  - [x] Instalar `paddlepaddle 3.2.2` + `paddleocr[doc-parser]`
  - [x] Implementar `detect_columns_paddleocr()` con `LayoutDetection(enable_mkldnn=False)`
  - [x] Probar en imgs/popurri01.jpg → **16 regiones** ✅
- [x] **Tarde (4h)**: FASE 2.2.3 — Docling ✅
  - [x] Instalar `docling` (modelos RT-DETR descargados automáticamente)
  - [x] Implementar `detect_columns_docling()` con corrección BOTTOMLEFT→TOPLEFT
  - [x] Probar en imgs/popurri01.jpg → **15 regiones** ✅

### Día 3 (4 horas) — ✅ FASE 2.2 (cont.) completada
- [x] **Mañana (3h)**: FASE 2.2.4 — LayoutParser ❌ (evaluado y descartado — bug `?dl=1` insalvable en Windows)
- [x] **Tarde (1h)**: Actualizar `EXPERIMENT_GRID` con métodos viables ✅
  - [x] Añadidos: `yolo11`, `paddleocr`, `docling` · Descartados: `surya`, `layoutparser`

### Día 5 (4 horas)
- [x] **Tarde (4h)**: FASE 3.1 - Crear `experiment_models.py` ✅
  - Script de grid search con todos los métodos viables de FASE 2.2
  - API correcta: `detect_columns(img: np.ndarray, ...)`, desempaquetado `_size, boxes = ...`
  - Grid: doclayout/yolo11 (conf×nms×merge=112), paddleocr/docling (nms×merge=16) = 256 configs
  - Checkpoint por método + `--resume` para reanudar
- [x] **Tarde (1h)**: FASE 3.3 - Crear `analyze_experiments.py` ✅
  - Aplanado manual de JSON, groupby con `dropna=False` para paddleocr/docling (conf=NaN)
  - Genera `experiment_ranking.csv` + `experiment_top.txt`
  - Fórmula: `score = mean_boxes*2.0 - total_duplicates*10.0`

### Día 6 (8 horas)
- [ ] **Mañana (4h)**: FASE 3.2 - Ejecutar grid search
  - Correr `py -3.11 experiment_models.py` (≈4608 experimentos, ~2-3h)
  - Monitorear progreso con checkpoints por método
- [ ] **Tarde (2h)**: FASE 3.3 - Análisis
  - Correr `py -3.11 analyze_experiments.py`
  - Seleccionar top 3 configuraciones por método

### Día 7 (8 horas)
- [ ] **Mañana (4h)**: FASE 4 - Validación OCR
  - Ejecutar OCR con top 3 configs
  - Comparación automática
- [ ] **Tarde (4h)**: FASE 4 - Revisión manual
  - Inspección de resultados
  - Scoring final

### Día 8 (4 horas)
- [ ] **Mañana (3h)**: FASE 5 - Decisión y deployment
  - Actualizar defaults
  - Documentación
- [ ] **Tarde (1h)**: Limpieza y entrega
  - Commit cambios
  - README actualizado

**Total estimado**: ~57 horas (~7 días laborables)
- Día 1 (8h): FASE 1 ✅
- Día 2 (9h): FASE 2.2 — YOLO11 + PaddleOCR + Docling
- Día 3 (4h): FASE 2.2 — LayoutParser evaluado (descartado) + consolidación
- Día 4 (4h): Inicio FASE 3
- Días 5–8: FASE 3, 4, 5

---

## ARCHIVOS A CREAR/MODIFICAR

### Nuevos archivos
- [x] `post_processing.py` - Módulo de post-procesamiento ✅ COMPLETADO
- [x] `experiment_models.py` - Grid search automático ✅ COMPLETADO
- [x] `analyze_experiments.py` - Análisis de resultados ✅ COMPLETADO
- [ ] `compare_ocr_quality.py` - Comparación de outputs OCR
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

### Objetivos cuantitativos
- [ ] Reducir duplicaciones en >80% vs baseline DocLayout 0.25
- [ ] Mantener cobertura >95% (no perder texto vs ground truth)
- [ ] Tiempo de procesamiento <2x vs método más rápido

### Objetivos cualitativos
- [ ] Texto extraído coherente (orden correcto)
- [ ] Mínimas intervenciones manuales necesarias
- [ ] Configuración reproducible y documentada

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
