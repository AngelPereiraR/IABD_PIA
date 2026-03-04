"""
compare_ocr_models.py

Compara los 4 modelos OCR (PaddleOCR, EasyOCR, Tesseract, DeepSeek-VL2) sobre el mismo conjunto de imágenes.
Genera un reporte comparativo con métricas de rendimiento y calidad.

Uso:
    python compare_ocr_models.py
    python compare_ocr_models.py --num-images 5 --method doclayout
    python compare_ocr_models.py --models paddle easyocr tesseract
"""
import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import os

from output_utils import get_output_dir


def get_popurri_images(imgs_dir: str = "imgs", num_images: int = 5) -> List[Path]:
    """Obtiene las primeras N imágenes de popurrí."""
    imgs_path = Path(imgs_dir)
    if not imgs_path.exists():
        print(f"❌ Error: Carpeta '{imgs_dir}' no encontrada")
        return []
    
    # Buscar archivos popurri*.jpg
    images = sorted(imgs_path.glob("popurri*.jpg"))[:num_images]
    
    if not images:
        print(f"❌ Error: No se encontraron imágenes popurri*.jpg en '{imgs_dir}'")
        return []
    
    print(f"✅ Encontradas {len(images)} imágenes:")
    for img in images:
        print(f"   - {img.name}")
    
    return images


def run_paddle_ocr(
    image_path: Path,
    out_base: str,
    method: str,
    doclayout_conf: float,
    model_path: str = None
) -> Dict[str, Any]:
    """Ejecuta PaddleOCR sobre una imagen."""
    print(f"\n  🔵 PaddleOCR...")
    
    cmd = [
        "python", "paddle-pruebas.py",
        str(image_path),
        "--outdir", out_base,
        "--method", method,
        "--doclayout-conf", str(doclayout_conf)
    ]
    
    if model_path:
        cmd.extend(["--model-path", model_path])
    
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start
        
        if result.returncode == 0:
            # Buscar el summary.json usando get_output_dir
            expected_dir = get_output_dir(str(image_path), f"paddle-{method}", base_dir=out_base)
            summary_path = expected_dir / "summary.json"
            
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                return {
                    "success": True,
                    "elapsed_time": elapsed,
                    "summary": summary,
                    "output_dir": str(expected_dir)
                }
        
        return {
            "success": False,
            "elapsed_time": elapsed,
            "error": result.stderr if result.stderr else "Unknown error"
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "elapsed_time": 300,
            "error": "Timeout (>300s)"
        }
    except Exception as e:
        return {
            "success": False,
            "elapsed_time": time.time() - start,
            "error": str(e)
        }


def run_easyocr(
    image_path: Path,
    out_base: str,
    method: str,
    doclayout_conf: float,
    model_path: str = None,
    use_gpu: bool = True
) -> Dict[str, Any]:
    """Ejecuta EasyOCR sobre una imagen."""
    print(f"\n  🟢 EasyOCR...")
    
    cmd = [
        "python", "easyocr-pruebas.py",
        str(image_path),
        "--outdir", out_base,
        "--method", method,
        "--doclayout-conf", str(doclayout_conf)
    ]
    
    if model_path:
        cmd.extend(["--model-path", model_path])
    
    if not use_gpu:
        cmd.append("--no-gpu")
    
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start
        
        if result.returncode == 0:
            # Buscar el summary.json usando get_output_dir
            expected_dir = get_output_dir(str(image_path), f"easyocr-{method}", base_dir=out_base)
            summary_path = expected_dir / "summary.json"
            
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                return {
                    "success": True,
                    "elapsed_time": elapsed,
                    "summary": summary,
                    "output_dir": str(expected_dir)
                }
        
        return {
            "success": False,
            "elapsed_time": elapsed,
            "error": result.stderr if result.stderr else "Unknown error"
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "elapsed_time": 300,
            "error": "Timeout (>300s)"
        }
    except Exception as e:
        return {
            "success": False,
            "elapsed_time": time.time() - start,
            "error": str(e)
        }


