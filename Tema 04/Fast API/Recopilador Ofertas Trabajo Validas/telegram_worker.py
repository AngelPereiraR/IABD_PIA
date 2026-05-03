"""
Telegram Worker - Procesa cola de mensajes desde BD
Deployable en Render/Vercel
Conecta a PostgreSQL y reintenta enviar mensajes indefinidamente
"""
import os
import time
import sys
from dotenv import load_dotenv

# Agregar src al path para importar módulos
sys.path.insert(0, os.path.dirname(__file__))

from src.database import SessionLocal, TelegramNotification
from src.bot import TelegramNotifier

load_dotenv()

def main():
    """Worker principal: procesa cola de Telegram indefinidamente."""
    print("[TELEGRAM WORKER] Iniciando worker...", flush=True)

    # Verificar credenciales
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        print("[TELEGRAM WORKER] ERROR: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados", flush=True)
        sys.exit(1)

    if not os.getenv("DATABASE_URL"):
        print("[TELEGRAM WORKER] ERROR: DATABASE_URL no configurada", flush=True)
        sys.exit(1)

    print("[TELEGRAM WORKER] Conectado a la BD y Telegram", flush=True)
    print("[TELEGRAM WORKER] Procesando cola cada 30 segundos...", flush=True)

    while True:
        try:
            TelegramNotifier.send_queued_messages()
            time.sleep(30)
        except Exception as e:
            print(f"[TELEGRAM WORKER] ERROR: {e}", flush=True)
            time.sleep(30)

if __name__ == "__main__":
    main()
