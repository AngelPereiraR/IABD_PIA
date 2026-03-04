from paddleocr import PaddleOCR
from PIL import Image
import time
import os
import shutil
import argparse

# Import our detector
from detect_columns import load_image, detect_columns
from output_utils import get_output_dir


def pil_to_pillow(img_path: str) -> Image.Image:
    return Image.open(img_path)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def main(
    image_path: str,
    out_base: str = "resultados",
    debug: bool = False,
    method: str = "opencv",
    doclayout_conf: float = 0.25,
    model_path: str = None
):
    start_time = time.time()

    # Preparar carpeta de resultados usando output_utils
    out_dir = get_output_dir(image_path, f"paddle-{method}", base_dir=out_base)
    from datetime import datetime
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    print(f"Carpeta de salida: {out_dir}")

    # Cargar imagen con PIL para recortes y con OpenCV para detección
    pil_img = Image.open(image_path)
    width, height = pil_img.size

    # Cargar con OpenCV via detect_columns.load_image
    cv_img = load_image(image_path)

    # Detectar columnas dinámicamente usando el método seleccionado
    (w, h), boxes = detect_columns(
        cv_img,
        method=method,
        debug=debug,
        doclayout_conf=doclayout_conf,
        model_path=model_path,
        image_path=image_path
    )

    # Las imágenes de debug ahora se guardan directamente en out_dir por detect_columns

    ocr = PaddleOCR(lang='es')
    # Preparar contenedores de métricas
    col_metrics = []
    total_lines = 0
    total_chars = 0
    total_ocr_time = 0.0
    total_words = 0

    for idx, b in enumerate(boxes, start=1):
        x1, y1, x2, y2 = b.x1, b.y1, b.x2, b.y2

        # Robustez: truncar a límites de imagen
        x2 = min(x2, width)
        y2 = min(y2, height)

        # Recortar con PIL (x1,y1,x2,y2)
        col_img = pil_img.crop((x1, y1, x2, y2))

        # Guardar recorte dentro de la carpeta de resultados
        temp_name = f'temp_col_{idx}.jpg'
        temp_path = str(out_dir / temp_name)
        col_img.save(temp_path)

        # OCR: NO modificar el funcionamiento del OCR
        t0 = time.time()
        result = ocr.predict(temp_path)
        t1 = time.time()
        ocr_time = t1 - t0

        # Resultado: lista de líneas con bounding boxes; extraer texto
        try:
            rec_texts = result[0].get('rec_texts', [])
        except Exception:
            # fallback a formato alternativo de PaddleOCR
            try:
                rec_texts = [r[1][0] for r in result]
            except Exception:
                rec_texts = []

        # Guardar texto OCR en archivo dentro de la subcarpeta
        txt_name = f'ocr_column_{idx}.txt'
        txt_path = str(out_dir / txt_name)
        with open(txt_path, 'w', encoding='utf-8') as f:
            for texto in rec_texts:
                f.write(texto + "\n")

        # Métricas por columna
        num_lines = len(rec_texts)
        num_chars = sum(len(t) for t in rec_texts)
        # Contar palabras: separar por espacios y filtrar vacíos
        num_words = sum(len([w for w in (t.split()) if w]) for t in rec_texts)
        total_words += num_words
        total_lines += num_lines
        total_chars += num_chars
        total_ocr_time += ocr_time
        col_metrics.append({
            'index': idx,
            'bbox': [x1, y1, x2, y2],
            'num_lines': num_lines,
            'num_words': num_words,
            'num_chars': num_chars,
            'ocr_time_seconds': ocr_time,
        })

        # Imprimir por consola tal como antes
        print(f"Columna {idx} ({x1},{y1},{x2},{y2}):")
        for texto in rec_texts:
            print(texto)
        print("-" * 40)


    elapsed = time.time() - start_time
    print(f"Tiempo transcurrido: {elapsed:.2f} segundos")

    # Crear summary.json con metadatos de la ejecución
    try:
        import json
        avg_ocr_time_per_column = (total_ocr_time / len(boxes)) if boxes else 0.0
        summary = {
            'timestamp': ts,
            'duration_seconds': elapsed,
            'num_columns': len(boxes),
            'out_dir': str(out_dir),
            'image_path': image_path,
            'columns': col_metrics,
            'total_lines': total_lines,
                'total_words': total_words,
            'total_chars': total_chars,
            'total_ocr_time_seconds': total_ocr_time,
            'avg_ocr_time_per_column_seconds': avg_ocr_time_per_column,
        }
        summary_path = str(out_dir / 'summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Summary guardado en: {summary_path}")
    except Exception as e:
        print(f"No se pudo guardar summary.json: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Proceso OCR por columnas dinámicas con PaddleOCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  OpenCV (método manual):
    python paddle-pruebas.py popurri01.jpg --method opencv --debug
  
  DocLayout-YOLO (modelo pre-entrenado):
    python paddle-pruebas.py popurri01.jpg --method doclayout --debug
    python paddle-pruebas.py imgs/ --method doclayout --doclayout-conf 0.3
        """
    )
    parser.add_argument('image', help='Ruta a la imagen o carpeta de imágenes')
    parser.add_argument('--outdir', default='resultados', help='Carpeta base donde se guardarán los resultados (default: resultados)')
    parser.add_argument('--debug', action='store_true', help='Generar imagen de depuración con cajas')
    parser.add_argument(
        '--method', '-m',
        default='opencv',
        choices=['opencv', 'doclayout', 'yolo'],
        help="Método de detección de columnas: 'opencv' (manual), 'doclayout'/'yolo' (modelo YOLO). Default: opencv"
    )
    parser.add_argument(
        '--doclayout-conf',
        type=float,
        default=0.25,
        help='Umbral de confianza para DocLayout-YOLO (0-1). Default: 0.25'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        default=None,
        help='Ruta personalizada al modelo DocLayout-YOLO (.pt)'
    )
    parser.add_argument('--runs', type=int, default=1, help='Número de veces que se ejecutará el procesamiento de la misma imagen (default: 1)')
    args = parser.parse_args()

    # Determinar si image es archivo o carpeta
    target = args.image
    image_paths = []
    if os.path.isdir(target):
        exts = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp')
        for fname in sorted(os.listdir(target)):
            if fname.lower().endswith(exts):
                image_paths.append(os.path.join(target, fname))
        if not image_paths:
            print(f"No se encontraron imágenes en la carpeta: {target}")
            raise SystemExit(1)
    elif os.path.isfile(target):
        image_paths = [target]
    else:
        print(f"La ruta proporcionada no es un archivo ni una carpeta válida: {target}")
        raise SystemExit(1)

    # Ejecutar main para cada imagen encontrada
    for img_path in image_paths:
        print(f"Procesando imagen: {img_path}")
        runs = max(1, args.runs if args.runs is not None else 1)
        for i in range(runs):
            if runs > 1:
                print(f"  Ejecución {i+1}/{runs}")
            main(
                img_path,
                out_base=args.outdir,
                debug=args.debug,
                method=args.method,
                doclayout_conf=args.doclayout_conf,
                model_path=args.model_path
            )