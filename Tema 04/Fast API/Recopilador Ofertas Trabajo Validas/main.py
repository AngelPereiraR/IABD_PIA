# --- FIX WINDOWS ASYNCIO COMPATIBILITY (MUST BE FIRST) ---
# On Windows, force SelectorEventLoop before any async operations
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import time
import os
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Importamos nuestros modulos especialistas (except routers, which are imported after limiter setup)
from src.loader import load_cv_context
from src.mail_agent import GmailJobCollector, save_offer_to_db
from src.scraper import scrape_offer_content
from src.brain import RecruitmentBrain
from src.bot import TelegramNotifier
from src.cv_generator import CVGenerator
from src.api.limiter import set_limiter

# Configuracion
POLLING_INTERVAL = 600  # 10 minutos
CV_PATH = os.path.join("data", "cv_usuario.pdf")

# --- SERVIDOR WEB FAKE (Para engañar a Render) ---
app = FastAPI(
    title="Recopilador Inteligente de Ofertas de Trabajo",
    description=(
        "Automated job offer monitoring and intelligent filtering system. "
        "Monitors job platforms, analyzes offers against user CV with AI, "
        "and sends filtered alerts via Telegram. "
        "Features: OAuth authentication, CV management, AI-powered compatibility scoring, "
        "offer tracking, and CV adaptation for specific opportunities."
    ),
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "ampr2003@gmail.com",
        "url": "https://github.com/AngelPereiraR/IABD_PIA/tree/main/Tema%2004/Fast%20API/Recopilador%20Ofertas%20Trabajo%20Validas"
    },
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
set_limiter(limiter)  # Make limiter available to route modules
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Import routers AFTER limiter is set (to avoid circular import issues)
from src.api import auth_router, cv_router, offers_router, adaptations_router, profile_router

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
app.include_router(auth_router)
app.include_router(cv_router)
app.include_router(offers_router)
app.include_router(adaptations_router)
app.include_router(profile_router)

# Configure OpenAPI schema with Bearer token security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token (received after login or registration)"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get('/')
def home():
    return "Reclutador IA esta vivo y vigilando. 🤖"

@app.get('/health')
def health():
    return "OK"


# --- LOGICA DEL BOT (Hilo Secundario) ---
def run_bot_logic():
    # 0. Cargar variables de entorno (ya cargadas, pero por seguridad)
    load_dotenv()
    print(" [INIT] Iniciando hilo del bot...", flush=True)

    # CRÍTICO: Crear event loop PERSISTENTE en este thread (no reutilizar el de FastAPI)
    # Esto evita el error "Task got Future attached to a different loop"
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    print(" [LOOP] Event loop creado para bot thread", flush=True)

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
                    if not decision:
                        print(f"       [ERROR] Brain retornó None para {url}")
                        continue

                    if decision.get("is_relevant"):
                        print(f"       [MATCH] Persistiendo y enviando alerta.")

                        # Persist to database
                        user_id = os.getenv("USER_ID")
                        if not user_id:
                            print(f"       [ERROR] USER_ID not set in .env")
                            continue

                        try:
                            # Call sync function directly (no event loop needed)
                            offer_id = save_offer_to_db(
                                analysis=decision,
                                offer_url=url,
                                raw_text=offer_markdown,
                                user_id=user_id
                            )
                            print(f"       [DB] Oferta persistida con ID: {offer_id}")

                            # Queue Telegram notification (no bloquea, se envía en background)
                            bot.send_match_alert({"url": url, "offer_id": offer_id}, decision, user_id=user_id, offer_id=offer_id)
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

if not _bot_started:
    _bot_started = True
    bot_thread = threading.Thread(target=run_bot_logic, daemon=True)
    bot_thread.start()
    print(" [SYSTEM] Hilo de Bot lanzado en segundo plano.", flush=True)
    print(" [SYSTEM] Worker de Telegram se ejecuta en Render (servicio separado).", flush=True)

if __name__ == "__main__":
    # Esto solo se ejecuta si lanzas 'python main.py' localmente
    import uvicorn
    port = int(os.environ.get("PORT", 7861))

    # On Windows, create a SelectorEventLoop explicitly BEFORE uvicorn touches it
    if sys.platform == "win32":
        # This ensures uvicorn uses SelectorEventLoop instead of ProactorEventLoop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("[SYSTEM] Using SelectorEventLoop on Windows for psycopg compatibility")

    uvicorn.run(app, host="0.0.0.0", port=port)