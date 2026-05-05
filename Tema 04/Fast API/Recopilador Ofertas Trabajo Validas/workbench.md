# **🛠️ Workbench: OptiCV - Recopilador Inteligente de Ofertas de Trabajo**

Versión: 2.0.0  
Estado: ✅ **PRODUCCIÓN - Completamente Funcional**  
Objetivo: Sistema integral que monitorea correos de empleo, analiza ofertas contra CV del usuario usando IA, y proporciona adaptaciones personalizadas de CV.

---

## **1. Arquitectura del Sistema**

OptiCV es un **sistema distribuido de 3 servicios** que trabajan juntos:

```
┌─────────────────────────────────────────────────────┐
│                   ARQUITECTURA GENERAL               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Frontend (Vercel)  ←→  Backend (HF Spaces)         │
│  React + Vite           FastAPI + Uvicorn           │
│  vercel.app             hf.space                     │
│                              ↓                       │
│                       Análisis Ofertas               │
│                       (DeepSeek LLM)                 │
│                              ↓                       │
│                    PostgreSQL (Neon)                 │
│                    (cola de mensajes)                │
│                              ↓                       │
│              Render Worker (Telegram)                │
│              Procesa notificaciones                  │
│                        cada 30s                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### **Pipeline de Datos**

1. **Input:** Email de LinkedIn/InfoJobs → URL de oferta
2. **Extracción:** Scraping web (Jina AI → FireCrawl → HTTP directo)
3. **Análisis:** DeepSeek LLM (doble fase: ATS + RRHH)
4. **Scoring:** 0-100 con 5 bandas (0-59, 60-69, 70-79, 80-89, 90-100)
5. **Persistencia:** Resultado guardado en BD
6. **Notificación:** Worker en Render envía a Telegram (si score ≥ 70)

---

## **2. Stack Tecnológico**

| Componente | Tecnología | Propósito |
|:-----------|:-----------|:----------|
| **Backend** | FastAPI + Uvicorn | API REST, análisis sincrónico |
| **Frontend** | React 18 + Vite 6 | UI interactiva, dashboard |
| **Base de datos** | PostgreSQL + asyncpg | Persistencia, cola de mensajes |
| **LLM** | DeepSeek v4-Flash (LangChain) | Análisis de ofertas, adaptación de CV |
| **Scraping** | Jina AI + FireCrawl + requests | Extracción de contenido web |
| **Storage** | Cloudinary | Almacenamiento de PDFs (CV adaptados) |
| **Notificaciones** | Telegram Bot API | Alertas en tiempo real |
| **Auth** | JWT + bcrypt | Autenticación segura |
| **Worker** | FastAPI (Render) | Procesa cola de Telegram |
| **Deploy** | Docker + GitHub Actions | HF Spaces (backend), Vercel (frontend), Render (worker) |

---

## **3. Servicios Principales**

### **3.1 Backend (HF Spaces)**

**Propósito:** Procesar análisis de ofertas, gestionar autenticación, servir API

**Endpoints principales:**
- `POST /api/analysis` - Analizar oferta por URL o texto
- `GET /api/analysis/history` - Historial de análisis
- `POST /api/adaptations/generate/{analysis_id}` - Generar CV adaptado
- `GET /health` - Health check

**Características:**
- ✅ Scoring en 5 bandas (0-59, 60-69, 70-79, 80-89, 90-100)
- ✅ Solo ofertas con score ≥ 60 pueden generar adaptación
- ✅ Rate limiting con slowapi
- ✅ Autenticación JWT

### **3.2 Telegram Worker (Render)**

**Propósito:** Procesar cola de notificaciones independientemente del backend

**Comportamiento:**
- Lee BD cada 30 segundos
- Si hay mensajes pendientes: intenta enviar a Telegram
- Si falla: reintenta con exponential backoff
- Marca como enviado o error

**¿Por qué separado?**
- HF Spaces tiene restricciones de red que bloquean conexiones persistentes
- Telegram API requiere timeouts largos
- Desacoplamiento → mayor confiabilidad y reintentos automáticos

### **3.3 Frontend (Vercel)**

**Propósito:** Dashboard web para análisis, gestión de CV, historial

**Características:**
- ✅ Análisis en tiempo real
- ✅ Generación de CV adaptados en LaTeX/PDF
- ✅ Historial paginado
- ✅ Responsive design

---

## **4. Lógica Detallada del Análisis**

### **Fase 1: ATS (Applicant Tracking System)**

Filtra por keywords técnicas y requisitos básicos:
- ¿Tiene los skills requeridos?
- ¿Coincide el nivel de experiencia?
- ¿Está en el rango salarial?

**Output:** Score 0-59 (RECHAZADO) o continúa a Fase 2

### **Fase 2: Evaluación Humana (RRHH)**

Evaluación semántica profunda:
- ¿Encaja la cultura empresarial?
- ¿Son los soft skills compatibles?
- ¿Hay crecimiento profesional?

**Output:** Score final 60-100

### **Bandas de Scoring Finales**

| Rango | Nivel | Icono | Acción |
|-------|-------|-------|--------|
| 0-59 | ATS_BLOCK | ⛔ | Descartar |
| 60-69 | Descarte | ⚠️ | No notificar |
| 70-79 | Apto | ✅ | ← Notificar |
| 80-89 | Fuerte | 🚀 | ← Notificar |
| 90-100 | Ideal | 🔥 | ← Notificar |

**Validez:** `is_valid = (score >= 60)` — solo estas pueden generar CV adaptado

---

## **5. Scraping en Cascada**

**Intento 1: Jina AI**
- Rápido, gratuito
- URL: `https://r.jina.ai/{url}`
- Timeout: 15s

