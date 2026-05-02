#!/bin/bash

# Script para ejecutar Backend + Frontend en paralelo
# Se usa en postStartCommand del devContainer

LOG_FILE="/tmp/dev.log"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

{
  echo "🚀 [$(date)] Iniciando ambiente de desarrollo..."
  echo "   Raíz del proyecto: $PROJECT_ROOT"

  # Inicia el backend en background
  echo "📦 [$(date)] Iniciando Backend (FastAPI)..."
  (
    cd "$PROJECT_ROOT"
    source .venv/bin/activate
    python main.py
  ) >> $LOG_FILE 2>&1 &
  BACKEND_PID=$!
  echo "✓ Backend PID: $BACKEND_PID"

  # Inicia el frontend en background
  echo "📦 [$(date)] Iniciando Frontend (Vite)..."
  (
    cd "$PROJECT_ROOT/frontend"
    npm run dev
  ) >> $LOG_FILE 2>&1 &
  FRONTEND_PID=$!
  echo "✓ Frontend PID: $FRONTEND_PID"

  echo ""
  echo "════════════════════════════════════════════════"
  echo "✨ Servidores iniciados"
  echo "════════════════════════════════════════════════"
  echo ""
  echo "📍 URLs disponibles:"
  echo "   Backend:  http://localhost:7861"
  echo "   Frontend: http://localhost:5173"
  echo ""
  echo "📋 Logs: $LOG_FILE"
  echo ""

  # Mantiene ambos procesos ejecutándose
  wait $BACKEND_PID $FRONTEND_PID

} 2>&1 | tee -a $LOG_FILE
