import os
import sys
import argparse
from pathlib import Path
from transformers import AutoModel, AutoTokenizer
import torch
import time
from datetime import timedelta

# Rutas por defecto
MODEL_PATH = r"E:\Modelos\DeepSeek-OCR"
IMGS_FOLDER = "imgs"
OUTPUT_FOLDER = "resultados_ocr"

# Configuraciones de calidad disponibles
CONFIGS = {
    'tiny': {
        'base_size': 512,
        'image_size': 512,
        'crop_mode': False,
        'descripcion': '512x512 (64 vision tokens) - Más rápido'
    },
    'small': {
        'base_size': 640,
        'image_size': 640,
        'crop_mode': False,
        'descripcion': '640x640 (100 vision tokens) - Rápido'
    },
    'base': {
        'base_size': 1024,
        'image_size': 1024,
        'crop_mode': False,
        'descripcion': '1024x1024 (256 vision tokens) - Balance'
    },
    'large': {
        'base_size': 1280,
        'image_size': 1280,
        'crop_mode': False,
        'descripcion': '1280x1280 (400 vision tokens) - Mayor detalle'
    },
    'gundam': {
        'base_size': 1024,
        'image_size': 640,
        'crop_mode': True,
        'descripcion': 'nx640x640 + 1x1024x1024 - Resolución dinámica'
    }
}

PROMPTS = {
    'default': {
        'text': "<image>\n<|grounding|>Convert the document to markdown.",
        'descripcion': 'Con grounding (boxes) - Detección estándar'
    },
    'simple': {
        'text': "<image>\nExtract all text from this document and convert to markdown.",
        'descripcion': 'Sin grounding - Para documentos simples'
    },
    'document': {
        'text': "<image>\nExtract all visible text from this document, treating all content as regular document text. Convert to markdown.",
        'descripcion': 'Trata todo como texto de documento'
    },
    'preserve_layout': {
        'text': "<image>\n<|grounding|>Extract all text while preserving the original layout and structure. Include all pages and sections.",
        'descripcion': 'Preserva el layout original'
    },
    'custom': {
        'text': None,  # Se usa CUSTOM_PROMPT
        'descripcion': 'Prompt personalizado definido por el usuario'
    }
}

def obtener_prompt(prompt_mode, custom_prompt=None):
    """Obtiene el prompt según la configuración"""
    if prompt_mode not in PROMPTS:
        print(f"⚠️  Advertencia: PROMPT_MODE '{prompt_mode}' no válido, usando 'default'")
        return PROMPTS['default']['text']
    
    if prompt_mode == 'custom':
        return custom_prompt if custom_prompt else PROMPTS['default']['text']
    
    return PROMPTS[prompt_mode]['text']

def cargar_modelo():
    """Carga el modelo y tokenizer de DeepSeek-OCR"""
    print("Cargando modelo DeepSeek-OCR...")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    
    # Intentar cargar con flash_attention_2, si falla usar eager
    try:
        model = AutoModel.from_pretrained(
            MODEL_PATH,
            _attn_implementation='flash_attention_2',
            trust_remote_code=True,
            use_safetensors=True
        )
        print("✓ Modelo cargado con flash_attention_2")
    except Exception as e:
        print(f"⚠ Flash attention no disponible, usando 'eager': {e}")
        model = AutoModel.from_pretrained(
            MODEL_PATH,
            trust_remote_code=True,
            use_safetensors=True
        )
    
    # Mover a GPU y convertir a bfloat16
    model = model.eval().cuda().to(torch.bfloat16)
    
    print("✓ Modelo cargado correctamente en GPU")
    return model, tokenizer

def obtener_imagenes(carpeta):
    """Obtiene todas las imágenes de la carpeta"""
    extensiones = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    imagenes = []
    
    carpeta_path = Path(carpeta)
    if not carpeta_path.exists():
        print(f"Error: La carpeta '{carpeta}' no existe")
        return []
    
    for archivo in carpeta_path.iterdir():
        if archivo.suffix.lower() in extensiones:
            imagenes.append(archivo)
    
    return sorted(imagenes)

