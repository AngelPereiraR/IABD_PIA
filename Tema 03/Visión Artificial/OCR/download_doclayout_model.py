"""
download_doclayout_model.py

Descarga el modelo DocLayout-YOLO pre-entrenado desde Hugging Face.
Este modelo detecta 9 tipos de elementos en documentos:
  - text, title, figure, table, caption, header, footer, reference, equation

Uso:
    python download_doclayout_model.py
"""
from huggingface_hub import hf_hub_download
from pathlib import Path
import sys

def main():
    # Crear carpeta para modelos en la misma ubicación del script
    script_dir = Path(__file__).parent
    models_dir = script_dir / "models" / "doclayout_yolo"
    models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Descargando DocLayout-YOLO desde Hugging Face")
    print("=" * 70)
    print("Repo: juliozhao/DocLayout-YOLO-DocStructBench")
    print("Tamaño: ~40MB")
    print("Propósito: Detectar texto/títulos/figuras en documentos\n")

    try:
        model_path = hf_hub_download(
            repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
            filename="doclayout_yolo_docstructbench_imgsz1024.pt",
            local_dir=str(models_dir),
            local_dir_use_symlinks=False
        )
        
        print(f"✅ Modelo descargado exitosamente")
        print(f"📁 Ubicación: {model_path}\n")
        
        print("=" * 70)
        print("Clases detectadas por DocLayout-YOLO:")
        print("=" * 70)
        classes_info = [
            ("0: text", "Párrafos de texto (COLUMNAS)"),
            ("1: title", "Títulos y encabezados"),
            ("2: figure", "Imágenes y figuras decorativas"),
            ("3: table", "Tablas"),
            ("4: caption", "Pies de figura/tabla"),
            ("5: header", "Encabezados de página"),
            ("6: footer", "Pies de página"),
            ("7: reference", "Referencias bibliográficas"),
            ("8: equation", "Ecuaciones matemáticas"),
        ]
        
        for class_id, description in classes_info:
            print(f"  {class_id:12s} - {description}")
        
        print("\n" + "=" * 70)
        print("✅ Listo para usar")
        print("=" * 70)
        print("\nPróximo paso:")
        print("  python detect_columns.py --image imgs/popurri01.jpg --method doclayout --debug")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error descargando modelo: {e}")
        print("\nVerifica:")
        print("  1. Conexión a internet")
        print("  2. huggingface-hub instalado: pip install huggingface-hub")
        print("  3. Espacio en disco (se necesitan ~50MB)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
