# 🚀 Deployment Guide - OptiCV (Distributed Architecture)

Guía completa para desplegar OptiCV con **Backend en Hugging Face Spaces** (vía GitHub Actions), **Worker de Telegram en Render** y **Frontend en Vercel**.

---

## 📋 Tabla de Contenidos

- [Arquitectura de Despliegue](#-arquitectura-de-despliegue)
- [Setup Inicial](#-setup-inicial)
- [Backend en Hugging Face Spaces](#-backend-en-hugging-face-spaces)
- [Telegram Worker en Render](#-telegram-worker-en-render)
- [Frontend en Vercel](#-frontend-en-vercel)
- [Configuración de Conexión](#-configuración-de-conexión)
- [Checklist Pre-Producción](#-checklist-pre-producción)
- [Troubleshooting](#-troubleshooting)
- [Monitoreo y Mantenimiento](#-monitoreo-y-mantenimiento)

---

## 🏗️ Arquitectura de Despliegue

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PRODUCCIÓN                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────┐      ┌──────────────────────┐                │
│  │ VERCEL FRONTEND    │      │ HUGGING FACE SPACES  │                │
│  │ (React + Vite)     │◀───▶│ (FastAPI + Uvicorn)  │                │
│  │ :5173 (dev)        │  ↑   │ :7860                │                │
│  │ vercel.app (prod)  │  │   │ hf.space (prod)      │                │
│  └────────────────────┘  │   └──────────────────────┘                │
│                          │            ▲                              │
│          GitHub Push     │            │ Mensaje Bot                  │
│         (Vercel CI)      │            │ (Telegram API)               │
│                          │            ▼                              │
│                      ┌──────────────────────────────┐                │
│                      │  RENDER WORKER               │                │
│                      │  (Telegram Bot Processor)    │                │
│                      │  Dockerfile.worker           │                │
│                      │  :8000 (health checks)       │                │
│                      │  render.com (prod)           │                │
│                      └──────────────────────────────┘                │
│                               ▲                                      │
│                               │ Lee cola de BD                       │
│                               │ cada 30s                             │
│                               ▼                                      │
│                      ┌──────────────────────┐                        │
│                      │  PostgreSQL (Neon)   │                        │
│                      │  (Persistencia)      │                        │
│                      └──────────────────────┘                        │
│                                                                      │
│  External Services:                                                  │
│  • Google OAuth (Gmail) → mail_agent.py                              │
│  • DeepSeek API (LLM) → brain.py                                     │
│  • Cloudinary (PDF Storage) → loader.py                              │
│  • Jina AI / FireCrawl (Scraping) → scraper.py                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

FLUJO DE DESPLIEGUE:
  1. GitHub Push → .github/workflows/deploy-to-hf.yml
  2. GitHub Actions → Push a HF Space (rama main)
  3. HF Spaces detecta cambios → Build Dockerfile → Deploy
  4. Frontend push → Vercel CI detecta automáticamente
  5. Render Worker corre independientemente (lee BD)

⚠️ NOTA IMPORTANTE - Por qué el Worker está separado:
  • HF Spaces tiene restricciones de red para APIs REST externas
  • Telegram API requiere conexiones persistentes y timeouts largos
  • HF Spaces puede bloquear/interrumpir estas conexiones
  • SOLUCIÓN: Desacoplar el envío a un servicio independiente (Render)
  • Beneficio: Mayor confiabilidad, reintentos automáticos, sin bloqueos
```

---

## 🔧 Setup Inicial

Antes de desplegar, asegúrate de tener todo configurado localmente:

### 1. Estructura de carpetas esperada

```
.
├── main.py                      # Punto de entrada (FastAPI + Bot thread)
├── requirements.txt             # Dependencias Python
├── Dockerfile                   # Backend: HF Spaces + GitHub Actions
├── Dockerfile.worker            # Worker: Telegram en Render
├── Dockerfile.frontend          # Frontend: opcional (local dev)
├── entrypoint.sh               # Script de inicio para backend
├── entrypoint.worker.sh        # Script de inicio para worker
├── .github/
│   └── workflows/
│       └── deploy-to-hf.yml    # GitHub Actions workflow
├── src/
│   ├── mail_agent.py           # Gmail OAuth
│   ├── scraper.py              # Web scraping
│   ├── brain.py                # DeepSeek AI analysis
│   ├── bot.py                  # Telegram bot
│   ├── loader.py               # CV loader
│   └── setup_auth.py           # OAuth setup
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.production
│   └── ...
├── data/
│   └── cv_usuario.pdf          # CV para análisis
└── tests/
    └── test_plan_*.py
```

### 2. Variables de entorno globales

Crear `.env` local (NO hacer push a GitHub):

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Gmail OAuth
GOOGLE_CREDENTIALS_JSON='{"installed":{...}}'
GOOGLE_TOKEN_JSON='{"token":"..."}'

# DeepSeek LLM
DEEPSEEK_API_KEY=sk-xxxx

# Cloudinary (PDF storage)
CLOUDINARY_NAME=xxxx
CLOUDINARY_API_KEY=xxxx
CLOUDINARY_API_SECRET=xxxx

# Jina AI (Scraping primario)
JINA_API_KEY=jina_xxxx

# FireCrawl (Scraping fallback)
FIRECRAWL_API_KEY=fcrawl_xxxx

# Telegram (Bot + Worker)
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=987654321

# Server
PORT=7860
SECRET_KEY=tu_secret_key_muy_segura
```

---

## ⚙️ Backend en Hugging Face Spaces

El backend se despliega automáticamente via GitHub Actions cuando haces push a `main`.

### Paso 1: Preparar el repositorio

Verifica que tengas:

- ✅ `main.py` en la raíz (punto de entrada)
- ✅ `requirements.txt` actualizado con todas las dependencias
- ✅ `Dockerfile` (multi-stage, optimizado)
- ✅ `entrypoint.sh` (inyecta secrets en credenciales)
- ✅ `src/` con todos los módulos
- ✅ `data/cv_usuario.pdf` existe
- ✅ `.github/workflows/deploy-to-hf.yml` configurado

### Paso 2: Configurar GitHub Secrets

En tu repositorio GitHub:

1. Ve a **Settings → Secrets and variables → Actions**
2. Añade estos secrets (todos obligatorios):

```
HF_TOKEN              # Token de Hugging Face (https://huggingface.co/settings/tokens)
```

**Cómo obtener HF_TOKEN:**

- Ve a https://huggingface.co/settings/tokens
- Crea un nuevo token con permisos de escritura (write)
- Cópialo y añádelo como `HF_TOKEN` en GitHub Secrets

### Paso 3: Crear el Space en Hugging Face

1. Ve a https://huggingface.co/new-space
2. Configura:
   - **Space name**: `opticv-backend`
   - **License**: Selecciona una (MIT recomendado)
   - **Visibility**: `Private` (para seguridad)
3. Click **Create space**
4. ⚠️ NO hagas push manual—GitHub Actions lo hará automáticamente

### Paso 4: Configurar Variables de Entorno en HF Spaces

En tu Space de HF:

1. Ve a **Settings → Repository secrets**
2. Añade todas estas variables:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
SECRET_KEY=tu_secret_key_super_segura
DEEPSEEK_API_KEY=sk-xxxx
CLOUDINARY_NAME=xxxx
CLOUDINARY_API_KEY=xxxx
CLOUDINARY_API_SECRET=xxxx
GOOGLE_CREDENTIALS_JSON={"installed":{...}}
GOOGLE_TOKEN_JSON={"token":"..."}
JINA_API_KEY=jina_xxxx
FIRECRAWL_API_KEY=fcrawl_xxxx
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=987654321
PORT=7860
```

### Paso 5: Entender el flujo de GitHub Actions

Cuando hagas `git push` a `main`:

1. GitHub Actions ejecuta `.github/workflows/deploy-to-hf.yml`
2. El workflow:
   - Clona tu repositorio
   - Copia la carpeta `Tema 04/Fast API/Recopilador Ofertas Trabajo Validas` a `/tmp/hf-space`
   - Inicializa git local en esa carpeta
   - Configura Git LFS para archivos binarios (`.pdf`, `.jpg`, `.png`)
   - Hace commit de todos los cambios
   - Pushea a `https://huggingface.co/spaces/AngelPereiraR/opticv-backend`
3. HF Spaces detecta el push:
   - Build del Dockerfile
   - Deploy automático
   - Logs visibles en tiempo real

### Paso 6: Monitorear el despliegue

Tras hacer `git push`:

1. Ve a tu repositorio GitHub → **Actions**
2. Verifica que el workflow `Deploy to Hugging Face Space` está en verde
3. Ve a https://huggingface.co/spaces/tu-usuario/opticv-backend
4. En la pestaña **Logs**, verás:
   ```
   Building Docker image...
   Installing dependencies...
   [TELEGRAM WORKER] Iniciando bot...
   Starting Uvicorn server...
   ```
5. Cuando veas `Uvicorn running on 0.0.0.0:7860`, el deploy está completo

### Paso 7: Verificar el backend

```bash
# En tu navegador o curl:
curl https://opticv-backend.hf.space/health

# Debe retornar:
# {"status":"ok"}
```

---

## 🤖 Telegram Worker en Render

El Worker de Telegram es un servicio independiente que procesa la cola de notificaciones en la BD.

### ¿Por qué un worker separado en Render?

**Restricciones de HF Spaces con Telegram API:**

HF Spaces ejecuta contenedores con restricciones severas de red que **interfieren con la API de Telegram**:

- 🔴 Conexiones persistentes → bloqueadas/interrumpidas
- 🔴 Timeouts extensos → HF puede terminar la conexión antes de que llegue la respuesta
- 🔴 Rate limiting → conexiones HTTP pueden ser limitadas
- 🔴 Reintentos → muy complejos de implementar de forma confiable

**Resultado en HF Spaces:** Los mensajes se pierden sin forma de recuperarlos.

**Solución: Desacoplamiento mediante Render Worker**

```
HF Spaces (main.py)          Render Worker
    │                            │
    ├─ Análisis offer            │
    ├─ Inserta en BD             │
    └─ INSERT telegram_          ├─ Lee BD cada 30s
       notifications (pending)    ├─ Intenta enviar
                                  ├─ Reintenta si falla
                                  └─ Marca como enviado
```

- ✅ El backend guarda mensajes, **no intenta enviarlos**
- ✅ Render Worker corre independientemente con mejor conectividad
- ✅ Implementa reintentos automáticos si Telegram API falla
- ✅ Render es gratuito y perfecto para tareas periódicas
- ✅ Desacoplamiento: análisis y envío son independientes

**Beneficios de esta arquitectura:**

| Aspecto           | HF Spaces Directo ❌ | Con Render Worker ✅   |
| ----------------- | -------------------- | ---------------------- |
| **Confiabilidad** | Mensajes se pierden  | Reintentos indefinidos |
| **Latencia**      | Bloquea análisis     | Análisis no afectado   |
| **Conectividad**  | Restricciones de red | Conexión normal        |
| **Costo**         | Gratuito (limitado)  | Gratuito (free tier)   |
| **Recuperación**  | Imposible            | Automática             |

### Paso 1: Crear un nuevo servicio en Render

1. Ve a https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Conecta tu repositorio GitHub (la rama `main`)

### Paso 2: Configurar el servicio

En la pantalla de creación:

| Campo               | Valor                    |
| ------------------- | ------------------------ |
| **Name**            | `opticv-telegram-worker` |
| **Environment**     | `Docker`                 |
| **Repository**      | Tu repo GitHub           |
| **Branch**          | `main`                   |
| **Dockerfile Path** | `Dockerfile.worker`      |
| **Plan**            | `Free` (suficiente)      |

### Paso 3: Configurar variables de entorno

En **Environment Variables**, añade exactamente las mismas que en HF Spaces:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=987654321
PORT=8000
```

⚠️ **Importante:**

- Usa el **mismo** `DATABASE_URL`, `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` que en HF Spaces
- El `PORT` en Render puede ser 8000 (el healthcheck lo encontrará)

### Paso 4: Deploy y monitoreo

1. Click **Create Web Service**
2. Render hace build y deployment automático
3. En la pestaña **Logs**, busca:
   ```
   [TELEGRAM WORKER] Iniciando worker...
   [TELEGRAM WORKER] Procesando cola cada 30 segundos...
   ```
4. Cuando veas esos logs, el worker está listo

### Paso 5: Entender el flujo de mensajes

```
HF Spaces (bot.py genera mensaje)
    ↓
BD PostgreSQL (Neon) - guarda en tabla telegram_notifications
    ↓
Render Worker (lee BD cada 30s)
    ↓
Si hay mensajes pendientes:
    • Intenta enviar a Telegram API
    • Si falla: reintenta con exponential backoff
    • Marca como enviado o error en BD
    ↓
Telegram Chat (usuario recibe alerta)
```

### Paso 6: Monitorear el worker

**En Render:**

- Visita tu servicio en el dashboard
- Pestaña **Logs** → filtra por `[TELEGRAM WORKER]`
- Status debe estar en verde (**Running**)

**En BD:**
Query para verificar la cola:

```sql
SELECT id, status, retries, created_at
FROM telegram_notifications
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🎨 Frontend en Vercel

### Requisitos Previos

- Cuenta en Vercel (https://vercel.com)
- Repositorio GitHub con el código frontend en carpeta `frontend/`

### Paso 1: Conectar repositorio a Vercel

1. Ve a https://vercel.com/new
2. Click **Import Git Repository**
3. Selecciona tu repositorio GitHub
4. Vercel detectará automáticamente que es un proyecto Node.js

### Paso 2: Configurar el proyecto

En la pantalla de importación:

```
Project Name: opticv-frontend
Root Directory: frontend/
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

Vercel debería detectar esto automáticamente si tienes:

- `frontend/package.json`
- `frontend/vite.config.js`

### Paso 3: Configurar variables de entorno

En **Project Settings → Environment Variables**, añade:

```
VITE_API_URL = https://opticv-backend.hf.space
```

**Aplicar a:**

- Production
- Preview
- Development

**Importante:**

- El prefijo `VITE_` es **obligatorio** para que Vite las exponga al navegador
- `VITE_API_URL` debe ser HTTPS

### Paso 4: Deploy automático

1. Click **Import** para crear el proyecto
2. Vercel hace build automáticamente
3. Tras el primer deploy, cada `git push` a `main` triggeará un nuevo deploy

**URLs generadas:**

- Preview: `https://opticv-frontend-RANDOM.vercel.app` (para cada PR)
- Production: `https://opticv-frontend.vercel.app` (rama main)

### Paso 5: Verificar el frontend

```bash
# En el navegador:
https://opticv-frontend.vercel.app

# En DevTools Console, verifica:
console.log(import.meta.env.VITE_API_URL)
# Debe mostrar: https://opticv-backend.hf.space
```

---

## 🔗 Configuración de Conexión

### Paso 1: CORS en Backend

En `main.py`, verifica que el middleware CORS incluye todos los dominios:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",                    # Dev local
        "http://localhost:3000",                    # Dev alt
        "https://opticv-frontend.vercel.app",       # Vercel production
        "https://opticv-backend.hf.space",           # HF Spaces (self)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Paso 2: Verificar API Client

En `frontend/src/services/apiClient.js`:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:7860";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Interceptor para agregar token Bearer
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Paso 3: Probar conectividad

En DevTools Console del navegador:

```javascript
fetch("https://opticv-backend.hf.space/health")
  .then((r) => r.json())
  .then(console.log)
  .catch((e) => console.error("Error:", e));

// Debe imprimir: {status: "ok"}
```

---

## 🗄️ Base de Datos Persistente

### Opción Recomendada: Neon

1. Ve a https://console.neon.tech
2. Crea un proyecto PostgreSQL
3. Copia la **Connection String**
4. Cámbialo a asyncpg:

```
# Original (psycopg2):
postgresql://user:pass@host/dbname

# Cambiar a asyncpg:
postgresql+asyncpg://user:pass@host/dbname
```

5. Usa este `DATABASE_URL` en:
   - `.env` local
   - HF Spaces Secrets
   - Render Worker Environment Variables

### Opción B: Railway

1. Ve a https://railway.app
2. **New Project** → **PostgreSQL**
3. En la BD recién creada:
   - Click **Variables**
   - Busca `DATABASE_URL`
   - Cópiala y cámbiala a asyncpg

### Verificar conexión local

```bash
python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql+asyncpg://...')
    result = await conn.fetchval('SELECT 1')
    print(f'Conexión OK: {result}')
    await conn.close()
asyncio.run(test())
"
```

---

## ⏱️ Tiempos Esperados en Producción

- **Análisis de oferta:** 12-25 segundos
  - Scraping: 2-8s
  - DeepSeek LLM: 10-15s
- **Generación de CV adaptado:** 30-60 segundos
  - Adaptación DeepSeek: 10-20s
  - Compilación LaTeX: 20-40s
- **Notificaciones Telegram:** <1 segundo (via Render Worker)

---

## 📝 Checklist Pre-Producción

### GitHub & Repositorio

- [ ] `.github/workflows/deploy-to-hf.yml` existe y está actualizado
- [ ] `HF_TOKEN` y `HF_USERNAME` configurados en GitHub Secrets
- [ ] Rama `main` está protegida (require review antes de merge)
- [ ] No hay secretos commiteados (`grep -r "sk-" .`)

### Backend (HF Spaces)

- [ ] `Dockerfile` funciona localmente: `docker build -t test .`
- [ ] `requirements.txt` actualizado con todas las dependencias
- [ ] `entrypoint.sh` existe y es ejecutable
- [ ] HF Space `opticv-backend` creado y set a Private
- [ ] Todos los secrets configurados en HF Spaces Settings
- [ ] `main.py` tiene ambos endpoints: `GET /` y `GET /health`
- [ ] `data/cv_usuario.pdf` existe en el repositorio
- [ ] GitHub Actions workflow ejecutó exitosamente (rama main)
- [ ] Backend responde en `https://opticv-backend.hf.space/health`

### Telegram Worker (Render)

- [ ] `Dockerfile.worker` existe y funciona localmente
- [ ] `entrypoint.worker.sh` existe
- [ ] `telegram_worker.py` existe
- [ ] Servicio creado en Render: `opticv-telegram-worker`
- [ ] Todos los secrets configurados en Render Environment Variables
- [ ] Logs muestran `[TELEGRAM WORKER]` messages
- [ ] Healthcheck responde en `http://localhost:8000/health`

### Frontend (Vercel)

- [ ] `frontend/package.json` tiene scripts `build` y `dev`
- [ ] `frontend/vite.config.js` existe y está configurado
- [ ] `frontend/.env.production` existe
- [ ] Variables de entorno en Vercel Project Settings
- [ ] `npm run build` funciona localmente sin errores
- [ ] Frontend carga en `https://opticv-frontend.vercel.app`
- [ ] `VITE_API_URL` apunta correctamente a backend HF

### Integración

- [ ] Frontend conecta a backend (no CORS errors)
- [ ] Login funciona con Google OAuth
- [ ] CV upload y análisis funcionan
- [ ] Telegram bot recibe alertas
- [ ] Rate limiting activo
- [ ] HTTPS en todas las URLs

---

## 🐛 Troubleshooting

### GitHub Actions workflow no se ejecuta

**Problema:** No ves logs en GitHub → Actions

**Soluciones:**

```bash
# 1. Verifica que el workflow file es válido YAML
yamllint .github/workflows/deploy-to-hf.yml

# 2. Verifica que los secrets existen
# GitHub → Settings → Secrets → Actions

# 3. Verifica permisos en el workflow:
#    El token debe tener write access a HF Spaces
```

### Backend no inicia en HF Spaces

**Error en logs:** `ModuleNotFoundError: No module named 'src'`

**Solución:**

```bash
# Verifica estructura:
ls -la
# Debe mostrar: main.py, requirements.txt, Dockerfile, src/, etc.

# Verifica Dockerfile copia correctamente:
COPY src/ src/
COPY main.py .
```

**Error:** `PORT already in use`

```bash
# En entrypoint.sh, verifica:
uvicorn main:app --host 0.0.0.0 --port $PORT
# Donde $PORT viene de variables de entorno (default 7860)
```

### CORS errors en frontend

**Error:** `Access to XMLHttpRequest at 'https://opticv-backend.hf.space/...' from origin 'https://opticv-frontend.vercel.app' has been blocked`

**Soluciones:**

1. Verifica CORS en `main.py`:

```python
allow_origins=[
    "https://opticv-frontend.vercel.app",  # ← Verifica que está aquí
    "https://opticv-backend.hf.space",
]
```

2. Verifica que es HTTPS, no HTTP:

```javascript
// ❌ Mal
const API_URL = "http://opticv-backend.hf.space";

// ✅ Correcto
const API_URL = "https://opticv-backend.hf.space";
```

3. Deploy a HF nuevamente (push a GitHub):

```bash
git add .
git commit -m "Fix CORS configuration"
git push origin main
# Espera a que GitHub Actions complete el deploy
```

### Telegram messages no llegan

**Problema:** Worker está running pero no se envían mensajes

**Checklist:**

1. Verifica logs en Render:

```
[TELEGRAM WORKER] Iniciando worker...
[TELEGRAM WORKER] Procesando cola cada 30 segundos...
```

2. Verifica que la cola tiene mensajes (en BD):

```sql
SELECT COUNT(*) FROM telegram_notifications WHERE status = 'pending';
```

3. Verifica credenciales:

```sql
-- En HF Spaces:
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

-- Deben coincidir con Render Environment Variables
```

4. Verifica que el worker está actualmente leyendo (logs cada 30s):

```
# Espera 30 segundos, deben ver logs como:
[TELEGRAM WORKER] Processing 5 messages...
[TELEGRAM WORKER] Message sent: id=123
```

5. Si sigue sin funcionar, revisa si la API de Telegram está bloqueada:

```bash
# En local:
curl -X POST https://api.telegram.org/bot${TOKEN}/sendMessage \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"'"${CHAT_ID}"'","text":"Test"}'
```

### Frontend no carga

**Error 404 o página en blanco**

1. Verifica que el build succeeded en Vercel Dashboard
2. Abre DevTools → Console y busca errores
3. Verifica `VITE_API_URL`:

```javascript
console.log(import.meta.env.VITE_API_URL);
```

### Database connection error

**Error:** `asyncpg.exceptions.PostgresError` o `OperationalError`

**Soluciones:**

1. Verifica que `DATABASE_URL` es correcta (asyncpg):

```
✅ postgresql+asyncpg://user:pass@host/db
❌ postgresql://user:pass@host/db (sin asyncpg)
```

2. Verifica que la BD existe y es accesible desde la red:

```bash
psql "$(echo $DATABASE_URL | sed 's/asyncpg//' | sed 's/+//')" -c "SELECT 1"
```

3. Si usa Neon, verifica connection limits no estén alcanzados:

```sql
SELECT datname, count(*) as connections
FROM pg_stat_activity
GROUP BY datname;
```

---

## 📊 Monitoreo y Mantenimiento

### Monitoreo Diario

**HF Spaces:**

- Ve a https://huggingface.co/spaces/tu-usuario/opticv-backend
- Pestaña **Logs** → Busca errores
- Status debe estar en verde (**RUNNING**)
- Endpoint debe responder en `/health`

**Render (Worker):**

- Dashboard Render → Tu servicio
- Logs → Filtra `[TELEGRAM WORKER]`
- Status debe estar en verde (**Running**)
- Última actualización no debe ser > 1 hora

**Vercel (Frontend):**

- https://vercel.com/dashboard → Tu proyecto
- Pestaña **Deployments** → Último debe estar en verde
- Analytics → Monitorea latencia y errores

### Alertas Recomendadas

Configura notificaciones para:

**GitHub Actions:**

- Workflow failures
- View: https://github.com/tu-repo/actions

**HF Spaces:**

- Visita los logs regularmente (no tiene alertas automáticas)

**Render:**

- Settings → Notifications
- Enable: Failed deploys, instance crashes

**Vercel:**

- Project Settings → Notifications
- Enable: Failed deployments

### Actualizar Dependencias

**Mensual:**

```bash
# Backend
pip list --outdated
pip install --upgrade <package>
pip freeze > requirements.txt
git add requirements.txt && git commit -m "Upgrade dependencies"
git push  # GitHub Actions hará deploy automático

# Frontend
npm outdated
npm update
git add package-lock.json && git commit -m "Upgrade dependencies"
git push  # Vercel hará deploy automático
```

**Trimestral:**

```bash
# Actualiza versiones major
pip install --upgrade --pre

# Revisa breaking changes
# Python: https://docs.python.org/3/whatsnew/
# Node.js: https://nodejs.org/en/blog/release/
```

---

## 🚨 Rollback (Emergencia)

Si algo falla en producción:

### Backend (HF Spaces)

```bash
# 1. Ve al último commit bueno
git log --oneline | head -5

# 2. Revert el commit malo
git revert <commit-hash>
git push origin main

# GitHub Actions detectará y hará deploy automático (2-3 min)
```

### Frontend (Vercel)

1. Dashboard Vercel → Deployments
2. Busca el deployment anterior que funcionaba
3. Click en los 3 puntos → "Promote to Production"

### Worker (Render)

Si el worker está en crash loop:

1. Dashboard Render → Tu servicio
2. Click **Suspend** (pausa el servicio)
3. Verifica logs para encontrar el error
4. Fix el código, push a GitHub
5. Render re-deploya automáticamente
6. Si sigue fallando, click **Resume** y investiga más

---

## 🔐 Checklist de Seguridad

- [ ] No hay secretos en GitHub (`.env` en `.gitignore`)
- [ ] HTTPS en todas las URLs (no http://)
- [ ] CORS solo permite dominios conocidos (no `*`)
- [ ] JWT tokens tienen expiración (15 min recomendado)
- [ ] Passwords hasheados con bcrypt, no plaintext
- [ ] Rate limiting activo en todos los endpoints
- [ ] No hay logs con tokens o passwords
- [ ] Cloudinary tiene restricciones de acceso (upload only for auth users)
- [ ] Base de datos tiene backups automáticos (verificar con Neon/Railway)
- [ ] API keys no expuestos en frontend (solo en backend via env vars)
- [ ] Google OAuth redirect URIs configurados correctamente

---

## 📞 Soporte

Si tienes problemas:

1. **Revisa logs** (por orden):
   - GitHub Actions: https://github.com/tu-repo/actions
   - HF Spaces: https://huggingface.co/spaces/tu-usuario/opticv-backend → Logs
   - Render: Dashboard → Tu servicio → Logs
   - Vercel: Dashboard → Tu proyecto → Logs
   - Browser: DevTools → Console

2. **Comprueba configuración:**
   - Todas las variables de entorno (copied exactamente)
   - URLs (https://, dominios correctos)
   - CORS (frontend URL en allow_origins)
   - Database (conexión correcta desde todas las apps)

3. **Contacta:**
   - GitHub Issues para bugs
   - Documentación oficial: HF, Render, Vercel
   - Comunidades: Discord de HF, Render, Vercel

---

**⚡ ¡Sistema completamente desplegado! 🎉**