def extraer_texto(model, tokenizer, imagen_path, output_path, config, prompt, prompt_mode='default'):
    """Extrae texto de una imagen usando DeepSeek-OCR"""
    inicio = time.time()
    
    try:
        cfg = CONFIGS.get(config, CONFIGS['base'])
        
        # Crear subcarpeta para esta imagen
        img_name = imagen_path.stem
        img_output_path = Path(output_path) / img_name
        img_output_path.mkdir(exist_ok=True, parents=True)
        
        print(f"  📋 Configuración: {config} - {cfg['descripcion']}")
        print(f"  💬 Prompt: {prompt_mode}")
        print(f"  🔍 Extrayendo texto...")
        
        # Llamar al método infer del modelo
        resultado = model.infer(
            tokenizer,
            prompt=prompt,
            image_file=str(imagen_path),
            output_path=str(img_output_path),
            base_size=cfg['base_size'],
            image_size=cfg['image_size'],
            crop_mode=cfg['crop_mode'],
            save_results=True,      # Guardar archivos de salida
            test_compress=False     # No comprimir para capturar todo
        )
        
        tiempo_total = time.time() - inicio
        
        # Verificar qué archivos se generaron realmente
        archivos_generados = list(img_output_path.glob("**/*"))
        archivos_generados = [f for f in archivos_generados if f.is_file()]
        
        print(f"  ⏱️  Tiempo: {tiempo_total:.2f}s")
        print(f"  ✓ Resultado devuelto por el modelo")
        print(f"  📁 Archivos generados: {len(archivos_generados)}")
        
        return resultado, img_output_path, tiempo_total, archivos_generados, True
        
    except Exception as e:
        tiempo_total = time.time() - inicio
        error_msg = f"Error al procesar: {str(e)}"
        print(f"  ❌ {error_msg}")
        print(f"  ⏱️  Tiempo hasta error: {tiempo_total:.2f}s")
        import traceback
        print(f"  🔍 Traceback completo:")
        traceback.print_exc()
        return None, None, tiempo_total, [], False

