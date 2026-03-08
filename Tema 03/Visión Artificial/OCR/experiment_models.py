"""experiment_models.py

Grid search sistemático sobre todos los métodos de detección de layout.

Espacio de búsqueda:
  - doclayout / yolo11 : conf_threshold × nms_iou × merge_distance
  - paddleocr / docling: nms_iou × merge_distance
                         (sin conf configurable — hardcodeado a 0.3 en el modelo)
  - opencv             : merge_distance
                         (sin conf ni nms_iou — proyección de histograma de columnas)

Uso:
    py -3.11 experiment_models.py
    py -3.11 experiment_models.py --methods doclayout yolo11
    py -3.11 experiment_models.py --resume
    py -3.11 experiment_models.py --images-dir imgs --output results.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import cv2
import numpy as np

# Ajustar sys.path para importar desde la misma carpeta
sys.path.insert(0, str(Path(__file__).parent))

from detect_columns import detect_columns, ColumnBox
import post_processing as pp
from output_utils import get_output_dir

# ============================================================================
# Grid de experimentos
# ============================================================================

EXPERIMENT_GRID: Dict[str, Any] = {
    # ✅ Métodos viables tras FASE 2.2 + opencv como referencia base (sin modelo DL)
    "methods": ["doclayout", "yolo11", "paddleocr", "docling", "opencv"],
    "conf_thresholds": [0.1, 0.2, 0.3, 0.4],
    "nms_iou": [0.3, 0.4, 0.5, 0.6],
    "merge_distance": [5, 10, 15, 20],
}

# Métodos con umbral de confianza configurable
METHODS_WITH_CONF = {"doclayout", "yolo11"}

# Métodos sin umbral de confianza (fijado internamente a 0.3 en LayoutPredictor)
METHODS_WITHOUT_CONF = {"paddleocr", "docling"}

# Métodos sin conf_threshold ni nms_iou — solo merge_distance varía
METHODS_ONLY_MERGE = {"opencv"}

# Rutas por defecto
IMAGES_DIR = Path(__file__).parent / "imgs"
DEFAULT_OUTPUT = Path(__file__).parent / "experiment_results.json"

MIN_EMPTY_FOREGROUND_PIXELS = 48
MIN_EMPTY_FOREGROUND_RATIO = 0.003
TINY_BOX_IMAGE_RATIO = 0.002
MIN_COMPONENT_AREA_RATIO = 0.00015
MIN_COMPONENT_DENSITY = 0.01
MAX_COMPONENT_DENSITY = 0.55


# ============================================================================
# Helpers
# ============================================================================

def _box_area(box: ColumnBox) -> int:
    """Área en píxeles de una ColumnBox."""
    return (box.x2 - box.x1) * (box.y2 - box.y1)


def _count_duplicates(boxes: List[ColumnBox], iou_threshold: float = 0.7) -> int:
    """Cuenta pares de cajas con IoU > iou_threshold (posibles duplicados)."""
    count = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if pp.calculate_iou(boxes[i].as_tuple(), boxes[j].as_tuple()) > iou_threshold:
                count += 1
    return count


def _clip_box(box: ColumnBox, width: int, height: int) -> Tuple[int, int, int, int]:
    """Recorta una caja a los límites válidos de la imagen."""
    x1 = max(0, min(int(box.x1), width))
    y1 = max(0, min(int(box.y1), height))
    x2 = max(0, min(int(box.x2), width))
    y2 = max(0, min(int(box.y2), height))
    return x1, y1, x2, y2


def _build_text_block_mask(img: Any) -> Dict[str, Any]:
    """Extrae una máscara centrada en bloques de texto, no en cualquier tinta.

    Devuelve tanto la máscara de tinta original como una máscara refinada donde
    los componentes conectados intentan representar líneas/bloques textuales.
    """
    height, width = img.shape[:2]
    image_area = max(1, height * width)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, ink_mask = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    ink_mask = cv2.morphologyEx(
        ink_mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
    )

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(15, width // 60), 3),
    )
    line_mask = cv2.morphologyEx(ink_mask, cv2.MORPH_CLOSE, horizontal_kernel)

    block_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(5, width // 100), max(11, height // 90)),
    )
    block_mask = cv2.morphologyEx(line_mask, cv2.MORPH_CLOSE, block_kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(block_mask, connectivity=8)
    filtered = np.zeros_like(block_mask)
    min_component_area = max(32, int(image_area * MIN_COMPONENT_AREA_RATIO))
    min_component_width = max(12, width // 100)
    min_component_height = max(12, height // 120)

    for label_id in range(1, num_labels):
        x, y, comp_width, comp_height, area = stats[label_id]
        if area < min_component_area:
            continue
        if comp_width < min_component_width or comp_height < min_component_height:
            continue

        bbox_area = max(1, comp_width * comp_height)
        ink_pixels = int((ink_mask[y:y + comp_height, x:x + comp_width] > 0).sum())
        density = ink_pixels / bbox_area
        if density < MIN_COMPONENT_DENSITY or density > MAX_COMPONENT_DENSITY:
            continue

        filtered[labels == label_id] = 255

    if not np.any(filtered):
        filtered = block_mask

    return {
        "ink_mask": ink_mask > 0,
        "text_block_mask": filtered > 0,
    }


def _config_debug_tag(method: str, config: Dict[str, Any]) -> str:
    """Genera una etiqueta legible para debug por experimento."""
    parts = [method]
    if "conf" in config:
        parts.append(f"conf{config['conf']:.2f}")
    if "nms_iou" in config:
        parts.append(f"nms{config['nms_iou']:.2f}")
    parts.append(f"mg{config['merge_distance']}")
    return "-".join(parts).replace(".", "_")


def _save_mask_debug(
    image_path: str,
    img: Any,
    ink_mask: Any,
    text_block_mask: Any,
    debug_dir: Optional[Path] = None,
) -> None:
    """Guarda máscaras y overlay para inspeccionar la heurística de texto."""
    base_dir = str(debug_dir) if debug_dir is not None else None
    out_dir = get_output_dir(image_path, "layout-mask-debug", base_dir=base_dir)

    ink_mask_u8 = (ink_mask.astype(np.uint8) * 255)
    text_block_u8 = (text_block_mask.astype(np.uint8) * 255)

    overlay = img.copy()
    overlay[text_block_mask] = (0.4 * overlay[text_block_mask] + 0.6 * np.array([0, 220, 0])).astype(np.uint8)

    cv2.imwrite(str(out_dir / "01_ink_mask.png"), ink_mask_u8)
    cv2.imwrite(str(out_dir / "02_text_block_mask.png"), text_block_u8)
    cv2.imwrite(str(out_dir / "03_text_block_overlay.png"), overlay)


def _save_boxes_debug(
    image_path: str,
    img: Any,
    boxes: List[ColumnBox],
    method: str,
    config: Dict[str, Any],
    debug_dir: Optional[Path] = None,
) -> None:
    """Guarda las cajas detectadas para un experimento concreto."""
    base_dir = str(debug_dir) if debug_dir is not None else None
    out_dir = get_output_dir(
        image_path,
        f"layout-boxes-{_config_debug_tag(method, config)}",
        base_dir=base_dir,
    )

    vis = img.copy()
    boxes_payload: List[Dict[str, int]] = []
    for index, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = int(box.x1), int(box.y1), int(box.x2), int(box.y2)
        boxes_payload.append({
            "index": index,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "width": max(0, x2 - x1),
            "height": max(0, y2 - y1),
        })
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(
            vis,
            str(index),
            (x1, max(18, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

    cv2.imwrite(str(out_dir / "01_boxes_overlay.png"), vis)
    with open(out_dir / "02_boxes.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "image": Path(image_path).name,
                "method": method,
                "config": config,
                "num_boxes": len(boxes_payload),
                "boxes": boxes_payload,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def _estimate_layout_quality(
    img: Any,
    boxes: List[ColumnBox],
    debug_mask: bool = False,
    image_path: Optional[str] = None,
    debug_dir: Optional[Path] = None,
) -> Dict[str, float]:
    """Aproxima cobertura textual, solapamiento y basura sin usar ground truth."""
    height, width = img.shape[:2]
    image_area = max(1, width * height)

    mask_data = _build_text_block_mask(img)
    ink_mask = mask_data["ink_mask"]
    text_block_mask = mask_data["text_block_mask"]
    total_foreground = int(text_block_mask.sum())

    if debug_mask and image_path:
        _save_mask_debug(image_path, img, ink_mask, text_block_mask, debug_dir=debug_dir)

    if not boxes:
        return {
            "text_coverage": 0.0,
            "overlap_ratio": 0.0,
            "empty_boxes": 0,
            "empty_ratio": 0.0,
            "tiny_boxes": 0,
            "tiny_ratio": 0.0,
        }

    coverage_count = np.zeros((height, width), dtype=np.uint16)
    empty_boxes = 0
    tiny_boxes = 0

    for box in boxes:
        x1, y1, x2, y2 = _clip_box(box, width, height)
        if x2 <= x1 or y2 <= y1:
            empty_boxes += 1
            continue

        coverage_count[y1:y2, x1:x2] += 1
        box_area = max(1, (x2 - x1) * (y2 - y1))
        foreground_pixels = int(text_block_mask[y1:y2, x1:x2].sum())
        foreground_ratio = foreground_pixels / box_area

        if foreground_pixels < MIN_EMPTY_FOREGROUND_PIXELS or foreground_ratio < MIN_EMPTY_FOREGROUND_RATIO:
            empty_boxes += 1

        if (box_area / image_area) < TINY_BOX_IMAGE_RATIO:
            tiny_boxes += 1

    if total_foreground > 0:
        covered_foreground = int((text_block_mask & (coverage_count > 0)).sum())
        overlap_foreground = int((text_block_mask & (coverage_count > 1)).sum())
        text_coverage = covered_foreground / total_foreground
        overlap_ratio = overlap_foreground / total_foreground
    else:
        text_coverage = 0.0
        overlap_ratio = 0.0

    box_count = max(1, len(boxes))
    return {
        "text_coverage": round(float(text_coverage), 6),
        "overlap_ratio": round(float(overlap_ratio), 6),
        "empty_boxes": int(empty_boxes),
        "empty_ratio": round(empty_boxes / box_count, 6),
        "tiny_boxes": int(tiny_boxes),
        "tiny_ratio": round(tiny_boxes / box_count, 6),
    }


# ============================================================================
# Ejecución de un único experimento
# ============================================================================

def run_single_experiment(
    img: Any,           # np.ndarray — tipado como Any para evitar import en bloque
    image_path: str,
    method: str,
    config: Dict[str, Any],
    debug_mask: bool = False,
    debug_boxes: bool = False,
    debug_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Ejecuta un único experimento y devuelve sus métricas.

    Returns:
        dict con claves: success, num_boxes, avg_area, duplicates, time_ms
                         y opcionalmente error (si success=False)
    """
    start = time.perf_counter()
    try:
        # Construir kwargs específicos por método
        # IMPORTANTE: detect_columns() recibe img:np.ndarray como primer argumento,
        # NO una ruta de archivo. Los nombres de parámetros de conf son distintos
        # según el método (doclayout_conf vs yolo11_conf).
        kwargs: Dict[str, Any] = dict(
            method=method,
            merge_distance=config["merge_distance"],
            debug=False,
            image_path=image_path,   # solo para nombrar la carpeta de debug si debug=True
        )
        if method == "doclayout":
            kwargs["doclayout_conf"] = config["conf"]
            kwargs["nms_iou"] = config["nms_iou"]
        elif method == "yolo11":
            kwargs["yolo11_conf"] = config["conf"]
            kwargs["nms_iou"] = config["nms_iou"]
        elif method in METHODS_WITHOUT_CONF:
            # paddleocr y docling: sin conf, hardcoded a 0.3 en LayoutPredictor
            kwargs["nms_iou"] = config["nms_iou"]
        # opencv: solo merge_distance — sin nms_iou ni conf_threshold

        # detect_columns devuelve ((width, height), List[ColumnBox])
        _size, boxes = detect_columns(img, **kwargs)

        elapsed_ms = (time.perf_counter() - start) * 1000
        num_boxes = len(boxes)
        avg_area = (
            sum(_box_area(b) for b in boxes) / num_boxes if num_boxes > 0 else 0.0
        )
        duplicates = _count_duplicates(boxes)
        if debug_boxes:
            _save_boxes_debug(
                image_path,
                img,
                boxes,
                method,
                config,
                debug_dir=debug_dir,
            )
        quality = _estimate_layout_quality(
            img,
            boxes,
            debug_mask=debug_mask,
            image_path=image_path,
            debug_dir=debug_dir,
        )

        return {
            "success": True,
            "num_boxes": num_boxes,
            "avg_area": round(avg_area, 1),
            "duplicates": duplicates,
            "time_ms": round(elapsed_ms, 1),
            **quality,
        }

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "num_boxes": 0,
            "avg_area": 0.0,
            "duplicates": 0,
            "time_ms": round(elapsed_ms, 1),
            "text_coverage": 0.0,
            "overlap_ratio": 0.0,
            "empty_boxes": 0,
            "empty_ratio": 0.0,
            "tiny_boxes": 0,
            "tiny_ratio": 0.0,
            "error": str(exc),
        }


