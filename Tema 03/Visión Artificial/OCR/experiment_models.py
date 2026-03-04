"""experiment_models.py

Grid search sistemático sobre todos los métodos de detección de layout.

Espacio de búsqueda:
  - doclayout / yolo11 : conf_threshold × nms_iou × merge_distance
  - paddleocr / docling: nms_iou × merge_distance
                         (sin conf configurable — hardcodeado a 0.3 en el modelo)

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

# Ajustar sys.path para importar desde la misma carpeta
sys.path.insert(0, str(Path(__file__).parent))

from detect_columns import detect_columns, ColumnBox
import post_processing as pp

# ============================================================================
# Grid de experimentos
# ============================================================================

EXPERIMENT_GRID: Dict[str, Any] = {
    # ✅ Métodos viables tras FASE 2.2
    "methods": ["doclayout", "yolo11", "paddleocr", "docling"],
    "conf_thresholds": [0.1, 0.2, 0.3, 0.4],
    "nms_iou": [0.3, 0.4, 0.5, 0.6],
    "merge_distance": [5, 10, 15, 20],
}

# Métodos con umbral de confianza configurable
METHODS_WITH_CONF = {"doclayout", "yolo11"}

# Métodos sin umbral de confianza (fijado internamente a 0.3 en LayoutPredictor)
METHODS_WITHOUT_CONF = {"paddleocr", "docling"}

# Rutas por defecto
IMAGES_DIR = Path(__file__).parent / "imgs"
DEFAULT_OUTPUT = Path(__file__).parent / "experiment_results.json"


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


# ============================================================================
# Ejecución de un único experimento
# ============================================================================

def run_single_experiment(
    img: Any,           # np.ndarray — tipado como Any para evitar import en bloque
    image_path: str,
    method: str,
    config: Dict[str, Any],
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
            nms_iou=config["nms_iou"],
            merge_distance=config["merge_distance"],
            debug=False,
            image_path=image_path,   # solo para nombrar la carpeta de debug si debug=True
        )
        if method == "doclayout":
            kwargs["doclayout_conf"] = config["conf"]
        elif method == "yolo11":
            kwargs["yolo11_conf"] = config["conf"]
        # paddleocr y docling: sin parámetro de conf, hardcoded a 0.3 en LayoutPredictor

        # detect_columns devuelve ((width, height), List[ColumnBox])
        _size, boxes = detect_columns(img, **kwargs)

        elapsed_ms = (time.perf_counter() - start) * 1000
        num_boxes = len(boxes)
        avg_area = (
            sum(_box_area(b) for b in boxes) / num_boxes if num_boxes > 0 else 0.0
        )
        duplicates = _count_duplicates(boxes)

        return {
            "success": True,
            "num_boxes": num_boxes,
            "avg_area": round(avg_area, 1),
            "duplicates": duplicates,
            "time_ms": round(elapsed_ms, 1),
        }

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "num_boxes": 0,
            "avg_area": 0.0,
            "duplicates": 0,
            "time_ms": round(elapsed_ms, 1),
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
            conf_str = f"conf={config['conf']:.2f}  " if "conf" in config else "conf=N/A(0.3)"
            print(
                f"[{exp_id:>5}/{total}] {method:12s} | {conf_str} "
                f"nms={config['nms_iou']}  merge={config['merge_distance']:>2d} | {img_name}"
            )

            img = images_cache.get(img_name)
            if img is None:
                continue

            metrics = run_single_experiment(img, str(img_path), method, config)

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
    args = parser.parse_args()

    run_grid_search(
        images_dir=Path(args.images_dir),
        output_file=Path(args.output),
        methods=args.methods,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
