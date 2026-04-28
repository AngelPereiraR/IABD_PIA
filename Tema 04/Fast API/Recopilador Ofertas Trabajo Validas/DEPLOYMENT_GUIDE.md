# 🚀 Deployment Guide - OpticsV (Distributed Architecture)

Guía completa para desplegar OpticsV con **Backend en Hugging Face Spaces** y **Frontend en Vercel/Render**.

---

## 📋 Tabla de Contenidos

- [Arquitectura de Despliegue](#-arquitectura-de-despliegue)
- [Backend en Hugging Face Spaces](#-backend-en-hugging-face-spaces)
- [Frontend en Vercel](#-frontend-en-vercel)
- [Frontend en Render](#-frontend-en-render)
- [Configuración de Conexión](#-configuración-de-conexión)
- [Troubleshooting](#-troubleshooting)
- [Monitoreo y Mantenimiento](#-monitoreo-y-mantenimiento)

---

## 🏗️ Arquitectura de Despliegue

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCCIÓN                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐         ┌──────────────────────┐  │
│  │   VERCEL            │         │  HUGGING FACE SPACES │  │
│  │   (Frontend)        │────────▶│  (Backend)           │  │
│  │                     │         │                      │  │
│  │ React + Vite 6      │         │ FastAPI + Uvicorn    │  │
│  │ TailwindCSS         │  REST   │ PostgreSQL (ext)     │  │
│  │ Zustand State       │  API    │ LangChain + DeepSeek │  │
│  │ Auto Deploy (Git)   │  :7860  │ Cloudinary           │  │
│  └─────────────────────┘         └──────────────────────┘  │
│   https://opticv.vercel.app    https://opticv-engine.hf.space│
│                                                             │
│  External Services:                                        │
│  • PostgreSQL (Railway / Neon / AWS RDS)                  │
│  • Google OAuth (Gmail)                                   │
│  • Cloudinary (PDF Storage)                               │
│  • LLM API (DeepSeek / Gemini)                           │
│  • Telegram (Notifications - Optional)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Backend en Hugging Face Spaces

Hugging Face Spaces es ideal para FastAPI porque:
- ✅ Soporte nativo para Python/FastAPI
- ✅ Permanencia de datos en disco
- ✅ Base de datos externa (PostgreSQL)
- ✅ Variables de entorno seguras
- ✅ SSL/HTTPS automático
- ✅ GPU disponible (si necesario)

### Paso 1: Preparar el Repositorio

#### 1.1 Estructura de archivos para HF Spaces

Crea en la raíz un archivo `app.py` (puede ser un symlink a `main.py`):

```bash
# En la raíz del proyecto
cp main.py app.py
# O crea un alias
ln -s main.py app.py  # Linux/Mac
mklink app.py main.py # Windows
```

#### 1.2 Archivo `requirements.txt` actualizado

Verifica que está en la raíz del proyecto con todas las dependencias.

#### 1.3 Crear archivo `.gitignore` si no existe

```
.venv/
__pycache__/
*.pyc
.env
.env.local
.DS_Store
*.pdf
node_modules/
dist/
credentials.json
token.json
.vercel/
```

### Paso 2: Crear Space en Hugging Face

1. Ve a https://huggingface.co/new-space
2. **Space name**: `opticv-backend` (o el que prefieras)
3. **Space type**: `Docker` (recomendado para FastAPI)
4. **Visibility**: `Private` (seguridad) o `Public` si prefieres
5. Click **Create space**

### Paso 3: Pushear Código a HF

```bash
# Clonar el space recién creado
git clone https://huggingface.co/spaces/tu-usuario/opticv-backend
cd opticv-backend

# Copiar archivos de tu proyecto
# Copia main.py, requirements.txt, src/, etc.

# Push a HF
git add .
git commit -m "Initial FastAPI backend"
git push
```

### Paso 4: Configurar Variables de Entorno

En el **Space → Settings → Repository Secrets**, añade:

```
DATABASE_URL = postgresql+asyncpg://user:pass@host/db
SECRET_KEY = tu_secret_key_super_segura
DEEPSEEK_API_KEY = sk-xxxx
CLOUDINARY_NAME = xxxx
CLOUDINARY_API_KEY = xxxx
CLOUDINARY_API_SECRET = xxxx
GOOGLE_CREDENTIALS_JSON = {"installed":{...}}
GOOGLE_TOKEN_JSON = {"token":"..."}
JINA_API_KEY = jina_xxxx            # Scraping primario
TELEGRAM_BOT_TOKEN = xxxx (opcional)
TELEGRAM_CHAT_ID = xxxx (opcional)
PORT = 7860                          # Default para HF Spaces
```

### Paso 5: Configurar Dockerfile (opcional pero recomendado)

Si usas Docker en HF Spaces, crea `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FastAPI en puerto 7860 (default de HF Spaces)
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Paso 6: Inicializar base de datos y usuario admin

Tras el primer deploy, ejecuta desde tu entorno local (o via HF terminal):

```bash
# Crear tablas
python init_db.py

# Aplicar migraciones
alembic upgrade head

# Inicializar usuario admin con CV y avatar en Cloudinary
python seed_user.py
```

### Paso 7: Monitoreo en HF Spaces

- El space automáticamente:
  - Detecta cambios en git
  - Reconstruye la imagen
  - Reinicia la aplicación
  - Proporciona logs en tiempo real

**URL del backend**: `https://opticv-engine.hf.space`

---

## 🎨 Frontend en Vercel

### Requisitos Previos

- Cuenta en Vercel (https://vercel.com)
- Repositorio GitHub con el código frontend

### Paso 1: Conectar Repositorio a Vercel

1. Ve a https://vercel.com/new
2. Selecciona **Import Git Repository**
3. Elige tu repositorio GitHub
4. Configure el Import:
   - **Project name**: `opticv-frontend`
   - **Root Directory**: `frontend/` (si es monorepo)
   - **Framework Preset**: `Vite`
5. Click **Import**

### Paso 2: Configurar Build Settings

Vercel automáticamente detecta Vite, pero verifica:

```
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### Paso 3: Variables de Entorno en Vercel

En **Project Settings → Environment Variables**, añade:

```
VITE_API_URL = https://opticv-engine.hf.space
VITE_GOOGLE_CLIENT_ID = tu_google_client_id_production
```

**Importante**: 
- Aplica a: **Production**, **Preview**, **Development**
- VITE_ prefix es requerido por Vite

### Paso 4: Deploy

```bash
# Automático: Push a GitHub y Vercel hace deploy automáticamente
git push origin main

# O manual con Vercel CLI:
npm install -g vercel
cd frontend
vercel --prod
```

### Paso 5: Verificar Deployment

- [ ] Accede a `https://opticv.vercel.app`
- [ ] Comprueba que carga sin errores
- [ ] Abre DevTools → Console y busca errores
- [ ] Verifica que `VITE_API_URL` apunta a `https://opticv-engine.hf.space`
- [ ] Prueba login (debe conectar con backend en HF)

### Troubleshooting Vercel

**Build falla:**
```bash
# Verifica que package.json tiene "build" script
npm run build  # Debe funcionar localmente primero
```

**CORS errors:**
```
→ Verifica que backend tiene CORS configurado para Vercel URL
→ En main.py: allow_origins incluye vercel.app domain
```

---

## 🚀 Frontend en Render (Alternativa a Vercel)

Si prefieres Render en lugar de Vercel:

### Paso 1: Crear Web Service en Render

1. Ve a https://dashboard.render.com
2. **New** → **Web Service**
3. Conecta tu repositorio GitHub
4. Configuración:
   - **Name**: `opticv-frontend`
   - **Environment**: `Node`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Start Command**: `npm run preview`
   - **Root Directory**: (dejar vacío o `/`)

### Paso 2: Variables de Entorno en Render

En **Environment → Environment Variables**:

```
VITE_API_URL = https://opticv-engine.hf.space
VITE_GOOGLE_CLIENT_ID = tu_google_client_id
```

### Paso 3: Deploy

Click **Create Web Service** y Render hace deploy automáticamente.

---

## 🔗 Configuración de Conexión

### Paso 1: Actualizar CORS en Backend (main.py)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",                # Local dev
        "https://opticv.vercel.app",            # Vercel producción
        "https://opticv-engine.hf.space",       # HF Spaces (self)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Paso 2: Verificar apiClient.js

```javascript
// frontend/src/services/apiClient.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:7860';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});
// El token Bearer se añade via interceptor de request
```

### Paso 3: Probar Conexión

En el navegador, abre la consola DevTools y ejecuta:

```javascript
fetch('https://opticv-engine.hf.space/health')
  .then(r => r.json())
  .then(console.log)
  .catch(e => console.error('Error:', e))
```

Debe retornar `{"status":"ok"}` o similar.

---

## 🗄️ Base de Datos Persistente

### Opción A: Railway (Recomendado)

1. Ve a https://railway.app
2. **New Project** → **PostgreSQL**
3. Copia `DATABASE_URL` completa
4. Añade a **HF Spaces Secrets**:
   ```
   DATABASE_URL = postgresql+asyncpg://...
   ```

### Opción B: Neon

1. Ve a https://console.neon.tech
2. Crea un proyecto PostgreSQL
3. Copia **Connection String**
4. Cámbialo a asyncpg:
   ```
   postgresql+asyncpg://user:pass@host/db
   ```

### Opción C: AWS RDS

Para producción más robusta, usa RDS, pero requiere setup más complejo.

---

## 📝 Checklist Pre-Producción

### Backend (HF Spaces)

- [ ] Dockerfile funciona localmente
- [ ] `requirements.txt` actualizado
- [ ] Variables de entorno configuradas en HF
- [ ] Base de datos externa conectada
- [ ] CORS permite frontend URL
- [ ] `/health` endpoint funciona
- [ ] Logs visibles en HF Spaces

### Frontend (Vercel/Render)

- [ ] `npm run build` funciona localmente
- [ ] `VITE_API_URL` apunta a backend HF
- [ ] Variables de entorno en Vercel/Render
- [ ] Login funciona con backend en HF
- [ ] CV upload funciona
- [ ] Análisis completo funciona
- [ ] Descargas de PDF funcionan

### Integración

- [ ] Frontend conecta a backend sin CORS errors
- [ ] Autenticación JWT funciona
- [ ] Rate limiting activo
- [ ] Errores se manejan gracefully
- [ ] Carga es rápida (<3s TTI)

---

## 🐛 Troubleshooting

### CORS Errors

**Error**: `Access to XMLHttpRequest blocked by CORS`

**Solución**:
```python
# En main.py, verifica que tu Vercel/Render URL está en allow_origins
# Y asegúrate de usar https, no http
```

### Backend no responde

**Error**: `502 Bad Gateway` en Vercel

**Solución**:
```bash
# Verifica logs en HF Spaces
# Asegúrate que el servicio está ejecutándose
# Comprueba DATABASE_URL es correcta
```

### Variables de entorno no funcionan

**Error**: `KeyError: VITE_API_URL` o `None`

**Solución**:
- Frontend: Verifica `VITE_` prefix
- Backend: Verifica nombres exactos en `.env`
- Reinicia el build después de cambiar env vars

### Base de datos no conecta

**Error**: `asyncpg.exceptions.PostgresError`

**Solución**:
```bash
# En local, prueba:
python -c "import asyncpg; print('OK')"

# Verifica DATABASE_URL:
# postgresql+asyncpg://user:pass@host:port/dbname
#                    ^-- asyncpg es importante
```

### PDF download no funciona

**Error**: `403 Forbidden` desde Cloudinary

**Solución**:
```
→ Verifica CLOUDINARY_API_KEY en HF Secrets
→ Asegúrate que Cloudinary_NAME es correcto
→ Prueba PDF upload localmente primero
```

### Análisis fallan

**Error**: `LLM API Error` o `Rate Limit`

**Solución**:
```
→ Verifica DEEPSEEK_API_KEY (o GOOGLE_GEMINI_API_KEY)
→ Comprueba que tienes saldo en API
→ Revisa rate limiting en slowapi
```

---

## 📊 Monitoreo y Mantenimiento

### Monitoreo Diario

**HF Spaces:**
- Visita https://huggingface.co/spaces/tu-usuario/opticv-backend
- Comprueba logs recientes
- Verifica que el status es "RUNNING"

**Vercel:**
- Visita https://vercel.com/dashboard
- Revisa últimos deployments
- Comprueba analytics

### Alertas Recomendadas

Configura notificaciones para:
- Fallos de deployment
- Errores 5xx en backend
- Uso alto de API
- Latencia > 2s

### Actualizaciones de Dependencias

**Mensual:**
```bash
# Backend
pip list --outdated
pip install --upgrade <package>

# Frontend
npm outdated
npm update
```

**Trimestral:**
```bash
# Actualiza Python minor version
# Actualiza Node.js LTS
# Revisa breaking changes en dependencias clave
```

---

## 🔄 CI/CD Automático

### GitHub Actions (Backend)

Crear `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy Backend to HF Spaces

on:
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'requirements.txt'
      - 'main.py'
      - '.github/workflows/deploy-backend.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Push to HF Spaces
        run: |
          git config --global user.email "ci@example.com"
          git config --global user.name "CI Bot"
          git remote add hf https://${{ secrets.HF_USERNAME }}:${{ secrets.HF_TOKEN }}@huggingface.co/spaces/${{ secrets.HF_USERNAME }}/opticv-backend
          git push -u hf main
```

### GitHub Actions (Frontend)

Vercel se integra automáticamente, pero puedes añadir checks:

```yaml
name: Frontend Tests & Deploy

on:
  push:
    branches: [main]
    paths: ['frontend/**']
  pull_request:
    paths: ['frontend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: cd frontend && npm run build
      # Vercel se despliega automáticamente
```

---

## 🚨 Rollback

### Si algo falla en producción

**Backend (HF Spaces):**
```bash
# Vuelve al commit anterior
git revert <commit-hash>
git push
# HF Spaces detecta cambios y redeploy automáticamente
```

**Frontend (Vercel):**
1. Dashboard Vercel → Deployments
2. Selecciona la versión anterior
3. Click "Promote to Production"

---

## 📋 Checklist de Seguridad

- [ ] No hay secretos en GitHub (usa env vars)
- [ ] HTTPS en todas las URLs
- [ ] CORS solo permite dominios conocidos
- [ ] Rate limiting activo
- [ ] Passwords hasheados con bcrypt
- [ ] JWT tokens con expiración
- [ ] No hay logs con datos sensibles
- [ ] Cloudinary tiene restricciones de acceso
- [ ] Base de datos tiene backups automáticos
- [ ] API keys no expuestos en frontend

---

## 📞 Soporte

Si tienes problemas:

1. Revisa logs:
   - Backend: HF Spaces dashboard
   - Frontend: Vercel analytics
   - Browser: DevTools console

2. Comprueba:
   - Variables de entorno (todas)
   - URLs (https://, no http://)
   - CORS (frontend URL en allow_origins)
   - Database (conecta correctamente)

3. Contacta:
   - GitHub Issues para bugs
   - Documentación de cada plataforma
   - Discord/comunidad de HF/Vercel

---

**⚡ ¡Despliegue completado! 🎉**
