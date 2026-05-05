# Docker Compose Setup - OptiCV (Desarrollo Local en Windows)

Setup para ejecutar **3 servicios** localmente: Backend FastAPI, Telegram Worker, y Frontend Vite.

## Requisitos

- **Docker Desktop** instalado en Windows (incluye docker-compose)
- **PowerShell** (Windows 11)
- **.env file** en la raíz del proyecto con todas las variables de entorno

## Configuración Inicial

### 1. Verificar Docker Desktop está corriendo

```powershell
docker --version
docker-compose --version
```

### 2. Preparar archivo .env

Crea `.env` en la raíz del proyecto (NO hacer push a GitHub):

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# Gmail OAuth
GOOGLE_CREDENTIALS_JSON='{"installed":{...}}'
GOOGLE_TOKEN_JSON='{"token":"..."}'

# DeepSeek LLM
DEEPSEEK_API_KEY=sk-xxxx

# Cloudinary (PDF storage)
CLOUDINARY_NAME=xxxx
CLOUDINARY_API_KEY=xxxx
CLOUDINARY_API_SECRET=xxxx

# Jina AI (Scraping)
JINA_API_KEY=jina_xxxx

# FireCrawl (Scraping fallback)
FIRECRAWL_API_KEY=fcrawl_xxxx

# Telegram (Bot + Worker)
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=987654321

# Server
PORT=7860
USER_ID=1
```

**⚠️ Importante:**
- `DATABASE_URL` debe usar `postgresql+asyncpg://` (asyncpg es obligatorio)
- Estos valores se cargan automáticamente en docker-compose.yml

---

## 🐳 Servicios en docker-compose.yml

Tu `docker-compose.yml` define **3 servicios**:

| Servicio | Container | Puerto | Dockerfile | Función |
|----------|-----------|--------|-----------|---------|
| **backend** | job-offers-backend | 7860 | Dockerfile | FastAPI + Bot thread |
| **telegram-worker** | telegram-worker | (no expuesto) | Dockerfile.worker | Procesa cola Telegram |
| **frontend** | job-offers-frontend | 5173 | Dockerfile.frontend | Vite React dev server |

**Dependencias:**
- `telegram-worker` espera que `backend` esté healthy (healthcheck en `/health`)

---

## 🚀 Comandos en PowerShell

### Iniciar todos los servicios

```powershell
# Foreground (ver logs en vivo)
docker-compose up

# Background
docker-compose up -d
```

Cuando ves esto, todos están listos:
```
job-offers-backend  | Uvicorn running on 0.0.0.0:7860
job-offers-frontend | Local: http://localhost:5173
telegram-worker     | [TELEGRAM WORKER] Iniciando worker...
```

### Ver logs

```powershell
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend

# Solo telegram worker
docker-compose logs -f telegram-worker
```

### Detener servicios

```powershell
# Detener (mantiene volúmenes)
docker-compose down

# Detener y limpiar volúmenes
docker-compose down -v
```

### Reconstruir imágenes

```powershell
# Si hay cambios en Dockerfile/requirements.txt
docker-compose build --no-cache

# Luego iniciar
docker-compose up
```

### Reiniciar servicios individuales

```powershell
# Reiniciar backend
docker-compose restart backend

# Reiniciar telegram worker
docker-compose restart telegram-worker

# Reiniciar frontend
docker-compose restart frontend
```

### Ejecutar comando en un container

```powershell
# Entrar al backend (Python bash)
docker-compose exec backend bash

# Entrar al frontend (Node sh)
docker-compose exec frontend sh

# Entrar al worker (Python bash)
docker-compose exec telegram-worker bash

# Ejecutar comando en backend
docker-compose exec backend python -c "import sys; print(sys.version)"
```

---

## 🌐 Acceso a la Aplicación

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:5173 | Vite dev server (hot reload) |
| **Backend API** | http://localhost:7860 | FastAPI endpoints |
| **Health Check** | http://localhost:7860/health | Estado del backend |
| **Telegram Worker** | (no expuesto) | Corre en background |

