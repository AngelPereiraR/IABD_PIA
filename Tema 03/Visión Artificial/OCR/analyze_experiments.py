"""analyze_experiments.py

Análisis estadístico de los resultados del grid search (FASE 3).

Lee el JSON generado por experiment_models.py y produce:
  - experiment_ranking.csv   — ranking completo de configuraciones
  - experiment_top.txt       — top-10 por método con detalle
  - Imprime p-values básicos para la selección de parámetros óptimos

Uso:
    py -3.11 analyze_experiments.py
    py -3.11 analyze_experiments.py --input experiment_results.json
    py -3.11 analyze_experiments.py --top 5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- pandas es obligatorio para el análisis ---
try:
    import pandas as pd
except ImportError:
    sys.exit("[ERROR] pandas no instalado. Ejecuta: pip install pandas")

# --- numpy para estadísticas, opcional pero deseable ---
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("[WARN] numpy no encontrado; algunas estadísticas se omitirán.")

# Rutas por defecto (misma carpeta que este script)
DEFAULT_INPUT = Path(__file__).parent / "experiment_results.json"
DEFAULT_RANKING = Path(__file__).parent / "experiment_ranking.csv"
DEFAULT_TOP = Path(__file__).parent / "experiment_top.txt"

COVERAGE_WEIGHT = 100.0
OVERLAP_PENALTY = 35.0
EMPTY_PENALTY = 20.0
TINY_PENALTY = 10.0
DUPLICATE_PENALTY = 4.0


# ============================================================================
# Carga y aplanado del JSON
# ============================================================================

def load_results(json_path: Path) -> pd.DataFrame:
    """Carga experiment_results.json y devuelve un DataFrame aplanado.

    Estructura por fila:
        experiment_id, image, method, conf (None para paddleocr/docling),
        nms_iou, merge_distance, success, num_boxes, avg_area, duplicates,
        text_coverage, overlap_ratio, empty_boxes, empty_ratio,
        tiny_boxes, tiny_ratio, time_ms, error
    """
    with open(json_path, encoding="utf-8") as f:
        raw: List[Dict[str, Any]] = json.load(f)

    rows = []
    for r in raw:
        # Aplanado manual — pd.json_normalize aplanarĺa config con prefijo
        cfg = r["config"]
        mts = r["metrics"]
        rows.append(
            {
                "experiment_id": r.get("experiment_id"),
                "image": r["image"],
                "method": r["method"],
                # conf es None para paddleocr/docling (no tienen umbral configurable)
                "conf": cfg.get("conf"),          # float o None
                "nms_iou": cfg.get("nms_iou"),   # None para opencv (sin nms_iou configurable)
                "merge_distance": cfg["merge_distance"],
                "success": mts.get("success", False),
                "num_boxes": mts.get("num_boxes", 0),
                "avg_area": mts.get("avg_area", 0.0),
                "duplicates": mts.get("duplicates", 0),
                "text_coverage": mts.get("text_coverage"),
                "overlap_ratio": mts.get("overlap_ratio"),
                "empty_boxes": mts.get("empty_boxes"),
                "empty_ratio": mts.get("empty_ratio"),
                "tiny_boxes": mts.get("tiny_boxes"),
                "tiny_ratio": mts.get("tiny_ratio"),
                "time_ms": mts.get("time_ms", 0.0),
                "error": mts.get("error"),
            }
        )

    df = pd.DataFrame(rows)

    # Conversión de tipos
    df["conf"]    = pd.to_numeric(df["conf"],    errors="coerce")  # NaN para paddleocr/docling
    df["nms_iou"] = pd.to_numeric(df["nms_iou"], errors="coerce")  # NaN para opencv
    df["num_boxes"] = df["num_boxes"].astype(int)
    df["duplicates"] = df["duplicates"].astype(int)
    df["merge_distance"] = df["merge_distance"].astype(int)
    df["text_coverage"] = pd.to_numeric(df["text_coverage"], errors="coerce")
    df["overlap_ratio"] = pd.to_numeric(df["overlap_ratio"], errors="coerce")
    df["empty_boxes"] = pd.to_numeric(df["empty_boxes"], errors="coerce").fillna(0).astype(int)
    df["empty_ratio"] = pd.to_numeric(df["empty_ratio"], errors="coerce")
    df["tiny_boxes"] = pd.to_numeric(df["tiny_boxes"], errors="coerce").fillna(0).astype(int)
    df["tiny_ratio"] = pd.to_numeric(df["tiny_ratio"], errors="coerce")

    return df


# ============================================================================
# Cálculo del ranking
# ============================================================================

def score_formula(row: "pd.Series") -> float:
    """Heurística de puntuación por configuración.

    Objetivo:
        - Priorizar recuperar la máxima cantidad posible de texto visible.
        - Penalizar solapamiento redundante entre cajas sobre el contenido.
        - Penalizar cajas vacías o muy pequeñas (basura / fragmentación).
        - Penalizar duplicados residuales.

    La cobertura domina la puntuación; el resto de términos son penalizaciones.
    """
    score = row["mean_text_coverage"] * COVERAGE_WEIGHT
    score -= row["mean_overlap_ratio"] * OVERLAP_PENALTY
    score -= row["mean_empty_ratio"] * EMPTY_PENALTY
    score -= row["mean_tiny_ratio"] * TINY_PENALTY
    score -= row["mean_duplicates"] * DUPLICATE_PENALTY
    return max(0.0, min(100.0, score))


def build_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa por (method, conf, nms_iou, merge_distance) y calcula métricas.

    NOTA: dropna=False es necesario para que las filas de paddleocr/docling
    (donde conf=NaN) no se descarten en el groupby.
    """
    only_success = df[df["success"]].copy()

    required_metrics = ["text_coverage", "overlap_ratio", "empty_ratio", "tiny_ratio"]
    missing_metrics = [metric for metric in required_metrics if only_success[metric].isna().any()]
    if missing_metrics:
        sys.exit(
            "[ERROR] experiment_results.json no contiene las nuevas métricas de layout "
            f"{missing_metrics}. Regenera los experimentos con experiment_models.py antes de analizar."
        )

    grouped = (
        only_success
        .groupby(["method", "conf", "nms_iou", "merge_distance"], dropna=False)
        .agg(
            n_images=("image", "nunique"),
            mean_boxes=("num_boxes", "mean"),
            std_boxes=("num_boxes", "std"),
            median_boxes=("num_boxes", "median"),
            mean_area=("avg_area", "mean"),
            mean_text_coverage=("text_coverage", "mean"),
            mean_overlap_ratio=("overlap_ratio", "mean"),
            mean_empty_boxes=("empty_boxes", "mean"),
            mean_empty_ratio=("empty_ratio", "mean"),
            mean_tiny_boxes=("tiny_boxes", "mean"),
            mean_tiny_ratio=("tiny_ratio", "mean"),
            mean_duplicates=("duplicates", "mean"),
            total_duplicates=("duplicates", "sum"),
            mean_time_ms=("time_ms", "mean"),
        )
        .reset_index()
    )

    grouped["score"] = grouped.apply(score_formula, axis=1)
    grouped = grouped.sort_values("score", ascending=False).reset_index(drop=True)
    grouped.index += 1  # ranking 1-based
    return grouped


