"""validate_ocr.py

FASE 4 — Validacion OCR completo con las mejores configuraciones del grid search.

Para cada configuracion seleccionada y cada motor OCR:
  1. Ejecuta deteccion de regions (detect_columns.detect_columns)
    2. Ejecuta OCR sobre cada region detectada (EasyOCR/Tesseract/Paddle/DeepSeek)
  3. Recopila metricas: caracteres, palabras, columnas, duplicados, tiempo
  4. Genera informe comparativo

Modos de uso:
    # Automatico (default usa 4 OCR: easyocr,tesseract,paddle,deepseek)
    # Requiere pasar ruta de Tesseract y modelo DeepSeek:
    py -3.11 validate_ocr.py --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" --deepseek-model-path ".\\models\\DeepSeek-OCR"

    # Automatico solo con OCR que no requieren argumentos extra (sin tesseract/deepseek)
    py -3.11 validate_ocr.py --ocr-engines easyocr,paddle

    # Automatico usando Tesseract + DeepSeek (requiere rutas explicitas en Windows)
    py -3.11 validate_ocr.py --ocr-engines tesseract,deepseek --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" --deepseek-model-path ".\\models\\DeepSeek-OCR"

  # Top-N configuraciones globales:
  py -3.11 validate_ocr.py --top 5

    # Top-N con DeepSeek:
    py -3.11 validate_ocr.py --top 5 --ocr-engines deepseek --deepseek-model-path ".\\models\\DeepSeek-OCR"

  # Configuraciones manuales (sin necesitar Phase 3):
  py -3.11 validate_ocr.py --configs '[
      {"method":"paddleocr","nms_iou":0.5,"merge_distance":10},
      {"method":"docling","nms_iou":0.5,"merge_distance":10},
      {"method":"doclayout","conf":0.2,"nms_iou":0.4,"merge_distance":15},
      {"method":"yolo11","conf":0.1,"nms_iou":0.5,"merge_distance":10},
      {"method":"opencv","merge_distance":10}
  ]'

    # Configuraciones manuales con Tesseract:
    py -3.11 validate_ocr.py --configs '[{"method":"docling","nms_iou":0.5,"merge_distance":10}]' --ocr-engines tesseract --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

  # Solo un metodo concreto:
  py -3.11 validate_ocr.py --method paddleocr

    # Solo un metodo concreto con DeepSeek:
    py -3.11 validate_ocr.py --method docling --ocr-engines deepseek --deepseek-model-path ".\\models\\DeepSeek-OCR"

  # Reanudar ejecucion interrumpida:
  py -3.11 validate_ocr.py --resume

    # Reanudar con Tesseract + DeepSeek:
    py -3.11 validate_ocr.py --resume --ocr-engines tesseract,deepseek --tesseract-cmd "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" --deepseek-model-path ".\\models\\DeepSeek-OCR"

    # DeepSeek sobre recortes detectados (recomendado: prompt oficial)
    py -3.11 validate_ocr.py --ocr-engines deepseek --deepseek-model-path ".\\models\\DeepSeek-OCR" --deepseek-prompt "<image>\n<|grounding|>Convert the document to markdown."

    # Nota: prompts libres de "plain text only" pueden devolver salida vacia en recortes.
    # Si personalizas el prompt, valida primero sobre una sola configuracion.

"""
from __future__ import annotations

import argparse
import os
import json
import re
import sys
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# Evita chequeos de conectividad de Paddle al iniciar modelos.
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

# ---------------------------------------------------------------------------
# Dependencias opcionales con feedback claro
# ---------------------------------------------------------------------------
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("[WARN] pandas no instalado; el modo automatico no estara disponible.")

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    print("[WARN] easyocr no instalado: pip install easyocr")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    print("[WARN] pytesseract no instalado: pip install pytesseract")

try:
    from paddleocr import PaddleOCR
    HAS_PADDLE_OCR = True
except ImportError:
    HAS_PADDLE_OCR = False
    print("[WARN] paddleocr no instalado: pip install paddleocr")

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
    HAS_DEEPSEEK_DEPS = True
except ImportError:
    HAS_DEEPSEEK_DEPS = False
    print("[WARN] transformers/torch no instalados; DeepSeek no disponible")

# Añadir directorio actual al path para importar detect_columns como modulo
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

try:
    import detect_columns as dc
    HAS_DC = True