### Verificar que está corriendo

```powershell
# Ver containers activos
docker ps

# Filtrar por nombre
docker ps | findstr job-offers

# Ver logs resumido
docker-compose logs

# Verificar estado individual
docker ps --filter name=job-offers-backend
```

---

## 🔍 Debugging

### Ver logs detallados

```powershell
# Logs completos de backend
docker-compose logs backend --tail 50

# Logs en tiempo real filtrando por palabra
docker-compose logs -f | findstr "ERROR"

# Logs del worker específicamente
docker-compose logs -f telegram-worker --tail 100
```

### Entrar en un container

```powershell
# Bash en backend (Python)
docker-compose exec backend bash
# Dentro: python -c "import src; print('OK')"

# Shell en frontend (Node)
docker-compose exec frontend sh
# Dentro: npm list react

# Bash en worker
docker-compose exec telegram-worker bash
# Dentro: python telegram_worker.py --test
```

### Verificar variables de entorno

```powershell
# En backend
docker-compose exec backend sh -c 'echo $DATABASE_URL'
docker-compose exec backend sh -c 'echo $TELEGRAM_BOT_TOKEN'

# En worker
docker-compose exec telegram-worker sh -c 'echo $TELEGRAM_CHAT_ID'
```

---

## 🐛 Troubleshooting

### Puerto ya está en uso

```powershell
# Ver qué ocupa puerto 5173 (frontend)
netstat -ano | findstr :5173

# Ver qué ocupa puerto 7860 (backend)
netstat -ano | findstr :7860

# Matar proceso por PID (cambiar <PID>)
taskkill /PID 12345 /F

# O simplemente cambiar puerto en docker-compose.yml
# ports:
#   - "5174:5173"  ← cambiar a 5174
```

### Contenedor no inicia

```powershell
# Ver logs específicos del servicio
docker-compose logs backend
docker-compose logs telegram-worker

# Reconstruir sin caché
docker-compose build --no-cache backend

# Iniciar con logs en vivo
docker-compose up
```

### Error: `DATABASE_URL` no conecta

```powershell
# Verificar que .env existe
ls .env

# Verificar que está en raíz
Get-Content .env | findstr DATABASE_URL

# Verificar dentro del container
docker-compose exec backend sh -c 'echo $DATABASE_URL'

# Probar conexión desde container
docker-compose exec backend python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('''$DATABASE_URL''')
    print('Connected!')
    await conn.close()
asyncio.run(test())
"
```

### Telegram Worker no procesa

```powershell
# Ver logs del worker
docker-compose logs -f telegram-worker

# Debe mostrar:
# [TELEGRAM WORKER] Iniciando worker...
# [TELEGRAM WORKER] Procesando cola cada 30 segundos...

# Si está en error, reconstruir
docker-compose build --no-cache telegram-worker
docker-compose up telegram-worker
```

### Frontend no compila

```powershell
# Ver logs completos
docker-compose logs frontend --tail 100

# Reconstruir sin caché
docker-compose build --no-cache frontend

# Entrar y revisar
docker-compose exec frontend sh
# npm ls  ← ver dependencias
# npm run build  ← probar build
```

### Limpiar todo y empezar de nuevo

```powershell
# Parar y eliminar todo
docker-compose down -v

# Limpiar sistema
docker system prune -a --volumes

# Reconstruir todo
docker-compose build --no-cache

# Iniciar fresh
docker-compose up
```

---

## 📊 Entrypoints y Secretos

### entrypoint.sh (Backend)

Se ejecuta cada vez que inicia el backend:

