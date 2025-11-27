import os
import time
import re
import requests
from urllib.parse import quote, urlparse, urlunparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
# Intentamos importar la clase correcta segun la version instalada
try:
    from firecrawl import Firecrawl
except ImportError:
    from firecrawl import FirecrawlApp as Firecrawl

# Cargar variables de entorno
load_dotenv()

def scrape_offer_content(url: str) -> str:
    """
    Estrategia en Cascada:
    1. Jina AI (Rápido).
    2. FireCrawl (Potente - InfoJobs).
    3. Directo (Último recurso).
    """
    # 0. LIMPIEZA PREVIA DE URL (Vital para evitar 422 en Jina)
    url = _clean_url(url)
    
    # --- 1. INTENTO CON JINA AI ---
    encoded_url = quote(url, safe='') 
    timestamp = int(time.time())
    jina_url = f"https://r.jina.ai/{encoded_url}?t={timestamp}"
    
    common_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Selectores Generales
    target_selector = "main, .core-rail, .description__text, #job-description"
    remove_selector = "nav, footer, script, style, iframe, .similar-jobs, .people-also-viewed, .contextual-sign-in-modal, .ad-banner, .header, #main-navigation"

    if "infojobs.net" in url:
        # INFOJOBS: Selectores basados en la auditoría del HTML real
        # - #job-description-container: Contenedor de la descripción
        # - .ij-OfferDetailHeader: Cabecera blanca con Titulo, Logo y Detalles (Ubicacion, Salario)
        # - .ij-OfferDetailHeader-detailsList-item: Cada dato individual (Madrid, Presencial, etc)
        target_selector = "#job-description-container, .job-description, .offer-body, .container-expanded, .ij-OfferDetailHeader, .ij-OfferDetailHeader-detailsList-item, h1, .subtitle" 
        
        # Eliminamos elementos de navegacion global (Menu azul superior y footer)
        remove_selector = "header.global-header, .ij-HeaderBasic, .ij-HeaderDesktop, footer, .ij-Header-global, .ij-Footer, .ij-Share, .ij-Report, #demand-button-container, .sui-AtomButton"

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
        print(f"Scrapeando via Jina AI: {url[:60]}...")
        response = session.get(jina_url, headers=headers_jina, timeout=(10, 40))
        
        if response.status_code == 200:
            content = response.text
            content_lower = content.lower()
            
            # Deteccion de bloqueos falsos positivos (200 OK pero es captcha)
            blocking_phrases = [
                "enable javascript", "browser", "identificar tu navegador", 
                "javascript este habilitado", "human verification", "challenge-platform",
                "access denied", "elemental, querido watson", "no podemos identificar tu navegador",
                "comprueba que javascript", "security check"
            ]
            
            is_blocked = any(phrase in content_lower for phrase in blocking_phrases)
            
            if is_blocked:
                print("Detectado BLOQUEO/CAPTCHA en respuesta de Jina. Pasando a Fallback...")
            elif len(content) > 200:
                content = _post_clean_markdown(content)
                content = _remove_markdown_links(content)
                print(f"Scraping Jina exitoso. Longitud: {len(content)}")
                return content # EXITO JINA
            else:
                print("Contenido Jina insuficiente. Pasando a Fallback...")
        else:
            print(f"Jina fallo con codigo {response.status_code}. Pasando a Fallback...")

    except Exception as e:
        print(f"Error conexion Jina: {e}")

    # --- 2. INTENTO CON FIRECRAWL (Motor Principal para InfoJobs si Jina falla) ---
    if os.getenv("FIRECRAWL_API_KEY"):
        print("Activando Fallback: FireCrawl (Renderizado JS)...")
        try:
            # Instanciamos FireCrawl
            app = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))
            
            # Intentamos scrape v1 (sin params dict, args directos o params dict segun version)
            # La forma mas estandar actual es params directos o scrapeOptions
            try:
                response = app.scrape(url, formats=['markdown'])
            except TypeError:
                # Fallback para versiones antiguas SDK
                response = app.scrape_url(url, params={'formats': ['markdown']})
            
            md = ""
            if isinstance(response, dict):
                md = response.get('markdown', '') or response.get('data', {}).get('markdown', '')
            else:
                md = getattr(response, 'markdown', '')
                
            
            if md:
                md_lower = md.lower()
                is_fc_blocked = any(phrase in md_lower for phrase in ["elemental, querido watson", "identificar tu navegador"])
                
                if is_fc_blocked:
                    print("FireCrawl tambien recibio bloqueo. Pasando a directo.")
                else:
                    if "infojobs.net" in url:
                        md = _clean_infojobs_noise(md)
                    
                    md = _post_clean_markdown(md)
                    md = _remove_markdown_links(md)
                    
                    if len(md) > 100:
                        print(f"Scraping FireCrawl exitoso. Longitud: {len(md)}")
                        return md
            else:
                print("FireCrawl no devolvio markdown.")
                
        except Exception as e:
            print(f"Fallo FireCrawl: {e}")

    # --- 3. INTENTO DIRECTO (Ultimo recurso) ---
    print("Activando Fallback Final: Peticion Directa Mejorada...")
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
                print("Bloqueo WAF (Cloudflare/Datadome) detectado en directo.")
                return None
                
            text = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '\n', text)
            text = re.sub(r'\n\s*\n', '\n\n', text).strip()
            
            if "infojobs.net" in url:
                text = _clean_infojobs_noise(text)
                
            text = _post_clean_markdown(text)
            text = _remove_markdown_links(text)
            
            print(f"Scraping Directo exitoso. Longitud: {len(text)}")
            return text
        else:
            print(f"Fallo directo. Codigo: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error en directo: {e}")
        return None