def procesar_modo_single(imagen_path, output_folder, resolution_config, prompt_mode, custom_prompt):
    """Procesa una única imagen específica"""
    # Validar que la imagen existe
    imagen_path = Path(imagen_path)
    if not imagen_path.exists():
        print(f"\n❌ Error: La imagen '{imagen_path}' no existe")
        print(f"   Por favor, especifica una ruta válida")
        return
    
    # Validar extensión
    extensiones_validas = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    if imagen_path.suffix.lower() not in extensiones_validas:
        print(f"\n❌ Error: '{imagen_path.suffix}' no es una extensión válida")
        print(f"   Extensiones válidas: {', '.join(extensiones_validas)}")
        return
    
    # Crear carpeta de salida
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    # Cargar modelo
    model, tokenizer = cargar_modelo()
    
    config_info = CONFIGS[resolution_config]
    prompt_info = PROMPTS.get(prompt_mode, PROMPTS['default'])
    prompt_texto = obtener_prompt(prompt_mode, custom_prompt)
    
    print(f"\n{'='*70}")
    print(f"🎯 MODO: IMAGEN ÚNICA")
    print(f"🖼️  Imagen a procesar: {imagen_path.name}")
    print(f"📁 Ruta completa: {imagen_path.absolute()}")
    print(f"⚙️  Configuración: {resolution_config.upper()}")
    print(f"📊 Detalles: {config_info['descripcion']}")
    print(f"💬 Prompt: {prompt_mode.upper()} - {prompt_info['descripcion']}")
    print(f"💾 Carpeta de salida: {output_folder}/{imagen_path.stem}/")
    print(f"{'='*70}\n")
    
    # Procesar imagen
    print(f"📷 Procesando: {imagen_path.name}")
    
    resultado, img_output, tiempo_img, archivos, exito = extraer_texto(
        model, tokenizer, imagen_path, str(output_path), resolution_config, prompt_texto, prompt_mode
    )
    
    # Mostrar archivos generados
    if archivos:
        print(f"\n  📄 Archivos creados:")
        for archivo in archivos:
            tamano = archivo.stat().st_size / 1024
            print(f"     • {archivo.name} ({tamano:.1f} KB)")
    
    # Guardar resumen
    if img_output:
        resumen_path = img_output / "RESUMEN.txt"
        with open(resumen_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("RESUMEN DE PROCESAMIENTO - DEEPSEEK-OCR (MODO SINGLE)\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Imagen procesada: {imagen_path.name}\n")
            f.write(f"Ruta original: {imagen_path.absolute()}\n")
            f.write(f"Configuración usada: {resolution_config} - {config_info['descripcion']}\n")
            f.write(f"Carpeta de salida: {img_output}\n")
            f.write(f"Tiempo de procesamiento: {tiempo_img:.2f}s\n")
            f.write(f"Estado: {'✓ Exitoso' if exito else '❌ Error'}\n\n")
            
            if archivos:
                f.write("ARCHIVOS GENERADOS:\n")
                f.write("-" * 70 + "\n")
                for archivo in archivos:
                    tamano = archivo.stat().st_size / 1024
                    f.write(f"  • {archivo.name} ({tamano:.1f} KB)\n")
            else:
                f.write("⚠️  No se generaron archivos\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("ARCHIVOS ESPERADOS:\n")
            f.write("-" * 70 + "\n")
            f.write("  • result.mmd - Markdown con el texto extraído\n")
            f.write("  • result_with_boxes.jpg - Imagen con boxes visualizados\n")
            f.write("  • images/ - Carpeta con figuras extraídas (si las hay)\n")
    
    print(f"\n{'='*70}")
    if exito:
        print(f"✅ Procesamiento completado exitosamente")
        print(f"⏱️  Tiempo: {tiempo_img:.2f}s")
        print(f"📁 Resultados en: {img_output}")
        if img_output:
            print(f"📋 Resumen en: {resumen_path}")
    else:
        print(f"❌ Error en el procesamiento")
        print(f"⏱️  Tiempo hasta error: {tiempo_img:.2f}s")
    print(f"{'='*70}\n")
    
    if exito and img_output:
        print("💡 UBICACIÓN DE LOS RESULTADOS:")
        print(f"   • Texto extraído: {img_output}/result.mmd")
        print(f"   • Imagen con boxes: {img_output}/result_with_boxes.jpg")
        print(f"   • Figuras extraídas: {img_output}/images/ (si las hay)")
        print(f"   • Resumen: {img_output}/RESUMEN.txt")

def procesar_modo_batch(imgs_folder, output_folder, resolution_config, prompt_mode, custom_prompt):
    """Procesa todas las imágenes de la carpeta"""
    # Crear carpeta de salida
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    # Cargar modelo
    model, tokenizer = cargar_modelo()
    
    # Obtener imágenes
    imagenes = obtener_imagenes(imgs_folder)
    
    if not imagenes:
        print(f"\n❌ No se encontraron imágenes en la carpeta '{imgs_folder}'")
        return
    
    config_info = CONFIGS[resolution_config]
    prompt_texto = obtener_prompt(prompt_mode, custom_prompt)
    
    print(f"\n{'='*70}")
    print(f"🎯 MODO: PROCESAMIENTO POR LOTES")
    print(f"🖼️  Imágenes encontradas: {len(imagenes)}")
    print(f"⚙️  Configuración: {resolution_config.upper()}")
    print(f"📊 Detalles: {config_info['descripcion']}")
    print(f"💾 Carpeta de salida: {output_folder}/")
    print(f"{'='*70}\n")
    
    # Procesar cada imagen
    archivos_por_imagen = []
    tiempos_procesamiento = []
    tiempo_total_inicio = time.time()
    
    for i, img_path in enumerate(imagenes, 1):
        print(f"[{i}/{len(imagenes)}] 📷 Procesando: {img_path.name}")
        
        # Extraer texto
        resultado, img_output, tiempo_img, archivos, exito = extraer_texto(
            model, tokenizer, img_path, str(output_path), resolution_config, prompt_texto, prompt_mode
        )
        
        tiempos_procesamiento.append({
            'imagen': img_path.name,
            'tiempo': tiempo_img,
            'exito': exito
        })
        
        if archivos:
            archivos_por_imagen.append((img_path.name, archivos))
    
    tiempo_total = time.time() - tiempo_total_inicio
    
    # Guardar resumen general
    resumen_path = output_path / "RESUMEN_GENERAL.txt"
    with open(resumen_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("RESUMEN DE PROCESAMIENTO - DEEPSEEK-OCR (MODO BATCH)\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total de imágenes procesadas: {len(imagenes)}\n")
        f.write(f"Configuración usada: {resolution_config} - {config_info['descripcion']}\n")
        f.write(f"Carpeta de salida: {output_folder}/\n")
        f.write(f"Tiempo total: {timedelta(seconds=int(tiempo_total))}\n\n")
        
        # Estadísticas de tiempo
        exitosas = [t for t in tiempos_procesamiento if t['exito']]
        if exitosas:
            tiempo_promedio = sum(t['tiempo'] for t in exitosas) / len(exitosas)
            tiempo_min = min(t['tiempo'] for t in exitosas)
            tiempo_max = max(t['tiempo'] for t in exitosas)
            
            f.write("ESTADÍSTICAS DE TIEMPO:\n")
            f.write("-" * 70 + "\n")
            f.write(f"Imágenes exitosas: {len(exitosas)}/{len(imagenes)}\n")
            f.write(f"Tiempo promedio por imagen: {tiempo_promedio:.2f}s\n")
            f.write(f"Tiempo mínimo: {tiempo_min:.2f}s\n")
            f.write(f"Tiempo máximo: {tiempo_max:.2f}s\n\n")
        
        # Tiempos individuales
        f.write("TIEMPOS POR IMAGEN:\n")
        f.write("-" * 70 + "\n")
        for t in tiempos_procesamiento:
            estado = "✓" if t['exito'] else "❌"
            f.write(f"{estado} {t['imagen']}: {t['tiempo']:.2f}s\n")
        f.write("\n")
        
        f.write("ARCHIVOS GENERADOS POR IMAGEN:\n")
        f.write("-" * 70 + "\n")
        if archivos_por_imagen:
            for img_name, archivos in archivos_por_imagen:
                f.write(f"\n📷 {img_name}:\n")
                if archivos:
                    for archivo in archivos:
                        tamano = archivo.stat().st_size / 1024
                        f.write(f"   - {archivo.name} ({tamano:.1f} KB)\n")
                else:
                    f.write(f"   ⚠️  No se generaron archivos\n")
        else:
            f.write("⚠️  No se generaron archivos para ninguna imagen\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("ARCHIVOS ESPERADOS POR IMAGEN:\n")
        f.write("-" * 70 + "\n")
        f.write("  • result.mmd - Markdown procesado\n")
        f.write("  • result_with_boxes.jpg - Imagen con boxes visualizados\n")
        f.write("  • images/ - Carpeta con figuras extraídas (si las hay)\n")
    
    print(f"{'='*70}")
    print(f"✅ Proceso completado")
    print(f"⏱️  Tiempo total: {timedelta(seconds=int(tiempo_total))}")
    
    # Mostrar estadísticas de tiempo
    exitosas = [t for t in tiempos_procesamiento if t['exito']]
    if exitosas:
        tiempo_promedio = sum(t['tiempo'] for t in exitosas) / len(exitosas)
        print(f"📊 Tiempo promedio por imagen: {tiempo_promedio:.2f}s")
    
    print(f"📁 Resultados en: {output_folder}/")
    print(f"📄 Resumen en: {resumen_path}")
    print(f"{'='*70}\n")
    
    print("💡 CONSEJOS:")
    print(f"   • Los boxes están en: {output_folder}/<imagen>/result_with_boxes.jpg")
    print(f"   • El texto extraído está en: {output_folder}/<imagen>/result.mmd")
    print(f"   • Si no se generan archivos, revisa los errores en la salida")

def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='DeepSeek-OCR: Extracción de texto de imágenes con IA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Procesar una imagen específica
  python pruebas-deepseek.py -i imgs/documento.jpg -o resultados -q large -p default
  
  # Procesar todas las imágenes de una carpeta
  python pruebas-deepseek.py -b imgs/ -o resultados -q gundam -p preserve_layout
  
  # Usar un prompt personalizado
  python pruebas-deepseek.py -i imagen.jpg -p custom -c "Extract all text maintaining structure"
  
Modos de calidad disponibles:
  tiny   - 512x512 (64 tokens)  - Más rápido
  small  - 640x640 (100 tokens) - Rápido
  base   - 1024x1024 (256 tokens) - Balance
  large  - 1280x1280 (400 tokens) - Mayor detalle
  gundam - Resolución dinámica con crop
  
Tipos de prompt disponibles:
  default          - Con grounding (boxes) - Detección estándar
  simple           - Sin grounding - Para documentos simples
  document         - Trata todo como texto de documento
  preserve_layout  - Preserva el layout original
  custom           - Prompt personalizado (usar con -c)
        """
    )
    
    # Grupo de entrada
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-i', '--image', type=str,
                           help='Ruta de la imagen individual a procesar')
    input_group.add_argument('-b', '--batch', type=str,
                           help='Carpeta con imágenes para procesamiento por lotes')
    
    # Configuración
    parser.add_argument('-o', '--output', type=str, default=OUTPUT_FOLDER,
                       help=f'Carpeta de salida (por defecto: {OUTPUT_FOLDER})')
    parser.add_argument('-q', '--quality', type=str, default='large',
                       choices=['tiny', 'small', 'base', 'large', 'gundam'],
                       help='Modo de calidad/resolución (por defecto: large)')
    parser.add_argument('-p', '--prompt', type=str, default='default',
                       choices=['default', 'simple', 'document', 'preserve_layout', 'custom'],
                       help='Tipo de prompt a usar (por defecto: default)')
    parser.add_argument('-c', '--custom-prompt', type=str,
                       help='Prompt personalizado (requerido si --prompt=custom)')
    parser.add_argument('-m', '--model-path', type=str, default=MODEL_PATH,
                       help=f'Ruta al modelo DeepSeek-OCR (por defecto: {MODEL_PATH})')
    
    # Opciones adicionales
    parser.add_argument('--list-configs', action='store_true',
                       help='Listar todas las configuraciones disponibles y salir')
    
    args = parser.parse_args()
    
    # Validaciones
    if args.prompt == 'custom' and not args.custom_prompt:
        parser.error("--custom-prompt es requerido cuando --prompt=custom")
    
    return args

def listar_configuraciones():
    """Lista todas las configuraciones disponibles"""
    print("\n" + "="*70)
    print("CONFIGURACIONES DISPONIBLES")
    print("="*70 + "\n")
    
    print("📊 MODOS DE CALIDAD:")
    print("-" * 70)
    for nombre, config in CONFIGS.items():
        print(f"  {nombre:10} - {config['descripcion']}")
        print(f"             Base: {config['base_size']}px, Image: {config['image_size']}px, Crop: {config['crop_mode']}")
    
    print("\n💬 TIPOS DE PROMPT:")
    print("-" * 70)
    for nombre, prompt in PROMPTS.items():
        print(f"  {nombre:18} - {prompt['descripcion']}")
    
    print("\n" + "="*70)

def main():
    # Configurar CUDA
    os.environ["CUDA_VISIBLE_DEVICES"] = '0'
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Listar configuraciones si se solicita
    if args.list_configs:
        listar_configuraciones()
        return
    
    # Actualizar ruta del modelo si se especificó
    global MODEL_PATH
    MODEL_PATH = args.model_path
    
    # Ejecutar según el modo
    if args.image:
        # Modo single
        procesar_modo_single(
            imagen_path=args.image,
            output_folder=args.output,
            resolution_config=args.quality,
            prompt_mode=args.prompt,
            custom_prompt=args.custom_prompt
        )
    else:
        # Modo batch
        procesar_modo_batch(
            imgs_folder=args.batch,
            output_folder=args.output,
            resolution_config=args.quality,
            prompt_mode=args.prompt,
            custom_prompt=args.custom_prompt
        )

if __name__ == "__main__":
    main()