# ============================================================================
# Top-N por método
# ============================================================================

def top_n_per_method(ranking: pd.DataFrame, n: int = 10) -> Dict[str, pd.DataFrame]:
    """Devuelve los top-n items para cada método."""
    result = {}
    for method, group in ranking.groupby("method"):
        result[method] = group.head(n).copy()
    return result


# ============================================================================
# Informe de texto
# ============================================================================

def format_top_report(top: Dict[str, pd.DataFrame]) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("  INFORME TOP CONFIGURACIONES POR MÉTODO")
    lines.append("=" * 72)

    for method, df in top.items():
        lines.append(f"\n── {method.upper()} ──────────────────────────────────────")
        lines.append(
            f"{'Pos':>4}  {'conf':>6}  {'nms':>5}  {'merge':>5}  "
            f"{'cov%':>6}  {'ovl%':>6}  {'empty%':>6}  {'dups':>5}  {'score':>8}"
        )
        lines.append("-" * 78)
        for pos, row in df.iterrows():
            conf_str = f"{row['conf']:.2f}" if pd.notna(row["conf"]) else "N/A  "
            nms_str  = f"{row['nms_iou']:.2f}" if pd.notna(row["nms_iou"]) else "N/A "
            lines.append(
                f"{pos:>4}  {conf_str:>6}  {nms_str:>5}  "
                f"{int(row['merge_distance']):>5d}  "
                f"{row['mean_text_coverage']*100:>5.1f}%  "
                f"{row['mean_overlap_ratio']*100:>5.1f}%  "
                f"{row['mean_empty_ratio']*100:>5.1f}%  "
                f"{row['mean_duplicates']:>5.2f}  "
                f"{row['score']:>8.2f}"
            )
    lines.append("\n" + "=" * 72)
    return "\n".join(lines)


