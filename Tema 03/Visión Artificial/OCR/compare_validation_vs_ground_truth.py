"""compare_validation_vs_ground_truth.py

FASE 6 - Esqueleto inicial para comparar resultados OCR contra ground truth.

Entradas:
- validation_results/<layout_config>/results_*.json
- ground_truth/ocr_ground_truth.json

Salidas:
- ocr_gt_comparison_report.csv
- ocr_gt_comparison_report.json
- ocr_gt_comparison_report.txt
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List


HERE = Path(__file__).parent
DEFAULT_VALIDATION_DIR = HERE / "validation_results"
DEFAULT_GT_PATH = HERE / "ground_truth" / "ocr_ground_truth.json"
DEFAULT_REPORT_JSON = HERE / "ocr_gt_comparison_report.json"
DEFAULT_REPORT_CSV = HERE / "ocr_gt_comparison_report.csv"
DEFAULT_REPORT_TXT = HERE / "ocr_gt_comparison_report.txt"

CONTENT_CER_WEIGHT = 0.6
CONTENT_WER_WEIGHT = 0.4
REORDER_THRESHOLD = 0.05


def normalize_text(text: str) -> str:
    """Normaliza espacios y saltos de linea para comparacion."""
    lines = [ln.strip() for ln in text.replace("\r", "").split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def tokenize_for_comparison(text: str) -> List[str]:
    """Tokeniza de forma robusta para comparar contenido y orden."""
    normalized = normalize_text(text).lower()
    return re.findall(r"\w+", normalized, flags=re.UNICODE)


def canonicalize_text_for_content(text: str) -> str:
    """Reordena tokens alfabeticamente para medir contenido sin depender del orden."""
    tokens = tokenize_for_comparison(text)
    if not tokens:
        return ""
    return " ".join(sorted(tokens))


def levenshtein_distance(a: str, b: str) -> int:
    """Distancia de Levenshtein para CER/WER."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + cost,
            ))
        prev = curr
    return prev[-1]


def cer(pred: str, gt: str) -> float:
    """Character Error Rate."""
    gt_n = normalize_text(gt)
    pred_n = normalize_text(pred)
    if not gt_n:
        return 0.0 if not pred_n else 1.0
    return levenshtein_distance(pred_n, gt_n) / max(1, len(gt_n))


def wer(pred: str, gt: str) -> float:
    """Word Error Rate."""
    gt_tokens = normalize_text(gt).split()
    pred_tokens = normalize_text(pred).split()
    if not gt_tokens:
        return 0.0 if not pred_tokens else 1.0

    # Levenshtein a nivel token
    prev = list(range(len(gt_tokens) + 1))
    for i, p in enumerate(pred_tokens, start=1):
        curr = [i]
        for j, g in enumerate(gt_tokens, start=1):
            cost = 0 if p == g else 1
            curr.append(min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + cost,
            ))
        prev = curr
    return prev[-1] / max(1, len(gt_tokens))


def _lcs_length(seq_a: List[str], seq_b: List[str]) -> int:
    """Longest Common Subsequence para medir similitud de orden."""
    if not seq_a or not seq_b:
        return 0

    prev = [0] * (len(seq_b) + 1)
    for token_a in seq_a:
        curr = [0]
        for j, token_b in enumerate(seq_b, start=1):
            if token_a == token_b:
                curr.append(prev[j - 1] + 1)
            else:
                curr.append(max(prev[j], curr[j - 1]))
        prev = curr
    return prev[-1]


def ordering_disorder(pred: str, gt: str) -> float:
    """Mide cuanto desorden tiene el texto predicho respecto al ground truth.

    0.0 implica orden equivalente; 1.0 implica orden completamente incompatible
    para las palabras coincidentes.
    """
    pred_tokens = tokenize_for_comparison(pred)
    gt_tokens = tokenize_for_comparison(gt)

    if not pred_tokens and not gt_tokens:
        return 0.0
    if not pred_tokens or not gt_tokens:
        return 1.0

    lcs = _lcs_length(pred_tokens, gt_tokens)
    max_len = max(1, min(len(pred_tokens), len(gt_tokens)))
    return 1.0 - (lcs / max_len)


def content_accuracy(cer_content: float, wer_content: float) -> float:
    """Accuracy priorizando contenido, en escala 0..1."""
    weighted_error = (
        cer_content * CONTENT_CER_WEIGHT
        + wer_content * CONTENT_WER_WEIGHT
    )
    return max(0.0, min(1.0, 1.0 - weighted_error))


