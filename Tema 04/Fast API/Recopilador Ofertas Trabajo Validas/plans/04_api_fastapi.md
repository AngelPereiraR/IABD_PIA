# Plan 04: API FastAPI

## Objetivo
Evolucionar `main.py` añadiendo los endpoints reales para el dashboard y la generación de CVs, manteniendo la compatibilidad con el bot thread existente.

## Prerrequisitos
- Plan 00 completado (BD + Storage)
- Plan 02 y 03 completados (`engine.py` + `latex_compiler.py`)
- FastAPI ya instalado y funcionando

---

## Paso 1 ✅: Estructura de endpoints

```
GET  /                           → "OptiCV Engine running"                ✅
GET  /health                     → {"status": "ok"} (keep-alive Render/HF) ✅
POST /api/generate/{job_offer_id}→ Dispara engine + LaTeX, retorna CV URL ✅
GET  /api/offers                 → Lista ofertas paginada (para dashboard) ✅
GET  /api/offers/{id}            → Detalle de una oferta                   ⏳ PENDIENTE
GET  /api/offers/{id}/cv         → Redirect a URL del PDF                  ⏳ PENDIENTE
POST /api/upload-master-cv       → Sube CV maestro a Cloudinary + actualiza user ✅
```

---

## Paso 2 ✅: Modelos Pydantic de respuesta

Ubicación: `src/api/schemas.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OfferDetail(BaseModel):
    id: int
    job_title: Optional[str]
    company: Optional[str]
    score: Optional[int]
    status: str
    offer_url: Optional[str]
    optimized_cv_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CVGenerationResponse(BaseModel):
    cv_url: str
    status: str = "done"

class CVUploadResponse(BaseModel):
    cv_url: str
    status: str
```

---

## Paso 3 ✅: Implementar endpoints en `main.py` + `src/api/routes/`

### 3.1 Imports adicionales

```python
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from src.database import get_db, JobOffer, User
from src.engine import generate_cv
from src.storage import upload_bytes
import io
```

### 3.2 Endpoint `/api/generate/{job_offer_id}` — `src/api/routes/cv.py` ✅

```python
@router.post("/generate/{offer_id}", response_model=CVGenerationResponse)
async def generate_optimized_cv(offer_id: int):
    """
    Genera CV optimizado para una oferta específica.
    Llama a CVGenerator.generate_for_offer(offer_id).
    Operación síncrona (espera resultado) - timeout recomendado: 5 min en cliente.
    """
    if offer.status == "processing":
        raise HTTPException(status_code=409, detail="CV ya está siendo generado")
    if offer.status == "done" and offer.optimized_cv_url:
        return CVGenerationResponse(cv_url=offer.optimized_cv_url)
    cv_url = await CVGenerator.generate_for_offer(offer_id)
    return CVGenerationResponse(cv_url=cv_url)
```

### 3.3 Endpoint `/api/offers` — `src/api/routes/offers.py` ✅

```python
@router.get("/offers", response_model=list[OfferDetail])
async def list_offers(skip: int = 0, limit: int = 20, user_id: str = Depends(get_user_id)):
    """Lista ofertas del usuario ordenadas por fecha desc, con paginación."""
```

### 3.4 Endpoint `/api/offers/{id}` — ⏳ PENDIENTE

Ver sección **## Pendiente** al final de este plan.

### 3.5 Endpoint `/api/offers/{id}/cv` — ⏳ PENDIENTE

Ver sección **## Pendiente** al final de este plan.

### 3.6 Endpoint `/api/upload-master-cv` — `src/api/routes/cv.py` ✅

```python
@router.post("/upload-master-cv", response_model=CVUploadResponse)
async def upload_master_cv(file: UploadFile = File(...)):
    """Sube CV maestro a Cloudinary. Solo acepta PDF, máx 10MB."""
    # upload_bytes(contents, "cv/master") → cv_url
    # Actualiza user.master_cv_url en BD
```

---

## Paso 4 ✅: CORS para el dashboard

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",          # Vite dev
        "https://opticv.vercel.app",      # Producción Vercel
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Paso 5 ✅: Verificación de endpoints implementados

```bash
# Servidor levantado
uvicorn main:app --reload --port 7860

# Health check
curl http://localhost:7860/health

# Listar ofertas
curl http://localhost:7860/api/offers | python -m json.tool

# Generar CV (reemplazar 1 con ID real)
curl -X POST http://localhost:7860/api/generate/1

# Subir CV maestro
curl -X POST http://localhost:7860/api/upload-master-cv \
  -F "file=@data/cv_usuario.pdf"

# Swagger UI (documentación automática)
# Abrir: http://localhost:7860/docs
```

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `main.py` | Registrar routers + CORS middleware |
| `src/api/schemas.py` | `OfferDetail`, `CVGenerationResponse`, `CVUploadResponse` |
| `src/api/routes/offers.py` | `GET /api/offers` ✅ |
| `src/api/routes/cv.py` | `POST /api/generate/{id}` ✅, `POST /api/upload-master-cv` ✅ |
| `src/api/dependencies.py` | `get_user_id()`, `get_async_session()` |

---

## Pendiente

Los siguientes endpoints están especificados en el plan pero aún no implementados:

### GET `/api/offers/{offer_id}`
Implementar en `src/api/routes/offers.py`:
- Retorna detalle completo de una oferta por ID
- Response model: `OfferDetail`
- 404 si la oferta no existe

### GET `/api/offers/{offer_id}/cv`
Implementar en `src/api/routes/offers.py`:
- Redirige (`RedirectResponse`) a `offer.optimized_cv_url`
- 404 si la oferta no existe
- 404 si `optimized_cv_url` es null (CV aún no generado)
