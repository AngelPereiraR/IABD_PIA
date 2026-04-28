# 🤖 OptiCV - Recopilador Inteligente de Ofertas de Trabajo

Sistema integral de análisis y visualización de ofertas laborales que combina **FastAPI backend**, **React frontend**, **IA Generativa** y **notificaciones en tiempo real**. Monitorea ofertas, analiza su ajuste con tu CV usando criterios profesionales (ATS + RRHH), proporciona adaptaciones personalizadas del CV, y te mantiene informado vía Telegram.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Stack Tecnológico](#-stack-tecnológico)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Local](#-instalación-local)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Despliegue](#-despliegue)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Características

### 🎯 **Análisis Inteligente con IA**

- **Doble Fase de Filtrado**: Simula tanto el escaneo ATS (Applicant Tracking System) como la evaluación de un reclutador humano
- **Puntuación de Ajuste**: Sistema de scoring 0-100 con clasificación automática
- **Anti-Alucinación**: Validación con "grounding" - solo usa información del texto original
- **Extracción Estructurada**: Detecta automáticamente título, empresa, salario, beneficios

### 📊 **Dashboard Web Completo**

- **Historial de Análisis**: Lista paginada de ofertas analizadas con scores
- **Historial de Adaptaciones**: CV adaptados anteriormente, organizados por oferta
- **Vista de Análisis Detallado**: Desglose completo del análisis con justificación
- **Generador de CV Adaptado**: Crea un CV personalizado para cada oferta en tiempo real
- **Gestor de Perfil**: Edita tu información personal y datos del CV

### 🔄 **Adaptación Dinámica de CV**

- **Generación en LaTeX**: CV compilado a PDF vía LaTeX personalizado para cada oferta — no HTML estático
- **Integración con IA**: DeepSeek filtra y adapta cada sección del CV según los requisitos de la oferta (sin inventar datos)
- **Descarga de PDF**: Genera y descarga el CV adaptado directamente desde Cloudinary
- **Historial de Versiones**: Consulta todas las adaptaciones anteriores desde `/dashboard/adaptations`
- **Vista de Detalle**: Previsualización del CV adaptado y botón de descarga en `/dashboard/adaptations/:id`

### 📧 **Integración con Gmail**

- **Búsqueda Automática**: Detecta alertas de empleo no leídas de LinkedIn e InfoJobs
- **Limpieza Automática**: Elimina correos antiguos (>14 días)
- **OAuth 2.0**: Autenticación segura sin guardar contraseñas

### 📱 **Notificaciones Telegram** (Opcional)

- **Alertas Visuales**: Iconos y barras de progreso según nivel de match
- **Respuesta Inmediata**: Notificaciones cuando se encuentra una oportunidad relevante

### 🔐 **Seguridad & Escalabilidad**

- **Autenticación JWT**: Sessions seguras basadas en tokens
- **Rate Limiting**: Control de tasa de API con slowapi
- **Base de Datos Escalable**: PostgreSQL con migraciones Alembic
- **CORS Configurado**: Seguridad entre frontend y backend
- **Encriptación**: Contraseñas hasheadas con bcrypt

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA GENERAL                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────┐    ┌───────────────────────┐ │
│  │  REACT FRONTEND (Vercel) │    │  FASTAPI BACKEND      │ │
│  ├──────────────────────────┤    ├───────────────────────┤ │
│  │ • React Router           │    │ • Uvicorn Server      │ │
│  │ • Zustand State          │    │ • SQLAlchemy ORM      │ │
│  │ • React Query            │    │ • PostgreSQL DB       │ │
│  │ • React Hook Form        │    │ • LangChain           │ │
│  │ • TailwindCSS            │    │ • LLM Integration     │ │
│  │ • Lucide Icons           │    │ • Rate Limiting       │ │
│  └──────────────────────────┘    └───────────────────────┘ │
│           │                                 │                │
│           │         REST API                │                │
│           └─────────────────────────────────┘                │
│                                                             │
│  External Services:                                        │
│  • Google Gmail API (OAuth 2.0)                           │
│  • LLM Provider (DeepSeek / Gemini)                       │
│  • Telegram Bot API (Opcional)                            │
│  • Cloudinary (Storage)                                   │
│  • Firecrawl (Web Scraping)                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

**Backend (src/):**

- `main.py` - FastAPI app con routers y CORS
- `api/routes/` - Endpoints: auth, cv, offers, adaptations, profile
- `api/services/` - Lógica de negocio: analysis, adaptation, cv
- `database.py` - Configuración SQLAlchemy
- `brain.py` - LLM integration para análisis
- `cv_generator.py` - Generación de CV adaptados
- `loader.py` - Extracción de CV desde PDF
- `mail_agent.py` - Integración Gmail (opcional)
- `bot.py` - Notificaciones Telegram (opcional)

**Frontend (frontend/):**

- `src/features/` - Módulos por feature (auth, analysis, adaptations, etc.)
- `src/shared/components/` - Componentes reutilizables (Layout, Spinner, CardItem, etc.)
- `src/services/` - Clientes API
- `src/stores/` - Zustand global state management

---

## 🛠️ Stack Tecnológico

### Backend

| Tecnología                      | Propósito                      |
| ------------------------------- | ------------------------------ |
| **FastAPI**                     | Framework web moderno y rápido |
| **Uvicorn**                     | Servidor ASGI                  |
| **SQLAlchemy (asyncio)**        | ORM asincrónico                |
| **PostgreSQL / asyncpg**        | Base de datos escalable        |
| **Alembic**                     | Migraciones de BD              |
| **LangChain + langchain-openai**| Orquestación de LLM            |
| **DeepSeek v4-Flash**           | LLM para análisis y adaptación |
| **Cloudinary**                  | Almacenamiento de archivos     |
| **Firecrawl / Jina AI**         | Web scraping avanzado          |
| **slowapi**                     | Rate limiting                  |
| **PyPDF**                       | Procesamiento de PDF           |
| **pydantic-settings**           | Configuración con env vars     |
| **passlib / python-jose**       | Hashing y JWT                  |

### Frontend

| Tecnología          | Propósito              |
| ------------------- | ---------------------- |
| **React 18.3**      | UI interactiva         |
| **Vite 6.4**        | Build tool rápido      |
| **React Router v6** | Navegación SPA         |
| **Zustand 4.4**     | State management       |
| **React Query 5**   | Gestión de datos       |
| **React Hook Form** | Formularios            |
| **TailwindCSS 3.4** | Estilos                |
| **Axios 1.7**       | HTTP client            |
| **Zod 3.22**        | Validación             |
| **Lucide React**    | Iconos                 |

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

# === LLMS (elige uno) ===
DEEPSEEK_API_KEY=sk-xxxx
# O
GOOGLE_GEMINI_API_KEY=xxxx

# === CLOUDINARY (Almacenamiento) ===
CLOUDINARY_NAME=xxxx
CLOUDINARY_API_KEY=xxxx
CLOUDINARY_API_SECRET=xxxx

# === GMAIL (Opcional) ===
GOOGLE_CREDENTIALS_JSON={"installed":{...}}
GOOGLE_TOKEN_JSON={"token":"..."}

# === TELEGRAM (Opcional) ===
TELEGRAM_BOT_TOKEN=xxxx
TELEGRAM_CHAT_ID=xxxx

# === FIRECRAWL (Opcional) ===
FIRECRAWL_API_KEY=xxxx
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
VITE_API_URL=http://localhost:8000
```

---

## ⚙️ Configuración

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
npm run dev
```

App disponible en: **http://localhost:5173**

### Flujo de Uso Típico

1. **Acceder al dashboard** → http://localhost:5173
2. **Registrarse / Login** con email
3. **Subir CV** → PDF procesado automáticamente
4. **Analizar ofertas** → Ingresa URL de oferta
5. **Ver análisis** → Score, desglose, justificación
6. **Generar CV adaptado** → Descarga personalizado
7. **Ver historial** → Análisis y adaptaciones anteriores

---

## 📁 Estructura del Proyecto

```
Recopilador Ofertas Trabajo Validas/
│
├── main.py                           # FastAPI entry point
├── requirements.txt                  # Python dependencies
├── init_db.py                        # Database initialization
├── apply_migration.py                # Runner manual de migraciones
├── seed_user.py                      # Inicializa usuario admin con CV/avatar en Cloudinary
├── .env                              # Variables de entorno (no commitear)
│
├── alembic/                          # Database migrations
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
│       ├── 001_extend_auth_and_cv_adaptations.py  # auth_provider, cv_adaptations table
│       ├── 002_add_cv_data_to_users.py             # cv_data JSONB column
│       ├── 003_add_avatar_url_to_users.py          # avatar_url column
│       ├── 004_add_role_to_users.py                # role ENUM (admin/user)
│       └── 005_remove_scoring_details.py           # consolida datos en analysis_result
│
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py               # Login, register, oauth
│   │   │   ├── cv.py                 # CV upload, preview
│   │   │   ├── offers.py             # Analysis de ofertas
│   │   │   ├── adaptations.py        # CV adaptations
│   │   │   └── profile.py            # User profile
│   │   ├── services/
│   │   │   ├── analysis_service.py   # Lógica de análisis
│   │   │   ├── adaptation_service.py # Generación de CV
│   │   │   ├── cv_service.py         # Gestión de CV
│   │   │   └── auth_service.py       # Autenticación
│   │   ├── schemas.py                # Pydantic models
│   │   ├── dependencies.py           # DI
│   │   └── limiter.py                # Rate limiting
│   │
│   ├── database.py                   # SQLAlchemy config
│   ├── brain.py                      # LLM analysis
│   ├── cv_generator.py               # CV generation
│   ├── loader.py                     # PDF processing
│   ├── storage.py                    # Cloudinary integration
│   ├── token_manager.py              # Token management
│   │
│   ├── mail_agent.py                 # Gmail integration (opcional)
│   ├── bot.py                        # Telegram bot (opcional)
│   ├── scraper.py                    # Web scraping (opcional)
│   └── setup_auth.py                 # OAuth setup helper
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   │
│   ├── src/
│   │   ├── App.jsx                   # Main router
│   │   ├── main.jsx
│   │   │
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── pages/
│   │   │   │   │   ├── LoginPage.jsx
│   │   │   │   │   ├── RegisterPage.jsx
│   │   │   │   │   └── GoogleCallbackPage.jsx
│   │   │   │   └── components/
│   │   │   │       └── LoginForm.jsx
│   │   │   │
│   │   │   ├── analysis/
│   │   │   │   ├── pages/
│   │   │   │   │   ├── AnalysisPage.jsx
│   │   │   │   │   ├── ResultPage.jsx
│   │   │   │   │   └── HistoryPage.jsx
│   │   │   │   └── components/
│   │   │   │       ├── AnalysisForm.jsx
│   │   │   │       ├── ResultCard.jsx
│   │   │   │       └── AnalysisListItem.jsx
│   │   │   │
│   │   │   ├── adaptations/
│   │   │   │   ├── pages/
│   │   │   │   │   ├── AdaptationPage.jsx         # Generar adaptación (generate/:analysisId)
│   │   │   │   │   ├── AdaptationDetailPage.jsx   # Ver adaptación + descarga PDF
│   │   │   │   │   └── AdaptationsHistoryPage.jsx # Historial paginado de adaptaciones
│   │   │   │   └── components/
│   │   │   │       ├── AdaptationPreview.jsx      # Preview del CV adaptado
│   │   │   │       ├── CVPreviewHTML.jsx
│   │   │   │       └── PDFDownloadButton.jsx
│   │   │   │
│   │   │   ├── cv/
│   │   │   │   ├── pages/
│   │   │   │   │   └── CVPage.jsx
│   │   │   │   └── components/
│   │   │   │       ├── CVUpload.jsx
│   │   │   │       └── CVPreview.jsx
│   │   │   │
│   │   │   ├── profile/
│   │   │   │   └── pages/
│   │   │   │       └── ProfilePage.jsx
│   │   │   │
│   │   │   ├── landing/
│   │   │   │   └── pages/
│   │   │   │       └── LandingPage.jsx
│   │   │   │
│   │   │   └── dashboard/
│   │   │       └── pages/
│   │   │           └── DashboardPage.jsx
│   │   │
│   │   ├── shared/
│   │   │   ├── components/
│   │   │   │   ├── Layout.jsx
│   │   │   │   ├── Navbar.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── Spinner.jsx        # Loading universal (message, fullHeight, inline)
│   │   │   │   ├── CardItem.jsx       # Card genérico para listas de análisis/adaptaciones
│   │   │   │   ├── ProtectedRoute.jsx
│   │   │   │   └── CVRequiredRoute.jsx
│   │   │   └── hooks/
│   │   │       └── useAuth.js
│   │   │
│   │   ├── services/
│   │   │   ├── apiClient.js           # Axios instance
│   │   │   ├── authService.js
│   │   │   ├── analysisService.js
│   │   │   ├── adaptationService.js
│   │   │   ├── cvService.js
│   │   │   └── profileService.js
│   │   │
│   │   └── stores/
│   │       └── globalStore.js         # Zustand state
│
├── tests/
│   ├── test_plan_01_integration.py
│   ├── test_plan_02_apis.py
│   ├── test_plan_03_latex.py
│   ├── test_plan_04_api_fastapi.py
│   ├── test_plan_05_rate_limiter.py
│   └── test_concurrent_access.py
│
└── data/
    └── cv_usuario.pdf                # Tu CV (lugar donde se carga)
```

---

## 🚀 Despliegue

### Backend (Render / Railway / Similar)

1. Haz push a GitHub
2. Conecta el repositorio en la plataforma (Render, Railway, etc.)
3. Configura variables de entorno
4. Deploy automático desde main

### Frontend (Vercel)

```bash
# Vercel CLI
npm install -g vercel
vercel
```

O conecta tu GitHub a Vercel y hace deploy automático.

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

---

## 🎯 Bandas de Puntuación (Scoring)

El análisis devuelve un score 0-100 calculado en dos fases (ATS + evaluación humana):

| Rango   | Nivel       | Significado                                              |
| ------- | ----------- | -------------------------------------------------------- |
| 0 – 59  | ATS_BLOCK   | Rechazo automático — faltan requisitos indispensables    |
| 60 – 69 | Descarte    | Pasa el ATS pero débil en evaluación cualitativa         |
| 70 – 79 | Apto        | Match competente                                         |
| 80 – 89 | Fuerte      | Match sólido, candidato destacado                        |
| 90 – 100| Ideal       | Ajuste perfecto                                          |

`is_valid = (score >= 60)` — solo las ofertas válidas permiten generar una adaptación de CV.

---

## 📊 Flujo de Desarrollo

```
User Input → Frontend Form
    ↓
REST API → Backend Endpoint
    ↓
Service Layer → Business Logic
    ↓
LLM Analysis → Score & Details
    ↓
Database → Store Results
    ↓
REST API Response → Frontend Display
    ↓
UI Update → User sees results
```

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

Proyecto educativo para el ciclo IABD - CFGS

---

**⚡ ¡Happy Job Hunting! 🎯**
