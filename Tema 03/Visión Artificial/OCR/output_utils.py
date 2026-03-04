"""
output_utils.py

Utilidades comunes para gestión de archivos de salida en carpeta build/
"""
from datetime import datetime
from pathlib import Path


def get_output_dir(image_path: str, method: str, base_dir: str = None) -> Path:
    """
    Genera la ruta de salida en build/NombreImagen-Metodo-Fecha/
    o en base_dir/NombreImagen-Metodo-Fecha/ si se especifica base_dir
    
    Args:
        image_path: Ruta a la imagen de entrada
        method: Método utilizado (opencv, doclayout, tesseract, easyocr, paddle, etc.)
        base_dir: Carpeta base personalizada (default: build/ en la misma carpeta del script)
    
    Returns:
        Path objeto con la ruta de la carpeta de salida
    """
    if base_dir is None:
        script_dir = Path(__file__).parent
        build_dir = script_dir / "build"
    else:
        build_dir = Path(base_dir)
    
    # Extraer nombre de imagen sin extensión
    image_name = Path(image_path).stem
    
    # Timestamp compacto YYYYMMDD-HHMM
    timestamp = datetime.now().strftime('%Y%m%d-%H%M')
    
    # Crear nombre de carpeta: NombreImagen-Metodo-Fecha
    folder_name = f"{image_name}-{method}-{timestamp}"
    
    output_dir = build_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir
