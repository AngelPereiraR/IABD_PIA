#!/bin/bash
set -e

echo "🚀 Configurando entorno de desarrollo..."

# Backend - Python
echo "📦 Instalando dependencias del Backend..."
echo "  Verificando Python..."
python3 --version || python --version || { echo "❌ Python no encontrado"; exit 1; }

if [ ! -d ".venv" ]; then
    echo "  Creando venv..."
    python3 -m venv .venv || python -m venv .venv || { echo "❌ Error creando venv"; exit 1; }
    [ -d ".venv" ] && echo "  ✓ Venv creado" || { echo "❌ Venv no se creó"; exit 1; }
fi

echo "  Activando venv..."
[ -f ".venv/bin/activate" ] || { echo "❌ activate no existe en .venv/bin"; ls -la .venv/bin 2>/dev/null || echo "  .venv/bin no existe"; exit 1; }
source .venv/bin/activate

echo "  Actualizando pip..."
pip install --upgrade pip setuptools wheel 2>&1 || true

echo "  Instalando requirements.txt..."
pip install -r requirements.txt || { echo "❌ Falló instalación de requirements"; exit 1; }

echo "✅ Backend configurado"

# Frontend - Node.js
echo "📦 Instalando dependencias del Frontend..."
if [ -d "frontend" ]; then
    cd frontend
    echo "  Instalando npm packages..."
    npm install --legacy-peer-deps || npm ci --legacy-peer-deps || { echo "❌ Falló instalación de npm"; exit 1; }
    cd ..
    echo "✅ Frontend configurado"
else
    echo "⚠️  Carpeta frontend no encontrada, saltando..."
fi

echo "✨ Entorno de desarrollo listo"