except ImportError as _e:
    HAS_DC = False
    print(f"[ERROR] No se pudo importar detect_columns: {_e}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Rutas y constantes
# ---------------------------------------------------------------------------
IMGS_DIR = _HERE / "imgs"
RANKING_CSV = _HERE / "experiment_ranking.csv"
RESULTS_DIR = _HERE / "validation_results"
DEEPSEEK_DEFAULT_MODEL_DIR = _HERE / "models" / "DeepSeek-OCR"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

# Pesos de la formula de scoring OCR (ajustables)
CHARS_WEIGHT = 1.0       # por caracter extraido
WORDS_WEIGHT = 5.0       # bonus por palabra detectada
DUP_PENALTY = 50.0       # penalizacion por duplicado en deteccion
MISSED_PENALTY = 20.0    # penalizacion por imagen sin regiones detectadas

SUPPORTED_ENGINES = ["easyocr", "tesseract", "paddle", "deepseek"]
DEEPSEEK_DEFAULT_REGION_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."


class DeepSeekFatalError(RuntimeError):
    """Error fatal de DeepSeek que invalida continuar con ese motor."""


def _load_deepseek_model_with_fallback(model_dir: Path) -> Tuple[Any, Any, str]:
    """Carga DeepSeek con la misma estrategia de pruebas-deepseek.py.

    Returns:
        tokenizer, model, attn_impl_utilizada
    """
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)

    try:
        model = AutoModel.from_pretrained(
            str(model_dir),
            trust_remote_code=True,
            use_safetensors=True,
            _attn_implementation="flash_attention_2",
        )
        model = model.eval().cuda().to(torch.bfloat16)
        return tokenizer, model, "flash_attention_2"
    except Exception:
        model = AutoModel.from_pretrained(
            str(model_dir),
            trust_remote_code=True,
            use_safetensors=True,
        )
        model = model.eval().cuda().to(torch.bfloat16)
        return tokenizer, model, "default"


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """Numero de palabras con al menos 2 caracteres alfabeticos."""
    return sum(1 for w in text.split() if sum(c.isalpha() for c in w) >= 2)


def clean_ocr_text(text: str) -> str:
    """Elimina lineas vacias y espacios extra."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# OCR sobre regiones
# ---------------------------------------------------------------------------

def run_easyocr_on_regions(
    img_bgr: np.ndarray,
    boxes: List,          # List[ColumnBox] de detect_columns
    reader: "easyocr.Reader",
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con EasyOCR.

    Returns dict con:
        total_chars, total_words, per_region (list de dicts con texto/chars/words)
    """
    per_region = []
    total_chars = 0
    total_words = 0

    for i, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
        # Clip a los limites de la imagen
        h, w = img_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
            continue

        region = img_bgr[y1:y2, x1:x2]

        try:
            results = reader.readtext(region, detail=0, paragraph=True)
            text = clean_ocr_text(" ".join(results))
        except Exception as exc:
            text = ""
            print(f"    [WARN] EasyOCR fallo en region {i}: {exc}")

        chars = len(text.replace(" ", "").replace("\n", ""))
        words = count_words(text)
        total_chars += chars
        total_words += words
        per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


