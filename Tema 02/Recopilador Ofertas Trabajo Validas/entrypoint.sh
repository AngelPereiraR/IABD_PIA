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

# Arrancamos con Gunicorn para produccion (mas estable que Flask directo)
# -w 1: Un solo worker (suficiente y ahorra RAM en free tier)
# -b 0.0.0.0:$PORT: Escucha en el puerto que asigne Render
# main:app : Archivo main.py, objeto app (Flask)
exec gunicorn -w 1 -b 0.0.0.0:$PORT main:app