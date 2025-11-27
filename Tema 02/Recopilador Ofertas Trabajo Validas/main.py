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
    print(" [INIT] Iniciando hilo del bot...", flush=True)

    # --- FASE 1: CARGA DE CONTEXTO (ESTÁTICO) ---
    # El CV y el Brain (Modelo) no necesitan reiniciarse constantemente
    # porque el CV no cambia y el cliente de Gemini gestiona bien su propia sesión.
    try:
        user_cv_context = load_cv_context(CV_PATH)
        if not user_cv_context:
            print(" [ERROR] Error Critico: El CV esta vacio.", flush=True)
            return
        
        # Inicializamos componentes estáticos una vez
        brain = RecruitmentBrain()
        bot = TelegramNotifier()
        print(" [OK] Contexto y Cerebro listos.", flush=True)
        
    except Exception as e:
        print(f" [ERROR] Error de inicializacion: {e}", flush=True)
        return

    print("\n [SISTEMA] OPERATIVO. Iniciando bucle infinito...\n", flush=True)

    # --- FASE 2: BUCLE ---
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            print(f" [LOOP #{loop_count}] Iniciando ciclo...", flush=True)

            # --- REINICIO DE AGENTE GMAIL ---
            # Creamos una nueva instancia del colector en cada vuelta.
            # Esto fuerza a recargar credenciales/tokens y evita timeouts de sesión.
            try:
                print("    [AUTH] Refrescando cliente de Gmail...", flush=True)
                gmail_agent = GmailJobCollector()
            except Exception as e:
                print(f"    [ERROR] Fallo al conectar con Gmail: {e}", flush=True)
                print("    [WAIT] Reintentando en 60s...", flush=True)
                time.sleep(60)
                continue # Saltamos al siguiente ciclo del while

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

# --- CORRECCION CRITICA PARA GUNICORN ---
# Arrancamos el hilo aqui, FUERA del bloque main, para que Gunicorn lo ejecute al importar
# Usamos una variable global para evitar arrancar hilos duplicados si Gunicorn reinicia workers
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    # Verificacion simple para evitar doble ejecucion en modo debug local
    bot_thread = threading.Thread(target=run_bot_logic, daemon=True)
    bot_thread.start()
    print(" [SYSTEM] Hilo de Bot lanzado en segundo plano.", flush=True)

if __name__ == "__main__":
    # Esto solo se ejecuta si lanzas 'python main.py' localmente
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)