def _clean_url(url: str) -> str:
    """
    Limpia parametros de tracking de la URL para evitar errores 422 en Jina.
    Mantiene solo esquema, dominio y path.
    """
    try:
        parsed = urlparse(url)
        # Reconstruye la URL sin query params (todo lo que va despues de ?)
        clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return clean
    except Exception:
        return url

def _clean_infojobs_noise(text: str) -> str:
    """Limpieza quirurgica para InfoJobs."""
    cutoff_markers = [
        "### Ofertas similares", "Ofertas similares",
        "### Top Subcategorías", "Top Subcategorías",
        "### Top Búsquedas", "Top Búsquedas",
        "### Top Puestos", "### Top Empresas",
        "Los datos bancarios, de pago y datos personales",
        "Consulta nuestros consejos para una búsqueda de empleo segura"
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    body_started = False 
    
    for line in lines:
        stripped = line.strip()
        
        # Deteccion un poco mas laxa del inicio para no perder cabeceras
        if len(stripped) > 50 or "Requisitos" in stripped or "Descripción" in stripped:
            body_started = True
            
        if body_started and any(marker in stripped for marker in cutoff_markers):
            break
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def _remove_markdown_links(text: str) -> str:
    """Elimina los enlaces de Markdown [Texto](URL) dejando solo el Texto."""
    return re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

def _post_clean_markdown(text: str) -> str:
    """Limpieza final de lineas sueltas."""
    lines = text.split('\n')
    cleaned_lines = []
    
    garbage_phrases = [
        "Sign in", "Join now", "Forgot password?", "LinkedIn Corporation", 
        "Cookie Policy", "Agree & Join", "Skip to main content",
        "Adevinta", "Condiciones legales", "Política de privacidad",
        "Uso de cookies", "Denunciar oferta", "Quiénes somos", 
        "enable JavaScript", "support your browser", "Publicada Hace"
    ]
    
    # Whitelist para proteger botones clave
    keep_phrases = [
        "Inscribirme en esta oferta", "Inscribirme", "Solicitar ahora", "Apply now",
        "Presencial", "Híbrido", "Remoto", "Teletrabajo"
    ]
    
    for line in lines:
        stripped = line.strip()
        
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
        print(content) # Mostramos el principio para ver si esta la UBICACION
        print("-" * 60)
        print("Prueba exitosa.")
    else:
        print("Prueba fallida.")