def run_tesseract_on_regions(
    img_bgr: np.ndarray,
    boxes: List,
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con Tesseract."""
    per_region: List[Dict[str, Any]] = []
    total_chars = 0
    total_words = 0

    for i, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
        h, w = img_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
            continue

        region = img_bgr[y1:y2, x1:x2]
        try:
            text = pytesseract.image_to_string(region, lang="spa+eng")
            text = clean_ocr_text(text)
        except Exception as exc:
            text = ""
            print(f"    [WARN] Tesseract fallo en region {i}: {exc}")

        chars = len(text.replace(" ", "").replace("\n", ""))
        words = count_words(text)
        total_chars += chars
        total_words += words
        per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


def run_paddle_on_regions(
    img_bgr: np.ndarray,
    boxes: List,
    paddle_reader: "PaddleOCR",
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con PaddleOCR."""
    per_region: List[Dict[str, Any]] = []
    total_chars = 0
    total_words = 0

    with tempfile.TemporaryDirectory(prefix="ocr_paddle_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        for i, box in enumerate(boxes, start=1):
            x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
            h, w = img_bgr.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 <= x1 or y2 <= y1:
                per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
                continue

            region = img_bgr[y1:y2, x1:x2]
            region_file = tmp_path / f"region_{i}.png"
            cv2.imwrite(str(region_file), region)

            text = ""
            try:
                pred = paddle_reader.predict(str(region_file))
                if pred and isinstance(pred, list) and len(pred) > 0:
                    rec_texts = pred[0].get("rec_texts", [])
                    text = clean_ocr_text("\n".join(rec_texts))
            except Exception as exc:
                print(f"    [WARN] PaddleOCR fallo en region {i}: {exc}")

            chars = len(text.replace(" ", "").replace("\n", ""))
            words = count_words(text)
            total_chars += chars
            total_words += words
            per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


def _deepseek_result_to_text(result: Any) -> str:
    """Intenta extraer texto OCR de distintos formatos devueltos por DeepSeek."""
    def _normalize(text: str) -> str:
        text = text.replace("<｜end▁of▁sentence｜>", "")
        text = re.sub(r"<\|ref\|>.*?<\|/ref\|>", "", text, flags=re.DOTALL)
        text = re.sub(r"<\|det\|>.*?<\|/det\|>", "", text, flags=re.DOTALL)
        text = re.sub(r"!\[\]\([^)]*\)", "", text)
        return clean_ocr_text(text)

    if result is None:
        return ""
    if isinstance(result, str):
        return _normalize(result)
    if isinstance(result, dict):
        for key in ("text", "result", "output", "markdown"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return _normalize(val)
        return _normalize(json.dumps(result, ensure_ascii=False))
    if isinstance(result, list):
        parts = [_deepseek_result_to_text(x) for x in result]
        return clean_ocr_text("\n".join([p for p in parts if p]))
    return _normalize(str(result))


def _prepare_region_for_deepseek(region_bgr: np.ndarray, min_side: int = 640) -> np.ndarray:
    """Acolcha el recorte a cuadrado para estabilizar el preprocesado visual.

    DeepSeek-OCR puede desalinear tokens visuales en recortes extremos
    (muy estrechos/altos). Este padding reduce casos de mismatch 299/300.
    """
    h, w = region_bgr.shape[:2]
    side = max(h, w, int(min_side))
    # Alinear a múltiplos de 32 para evitar artefactos de discretización.
    side = int(np.ceil(side / 32.0) * 32)

    canvas = np.full((side, side, 3), 255, dtype=region_bgr.dtype)
    y = (side - h) // 2
    x = (side - w) // 2
    canvas[y:y + h, x:x + w] = region_bgr
    return canvas


def run_deepseek_on_regions(
    img_bgr: np.ndarray,
    boxes: List,
    deepseek_model: Any,
    deepseek_tokenizer: Any,
    prompt: str,
    base_size: int = 1024,
    image_size: int = 1024,
    crop_mode: bool = False,
) -> Dict[str, Any]:
    """Extrae texto de cada region detectada con DeepSeek OCR local.

    Se fuerza eval_mode=True porque el modelo remoto devuelve el texto OCR de
    forma fiable por retorno en ese modo. Con save_results=False y eval_mode=False
    puede no devolver texto util aunque la inferencia termine correctamente.
    """
    per_region: List[Dict[str, Any]] = []
    total_chars = 0
    total_words = 0

    with tempfile.TemporaryDirectory(prefix="ocr_deepseek_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        canonical_prompt = DEEPSEEK_DEFAULT_REGION_PROMPT

        for i, box in enumerate(boxes, start=1):
            x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
            h, w = img_bgr.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 <= x1 or y2 <= y1:
                per_region.append({"region": i, "text": "", "chars": 0, "words": 0})
                continue

            region = img_bgr[y1:y2, x1:x2]
            region = _prepare_region_for_deepseek(region, min_side=max(image_size, 640))
            region_file = tmp_path / f"region_{i}.png"
            cv2.imwrite(str(region_file), region)

            text = ""
            try:
                result = deepseek_model.infer(
                    deepseek_tokenizer,
                    prompt=prompt,
                    image_file=str(region_file),
                    output_path=str(tmp_path / f"out_{i}"),
                    base_size=base_size,
                    image_size=image_size,
                    crop_mode=crop_mode,
                    save_results=False,
                    test_compress=False,
                    eval_mode=True,
                )
                text = _deepseek_result_to_text(result)
            except Exception as exc:
                msg = str(exc)
                # Workaround para bug interno: `param_img` queda sin inicializar
                # con ciertas resoluciones no soportadas por el encoder.
                if "param_img" in msg and (base_size, image_size, crop_mode) != (1024, 1024, False):
                    try:
                        result = deepseek_model.infer(
                            deepseek_tokenizer,
                            prompt=prompt,
                            image_file=str(region_file),
                            output_path=str(tmp_path / f"out_{i}_fallback"),
                            base_size=1024,
                            image_size=1024,
                            crop_mode=False,
                            save_results=False,
                            test_compress=False,
                            eval_mode=True,
                        )
                        text = _deepseek_result_to_text(result)
                        print(
                            f"    [INFO] DeepSeek region {i}: fallback 1024x1024 aplicado por error param_img"
                        )
                    except Exception as retry_exc:
                        print(f"    [WARN] DeepSeek fallo en region {i}: {retry_exc}")
                else:
                    # Fallback para desajustes de longitud visual/token (299/300, 598/299, etc.)
                    # observados en ciertas combinaciones de prompt/API de transformers.
                    shape_mismatch = (
                        "expanded size of the tensor" in msg
                        or "size of tensor" in msg
                        or "must match the existing size" in msg
                    )
                    if shape_mismatch:
                        try:
                            result = deepseek_model.infer(
                                deepseek_tokenizer,
                                prompt=canonical_prompt,
                                image_file=str(region_file),
                                output_path=str(tmp_path / f"out_{i}_shape_retry"),
                                base_size=1024,
                                image_size=640,
                                crop_mode=True,
                                save_results=False,
                                test_compress=False,
                                eval_mode=True,
                            )
                            text = _deepseek_result_to_text(result)
                            print(
                                f"    [INFO] DeepSeek region {i}: retry shape-mismatch con prompt/crop oficial"
                            )
                        except Exception as retry_exc:
                            retry_msg = str(retry_exc)
                            print(f"    [WARN] DeepSeek fallo en region {i}: {retry_exc}")
                            if (
                                "expanded size of the tensor" in retry_msg
                                or "must match the existing size" in retry_msg
                                or "size of tensor" in retry_msg
                            ):
                                raise DeepSeekFatalError(retry_msg)
                    else:
                        print(f"    [WARN] DeepSeek fallo en region {i}: {exc}")

            chars = len(text.replace(" ", "").replace("\n", ""))
            words = count_words(text)
            total_chars += chars
            total_words += words
            per_region.append({"region": i, "text": text, "chars": chars, "words": words})

    return {
        "total_chars": total_chars,
        "total_words": total_words,
        "per_region": per_region,
    }


# ---------------------------------------------------------------------------
# Deteccion de regiones (wrapper sobre detect_columns)
# ---------------------------------------------------------------------------

def run_detection(
    img_bgr: np.ndarray,
    image_path: str,
    cfg: Dict[str, Any],
) -> Tuple[List, int, float]:
    """Ejecuta deteccion de regiones para una configuracion.

    Returns:
        boxes        — lista de ColumnBox
        duplicates   — numero de duplicados detectados por NMS
        elapsed_ms   — tiempo transcurrido en milisegundos
    """
    method = cfg["method"]
    conf = cfg.get("conf", 0.25)
    nms_iou = cfg.get("nms_iou", 0.5)
    merge_distance = cfg.get("merge_distance", 10)
    min_area = cfg.get("min_area", 100)
    yolo11_conf = cfg.get("yolo11_conf", conf)  # mismo conf para yolo11
    yolo11_size = cfg.get("yolo11_size", "nano")

    t0 = time.perf_counter()
    try:
        _, boxes = dc.detect_columns(
            img_bgr,
            method=method,
            debug=False,
            doclayout_conf=conf,
            doclayout_all_classes=False,
            nms_iou=nms_iou,
            merge_distance=merge_distance,
            min_area=min_area,
            enable_nms=True,
            enable_merge=True,
            enable_filter=True,
            model_path=None,
            image_path=image_path,
            yolo11_conf=yolo11_conf,
            yolo11_size=yolo11_size,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Estimar duplicados: cuantas cajas eliminaria un NMS mas estricto
        duplicates = _estimate_duplicates(boxes)
        return boxes, duplicates, elapsed_ms

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"    [ERROR] Deteccion fallo: {exc}")
        return [], 0, elapsed_ms


def _estimate_duplicates(boxes: List) -> int:
    """Cuenta pares de cajas con IoU > 0.3 (posibles duplicados residuales)."""
    from post_processing import calculate_iou  # disponible en el proyecto
    count = 0
    n = len(boxes)
    for i in range(n):
        for j in range(i + 1, n):
            b1 = (boxes[i].x1, boxes[i].y1, boxes[i].x2, boxes[i].y2)
            b2 = (boxes[j].x1, boxes[j].y1, boxes[j].x2, boxes[j].y2)
            if calculate_iou(b1, b2) > 0.3:
                count += 1
    return count


# ---------------------------------------------------------------------------
# Carga de configuraciones
# ---------------------------------------------------------------------------

def load_top_configs_from_ranking(
    csv_path: Path,
    top_n: int = 3,
    method_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lee experiment_ranking.csv y devuelve las top_n configuraciones.

    Si method_filter se especifica, devuelve las top_n de ese metodo.
    Si no, devuelve las top_n globales (una por metodo diferente si es posible).
    """
    if not HAS_PANDAS:
        sys.exit("[ERROR] pandas requerido para leer el ranking. Instala con: pip install pandas")
    if not csv_path.exists():
        sys.exit(
            f"[ERROR] No se encontro {csv_path}\n"
            "        Ejecuta primero: py -3.11 analyze_experiments.py"
        )

    df = pd.read_csv(csv_path)

    if method_filter:
        df = df[df["method"] == method_filter]
        if df.empty:
            sys.exit(f"[ERROR] No hay resultados para el metodo '{method_filter}' en el ranking.")

    # Ordenar por score descendente
    df = df.sort_values("score", ascending=False).head(top_n)

    configs = []
    for _, row in df.iterrows():
        cfg: Dict[str, Any] = {
            "method": row["method"],
            "merge_distance": int(row["merge_distance"]),
        }
        # nms_iou es NaN para opencv (sin nms configurable)
        nms_val = row.get("nms_iou")
        if pd.notna(nms_val):
            cfg["nms_iou"] = float(nms_val)
        conf_val = row.get("conf")
        if pd.notna(conf_val):
            cfg["conf"] = float(conf_val)
        configs.append(cfg)

    return configs


def build_config_label(cfg: Dict[str, Any]) -> str:
    """Genera un identificador legible para una configuracion."""
    parts = [cfg["method"]]
    if "conf" in cfg:
        parts.append(f"conf{cfg['conf']:.2f}")
    if "nms_iou" in cfg:          # opencv no tiene nms_iou
        parts.append(f"nms{cfg['nms_iou']:.2f}")
    parts.append(f"mg{cfg['merge_distance']}")
    return "_".join(parts)


# ---------------------------------------------------------------------------
# Ejecucion de una configuracion sobre todas las imagenes
# ---------------------------------------------------------------------------

def run_config(
    cfg: Dict[str, Any],
    image_paths: List[Path],
    ocr_engines: List[str],
    engine_ctx: Dict[str, Any],
    output_dir: Path,
    resume: bool = False,
) -> List[Dict[str, Any]]:
    """Ejecuta deteccion una vez por imagen y OCR para uno o varios motores.

    Optimizacion clave:
      - La deteccion de layout se calcula solo una vez por imagen/config.
      - El resultado (boxes, dups, det_ms) se reutiliza para todos los OCR pendientes.
    """
    label = build_config_label(cfg)
    config_dir = output_dir / label
    config_dir.mkdir(parents=True, exist_ok=True)

    # Estado por motor OCR (fichero + resultados parciales para resume)
    per_engine: Dict[str, Dict[str, Any]] = {}
    for ocr_engine in ocr_engines:
        results_file = config_dir / f"results_{ocr_engine}.json"
        existing: Dict[str, Any] = {}
        if resume and results_file.exists():
            with open(results_file, encoding="utf-8") as f:
                existing = json.load(f)
            already_done = set(existing.get("per_image", {}).keys())
            print(f"    [resume] {ocr_engine}: {len(already_done)} imagenes ya procesadas, saltando.")
        else:
            already_done = set()

        per_engine[ocr_engine] = {
            "results_file": results_file,
            "per_image": existing.get("per_image", {}),
            "already_done": already_done,
        }

    for img_path in image_paths:
        img_name = img_path.name

        # Procesar solo motores que aun no tengan esta imagen (modo resume parcial)
        pending_engines = [
            eng for eng in ocr_engines
            if img_name not in per_engine[eng]["already_done"]
        ]
        if not pending_engines:
            continue

        print(f"    {img_name} ...", end="", flush=True)
        img_bgr = dc.load_image(str(img_path))

        # --- Deteccion ---
        boxes, duplicates, det_ms = run_detection(img_bgr, str(img_path), cfg)
        num_boxes = len(boxes)

        print(f" boxes={num_boxes}, dups={duplicates}, det={det_ms:.0f}ms")

        for ocr_engine in pending_engines:
            # --- OCR ---
            can_run_engine = (
                (ocr_engine == "easyocr" and "easyocr" in engine_ctx)
                or (ocr_engine == "tesseract")
                or (ocr_engine == "paddle" and "paddle" in engine_ctx)
                or (
                    ocr_engine == "deepseek"
                    and "deepseek_model" in engine_ctx
                    and "deepseek_tokenizer" in engine_ctx
                    and not bool(engine_ctx.get("deepseek_disabled", False))
                )
            )

            if num_boxes > 0 and can_run_engine:
                ocr_start = time.perf_counter()
                if ocr_engine == "easyocr":
                    ocr_data = run_easyocr_on_regions(img_bgr, boxes, engine_ctx["easyocr"])
                elif ocr_engine == "tesseract":
                    ocr_data = run_tesseract_on_regions(img_bgr, boxes)
                elif ocr_engine == "paddle":
                    ocr_data = run_paddle_on_regions(img_bgr, boxes, engine_ctx["paddle"])
                elif ocr_engine == "deepseek":
                    try:
                        ocr_data = run_deepseek_on_regions(
                            img_bgr,
                            boxes,
                            engine_ctx["deepseek_model"],
                            engine_ctx["deepseek_tokenizer"],
                            engine_ctx.get(
                                "deepseek_prompt",
                                DEEPSEEK_DEFAULT_REGION_PROMPT,
                            ),
                            base_size=int(engine_ctx.get("deepseek_base_size", 1024)),
                            image_size=int(engine_ctx.get("deepseek_image_size", 1024)),
                            crop_mode=bool(engine_ctx.get("deepseek_crop_mode", False)),
                        )
                    except DeepSeekFatalError as fatal_exc:
                        engine_ctx["deepseek_disabled"] = True
                        print(
                            "    [WARN] DeepSeek desactivado para el resto de la ejecución "
                            f"por error fatal interno: {fatal_exc}"
                        )
                        ocr_data = {"total_chars": 0, "total_words": 0, "per_region": []}
                else:
                    ocr_data = {"total_chars": 0, "total_words": 0, "per_region": []}
                ocr_ms = (time.perf_counter() - ocr_start) * 1000
            else:
                ocr_data = {"total_chars": 0, "total_words": 0, "per_region": []}
                ocr_ms = 0.0

            per_image = per_engine[ocr_engine]["per_image"]
            per_image[img_name] = {
                "num_boxes": num_boxes,
                "duplicates": duplicates,
                "det_ms": round(det_ms, 1),
                "ocr_ms": round(ocr_ms, 1),
                "total_chars": ocr_data["total_chars"],
                "total_words": ocr_data["total_words"],
                "per_region": ocr_data["per_region"],
            }

            total_ms = det_ms + ocr_ms
            print(
                f"      [{ocr_engine}] chars={ocr_data['total_chars']}, "
                f"words={ocr_data['total_words']}, time={total_ms:.0f}ms"
            )

            # Guardado incremental por motor
            _save_config_results(
                per_engine[ocr_engine]["results_file"],
                cfg,
                label,
                per_image,
            )

    # --- Calcular agregados finales por motor ---
    summaries: List[Dict[str, Any]] = []
    for ocr_engine in ocr_engines:
        per_image = per_engine[ocr_engine]["per_image"]

        n_imgs = len(per_image)
        total_chars = sum(v["total_chars"] for v in per_image.values())
        total_words = sum(v["total_words"] for v in per_image.values())
        total_dups = sum(v["duplicates"] for v in per_image.values())
        mean_boxes = sum(v["num_boxes"] for v in per_image.values()) / max(n_imgs, 1)
        mean_det_ms = sum(v["det_ms"] for v in per_image.values()) / max(n_imgs, 1)
        mean_ocr_ms = sum(v["ocr_ms"] for v in per_image.values()) / max(n_imgs, 1)
        imgs_no_boxes = sum(1 for v in per_image.values() if v["num_boxes"] == 0)

        # Formula de scoring OCR
        ocr_score = (
            total_chars * CHARS_WEIGHT
            + total_words * WORDS_WEIGHT
            - total_dups * DUP_PENALTY
            - imgs_no_boxes * MISSED_PENALTY
        )

        summary = {
            "config": cfg,
            "label": label,
            "ocr_engine": ocr_engine,
            "n_images": n_imgs,
            "total_chars": total_chars,
            "total_words": total_words,
            "total_duplicates": total_dups,
            "mean_boxes": round(mean_boxes, 2),
            "imgs_no_boxes": imgs_no_boxes,
            "mean_det_ms": round(mean_det_ms, 1),
            "mean_ocr_ms": round(mean_ocr_ms, 1),
            "ocr_score": round(ocr_score, 2),
            "per_image": per_image,
        }

        _save_config_results(
            per_engine[ocr_engine]["results_file"],
            cfg,
            label,
            per_image,
            summary,
        )
        summaries.append(summary)

    return summaries


def _save_config_results(
    path: Path,
    cfg: Dict,
    label: str,
    per_image: Dict,
    summary: Optional[Dict] = None,
) -> None:
    """Guardado incremental a disco."""
    data = {"config": cfg, "label": label, "per_image": per_image}
    if summary:
        data.update({k: v for k, v in summary.items() if k != "per_image"})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FASE 4 — Validacion OCR con las mejores configuraciones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--top", type=int, default=3, metavar="N",
        help="Numero de configuraciones a validar desde el ranking (default: 3)"
    )
    parser.add_argument(
        "--method", type=str, default=None,
        choices=["opencv", "doclayout", "yolo11", "paddleocr", "docling"],
        help="Filtrar por metodo al leer el ranking"
    )
    parser.add_argument(
        "--configs", type=str, default=None, metavar="JSON",
        help="Lista de configuraciones en JSON (modo manual, no necesita Phase 3)"
    )
    parser.add_argument(
        "--images-dir", type=Path, default=IMGS_DIR,
        help=f"Directorio de imagenes (default: {IMGS_DIR})"
    )
    parser.add_argument(
        "--ranking-csv", type=Path, default=RANKING_CSV,
        help=f"CSV de ranking generado por analyze_experiments.py (default: {RANKING_CSV})"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=RESULTS_DIR,
        help=f"Directorio de salida (default: {RESULTS_DIR})"
    )
    parser.add_argument(
        "--no-ocr", action="store_true",
        help="Solo ejecutar deteccion, sin OCR (mas rapido para debug)"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Reanudar ejecucion anterior (salta imagenes ya procesadas)"
    )
    parser.add_argument(
        "--langs", type=str, default="es,en",
        help="Idiomas para EasyOCR separados por coma (default: es,en)"
    )
    parser.add_argument(
        "--ocr-engines", type=str, default="easyocr,tesseract,paddle,deepseek",
        help="Motores OCR a usar separados por coma (easyocr,tesseract,paddle,deepseek)"
    )
    parser.add_argument(
        "--deepseek-model-path", type=str, default=str(DEEPSEEK_DEFAULT_MODEL_DIR),
        help=(
            "Ruta local del modelo DeepSeek-OCR "
            f"(default: {DEEPSEEK_DEFAULT_MODEL_DIR}; sobreescribe si quieres otra ruta)"
        )
    )
    parser.add_argument(
        "--deepseek-prompt",
        type=str,
        default=DEEPSEEK_DEFAULT_REGION_PROMPT,
        help="Prompt para inferencia DeepSeek por region (default: prompt oficial con grounding)"
    )
    parser.add_argument(
        "--deepseek-base-size", type=int, default=1024,
        help="Base size de DeepSeek por region (default: 1024; evita bug param_img)"
    )
    parser.add_argument(
        "--deepseek-image-size", type=int, default=1024,
        help="Image size de DeepSeek por region (default: 1024; evita bug param_img)"
    )
    parser.add_argument(
        "--deepseek-crop-mode", action="store_true",
        help="Activar crop_mode de DeepSeek (default: desactivado)"
    )
    parser.add_argument(
        "--tesseract-cmd", type=str, default=None,
        help="Ruta a tesseract.exe (opcional, para Windows)"
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # --- Buscar imagenes ---
    images_dir = args.images_dir
    if not images_dir.exists():
        sys.exit(f"[ERROR] Directorio de imagenes no encontrado: {images_dir}")

    image_paths = sorted(
        p for p in images_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_paths:
        sys.exit(f"[ERROR] No se encontraron imagenes en: {images_dir}")

    print(f"[i] Imagenes encontradas: {len(image_paths)} en {images_dir}")

    # --- Cargar configuraciones ---
    if args.configs:
        try:
            configs = json.loads(args.configs)
        except json.JSONDecodeError as e:
            sys.exit(f"[ERROR] --configs no es JSON valido: {e}")
        print(f"[i] Modo manual: {len(configs)} configuraciones especificadas")
    else:
        configs = load_top_configs_from_ranking(
            args.ranking_csv, top_n=args.top, method_filter=args.method
        )
        print(f"[i] Top-{args.top} configuraciones del ranking:")

    for cfg in configs:
        print(f"    {build_config_label(cfg)}")
    print()

    # --- Resolver motores OCR solicitados ---
    requested_engines = [e.strip().lower() for e in args.ocr_engines.split(",") if e.strip()]
    invalid = [e for e in requested_engines if e not in SUPPORTED_ENGINES]
    if invalid:
        sys.exit(f"[ERROR] Motores OCR no validos: {invalid}. Validos: {SUPPORTED_ENGINES}")

    if args.no_ocr:
        active_engines: List[str] = []
        print("[WARN] --no-ocr activo: se ejecutara solo deteccion.")
    else:
        active_engines = []
        engine_ctx: Dict[str, Any] = {}

        # EasyOCR
        if "easyocr" in requested_engines:
            if HAS_EASYOCR:
                langs = [lang.strip() for lang in args.langs.split(",") if lang.strip()]
                print(f"[i] Inicializando EasyOCR (idiomas: {langs})...")
                t0 = time.perf_counter()
                engine_ctx["easyocr"] = easyocr.Reader(langs, gpu=False, verbose=False)
                print(f"[OK] EasyOCR listo en {(time.perf_counter()-t0)*1000:.0f}ms")
                active_engines.append("easyocr")
            else:
                print("[WARN] easyocr solicitado pero no disponible; se omite.")

        # Tesseract
        if "tesseract" in requested_engines:
            if HAS_TESSERACT:
                if args.tesseract_cmd:
                    pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd
                active_engines.append("tesseract")
                print("[OK] Tesseract disponible")
            else:
                print("[WARN] tesseract solicitado pero pytesseract no disponible; se omite.")

        # PaddleOCR
        if "paddle" in requested_engines:
            if HAS_PADDLE_OCR:
                print("[i] Inicializando PaddleOCR...")
                t0 = time.perf_counter()
                engine_ctx["paddle"] = PaddleOCR(lang="es", use_textline_orientation=False)
                print(f"[OK] PaddleOCR listo en {(time.perf_counter()-t0)*1000:.0f}ms")
                active_engines.append("paddle")
            else:
                print("[WARN] paddle solicitado pero paddleocr no disponible; se omite.")

        # DeepSeek local
        if "deepseek" in requested_engines:
            deepseek_ready = False
            deepseek_model_path = Path(args.deepseek_model_path)
            if HAS_DEEPSEEK_DEPS:
                if not torch.cuda.is_available():
                    print("[WARN] deepseek solicitado pero CUDA no disponible; se omite.")
                elif not deepseek_model_path.exists():
                    print(
                        "[WARN] Modelo DeepSeek no encontrado en "
                        f"'{deepseek_model_path}'. Ejecuta install.bat o usa --deepseek-model-path."
                    )
                else:
                    print("[i] Inicializando DeepSeek OCR local...")
                    t0 = time.perf_counter()
                    try:
                        tokenizer, model, attn_impl = _load_deepseek_model_with_fallback(deepseek_model_path)
                        engine_ctx["deepseek_model"] = model
                        engine_ctx["deepseek_tokenizer"] = tokenizer
                        engine_ctx["deepseek_prompt"] = args.deepseek_prompt
                        engine_ctx["deepseek_base_size"] = int(args.deepseek_base_size)
                        engine_ctx["deepseek_image_size"] = int(args.deepseek_image_size)
                        engine_ctx["deepseek_crop_mode"] = bool(args.deepseek_crop_mode)
                        print(
                            f"[OK] DeepSeek listo en {(time.perf_counter()-t0)*1000:.0f}ms "
                            f"(attn={attn_impl}, base={args.deepseek_base_size}, "
                            f"img={args.deepseek_image_size}, crop={args.deepseek_crop_mode})"
                        )
                        deepseek_ready = True
                    except Exception as exc:
                        msg = str(exc)
                        if "LlamaFlashAttention2" in msg:
                            msg += (
                                " | Sugerencia: reinstala el entorno con install.bat y verifica que "
                                "sitecustomize.py se haya copiado al site-packages de Python 3.11."
                            )
                        print(
                            "[WARN] No se pudo inicializar DeepSeek; se omite este motor. "
                            f"Detalle: {msg}"
                        )
            else:
                print("[WARN] deepseek solicitado pero faltan dependencias (torch/transformers); se omite.")
            if deepseek_ready:
                active_engines.append("deepseek")

        if not active_engines:
            print("[WARN] Ningun motor OCR disponible; se ejecutara solo deteccion.")
            engine_ctx = {}

        print(f"[i] Motores OCR activos: {active_engines if active_engines else ['none']}\n")

    # --- Ejecutar cada configuracion ---
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []

    for i, cfg in enumerate(configs, start=1):
        label = build_config_label(cfg)
        print(f"[{i}/{len(configs)}] {label}")

        engines_to_run = active_engines if not args.no_ocr else ["none"]
        print(f"    [OCR: {', '.join(engines_to_run)}]")

        if engines_to_run == ["none"]:
            cfg_summaries = run_config(
                cfg,
                image_paths,
                ["none"],
                {},
                args.output_dir,
                resume=args.resume,
            )
        else:
            cfg_summaries = run_config(
                cfg,
                image_paths,
                engines_to_run,
                engine_ctx,
                args.output_dir,
                resume=args.resume,
            )

        for summary in cfg_summaries:
            summaries.append(summary)
            print(
                f"      -> [{summary.get('ocr_engine', 'none')}] "
                f"chars={summary['total_chars']}, words={summary['total_words']}, "
                f"dups={summary['total_duplicates']}, score={summary['ocr_score']:.1f}"
            )
        print()



if __name__ == "__main__":
    main()
