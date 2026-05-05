---
title: OptiCV - Recopilador Inteligente de Ofertas de Trabajo
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# 🤖 OptiCV - Recopilador Inteligente de Ofertas de Trabajo

Sistema integral de análisis y visualización de ofertas laborales que combina **FastAPI backend**, **React frontend**, **IA Generativa** y **notificaciones en tiempo real**. Monitorea ofertas, analiza su ajuste con tu CV usando criterios profesionales (ATS + RRHH), proporciona adaptaciones personalizadas del CV, y te mantiene informado vía Telegram.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Integración Frontend-Backend](#-integración-frontend-backend)
- [Flujo Completo del Análisis](#-flujo-completo-del-análisis-dual-fase)
- [Bandas de Puntuación](#-bandas-de-puntuación-scoring-real)
- [Stack Tecnológico](#-stack-tecnológico)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Local](#-instalación-local)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Despliegue](#-despliegue)
- [Troubleshooting](#-troubleshooting)

---

---

## ✨ Características

### 🎯 **Análisis Inteligente con IA (Dual-Fase)**

- **Fase 0 - Validación**: Detecta ofertas cerradas, textos incompletos, duplicados (Score: 0)
- **Fase 1 - ATS (Automated Tracking System)**:
  - Filtra requisitos indispensables (experiencia, skills hard, idiomas)
  - Score 0-59: Rechazo automático si faltan requisitos críticos
- **Fase 2 - Evaluación Humana (RRHH)**:
  - Valida coherencia con trayectoria, profundidad de match, ajuste cualitativo
  - Score 60-100: Graduado desde "Descarte" (60-69) hasta "Ideal" (90-100)
- **Anti-Alucinación**: Validación con "grounding" - solo información del texto original, sin inventar
- **Extracción Estructurada**: Detecta automáticamente título normalizado, empresa, salario, beneficios, skills requeridas

### 🤖 **Bot Inteligente (Thread Daemon)**

- **Monitoreo Automático**: Polling cada 10 minutos (configurable)
- **Gmail Integration**: Busca alertas no leídas (<14 días) de LinkedIn e InfoJobs
- **Auto-limpieza**: Elimina emails >14 días automáticamente (sin intervención)
- **Web Scraping Cascada**:
  - Intento 1: Jina AI (API gratuita, markdown limpio)
  - Intento 2: FireCrawl (renderizado JS para AJAX)
  - Intento 3: HTTP directo (fallback)
- **Notificaciones Telegram**: Encola mensajes en BD con reintentos automáticos (hasta 5 intentos)

### 📊 **Dashboard Web - Análisis**

- **Historial de Análisis**: Lista paginada de todas las ofertas analizadas con scores y bandas de clasificación
- **Vista Detallada**: Desglose completo (Fase ATS, Fase RRHH, justificación, requisitos faltantes)
- **Generador de CV en Tiempo Real**: Crea adaptación personalizada para cada oferta (si score ≥ 60)
- **Interfaz Intuitiva**: Bandas de color según score (rojo/naranja/verde)

### 🔄 **Adaptación Dinámica de CV**

- **Generación en LaTeX+PDF**: CV compilado a PDF real (no HTML estático, descargable)
- **Adaptación Inteligente**: DeepSeek adapta secciones según requisitos de oferta (sin inventar datos)
- **Almacenamiento en Cloudinary**: URL permanente del PDF adaptado
- **Historial de Versiones**: Consulta todas las adaptaciones anteriores, no pierdas ningún CV
- **Preview Antes de Descargar**: Previsualización del CV adaptado en navegador

### 📧 **Gmail Integration**

- **Búsqueda Automática**: Detecta alertas de empleo no leídas (<14 días) de LinkedIn e InfoJobs
- **Limpieza Automática**: Elimina correos antiguos (>14 días) sin intervención
- **OAuth 2.0**: Autenticación segura, sin guardar contraseñas en servidor
- **Resolución de Redirects**: Maneja URLs de tracking y redirecciones correctamente

### 📱 **Notificaciones Telegram (Asincrónico)**

- **Alertas Visuales**: Iconos (⛔🚀🔥) y emojis según nivel de match
- **Mensajes Encolados**: Guardados en BD con status tracking (pending/sent/failed)
- **Reintentos Automáticos**: Hasta 5 intentos con exponential backoff
- **Worker Independiente**: Procesa la cola sin bloquear análisis
- **Compatible con Render**: Puede correr en servicio separado en Render o HF Spaces

### 🔐 **Seguridad & Escalabilidad**

- **Autenticación JWT**: Tokens seguros, no sesiones de cookie
- **Rate Limiting**: 60 req/min global, 10 req/min en adaptaciones (slowapi)
- **PostgreSQL Escalable**: Migraciones Alembic, indices en campos principales
- **CORS Configurado**: Whitelist de orígenes (localhost, Vercel, HF Spaces)
- **Encriptación**: Contraseñas con bcrypt, tokens con python-jose
- **Event Loops Separados**: Thread-safe (FastAPI async + bot sync independientes)

---

---

## 🏗️ Arquitectura del Sistema {#-arquitectura-del-sistema}

**OptiCV utiliza una arquitectura DUAL-PROCESS:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                  ARQUITECTURA REAL: SERVIDOR + BOT THREAD                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PROCESO 1: WEB SERVER (FastAPI + Uvicorn)                                  │
│  ────────────────────────────────────────────────────────────────            │
│  Endpoints:                                                                  │
│  • GET / (home)  ──────────────────────────────────────────┐               │
│  • GET /health (monitoring)                                │               │
│  • POST /auth/register, /auth/login (JWT)                  │ REST API      │
│  • POST /cv/upload, GET /cv/current (CV master)            │               │
│  • POST /offers/analyze (scraping + análisis)              │ ────────────►  │
│  • GET /offers (lista paginada)                            │               │
│  • POST /adaptations/create (generación CV adaptado)       │ PostgreSQL    │
│  • GET /adaptations (historial)                            │               │
│  • GET/PUT /profile (datos usuario)                        │               │
│                                                              │               │
│  ┌────────────────────────────────────────────────────────┐ │               │
│  │ FastAPI App                                            │ │               │
│  │ • CORS configurado (localhost, Vercel, HF Spaces)     │ │               │
│  │ • Rate limiting: 60/min default, 10/min adaptations   │ │               │
│  │ • 2 connection pools: async (FastAPI) + sync (bot)    │ │               │
│  │ • Thread-safe: event loops separados                   │ │               │
│  └────────────────────────────────────────────────────────┘ │               │
│                                                              │               │
│  PROCESO 2: BOT THREAD (Daemon - Polling cada 600s)        │               │
│  ────────────────────────────────────────────────────────────               │
│  ┌──────────────────────────────────────────────────────┐                  │
│  │ Loop infinito (arranque automático en import):       │                  │
│  │                                                      │                  │
│  │ 1. Gmail API ──────────► GmailJobCollector           │                  │
│  │    • Búsqueda: alertas (<14d) de LinkedIn/InfoJobs  │                  │
│  │    • Limpieza automática: emails >14 días a TRASH   │                  │
│  │             │                                        │                  │
│  │ 2. Web Scraping ──────► scraper.py (Cascada)         │                  │
│  │    • Intento 1: Jina AI (markdown limpio)            │                  │
│  │    • Intento 2: FireCrawl (JS rendering)             │                  │
│  │    • Intento 3: HTTP directo (fallback)              │                  │
│  │             │                                        │                  │
│  │ 3. Brain (LLM) ────────► brain.py (DeepSeek)         │                  │
│  │    • Fase 0: Validación (cierre, duplicados, etc)    │                  │
│  │    • Fase 1: ATS (requisitos hard - 0-59 fallo)      │                  │
│  │    • Fase 2: RRHH (ajuste cualitativo - 60-100)      │                  │
│  │    • Output: Score, is_valid, análisis detallado     │                  │
│  │             │                                        │                  │
│  │ 4. Save to DB ─────────► JobOffer + TelegramNotif    │                  │
│  │    • Guarda oferta + análisis en BD                  │                  │
│  │    • Encola mensaje Telegram (NO bloquea)            │                  │
│  │             │                                        │                  │
│  │ 5. Telegram Queue ─────► bot.py                      │                  │
│  │    • send_queued_messages() procesa pendientes       │                  │
│  │    • Reintentos: hasta 5 intentos con backoff        │                  │
│  │    • Status: pending → sent/failed                   │                  │
│  └──────────────────────────────────────────────────────┘                  │
│                                                                              │
│  EXTERNAL SERVICES:                                                         │
│  ├─ PostgreSQL (ofertas, usuarios, notificaciones)                         │
│  ├─ Google Gmail API (OAuth 2.0)                                           │
│  ├─ Jina AI (scraping - primario, API key opcional)                        │
│  ├─ FireCrawl (scraping - fallback con JS rendering)                       │
│  ├─ DeepSeek API (análisis dual-fase)                                      │
│  ├─ Cloudinary (almacenamiento PDFs + avatars)                             │
│  └─ Telegram Bot API (notificaciones usuario)                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Componentes Principales del Backend

**Módulos Core (src/):**

- **`main.py`** - Entry point de la aplicación
  - FastAPI + Uvicorn en puerto 7860 (HF Spaces) o 7861 (local)
  - Dos endpoints web: `GET /` y `GET /health` (keep-alive para Render)
  - Inicia daemon thread con lógica del bot al ser importado
  - Configura CORS, rate limiting, y todos los routers
  - Maneja Windows async loop policy (SelectorEventLoop vs ProactorEventLoop)
  - Event loops separados: async para FastAPI, sync para bot thread

- **`bot.py` - TelegramNotifier**
  - `send_match_alert()`: Encola mensajes en BD (no bloquea, devuelve inmediatamente)
  - `send_queued_messages()`: Worker que procesa la cola de notificaciones
  - Reintentos automáticos: hasta 5 intentos con exponential backoff
  - Formato HTML con emojis: ⛔ ATS_BLOCK, ⚠️ Descarte, ✅ Apto, 🚀 Fuerte, 🔥 Ideal
  - Estados: pending → sent / failed (con timestamp)

- **`brain.py` - RecruitmentBrain**
  - Análisis estructurado en 3 fases:
    - **Fase 0**: Validación (oferta cerrada, texto muy corto, etc) → Score 0
    - **Fase 1**: ATS (requisitos indispensables) → 0-59 = fallo automático
    - **Fase 2**: Evaluación cualitativa (coherencia, profundidad, etc) → 60-100
  - Output: `RecruitmentDecision` con JSON validado
  - Anti-alucinación: solo información del texto scrapeado, sin inventar datos
  - Extrae automáticamente: título normalizado, empresa, salario, beneficios, skills

- **`mail_agent.py` - GmailJobCollector**
  - OAuth 2.0 vía Google API (token.json + credentials.json)
  - `get_offers()`: Orquesta limpieza + búsqueda
  - `_cleanup_old_emails()`: Elimina emails >14 días de LinkedIn/InfoJobs a TRASH
  - `_fetch_recent_offers()`: Busca alertas no leídas (<14 días), no duplicadas
  - Distingue entre LinkedIn e InfoJobs por sender para extraer URLs correctas
  - Resuelve redirects en URLs de tracking

- **`scraper.py` - scrape_offer_content()**
  - Cascada de 3 estrategias:
    1. **Jina AI** (API gratuita con header auth opcional) → markdown limpio
    2. **FireCrawl** (renderizado JS, mejor para AJAX) → markdown
    3. **HTTP directo** (último recurso si ambas fallan)
  - Limpieza de URLs: elimina parámetros que causan 422
  - Retry logic: 2 reintentos con exponential backoff (1s between retries)
  - Manejo de selectores CSS específicos por plataforma

- **`cv_generator.py` - CVGenerator**
  - `generate_for_offer()`: Orquesta adaptación completa (async)
  - `_adapt_with_deepseek()`: Adapta secciones del CV según requisitos de oferta
  - `_build_latex_template()`: Genera LaTeX a partir de datos maestro + adaptaciones
  - `_compile_latex_to_pdf()`: Compila LaTeX → PDF vía `latex_compiler.py`
  - Upload automático a Cloudinary con nombre: `cv_optimizados/{titulo}_{empresa}_{candidato}.pdf`
  - Guarda URL en BD y marca status como "done"

- **`loader.py`** - Extrae texto de PDF maestro para contexto del análisis
- **`storage.py`** - Integración Cloudinary (upload/delete de PDFs y avatars)
- **`token_manager.py`** - Gestión de tokens OAuth de Gmail (refresh automático)
- **`latex_compiler.py`** - Compila LaTeX a PDF (reportlab)
- **`database.py`** - Configuración SQLAlchemy + modelos (User, JobOffer, CVAdaptation, TelegramNotification)

**API Routes (src/api/routes/):**

- **`auth.py`** - `/auth` prefix
  - `POST /register` - Crea usuario con email/password
  - `POST /login` - Genera JWT token
  - `POST /google-callback` - OAuth de Google (opcional)

- **`cv.py`** - `/cv` prefix
  - `POST /upload` - Sube CV maestro (PDF/DOCX, max 10MB)
  - `GET /current` - Preview del CV actual cargado
  - `POST /preview` - Previsualiza CV antes de usar

- **`offers.py`** - Sin prefix
  - `GET /offers` - Lista ofertas (skip, limit, filtrable)
  - `POST /offers/analyze` - Scraping + análisis de nueva URL
  - `GET /offers/{id}` - Detalle de oferta con análisis

- **`adaptations.py`** - `/adaptations` prefix
  - `POST /create` - Genera CV adaptado para oferta (score ≥ 60)
  - `GET` - Lista adaptaciones del usuario (paginado)
  - `GET /{id}` - Detalle + descarga de adaptación
  - `GET /{id}/download` - Redirect a Cloudinary (PDF directo)

- **`profile.py`** - `/profile` prefix
  - `GET` - Obtiene datos del perfil (nombre, skills, idiomas, etc)
  - `PUT` - Actualiza datos del perfil
  - `POST /avatar` - Sube avatar (imagen, max 5MB)

**Services (src/api/services/):**

- **`analysis_service.py`** - Orquesta análisis: scrape → brain → save to DB
- **`adaptation_service.py`** - Orquesta generación: load CV → deepseek adapt → LaTeX → PDF → upload
- **`cv_service.py`** - Gestión de archivos CV (upload, preview, extracción)
- **`auth_service.py`** - Autenticación, JWT, hash de contraseñas

**Frontend (frontend/) - React 18 + Vite:**

**Stack:**

- React 18.3 (UI framework)
- Vite 6.4 (build tool, dev server con HMR)
- React Router v6 (routing SPA)
- Zustand 4.4 (state management - global store)
- React Query 5 (server state / data fetching)
- React Hook Form + Zod (forms con validación)
- TailwindCSS 3.4 (styling)
- Lucide React (icons)
- Axios (HTTP client con JWT interceptors)
- i18next (internacionalización: ES/EN)

**Estructura de Carpetas:**

```
frontend/
├── src/
│   ├── App.jsx                    # Router principal (13 rutas)
│   ├── main.jsx                   # Entry point
│   ├── i18n.js                    # i18next config
│   │
│   ├── features/                  # Módulos por dominio
│   │   ├── landing/
│   │   │   └── LandingPage.jsx    # Homepage pública
│   │   ├── auth/
│   │   │   ├── pages/LoginPage, RegisterPage, GoogleCallbackPage
│   │   │   └── components/LoginForm, RegisterForm, PrivacyModal, TermsModal
│   │   ├── dashboard/
│   │   │   └── DashboardPage.jsx  # Hub central (4 opciones)
│   │   ├── cv/
│   │   │   ├── pages/CVPage.jsx
│   │   │   └── components/CVUpload, CVPreview
│   │   ├── analysis/
│   │   │   ├── pages/AnalysisPage, ResultPage, HistoryPage
│   │   │   └── components/AnalysisForm, ResultCard, AnalysisListItem
│   │   ├── adaptations/
│   │   │   ├── pages/AdaptationPage, AdaptationsHistoryPage, AdaptationDetailPage
│   │   │   └── components/AdaptationPreview, CVPreviewHTML, PDFDownloadButton
│   │   └── profile/
│   │       └── ProfilePage.jsx    # Editar perfil + avatar
│   │
│   ├── shared/
│   │   ├── components/            # Reutilizables globales
│   │   │   ├── Layout.jsx         # Navbar + Sidebar + main + Footer
│   │   │   ├── Navbar.jsx         # Header con menu
│   │   │   ├── Sidebar.jsx        # Menú lateral (6 opciones)
│   │   │   ├── Footer.jsx
│   │   │   ├── ProtectedRoute.jsx # Wrapper: requiere token
│   │   │   ├── CVRequiredRoute.jsx # Wrapper: requiere CV cargado
│   │   │   ├── Spinner.jsx        # Loading universal
│   │   │   ├── CardItem.jsx       # Card genérico (ofertas/CVs)
│   │   │   ├── Modal.jsx, Toast.jsx, LanguageSwitcher.jsx
│   │   │   └── index.js (exports)
│   │   └── hooks/
│   │       └── useAuth.js
│   │
│   ├── services/                  # API clients (axios)
│   │   ├── apiClient.js           # Axios instance con interceptors
│   │   ├── authService.js         # login, register, googleCallback
│   │   ├── cvService.js           # upload, getCurrent, getPreview
│   │   ├── analysisService.js     # analyze, getHistory, getDetail
│   │   ├── adaptationService.js   # create, getList, getDetail
│   │   ├── profileService.js      # getProfile, updateProfile, uploadAvatar
│   │   └── localeService.js       # i18next init
│   │
│   ├── stores/
│   │   └── globalStore.js         # Zustand store (auth, cv, analysis, etc)
│   │
│   ├── hooks/
│   │   └── useLocale.js           # i18next wrapper
│   │
│   └── index.css                  # Tailwind + custom brand colors
│
├── vite.config.js                 # Config Vite + alias + proxy
├── tailwind.config.js             # Tema (brand-black, brand-gold, etc)
├── package.json
└── .env.local                     # VITE_API_URL (backend URL)
```

**Rutas (13 rutas en App.jsx):**

| Ruta                                  | Componente             | Requerimientos | Descripción            |
| ------------------------------------- | ---------------------- | -------------- | ---------------------- |
| `/`                                   | LandingPage            | Público        | Homepage               |
| `/auth/login`                         | LoginPage              | Público        | Login con email/Google |
| `/auth/register`                      | RegisterPage           | Público        | Registro               |
| `/auth/google-callback`               | GoogleCallbackPage     | Público        | OAuth callback         |
| `/dashboard`                          | DashboardPage          | Token          | Hub central            |
| `/dashboard/cv`                       | CVPage                 | Token          | Upload/preview CV      |
| `/dashboard/analysis`                 | AnalysisPage           | Token          | Formulario + lista     |
| `/dashboard/analysis/result/:id`      | ResultPage             | Token          | Detalle análisis       |
| `/dashboard/analysis/history`         | HistoryPage            | Token          | Historial ofertas      |
| `/dashboard/adaptations/generate/:id` | AdaptationPage         | Token + CV     | Generar CV             |
| `/dashboard/adaptations`              | AdaptationsHistoryPage | Token + CV     | Historial CVs          |
| `/dashboard/adaptations/:id`          | AdaptationDetailPage   | Token + CV     | Preview + descarga     |
| `/profile`                            | ProfilePage            | Token          | Editar perfil          |

**State Management (Zustand):**

```javascript
globalStore.js (2000+ líneas)
├── auth slice: { user, token, isLoading, error }
│   └─ actions: login, register, logout, restoreSession, googleCallback
├── cv slice: { currentCV, cvHistory, isLoading }
│   └─ actions: fetchCurrentCV, uploadCV, deleteCV
├── analysis slice: { analyses, currentAnalysis, isAnalyzing, error }
│   └─ actions: createAnalysis, fetchHistory, getDetail
├── adaptations slice: { adaptations, currentAdaptation, isGenerating }
│   └─ actions: createAdaptation, fetchList, getDetail, downloadPDF
├── profile slice: { data, avatar, isLoading }
│   └─ actions: loadProfile, updateProfile, uploadAvatar
├── locale slice: { initialized, language }
│   └─ actions: setInitialized, changeLanguage
└── (cada acción: axios call → update store → return result)
```

**API Client (apiClient.js):**

```javascript
Axios instance:
├─ baseURL: VITE_API_URL (env) → http://localhost:7860
├─ Request interceptor:
│  └─ inyecta token en header Authorization: Bearer {token}
└─ Response interceptor:
   ├─ 401 → logout automático + redirect /auth/login
   └─ error → rechaza promesa
```

**Protección de Rutas:**

```
<ProtectedRoute>
├─ Verifica: token en store
├─ Si no: <Navigate to="/auth/login" />
└─ Si sí: <Component />

<CVRequiredRoute>
├─ Verifica: token + cv.currentCV exists
├─ Si no CV: <Navigate to="/dashboard/cv" /> (con toast)
└─ Si sí: <Component />
```

**Flujo de Componentes (Ejemplo: Análisis):**

```
App.jsx
  ├─ <Routes>
  │   └─ <Route path="/dashboard/analysis" element={<ProtectedRoute><AnalysisPage/></ProtectedRoute>} />
  │
  ├─ AnalysisPage.jsx
  │   ├─ <Layout>
  │   ├─ <AnalysisForm onSuccess={handleSuccess} />
  │   │   ├─ useForm(resolver: zodResolver(schema))
  │   │   ├─ Tab: URL vs Texto
  │   │   ├─ Submit: analysisActions.createAnalysis(url)
  │   │   │   └─ analysisService.createAnalysis({offer_url: url})
  │   │   │       └─ apiClient.post('/offers/analyze', ...)
  │   │   │           ├─ Backend scrapes + analyzes
  │   │   │           ├─ Returns: {score, is_valid, job_title, ...}
  │   │   │           └─ Store: analysis.analyses.push(result)
  │   │   └─ isAnalyzing? <Spinner />
  │   │
  │   ├─ CardItem × N (list)
  │   │   ├─ resultCard.score badge
  │   │   ├─ resultCard.title + company
  │   │   └─ onClick → navigate(`/dashboard/analysis/result/${id}`)
  │   │
  │   └─ </Layout>
  │
  └─ ResultPage.jsx
      ├─ <Layout>
      ├─ <ResultCard analysis={data} />
      │   ├─ Score display (0-100)
      │   ├─ is_valid badge (✓ / ✗)
      │   ├─ Análisis summary
      │   ├─ Job details (title, company, salary, skills)
      │   └─ [Botón] "Generar CV Adaptado" (si is_valid=true)
      │       └─ onClick → navigate(`/dashboard/adaptations/generate/${analysisId}`)
      │
      └─ </Layout>
```

**i18next (Internacionalización):**

```
Soporta: ES (español), EN (inglés)
Files: src/i18n.js
Keys: pages.analysis.*, pages.dashboard.*, auth.login, etc
Hook: const { t, i18n } = useLocale()
```

---

---

## 🔗 Integración Frontend-Backend

### Flujo Completo: User → React UI → FastAPI → DB → React Update

```
┌─────────────────────────────────────────────────────────────────────────┐
│ USER INTERACTION IN REACT (frontend/)                                   │
│                                                                           │
│  1. User ingresa URL en AnalysisForm                                    │
│     └─ React Hook Form captura input                                    │
│        └─ Zod valida: min 10 chars                                      │
│           └─ Submit → analysisActions.createAnalysis(url)               │
│              (Zustand store action)                                      │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ API CALL WITH JWT AUTH (apiClient.js interceptor)                      │
│                                                                           │
│  2. analysisService.createAnalysis(data)                                │
│     └─ apiClient.post('/offers/analyze', {offer_url: url})             │
│        ├─ Request interceptor: adds Authorization header                │
│        │  └─ Header: Authorization: Bearer {token}                      │
│        └─ Response interceptor:                                          │
│           ├─ 200 → parse response                                       │
│           ├─ 401 → logout + redirect /auth/login                       │
│           └─ error → reject promise                                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND PROCESSING (FastAPI)                                            │
│                                                                           │
│  3. POST /offers/analyze                                                │
│     └─ offers_router.analyze_offer()                                    │
│        ├─ get_current_user() → valida JWT                              │
│        ├─ analysis_service.analyze_job_url(url, user_id)               │
│        │   ├─ scraper.py: Jina → FireCrawl → HTTP                      │
│        │   ├─ brain.py: Fase 0/1/2 dual-phase                          │
│        │   └─ save_offer_to_db()                                        │
│        │       ├─ JobOffer created                                      │
│        │       ├─ analysis_result (JSONB)                              │
│        │       ├─ is_valid = (score >= 60)                             │
│        │       └─ Telegram notif enqueued (non-blocking)               │
│        └─ Return: AnalysisResponse                                      │
│           {score, is_valid, job_title, company, analysis_result, ...}  │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND STORES & UI UPDATE (Zustand)                                   │
│                                                                           │
│  4. analysisService promise resolves                                    │
│     └─ analysisActions.createAnalysis:                                  │
│        ├─ set(analysis.isAnalyzing = false)                            │
│        ├─ set(analysis.analyses.push(result))                          │
│        ├─ set(analysis.currentAnalysis = result)                       │
│        └─ Store updated → React components re-render                    │
│           └─ UI shows new card in list                                  │
│           └─ Redirect: navigate(`/dashboard/analysis/result/${id}`)    │
│              └─ ResultPage loads with analysis.currentAnalysis          │
│                 ├─ <ResultCard> renders score, is_valid, details       │
│                 └─ User sees: Score 0-100, band color, summary         │
│                    ├─ If score < 60: [Generar CV] DISABLED             │
│                    └─ If score ≥ 60: [Generar CV] ENABLED              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Generación de CV Adaptado

```
┌─────────────────────────────────────────────────────────────────────────┐
│ USER CLICK: "Generar CV Adaptado" (ResultCard)                         │
│                                                                           │
│  1. Button onClick → navigate(`/adaptations/generate/${analysisId}`)    │
│     └─ AdaptationPage mounts                                            │
│        ├─ <Spinner message="Preparando..."/> (UI locked)               │
│        └─ componentDidMount → check is_valid = true (guard)            │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ API CALL: POST /adaptations/create                                      │
│                                                                           │
│  2. adaptationActions.createAdaptation(analysis_id)                     │
│     └─ adaptationService.createAdaptation({analysis_id})               │
│        └─ apiClient.post('/adaptations/create', {analysis_id})         │
│           ├─ Request: JWT header added                                  │
│           └─ Response: {adapted_cv_url, adapted_cv_html}               │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND LONG-RUNNING TASK (30-60s)                                      │
│                                                                           │
│  3. POST /adaptations/create                                            │
│     └─ adaptation_service.create_adaptation(analysis_id, user_id)      │
│        ├─ Load master CV from Cloudinary                               │
│        ├─ cv_generator._adapt_with_deepseek()                          │
│        │   └─ DeepSeek: adapt secciones (10-20s)                       │
│        ├─ cv_generator._build_latex_template()                         │
│        │   └─ Merge datos + adaptaciones (5s)                          │
│        ├─ latex_compiler.compile_to_pdf()                              │
│        │   └─ reportlab: LaTeX → PDF (20-40s)                          │
│        ├─ storage.upload_pdf_async()                                   │
│        │   └─ Cloudinary: save PDF + return URL                        │
│        ├─ Update BD:                                                    │
│        │   ├─ CVAdaptation: save adapted_cv_url                        │
│        │   └─ JobOffer: update optimized_cv_url                        │
│        └─ Return: {adapted_cv_url, adapted_cv_html, created_at}        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND: PREVIEW + DOWNLOAD (UI Update)                                │
│                                                                           │
│  4. Promise resolves → Store updated                                    │
│     └─ AdaptationPage / AdaptationDetailPage:                          │
│        ├─ <Spinner /> hidden                                            │
│        ├─ <AdaptationPreview>                                           │
│        │   └─ <iframe srcDoc={adapted_cv_html} />                      │
│        └─ <PDFDownloadButton>                                           │
│            └─ onClick → navigate or GET /download                       │
│               └─ Redirect to Cloudinary → browser downloads PDF         │
│                                                                           │
│  User can:                                                               │
│  ├─ Preview CV en browser                                              │
│  ├─ Descargar PDF desde Cloudinary                                     │
│  └─ Ver en historial (/adaptations)                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estado Compartido (Zustand) vs Local (React Hook Form)

```
GLOBAL STATE (Zustand store - persisten entre páginas):
├─ auth.user, auth.token → usado en ProtectedRoute, Navbar
├─ cv.currentCV → usado en CVRequiredRoute, ProfilePage
├─ analysis.analyses → lista ofertas analizadas
├─ analysis.currentAnalysis → detalle de oferta seleccionada
├─ adaptations.adaptations → lista CVs generados
├─ profile.data → datos usuario (nombre, skills, idiomas)
└─ locale.language → idioma seleccionado (ES/EN)

LOCAL STATE (React Hook Form - form-level only):
├─ AnalysisForm: { type: 'url'|'text', content: string }
├─ RegisterForm: { email, password, confirmPassword }
├─ ProfileForm: { name, skills, languages, ... }
└─ CVUploadForm: { file: File }

API RESPONSES (después convertidos a global state):
├─ POST /auth/login → auth.token + auth.user
├─ POST /offers/analyze → analysis.currentAnalysis + analysis.analyses.push
├─ POST /adaptations/create → adaptations.currentAdaptation
└─ GET /profile → profile.data
```

---

---

## 🔍 Flujo Completo del Análisis (Dual-Fase)

### Fase 0: Validación Inicial

```
Input: URL de oferta
  ↓
¿Oferta disponible? (no cerrada, no genérica)
¿Texto suficiente? (>200 caracteres)
¿No es duplicado?
  ↓
NO → Score: 0, Summary: "SYSTEM_BLOCK: OFERTA CERRADA O NO DISPONIBLE"
```

### Fase 1: ATS (Applicant Tracking System) - Requisitos Indispensables

```
Análisis de:
  ├─ Experiencia (años) → Debe cumplir mínimo requerido (sin redondear)
  ├─ Habilidades HARD (técnicas) → Todas las "imprescindibles" deben estar
  ├─ Idiomas → Si es excluyente, candidato debe tener
  └─ Sector → Validar alineación básica

Resultado:
  ├─ PASA → Continúa a Fase 2
  └─ FALLA → Score: 0-59, Match: False, Motivo: "ATS_BLOCK: [razón exacta]"

Ejemplos de rechazo ATS:
  ├─ "Experiencia Insuficiente (Tiene 2, Piden 3)"
  ├─ "Idioma requerido no disponible (Piden C1 Alemán)"
  ├─ "Skills críticas faltantes (Piden Java, candidato solo tiene Python)"
  └─ "Sector incompatible (Piden Medicina, candidato es Ventas)"
```

### Fase 2: Evaluación Cualitativa (RRHH) - Score 60-100

```
Análisis de:
  ├─ Coherencia → ¿Tiene sentido este puesto en su trayectoria?
  ├─ Profundidad → ¿Match real o superficial?
  ├─ Skills Soft → Liderazgo, comunicación, adaptabilidad requeridas
  ├─ Beneficios → ¿Oferecidos vs esperados?
  └─ Proyección → ¿Oportunidad de crecimiento?

Scoring:
  ├─ 60-69: Descarte ⚠️  (pasa ATS pero débil cualitativamente)
  ├─ 70-79: Apto ✅       (candidato competente, worth applying)
  ├─ 80-89: Fuerte 🚀    (muy buen match)
  └─ 90-100: Ideal 🔥    (ajuste perfecto)
```

### Decisión Final

```
is_valid = (score >= 60)
  ├─ TRUE → Permite generar CV adaptado
  └─ FALSE → Bloquea adaptación (usuario solo ve el análisis)

Output JSON:
{
  "score": 75,
  "is_valid": true,
  "job_title": "Senior Python Developer",
  "company": "TechCorp",
  "salary": "€45k-55k",
  "summary": "ATS_PASS: Experiencia y skills verificadas. RRHH: Coherencia alta con trayectoria...",
  "analysis_details": {...}
}
```

---

---

## 🎯 Bandas de Puntuación (Scoring Real)

El sistema devuelve un **score 0-100 calculado en DOS FASES independientes**:

| Fase     | Rango    | Nivel           | Icono | Acción     | Descripción                                                                      |
| -------- | -------- | --------------- | ----- | ---------- | -------------------------------------------------------------------------------- |
| **ATS**  | 0 – 59   | **RECHAZO ATS** | ⛔    | BLOQUEA CV | Faltan requisitos indispensables (skills hard, experiencia, idiomas excluyentes) |
| **RRHH** | 60 – 69  | **Descarte**    | ⚠️    | PERMITE CV | Pasa ATS pero coherencia baja, match superficial                                 |
| **RRHH** | 70 – 79  | **Apto**        | ✅    | PERMITE CV | Candidato competente, alineación moderada (🎯 **objetivo principal**)            |
| **RRHH** | 80 – 89  | **Fuerte**      | 🚀    | PERMITE CV | Match muy sólido, candidato destacado                                            |
| **RRHH** | 90 – 100 | **Ideal**       | 🔥    | PERMITE CV | Ajuste casi perfecto, match excepcional                                          |

### Lógica de Decisión

```
if score < 60:
    is_valid = False
    puede_adaptar_cv = False
    motivo = "ATS_BLOCK: [requisito faltante exacto]"
    Ejemplos:
    ├─ "Experiencia Insuficiente (Tiene 2, Piden 3)"
    ├─ "Skills críticas faltantes (Piden Java, solo tiene Python)"
    ├─ "Idioma excluyente no disponible (Piden C1 Alemán)"
    └─ "Sector incompatible (Piden Medicina, es Ventas)"

elif score >= 60:
    is_valid = True
    puede_adaptar_cv = True
    motivo = "ATS_PASS → RRHH: [análisis cualitativo]"
    Ejemplos:
    ├─ 65: "Pasa ATS. Coherencia moderada con trayectoria"
    ├─ 75: "ATS OK. Strong match, excelente fit técnico"
    └─ 92: "Perfect match. Candidato ideal para este rol"
```

### Comportamiento en UI

| Score  | Banda    | Color           | Botón "Generar CV" | Historial                |
| ------ | -------- | --------------- | ------------------ | ------------------------ |
| 0-59   | RECHAZO  | 🔴 Rojo         | ❌ DISABLED        | Guardado para referencia |
| 60-69  | DESCARTE | 🟠 Naranja      | ✅ Activo          | Puede generar si quiere  |
| 70-79  | APTO     | 🟢 Verde        | ✅ Activo          | **Recomendado**          |
| 80-89  | FUERTE   | 🟢 Verde Oscuro | ✅ Activo          | Muy recomendado          |
| 90-100 | IDEAL    | 🟡 Oro          | ✅ Activo          | Prioritario              |

### Garantía de Validez

- ✅ **Score ≥ 60**: DeepSeek verificó requisitos ATS + evaluó match cualitativo
- ❌ **Score < 60**: Rechazo automático por ATS → no vale la pena adaptar CV
- 📊 **Desglose visible**: Usuario ve motivos exactos (Fase 1 + Fase 2) en detalle
- 🔒 **Anti-alucinación**: Solo información del texto original, nunca inventado

---

---

## 🛠️ Stack Tecnológico {#-stack-tecnológico}

### Backend

| Tecnología                       | Propósito                      |
| -------------------------------- | ------------------------------ |
| **FastAPI**                      | Framework web moderno y rápido |
| **Uvicorn**                      | Servidor ASGI                  |
| **SQLAlchemy (asyncio)**         | ORM asincrónico                |
| **PostgreSQL / asyncpg**         | Base de datos escalable        |
| **Alembic**                      | Migraciones de BD              |
| **LangChain + langchain-openai** | Orquestación de LLM            |
| **DeepSeek v4-Flash**            | LLM para análisis y adaptación |
| **Cloudinary**                   | Almacenamiento de archivos     |
| **Firecrawl / Jina AI**          | Web scraping avanzado          |
| **slowapi**                      | Rate limiting                  |
| **PyPDF**                        | Procesamiento de PDF           |
| **pydantic-settings**            | Configuración con env vars     |
| **passlib / python-jose**        | Hashing y JWT                  |

### Frontend

| Tecnología          | Propósito         |
| ------------------- | ----------------- |
| **React 18.3**      | UI interactiva    |
| **Vite 6.4**        | Build tool rápido |
| **React Router v6** | Navegación SPA    |
| **Zustand 4.4**     | State management  |
| **React Query 5**   | Gestión de datos  |
| **React Hook Form** | Formularios       |
| **TailwindCSS 3.4** | Estilos           |
| **Axios 1.7**       | HTTP client       |
| **Zod 3.22**        | Validación        |
| **Lucide React**    | Iconos            |

---

---

## 📦 Requisitos Previos

### Software

- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- **PostgreSQL 12+** (base de datos)
- **Git** (control de versiones)

### Cuentas Online

- **Google Cloud Platform** - Para Gmail API y/o Gemini
- **Cloudinary** - Para almacenamiento de archivos (opcional)
- **Firecrawl** - Para web scraping avanzado (opcional)
- **Telegram Bot** - Para notificaciones (opcional)
- **DeepSeek / OpenAI** - Para análisis con LLM (opcional)

---

## 🚀 Instalación Local

### 1. Clonar el Repositorio

```bash
git clone https://github.com/AngelPereiraR/IABD_PIA.git
cd "IABD_PIA/Tema 04/Fast API/Recopilador Ofertas Trabajo Validas"
```

### 2. Configurar Backend

#### 2.1 Crear entorno virtual

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 2.2 Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 2.3 Configurar variables de entorno

Crea un archivo `.env` en la raíz:

```env
# === DATABASE ===
DATABASE_URL=postgresql+asyncpg://user:password@localhost/opticv_db

# === JWT SECURITY ===
SECRET_KEY=tu_secret_key_super_segura_aqui
ALGORITHM=HS256

# === LLM (DeepSeek recomendado) ===
DEEPSEEK_API_KEY=sk-xxxx

# === CLOUDINARY (Almacenamiento) ===
CLOUDINARY_NAME=xxxx
CLOUDINARY_API_KEY=xxxx
CLOUDINARY_API_SECRET=xxxx

# === GMAIL (Opcional) ===
GOOGLE_CREDENTIALS_JSON={"installed":{...}}
GOOGLE_TOKEN_JSON={"token":"..."}

# === TELEGRAM (Opcional - procesado en Render Worker) ===
TELEGRAM_BOT_TOKEN=xxxx
TELEGRAM_CHAT_ID=xxxx

# === FIRECRAWL (Opcional - fallback de scraping) ===
FIRECRAWL_API_KEY=xxxx

# === SERVER ===
PORT=7860
```

#### 2.4 Inicializar base de datos

```bash
# Crear tablas
python init_db.py

# Aplicar migraciones (si hay)
alembic upgrade head

# Inicializar usuario admin con CV y avatar en Cloudinary (opcional)
python seed_user.py
```

### 3. Configurar Frontend

#### 3.1 Instalar dependencias

```bash
cd frontend
npm install
```

#### 3.2 Crear archivo de configuración

Crea `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:7860
```

---

## ⚙️ Configuración {#-configuración}

### 1. Configurar Gmail (Opcional pero Recomendado)

#### A. Crear proyecto en Google Cloud Console

1. Ve a https://console.cloud.google.com
2. Crea un nuevo proyecto
3. Habilita **Gmail API**
4. Descarga credenciales OAuth (Desktop app) como `credentials.json`

#### B. Generar token

```bash
python src/setup_auth.py
```

Esto generará `token.json` automáticamente.

### 2. Configurar LLM (DeepSeek o Gemini)

- **DeepSeek**: Obtén tu API key en https://platform.deepseek.com
- **Gemini**: Obtén tu API key en https://aistudio.google.com/app/apikey

### 3. Configurar Cloudinary (Para almacenar PDFs)

1. Regístrate en https://cloudinary.com
2. Obtén tus credenciales desde el dashboard
3. Añádelas al `.env`

---

## 💻 Uso

### Desarrollo Local

#### Backend

```bash
# Con entorno virtual activado
python main.py
```

Servidor disponible en: **http://localhost:7860**
Documentación API: **http://localhost:7860/docs**

#### Frontend

```bash
cd frontend
npm install                    # Solo primera vez

npm run dev                    # Dev server con HMR (Hot Module Reload)
                              # Abre http://localhost:5173 automáticamente
```

**Dev Server características:**

- **HMR**: Cambios en código actualizan el navegador al instante
- **Proxy**: Requests a `/api/*` se redirigen al backend (ver `vite.config.js`)
- **VITE_API_URL**: Variable de entorno que configura backend URL
  - Local: `http://localhost:7860`
  - Producción: `https://opticv-backend.hf.space` (Vercel .env)

**URL disponible:** http://localhost:5173

**Debug en navegador:**

```
1. Abre DevTools (F12)
2. Network tab: inspecciona requests a /api/* (JWT headers, response)
3. Application tab → LocalStorage:
   ├─ token: JWT bearer token
   ├─ user: {id, email}
   └─ i18nextLng: idioma seleccionado
4. React DevTools extension:
   ├─ Inspecciona component tree
   └─ Ver state en cada componente
5. Console: errores de Zustand, servicios, etc
```

**Build para producción:**

```bash
npm run build                 # Genera dist/ con JS bundleado
npm run preview              # Preview de build en local (http://localhost:5173)
```

### Flujos de Uso (Según el Actor)

#### **Flujo A: Usuario Final (Dashboard Web)**

```
1. Registro / Login
   ├─ POST /auth/register → Crea usuario, devuelve JWT
   ├─ POST /auth/login → Autentica, devuelve JWT
   └─ Token almacenado en localStorage (frontend)

2. Upload CV Maestro
   ├─ POST /cv/upload → Sube PDF
   ├─ Backend: Extrae texto con loader.py, guarda en Cloudinary
   ├─ Retorna: URL + datos estructurados (cv_data JSONB)
   └─ El CV se usa como contexto para todos los análisis

3. Analizar Oferta (Manual - desde UI)
   ├─ POST /offers/analyze
   ├─ Body: {url: "https://linkedin.com/..."}
   ├─ Backend:
   │   ├─ scraper.py: Jina AI → FireCrawl → HTTP directo
   │   ├─ brain.py: Fase 0/1/2 análisis dual-fase
   │   ├─ save_offer_to_db: Guarda JobOffer + análisis
   │   └─ send_match_alert: Encola notificación Telegram (NO bloquea)
   ├─ Retorna: {score, is_valid, analysis_result, ...}
   ├─ Tiempo: 12-25 segundos (scraping 2-8s + análisis 10-15s)
   └─ UI muestra score, band color (rojo/naranja/verde)

4. Ver Historial de Ofertas
   ├─ GET /offers?skip=0&limit=20
   ├─ Retorna: Lista paginada de JobOffers con scores
   └─ UI: Cards con título, empresa, score, botón "Ver detalle"

5. Ver Análisis Detallado
   ├─ GET /offers/{id}
   ├─ Retorna: OfferDetail completo con desglose
   ├─ UI muestra:
   │   ├─ Score y band (0-59/60-69/70-79/80-89/90-100)
   │   ├─ Resultado ATS (pasa/falla + motivo)
   │   ├─ Resultado RRHH (coherencia, profundidad, etc)
   │   ├─ Requisitos extraídos (skills, experiencia, idiomas)
   │   └─ Botón "Generar CV adaptado" (si is_valid = true)
   └─ Si is_valid = false, botón DISABLED

6. Generar CV Adaptado (Solo si score ≥ 60)
   ├─ POST /adaptations/create
   ├─ Body: {analysis_id: 123}
   ├─ Backend:
   │   ├─ cv_generator.py: load CV maestro
   │   ├─ Adaptar secciones vía DeepSeek (10-20s)
   │   ├─ Generar LaTeX (5s)
   │   ├─ Compilar a PDF vía latex_compiler.py (20-40s)
   │   ├─ Upload a Cloudinary
   │   ├─ Guardar en CVAdaptation
   │   └─ Actualizar JobOffer.optimized_cv_url
   ├─ Retorna: {adapted_cv_url, adapted_cv_html}
   ├─ Tiempo: 30-60 segundos
   └─ UI: Preview del CV + botón "Descargar PDF"

7. Descargar CV Adaptado
   ├─ GET /adaptations/{id}/download
   ├─ Retorna: Redirect a Cloudinary (PDF)
   └─ Descarga directo del navegador

8. Historial de Adaptaciones
   ├─ GET /adaptations?skip=0&limit=20
   ├─ Retorna: Lista de CVAdaptations del usuario
   └─ UI: Cards con oferta, fecha creación, botón "Descargar"

9. Gestión de Perfil
   ├─ GET /profile → Obtiene datos actuales
   ├─ PUT /profile → Actualiza cv_data (skills, languages, etc)
   └─ POST /profile/avatar → Sube foto de perfil a Cloudinary
```

#### **Flujo B: Bot Thread (Automático - Background)**

```
Inicia al importar main.py (daemon thread, no bloquea uvicorn)

Loop infinito (cada 600 segundos = 10 minutos):
│
├─ 1. GmailJobCollector.get_offers(limit=5)
│     ├─ Limpia emails >14 días (automático)
│     ├─ Busca alertas no leídas (<14d) de LinkedIn/InfoJobs
│     ├─ Resuelve redirects de tracking
│     └─ Retorna: [urls] (máx 5 nuevas)
│
├─ 2. Para cada URL:
│     ├─ scraper.py: scrape_offer_content(url)
│     │   ├─ Intento 1: Jina AI (gratuito, rápido)
│     │   ├─ Intento 2: FireCrawl (JS rendering)
│     │   ├─ Intento 3: HTTP directo (fallback)
│     │   └─ Retorna: raw_text (markdown/HTML)
│     │
│     ├─ brain.py: RecruitmentBrain.analyze_offer(raw_text, cv_context)
│     │   ├─ Fase 0: Validación
│     │   ├─ Fase 1: ATS check
│     │   ├─ Fase 2: RRHH evaluation
│     │   └─ Retorna: RecruitmentDecision (JSON)
│     │
│     ├─ save_offer_to_db(user_id, offer, analysis)
│     │   ├─ Crea JobOffer en BD
│     │   ├─ Guarda analysis_result (JSONB)
│     │   ├─ Calcula is_valid = (score >= 60)
│     │   └─ Retorna: offer_id
│     │
│     └─ TelegramNotifier.send_match_alert(job_data, analysis)
│         ├─ Si score > 60: Encola en BD (NO bloquea)
│         ├─ Formato: HTML con emojis, score, link
│         └─ Status: pending (esperando a be procesado)
│
├─ 3. Worker: TelegramNotifier.send_queued_messages() (async)
│     ├─ Busca mensajes con status='pending'
│     ├─ Para cada uno: intenta enviar a Telegram
│     ├─ Si éxito: status = 'sent'
│     ├─ Si fallo: retries++, reintenta (máx 5)
│     └─ Si retries > 5: status = 'failed', abandona
│
└─ [Espera 600s] ↻

Error handling:
├─ Email fetch error → Exponential backoff, reintenta
├─ Scraper error → Cascada de métodos (Jina → FireCrawl → HTTP)
├─ Brain error → Log, skip oferta, continúa
├─ Telegram send error → Guarda en BD, reintentos automáticos
└─ Todos los errores se prinean a stdout (visible en Render logs)
```

#### **Timing Real (Aproximado)**

| Operación                  | Tiempo        | Notas                                      |
| -------------------------- | ------------- | ------------------------------------------ |
| **Análisis de oferta**     | 12-25s        | 2-8s scraping + 10-15s DeepSeek            |
| **Generación CV adaptado** | 30-60s        | 10-20s DeepSeek + 20-40s LaTeX compile     |
| **Bot polling**            | Cada 10 min   | Configurable en main.py (POLLING_INTERVAL) |
| **Telegram send**          | <1s           | Encolado en BD, no bloquea                 |
| **Rate limit**             | 60/min global | 10/min en /adaptations                     |

---

## 📁 Estructura del Proyecto {#-estructura-del-proyecto}

```
.
├── main.py                          # Entry point: FastAPI + daemon bot thread
├── requirements.txt                 # Dependencias Python
├── .env.template                    # Variables de entorno (plantilla)
├── init_db.py                       # Inicializa base de datos
├── seed_user.py                     # Siembra datos de prueba (opcional)
├── Dockerfile                       # Docker para HF Spaces
├── entrypoint.sh                    # Script de arranque
│
├── src/
│   ├── __init__.py
│   ├── database.py                  # SQLAlchemy + modelos (User, JobOffer, CVAdaptation, TelegramNotification)
│   ├── bot.py                       # TelegramNotifier: send_match_alert(), send_queued_messages()
│   ├── brain.py                     # RecruitmentBrain: análisis dual-fase (Fase 0/1/2)
│   ├── mail_agent.py                # GmailJobCollector: OAuth, búsqueda, limpieza
│   ├── scraper.py                   # scrape_offer_content(): Cascada Jina → FireCrawl → HTTP
│   ├── cv_generator.py              # CVGenerator: adapt + LaTeX → PDF
│   ├── loader.py                    # load_cv_context(): extrae texto de PDF
│   ├── storage.py                   # Cloudinary: upload/delete PDFs y avatars
│   ├── token_manager.py             # Gestión tokens OAuth de Gmail
│   ├── latex_compiler.py            # compile_latex_to_pdf(): reportlab
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py              # POST /register, /login, /google-callback
│       │   ├── cv.py                # POST /upload, GET /current, POST /preview
│       │   ├── offers.py            # GET /offers, POST /analyze, GET /offers/{id}
│       │   ├── adaptations.py       # POST /create, GET, GET /{id}, GET /{id}/download
│       │   └── profile.py           # GET /profile, PUT /profile, POST /avatar
│       │
│       └── services/
│           ├── __init__.py
│           ├── analysis_service.py  # Orquesta: scrape → brain → save to DB
│           ├── adaptation_service.py# Orquesta: load CV → deepseek → LaTeX → PDF
│           ├── cv_service.py        # Gestión CV: upload, preview, extracción
│           └── auth_service.py      # JWT, hash, autenticación
│
├── tests/
│   ├── test_plan_01_simple.py       # 10 tests básicos
│   ├── test_plan_02_apis.py         # 29 tests de APIs
│   ├── TEST_RESULTS_*.md            # Reportes de pruebas
│   └── ...
│
├── frontend/                        # React 18 + Vite
│   ├── src/
│   │   ├── App.jsx                  # Router (13 rutas)
│   │   ├── main.jsx                 # Entry point
│   │   ├── i18n.js                  # i18next (ES/EN)
│   │   │
│   │   ├── features/                # Módulos por dominio
│   │   │   ├── landing/
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── cv/
│   │   │   ├── analysis/
│   │   │   ├── adaptations/
│   │   │   └── profile/
│   │   │
│   │   ├── shared/
│   │   │   ├── components/          # Componentes reutilizables
│   │   │   │   ├── Layout, Navbar, Sidebar, Footer
│   │   │   │   ├── ProtectedRoute, CVRequiredRoute
│   │   │   │   └── Spinner, Modal, Toast, etc
│   │   │   └── hooks/
│   │   │
│   │   ├── services/                # API clients (axios)
│   │   │   ├── apiClient.js         # Interceptors JWT
│   │   │   ├── authService.js
│   │   │   ├── cvService.js
│   │   │   ├── analysisService.js
│   │   │   ├── adaptationService.js
│   │   │   └── profileService.js
│   │   │
│   │   ├── stores/
│   │   │   └── globalStore.js       # Zustand (auth, cv, analysis, adaptations, profile, locale)
│   │   │
│   │   └── index.css                # Tailwind + brand colors
│   │
│   ├── vite.config.js               # Vite + proxy + alias
│   ├── tailwind.config.js           # Tema (brand-black, brand-gold)
│   ├── package.json
│   └── .env.local                   # VITE_API_URL
│
├── data/
│   └── cv_usuario.pdf               # CV maestro del usuario (requerido)
│
├── credentials.json                 # Google OAuth (generado en deploy)
├── token.json                       # Gmail token (generado en deploy)
├── CLAUDE.md                        # Instrucciones del proyecto
├── README.md                        # Este archivo
├── DOCKER_COMPOSE_SETUP.md          # Guía Docker Compose
├── DEPLOYMENT_GUIDE.md              # Guía de despliegue
├── TESTING_E2E.md                   # Testing end-to-end
└── workbench.md                     # Notas de desarrollo

```

### Archivos Clave

**Backend (Python/FastAPI):**

- **`main.py`** - Punto de entrada: levanta FastAPI en puerto 7860 + inicia daemon thread del bot
- **`src/bot.py`** - Notificador Telegram: encola mensajes en BD + reintentos automáticos
- **`src/brain.py`** - Análisis de ofertas: dual-fase (ATS + RRHH) con DeepSeek
- **`src/mail_agent.py`** - Integración Gmail: OAuth 2.0, búsqueda, limpieza automática
- **`src/scraper.py`** - Web scraping: cascada Jina AI → FireCrawl → HTTP directo
- **`src/cv_generator.py`** - Generación de CV adaptado: LaTeX → PDF → Cloudinary
- **`src/database.py`** - ORM SQLAlchemy con async + modelos de BD

**Frontend (React/Vite):**

- **`frontend/src/App.jsx`** - Router principal con 13 rutas
- **`frontend/src/stores/globalStore.js`** - Zustand: state global (2000+ líneas)
- **`frontend/src/services/apiClient.js`** - Axios con JWT interceptors
- **`frontend/src/features/`** - 7 módulos funcionales (auth, cv, analysis, adaptations, profile, dashboard, landing)

**Configuración & Despliegue:**

- **`.env`** - Variables sensibles (NO commitear)
- **`Dockerfile`** - Build para HF Spaces
- **`entrypoint.sh`** - Script de arranque en Docker
- **`requirements.txt`** - Dependencias Python
- **`frontend/package.json`** - Dependencias Node.js

---

## 📊 Flujo Técnico Detallado

### Flujo de Análisis (User Manual - via Dashboard)

```
┌─────────────────┐
│  User UI Input  │ "Analizar oferta: https://linkedin.com/job/..."
│  (React)        │
└────────┬────────┘
         │
         │ POST /offers/analyze (JWT en header)
         ↓
┌─────────────────────────────────────────────────────────┐
│  Backend - API Handler (offers_router)                  │
│  get_current_user() → valida JWT                        │
│  analysis_service.analyze_job_url(url, user_id)         │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─→ PASO 1: Web Scraping
       │   ├─ scraper.py: scrape_offer_content(url)
       │   ├─ Cascada: Jina AI → FireCrawl → HTTP
       │   └─ Retorna: raw_text (markdown/HTML)
       │
       ├─→ PASO 2: Load User Context
       │   ├─ loader.py: load_cv_context(user_id)
       │   └─ Retorna: CV del usuario (texto)
       │
       ├─→ PASO 3: Análisis DeepSeek
       │   ├─ brain.py: RecruitmentBrain.analyze_offer(raw_text, cv_context)
       │   ├─ Fase 0: Validación → score=0 si cierra
       │   ├─ Fase 1: ATS → score=0-59 si falla
       │   ├─ Fase 2: RRHH → score=60-100 si pasa
       │   └─ Retorna: RecruitmentDecision (JSON)
       │
       ├─→ PASO 4: Guardar en BD
       │   ├─ JobOffer: raw_text, score, is_valid, analysis_result
       │   ├─ Status: "done"
       │   └─ offer_id guardado
       │
       ├─→ PASO 5: Encolar Telegram (async, no bloquea)
       │   ├─ TelegramNotifier.send_match_alert(...)
       │   ├─ TelegramNotification creada con status='pending'
       │   └─ Retorna inmediatamente
       │
       └─→ Retorna AnalysisResponse
           ├─ score
           ├─ is_valid
           ├─ job_title
           ├─ analysis_result
           └─ optimized_cv_url (null aquí)
         ↓
┌─────────────────────────────────────────────────────────┐
│  Frontend - Display Result                              │
│  ├─ Score 0-59: Rojo, "RECHAZO ATS"                    │
│  ├─ Score 60-69: Naranja, "DESCARTE"                   │
│  ├─ Score 70-79: Verde, "APTO" → Botón "Generar CV"   │
│  ├─ Score 80-89: Verde oscuro, "FUERTE"               │
│  └─ Score 90-100: Oro, "IDEAL"                         │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Generación CV (User Manual - via Dashboard)

```
┌──────────────────────────────┐
│  User Click                  │ "Generar CV para esta oferta"
│  (Si is_valid = true)        │ (Botón habilitado solo si score ≥ 60)
└─────────┬────────────────────┘
          │
          │ POST /adaptations/create (analysis_id)
          ↓
┌──────────────────────────────────────────────────────┐
│  Backend - Adaptation Service                        │
│  adaptation_service.create_adaptation(analysis_id)   │
└───────┬──────────────────────────────────────────────┘
        │
        ├─→ PASO 1: Load Offer
        │   ├─ JobOffer.get(analysis_id)
        │   └─ Check: is_valid = true (score ≥ 60)
        │
        ├─→ PASO 2: Load Master CV
        │   ├─ loader.py: load_cv_context(user_id)
        │   ├─ storage.py: download CV from Cloudinary
        │   └─ cv_data (JSONB) con estructura
        │
        ├─→ PASO 3: Adapt Sections via DeepSeek
        │   ├─ cv_generator.py: _adapt_with_deepseek()
        │   ├─ Para cada sección (experience, skills, etc):
        │   │   └─ DeepSeek: "Adapta esto para [requirements]"
        │   ├─ Output: AdaptedCVSections (Pydantic)
        │   └─ Tiempo: 10-20 segundos
        │
        ├─→ PASO 4: Generate LaTeX
        │   ├─ cv_generator.py: _build_latex_template()
        │   ├─ Template + datos maestro + adaptaciones
        │   └─ Retorna: LaTeX source code (texto)
        │
        ├─→ PASO 5: Compile LaTeX → PDF
        │   ├─ latex_compiler.py: compile_latex_to_pdf()
        │   ├─ reportlab: LaTeX → PDF binary
        │   └─ Tiempo: 20-40 segundos
        │
        ├─→ PASO 6: Upload to Cloudinary
        │   ├─ storage.py: upload_pdf_async()
        │   ├─ Nombre: "cv_optimizados/{title}_{company}_{name}.pdf"
        │   └─ Retorna: URL permanente
        │
        ├─→ PASO 7: Save to DB
        │   ├─ CVAdaptation: guardar adapted_cv_url
        │   ├─ JobOffer: actualizar optimized_cv_url
        │   ├─ JobOffer.status = "done"
        │   └─ job_offer_id = adaptation.job_offer_id
        │
        └─→ Retorna AdaptationResponse
            ├─ adapted_cv_url (Cloudinary link)
            ├─ adapted_cv_html (preview)
            └─ created_at
          ↓
┌──────────────────────────────────────────────────────┐
│  Frontend - Display Preview & Download                │
│  ├─ Iframe: muestra adapted_cv_html                  │
│  ├─ Botón: "Descargar PDF" → GET /download           │
│  │   └─ Redirect a Cloudinary (navegador descarga)   │
│  └─ Historial: CV aparece en /adaptations            │
└──────────────────────────────────────────────────────┘
```

### Flujo del Bot Thread (Automático - Background)

```
┌────────────────────────────────────┐
│  Bot Thread Inicia (daemon)        │ Cada 600 segundos (10 minutos)
│  run_bot_logic() en main.py        │
└─────────┬──────────────────────────┘
          │
          ├─→ ETAPA 1: Recolectar URLs
          │   ├─ GmailJobCollector()
          │   ├─ _cleanup_old_emails() → TRASH emails >14 días
          │   ├─ _fetch_recent_offers() → Lista nuevas URLs
          │   └─ Retorna: [urls] sin duplicados
          │
          ├─→ ETAPA 2: Para cada URL
          │   │
          │   ├─ Scrape
          │   │  ├─ scraper.py: scrape_offer_content(url)
          │   │  ├─ Cascada: Jina AI (1) → FireCrawl (2) → HTTP (3)
          │   │  └─ raw_text
          │   │
          │   ├─ Analyze
          │   │  ├─ brain.py: RecruitmentBrain.analyze_offer()
          │   │  ├─ Fase 0/1/2
          │   │  └─ RecruitmentDecision (JSON)
          │   │
          │   ├─ Save
          │   │  ├─ save_offer_to_db(user_id, offer, analysis)
          │   │  ├─ JobOffer creado con status="done"
          │   │  └─ offer_id
          │   │
          │   └─ Notify
          │      ├─ TelegramNotifier.send_match_alert()
          │      ├─ TelegramNotification encolada (status='pending')
          │      └─ NO bloquea (async queue)
          │
          └─→ ETAPA 3: Procesar Cola Telegram
              ├─ TelegramNotifier.send_queued_messages()
              ├─ Query: TelegramNotification where status='pending'
              ├─ Para cada:
              │  ├─ POST https://api.telegram.org/bot...
              │  ├─ Si OK: status='sent'
              │  ├─ Si fallo: retries++, reintenta
              │  └─ Si retries>5: status='failed'
              └─ [Espera 600s] ↻
```

### Event Loops (Thread-Safe)

```
FastAPI/Uvicorn (ASYNC)                Bot Thread (SYNC)
├─ create_async_engine()                ├─ create_engine() (psycopg2)
├─ AsyncSession                         ├─ Session
├─ Pool: 3 connections                  ├─ Pool: 2 connections
└─ Maneja requests REST                 └─ Polling cada 600s
```

---

## 🚀 Despliegue

OptiCV utiliza una **arquitectura distribuida** con múltiples servicios independientes:

### Backend (Hugging Face Spaces via GitHub Actions)

El backend se despliega automáticamente a HF Spaces cuando haces push a GitHub.

1. Crea un Space en https://huggingface.co/new-space
   - Nombre: `opticv-backend`
   - Tipo: Docker
   - Visibilidad: Private
2. Configura `HF_TOKEN` en GitHub Secrets
3. Haz push a `main` → GitHub Actions despliega automáticamente a HF

**URL Producción:** https://opticv-backend.hf.space

### Telegram Worker (Render)

El worker procesa la cola de notificaciones independiente de HF Spaces.

1. Crea un nuevo Web Service en https://dashboard.render.com
2. Conecta tu repo GitHub
3. Dockerfile: `Dockerfile.worker`
4. Configura variables de entorno
5. Deploy automático

### Frontend (Vercel)

El frontend se despliega automáticamente desde Vercel.

1. Conecta tu repositorio en https://vercel.com/new
2. Root Directory: `frontend/`
3. Framework: Vite
4. Configura `VITE_API_URL = https://opticv-backend.hf.space`
5. Deploy automático

**URL Producción:** https://opticv-frontend.vercel.app

---

## 🐛 Troubleshooting

### Error: "database.db: no such file or directory"

**Solución**: Ejecuta `python init_db.py` para crear la base de datos.

### Error: "SECRET_KEY not found"

**Solución**: Asegúrate de tener `.env` con `SECRET_KEY` configurada.

### Error: "CORS blocked"

**Solución**: Verifica que tu frontend está en `allow_origins` en `main.py`.

### Frontend no conecta con backend

**Solución**:

- Verifica que `VITE_API_URL` en `.env.local` es correcto
- Backend debe estar ejecutándose en http://localhost:7860
- CORS debe permitir localhost:5173

### Análisis fallan sin error claro

**Solución**:

- Verifica que tienes una API key de LLM configurada
- Revisa logs del backend: `python main.py`
- Rate limiting puede estar activo

### Bot no envía notificaciones

**Solución**:

- Verifica que `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` están configurados
- Revisa logs: `TelegramNotification` table status
- Reintentos automáticos: hasta 5 intentos

---

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con bcrypt
- ✅ JWT tokens para autenticación
- ✅ CORS configurado correctamente
- ✅ Rate limiting en endpoints
- ✅ Variables sensibles en `.env` (no commitear)
- ✅ OAuth 2.0 para Gmail (sin guardar contraseñas)

---

## 📞 Soporte & Contacto

**Autor**: Ángel Pereira  
**GitHub**: [@AngelPereiraR](https://github.com/AngelPereiraR)  
**Email**: ampr2003@gmail.com

Para problemas o sugerencias, abre un issue en el repositorio.

---

## 📄 Licencia

Proyecto educativo para el ciclo IABD - Curso de Especialización

---

**⚡ ¡Happy Job Hunting! 🎯**
