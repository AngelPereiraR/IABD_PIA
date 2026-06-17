"""
Telegram Worker - Procesa cola de mensajes desde BD
Deployable en Render como API con worker en background
Conecta a PostgreSQL y reintenta enviar mensajes indefinidamente
"""
import os
import time
import sys
import threading
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Agregar src al path para importar módulos
sys.path.insert(0, os.path.dirname(__file__))

from src.database import SessionLocal, TelegramNotification
from src.bot import TelegramNotifier

load_dotenv()

# Flag para evitar iniciar múltiples threads
_worker_started = False

def run_telegram_worker():
    """Worker que procesa cola de Telegram indefinidamente."""
    print("[TELEGRAM WORKER] Iniciando worker en background...", flush=True)

    # Verificar credenciales
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        print("[TELEGRAM WORKER] ERROR: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados", flush=True)
        return

    if not os.getenv("DATABASE_URL"):
        print("[TELEGRAM WORKER] ERROR: DATABASE_URL no configurada", flush=True)
        return

    print("[TELEGRAM WORKER] Conectado a la BD y Telegram", flush=True)
    print("[TELEGRAM WORKER] Procesando cola cada 30 segundos...", flush=True)

    while True:
        try:
            TelegramNotifier.send_queued_messages()
            time.sleep(30)
        except Exception as e:
            print(f"[TELEGRAM WORKER] ERROR: {e}", flush=True)
            time.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia el worker en background al iniciar la app."""
    global _worker_started

    if not _worker_started:
        _worker_started = True
        worker_thread = threading.Thread(target=run_telegram_worker, daemon=True)
        worker_thread.start()
        print("[API] Worker thread iniciado", flush=True)

    yield

    # Cleanup (opcional)
    print("[API] Apagando worker...", flush=True)

# Crear FastAPI app
app = FastAPI(title="Telegram Worker API", lifespan=lifespan)

@app.get("/")
@app.head("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "telegram-worker"}

@app.get("/health")
async def health():
    """Health check endpoint para Render."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
