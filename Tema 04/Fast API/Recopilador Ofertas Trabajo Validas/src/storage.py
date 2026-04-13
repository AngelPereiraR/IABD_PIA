"""
Cloudinary SDK wrapper para subir y gestionar archivos en la nube.
Usado para: CV maestro, CVs optimizados, otros assets.
"""
import os
import logging

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno desde .env

logger = logging.getLogger(__name__)

# --- CONFIGURACION ---
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)


# --- FUNCIONES PUBLICAS ---
def upload_pdf(file_path: str, public_id: str) -> str:
    """
    Sube un PDF a Cloudinary desde ruta del filesystem.

    Args:
        file_path: Ruta absoluta al archivo PDF
        public_id: ID único en Cloudinary (ej: "cv/optimized/offer_123")

    Returns:
        URL segura del PDF en Cloudinary

    Raises:
        Exception: Si Cloudinary falla
    """
    try:
        result = cloudinary.uploader.upload(
            file_path,
            public_id=public_id,
            resource_type="image",  # PDFs se gestionan como imagen en Cloudinary
            overwrite=True,
            folder="opticv"  # Organizar en carpeta
        )
        url = result.get("secure_url")
        logger.info(f"[Storage] PDF subido: {url}")
        return url
    except Exception as e:
        logger.error(f"[Storage] Error uploading {public_id}: {e}")
        raise


def upload_bytes(data: bytes, public_id: str) -> str:
    """
    Sube bytes directamente (útil para archivos desde form/memoria).

    Args:
        data: Contenido en bytes
        public_id: ID único en Cloudinary

    Returns:
        URL segura del archivo

    Raises:
        Exception: Si Cloudinary falla
    """
    try:
        result = cloudinary.uploader.upload(
            data,
            public_id=public_id,
            resource_type="image",  # PDFs se gestionan como imagen en Cloudinary
            overwrite=True,
            folder="opticv"
        )
        url = result.get("secure_url")
        logger.info(f"[Storage] Bytes subidos: {url}")
        return url
    except Exception as e:
        logger.error(f"[Storage] Error uploading bytes {public_id}: {e}")
        raise


def get_url(public_id: str) -> str:
    """
    Construye URL de un asset ya subido (sin subirlo de nuevo).

    Args:
        public_id: ID del asset en Cloudinary (ej: "cv/master")

    Returns:
        URL del asset
    """
    try:
        url = cloudinary.CloudinaryImage(public_id).build_url(resource_type="image")
        return url
    except Exception as e:
        logger.error(f"[Storage] Error building URL for {public_id}: {e}")
        raise


def delete_file(public_id: str) -> bool:
    """
    Elimina un archivo de Cloudinary.

    Args:
        public_id: ID del asset a eliminar

    Returns:
        True si se eliminó, False si no existe
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        if result.get("result") == "ok":
            logger.info(f"[Storage] Eliminado: {public_id}")
            return True
        logger.warning(f"[Storage] No eliminado: {public_id}")
        return False
    except Exception as e:
        logger.error(f"[Storage] Error deleting {public_id}: {e}")
        return False
