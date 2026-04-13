import time
import os
import sys
import threading
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Importamos nuestros modulos especialistas
from src.loader import load_cv_context
from src.mail_agent import GmailJobCollector, save_offer_to_db
from src.scraper import scrape_offer_content
from src.brain import RecruitmentBrain
from src.bot import TelegramNotifier
from src.cv_generator import CVGenerator
from src.api import cv_router, offers_router
from telegram.ext import Application, CallbackQueryHandler

# Configuracion
POLLING_INTERVAL = 600  # 10 minutos
CV_PATH = os.path.join("data", "cv_usuario.pdf")

# --- SERVIDOR WEB FAKE (Para engañar a Render) ---
app = FastAPI()

# CORS para dashboard (Vercel frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # Vite dev
        "https://opticv.vercel.app",       # Producción Vercel
        "https://opticv-engine.hf.space",  # HF Spaces
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de API
app.include_router(cv_router)
app.include_router(offers_router)

@app.get('/')
def home():
    return "Reclutador IA esta vivo y vigilando. 🤖"

@app.get('/health')
def health():
    return "OK"

# --- TELEGRAM POLLING SETUP ---
def setup_telegram_polling():
    """
    Configures and runs Telegram polling with callback handlers.
    Runs synchronously in its own thread — Application.run_polling() manages
    its own event loop internally (python-telegram-bot v20+).

    Handles inline button callbacks with pattern "gen_cv:offer_id"
    """
    try:
        telegram_app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

        # Register handler for "gen_cv:offer_id" callbacks
        telegram_app.add_handler(
            CallbackQueryHandler(
                TelegramNotifier().handle_generate_cv_callback,
                pattern="^gen_cv:"
            )
        )

        print(" [TELEGRAM] Iniciando polling de Telegram...", flush=True)
        telegram_app.run_polling()
    except Exception as e:
        print(f" [TELEGRAM] Error en polling: {e}", flush=True)

# --- LOGICA DEL BOT (Hilo Secundario) ---
def run_bot_logic():
    # 0. Cargar variables de entorno (ya cargadas, pero por seguridad)
    load_dotenv()
    print(" [INIT] Iniciando hilo del bot...", flush=True)

    # --- FASE 1: CARGA DE CONTEXTO (ESTÁTICO) ---
    # El CV y el Brain (Modelo) no necesitan reiniciarse constantemente
    # porque el CV no cambia y el cliente de DeepSeek gestiona bien su propia sesión.
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

                    if decision.get("is_relevant"):
                        print(f"       [MATCH] Persistiendo y enviando alerta.")

                        # Persist to database
                        user_id = os.getenv("USER_ID")
                        if not user_id:
                            print(f"       [ERROR] USER_ID not set in .env")
                            continue

                        try:
                            offer_id = asyncio.run(save_offer_to_db(
                                analysis=decision,
                                offer_url=url,
                                raw_text=offer_markdown,
                                user_id=user_id
                            ))
                            print(f"       [DB] Oferta persistida con ID: {offer_id}")

                            # Send Telegram notification with offer_id embedded
                            bot.send_match_alert({"url": url, "offer_id": offer_id}, decision)
                        except Exception as e:
                            print(f"       [ERROR] Error persisting offer: {e}")
                    else:
                        print(f"       [DESCARTADO] {decision.get('summary')[:50]}...")
            
            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            print(f" [CRITICAL] Error en bucle: {e}")
            time.sleep(60)

# --- CORRECCION CRITICA PARA UVICORN ---
# Arrancamos el hilo aqui, FUERA del bloque main, para que Uvicorn lo ejecute al importar
# Usamos una variable global para evitar arrancar hilos duplicados si Uvicorn reinicia workers
_bot_started = False
_telegram_polling_started = False

if not _bot_started:
    _bot_started = True
    bot_thread = threading.Thread(target=run_bot_logic, daemon=True)
    bot_thread.start()
    print(" [SYSTEM] Hilo de Bot lanzado en segundo plano.", flush=True)

if not _telegram_polling_started:
    _telegram_polling_started = True
    telegram_thread = threading.Thread(target=setup_telegram_polling, daemon=True)
    telegram_thread.start()
    print(" [SYSTEM] Hilo de Telegram Polling lanzado en segundo plano.", flush=True)

if __name__ == "__main__":
    # Esto solo se ejecuta si lanzas 'python main.py' localmente
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)