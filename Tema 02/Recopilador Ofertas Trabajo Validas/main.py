import time
import os
import sys
from dotenv import load_dotenv

# Importamos nuestros módulos especialistas
from src.loader import load_cv_context
from src.mail_agent import GmailJobCollector
from src.scraper import scrape_offer_content
from src.brain import RecruitmentBrain
from src.bot import TelegramNotifier

# Configuración
POLLING_INTERVAL = 300  # 5 minutos en segundos (evita saturar APIs)
CV_PATH = os.path.join("data", "cv_usuario.pdf")

def main():
    # 0. Cargar variables de entorno
    load_dotenv()
    print("\n" + "="*50)
    print("INICIANDO RECLUTADOR IA PERSONAL (Workbench 1.1)")
    print("="*50 + "\n")

    # --- FASE 1: INICIALIZACIÓN (Cold Start) ---
    print("Fase 1: Inicializando componentes...")

    # A. Cargar Contexto del Usuario (CV)
    try:
        user_cv_context = load_cv_context(CV_PATH)
        if not user_cv_context:
            print("Error Crítico: El CV está vacío o no se pudo leer. Deteniendo sistema.")
            sys.exit(1)
        print("   Contexto de CV cargado en memoria.")
    except Exception as e:
        print(f"Error al cargar CV: {e}")
        sys.exit(1)

    # B. Inicializar Agentes
    try:
        gmail_agent = GmailJobCollector()
        brain = RecruitmentBrain()
        bot = TelegramNotifier()
        print("   Agentes (Gmail, Gemma, Telegram) listos.")
    except Exception as e:
        print(f"Error al inicializar agentes (Revisa tu .env): {e}")
        sys.exit(1)

    print("\nSISTEMA OPERATIVO. Iniciando vigilancia...\n")

    # --- FASE 2: BUCLE DE EJECUCIÓN (Runtime Loop) ---
    loop_count = 0
    
    try:
        while True:
            loop_count += 1
            print("\n" + "="*50)
            print(f"[Ciclo #{loop_count}] Escaneando bandeja de entrada...")
            print("="*50)

            # 1. Buscar Ofertas Nuevas
            urls = gmail_agent.get_offers(limit=3)

            if not urls:
                print(f"   Sin alertas nuevas. Próximo escaneo en {POLLING_INTERVAL/60:.0f} min.")
            else:
                print(f"   Se encontraron {len(urls)} ofertas. Iniciando procesamiento...")

                for i, url in enumerate(urls, 1):
                    print(f"\n   [{i}/{len(urls)}] Procesando: {url}")
                    
                    # 2. Web Scraping (FireCrawl)
                    offer_markdown = scrape_offer_content(url)
                    
                    if not offer_markdown:
                        print("      Saltando: No se pudo obtener contenido.")
                        continue
                    
                    # 3. Análisis Inteligente (Gemma-3)
                    decision = brain.analyze_offer(user_cv_context, offer_markdown)
                    
                    # 4. Toma de Decisión y Notificación
                    if decision.get("match"):
                        print(f"      ¡MATCH! ({decision.get('company')}) -> Enviando alerta.")
                        
                        # Datos mínimos para el bot
                        job_data = {"url": url}
                        
                        success = bot.send_match_alert(job_data, decision)
                        if not success:
                            print("      Error enviando Telegram.")
                    else:
                        print(f"       Descartado. Razón: {decision.get('summary', 'No especificada')}. Umbral de aceptación: {decision.get('match_score', 0)}%")
            
            # Espera inteligente
            print(f"\nDurmiendo {POLLING_INTERVAL} segundos...")
            time.sleep(POLLING_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nSistema detenido manualmente por el usuario. ¡Hasta pronto!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError inesperado en el bucle principal: {e}")
        print("reiniciando en 60 segundos...")
        time.sleep(60)

if __name__ == "__main__":
    main()