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
from pathlib import Path
from typing import Any, Dict, List


HERE = Path(__file__).parent
DEFAULT_VALIDATION_DIR = HERE / "validation_results"
DEFAULT_GT_PATH = HERE / "ground_truth" / "ocr_ground_truth.json"
DEFAULT_REPORT_JSON = HERE / "ocr_gt_comparison_report.json"
DEFAULT_REPORT_CSV = HERE / "ocr_gt_comparison_report.csv"
DEFAULT_REPORT_TXT = HERE / "ocr_gt_comparison_report.txt"


def normalize_text(text: str) -> str:
    """Normaliza espacios y saltos de linea para comparacion."""
    lines = [ln.strip() for ln in text.replace("\r", "").split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


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

    for config_dir in sorted(validation_dir.iterdir()):
        if not config_dir.is_dir():
            continue

        for result_file in sorted(config_dir.glob("results_*.json")):
            with open(result_file, encoding="utf-8") as f:
                data = json.load(f)

            label = data.get("label", config_dir.name)
            ocr_engine = data.get("ocr_engine") or result_file.stem.replace("results_", "")
            per_image = data.get("per_image", {})

            for image_name, image_data in per_image.items():
                gt_text = str(gt_data.get(image_name, {}).get("text", ""))
                pred_text = reconstruct_text(image_data.get("per_region", []))

                row = {
                    "layout_config": label,
                    "ocr_engine": ocr_engine,
                    "image": image_name,
                    "cer": round(cer(pred_text, gt_text), 6),
                    "wer": round(wer(pred_text, gt_text), 6),
                    "time_per_image_ms": float(image_data.get("det_ms", 0.0)) + float(image_data.get("ocr_ms", 0.0)),
                    "duplicates": int(image_data.get("duplicates", 0)),
                    "chars_pred": int(image_data.get("total_chars", 0)),
                    "words_pred": int(image_data.get("total_words", 0)),
                }
                rows.append(row)

    return rows


def aggregate_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrega por layout_config + ocr_engine."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        key = f"{row['layout_config']}||{row['ocr_engine']}"
        if key not in grouped:
            grouped[key] = {
                "layout_config": row["layout_config"],
                "ocr_engine": row["ocr_engine"],
                "n_images": 0,
                "cer_sum": 0.0,
                "wer_sum": 0.0,
                "time_sum": 0.0,
                "dup_sum": 0,
            }

        g = grouped[key]
        g["n_images"] += 1
        g["cer_sum"] += float(row["cer"])
        g["wer_sum"] += float(row["wer"])
        g["time_sum"] += float(row["time_per_image_ms"])
        g["dup_sum"] += int(row["duplicates"])

    out: List[Dict[str, Any]] = []
    for g in grouped.values():
        n = max(1, g["n_images"])
        cer_mean = g["cer_sum"] / n
        wer_mean = g["wer_sum"] / n
        time_mean = g["time_sum"] / n
        dup_mean = g["dup_sum"] / n
        score = (1 - cer_mean) * 50 + (1 - wer_mean) * 35 - (time_mean / 1000) * 10 - dup_mean * 5

        out.append({
            "layout_config": g["layout_config"],
            "ocr_engine": g["ocr_engine"],
            "n_images": g["n_images"],
            "cer": round(cer_mean, 6),
            "wer": round(wer_mean, 6),
            "time_per_image_ms": round(time_mean, 2),
            "dup_mean": round(dup_mean, 4),
            "score": round(score, 4),
        })

    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def write_outputs(rows: List[Dict[str, Any]], aggregate: List[Dict[str, Any]], out_json: Path, out_csv: Path, out_txt: Path) -> None:
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
                f"CER={row['cer']:.4f} WER={row['wer']:.4f} "
                f"Time={row['time_per_image_ms']:.1f}ms Dup={row['dup_mean']:.2f} Score={row['score']:.2f}"
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

    gt_data = load_ground_truth(args.ground_truth)
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
            f"(CER={top['cer']:.4f}, WER={top['wer']:.4f}, SCORE={top['score']:.2f})"
        )


if __name__ == "__main__":
    main()