def run_tesseract(
    image_path: Path,
    out_base: str,
    method: str,
    doclayout_conf: float,
    model_path: str = None,
    use_columns: bool = True
) -> Dict[str, Any]:
    """Ejecuta Tesseract sobre una imagen."""
    print(f"\n  🟡 Tesseract...")
    
    cmd = [
        "python", "tesseract-pruebas.py",
        str(image_path),
        "--outdir", out_base,
        "--method", method,
        "--doclayout-conf", str(doclayout_conf)
    ]
    
    if not use_columns:
        cmd.append("--no-columns")
    
    if model_path:
        cmd.extend(["--model-path", model_path])
    
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start
        
        if result.returncode == 0:
            # Buscar el summary.json usando get_output_dir
            method_name = "tesseract-fullpage" if not use_columns else f"tesseract-{method}"
            expected_dir = get_output_dir(str(image_path), method_name, base_dir=out_base)
            summary_path = expected_dir / "summary.json"
            
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                return {
                    "success": True,
                    "elapsed_time": elapsed,
                    "summary": summary,
                    "output_dir": str(expected_dir)
                }
        
        return {
            "success": False,
            "elapsed_time": elapsed,
            "error": result.stderr if result.stderr else "Unknown error"
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "elapsed_time": 300,
            "error": "Timeout (>300s)"
        }
    except Exception as e:
        return {
            "success": False,
            "elapsed_time": time.time() - start,
            "error": str(e)
        }


def run_deepseek(
    image_path: Path,
    out_base: str,
    resolution: str = "base",
    prompt_mode: str = "default"
) -> Dict[str, Any]:
    """Ejecuta DeepSeek-VL2 sobre una imagen."""
    print(f"\n  🔴 DeepSeek-VL2...")
    
    cmd = [
        "python", "pruebas-deepseek.py",
        "--mode", "single",
        "--image", str(image_path),
        "--output", out_base,
        "--resolution", resolution,
        "--prompt-mode", prompt_mode
    ]
    
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start
        
        if result.returncode == 0:
            # DeepSeek guarda resultados de forma diferente
            # Buscar archivos de salida
            out_path = Path(out_base) / image_path.stem
            
            if out_path.exists():
                # Contar archivos generados
                files = list(out_path.glob("**/*"))
                files = [f for f in files if f.is_file()]
                
                # Buscar archivo de texto generado (markdown)
                md_files = list(out_path.glob("*.md"))
                total_chars = 0
                total_words = 0
                
                if md_files:
                    with open(md_files[0], 'r', encoding='utf-8') as f:
                        content = f.read()
                        total_chars = len(content)
                        total_words = len(content.split())
                
                return {
                    "success": True,
                    "elapsed_time": elapsed,
                    "summary": {
                        "num_files": len(files),
                        "total_chars": total_chars,
                        "total_words": total_words,
                        "ocr_engine": "DeepSeek-VL2",
                        "resolution": resolution,
                        "prompt_mode": prompt_mode
                    },
                    "output_dir": str(out_path)
                }
        
        return {
            "success": False,
            "elapsed_time": elapsed,
            "error": result.stderr if result.stderr else "Unknown error"
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "elapsed_time": 300,
            "error": "Timeout (>300s)"
        }
    except Exception as e:
        return {
            "success": False,
            "elapsed_time": time.time() - start,
            "error": str(e)
        }