def needs_reorder(disorder: float, cer_raw: float, cer_content: float, wer_raw: float, wer_content: float) -> bool:
    """Detecta si el contenido parece correcto pero el orden requiere correccion."""
    raw_error = (cer_raw + wer_raw) / 2.0
    content_error = (cer_content + wer_content) / 2.0
    return disorder >= REORDER_THRESHOLD and content_error < raw_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compara validation_results contra ground truth (CER/WER).")
    parser.add_argument("--validation-dir", type=Path, default=DEFAULT_VALIDATION_DIR)
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GT_PATH)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_REPORT_CSV)
    parser.add_argument("--out-txt", type=Path, default=DEFAULT_REPORT_TXT)
    return parser.parse_args()


def load_ground_truth(path: Path) -> Dict[str, Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def reconstruct_text(per_region: List[Dict[str, Any]]) -> str:
    """Concatena texto OCR por region en orden."""
    chunks: List[str] = []
    for region in per_region:
        text = str(region.get("text", "")).strip()
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def build_rows(validation_dir: Path, gt_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    result_files: List[Path] = []

    for config_dir in sorted(validation_dir.iterdir()):
        if not config_dir.is_dir():
            continue
        result_files.extend(sorted(config_dir.glob("results_*.json")))

    total_files = len(result_files)
    processed_files = 0
    processed_images = 0

    if total_files == 0:
        print(f"[WARN] No se encontraron archivos results_*.json en {validation_dir}")
        return rows

    print(f"[i] Archivos de resultados encontrados: {total_files}")

    for result_file in result_files:
        processed_files += 1
        print(f"[i] Leyendo {processed_files}/{total_files}: {result_file.parent.name}/{result_file.name}", flush=True)

        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)

        label = data.get("label", result_file.parent.name)
        ocr_engine = data.get("ocr_engine") or result_file.stem.replace("results_", "")
        per_image = data.get("per_image", {})
        total_images = len(per_image)

        for image_index, (image_name, image_data) in enumerate(per_image.items(), start=1):
            processed_images += 1
            print(
                f"    [img {image_index}/{total_images}] {image_name} "
                f"(total procesadas: {processed_images})",
                flush=True,
            )
            gt_text = str(gt_data.get(image_name, {}).get("text", ""))
            pred_text = reconstruct_text(image_data.get("per_region", []))
            pred_content_text = canonicalize_text_for_content(pred_text)
            gt_content_text = canonicalize_text_for_content(gt_text)

            cer_raw = cer(pred_text, gt_text)
            wer_raw = wer(pred_text, gt_text)
            cer_content = cer(pred_content_text, gt_content_text)
            wer_content = wer(pred_content_text, gt_content_text)
            disorder = ordering_disorder(pred_text, gt_text)
            content_acc = content_accuracy(cer_content, wer_content)
            reorder_needed = needs_reorder(
                disorder,
                cer_raw,
                cer_content,
                wer_raw,
                wer_content,
            )
            time_per_image_ms = float(image_data.get("det_ms", 0.0)) + float(image_data.get("ocr_ms", 0.0))
            duplicates = int(image_data.get("duplicates", 0))

            row = {
                "layout_config": label,
                "ocr_engine": ocr_engine,
                "image": image_name,
                "cer_raw": round(cer_raw, 6),
                "wer_raw": round(wer_raw, 6),
                "cer_content": round(cer_content, 6),
                "wer_content": round(wer_content, 6),
                "content_accuracy": round(content_acc, 6),
                "disorder": round(disorder, 6),
                "needs_reorder": reorder_needed,
                "reorder_status": "requires_reorder" if reorder_needed else "ordered",
                "time_per_image_ms": time_per_image_ms,
                "duplicates": duplicates,
                "chars_pred": int(image_data.get("total_chars", 0)),
                "words_pred": int(image_data.get("total_words", 0)),
            }
            rows.append(row)

    print(f"[OK] Comparaciones por imagen generadas: {len(rows)}")

    return rows


def aggregate_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrega por layout_config + ocr_engine."""
    grouped: Dict[str, Dict[str, Any]] = {}

    print(f"[i] Agregando {len(rows)} comparaciones por imagen...", flush=True)

    for row in rows:
        key = f"{row['layout_config']}||{row['ocr_engine']}"
        if key not in grouped:
            grouped[key] = {
                "layout_config": row["layout_config"],
                "ocr_engine": row["ocr_engine"],
                "n_images": 0,
                "cer_raw_sum": 0.0,
                "wer_raw_sum": 0.0,
                "cer_content_sum": 0.0,
                "wer_content_sum": 0.0,
                "content_accuracy_sum": 0.0,
                "disorder_sum": 0.0,
                "time_sum": 0.0,
                "dup_sum": 0,
                "reorder_count": 0,
            }

        g = grouped[key]
        g["n_images"] += 1
        g["cer_raw_sum"] += float(row["cer_raw"])
        g["wer_raw_sum"] += float(row["wer_raw"])
        g["cer_content_sum"] += float(row["cer_content"])
        g["wer_content_sum"] += float(row["wer_content"])
        g["content_accuracy_sum"] += float(row["content_accuracy"])
        g["disorder_sum"] += float(row["disorder"])
        g["time_sum"] += float(row["time_per_image_ms"])
        g["dup_sum"] += int(row["duplicates"])
        if bool(row["needs_reorder"]):
            g["reorder_count"] += 1

    out: List[Dict[str, Any]] = []
    for g in grouped.values():
        n = max(1, g["n_images"])
        cer_raw_mean = g["cer_raw_sum"] / n
        wer_raw_mean = g["wer_raw_sum"] / n
        cer_content_mean = g["cer_content_sum"] / n
        wer_content_mean = g["wer_content_sum"] / n
        content_accuracy_mean = g["content_accuracy_sum"] / n
        disorder_mean = g["disorder_sum"] / n
        time_mean = g["time_sum"] / n
        dup_mean = g["dup_sum"] / n
        reorder_ratio = g["reorder_count"] / n

        out.append({
            "layout_config": g["layout_config"],
            "ocr_engine": g["ocr_engine"],
            "n_images": g["n_images"],
            "cer_raw": round(cer_raw_mean, 6),
            "wer_raw": round(wer_raw_mean, 6),
            "cer_content": round(cer_content_mean, 6),
            "wer_content": round(wer_content_mean, 6),
            "content_accuracy": round(content_accuracy_mean, 6),
            "disorder": round(disorder_mean, 6),
            "images_requiring_reorder": g["reorder_count"],
            "reorder_ratio": round(reorder_ratio, 6),
            "time_per_image_ms": round(time_mean, 2),
            "dup_mean": round(dup_mean, 4),
        })

    out.sort(key=lambda x: x["content_accuracy"], reverse=True)
    print(f"[OK] Comparativas agregadas: {len(out)}")
    return out


def write_outputs(rows: List[Dict[str, Any]], aggregate: List[Dict[str, Any]], out_json: Path, out_csv: Path, out_txt: Path) -> None:
    print("[i] Escribiendo salidas...", flush=True)
    payload = {
        "per_image": rows,
        "aggregate": aggregate,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        if aggregate:
            writer = csv.DictWriter(f, fieldnames=list(aggregate[0].keys()))
            writer.writeheader()
            writer.writerows(aggregate)

    lines: List[str] = []
    lines.append("COMPARATIVA OCR VS GROUND TRUTH")
    lines.append("=" * 90)
    if not aggregate:
        lines.append("No hay datos para comparar. Revisa validation_results y ground_truth.")
    else:
        for idx, row in enumerate(aggregate, start=1):
            lines.append(
                f"#{idx} {row['layout_config']} | {row['ocr_engine']} | "
                f"CERraw={row['cer_raw']:.4f} WERraw={row['wer_raw']:.4f} "
                f"CERcontent={row['cer_content']:.4f} WERcontent={row['wer_content']:.4f} "
                f"AccContent={row['content_accuracy']*100:.2f}% Disorder={row['disorder']:.4f} "
                f"Reorder={row['images_requiring_reorder']}/{row['n_images']} "
                f"Time={row['time_per_image_ms']:.1f}ms Dup={row['dup_mean']:.2f} "
                f"RankingMetric=AccContent"
            )
    lines.append("")

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    args = parse_args()

    if not args.validation_dir.exists():
        raise SystemExit(f"[ERROR] No existe validation dir: {args.validation_dir}")
    if not args.ground_truth.exists():
        raise SystemExit(f"[ERROR] No existe ground truth: {args.ground_truth}")

    print(f"[i] Validation dir: {args.validation_dir}")
    print(f"[i] Ground truth:   {args.ground_truth}")
    print("[i] Cargando ground truth...", flush=True)
    gt_data = load_ground_truth(args.ground_truth)
    print(f"[OK] Entradas de ground truth: {len(gt_data)}")

    rows = build_rows(args.validation_dir, gt_data)
    aggregate = aggregate_rows(rows)
    write_outputs(rows, aggregate, args.out_json, args.out_csv, args.out_txt)

    print(f"[OK] Reporte JSON: {args.out_json}")
    print(f"[OK] Reporte CSV:  {args.out_csv}")
    print(f"[OK] Reporte TXT:  {args.out_txt}")
    if aggregate:
        top = aggregate[0]
        print(
            "[TOP] "
            f"{top['layout_config']} + {top['ocr_engine']} "
            f"(AccContent={top['content_accuracy']*100:.2f}%, Reorder={top['images_requiring_reorder']}/{top['n_images']}, "
            f"Disorder={top['disorder']:.4f})"
        )


if __name__ == "__main__":
    main()
