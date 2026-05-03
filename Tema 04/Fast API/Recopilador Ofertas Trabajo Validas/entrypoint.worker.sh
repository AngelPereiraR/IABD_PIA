#!/bin/bash

# Generacion de secretos (Igual que en entrypoint.sh)
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "Creando credentials.json..."
    echo "$GOOGLE_CREDENTIALS_JSON" > credentials.json
fi

if [ -n "$GOOGLE_TOKEN_JSON" ]; then
    echo "Creando token.json..."
    echo "$GOOGLE_TOKEN_JSON" > token.json
fi

if [ -n "$MY_ENV_FILE" ]; then
    echo "Creando .env..."
    echo "$MY_ENV_FILE" > .env
fi

# Usar puerto de env o default 8000 para worker
PORT=${PORT:-8000}
echo "Iniciando Telegram Worker API en puerto $PORT..."

# Arrancamos el worker que ahora es una FastAPI app
exec python telegram_worker.py
