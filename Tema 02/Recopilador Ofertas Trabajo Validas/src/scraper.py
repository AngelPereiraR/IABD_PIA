import os
import time
import re
import requests
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from firecrawl import Firecrawl 

# Cargar variables de entorno
load_dotenv()

def scrape_offer_content(url: str) -> str:
    """
    Estrategia en Cascada:
    1. Jina AI (Rápido).
    2. FireCrawl (Potente - InfoJobs).
    3. Directo (Último recurso).
    """
    # --- 1. INTENTO CON JINA AI ---
    encoded_url = quote(url, safe='') 
    timestamp = int(time.time())
    jina_url = f"https://r.jina.ai/{encoded_url}?t={timestamp}"
    
    common_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Selectores generales
    target_selector = "main, .core-rail, .description__text, #job-description"
    remove_selector = "nav, footer, script, style, iframe, .similar-jobs, .people-also-viewed, .contextual-sign-in-modal, .ad-banner, .header, #main-navigation"

    if "infojobs.net" in url:
        # INFOJOBS: Capturamos cabecera de oferta (titulo, ubicacion) + cuerpo
        target_selector = "#job-description-container, .job-description, .offer-body, .container-expanded, .ij-Offer-header, h1, .subtitle" 
        # Eliminamos elementos de navegacion global, pero NO la cabecera de la oferta
        remove_selector = "header.global-header, footer, .ij-Header-global, .ij-Footer, .ij-Share, .ij-Report, #demand-button-container, .sui-AtomButton"

    headers_jina = {
        "User-Agent": common_ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "X-Target-Selector": target_selector,
        "X-Remove-Selector": remove_selector
    }

    session = requests.Session()
    retry = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))

    try:
        print(f"Scrapeando vía Jina AI: {url[:60]}...")
        response = session.get(jina_url, headers=headers_jina, timeout=(10, 40))
        
        if response.status_code == 200:
            content = response.text
            # Check de bloqueo
            if "browser" in content.lower() and "enable javascript" in content.lower():
                print("Jina bloqueado (JS Challenge). Pasando a FireCrawl...")
            elif len(content) > 200:
                content = _post_clean_markdown(content)
                content = _remove_markdown_links(content)
                print(f"✅ Scraping Jina exitoso. Longitud: {len(content)}")
                return content
            else:
                print("Contenido Jina insuficiente.")
        else:
            print(f"Jina falló con código {response.status_code}.")

    except Exception as e:
        print(f"Error conexión Jina: {e}")

    # --- 2. INTENTO CON FIRECRAWL (Motor Principal para InfoJobs) ---
    if os.getenv("FIRECRAWL_API_KEY"):
        print("🔄 Activando Fallback: FireCrawl (Renderizado JS)...")
        try:
            app = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))
            response = app.scrape(url, formats=['markdown'])
            
            md = ""
            if isinstance(response, dict):
                md = response.get('markdown', '') or response.get('data', {}).get('markdown', '')
            else:
                md = getattr(response, 'markdown', '')
            
            if md:
                # Limpieza específica para InfoJobs
                if "infojobs.net" in url:
                    md = _clean_infojobs_noise(md)
                
                md = _post_clean_markdown(md)
                md = _remove_markdown_links(md)
                
                print(f"✅ Scraping FireCrawl exitoso. Longitud: {len(md)}")
                return md
            else:
                print("FireCrawl no devolvió markdown.")
                
        except Exception as e:
            print(f"❌ Fallo FireCrawl: {e}")

    # --- 3. INTENTO DIRECTO (Último recurso) ---
    print("🔄 Activando Fallback Final: Petición Directa Mejorada...")
    return _direct_scrape_fallback(url, session, common_ua)

def _direct_scrape_fallback(url: str, session: requests.Session, ua: str) -> str:
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            html = response.text
            if "enable javascript" in html.lower() or "identificar tu navegador" in html.lower():
                print("⚠️ Bloqueo WAF (Cloudflare/Datadome) detectado en directo.")
                return None
                
            text = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '\n', text)
            text = re.sub(r'\n\s*\n', '\n\n', text).strip()
            
            if "infojobs.net" in url:
                text = _clean_infojobs_noise(text)
                
            text = _post_clean_markdown(text)
            text = _remove_markdown_links(text)
            
            print(f"✅ Scraping Directo exitoso. Longitud: {len(text)}")
            return text
        else:
            print(f"❌ Fallo directo. Código: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error en directo: {e}")
        return None

def _clean_infojobs_noise(text: str) -> str:
    """
    Limpieza quirúrgica para InfoJobs: Corta el texto SOLO cuando empiezan
    las secciones finales irrelevantes, preservando el contenido y la CABECERA.
    """
    cutoff_markers = [
        "### Ofertas similares", "Ofertas similares",
        "### Top Subcategorías", "Top Subcategorías",
        "### Top Búsquedas", "Top Búsquedas",
        "### Top Puestos", "### Top Empresas",
        "Los datos bancarios, de pago y datos personales nunca deben proporcionarse",
        "Consulta nuestros consejos para una búsqueda de empleo segura"
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    # Flag para saber si ya hemos pasado la descripcion principal
    body_started = False 
    
    for line in lines:
        stripped = line.strip()
        
        # Detección de inicio de cuerpo
        if "Requisitos" in stripped or "Descripción" in stripped:
            body_started = True
            
        # Corte inteligente: Solo corta si estamos SEGUROS de que acabó la oferta
        if body_started and any(marker in stripped for marker in cutoff_markers):
            break
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def _remove_markdown_links(text: str) -> str:
    """
    Elimina los enlaces de Markdown [Texto](URL) dejando solo el Texto.
    """
    return re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

def _post_clean_markdown(text: str) -> str:
    """Limpieza final de líneas sueltas y basura común."""
    lines = text.split('\n')
    cleaned_lines = []
    
    garbage_phrases = [
        "Sign in", "Join now", "Forgot password?", "LinkedIn Corporation", 
        "Cookie Policy", "Agree & Join", "Skip to main content",
        "Adevinta", "Condiciones legales", "Política de privacidad",
        "Uso de cookies", "Denunciar oferta", "Quiénes somos", 
        "enable JavaScript", "support your browser", "Publicada Hace", "Más ofertas en"
    ]
    
    # Whitelist para proteger datos clave
    keep_phrases = [
        "Inscribirme en esta oferta", "Inscribirme", "Solicitar ahora", "Apply now",
        "Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Málaga", # Ciudades principales
        "Presencial", "Híbrido", "Remoto", "Teletrabajo"
    ]
    
    for line in lines:
        stripped = line.strip()
        
        # Si es una frase clave (boton o ubicacion probable), la mantenemos
        if any(keep in stripped for keep in keep_phrases):
            cleaned_lines.append(line)
            continue

        if len(stripped) < 3: continue 
        if any(garbage in stripped for garbage in garbage_phrases): continue
        if stripped.startswith("[") and ("Agreement" in stripped or "Política" in stripped): continue
        if stripped.lower() in ["guardar", "compartir", "denunciar", "guardar oferta"]: continue
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    test_url = "https://www.infojobs.net/getafe/programador-gibbscam-junior-10625/of-id59fb5a76f40d09df2cf8426627ec3"
    print("Iniciando prueba de Scraping (Cascada)...")
    content = scrape_offer_content(test_url)
    if content:
        print("\n--- VISTA PREVIA ---")
        print("-" * 60)
        print(content) 
        print("-" * 60)
        print("Prueba exitosa.")
    else:
        print("Prueba fallida.")