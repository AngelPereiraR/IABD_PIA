import time
import os
import sys
import threading
from flask import Flask
from dotenv import load_dotenv

# Importamos nuestros modulos especialistas
from src.loader import load_cv_context
from src.mail_agent import GmailJobCollector
from src.scraper import scrape_offer_content
from src.brain import RecruitmentBrain
from src.bot import TelegramNotifier

# Configuracion
POLLING_INTERVAL = 600  # 10 minutos
CV_PATH = os.path.join("data", "cv_usuario.pdf")

# --- SERVIDOR WEB FAKE (Para engañar a Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Reclutador IA esta vivo y vigilando. 🤖"

@app.route('/health')
def health():
    return "OK", 200

# --- LOGICA DEL BOT (Hilo Secundario) ---
def run_bot_logic():
    # 0. Cargar variables de entorno (ya cargadas, pero por seguridad)
    load_dotenv()
    print("\n" + "="*50)
    print(" INICIANDO RECLUTADOR IA PERSONAL (Modo Web Service)")
    print("="*50 + "\n")

    # --- FASE 1: INICIALIZACION ---
    print(" [INFO] Fase 1: Inicializando componentes...")

    try:
        user_cv_context = load_cv_context(CV_PATH)
        if not user_cv_context:
            print(" [ERROR] Error Critico: El CV esta vacio.")
            return # Salimos del hilo, no del programa
        print(" [OK] Contexto de CV cargado.")
    except Exception as e:
        print(f" [ERROR] Error al cargar CV: {e}")
        return

    try:
        gmail_agent = GmailJobCollector()
        brain = RecruitmentBrain()
        bot = TelegramNotifier()
        print(" [OK] Agentes listos.")
    except Exception as e:
        print(f" [ERROR] Error al inicializar agentes: {e}")
        return

    print("\n [SISTEMA] OPERATIVO. Iniciando bucle...\n")

    # --- FASE 2: BUCLE ---
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            print(f" [LOOP #{loop_count}] Escaneando bandeja...")

            urls = gmail_agent.get_offers(limit=5)

            if not urls:
                print(f"    - Sin alertas. Proximo escaneo en {POLLING_INTERVAL/60:.0f} min.")
            else:
                print(f"    + Se encontraron {len(urls)} ofertas.")
                for i, url in enumerate(urls, 1):
                    print(f"\n    [{i}/{len(urls)}] Procesando: {url}")
                    
                    offer_markdown = scrape_offer_content(url)
                    if not offer_markdown:
                        continue
                    
                    decision = brain.analyze_offer(user_cv_context, offer_markdown)
                    
                    if decision.get("match"):
                        print(f"       [MATCH] Enviando alerta.")
                        bot.send_match_alert({"url": url}, decision)
                    else:
                        print(f"       [DESCARTADO] {decision.get('summary')[:50]}...")
            
            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            print(f" [CRITICAL] Error en bucle: {e}")
            time.sleep(60)

# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    # 1. Arrancar el Bot en un hilo separado
    # Daemon=True significa que si el servidor web muere, el bot tambien.
    bot_thread = threading.Thread(target=run_bot_logic, daemon=True)
    bot_thread.start()
    
    # 2. Arrancar el Servidor Web (Bloqueante)
    # Render asigna un puerto en la variable PORT
    port = int(os.environ.get("PORT", 10000))
    # Usamos 0.0.0.0 para que sea visible desde fuera del contenedor
    app.run(host="0.0.0.0", port=port)