# ============================================================================
# Estadísticas de sensibilidad de parámetros
# ============================================================================

def print_sensitivity(df: pd.DataFrame) -> None:
    """Imprime la varianza de num_boxes al variar cada parámetro."""
    print("\n── Sensibilidad paramétrica (varianza de num_boxes) ──────────────")
    for param in ["conf", "nms_iou", "merge_distance"]:
        try:
            variances = (
                df[df["success"]]
                .groupby(["method", param], dropna=False)["num_boxes"]
                .mean()
                .groupby(level=0)
                .var()
            )
            print(f"  {param:15s}: varianza media intra-método = {variances.mean():.2f}")
        except Exception as exc:
            print(f"  {param:15s}: no disponible ({exc})")


# ============================================================================
# Main
# ============================================================================

def analyze(
    input_file: Path = DEFAULT_INPUT,
    ranking_file: Path = DEFAULT_RANKING,
    top_file: Path = DEFAULT_TOP,
    top_n: int = 10,
) -> pd.DataFrame:
    """Pipeline completo de análisis."""

    if not input_file.exists():
        sys.exit(f"[ERROR] No se encontró '{input_file}'. ¿Ejecutaste experiment_models.py?")

    print(f"Cargando resultados desde {input_file}...")
    df = load_results(input_file)

    total = len(df)
    failed = (~df["success"]).sum()
    methods = df["method"].unique().tolist()
    print(f"  Total filas: {total}  |  Fallidas: {failed}  |  Métodos: {methods}")

    # ── Ranking ──────────────────────────────────────────────────────────────
    ranking = build_ranking(df)
    ranking.to_csv(ranking_file, index_label="rank", float_format="%.2f")
    print(f"\nRanking guardado en {ranking_file}  ({len(ranking)} configs)")

    # ── Top-N por método ──────────────────────────────────────────────────────
    top = top_n_per_method(ranking, n=top_n)
    report = format_top_report(top)
    print(report)
    top_file.write_text(report, encoding="utf-8")
    print(f"Informe top-{top_n} guardado en {top_file}")

    # ── Sensibilidad ──────────────────────────────────────────────────────────
    print_sensitivity(df)

    return ranking


# ============================================================================
# CLI
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Análisis de resultados del grid search FASE 3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "\nEjemplos:\n"
            "  py -3.11 analyze_experiments.py\n"
            "  py -3.11 analyze_experiments.py --input experiment_results.json --top 5\n"
        ),
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"Archivo JSON de entrada (default: {DEFAULT_INPUT.name})",
    )
    parser.add_argument(
        "--ranking-output",
        default=str(DEFAULT_RANKING),
        help=f"CSV de ranking (default: {DEFAULT_RANKING.name})",
    )
    parser.add_argument(
        "--top-output",
        default=str(DEFAULT_TOP),
        help=f"TXT de top-N (default: {DEFAULT_TOP.name})",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Número de configuraciones top a mostrar por método (default: 10)",
    )
    args = parser.parse_args()

    analyze(
        input_file=Path(args.input),
        ranking_file=Path(args.ranking_output),
        top_file=Path(args.top_output),
        top_n=args.top,
    )


if __name__ == "__main__":
    main()
