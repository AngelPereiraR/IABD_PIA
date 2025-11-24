import os
from dotenv import load_dotenv
from firecrawl import Firecrawl

# Cargar variables de entorno al importar el módulo
load_dotenv()

def scrape_offer_content(url: str) -> str:
    """
    Navega a la URL proporcionada y extrae el contenido principal en formato Markdown.
    
    Args:
        url (str): El enlace de la oferta de trabajo.
        
    Returns:
        str: El contenido limpio en Markdown, o None si falla.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not api_key:
        print("Error: No se encontró FIRECRAWL_API_KEY en el archivo .env")
        return None

    try:
        print(f"Iniciando FireCrawl para: {url}...")
        
        app = Firecrawl(api_key=api_key)
        
        response = app.scrape(
            url,
            formats=['markdown'],
            only_main_content=True,
        )
        
        markdown_content = ""
        
        if isinstance(response, dict):
            markdown_content = response.get('markdown', '')
            if not markdown_content and 'data' in response:
                markdown_content = response['data'].get('markdown', '')
        else:
            markdown_content = getattr(response, 'markdown', '')
            
            if not markdown_content:
                data_obj = getattr(response, 'data', None)
                if data_obj:
                    if isinstance(data_obj, dict):
                         markdown_content = data_obj.get('markdown', '')
                    else:
                         markdown_content = getattr(data_obj, 'markdown', '')

        if markdown_content:
            print(f"Scraping exitoso. Longitud del contenido: {len(markdown_content)} caracteres.")
            return markdown_content
        else:
            print("FireCrawl no devolvió contenido Markdown válido.")
            return None

    except Exception as e:
        print(f"Error al scrapear la URL: {e}")
        return None

if __name__ == "__main__":
    # --- PRUEBA UNITARIA ---
    # URL de prueba pública y estable
    test_url = "https://www.ycombinator.com/companies/alinea/jobs/2GVRUn2-full-stack-ios-software-engineer" 
    
    print("Iniciando prueba de Scraping (v1 SDK)...")
    
    content = scrape_offer_content(test_url)
    
    if content:
        print("\n--- VISTA PREVIA DEL MARKDOWN (Primeros 500 caracteres) ---")
        print("-" * 60)
        print(content[:500] + "...")
        print("-" * 60)
        print("La prueba ha sido exitosa.")
    else:
        print("La prueba falló.")