```bash
#!/bin/bash
# 1. Si existe GOOGLE_CREDENTIALS_JSON → crea credentials.json
# 2. Si existe GOOGLE_TOKEN_JSON → crea token.json
# 3. Inicia Uvicorn en puerto $PORT (default 7860)
exec uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Variables que inyecta:**
- `credentials.json` (lectura de Gmail)
- `token.json` (OAuth Gmail)
- `.env` (si se proporciona `MY_ENV_FILE`)

### entrypoint.worker.sh (Telegram Worker)

Se ejecuta cada vez que inicia el worker:

```bash
#!/bin/bash
# 1. Igual que entrypoint.sh (crea credenciales)
# 2. Ejecuta python telegram_worker.py
exec python telegram_worker.py
```

**No expone puerto web** (corre en background)

---

## 🔄 Volúmenes y Sincronización

Tu docker-compose.yml define:

```yaml
# Backend: datos persistentes
volumes:
  - ./data:/app/data

# Frontend: hot reload en desarrollo
volumes:
  - ./frontend/src:/app/src
  - ./frontend/public:/app/public
  - ./frontend/index.html:/app/index.html
  - ./frontend/node_modules:/app/node_modules
```

**Esto significa:**
- ✅ Cambios en `frontend/src` → se recargan automáticamente en http://localhost:5173
- ✅ `./data` sincronizado entre host y container
- ✅ Puedes editar código mientras está corriendo

---

## ⏱️ Tiempos Esperados en Desarrollo Local

- **Análisis de oferta:** 12-25 segundos (scraping 2-8s + DeepSeek 10-15s)
- **Generación de CV adaptado:** 30-60 segundos (adaptación 10-20s + LaTeX 20-40s)
- **Health checks:** <1 segundo

---

## 🏭 Despliegue en Producción

### Backend (HF Spaces)

```bash
# GitHub Actions ejecuta:
git push origin main
# ↓
.github/workflows/deploy-to-hf.yml
# ↓
Usa Dockerfile (mismo que docker-compose)
# ↓
HF Spaces build automático
# ↓
https://opticv-engine.hf.space
```

**Variables:** Se configuran en HF Space Settings → Repository Secrets

### Telegram Worker (Render)

```bash
# Servicio independiente en Render:
# 1. Conecta repo GitHub
# 2. Usa Dockerfile.worker
# 3. Configura variables en Environment Variables
# ↓
https://opticv-telegram-worker.onrender.com (health checks)
```

**Variables:** Se configuran en Render Dashboard → Environment

### Frontend (Vercel)

```bash
# Vercel CI automático:
git push origin main
# ↓
Detecta cambios en /frontend
# ↓
npm run build
# ↓
https://opticv-frontend.vercel.app
```

**Variables:** Se configuran en Vercel Project Settings → Environment Variables

---

## ✅ Checklist de Setup Local

- [ ] Docker Desktop instalado y corriendo
- [ ] `.env` creado en raíz con todas las variables
- [ ] `DATABASE_URL` con `postgresql+asyncpg://`
- [ ] `docker-compose build` completó sin errores
- [ ] `docker-compose up` muestra 3 servicios starting
- [ ] Frontend accesible en http://localhost:5173
- [ ] Backend responde en http://localhost:7860/health
- [ ] Logs muestran `[TELEGRAM WORKER]` iniciando
- [ ] Cambios en `frontend/src` se recargan automáticamente
- [ ] Puedes hacer `docker-compose exec backend bash`

---

## 📞 Tips Finales

```powershell
# Alias útiles (agregados a tu PowerShell profile)
# function dc { docker-compose $args }
# function dcl { docker-compose logs -f $args }
# function dce { docker-compose exec $args }

# Entonces:
# dc up               ← docker-compose up
# dcl backend         ← docker-compose logs -f backend
# dce backend bash    ← docker-compose exec backend bash
```

**Para agregar alias permanentes:**
```powershell
# Editar tu PowerShell profile
notepad $PROFILE

# Agregar estas líneas:
function dc { docker-compose $args }
function dcl { docker-compose logs -f $args }
function dce { docker-compose exec $args }

# Guardar y recargar:
. $PROFILE
```

---

⚡ **¡Setup local completado! Ahora puedes desarrollar con hot reload.**