**Intento 2: FireCrawl**
- Renderiza JavaScript
- Maneja HTML complejo
- Timeout: 30s

**Intento 3: HTTP Directo**
- Requests + BeautifulSoup
- Retry con exponential backoff
- Último recurso

**Ventaja:** Si un servicio cae, los otros compensan

---

## **6. CV Adaptado (LaTeX + Cloudinary)**

**Flujo:**
1. Usuario selecciona oferta (score ≥ 60)
2. Backend adapta CV con DeepSeek (10-20s)
3. Genera template LaTeX personalizado (5s)
4. Compila LaTeX → PDF (20-40s)
5. Sube a Cloudinary (<5s)
6. Frontend descarga desde Cloudinary

**⏱️ Tiempo Total:** 30-60 segundos por generación

**Características:**
- ✅ Adaptación automática de secciones según oferta
- ✅ Sin inventar datos (grounding del prompt)
- ✅ PDF compilado y descargable
- ✅ Almacenado en Cloudinary para acceso rápido

---

## **7. Anti-Alucinación (Grounding)**

El prompt de DeepSeek incluye instrucciones explícitas:

```
⚠️ INSTRUCCIONES DE GROUNDING:
1. Tu análisis debe basarse ÚNICA Y EXCLUSIVAMENTE en el contenido de "TEXTO DE LA WEB"
2. PROHIBIDO usar conocimiento externo o suposiciones
3. Debes extraer la fecha de publicación REAL del texto
```

Esto reduce alucinaciones en:
- Salarios no especificados
- Fechas inventadas
- Beneficios no mencionados

---

## **8. Configuración del Entorno**

### **Variables de Entorno (.env)**

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# JWT
SECRET_KEY=tu_secret_key_super_segura

# DeepSeek LLM
DEEPSEEK_API_KEY=sk-xxxx

# Cloudinary (PDF)
CLOUDINARY_NAME=xxxx
CLOUDINARY_API_KEY=xxxx
CLOUDINARY_API_SECRET=xxxx

# Gmail (Opcional)
GOOGLE_CREDENTIALS_JSON={...}
GOOGLE_TOKEN_JSON={...}

# Telegram
TELEGRAM_BOT_TOKEN=xxxx
TELEGRAM_CHAT_ID=xxxx

# Scraping
JINA_API_KEY=jina_xxxx
FIRECRAWL_API_KEY=fcrawl_xxxx

# Server
PORT=7860
```

---

## **9. Despliegue**

### **Backend → Hugging Face Spaces**

```bash
git push origin main
↓
GitHub Actions ejecuta .github/workflows/deploy-to-hf.yml
↓
Pushea a HF Space
↓
HF Spaces build Dockerfile automático
↓
https://opticv-engine.hf.space
```

### **Worker → Render**

```bash
git push origin main
↓
Render detecta cambios automáticamente
↓
Build Dockerfile.worker
↓
Proceso corre independientemente
```

### **Frontend → Vercel**

```bash
git push origin main
↓
Vercel detecta cambios automáticamente
↓
Build con npm run build
↓
https://opticv-frontend.vercel.app
```

---

## **10. Notas Técnicas Importantes**

### **Por qué FastAPI + Uvicorn (no Flask)**

- ✅ Async nativo → mejor performance
- ✅ Automatic docs (Swagger)
- ✅ Validación automática (Pydantic)
- ✅ Rate limiting integrado
- ✅ Mejor para APIs modernas

### **Por qué Worker Separado en Render**

**Problema con HF Spaces:**
- Restricciones de red para conexiones persistentes
- Telegram API requiere timeouts largos
- Conexiones pueden ser bloqueadas/interrumpidas

**Solución:**
- Backend guarda mensajes en BD
- Render Worker los procesa independientemente
- Reintentos automáticos sin afectar análisis

### **Scoring en 5 Bandas (no 2)**

Permite usuario distinguir entre:
- Oferta completamente fuera de rango (0-59)
- Oferta válida pero débil (60-69)
- Oferta buena (70-79)
- Oferta excelente (80-89)
- Oferta perfecta (90-100)

---

## **11. Métricas de Rendimiento**

### **Tiempo de Análisis de Oferta**
- Scraping: 2-8s (depende de estrategia exitosa)
- DeepSeek LLM: 10-15s (doble fase ATS + RRHH)
- Notificación Telegram: <1s
- **⏱️ Total análisis:** 12-25s

### **Tiempo de Generación de CV Adaptado**
- Adaptación con DeepSeek: 10-20s
- Compilación LaTeX → PDF: 20-40s
- Upload a Cloudinary: <5s
- **⏱️ Total generación:** 30-60s

### **Recursos del Sistema**
- RAM: ~150-200 MB
- CPU: Mínimo (mayoría del tiempo en sleep)
- BD: ~5MB por 1000 análisis

### **Rate Limits**

**DeepSeek API:**
- Límites de concurrencia **dinámicos** (basados en carga del servidor)
- HTTP 429: Respuesta inmediata cuando se alcanza el límite de concurrencia
- Timeout: Cierra conexión si no comienza inferencia después de 10 minutos
- Ver: [DeepSeek Rate Limit Docs](https://api-docs.deepseek.com/quick_start/rate_limit)

**LaTeX Compiler:**
- Tiempo variable según complejidad del CV

---

## **12. Mejoras Futuras**

- [ ] Soporte para más plataformas (Indeed, Glassdoor, etc.)
- [ ] Dashboard de estadísticas (salary trends, demand by skill)
- [ ] Integración Notion/Trello para gestionar candidaturas
- [ ] Generación automática de cover letters
- [ ] Sistema de feedback (usuario indica si match fue correcto)
- [ ] Export a CSV/JSON

---

⚡ **Sistema completamente funcional en producción.**
