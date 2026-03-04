"""
benchmark_methods.py

Compara el rendimiento de OpenCV vs DocLayout-YOLO para la detección de columnas.
Procesa las primeras N imágenes de popurrí y genera estadísticas comparativas.

Uso:
    python benchmark_methods.py
    python benchmark_methods.py --num-images 10
    python benchmark_methods.py --conf 0.3
"""
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

from detect_columns import load_image, detect_columns, ColumnBox
import numpy as np
import cv2


def create_comparison_image(
    img: np.ndarray,
    methods_results: Dict[str, Any],
    methods: List[str]
) -> np.ndarray:
    """Crea una imagen comparativa con los boxes detectados por cada método.
    
    Args:
        img: Imagen original BGR de OpenCV
        methods_results: Diccionario con resultados de cada método
        methods: Lista de nombres de métodos (en orden: izquierda a derecha)
    
    Returns:
        Imagen concatenada horizontalmente con visualizaciones
    """
    vis_images = []
    colors = {
        "opencv": (0, 255, 0),      # Verde
        "doclayout": (0, 165, 255),  # Naranja
        "yolo": (0, 165, 255)        # Naranja (alias)
    }
    
    for method in methods:
        # Crear copia de la imagen para dibujar
        vis = img.copy()
        
        result = methods_results.get(method, {})
        if result.get("success", False) and "columns" in result:
            boxes = result["columns"]
            color = colors.get(method, (255, 255, 255))
            
            # Dibujar cada box
            for i, box_data in enumerate(boxes, start=1):
                bbox = box_data["bbox"]
                x1, y1, x2, y2 = bbox
                conf = box_data.get("confidence", 0.0)
                
                # Dibujar rectángulo
                cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
                
                # Texto con número y confianza
                text = f"{i} ({conf:.2f})"
                cv2.putText(
                    vis, text, (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                )
        
        # Añadir título del método en la parte superior
        h, w = vis.shape[:2]
        title = method.upper()
        num_cols = result.get("num_columns", 0) if result.get("success", False) else 0
        time_taken = result.get("detect_time_seconds", 0.0) if result.get("success", False) else 0.0
        
        title_text = f"{title}: {num_cols} cols - {time_taken:.3f}s"
        
        # Fondo para el texto
        (text_width, text_height), _ = cv2.getTextSize(
            title_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2
        )
        cv2.rectangle(vis, (0, 0), (text_width + 20, text_height + 20), (0, 0, 0), -1)
        
        # Texto del título
        cv2.putText(
            vis, title_text, (10, text_height + 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2
        )
        
        vis_images.append(vis)
    
    # Concatenar horizontalmente
    if len(vis_images) == 1:
        return vis_images[0]
    elif len(vis_images) == 2:
        return np.hstack(vis_images)
    else:
        # Si hay más de 2, concatenar todos horizontalmente
        return np.hstack(vis_images)


def benchmark_single_image(
    img_path: Path,
    methods: List[str],
    doclayout_conf: float = 0.25,
    model_path: str = None
) -> Dict[str, Any]:
    """Ejecuta benchmark en una sola imagen con ambos métodos.
    
    Returns:
        Diccionario con resultados de ambos métodos
    """
    print(f"\n{'='*80}")
    print(f"Imagen: {img_path.name}")
    print(f"{'='*80}")
    
    # Cargar imagen una vez
    img = load_image(str(img_path))
    h, w = img.shape[:2]
    
    results = {
        "image": img_path.name,
        "image_width": w,
        "image_height": h,
        "methods": {}
    }
    
    for method in methods:
        print(f"\n{method.upper()}:")
        
        try:
            # Medir tiempo de detección
            t0 = time.time()
            (w, h), boxes = detect_columns(
                img,
                method=method,
                debug=False,
                doclayout_conf=doclayout_conf,
                model_path=model_path
            )
            detect_time = time.time() - t0
            
            # Calcular métricas de las columnas
            num_columns = len(boxes)
            if num_columns > 0:
                widths = [b.x2 - b.x1 for b in boxes]
                heights = [b.y2 - b.y1 for b in boxes]
                areas = [(b.x2 - b.x1) * (b.y2 - b.y1) for b in boxes]
                confidences = [b.confidence for b in boxes]
                
                method_results = {
                    "success": True,
                    "detect_time_seconds": detect_time,
                    "num_columns": num_columns,
                    "columns": [
                        {
                            "bbox": [b.x1, b.y1, b.x2, b.y2],
                            "width": b.x2 - b.x1,
                            "height": b.y2 - b.y1,
                            "area": (b.x2 - b.x1) * (b.y2 - b.y1),
                            "confidence": b.confidence
                        }
                        for b in boxes
                    ],
                    "metrics": {
                        "avg_width": np.mean(widths),
                        "avg_height": np.mean(heights),
                        "avg_area": np.mean(areas),
                        "avg_confidence": np.mean(confidences),
                        "std_width": np.std(widths),
                        "std_height": np.std(heights),
                        "min_width": min(widths),
                        "max_width": max(widths),
                        "total_coverage_percent": (sum(areas) / (w * h)) * 100
                    }
                }
                
                print(f"  ✅ {num_columns} columnas en {detect_time:.3f}s")
                print(f"     Ancho promedio: {method_results['metrics']['avg_width']:.1f}px")
                print(f"     Confianza promedio: {method_results['metrics']['avg_confidence']:.3f}")
                print(f"     Cobertura: {method_results['metrics']['total_coverage_percent']:.1f}%")
            else:
                method_results = {
                    "success": True,
                    "detect_time_seconds": detect_time,
                    "num_columns": 0,
                    "columns": [],
                    "metrics": {}
                }
                print(f"  ⚠️  0 columnas detectadas en {detect_time:.3f}s")
            
        except Exception as e:
            method_results = {
                "success": False,
                "error": str(e)
            }
            print(f"  ❌ Error: {e}")
        
        results["methods"][method] = method_results
    
    # Crear imagen comparativa
    try:
        comparison_img = create_comparison_image(img, results["methods"], methods)
        
        # Guardar en build/
        script_dir = Path(__file__).parent
        build_dir = script_dir / "build"
        build_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        img_stem = img_path.stem
        comparison_filename = f"comparison_{img_stem}_{timestamp}.png"
        comparison_path = build_dir / comparison_filename
        
        cv2.imwrite(str(comparison_path), comparison_img)
        results["comparison_image"] = str(comparison_path)
        print(f"\n📸 Imagen comparativa guardada: {comparison_path}")
    except Exception as e:
        print(f"\n⚠️  No se pudo crear imagen comparativa: {e}")
        results["comparison_image"] = None
    
    return results


def compare_methods(
    imgs_dir: str = "imgs",
    num_images: int = None,
    methods: List[str] = None,
    doclayout_conf: float = 0.25,
    model_path: str = None
) -> Dict[str, Any]:
    """Compara múltiples métodos de detección.
    
    Returns:
        Diccionario con resultados comparativos
    """
    if methods is None:
        methods = ["opencv", "doclayout"]
    
    imgs_path = Path(imgs_dir)
    if not imgs_path.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {imgs_dir}")
    
    # Buscar imágenes popurri
    all_images = sorted(imgs_path.glob("popurri*.jpg"))
    popurri_images = all_images if num_images is None else all_images[:num_images]
    
    if not popurri_images:
        raise FileNotFoundError(f"No se encontraron imágenes popurri*.jpg en {imgs_dir}")
    
    print("=" * 80)
    print(f"BENCHMARK: COMPARACIÓN DE MÉTODOS")
    print("=" * 80)
    print(f"Métodos: {', '.join(m.upper() for m in methods)}")
    print(f"Imágenes a procesar: {len(popurri_images)}")
    print(f"Directorio: {imgs_dir}\n")
    
    all_results = []
    
    for img_path in popurri_images:
        result = benchmark_single_image(
            img_path,
            methods=methods,
            doclayout_conf=doclayout_conf,
            model_path=model_path
        )
        all_results.append(result)
    
    # Calcular estadísticas agregadas por método
    aggregated_stats = {}
    
    for method in methods:
        method_data = []
        times = []
        columns = []
        
        for result in all_results:
            if method in result["methods"]:
                method_result = result["methods"][method]
                if method_result.get("success", False):
                    times.append(method_result["detect_time_seconds"])
                    columns.append(method_result["num_columns"])
                    method_data.append(method_result)
        
        if times:
            aggregated_stats[method] = {
                "num_images_processed": len(times),
                "avg_time_seconds": np.mean(times),
                "std_time_seconds": np.std(times),
                "min_time_seconds": min(times),
                "max_time_seconds": max(times),
                "total_time_seconds": sum(times),
                "avg_columns": np.mean(columns),
                "std_columns": np.std(columns),
                "min_columns": min(columns),
                "max_columns": max(columns),
                "total_columns": sum(columns)
            }
        else:
            aggregated_stats[method] = {
                "num_images_processed": 0,
                "error": "No se pudieron procesar imágenes"
            }
    
    # Resultados finales
    benchmark_results = {
        "methods_compared": methods,
        "num_images": len(popurri_images),
        "doclayout_conf_threshold": doclayout_conf,
        "images_dir": str(imgs_dir),
        "aggregated_statistics": aggregated_stats,
        "detailed_results": all_results
    }
    
    # Mostrar resumen comparativo
    print("\n" + "=" * 80)
    print("RESUMEN COMPARATIVO")
    print("=" * 80)
    
    for method in methods:
        stats = aggregated_stats.get(method, {})
        print(f"\n{method.upper()}:")
        if "error" in stats:
            print(f"  ❌ {stats['error']}")
        else:
            print(f"  Imágenes procesadas: {stats['num_images_processed']}")
            print(f"  Tiempo promedio: {stats['avg_time_seconds']:.3f}s ± {stats['std_time_seconds']:.3f}s")
            print(f"  Tiempo total: {stats['total_time_seconds']:.3f}s")
            print(f"  Columnas promedio: {stats['avg_columns']:.1f} ± {stats['std_columns']:.1f}")
            print(f"  Rango columnas: {stats['min_columns']} - {stats['max_columns']}")
            print(f"  Total columnas: {stats['total_columns']}")
    
    # Comparación directa si ambos métodos tuvieron éxito
    if len(methods) == 2 and all(m in aggregated_stats for m in methods):
        m1, m2 = methods
        s1 = aggregated_stats[m1]
        s2 = aggregated_stats[m2]
        
        if "error" not in s1 and "error" not in s2:
            print("\n" + "=" * 80)
            print("COMPARACIÓN DIRECTA")
            print("=" * 80)
            
            time_diff = s2['avg_time_seconds'] - s1['avg_time_seconds']
            time_ratio = s2['avg_time_seconds'] / s1['avg_time_seconds'] if s1['avg_time_seconds'] > 0 else float('inf')
            
            print(f"\nVelocidad:")
            if time_diff > 0:
                print(f"  {m1.upper()} es {abs(time_diff):.3f}s más rápido en promedio")
                print(f"  {m1.upper()} es {time_ratio:.2f}x más rápido que {m2.upper()}")
            else:
                print(f"  {m2.upper()} es {abs(time_diff):.3f}s más rápido en promedio")
                print(f"  {m2.upper()} es {1/time_ratio:.2f}x más rápido que {m1.upper()}")
            
            col_diff = s2['avg_columns'] - s1['avg_columns']
            print(f"\nColumnas detectadas:")
            print(f"  {m1.upper()}: {s1['avg_columns']:.1f} promedio")
            print(f"  {m2.upper()}: {s2['avg_columns']:.1f} promedio")
            if col_diff > 0:
                print(f"  {m2.upper()} detecta {col_diff:.1f} columnas más en promedio")
            else:
                print(f"  {m1.upper()} detecta {abs(col_diff):.1f} columnas más en promedio")
    
    return benchmark_results


def main():
    parser = argparse.ArgumentParser(
        description="Compara rendimiento de métodos de detección de columnas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  Comparar OpenCV vs DocLayout-YOLO en todas las imágenes:
    python benchmark_methods.py
  
  Comparar solo las primeras 10 imágenes con umbral personalizado:
    python benchmark_methods.py --num-images 10 --conf 0.3
  
  Comparar solo un método:
    python benchmark_methods.py --methods doclayout
        """
    )
    parser.add_argument(
        "--imgs-dir",
        default="imgs",
        help="Directorio con las imágenes popurri*.jpg (default: imgs)"
    )
    parser.add_argument(
        "--num-images",
        type=int,
        default=None,
        help="Número de imágenes a procesar (default: todas las encontradas)"
    )
    parser.add_argument(
        "--methods",
        nargs='+',
        default=["opencv", "doclayout"],
        choices=["opencv", "doclayout", "yolo"],
        help="Métodos a comparar (default: opencv doclayout)"
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
        help="Archivo de salida JSON (default: build/benchmark_results_YYYYMMDD-HHMM.json)"
    )
    args = parser.parse_args()
    
    # Normalizar métodos (yolo -> doclayout)
    methods = ["doclayout" if m == "yolo" else m for m in args.methods]
    methods = list(dict.fromkeys(methods))  # Eliminar duplicados preservando orden
    
    # Ejecutar benchmark
    results = compare_methods(
        imgs_dir=args.imgs_dir,
        num_images=args.num_images,
        methods=methods,
        doclayout_conf=args.conf,
        model_path=args.model_path
    )
    
    # Guardar resultados en build/ por defecto
    if args.output is None:
        script_dir = Path(__file__).parent
        build_dir = script_dir / "build"
        build_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        output_path = build_dir / f"benchmark_results_{timestamp}.json"
    else:
        output_path = Path(args.output)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ Resultados guardados en: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
