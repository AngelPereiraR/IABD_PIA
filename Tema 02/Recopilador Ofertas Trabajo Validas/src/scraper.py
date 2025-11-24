import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def scrape_offer_content(url: str) -> str:
    """
    Utiliza Jina AI Reader para convertir la URL de la oferta en Markdown limpio.
    Incluye lógica de reintentos, ANTI-CACHE y selectores CSS para eliminar basura.
    """
    # TRUCO ANTI-CACHE
    timestamp = int(time.time())
    jina_url = f"https://r.jina.ai/{url}?t={timestamp}"
    
    # --- CONFIGURACIÓN DE LIMPIEZA (HEADERS DE JINA) ---
    # Le decimos a Jina qué partes de la página web queremos y cuáles NO.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Cache-Control": "no-cache",
        # 1. TARGET: Intentamos coger solo el contenido principal
        # LinkedIn suele poner el contenido en <main> o en clases especificas.
        # 'main' es el estándar HTML5 más seguro.
        "X-Target-Selector": "main, .core-rail, .description__text",
        
        # 2. REMOVE: Eliminamos explícitamente basura conocida de LinkedIn
        # nav: Menú superior
        # footer: Pie de página legal
        # .similar-jobs: Lista de otros empleos (mete ruido)
        # .contextual-sign-in-modal: Pop-up de login
        # .ad-banner: Publicidad
        "X-Remove-Selector": "nav, footer, script, style, iframe, .similar-jobs, .people-also-viewed, .contextual-sign-in-modal, .ad-banner, .header, #main-navigation"
    }

    # --- CONFIGURACIÓN DE ROBUSTEZ ---
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        print(f"Scrapeando vía Jina AI (Selectores Activados): {url}...")
        
        response = session.get(jina_url, headers=headers, timeout=(10, 60))
        
        if response.status_code == 200:
            markdown_content = response.text
            
            # Limpieza post-procesado simple (Backup por si Jina falla los selectores)
            markdown_content = _post_clean_markdown(markdown_content)

            if len(markdown_content) < 100:
                print("Advertencia: Contenido demasiado corto tras limpieza. Posible bloqueo.")
                return None
                
            print(f"Scraping exitoso. Longitud: {len(markdown_content)} caracteres.")
            return markdown_content
        
        elif response.status_code == 429:
            print("Advertencia: Rate Limit de Jina AI excedido.")
            return None
        else:
            print(f"Error HTTP {response.status_code} al scrapear.")
            return None

    except Exception as e:
        print(f"Error crítico de conexión: {e}")
        return None
    finally:
        session.close()

def _post_clean_markdown(text: str) -> str:
    """
    Limpieza final de cadenas de texto que suelen colarse en el Markdown
    incluso después de filtrar el HTML.
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    # Frases basura comunes en los dumps de LinkedIn
    garbage_phrases = [
        "Sign in", "Join now", "Forgot password?", 
        "LinkedIn Corporation", "Cookie Policy", 
        "Agree & Join", "Skip to main content"
    ]
    
    for line in lines:
        # Si la línea es exactamente una frase basura, la saltamos
        if any(garbage in line for garbage in garbage_phrases):
            continue
        # Si la línea es un enlace de navegación solo (ej. "[ User Agreement ]")
        if line.strip().startswith("[") and "Agreement" in line:
            continue
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    test_url = "https://www.linkedin.com/jobs/view/4315461080"
    
    print("Iniciando prueba de Scraping (Motor: Jina AI + Selectores CSS)...")
    
    content = scrape_offer_content(test_url)
    
    if content:
        print("\n--- VISTA PREVIA DEL MARKDOWN (Primeros 500 caracteres) ---")
        print("-" * 60)
        print(content + "...")
        print("-" * 60)
        print("La prueba ha sido exitosa.")
    else:
        print("La prueba falló.")