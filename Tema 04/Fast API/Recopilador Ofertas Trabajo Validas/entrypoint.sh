#!/bin/bash

# Generacion de secretos (Igual que antes)
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

# Arrancamos con Uvicorn para produccion
# --host 0.0.0.0: Escucha en todas las interfaces
# --port $PORT: Usa el puerto que asigne Render
# main:app : Archivo main.py, objeto app (FastAPI)
exec uvicorn main:app --host 0.0.0.0 --port $PORT