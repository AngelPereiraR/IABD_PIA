"""detect_columns.py

Carga una imagen, devuelve su tamano original y detecta columnas de texto
retornando una lista de coordenadas (x1, y1, x2, y2) en pixeles.

Metodos disponibles:
  - opencv:        Analisis de proyeccion vertical (sin modelos DL)
  - doclayout/yolo: DocLayout-YOLO (YOLOv10) entrenado en DocStructBench
  - yolo11:        YOLO11 fine-tuned en DocLayNet (Armaggheddon/HuggingFace)
  - paddleocr:     PaddleOCR PP-StructureV3 (con fix enable_mkldnn=False)
  - docling:       IBM Docling con modelo RT-DETR (docling-layout-heron)

Dependencias opcionales:
  pip install doclayout-yolo
  pip install ultralytics huggingface_hub
  pip install paddlepaddle==3.2.2 "paddleocr[doc-parser]"
  pip install docling
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Any

import os
import cv2
import numpy as np
from PIL import Image

# Import utilidad para gestión de carpetas de salida
from output_utils import get_output_dir
from PIL import Image

# Import módulo de post-procesamiento
import post_processing as pp

# Importar DocLayout-YOLO si está disponible
try:
    from doclayout_yolo import YOLOv10
    DOCLAYOUT_AVAILABLE = True
except ImportError:
    DOCLAYOUT_AVAILABLE = False
    YOLOv10 = None

# Importar YOLO11 (Ultralytics) si está disponible
try:
    from ultralytics import YOLO as UltralyticsYOLO
    YOLO11_AVAILABLE = True
except ImportError:
    YOLO11_AVAILABLE = False
    UltralyticsYOLO = None

# Deshabilitar la comprobación de conectividad al servidor de modelos de Paddle.
# Debe establecerse ANTES de cualquier import de paddleocr/paddlepaddle.
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Importar PaddleOCR si está disponible
try:
    from paddleocr import LayoutDetection as PaddleOCREngine
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    PaddleOCREngine = None

# Importar Docling si está disponible
try:
    from docling.document_converter import DocumentConverter as DoclingConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DoclingConverter = None

# Variables globales para caché de modelos (carga única por sesión)
_yolo11_models: dict = {}
_paddleocr_model: Optional[Any] = None
_docling_converter: Optional[Any] = None

# ============================================================================
# Constantes para DocLayout-YOLO
# ============================================================================
# Mapeo de índices de clase a nombres
DOCLAYOUT_CLASSES = {
    0: "text",       # Párrafos de texto (COLUMNAS)
    1: "title",      # Títulos y encabezados
    2: "figure",     # Imágenes y figuras decorativas
    3: "table",      # Tablas
    4: "caption",    # Pies de figura/tabla
    5: "header",     # Encabezados de página
    6: "footer",     # Pies de página
    7: "reference",  # Referencias bibliográficas
    8: "equation",   # Ecuaciones matemáticas
}

# Clases que representan texto (usadas para extracción de columnas)
TEXT_CLASSES = {0, 1, 5, 7}  # text, title, header, reference

# Colores de visualización (BGR) para cada clase
CLASS_COLORS = {
    0: (0, 255, 0),      # text -> verde
    1: (255, 0, 255),    # title -> magenta
    2: (0, 0, 255),      # figure -> rojo
    3: (255, 255, 0),    # table -> cyan
    4: (0, 165, 255),    # caption -> naranja
    5: (128, 0, 128),    # header -> púrpura
    6: (128, 128, 128),  # footer -> gris
    7: (255, 255, 255),  # reference -> blanco
    8: (0, 255, 255),    # equation -> amarillo
}

# ============================================================================
# Constantes para YOLO11 fine-tuned (DocLayNet, 11 clases)
# ============================================================================
YOLO11_CLASSES = {
    0: "Text",
    1: "Title",
    2: "Section-header",
    3: "Table",
    4: "Picture",
    5: "Caption",
    6: "List-item",
    7: "Formula",
    8: "Page-header",
    9: "Page-footer",
    10: "Footnote",
}
# Clases que representan texto (para filtrado de columnas)
YOLO11_TEXT_LABELS = {"Text", "Title", "Section-header", "Caption", "List-item", "Footnote"}

YOLO11_CLASS_COLORS = {
    "Text": (0, 200, 0),
    "Title": (255, 0, 255),
    "Section-header": (255, 128, 0),
    "List-item": (0, 200, 200),
    "Caption": (200, 0, 200),
    "Footnote": (128, 128, 0),
    "Table": (255, 255, 0),
    "Picture": (0, 0, 255),
    "Formula": (0, 255, 255),
    "Page-header": (128, 0, 128),
    "Page-footer": (128, 128, 128),
}

# URLs de modelos YOLO11 en HuggingFace
YOLO11_MODEL_FILES = {
    "nano":   "yolo11n_doc_layout.pt",
    "small":  "yolo11s_doc_layout.pt",
    "medium": "yolo11m_doc_layout.pt",
}
YOLO11_HF_REPO = "Armaggheddon/yolo11-document-layout"

# ============================================================================
# Constantes para PaddleOCR PP-StructureV3
# ============================================================================
PADDLEOCR_TEXT_LABELS = {
    "text", "paragraph", "title", "header",
    "figure_caption", "table_caption", "doc_title",
    "paragraph_title", "reference"
}

# ============================================================================
# Constantes para Docling (DocItemLabel)
# ============================================================================
DOCLING_TEXT_LABELS = {
    "TEXT", "TITLE", "SECTION_HEADER", "CAPTION",
    "LIST_ITEM", "FOOTNOTE", "DOCUMENT_INDEX"
}


@dataclass
class ColumnBox:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float = 0.0
    label: str = ""

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)


def load_image(path: str) -> np.ndarray:
    # Load with OpenCV (BGR)
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {path}")
    return img


def detect_columns_opencv(img: np.ndarray, debug: bool = False, image_path: str = None, method: str = "opencv") -> Tuple[Tuple[int, int], List[ColumnBox]]:
    """Detecta columnas en la imagen usando OpenCV y retorna (width,height) y lista de ColumnBox.

    Heurísticas:
    - Convertir a gris y aplicar umbral adaptativo para resaltar texto.
    - Aplicar morfología (closing) con kernel vertical para unir líneas de texto
      y horizontal para limpiar pequeñas separaciones.
    - Buscar contornos grandes y estrechos (columnas) y devolver sus bounding boxes.
    """
    h, w = img.shape[:2]

    # Convertir directamente a blanco y negro (binaria) usando la componente de luminancia
    # Evitamos hacer CLAHE/blur intermedios y produciomos una imagen B/W mediante umbral adaptativo.
    luma = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(luma, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 51, 9)

    # Morfología para unir líneas de una columna verticalmente
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, max(10, h // 100)))
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(10, w // 40), 3))

    # Close vertical to connect text lines into blocks
    closed = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, vert_kernel, iterations=2)
    # Then close horizontally to bridge small gaps inside column
    closed = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, hor_kernel, iterations=1)

    # ---- Proyección vertical para encontrar separadores entre columnas ----
    # Usaremos la imagen binarizada original (bw) donde el texto es blanco (255)
    bin_img = (bw > 0).astype(np.uint8)  # 0/1

    # Conteo de píxeles de texto por columna
    col_counts = bin_img.sum(axis=0)  # shape: (w,)
    # Normalizar por altura
    col_frac = col_counts / float(h)

    # Umbral para considerar un px vertical como separador (muy pocos píxeles de texto)
    # Hacer menos agresivo (más permisivo): reducir el umbral para permitir más texto
    sep_thresh = max(0.005, 0.001 * (h / 2000.0))  # adaptativo según altura

    separators = col_frac < sep_thresh

    # Encontrar runs de columnas (zonas entre separadores)
    spans: List[Tuple[int, int]] = []
    in_span = False
    span_start = 0
    for x in range(w):
        if not separators[x]:
            if not in_span:
                in_span = True
                span_start = x
        else:
            if in_span:
                spans.append((span_start, x - 1))
                in_span = False
    if in_span:
        spans.append((span_start, w - 1))

    # Filtrar spans estrechos
    # Permitir columnas más estrechas: reducir la fracción del ancho mínima
    min_col_width = max(32, int(w * 0.092))
    spans = [s for s in spans if (s[1] - s[0] + 1) >= min_col_width]

    boxes: List[ColumnBox] = []
    # Si no hay spans detectados, fallback a 3 columnas iguales
    if not spans:
        third = w // 3
        spans = [(i * third, (i + 1) * third - 1 if i < 2 else w - 1) for i in range(3)]

    # Si sólo hay un span grande, intentar dividirlo por valles en la proyección vertical
    if len(spans) == 1:
        left, right = spans[0]
        span_width = right - left + 1
        # Sólo intentar si el span ocupa gran parte del ancho (posible fusión)
        if span_width > 0.7 * w:
            # Extraer la fracción de texto dentro del span y suavizar
            seg_frac = col_frac[left:right + 1]
            # Suavizado simple para reducir ruido
            kernel = np.ones(5) / 5.0
            smooth = np.convolve(seg_frac, kernel, mode='same')

            # Buscar mínimos locales en smooth
            minima = []
            for i in range(1, len(smooth) - 1):
                if smooth[i] < smooth[i - 1] and smooth[i] < smooth[i + 1]:
                    minima.append((smooth[i], i))

            # Ordenar por profundidad (valor) ascendente -> valles más profundos primero
            minima.sort(key=lambda x: x[0])

            chosen = []
            # elegir hasta 2 valles (para dividir en hasta 3 columnas)
            for val, idx in minima:
                # convertir índice local a coordenada global
                x = left + idx
                # asegurarse de que no quede demasiado cerca de los bordes ni de otros cortes
                if x - left < min_col_width or right - x < min_col_width:
                    continue
                if any(abs(x - c) < min_col_width for c in chosen):
                    continue
                # considerar profundidad relativa: menos estricto
                if val < np.median(seg_frac) * 0.9:
                    chosen.append(x)
                if len(chosen) >= 2:
                    break

            if chosen:
                # construir nuevos spans dividiendo por chosen (orden ascendente)
                chosen = sorted(chosen)
                new_spans = []
                cur_l = left
                for c in chosen:
                    new_spans.append((cur_l, c - 1))
                    cur_l = c
                new_spans.append((cur_l, right))
                # Reemplazar spans si los nuevos tienen ancho suficiente
                new_spans = [s for s in new_spans if (s[1] - s[0] + 1) >= max(10, int(w * 0.03))]
                if len(new_spans) > 1:
                    spans = new_spans

    # Para cada span, ajustar límites verticales por proyección horizontal dentro del span
    for left, right in spans:
        # recortar la porción binaria
        seg = bin_img[:, left:right + 1]
        # densidad de texto dentro del span (fracción de píxeles de texto)
        span_text_pixels = seg.sum()
        span_area = seg.shape[0] * seg.shape[1]
        span_density = float(span_text_pixels) / float(max(1, span_area))
        # descartar spans con muy poca densidad (menos agresivo)
        if span_density < 0.0003:  # umbral menos agresivo
            continue
        row_counts = seg.sum(axis=1) / float(max(1, (right - left + 1)))
        # Umbral para filas que contienen texto (menos agresivo)
        row_thresh = max(0.001, 0.005 * (w / 2000.0))
        rows = np.where(row_counts > row_thresh)[0]
        if rows.size:
            top = int(max(0, rows[0] - 3))
            bottom = int(min(h - 1, rows[-1] + 3))
        else:
            top = 0
            bottom = h - 1

        # Sin padding: usar los límites exactos de la columna.
        # x2/y2 se calculan como índices de fin exclusivos para slicing (right+1, bottom+1).
        x1 = max(0, left)
        y1 = max(0, top)
        x2 = min(w, right + 1)
        y2 = min(h, bottom + 1)

        # calcular confianza: combinar ancho relativa y densidad
        width_rel = (x2 - x1) / float(w)
        # normalizar density al rango [0,1] con saturación razonable
        density_norm = min(1.0, span_density / 0.02)
        confidence = float(0.6 * density_norm + 0.4 * min(1.0, width_rel / 0.2))

        boxes.append(ColumnBox(int(x1), int(y1), int(x2), int(y2), confidence))

    # Ordenar izquierda a derecha por seguridad
    boxes.sort(key=lambda b: b.x1)

    # Guardar una copia 'raw' de las cajas detectadas antes del agrupado por confianza
    raw_boxes: List[ColumnBox] = [ColumnBox(b.x1, b.y1, b.x2, b.y2, b.confidence) for b in boxes]
    if debug:
        # Generar carpeta de salida si se proporciona image_path
        if image_path and method:
            output_dir = get_output_dir(image_path, method)
            raw_debug_path = str(output_dir / "debug_columns_raw.png")
        else:
            raw_debug_path = "debug_columns_raw.png"
        
        vis_raw = img.copy()
        for i, b in enumerate(raw_boxes, start=1):
            cv2.rectangle(vis_raw, (b.x1, b.y1), (b.x2, b.y2), (255, 0, 0), 2)
            cv2.putText(vis_raw, f"raw {i} ({b.confidence:.2f})", (b.x1 + 5, b.y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.imwrite(raw_debug_path, vis_raw)
        print(f"Raw debug image saved to: {raw_debug_path}")

    # Agrupar columnas con baja confianza: si la confianza de una columna
    # no es mayor que MIN_CONF, agruparla a la anterior que sí lo sea. Si no hay
    # anterior con >MIN_CONF, agrupar hacia adelante hasta encontrar la siguiente
    # que lo sea. Si no existe ninguna con >MIN_CONF, agrupar todo en una sola caja.
    MIN_CONF = 0.99
    merged: List[ColumnBox] = []
    n = len(boxes)
    i = 0
    if n == 0:
        boxes = merged
    else:
        while i < n:
            b = boxes[i]
            # caja suficientemente confiable -> conservar como base
            if b.confidence > MIN_CONF:
                merged.append(ColumnBox(b.x1, b.y1, b.x2, b.y2, b.confidence))
                i += 1
                continue

            # intentar buscar una anterior confiable en merged
            prev_high_idx = None
            for idx in range(len(merged) - 1, -1, -1):
                if merged[idx].confidence > MIN_CONF:
                    prev_high_idx = idx
                    break

            if prev_high_idx is not None:
                # fusionar con la anterior confiable
                r = merged[prev_high_idx]
                r.x1 = min(r.x1, b.x1)
                r.y1 = min(r.y1, b.y1)
                r.x2 = max(r.x2, b.x2)
                r.y2 = max(r.y2, b.y2)
                r.confidence = max(r.confidence, b.confidence)
                i += 1
                continue

            # no hay anterior confiable: buscar la siguiente confiable hacia adelante
            next_high = None
            for k in range(i + 1, n):
                if boxes[k].confidence > MIN_CONF:
                    next_high = k
                    break

            if next_high is not None:
                # fusionar desde i hasta next_high (inclusive) en una sola caja
                seg = boxes[i: next_high + 1]
                x1 = min(s.x1 for s in seg)
                y1 = min(s.y1 for s in seg)
                x2 = max(s.x2 for s in seg)
                y2 = max(s.y2 for s in seg)
                conf = max(s.confidence for s in seg)
                merged.append(ColumnBox(x1, y1, x2, y2, conf))
                i = next_high + 1
                continue

            # no hay ninguna columna con >MIN_CONF en adelante tampoco
            if merged:
                # fusionar el resto en la última caja ya creada
                last = merged[-1]
                while i < n:
                    s = boxes[i]
                    last.x1 = min(last.x1, s.x1)
                    last.y1 = min(last.y1, s.y1)
                    last.x2 = max(last.x2, s.x2)
                    last.y2 = max(last.y2, s.y2)
                    last.confidence = max(last.confidence, s.confidence)
                    i += 1
            else:
                # no hay merged previo y no hay futuras >MIN_CONF: fusionar todo en una
                x1 = min(s.x1 for s in boxes[i:])
                y1 = min(s.y1 for s in boxes[i:])
                x2 = max(s.x2 for s in boxes[i:])
                y2 = max(s.y2 for s in boxes[i:])
                conf = max(s.confidence for s in boxes[i:])
                merged.append(ColumnBox(x1, y1, x2, y2, conf))
                break

        boxes = merged

    if debug:
        vis = img.copy()
        # Dibujar proyección vertical (normalizada) en la parte inferior de la imagen
        proj = col_frac.copy()
        # normalizar para visualización
        proj_norm = (proj - proj.min()) / float(max(1e-6, proj.max() - proj.min()))
        ph = min(100, h // 6)
        # crear overlay
        overlay = vis.copy()
        for x in range(w):
            val = int(proj_norm[x] * ph)
            cv2.line(overlay, (x, h - 1), (x, h - 1 - val), (200, 200, 0), 1)
        # mezclar overlay para suavizar la visibilidad
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, vis, 1 - alpha, 0, vis)

        for i, b in enumerate(boxes, start=1):
            cv2.rectangle(vis, (b.x1, b.y1), (b.x2, b.y2), (0, 255, 0), 2)
            text = f"{i} ({b.confidence:.2f})"
            cv2.putText(vis, text, (b.x1 + 5, b.y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        # Save debug image using output_dir if available
        if image_path and method:
            output_dir = get_output_dir(image_path, method)
            debug_path = str(output_dir / "debug_columns_opencv.png")
        else:
            debug_path = "debug_columns_opencv.png"
        cv2.imwrite(debug_path, vis)
        print(f"Debug image (OpenCV) saved to: {debug_path}")

    return (w, h), boxes


def detect_columns_doclayout(
    img: np.ndarray,
    model_path: Optional[str] = None,
    conf_threshold: float = 0.25,
    all_classes: bool = False,
    nms_iou: float = 0.5,
    merge_distance: int = 10,
    min_area: int = 100,
    enable_nms: bool = True,
    enable_merge: bool = True,
    enable_filter: bool = True,
    debug: bool = False,
    image_path: str = None,
    method: str = "doclayout"
) -> Tuple[Tuple[int, int], List[ColumnBox]]:
    """Detecta columnas de texto usando el modelo DocLayout-YOLO.
    
    Args:
        img: Imagen BGR de OpenCV (numpy array)
        model_path: Ruta al archivo .pt del modelo. Si es None, usa la ruta por defecto.
        conf_threshold: Umbral de confianza para las detecciones (0-1)
        all_classes: Si True, detecta todas las 9 clases. Si False, sólo clases de texto.
        nms_iou: Umbral IoU para Non-Maximum Suppression (default: 0.5)
        merge_distance: Distancia en píxeles para fusionar cajas cercanas (default: 10)
        min_area: Área mínima en píxeles para filtrar ruido (default: 100)
        enable_nms: Activar NMS (default: True)
        enable_merge: Activar fusión de cajas cercanas (default: True)
        enable_filter: Activar filtrado de ruido (default: True)
        debug: Si True, guarda una imagen de depuración con las cajas dibujadas.
        image_path: Ruta de la imagen (para generar carpeta de salida)
        method: Método usado (para generar carpeta de salida)
    
    Returns:
        Tupla ((width, height), List[ColumnBox])
    """
    if not DOCLAYOUT_AVAILABLE:
        raise ImportError(
            "DocLayout-YOLO no está disponible. Instala con: pip install doclayout-yolo\n"
            "También asegúrate de descargar el modelo con: python download_doclayout_model.py"
        )
    
    h, w = img.shape[:2]
    
    # Determinar ruta del modelo
    if model_path is None:
        default_model = Path("models/doclayout_yolo/doclayout_yolo_docstructbench_imgsz1024.pt")
        if not default_model.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en: {default_model}\n"
                "Descárgalo con: python download_doclayout_model.py"
            )
        model_path = str(default_model)
    
    # Cargar modelo
    print(f"Cargando modelo DocLayout-YOLO desde: {model_path}")
    model = YOLOv10(model_path)
    
    # Realizar inferencia
    print(f"Ejecutando inferencia con umbral de confianza: {conf_threshold}")
    results = model.predict(img, conf=conf_threshold, device='cuda:0' if cv2.cuda.getCudaEnabledDeviceCount() > 0 else 'cpu')
    
    # Procesar resultados
    boxes: List[ColumnBox] = []
    scores: List[float] = []
    
    if len(results) > 0:
        result = results[0]
        
        # Obtener cajas, confianzas y clases
        if hasattr(result, 'boxes') and result.boxes is not None:
            for box in result.boxes:
                # Coordenadas (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                
                # Filtrar por clase si no se solicitan todas
                if not all_classes and class_id not in TEXT_CLASSES:
                    continue
                
                # Crear ColumnBox
                boxes.append(ColumnBox(
                    int(x1), int(y1), int(x2), int(y2),
                    confidence=confidence
                ))
                scores.append(confidence)
    
    # Aplicar post-procesamiento si está habilitado
    if len(boxes) > 0 and (enable_nms or enable_merge or enable_filter):
        if debug:
            print(f"\nAplicando post-procesamiento...")
            print(f"Boxes antes: {len(boxes)}")
        
        # Convertir ColumnBox a tuplas para post-procesamiento
        boxes_tuples = [(b.x1, b.y1, b.x2, b.y2, b.confidence) for b in boxes]
        
        # Aplicar pipeline de post-procesamiento
        processed = pp.process_detections(
            boxes_tuples,
            scores,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
            debug=debug
        )
        
        # Convertir de vuelta a ColumnBox
        boxes = [ColumnBox(int(b[0]), int(b[1]), int(b[2]), int(b[3]), 
                          confidence=b[4] if len(b) > 4 else 1.0) 
                 for b in processed]
        
        if debug:
            print(f"Boxes después: {len(boxes)}")
    
    # Ordenar de izquierda a derecha
    boxes.sort(key=lambda b: b.x1)
    
    # Guardar imagen de depuración si se solicita
    if debug:
        vis = img.copy()
        
        if len(results) > 0 and hasattr(results[0], 'boxes') and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = DOCLAYOUT_CLASSES.get(class_id, "unknown")
                
                # Color según la clase
                color = CLASS_COLORS.get(class_id, (255, 255, 255))
                
                # Dibujar rectángulo
                cv2.rectangle(vis, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Texto con clase y confianza
                text = f"{class_name} ({confidence:.2f})"
                cv2.putText(vis, text, (int(x1) + 5, int(y1) + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Guardar imagen de depuración usando output_dir si está disponible
        if image_path and method:
            output_dir = get_output_dir(image_path, method)
            debug_path = str(output_dir / "debug_columns_doclayout.png")
        else:
            debug_path = "debug_columns_doclayout.png"
        cv2.imwrite(debug_path, vis)
        print(f"Debug image (DocLayout-YOLO) saved to: {debug_path}")
    
    print(f"DocLayout-YOLO detectó {len(boxes)} región(es) de texto")
    return (w, h), boxes


# ============================================================================
# YOLO11 fine-tuned en DocLayNet (Armaggheddon/yolo11-document-layout)
# ============================================================================

def detect_columns_yolo11(
    img: np.ndarray,
    conf_threshold: float = 0.25,
    model_size: str = "nano",
    all_classes: bool = False,
    nms_iou: float = 0.5,
    merge_distance: int = 10,
    min_area: int = 100,
    enable_nms: bool = True,
    enable_merge: bool = True,
    enable_filter: bool = True,
    debug: bool = False,
    image_path: str = None,
    method: str = "yolo11",
) -> Tuple[Tuple[int, int], List[ColumnBox]]:
    """Detecta regiones usando YOLO11 fine-tuned en DocLayNet (11 clases).

    El modelo se descarga automáticamente de HuggingFace la primera vez
    (Armaggheddon/yolo11-document-layout).  Se cachea en ~/.cache/huggingface/.

    Args:
        img: Imagen BGR (OpenCV).
        conf_threshold: Umbral de confianza (0-1). Default: 0.25.
        model_size: "nano" | "small" | "medium". Default: "nano".
        all_classes: Si True, devuelve todas las clases (no sólo texto).
        nms_iou/merge_distance/min_area/enable_*: parámetros de post-processing.
        debug: Guardar imagen de depuración.
        image_path: Ruta de la imagen original (para la carpeta de salida).
        method: Nombre del método (para la carpeta de salida).

    Returns:
        Tupla ((width, height), List[ColumnBox]) ordenada de izquierda a derecha.
    """
    if not YOLO11_AVAILABLE:
        raise ImportError(
            "ultralytics no está instalado. "
            "Instálalo con: pip install ultralytics huggingface_hub"
        )

    global _yolo11_models
    h, w = img.shape[:2]

    # Cargar modelo (cacheado por tamaño)
    if model_size not in _yolo11_models:
        model_filename = YOLO11_MODEL_FILES.get(model_size, "yolo11n_doc_layout.pt")
        try:
            from huggingface_hub import hf_hub_download
            model_path = hf_hub_download(
                repo_id=YOLO11_HF_REPO,
                filename=model_filename,
            )
        except Exception as e:
            raise RuntimeError(
                f"No se pudo descargar el modelo YOLO11 '{model_filename}' "
                f"desde HuggingFace ({YOLO11_HF_REPO}): {e}"
            ) from e
        print(f"[YOLO11] Cargando modelo {model_size} desde: {model_path}")
        _yolo11_models[model_size] = UltralyticsYOLO(model_path)

    model = _yolo11_models[model_size]

    # Inferencia (imgsz=1280 recomendado por el autor del modelo)
    results = model.predict(img, imgsz=1280, conf=conf_threshold, verbose=False)

    raw_results = []   # Lista[ColumnBox] antes de post-processing
    raw_scores = []    # Lista[float] para pp.process_detections

    if results and len(results) > 0:
        result = results[0]
        boxes_tensor = result.boxes

        for i in range(len(boxes_tensor)):
            xyxy = boxes_tensor.xyxy[i].cpu().numpy()
            conf = float(boxes_tensor.conf[i].cpu().numpy())
            cls_id = int(boxes_tensor.cls[i].cpu().numpy())
            class_name = YOLO11_CLASSES.get(cls_id, "Unknown")

            # Filtrar por tipo de clase
            if not all_classes and class_name not in YOLO11_TEXT_LABELS:
                continue

            x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 > x1 and y2 > y1:
                raw_results.append(ColumnBox(x1, y1, x2, y2, confidence=conf, label=class_name))
                raw_scores.append(conf)

    # Post-processing (NMS, merge, filter)
    if raw_results:
        boxes_tuples = [(b.x1, b.y1, b.x2, b.y2) for b in raw_results]
        processed = pp.process_detections(
            boxes=boxes_tuples,
            scores=raw_scores,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
        )
        # Reconstruir ColumnBox desde los índices originales devueltos
        idx_map = {(b.x1, b.y1, b.x2, b.y2): b for b in raw_results}
        boxes: List[ColumnBox] = []
        for bx in processed:
            orig = idx_map.get(tuple(bx), None)
            label = orig.label if orig else "Text"
            conf = orig.confidence if orig else 0.0
            boxes.append(ColumnBox(bx[0], bx[1], bx[2], bx[3], confidence=conf, label=label))
    else:
        boxes = []

    boxes.sort(key=lambda b: b.x1)

    # Imagen de depuración
    if debug:
        vis = img.copy()
        # Todas las cajas brutas (antes de post-processing) en gris
        for b in raw_results:
            cv2.rectangle(vis, (b.x1, b.y1), (b.x2, b.y2), (180, 180, 180), 1)
        # Cajas finales con color por clase
        for b in boxes:
            color = YOLO11_CLASS_COLORS.get(b.label, (0, 200, 0))
            cv2.rectangle(vis, (b.x1, b.y1), (b.x2, b.y2), color, 2)
            label_text = f"{b.label} ({b.confidence:.2f})"
            cv2.putText(vis, label_text, (b.x1 + 4, b.y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        if image_path and method:
            output_dir = get_output_dir(image_path, method)
            debug_path = str(output_dir / "debug_columns_yolo11.png")
        else:
            debug_path = "debug_columns_yolo11.png"
        cv2.imwrite(debug_path, vis)
        print(f"Debug image (YOLO11) guardada en: {debug_path}")

    print(f"YOLO11 detectó {len(boxes)} región(es) de texto (raw: {len(raw_results)})")
    return (w, h), boxes


# ============================================================================
# PaddleOCR PP-StructureV3 (fix enable_mkldnn=False)
# ============================================================================

def detect_columns_paddleocr(
    img: np.ndarray,
    all_classes: bool = False,
    nms_iou: float = 0.5,
    merge_distance: int = 10,
    min_area: int = 100,
    enable_nms: bool = True,
    enable_merge: bool = True,
    enable_filter: bool = True,
    debug: bool = False,
    image_path: str = None,
    method: str = "paddleocr",
) -> Tuple[Tuple[int, int], List[ColumnBox]]:
    """Detecta regiones usando PaddleOCR PP-StructureV3.

    Requiere paddlepaddle==3.2.2 y paddleocr[doc-parser] para evitar el bug
    oneDNN de PaddlePaddle >= 3.3.0.  El flag enable_mkldnn=False es el fix clave.

    Args:
        img: Imagen BGR (OpenCV).
        all_classes: Si True, devuelve todas las clases de layout detectadas.
        nms_iou/merge_distance/min_area/enable_*: parámetros de post-processing.
        debug: Guardar imagen de depuración.
        image_path: Ruta de la imagen original.
        method: Nombre del método (para la carpeta de salida).

    Returns:
        Tupla ((width, height), List[ColumnBox]) ordenada de izquierda a derecha.
    """
    if not PADDLEOCR_AVAILABLE:
        raise ImportError(
            "paddleocr no está instalado. Instala con:\n"
            "  pip install paddlepaddle==3.2.2\n"
            "  pip install \"paddleocr[doc-parser]\""
        )

    global _paddleocr_model
    h, w = img.shape[:2]

    # Cargar modelo (cacheado) - usa LayoutDetection (PP-DocLayout_plus-L)
    if _paddleocr_model is None:
        print("[PaddleOCR] Inicializando LayoutDetection / PP-DocLayout (enable_mkldnn=False)...")
        _paddleocr_model = PaddleOCREngine(enable_mkldnn=False)

    # predict() devuelve un generador de DetResult (subclase de dict)
    # Estructura: result["res"] = {"boxes": [{"cls_id":N, "label":"text",
    #                              "score":0.9, "coordinate":[x1,y1,x2,y2]}, ...]}
    try:
        result_list = list(_paddleocr_model.predict(img))
    except Exception as e:
        print(f"[PaddleOCR] Error en predict(): {e}")
        return (w, h), []

    raw_results: List[ColumnBox] = []
    raw_scores: List[float] = []

    for det_result in (result_list or []):
        # DetResult hereda de dict pero almacena datos en .json["res"]
        # det_result["res"] lanza KeyError; la ruta correcta es .json["res"]
        try:
            j = det_result.json if hasattr(det_result, "json") else det_result
            res_data = j.get("res", {}) if isinstance(j, dict) else {}
        except Exception:
            continue

        boxes_raw = res_data.get("boxes", []) if isinstance(res_data, dict) else []

        for item in boxes_raw:
            label = str(item.get("label", "")).lower()
            score = float(item.get("score", 1.0))
            coord = item.get("coordinate", None)   # [x1, y1, x2, y2]

            if coord is None:
                continue

            if not all_classes and label not in {ll.lower() for ll in PADDLEOCR_TEXT_LABELS}:
                continue

            x1, y1, x2, y2 = int(coord[0]), int(coord[1]), int(coord[2]), int(coord[3])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 > x1 and y2 > y1:
                raw_results.append(ColumnBox(x1, y1, x2, y2, confidence=score, label=label))
                raw_scores.append(score)

    # Post-processing
    if raw_results:
        boxes_tuples = [(b.x1, b.y1, b.x2, b.y2) for b in raw_results]
        processed = pp.process_detections(
            boxes=boxes_tuples,
            scores=raw_scores,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
        )
        idx_map = {(b.x1, b.y1, b.x2, b.y2): b for b in raw_results}
        boxes: List[ColumnBox] = []
        for bx in processed:
            orig = idx_map.get(tuple(bx), None)
            label_str = orig.label if orig else "text"
            conf = orig.confidence if orig else 0.0
            boxes.append(ColumnBox(bx[0], bx[1], bx[2], bx[3], confidence=conf, label=label_str))
    else:
        boxes = []

    boxes.sort(key=lambda b: b.x1)

    # Imagen de depuración
    if debug:
        vis = img.copy()
        for b in raw_results:
            cv2.rectangle(vis, (b.x1, b.y1), (b.x2, b.y2), (180, 180, 180), 1)
        for b in boxes:
            cv2.rectangle(vis, (b.x1, b.y1), (b.x2, b.y2), (0, 200, 50), 2)
            cv2.putText(vis, f"{b.label} ({b.confidence:.2f})",
                        (b.x1 + 4, b.y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 50), 2)

        if image_path and method:
            output_dir = get_output_dir(image_path, method)
            debug_path = str(output_dir / "debug_columns_paddleocr.png")
        else:
            debug_path = "debug_columns_paddleocr.png"
        cv2.imwrite(debug_path, vis)
        print(f"Debug image (PaddleOCR) guardada en: {debug_path}")

    print(f"PaddleOCR detectó {len(boxes)} región(es) de texto (raw: {len(raw_results)})")
    return (w, h), boxes


# ============================================================================
# Docling (IBM) con RT-DETR / docling-layout-heron
# ============================================================================

def detect_columns_docling(
    img: np.ndarray,
    all_classes: bool = False,
    nms_iou: float = 0.5,
    merge_distance: int = 10,
    min_area: int = 100,
    enable_nms: bool = True,
    enable_merge: bool = True,
    enable_filter: bool = True,
    debug: bool = False,
    image_path: str = None,
    method: str = "docling",
) -> Tuple[Tuple[int, int], List[ColumnBox]]:
    """Detecta regiones usando IBM Docling (RT-DETR / docling-layout-heron).

    Docling requiere una ruta de archivo como entrada.  Si se pasa image_path,
    se usa directamente; de lo contrario se guarda en un fichero temporal.

    El bbox de Docling está normalizado en el rango 0-1 (l, t, r, b).

    Args:
        img: Imagen BGR (OpenCV).
        all_classes: Si True, devuelve todos los elementos DocItemLabel.
        debug: Guardar imagen de depuración.
        image_path: Ruta de la imagen original (preferido para evitar E/S temporal).
        method: Nombre del método (para la carpeta de salida).

    Returns:
        Tupla ((width, height), List[ColumnBox]) ordenada de izquierda a derecha.
    """
    if not DOCLING_AVAILABLE:
        raise ImportError(
            "docling no está instalado. Instálalo con: pip install docling"
        )

    global _docling_converter
    h, w = img.shape[:2]

    # Cargar conversor (cacheado)
    if _docling_converter is None:
        print("[Docling] Inicializando DocumentConverter (primera vez puede tardar ~30s)...")
        _docling_converter = DoclingConverter()

    # Ruta de entrada para Docling
    import tempfile
    _tmp_path = None
    if image_path:
        input_path = image_path
    else:
        # Guardar imagen en fichero temporal
        suffix = ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            _tmp_path = tmp.name
        cv2.imwrite(_tmp_path, img)
        input_path = _tmp_path

    try:
        doc_result = _docling_converter.convert(input_path)
        document = doc_result.document
    except Exception as e:
        print(f"[Docling] Error convertiendo imagen: {e}")
        return (w, h), []
    finally:
        if _tmp_path:
            try:
                import os as _os_tmp
                _os_tmp.unlink(_tmp_path)
            except OSError:
                pass

    raw_results: List[ColumnBox] = []
    raw_scores: List[float] = []

    # Iterar elementos del documento
    for item, _level in document.iterate_items():
        # Filtrar por tipo (DocItemLabel)
        label_name = ""
        if hasattr(item, "label"):
            lbl = item.label
            # lbl.value es minúscula ("text"), lo convertimos a mayúscula para DOCLING_TEXT_LABELS
            label_name = (lbl.value if hasattr(lbl, "value") else str(lbl)).upper()

        if not all_classes and label_name not in DOCLING_TEXT_LABELS:
            continue

        # Iterar todas las entradas prov (un item puede abarcar varias cajas)
        for prov_item in (item.prov or []):
            bbox = getattr(prov_item, "bbox", None)
            if bbox is None:
                continue

            # Las coordenas son píxeles ABSOLUTOS con origen BOTTOMLEFT
            # Convertir a TOP-LEFT: y_top = H - t,  y_bot = H - b  (t > b en BOTTOMLEFT)
            try:
                # to_top_left_origin() lo hace automáticamente si está disponible
                if hasattr(bbox, "to_top_left_origin"):
                    bbox_tl = bbox.to_top_left_origin(h)
                    l_px, t_px, r_px, b_px = bbox_tl.l, bbox_tl.t, bbox_tl.r, bbox_tl.b
                else:
                    l_px = float(bbox.l)
                    r_px = float(bbox.r)
                    # BOTTOMLEFT: t > b (t más lejano del origen = más arriba visualmente)
                    t_px = h - float(bbox.t)   # top en coordenadas imagen
                    b_px = h - float(bbox.b)   # bottom en coordenadas imagen
            except AttributeError:
                continue

            x1 = int(min(l_px, r_px))
            x2 = int(max(l_px, r_px))
            y1 = int(min(t_px, b_px))
            y2 = int(max(t_px, b_px))

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 > x1 and y2 > y1:
                raw_results.append(ColumnBox(x1, y1, x2, y2, confidence=1.0, label=label_name))
                raw_scores.append(1.0)

    # Post-processing
    if raw_results:
        boxes_tuples = [(b.x1, b.y1, b.x2, b.y2) for b in raw_results]
        processed = pp.process_detections(
            boxes=boxes_tuples,
            scores=raw_scores,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
        )
        idx_map = {(b.x1, b.y1, b.x2, b.y2): b for b in raw_results}
        boxes: List[ColumnBox] = []
        for bx in processed:
            orig = idx_map.get(tuple(bx), None)
            label_str = orig.label if orig else "TEXT"
            boxes.append(ColumnBox(bx[0], bx[1], bx[2], bx[3], confidence=1.0, label=label_str))
    else:
        boxes = []

    boxes.sort(key=lambda b: b.x1)

    # Imagen de depuración
    if debug:
        vis = img.copy()
        for b in raw_results:
            cv2.rectangle(vis, (b.x1, b.y1), (b.x2, b.y2), (180, 180, 180), 1)
        for b in boxes:
            cv2.rectangle(vis, (b.x1, b.y1), (b.x2, b.y2), (255, 128, 0), 2)
            cv2.putText(vis, b.label,
                        (b.x1 + 4, b.y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 128, 0), 2)

        if image_path and method:
            output_dir = get_output_dir(image_path, method)
            debug_path = str(output_dir / "debug_columns_docling.png")
        else:
            debug_path = "debug_columns_docling.png"
        cv2.imwrite(debug_path, vis)
        print(f"Debug image (Docling) guardada en: {debug_path}")

    print(f"Docling detectó {len(boxes)} región(es) de texto (raw: {len(raw_results)})")
    return (w, h), boxes


# ============================================================================
# Wrapper principal
# ============================================================================

def detect_columns(
    img: np.ndarray,
    method: str = "opencv",
    debug: bool = False,
    doclayout_conf: float = 0.25,
    doclayout_all_classes: bool = False,
    nms_iou: float = 0.5,
    merge_distance: int = 10,
    min_area: int = 100,
    enable_nms: bool = True,
    enable_merge: bool = True,
    enable_filter: bool = True,
    model_path: Optional[str] = None,
    image_path: str = None,
    # Nuevos parámetros FASE 2.2
    yolo11_conf: float = 0.25,
    yolo11_size: str = "nano",
) -> Tuple[Tuple[int, int], List[ColumnBox]]:
    """Detecta columnas usando el método especificado.
    
    Args:
        img: Imagen BGR de OpenCV
        method: Metodo a usar: "opencv", "doclayout"/"yolo", "yolo11",
                "paddleocr", "docling"
        debug: Generar imagen de depuración
        doclayout_conf: Umbral de confianza para DocLayout-YOLO
        doclayout_all_classes: Detectar todas las clases con DocLayout-YOLO
        nms_iou: Umbral IoU para NMS (post-processing)
        merge_distance: Distancia para fusionar cajas (post-processing)
        min_area: Área mínima para filtrado (post-processing)
        enable_nms/merge/filter: Activar etapas de post-processing
        model_path: Ruta personalizada al modelo DocLayout-YOLO
        image_path: Ruta de la imagen (para generar carpeta de salida)
        yolo11_conf: Umbral de confianza para YOLO11 (default 0.25)
        yolo11_size: Tamaño del modelo YOLO11 ("nano"/"small"/"medium")
    
    Returns:
        Tupla ((width, height), List[ColumnBox])
    """
    method = method.lower()
    
    if method in ("doclayout", "yolo"):
        return detect_columns_doclayout(
            img,
            model_path=model_path,
            conf_threshold=doclayout_conf,
            all_classes=doclayout_all_classes,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
            debug=debug,
            image_path=image_path,
            method=method
        )
    elif method == "yolo11":
        return detect_columns_yolo11(
            img,
            conf_threshold=yolo11_conf,
            model_size=yolo11_size,
            all_classes=doclayout_all_classes,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
            debug=debug,
            image_path=image_path,
            method=method
        )
    elif method == "paddleocr":
        return detect_columns_paddleocr(
            img,
            all_classes=doclayout_all_classes,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
            debug=debug,
            image_path=image_path,
            method=method
        )
    elif method == "docling":
        return detect_columns_docling(
            img,
            all_classes=doclayout_all_classes,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=enable_nms,
            enable_merge=enable_merge,
            enable_filter=enable_filter,
            debug=debug,
            image_path=image_path,
            method=method
        )
    elif method == "opencv":
        return detect_columns_opencv(img, debug=debug, image_path=image_path, method=method)
    else:
        raise ValueError(
            f"Método desconocido: '{method}'. "
            "Usa: 'opencv', 'doclayout', 'yolo', 'yolo11', 'paddleocr', 'docling'"
        )


def pil_save_utfpath(img: np.ndarray, path: str) -> None:
    # Helper to save using PIL to support unicode paths on Windows
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img_rgb)
    pil.save(path)


def process_single_image(
    image_path: str,
    method: str,
    debug: bool,
    doclayout_conf: float,
    doclayout_all_classes: bool,
    nms_iou: float = 0.5,
    merge_distance: int = 10,
    min_area: int = 100,
    disable_nms: bool = False,
    disable_merge: bool = False,
    disable_filter: bool = False,
    model_path: str = None,
    # Nuevos parámetros FASE 2.2
    yolo11_conf: float = 0.25,
    yolo11_size: str = "nano",
) -> None:
    """Procesa una sola imagen."""
    img = load_image(image_path)
    
    # Generar carpeta de salida
    output_dir = get_output_dir(image_path, method)
    print(f"\nCarpeta de salida: {output_dir}")
    
    (w, h), boxes = detect_columns(
        img,
        method=method,
        debug=debug,
        doclayout_conf=doclayout_conf,
        doclayout_all_classes=doclayout_all_classes,
        nms_iou=nms_iou,
        merge_distance=merge_distance,
        min_area=min_area,
        enable_nms=not disable_nms,
        enable_merge=not disable_merge,
        enable_filter=not disable_filter,
        model_path=model_path,
        image_path=image_path,
        yolo11_conf=yolo11_conf,
        yolo11_size=yolo11_size,
    )

    print(f"\nTamaño original: width={w}, height={h}")
    print(f"Método usado: {method.upper()}")
    print(f"Columnas detectadas (x1,y1,x2,y2) en píxeles, ordenadas L->R:")
    for i, b in enumerate(boxes, start=1):
        info = b.as_tuple()
        conf = getattr(b, 'confidence', 0.0)
        print(f"{i}: {info} confidence={conf:.3f}")
        # Guardar cada columna como imagen separada
        col_img = img[b.y1:b.y2, b.x1:b.x2]
        out_name = str(output_dir / f"column_{i}.png")
        pil_save_utfpath(col_img, out_name)
        print(f"  -> saved: {out_name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Detecta columnas de texto en documentos usando múltiples métodos:\n"
            "  opencv, doclayout/yolo, yolo11, paddleocr, docling"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  OpenCV (método manual):
    python detect_columns.py --image popurri01.jpg --method opencv --debug

  DocLayout-YOLO:
    python detect_columns.py --image imgs/ --method doclayout --debug

  YOLO11 fine-tuned (DocLayNet, modelo nano):
    python detect_columns.py --image popurri01.jpg --method yolo11 --yolo11-size nano --debug

  PaddleOCR PP-StructureV3:
    python detect_columns.py --image popurri01.jpg --method paddleocr --debug

  Docling (IBM, RT-DETR):
    python detect_columns.py --image popurri01.jpg --method docling --debug
        """
    )
    parser.add_argument("--image", "-i", required=True, help="Ruta a la imagen o carpeta de imágenes")
    parser.add_argument(
        "--method", "-m",
        default="opencv",
        choices=["opencv", "doclayout", "yolo", "yolo11", "paddleocr", "docling"],
        help="Método de detección (default: opencv)"
    )
    parser.add_argument("--debug", action="store_true", help="Guardar imagen de depuración con cajas")
    parser.add_argument(
        "--doclayout-conf",
        type=float,
        default=0.25,
        help="Umbral de confianza para DocLayout-YOLO (0-1). Default: 0.25"
    )
    parser.add_argument(
        "--all-classes",
        action="store_true",
        help="Detectar todas las clases (no sólo texto) para métodos basados en YOLO/DL"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Ruta personalizada al modelo DocLayout-YOLO (.pt)"
    )

    # Argumentos de post-procesamiento
    parser.add_argument("--nms-iou", type=float, default=0.5,
                        help="Umbral IoU para NMS (default: 0.5)")
    parser.add_argument("--merge-distance", type=int, default=10,
                        help="Distancia en píxeles para fusionar cajas cercanas (default: 10)")
    parser.add_argument("--min-area", type=int, default=100,
                        help="Área mínima en píxeles para filtrar ruido (default: 100)")
    parser.add_argument("--disable-nms", action="store_true",
                        help="Desactivar Non-Maximum Suppression")
    parser.add_argument("--disable-merge", action="store_true",
                        help="Desactivar fusión de cajas cercanas")
    parser.add_argument("--disable-filter", action="store_true",
                        help="Desactivar filtrado de ruido")

    # === Argumentos FASE 2.2 ===
    parser.add_argument(
        "--yolo11-conf",
        type=float,
        default=0.25,
        help="Umbral de confianza para YOLO11 (default: 0.25)"
    )
    parser.add_argument(
        "--yolo11-size",
        type=str,
        default="nano",
        choices=["nano", "small", "medium"],
        help="Tamaño del modelo YOLO11: nano/small/medium (default: nano)"
    )

    args = parser.parse_args()

    # Determinar si es archivo o carpeta
    from pathlib import Path
    target = Path(args.image)
    image_paths = []
    
    if target.is_dir():
        exts = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp')
        for fname in sorted(target.iterdir()):
            if fname.suffix.lower() in exts:
                image_paths.append(str(fname))
        if not image_paths:
            print(f"No se encontraron imágenes en la carpeta: {target}")
            raise SystemExit(1)
    elif target.is_file():
        image_paths = [str(target)]
    else:
        print(f"La ruta proporcionada no es un archivo ni una carpeta válida: {target}")
        raise SystemExit(1)

    # Procesar cada imagen
    for img_path in image_paths:
        print(f"\n{'='*80}")
        print(f"Procesando: {Path(img_path).name}")
        print(f"{'='*80}")
        
        process_single_image(
            img_path,
            method=args.method,
            debug=args.debug,
            doclayout_conf=args.doclayout_conf,
            doclayout_all_classes=args.all_classes,
            nms_iou=args.nms_iou,
            merge_distance=args.merge_distance,
            min_area=args.min_area,
            disable_nms=args.disable_nms,
            disable_merge=args.disable_merge,
            disable_filter=args.disable_filter,
            model_path=args.model_path,
            yolo11_conf=args.yolo11_conf,
            yolo11_size=args.yolo11_size,
        )


if __name__ == "__main__":
    main()