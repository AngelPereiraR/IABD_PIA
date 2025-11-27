# 🤖 Recopilador Inteligente de Ofertas de Trabajo

Sistema automatizado de análisis y notificación de ofertas laborales que combina **IA Generativa (Gemini 2.5 Flash)**, **Web Scraping inteligente** y **Notificaciones en tiempo real** vía Telegram. Monitorea correos de plataformas como LinkedIn e InfoJobs, evalúa el ajuste con tu CV usando criterios de selección profesional (ATS + RRHH), y te alerta solo de las oportunidades realmente relevantes.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Local](#-instalación-local)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Despliegue en Producción](#-despliegue-en-producción)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Flujo de Trabajo](#-flujo-de-trabajo)
- [Troubleshooting](#-troubleshooting)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)

---

## ✨ Características

### 🎯 **Análisis Inteligente con IA**
- **Doble Fase de Filtrado**: Simula tanto el escaneo ATS (Applicant Tracking System) como la evaluación de un reclutador humano
- **Puntuación de Ajuste**: Sistema de scoring 0-100 con clasificación automática (Ideal/Fuerte/Apto/Dudoso)
- **Anti-Alucinación**: Sistema de "grounding" que evita suposiciones no presentes en el texto original
- **Extracción Estructurada**: Detecta automáticamente título, empresa, salario, beneficios y fecha de publicación

### 🔍 **Web Scraping Robusto**
- **Estrategia en Cascada**: Jina AI → FireCrawl → Scraping Directo
- **Soporte Multi-Plataforma**: LinkedIn, InfoJobs y otras plataformas genéricas
- **Limpieza Inteligente**: Selectores CSS personalizados para eliminar navegación, anuncios y elementos no deseados
- **Manejo de Errores**: Reintentos automáticos con exponential backoff

### 📧 **Integración con Gmail**
- **Búsqueda Automática**: Detecta alertas de empleo no leídas de LinkedIn e InfoJobs
- **Limpieza Automática**: Elimina correos antiguos (>14 días) para mantener la bandeja organizada
- **Resolución de Links**: Maneja automáticamente URLs de tracking y redirecciones

### 📱 **Notificaciones Telegram**
- **Alertas Visuales**: Iconos y barras de progreso según nivel de match
- **Formato Rico**: Mensajes estructurados con todos los detalles relevantes
- **Respuesta Inmediata**: Notificaciones en tiempo real cuando se encuentra una oportunidad

### 🐳 **Listo para Producción**
- **Dockerizado**: Imagen optimizada con Python 3.11-slim
- **Health Checks**: Endpoint `/health` para monitoreo
- **Gestión de Secretos**: Inyección segura de credenciales vía variables de entorno
- **Servidor Web**: Flask + Gunicorn para cumplir requisitos de plataformas como Render

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         MAIN PROCESS                            │
│  ┌──────────────────┐          ┌─────────────────────────────┐  │
│  │  Flask Server    │          │    Bot Logic Thread         │  │
│  │  (Render Keep-   │          │    (Infinite Loop)          │  │
│  │   Alive)         │          │                             │  │
│  │                  │          │  ┌─────────────────────┐    │  │
│  │  GET /           │          │  │ 1. Gmail Collector  │    │  │
│  │  GET /health     │          │  │    - Fetch offers   │    │  │
│  └──────────────────┘          │  │    - Clean old mail │    │  │
│                                │  └──────────┬──────────┘    │  │
│                                │             │               │  │
│                                │  ┌──────────▼──────────┐    │  │
│                                │  │ 2. Scraper          │    │  │
│                                │  │    - Jina AI        │    │  │
│                                │  │    - FireCrawl      │    │  │
│                                │  │    - Direct HTTP    │    │  │
│                                │  └──────────┬──────────┘    │  │
│                                │             │               │  │
│                                │  ┌──────────▼──────────┐    │  │
│                                │  │ 3. Brain (Gemini)   │    │  │
│                                │  │    - ATS Filter     │    │  │
│                                │  │    - RRHH Eval      │    │  │
│                                │  └──────────┬──────────┘    │  │
│                                │             │               │  │
│                                │  ┌──────────▼──────────┐    │  │
│                                │  │ 4. Telegram Bot     │    │  │
│                                │  │    - Send Alert     │    │  │
│                                │  └─────────────────────┘    │  │
│                                └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

External APIs:
- Google Gmail API (OAuth 2.0)
- Google Gemini 2.5 Flash
- Jina AI Reader
- FireCrawl API
```

---

## 📦 Requisitos Previos

### Software
- **Python 3.11+** (recomendado 3.11 para compatibilidad con LangChain)
- **pip** (gestor de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)
- **Docker** (opcional, para despliegue containerizado)

### Cuentas y APIs Necesarias

#### 1. **Google Cloud Platform** (para Gmail API y Gemini)
- Proyecto en Google Cloud Console
- OAuth 2.0 credentials habilitadas
- Gmail API activada
- Generative Language API (Gemini) activada

#### 2. **Telegram Bot**
- Bot creado con @BotFather
- Bot Token y Chat ID

#### 3. **APIs de Scraping** (Opcional pero recomendado)
- FireCrawl API Key (https://firecrawl.dev)
- Jina AI (gratuito, sin API key requerida)

---

## 🚀 Instalación Local

### 1. Clonar o Descargar el Proyecto

```powershell
git clone https://github.com/AngelPereiraR/IABD_PIA.git
cd "IABD_PIA/Tema 02/Recopilador Ofertas Trabajo Validas"
```

### 2. Crear Entorno Virtual

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual (PowerShell)
.\.venv\Scripts\Activate.ps1

# Si da error de permisos, ejecuta:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependencias

```powershell
pip install -r requirements.txt
```

### 4. Preparar CV

Coloca tu CV en formato PDF en:
```
data/cv_usuario.pdf
```

---

## ⚙️ Configuración

### 1. Configurar Google Cloud (OAuth + Gemini)

#### A. Crear Proyecto en Google Cloud Console
1. Ve a https://console.cloud.google.com
2. Crea un nuevo proyecto o selecciona uno existente
3. Navega a **APIs & Services > Enable APIs and Services**
4. Habilita las siguientes APIs:
   - **Gmail API**
   - **Generative Language API** (Gemini)

#### B. Crear Credenciales OAuth 2.0
1. Ve a **APIs & Services > Credentials**
2. Haz clic en **+ CREATE CREDENTIALS > OAuth client ID**
3. Tipo de aplicación: **Desktop app**
4. Descarga el archivo JSON y guárdalo como `credentials.json` en la raíz del proyecto

#### C. Configurar Pantalla de Consentimiento
1. Ve a **OAuth consent screen**
2. Tipo de usuario: **Externo** (para cuentas personales)
3. Completa la información básica
4. En **Scopes**, añade: `https://mail.google.com/` (Gmail completo)
5. En **Test users**, añade tu correo personal

#### D. Generar Token de Gmail

```powershell
# Con el entorno virtual activado
python src/setup_auth.py
```

Este script:
- Abrirá tu navegador
- Te pedirá que inicies sesión con Google
- Solicitará permisos de acceso a Gmail
- Generará el archivo `token.json`

⚠️ **Importante**: Si ves "Aplicación no verificada", haz clic en **Avanzado** → **Ir a [nombre-app] (inseguro)**.

#### E. Obtener API Key de Gemini
1. Ve a https://aistudio.google.com/app/apikey
2. Crea una API Key
3. Cópiala para usar en el archivo `.env`

### 2. Configurar Telegram Bot

#### A. Crear Bot con BotFather
```
1. Abre Telegram y busca @BotFather
2. Envía: /newbot
3. Sigue las instrucciones (nombre y username)
4. Copia el Token que te proporciona
```

#### B. Obtener Chat ID
```
1. Envía un mensaje a tu bot (cualquier mensaje)
2. Ve a: https://api.telegram.org/bot<TU_TOKEN>/getUpdates
3. Busca el campo "chat":{"id":123456789}
4. Copia ese número (tu Chat ID)
```

### 3. Configurar APIs de Scraping (Opcional)

#### FireCrawl
1. Regístrate en https://firecrawl.dev
2. Obtén tu API Key desde el dashboard
3. Añádela al archivo `.env`

### 4. Crear Archivo `.env`

Crea un archivo llamado `.env` en la raíz del proyecto:

```env
# === GEMINI (Google AI) ===
GEMINI_API_KEY=tu_api_key_de_gemini

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# === FIRECRAWL (Opcional pero recomendado) ===
FIRECRAWL_API_KEY=fc-tu_api_key_aqui

# === CONFIGURACION DEL SISTEMA ===
# Interval en segundos (600 = 10 minutos)
POLLING_INTERVAL=600
```

### 5. Verificar Archivos de Credenciales

Tu estructura debe verse así:
```
├── credentials.json      ← OAuth credentials de Google
├── token.json            ← Token generado por setup_auth.py
├── .env                  ← Variables de entorno
├── data/
│   └── cv_usuario.pdf    ← Tu CV
└── ...
```

---

## 💻 Uso

### Ejecución Local (Desarrollo)

```powershell
# Con el entorno virtual activado
python main.py
```

**Salida esperada:**
```
 [INIT] Iniciando hilo del bot...
 [OK] Contexto y Cerebro listos.
 [SISTEMA] OPERATIVO. Iniciando bucle infinito...
 [LOOP #1] Iniciando ciclo...
    [AUTH] Refrescando cliente de Gmail...
    [BUSQUEDA] Buscando alertas recientes (<14 días)...
    - Sin alertas. Proximo escaneo en 10 min.
```

### Servidor Web (Flask)

El sistema incluye un servidor web en `http://localhost:10000`:
- **GET /** → Página de status simple
- **GET /health** → Endpoint de health check (retorna "OK")

### Pruebas Unitarias de Componentes

Cada módulo puede ejecutarse independientemente para pruebas:

#### Probar Scraper
```powershell
python src/scraper.py
```

#### Probar Gmail Collector
```powershell
python src/mail_agent.py
```

#### Probar Telegram Notifier
```powershell
python src/bot.py
```

#### Probar Carga de CV
```powershell
python src/loader.py
```

---

## 🌐 Despliegue en Producción

### Opción 1: Render (Recomendado - Free Tier)

#### 1. Preparar el Repositorio
```powershell
# Si aún no está en Git
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/tu-usuario/tu-repo.git
git push -u origin main
```

#### 2. Crear Web Service en Render

1. Ve a https://render.com y regístrate
2. **New** → **Web Service**
3. Conecta tu repositorio de GitHub
4. Configuración:
   - **Name**: `job-scraper-bot` (o el que prefieras)
   - **Region**: Elige el más cercano
   - **Branch**: `main`
   - **Root Directory**: `Tema 02/Recopilador Ofertas Trabajo Validas`
   - **Runtime**: `Docker`
   - **Instance Type**: `Free`

#### 3. Configurar Variables de Entorno

En la sección **Environment**, añade estas variables:

```
GEMINI_API_KEY=tu_api_key_de_gemini
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
FIRECRAWL_API_KEY=fc-tu_api_key
```

#### 4. Configurar Secretos JSON (Crítico)

Para archivos como `credentials.json`, `token.json` y `.env`, usa el sistema de secretos:

```
GOOGLE_CREDENTIALS_JSON={"installed":{"client_id":"...","project_id":"...",...}}
GOOGLE_TOKEN_JSON={"token":"...","refresh_token":"...","token_uri":"...",...}
MY_ENV_FILE=GEMINI_API_KEY=xxx
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
FIRECRAWL_API_KEY=xxx
```

**Cómo obtener el contenido de estos archivos:**

##### En PowerShell:
```powershell
# Credentials.json (todo en una línea)
Get-Content credentials.json -Raw | ConvertTo-Json -Compress

# Token.json (todo en una línea)
Get-Content token.json -Raw | ConvertTo-Json -Compress

# .env (todo en una línea, con \n para saltos)
(Get-Content .env -Raw).Replace("`r`n", "\n")
```

##### En Linux/Mac:
```bash
# Credentials.json
cat credentials.json | jq -c

# Token.json
cat token.json | jq -c

# .env
cat .env | sed ':a;N;$!ba;s/\n/\\n/g'
```

#### 5. Desplegar

Haz clic en **Create Web Service**. Render:
1. Clonará tu repositorio
2. Construirá la imagen Docker
3. Inyectará las variables de entorno
4. Ejecutará `entrypoint.sh` que:
   - Creará `credentials.json`, `token.json` y `.env` desde las variables
   - Arrancará Gunicorn con Flask
   - Iniciará el hilo del bot en segundo plano

#### 6. Verificar

- Revisa los logs en tiempo real desde el dashboard de Render
- Accede a `https://tu-app.onrender.com/health` para verificar que está vivo

⚠️ **Limitaciones del Free Tier de Render**:
- El servicio se "duerme" tras 15 minutos de inactividad
- Solución: Configura un servicio externo (UptimeRobot, cron-job.org) para hacer ping al endpoint `/health` cada 10 minutos

---

### Opción 2: Railway

#### 1. Conectar Repositorio
1. Ve a https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. Selecciona tu repositorio

#### 2. Configurar
- Railway detectará automáticamente el Dockerfile
- Añade las mismas variables de entorno que en Render (paso 3 y 4 de arriba)

#### 3. Deploy
- Railway desplegará automáticamente
- Obtendrás una URL pública tipo `https://xxx.up.railway.app`

---

### Opción 3: Docker Local (Testing de Producción)

```powershell
# 1. Construir imagen
docker build -t job-scraper:latest .

# 2. Ejecutar con variables de entorno
docker run -d `
  -p 10000:10000 `
  -e PORT=10000 `
  -e GEMINI_API_KEY="tu_key" `
  -e TELEGRAM_BOT_TOKEN="tu_token" `
  -e TELEGRAM_CHAT_ID="tu_chat_id" `
  -e FIRECRAWL_API_KEY="tu_key" `
  -e GOOGLE_CREDENTIALS_JSON='{"installed":{...}}' `
  -e GOOGLE_TOKEN_JSON='{"token":"..."}' `
  -e MY_ENV_FILE='GEMINI_API_KEY=xxx
TELEGRAM_BOT_TOKEN=xxx' `
  --name job-scraper `
  job-scraper:latest

# 3. Ver logs
docker logs -f job-scraper

# 4. Detener
docker stop job-scraper
docker rm job-scraper
```

---

## 📁 Estructura del Proyecto

```
Recopilador Ofertas Trabajo Validas/
│
├── main.py                 # Punto de entrada (Flask + Bot Thread)
├── requirements.txt        # Dependencias de Python
├── Dockerfile              # Imagen Docker optimizada
├── entrypoint.sh           # Script de inicialización para producción
├── .env                    # Variables de entorno (no commitear)
├── credentials.json        # OAuth Google (no commitear)
├── token.json              # Token Gmail (no commitear)
├── .dockerignore           # Excluye archivos sensibles del build
├── .gitignore              # Excluye archivos sensibles del repo
├── workbench.md            # Documentación de desarrollo
│
├── data/
│   └── cv_usuario.pdf      # Tu CV (no commitear si es privado)
│
└── src/
    ├── bot.py              # Telegram Notifier (envío de alertas)
    ├── brain.py            # LLM Brain (análisis con Gemini)
    ├── loader.py           # CV Loader (extracción de PDF)
    ├── mail_agent.py       # Gmail Collector (búsqueda de ofertas)
    ├── scraper.py          # Web Scraper (extracción de contenido)
    └── setup_auth.py       # Generador de token OAuth
```

### Descripción de Módulos

| Archivo | Responsabilidad |
|---------|----------------|
| `main.py` | Orquestador principal. Lanza Flask y el bucle del bot en paralelo |
| `src/bot.py` | Gestiona notificaciones Telegram con formato enriquecido |
| `src/brain.py` | Cerebro del sistema. Usa Gemini para analizar ofertas vs CV |
| `src/loader.py` | Extrae texto del CV PDF usando PyPDFLoader |
| `src/mail_agent.py` | Busca alertas en Gmail y limpia correos antiguos |
| `src/scraper.py` | Estrategia en cascada para extraer contenido de ofertas |
| `src/setup_auth.py` | Herramienta CLI para generar token.json localmente |

---

## 🔄 Flujo de Trabajo

```
                    ┌─────────────────────────────────────┐
                    │       INICIO DEL SISTEMA            │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │      Cargar CV (PDF → Texto)        │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │      Inicializar Brain (Gemini)     │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │      Inicializar Bot (Telegram)     │
                    └──────────────┬──────────────────────┘
                                   │
        ┌──────────────────────────▼──────────────────────────┐
        │             BUCLE INFINITO (cada 10 min)            │
        │                                                     │
        │  ┌────────────────────────────────────────────┐     │
        │  │      Crear nuevo Gmail Collector           │     │
        │  │     (Refresca credenciales OAuth)          │     │
        │  └────────────────┬───────────────────────────┘     │
        │                   │                                 │
        │  ┌────────────────▼───────────────────────────┐     │
        │  │      Limpiar correos antiguos (>14 días)   │     │
        │  └────────────────┬───────────────────────────┘     │
        │                   │                                 │
        │  ┌────────────────▼───────────────────────────┐     │
        │  │     Buscar ofertas UNREAD                  │     │
        │  │     (LinkedIn + InfoJobs)                  │     │
        │  └────────────────┬───────────────────────────┘     │
        │                   │                                 │
        │            ┌──────▼───────┐                         │
        │            │ ¿Hay ofertas?│                         │
        │            └──┬────────┬──┘                         │
        │               │ NO     │ SÍ                         │
        │       ┌───────▼─┐    ┌─▼─────────────┐              │
        │       │ Esperar │    │ Para cada URL │              │
        │       │ 10 min  │    └─┬─────────────┘              │
        │       └────┬────┘      │                            │
        │            │         ┌──▼──────────────────────┐    │
        │            │         │  SCRAPER (Cascada)      │    │
        │            │         ├─────────────────────────┤    │
        │            │         │  Intento: Jina AI       │    │
        │            │         │    ├─  → Continuar      │    │
        │            │         │    └─  → Siguiente      │    │
        │            │         │                         │    │
        │            │         │  Intento: FireCrawl     │    │
        │            │         │    ├─  → Continuar      │    │
        │            │         │    └─  → Siguiente      │    │
        │            │         │                         │    │
        │            │         │  Intento: Directo       │    │
        │            │         │    ├─  → Continuar      │    │
        │            │         │    └─  → Descartar      │    │
        │            │         └──┬──────────────────────┘    │
        │            │            │                           │
        │            │    ┌───────▼───────────────────────┐   │
        │            │    │  BRAIN: Análisis con IA       │   │
        │            │    ├───────────────────────────────┤   │
        │            │    │ FASE 1: Filtro ATS            │   │
        │            │    │  ↓                            │   │
        │            │    │ FASE 2: Evaluación RRHH       │   │
        │            │    │  ↓                            │   │
        │            │    │ Genera Score (0-100)          │   │
        │            │    └───────┬───────────────────────┘   │
        │            │            │                           │
        │            │     ┌──────▼───────┐                   │
        │            │     │ Score >= 70? │                   │
        │            │     └──┬────────┬──┘                   │
        │            │        │ NO     │ SÍ                   │
        │            │   ┌────▼──┐  ┌──▼──────────────────┐   │
        │            │   │Ocultar│  │  TELEGRAM ALERT     │   │
        │            │   └───┬───┘  │  Título + Empresa   │   │
        │            │       │      │  Salario            │   │
        │            │       │      │  Score + Barra      │   │
        │            │       │      │  Justificación      │   │
        │            │       │      │  Link directo       │   │
        │            │       │      └──┬──────────────────┘   │
        │            │       │         │                      │
        │            │     ┌─▼─────────▼───┐                  │
        │            │     │ ¿Más ofertas? │                  │
        │            │     └─┬──────────┬──┘                  │
        │            │       │ SÍ    NO │                     │
        │            └───────┴──────────┘                     │
        │                    │                                │
        └────────────────────┘                                │
                             │                                │
                    ┌────────▼────────┐                       │
                    │   Sleep 10min   │                       │
                    └────────┬────────┘                       │
                             │                                │
                             └──────────────► (Volver al bucle)
```

### Desglose del Proceso

1. **Inicialización** (Una sola vez al arrancar)
   - Carga del CV en memoria
   - Conexión con Gemini
   - Validación de credenciales Telegram

2. **Bucle Principal** (Cada 10 minutos)
   - Refresco de conexión Gmail (evita timeouts OAuth)
   - Limpieza automática de correos viejos
   - Búsqueda de alertas nuevas no leídas

3. **Procesamiento por Oferta**
   - **Scraping en Cascada**: Intenta 3 métodos hasta obtener contenido válido
   - **Análisis Dual**: Filtro ATS + Evaluación Humana
   - **Decisión**: Solo notifica si `score >= 70`

4. **Notificación**
   - Formato rico con iconos según score
   - Información estructurada (título, salario, beneficios, etc.)
   - Link directo para aplicar

---

## 🐛 Troubleshooting

### Error: "No se encuentra credentials.json"
**Solución**: Asegúrate de haber descargado las credenciales OAuth de Google Cloud Console y guardarlas como `credentials.json` en la raíz del proyecto.

### Error: "Invalid grant" al generar token
**Causas comunes**:
1. El token expiró (válido por 7 días en modo test)
2. Cambiaste los scopes en Google Cloud Console

**Solución**: 
```powershell
# Elimina el token antiguo y genera uno nuevo
del token.json
python src/setup_auth.py
```

### Error: "Application not verified" en OAuth
**Solución**: Es normal en aplicaciones en desarrollo. Haz clic en **Avanzado** → **Ir a [nombre-app] (inseguro)**.

Para eliminar la advertencia (opcional):
1. Ve a Google Cloud Console
2. OAuth consent screen → Publishing status
3. Completa el proceso de verificación (requiere revisión de Google)

### Bot no recibe correos nuevos
**Verificaciones**:
1. Los correos deben estar **NO LEÍDOS**
2. Deben ser de LinkedIn (`@linkedin.com`) o InfoJobs (`@infojobs.net`)
3. Deben contener palabras clave como "alerta de empleo"
4. No deben tener más de 14 días

**Nota importante**: El sistema reinicia el cliente Gmail en cada ciclo porque `GmailToolkit` cachea internamente la lista de correos en el momento de su inicialización. Sin este refresco, los correos que lleguen después no serán detectados hasta el siguiente reinicio del servicio.

**Test manual**:
```powershell
python src/mail_agent.py
```

### Scraper retorna contenido vacío
**Causas**:
1. La página requiere JavaScript (Jina/FireCrawl deberían manejarlo)
2. URL inválida o bloqueada

**Solución**: Revisa los logs para ver qué estrategia falló:
```
[SCRAPER] Jina AI: ✅ | FireCrawl: ❌ | Directo: ❌
```

### Gemini retorna errores 429 (Rate Limit)
**Solución**: 
- Free tier: 15 RPM (requests per minute)
- Ajusta `POLLING_INTERVAL` a un valor más alto (ej. 1200 = 20 min)

### Docker: "exec format error" en entrypoint.sh
**Causa**: Finales de línea Windows (CRLF) en lugar de Unix (LF)

**Solución**:
```powershell
# Convierte a LF usando Git
git config core.autocrlf input
git rm --cached -r .
git reset --hard
```

O edita `entrypoint.sh` en VS Code y cambia el final de línea (esquina inferior derecha: CRLF → LF)

### Render: "Health check failed"
**Verificaciones**:
1. El servicio debe responder en el puerto especificado por `$PORT`
2. El endpoint `/health` debe retornar status 200

**Test local**:
```powershell
curl http://localhost:10000/health
# Debe retornar: OK
```

---

## 🛠️ Tecnologías Utilizadas

### Backend & Framework
- **Python 3.11** - Lenguaje principal
- **Flask** - Servidor web ligero
- **Gunicorn** - WSGI HTTP Server para producción

### IA & LangChain
- **LangChain** - Framework de orquestación LLM
- **Google Gemini 2.5 Flash** - Modelo de análisis de ofertas
- **LangChain Google Community** - Integración Gmail Toolkit

### Web Scraping
- **Jina AI Reader** - Scraping rápido sin API key
- **FireCrawl** - Scraping avanzado con renderizado JS
- **Requests + BeautifulSoup** - Scraping directo de fallback

### APIs & Servicios
- **Gmail API** - Acceso a correos vía OAuth 2.0
- **Telegram Bot API** - Notificaciones en tiempo real
- **PyPDF** - Extracción de texto de CV en PDF

### DevOps
- **Docker** - Containerización
- **Render/Railway** - Plataformas de despliegue
- **python-dotenv** - Gestión de variables de entorno

---

### Ideas de Mejoras
- [ ] Soporte para más plataformas (Indeed, Glassdoor, etc.)
- [ ] Dashboard web para visualizar estadísticas
- [ ] Base de datos para histórico de ofertas
- [ ] Sistema de respuestas automáticas
- [ ] Integración con Notion/Trello para tracking de aplicaciones
- [ ] Generación automática de cover letters personalizadas


---

## 👤 Autor

**Ángel Pereira**
- GitHub: [@AngelPereiraR](https://github.com/AngelPereiraR)
- Proyecto: [IABD_PIA](https://github.com/AngelPereiraR/IABD_PIA)

---

## 🙏 Agradecimientos

- **Google Cloud** por las APIs de Gmail y Gemini
- **LangChain** por el framework de orquestación
- **Jina AI** y **FireCrawl** por las herramientas de scraping
- **Telegram** por la plataforma de bots

---

## 📞 Soporte

Si encuentras algún problema o tienes preguntas:

1. Revisa la sección [Troubleshooting](#-troubleshooting)
2. Consulta el archivo `workbench.md` para detalles técnicos
3. Abre un **Issue** en el repositorio de GitHub

---

**⚡ ¡Happy Job Hunting! 🎯**