# ============================================================================
# Generador de configuraciones
# ============================================================================

def iter_configs(
    methods: Optional[List[str]] = None,
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Genera tuplas (method, config_dict) para todo el grid.

    Para métodos con conf (doclayout, yolo11):
        config = {"conf": float, "nms_iou": float, "merge_distance": int}
    Para métodos sin conf (paddleocr, docling):
        config = {"nms_iou": float, "merge_distance": int}
    """
    methods = methods or EXPERIMENT_GRID["methods"]
    for method in methods:
        if method in METHODS_ONLY_MERGE:
            # opencv: sin conf_threshold ni nms_iou — solo merge_distance varía
            for merge in EXPERIMENT_GRID["merge_distance"]:
                yield method, {"merge_distance": merge}
            continue
        for nms in EXPERIMENT_GRID["nms_iou"]:
            for merge in EXPERIMENT_GRID["merge_distance"]:
                if method in METHODS_WITH_CONF:
                    for conf in EXPERIMENT_GRID["conf_thresholds"]:
                        yield method, {
                            "conf": conf,
                            "nms_iou": nms,
                            "merge_distance": merge,
                        }
                else:
                    yield method, {
                        "nms_iou": nms,
                        "merge_distance": merge,
                    }


def count_configs(methods: Optional[List[str]] = None) -> int:
    """Total de configuraciones (sin multiplicar por imágenes)."""
    return sum(1 for _ in iter_configs(methods))


# ============================================================================
# Grid search principal
# ============================================================================

def run_grid_search(
    images_dir: Path = IMAGES_DIR,
    output_file: Path = DEFAULT_OUTPUT,
    methods: Optional[List[str]] = None,
    resume: bool = False,
    debug_mask: bool = False,
    debug_boxes: bool = False,
    debug_dir: Optional[Path] = None,
) -> List[Dict]:
    """Ejecuta el grid search completo y guarda resultados en output_file.

    Args:
        images_dir: Carpeta con imágenes popurri*.jpg.
        output_file: Ruta del JSON de resultados.
        methods:    Subconjunto de métodos a probar (None = todos).
        resume:     Si True, carga resultados previos y salta experimentos ya hechos.

    Returns:
        Lista de dicts con todos los resultados.
    """
    images = sorted(images_dir.glob("popurri*.jpg"))
    if not images:
        print(f"[ERROR] No se encontraron imágenes popurri*.jpg en {images_dir}")
        return []

    # ── Reanudar desde sesión anterior ───────────────────────────────────────
    existing_results: List[Dict] = []
    done_keys: set = set()
    if resume and output_file.exists():
        with open(output_file, encoding="utf-8") as f:
            existing_results = json.load(f)
        done_keys = {
            (r["image"], r["method"], json.dumps(r["config"], sort_keys=True))
            for r in existing_results
        }
        print(f"[Resume] Saltando {len(done_keys)} experimentos ya completados.\n")

    n_configs = count_configs(methods)
    total = n_configs * len(images)
    print(f"Imágenes        : {len(images)}")
    print(f"Configuraciones : {n_configs}")
    print(f"Total experimentos: {total}")
    print()

    # ── Pre-cargar imágenes (evita I/O repetida en el loop) ──────────────────
    images_cache: Dict[str, Any] = {}
    for img_path in images:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"[WARN] No se pudo cargar {img_path.name}, se omite.")
        else:
            images_cache[img_path.name] = img

    results = list(existing_results)
    exp_id = len(existing_results)
    prev_method: Optional[str] = None
    debug_done_images: set[str] = set()

    for method, config in iter_configs(methods):
        # Checkpoint al terminar todos los experimentos de un método
        if prev_method is not None and method != prev_method:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  → Checkpoint guardado después de '{prev_method}' ({output_file.name})")
        prev_method = method

        for img_path in images:
            img_name = img_path.name
            key = (img_name, method, json.dumps(config, sort_keys=True))
            if key in done_keys:
                continue  # Ya procesado en sesión anterior

            exp_id += 1
            conf_str = f"conf={config['conf']:.2f}" if "conf" in config else "conf=N/A "
            nms_str  = f"nms={config['nms_iou']}" if "nms_iou" in config else "nms=N/A "
            print(
                f"[{exp_id:>5}/{total}] {method:12s} | {conf_str}  "
                f"{nms_str}  merge={config['merge_distance']:>2d} | {img_name}"
            )

            img = images_cache.get(img_name)
            if img is None:
                continue

            should_debug_mask = debug_mask and img_name not in debug_done_images
            metrics = run_single_experiment(
                img,
                str(img_path),
                method,
                config,
                debug_mask=should_debug_mask,
                debug_boxes=debug_boxes,
                debug_dir=debug_dir,
            )
            if should_debug_mask:
                debug_done_images.add(img_name)

            results.append({
                "experiment_id": exp_id,
                "image": img_name,
                "method": method,
                "config": config,
                "metrics": metrics,
            })

    # Checkpoint final
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Resumen rápido
    total_run = len(results)
    failed = sum(1 for r in results if not r["metrics"].get("success", False))
    print(f"\nFinalizados: {total_run}  |  Fallidos: {failed}")
    print(f"Resultados guardados en {output_file}")
    return results


# ============================================================================
# CLI
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grid search de detección de layout sobre las 18 imágenes popurri",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "\nEjemplos:\n"
            "  py -3.11 experiment_models.py\n"
            "  py -3.11 experiment_models.py --methods doclayout yolo11\n"
            "  py -3.11 experiment_models.py --resume\n"
        ),
    )
    parser.add_argument(
        "--images-dir",
        default=str(IMAGES_DIR),
        help=f"Carpeta con imágenes popurri*.jpg (default: {IMAGES_DIR})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Archivo JSON de resultados (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=EXPERIMENT_GRID["methods"],
        help="Subconjunto de métodos a ejecutar (default: todos)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reanudar desde un archivo de resultados previo",
    )
    parser.add_argument(
        "--debug-mask",
        action="store_true",
        help="Guardar la mascara refinada de bloques de texto para inspeccion visual",
    )
    parser.add_argument(
        "--debug-mask-dir",
        default=None,
        help="Carpeta base para guardar las mascaras debug (default: build/)",
    )
    parser.add_argument(
        "--debug-boxes",
        action="store_true",
        help="Guardar una visualizacion y JSON con las cajas detectadas por experimento",
    )
    args = parser.parse_args()

    run_grid_search(
        images_dir=Path(args.images_dir),
        output_file=Path(args.output),
        methods=args.methods,
        resume=args.resume,
        debug_mask=args.debug_mask,
        debug_boxes=args.debug_boxes,
        debug_dir=Path(args.debug_mask_dir) if args.debug_mask_dir else None,
    )


if __name__ == "__main__":
    main()
