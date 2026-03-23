# Plan: OptiCV Engine

## Contexto

El proyecto actual ("Recopilador Inteligente de Ofertas de Trabajo") es un bot funcional que
monitoriza Gmail, analiza ofertas con Gemini y notifica por Telegram. Este plan describe su
evolución hacia **OptiCV Engine**: una plataforma completa que añade generación automática
de CVs optimizados en PDF (vía LaTeX), base de datos persistente, almacenamiento en
Cloudinary y un dashboard web.

El cambio está motivado por la necesidad de:
- Persistir el historial de ofertas y CVs generados
- Automatizar la adaptación del CV a cada oferta con IA
- Ofrecer una interfaz web al usuario

---

## Stack Tecnológico

| Capa | Tecnología | Plataforma |
|------|-----------|------------|
| Frontend | React + Vite | Vercel |
| Backend / API | FastAPI (Python) | Hugging Face Spaces |
| IA / Agentes | LangChain + DeepSeek | HF (Cómputo) |
| Base de Datos | PostgreSQL | Neon (serverless) |
| Almacenamiento | Cloudinary SDK | Cloudinary |
| Worker/Bot | Python Async | HF (Background thread) |
| Keep-Alive | HTTP Pings | Cron-job.org (cada 5 min) |

---

## Módulos a Implementar

### A. Módulo de Vigilancia (Worker/Bot)

Evolución del bot actual (`src/mail_agent.py`, `src/bot.py`).

- **Gmail OAuth2**: mantener integración existente en `src/mail_agent.py`
- **Filtrado inteligente**: reemplazar `src/brain.py` (Gemini) por agente LangChain + DeepSeek que pre-analiza el cuerpo del correo para descartar ofertas no relevantes
- **Persistencia**: al detectar una oferta válida, guardar registro en tabla `job_offers` de Neon (en lugar de solo notificar)
- **Telegram**: mantener `src/bot.py`, añadir botón inline "Generar CV Optimizado" que dispara el Engine vía API

### B. Módulo de Procesamiento e IA (Engine)

Nuevo módulo `src/engine.py`.

- **Análisis de JD**: extracción de keywords y habilidades requeridas de la oferta (LangChain + DeepSeek)
- **Adaptación de perfil**: descargar CV Maestro desde Cloudinary, reescribir secciones "Experiencia" y "Habilidades" para alinearlas con la oferta
- **Generador LaTeX**: producir archivo `.tex` dinámico con datos actualizados, listo para compilar

### C. Motor de Compilación LaTeX

Nuevo módulo `src/latex_compiler.py`.

- **Docker en HF**: imagen con `texlive-full` preinstalado (ver Dockerfile abajo)
- **Compilación**: ejecutar `pdflatex` sobre el `.tex` generado; los 16 GB RAM de HF garantizan ausencia de OOM
- **Subida a Cloudinary**: PDF resultante se sube y su URL se registra en Neon (`job_offers.optimized_cv_url`)

### D. API FastAPI

Evolución de `main.py`, añadiendo endpoints reales.

```
GET  /health                         → keep-alive
POST /api/generate/{job_offer_id}    → dispara Engine + compilación LaTeX
GET  /api/offers                     → historial de ofertas (para dashboard)
GET  /api/offers/{id}/cv             → URL del PDF generado
POST /api/upload-master-cv           → sube CV Maestro a Cloudinary
```

### E. Panel de Control (Dashboard)

Nuevo proyecto React + Vite, desplegado en Vercel.

- **Gestión de CV Maestro**: formulario para subir el CV base (llama a `POST /api/upload-master-cv`)
- **Historial**: tabla con ofertas detectadas, estado del procesamiento y botón de descarga del PDF
- **Configuración**: ajuste de filtros de búsqueda Gmail y credenciales Telegram

---

## Modelo de Datos (Neon/PostgreSQL)

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  master_cv_url TEXT,        -- Link a Cloudinary
  telegram_id VARCHAR(50)
);

CREATE TABLE job_offers (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  job_title VARCHAR(255),
  company VARCHAR(255),
  raw_text TEXT,
  optimized_cv_url TEXT,     -- Link al PDF generado en Cloudinary
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Flujo Operativo

```
1. Reposo    → Cron-job.org hace ping a /health cada 5 min (HF no se suspende)
2. Email     → Worker detecta correo → LangChain filtra → guarda en job_offers (Neon)
3. Telegram  → Bot notifica al usuario + botón "Generar CV"
4. Generación:
   a. FastAPI recibe POST /api/generate/{id}
   b. Descarga CV Maestro de Cloudinary
   c. DeepSeek analiza JD y adapta el CV
   d. Engine genera .tex → pdflatex compila PDF
   e. PDF se sube a Cloudinary → URL se guarda en Neon
5. Final     → Bot envía al usuario el enlace al PDF optimizado
```

---

## Cambios en Infraestructura

### Migración Render → Hugging Face Spaces

- **Motivación**: HF Spaces soporta hasta 16 GB RAM (necesario para `texlive-full`)
- **Puerto**: uvicorn en `0.0.0.0:7860` (puerto requerido por HF)

### Dockerfile HF

```dockerfile
FROM python:3.9

# LaTeX engine
RUN apt-get update && apt-get install -y \
    texlive-full \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

---

## Archivos Críticos a Crear/Modificar

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `main.py` | Modificar | Añadir endpoints API |
| `src/brain.py` | Modificar | Reemplazar Gemini por LangChain + DeepSeek |
| `src/bot.py` | Modificar | Añadir botón inline "Generar CV" |
| `src/mail_agent.py` | Modificar | Persistir ofertas en Neon |
| `src/engine.py` | Crear | Análisis JD + adaptación de perfil |
| `src/latex_compiler.py` | Crear | Generación .tex + compilación + upload |
| `src/database.py` | Crear | Conexión Neon + modelos SQLAlchemy |
| `src/storage.py` | Crear | Wrapper Cloudinary SDK |
| `Dockerfile` | Modificar | Añadir `texlive-full` |
| `requirements.txt` | Modificar | Añadir nuevas dependencias |
| `frontend/` | Crear | Proyecto React + Vite |

---

## Variables de Entorno Necesarias (nuevas)

```env
# Neon PostgreSQL
DATABASE_URL=postgresql://...

# Cloudinary
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# DeepSeek
DEEPSEEK_API_KEY=...
```

---

## Dependencias Python Nuevas

```
langchain
langchain-community
langchain-openai          # compatible con DeepSeek via OpenAI SDK
sqlalchemy
asyncpg
cloudinary
python-multipart
```

---

## Verificación por Módulo

| Módulo | Cómo verificar |
|--------|---------------|
| BD Neon | `python -c "from src.database import engine; print('OK')"` |
| Cloudinary | Subir un PDF de prueba y verificar URL generada |
| LaTeX Engine | Compilar una plantilla `.tex` básica y comprobar PDF |
| FastAPI endpoints | Probar con `curl` o Swagger UI (`/docs`) |
| Worker/Bot | Simular email con oferta y verificar notificación Telegram |
| Frontend | `npm run dev` y verificar dashboard en localhost |
