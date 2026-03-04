import pytesseract
from PIL import Image
import time
import os
import shutil
import argparse
import json

# Import our detector
from detect_columns import load_image, detect_columns
from output_utils import get_output_dir

pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


def ensure_dir(path: str):
	os.makedirs(path, exist_ok=True)


def process_image_with_tesseract(
	image_path: str,
	out_base: str = "resultados",
	debug: bool = False,
	use_columns: bool = True,
	method: str = "opencv",
	doclayout_conf: float = 0.25,
	model_path: str = None
):
	start_time = time.time()

	# Preparar carpeta de resultados usando output_utils
	method_name = "tesseract-fullpage" if not use_columns else f"tesseract-{method}"
	out_dir = get_output_dir(image_path, method_name, base_dir=out_base)
	from datetime import datetime
	ts = datetime.now().strftime('%Y%m%d_%H%M')
	print(f"Carpeta de salida: {out_dir}")

	# Cargar imagen con PIL para recortes
	pil_img = Image.open(image_path)
	width, height = pil_img.size

	# Si debug, guardar una copia de la imagen original en el out_dir
	if debug:
		orig_copy = str(out_dir / 'input_image.png')
		pil_img.save(orig_copy)

	# Preparar contenedores de métricas
	col_metrics = []
	total_lines = 0
	total_chars = 0
	total_ocr_time = 0.0
	total_words = 0

	if use_columns:
		# Detectar columnas dinámicamente
		cv_img = load_image(image_path)
		(w, h), boxes = detect_columns(
			cv_img,
			method=method,
			debug=debug,
			doclayout_conf=doclayout_conf,
			model_path=model_path,
			image_path=image_path
		)

		# Las imágenes de debug ahora se guardan directamente en out_dir por detect_columns

		# Procesar cada columna
		for idx, b in enumerate(boxes, start=1):
			x1, y1, x2, y2 = b.x1, b.y1, b.x2, b.y2

			# Robustez: truncar a límites de imagen
			x2 = min(x2, width)
			y2 = min(y2, height)

			# Recortar con PIL (x1,y1,x2,y2)
			col_img = pil_img.crop((x1, y1, x2, y2))

			# Ejecutar Tesseract OCR directamente sobre la imagen PIL
			t0 = time.time()
			texto = pytesseract.image_to_string(col_img, lang='spa')
			t1 = time.time()
			ocr_time = t1 - t0

			# Guardar texto
			txt_name = f'ocr_column_{idx}.txt'
			txt_path = str(out_dir / txt_name)
			with open(txt_path, 'w', encoding='utf-8') as f:
				f.write(texto)

			# Métricas
			num_lines = len([l for l in texto.splitlines() if l.strip()])
			num_chars = len(texto)
			num_words = len([w for w in texto.split() if w])

			col_metrics.append({
				'column_index': idx,
				'bbox': [x1, y1, x2, y2],
				'width': x2 - x1,
				'height': y2 - y1,
				'num_lines': num_lines,
				'num_words': num_words,
				'num_chars': num_chars,
				'ocr_time_seconds': ocr_time,
				'output_txt': txt_name,
			})

			total_lines += num_lines
			total_chars += num_chars
			total_words += num_words
			total_ocr_time += ocr_time

			print(f"Columna {idx}: {num_lines} líneas, {num_chars} chars, {ocr_time:.2f}s")

		num_columns = len(boxes)
	else:
		# Procesamiento sin columnas (imagen completa)
		t0 = time.time()
		texto = pytesseract.image_to_string(pil_img, lang='spa')
		t1 = time.time()
		ocr_time = t1 - t0

		# Guardar texto
		txt_name = 'ocr_column_1.txt'
		txt_path = str(out_dir / txt_name)
		with open(txt_path, 'w', encoding='utf-8') as f:
			f.write(texto)

		# Métricas
		num_lines = len([l for l in texto.splitlines() if l.strip()])
		num_chars = len(texto)
		num_words = len([w for w in texto.split() if w])

		col_metrics.append({
			'column_index': 1,
			'bbox': [0, 0, width, height],
			'width': width,
			'height': height,
			'num_lines': num_lines,
			'num_words': num_words,
			'num_chars': num_chars,
			'ocr_time_seconds': ocr_time,
			'output_txt': txt_name,
		})

		total_lines = num_lines
		total_chars = num_chars
		total_words = num_words
		total_ocr_time = ocr_time
		num_columns = 1

		print(f"Imagen completa: {num_lines} líneas, {num_chars} chars, {ocr_time:.2f}s")

	elapsed = time.time() - start_time

	# Crear summary.json
	try:
		avg_ocr_time_per_column = total_ocr_time / num_columns if num_columns > 0 else 0

		summary = {
			'timestamp': ts,
			'duration_seconds': elapsed,
			'detection_method': method if use_columns else 'none',
			'use_columns': use_columns,
			'ocr_engine': 'Tesseract',
			'num_columns': num_columns,
			'out_dir': str(out_dir),
			'image_path': image_path,
			'image_width': width,
			'image_height': height,
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

	print(f"Tiempo total: {elapsed:.2f}s | OCR tiempo: {total_ocr_time:.2f}s | chars: {total_chars} | words: {total_words}")


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description='Proceso OCR con Tesseract (con o sin detección de columnas)',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Ejemplos de uso:
  Con detección de columnas (OpenCV):
    python tesseract-pruebas.py popurri01.jpg --method opencv --debug
  
  Con detección de columnas (DocLayout-YOLO):
    python tesseract-pruebas.py popurri01.jpg --method doclayout --debug
    python tesseract-pruebas.py imgs/ --method doclayout --doclayout-conf 0.3
  
  Sin detección de columnas (imagen completa):
    python tesseract-pruebas.py popurri01.jpg --no-columns --debug
		"""
	)
	parser.add_argument('image', help='Ruta a la imagen o carpeta de imágenes')
	parser.add_argument('--outdir', default='resultados', help='Carpeta base donde se guardarán los resultados (default: resultados)')
	parser.add_argument('--debug', action='store_true', help='Guardar copia de la imagen de entrada y outputs en carpeta de resultados')
	parser.add_argument(
		'--no-columns',
		action='store_true',
		help='Procesar imagen completa sin detectar columnas'
	)
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

	for img_path in image_paths:
		print(f"Procesando imagen: {img_path}")
		runs = max(1, args.runs if args.runs is not None else 1)
		for i in range(runs):
			if runs > 1:
				print(f"  Ejecución {i+1}/{runs}")
			process_image_with_tesseract(
				img_path,
				out_base=args.outdir,
				debug=args.debug,
				use_columns=not args.no_columns,
				method=args.method,
				doclayout_conf=args.doclayout_conf,
				model_path=args.model_path
			)