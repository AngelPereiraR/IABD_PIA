"""
validate_18_popurris.py

Script para validar la detección de columnas en las 18 imágenes de popurrís
usando DocLayout-YOLO. Procesa todas las imágenes popurri01.jpg - popurri18.jpg
y guarda los resultados en un archivo JSON con métricas y estadísticas.

Uso:
    python validate_18_popurris.py
    python validate_18_popurris.py --method doclayout --conf 0.3
    python validate_18_popurris.py --method opencv
"""
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from detect_columns import load_image, detect_columns


def validate_popurris(
    imgs_dir: str = "imgs",
    method: str = "doclayout",
    doclayout_conf: float = 0.25,
    model_path: str = None
) -> Dict[str, Any]:
    """Valida la detección en las 18 imágenes de popurrís.
    
    Returns:
        Diccionario con resultados y estadísticas
    """
    imgs_path = Path(imgs_dir)
    if not imgs_path.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {imgs_dir}")
    
    # Buscar todas las imágenes popurri##.jpg
    popurri_images = sorted(imgs_path.glob("popurri*.jpg"))
    
    if not popurri_images:
        raise FileNotFoundError(f"No se encontraron imágenes popurri*.jpg en {imgs_dir}")
    
    print("=" * 80)
    print(f"VALIDACIÓN DE DETECCIÓN DE COLUMNAS - Método: {method.upper()}")
    print("=" * 80)
    print(f"Directorio: {imgs_dir}")
    print(f"Imágenes encontradas: {len(popurri_images)}\n")
    
    results: List[Dict[str, Any]] = []
    total_columns = 0
    total_time = 0.0
    errors = []
    
    for i, img_path in enumerate(popurri_images, start=1):
        print(f"[{i}/{len(popurri_images)}] Procesando: {img_path.name}")
        
        try:
            # Cargar imagen
            t0 = time.time()
            img = load_image(str(img_path))
            load_time = time.time() - t0
            
            # Detectar columnas
            t0 = time.time()
            (w, h), boxes = detect_columns(
                img,
                method=method,
                debug=False,
                doclayout_conf=doclayout_conf,
                model_path=model_path
            )
            detect_time = time.time() - t0
            
            num_columns = len(boxes)
            total_columns += num_columns
            total_time += detect_time
            
            # Extraer información de las columnas
            columns_info = []
            for j, box in enumerate(boxes, start=1):
                col_width = box.x2 - box.x1
                col_height = box.y2 - box.y1
                col_area = col_width * col_height
                
                columns_info.append({
                    "column_id": j,
                    "bbox": [box.x1, box.y1, box.x2, box.y2],
                    "width": col_width,
                    "height": col_height,
                    "area": col_area,
                    "confidence": box.confidence
                })
            
            # Guardar resultado de esta imagen
            result = {
                "image": img_path.name,
                "image_width": w,
                "image_height": h,
                "load_time_seconds": load_time,
                "detect_time_seconds": detect_time,
                "num_columns": num_columns,
                "columns": columns_info
            }
            results.append(result)
            
            print(f"  ✅ {num_columns} columnas detectadas en {detect_time:.3f}s")
            
        except Exception as e:
            error_msg = f"Error procesando {img_path.name}: {str(e)}"
            print(f"  ❌ {error_msg}")
            errors.append({
                "image": img_path.name,
                "error": str(e)
            })
    
    # Calcular estadísticas
    if results:
        detection_times = [r["detect_time_seconds"] for r in results]
        num_columns_list = [r["num_columns"] for r in results]
        
        stats = {
            "num_images_processed": len(results),
            "num_images_with_errors": len(errors),
            "total_columns_detected": total_columns,
            "avg_columns_per_image": total_columns / len(results),
            "min_columns": min(num_columns_list),
            "max_columns": max(num_columns_list),
            "avg_detection_time_seconds": sum(detection_times) / len(detection_times),
            "min_detection_time_seconds": min(detection_times),
            "max_detection_time_seconds": max(detection_times),
            "total_processing_time_seconds": sum(detection_times)
        }
    else:
        stats = {
            "num_images_processed": 0,
            "num_images_with_errors": len(errors),
            "total_columns_detected": 0
        }
    
    # Resultados finales
    validation_results = {
        "method": method,
        "doclayout_conf_threshold": doclayout_conf if method in ("doclayout", "yolo") else None,
        "images_dir": str(imgs_dir),
        "statistics": stats,
        "results": results,
        "errors": errors
    }
    
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS")
    print("=" * 80)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} imagen(es) con errores")
    
    return validation_results


def main():
    parser = argparse.ArgumentParser(
        description="Valida la detección de columnas en las 18 imágenes de popurrís"
    )
    parser.add_argument(
        "--imgs-dir",
        default="imgs",
        help="Directorio con las imágenes popurri*.jpg (default: imgs)"
    )
    parser.add_argument(
        "--method",
        default="doclayout",
        choices=["opencv", "doclayout", "yolo"],
        help="Método de detección (default: doclayout)"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Umbral de confianza para DocLayout-YOLO (default: 0.25)"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Ruta personalizada al modelo DocLayout-YOLO"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Archivo de salida JSON (default: build/validacion_popurris_YYYYMMDD-HHMM.json)"
    )
    args = parser.parse_args()
    
    # Validar
    results = validate_popurris(
        imgs_dir=args.imgs_dir,
        method=args.method,
        doclayout_conf=args.conf,
        model_path=args.model_path
    )
    
    # Guardar resultados en build/ por defecto
    if args.output is None:
        script_dir = Path(__file__).parent
        build_dir = script_dir / "build"
        build_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        output_path = build_dir / f"validacion_popurris_{timestamp}.json"
    else:
        output_path = Path(args.output)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ Resultados guardados en: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