def compare_models(
    images: List[Path],
    models: List[str],
    method: str,
    doclayout_conf: float,
    model_path: str = None,
    deepseek_resolution: str = "base",
    deepseek_prompt: str = "default",
    use_gpu: bool = True,
    tesseract_use_columns: bool = True
) -> Dict[str, Any]:
    """Compara múltiples modelos OCR en las mismas imágenes."""
    
    print("="*80)
    print("COMPARACIÓN DE MODELOS OCR")
    print("="*80)
    print(f"Imágenes a procesar: {len(images)}")
    print(f"Modelos: {', '.join(models)}")
    print(f"Método de detección: {method}")
    print(f"Confianza YOLO: {doclayout_conf}")
    print("="*80)
    
    # Crear carpeta de resultados base
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_base = f"comparacion_ocr_{timestamp}"
    Path(out_base).mkdir(exist_ok=True)
    
    comparison_results = {
        "timestamp": timestamp,
        "config": {
            "num_images": len(images),
            "models": models,
            "detection_method": method,
            "doclayout_conf": doclayout_conf,
            "deepseek_resolution": deepseek_resolution,
            "deepseek_prompt": deepseek_prompt,
            "use_gpu": use_gpu,
            "tesseract_use_columns": tesseract_use_columns
        },
        "images": []
    }
    
    # Procesar cada imagen con cada modelo
    for img_idx, image_path in enumerate(images, 1):
        print(f"\n{'='*80}")
        print(f"IMAGEN {img_idx}/{len(images)}: {image_path.name}")
        print(f"{'='*80}")
        
        image_results = {
            "image_name": image_path.name,
            "image_path": str(image_path),
            "models": {}
        }
        
        # PaddleOCR
        if "paddle" in models:
            model_out = Path(out_base) / "paddle"
            model_out.mkdir(exist_ok=True)
            result = run_paddle_ocr(image_path, str(model_out), method, doclayout_conf, model_path)
            image_results["models"]["paddle"] = result
            
            if result["success"]:
                print(f"    ✅ Tiempo: {result['elapsed_time']:.2f}s | Chars: {result['summary'].get('total_chars', 0)}")
            else:
                print(f"    ❌ Error: {result.get('error', 'Unknown')}")
        
        # EasyOCR
        if "easyocr" in models:
            model_out = Path(out_base) / "easyocr"
            model_out.mkdir(exist_ok=True)
            result = run_easyocr(image_path, str(model_out), method, doclayout_conf, model_path, use_gpu)
            image_results["models"]["easyocr"] = result
            
            if result["success"]:
                print(f"    ✅ Tiempo: {result['elapsed_time']:.2f}s | Chars: {result['summary'].get('total_chars', 0)}")
            else:
                print(f"    ❌ Error: {result.get('error', 'Unknown')}")
        
        # Tesseract
        if "tesseract" in models:
            model_out = Path(out_base) / "tesseract"
            model_out.mkdir(exist_ok=True)
            result = run_tesseract(image_path, str(model_out), method, doclayout_conf, model_path, tesseract_use_columns)
            image_results["models"]["tesseract"] = result
            
            if result["success"]:
                print(f"    ✅ Tiempo: {result['elapsed_time']:.2f}s | Chars: {result['summary'].get('total_chars', 0)}")
            else:
                print(f"    ❌ Error: {result.get('error', 'Unknown')}")
        
        # DeepSeek-VL2
        if "deepseek" in models:
            model_out = Path(out_base) / "deepseek"
            model_out.mkdir(exist_ok=True)
            result = run_deepseek(image_path, str(model_out), deepseek_resolution, deepseek_prompt)
            image_results["models"]["deepseek"] = result
            
            if result["success"]:
                print(f"    ✅ Tiempo: {result['elapsed_time']:.2f}s | Chars: {result['summary'].get('total_chars', 0)}")
            else:
                print(f"    ❌ Error: {result.get('error', 'Unknown')}")
        
        comparison_results["images"].append(image_results)
    
    # Calcular estadísticas agregadas
    print(f"\n{'='*80}")
    print("ESTADÍSTICAS AGREGADAS")
    print(f"{'='*80}")
    
    stats = {}
    for model in models:
        successes = []
        times = []
        chars = []
        words = []
        
        for img_result in comparison_results["images"]:
            model_result = img_result["models"].get(model, {})
            if model_result.get("success"):
                successes.append(1)
                times.append(model_result.get("elapsed_time", 0))
                
                summary = model_result.get("summary", {})
                chars.append(summary.get("total_chars", 0))
                words.append(summary.get("total_words", 0))
        
        if successes:
            stats[model] = {
                "success_rate": sum(successes) / len(comparison_results["images"]),
                "avg_time": sum(times) / len(times),
                "total_time": sum(times),
                "avg_chars": sum(chars) / len(chars) if chars else 0,
                "avg_words": sum(words) / len(words) if words else 0,
                "total_chars": sum(chars),
                "total_words": sum(words),
                "num_processed": len(successes)
            }
            
            print(f"\n{model.upper()}:")
            print(f"  Éxito: {stats[model]['success_rate']*100:.1f}% ({stats[model]['num_processed']}/{len(comparison_results['images'])})")
            print(f"  Tiempo promedio: {stats[model]['avg_time']:.2f}s")
            print(f"  Tiempo total: {stats[model]['total_time']:.2f}s")
            print(f"  Chars promedio: {stats[model]['avg_chars']:.0f}")
            print(f"  Chars totales: {stats[model]['total_chars']}")
            print(f"  Words totales: {stats[model]['total_words']}")
        else:
            stats[model] = {
                "success_rate": 0,
                "error": "No successful executions"
            }
            print(f"\n{model.upper()}:")
            print(f"  ❌ No se procesaron imágenes exitosamente")
    
    comparison_results["aggregate_stats"] = stats
    
    # Guardar resultados
    results_file = Path(out_base) / "comparison_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✅ Comparación completada")
    print(f"📁 Resultados guardados en: {out_base}/")
    print(f"📊 Reporte JSON: {results_file}")
    print(f"{'='*80}")
    
    return comparison_results


def main():
    parser = argparse.ArgumentParser(
        description='Compara múltiples modelos OCR en las mismas imágenes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  Comparar todos los modelos con OpenCV (primeras 5 imágenes):
    python compare_ocr_models.py
  
  Comparar con DocLayout-YOLO en 10 imágenes:
    python compare_ocr_models.py --num-images 10 --method doclayout
  
  Comparar solo PaddleOCR y EasyOCR:
    python compare_ocr_models.py --models paddle easyocr
  
  Comparar todos con configuración personalizada:
    python compare_ocr_models.py --method doclayout --doclayout-conf 0.3 --deepseek-resolution large
        """
    )
    
    parser.add_argument(
        '--imgs-dir',
        type=str,
        default='imgs',
        help='Carpeta con imágenes popurrí (default: imgs)'
    )
    parser.add_argument(
        '--num-images',
        type=int,
        default=5,
        help='Número de imágenes a procesar (default: 5)'
    )
    parser.add_argument(
        '--models',
        nargs='+',
        default=['paddle', 'easyocr', 'tesseract', 'deepseek'],
        choices=['paddle', 'easyocr', 'tesseract', 'deepseek'],
        help='Modelos a comparar (default: todos)'
    )
    parser.add_argument(
        '--method', '-m',
        default='opencv',
        choices=['opencv', 'doclayout', 'yolo'],
        help="Método de detección de columnas para Paddle/Easy/Tesseract (default: opencv)"
    )
    parser.add_argument(
        '--doclayout-conf',
        type=float,
        default=0.25,
        help='Umbral de confianza para DocLayout-YOLO (default: 0.25)'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        default=None,
        help='Ruta personalizada al modelo DocLayout-YOLO (.pt)'
    )
    parser.add_argument(
        '--deepseek-resolution',
        type=str,
        default='base',
        choices=['tiny', 'small', 'base', 'large', 'gundam'],
        help='Resolución de DeepSeek-VL2 (default: base)'
    )
    parser.add_argument(
        '--deepseek-prompt',
        type=str,
        default='default',
        choices=['default', 'simple', 'document', 'preserve_layout'],
        help='Prompt mode de DeepSeek-VL2 (default: default)'
    )
    parser.add_argument(
        '--no-gpu',
        action='store_true',
        help='Desactivar GPU para EasyOCR'
    )
    parser.add_argument(
        '--tesseract-no-columns',
        action='store_true',
        help='Procesar Tesseract sin detección de columnas'
    )
    
    args = parser.parse_args()
    
    # Obtener imágenes
    images = get_popurri_images(args.imgs_dir, args.num_images)
    if not images:
        return 1
    
    # Ejecutar comparación
    compare_models(
        images=images,
        models=args.models,
        method=args.method,
        doclayout_conf=args.doclayout_conf,
        model_path=args.model_path,
        deepseek_resolution=args.deepseek_resolution,
        deepseek_prompt=args.deepseek_prompt,
        use_gpu=not args.no_gpu,
        tesseract_use_columns=not args.tesseract_no_columns
    )
    
    return 0


if __name__ == '__main__':
    exit(main())
