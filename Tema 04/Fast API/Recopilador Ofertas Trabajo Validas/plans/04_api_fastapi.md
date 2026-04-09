# Plan 04: API FastAPI

## Objetivo
Evolucionar `main.py` añadiendo los endpoints reales para el dashboard y la generación de CVs, manteniendo la compatibilidad con el bot thread existente.

## Prerrequisitos
- Plan 00 completado (BD + Storage)
- Plan 02 y 03 completados (`engine.py` + `latex_compiler.py`)
- FastAPI ya instalado y funcionando

---

## Paso 1: Estructura de endpoints

```
GET  /                           → "OptiCV Engine running"
GET  /health                     → {"status": "ok"} (keep-alive Render/HF)
POST /api/generate/{job_offer_id}→ Dispara engine + LaTeX, retorna CV URL
GET  /api/offers                 → Lista ofertas paginada (para dashboard)
GET  /api/offers/{id}            → Detalle de una oferta
GET  /api/offers/{id}/cv         → Redirect a URL del PDF
POST /api/upload-master-cv       → Sube CV maestro a Cloudinary + actualiza user
```

---

## Paso 2: Modelos Pydantic de respuesta

```python
# Añadir a main.py o crear src/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OfferResponse(BaseModel):
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

class GenerateResponse(BaseModel):
    offer_id: int
    cv_url: str
    status: str = "done"

class UploadCVResponse(BaseModel):
    master_cv_url: str
    message: str
```

---

## Paso 3: Implementar endpoints en `main.py`

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

### 3.2 Endpoint `/api/generate/{job_offer_id}`

```python
@app.post("/api/generate/{job_offer_id}", response_model=GenerateResponse)
async def generate_optimized_cv(job_offer_id: int, db: AsyncSession = Depends(get_db)):
    """
    Genera CV optimizado para una oferta específica.
    Operación síncrona (espera resultado) - timeout recomendado: 5 min en cliente.
    """
    # Verificar que la oferta existe
    result = await db.execute(select(JobOffer).where(JobOffer.id == job_offer_id))
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(status_code=404, detail=f"Oferta {job_offer_id} no encontrada")
    
    if offer.status == "processing":
        raise HTTPException(status_code=409, detail="CV ya está siendo generado")
    
    if offer.status == "done" and offer.optimized_cv_url:
        # Ya generado, retornar directamente
        return GenerateResponse(offer_id=job_offer_id, cv_url=offer.optimized_cv_url)
    
    try:
        cv_url = await generate_cv(job_offer_id)
        return GenerateResponse(offer_id=job_offer_id, cv_url=cv_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3.3 Endpoint `/api/offers`

```python
@app.get("/api/offers", response_model=list[OfferResponse])
async def list_offers(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lista ofertas detectadas, ordenadas por fecha desc. Soporta filtro por status."""
    query = select(JobOffer).order_by(desc(JobOffer.created_at))
    
    if status:
        query = query.where(JobOffer.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

### 3.4 Endpoint `/api/offers/{id}`

```python
@app.get("/api/offers/{offer_id}", response_model=OfferResponse)
async def get_offer(offer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobOffer).where(JobOffer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return offer
```

### 3.5 Endpoint `/api/offers/{id}/cv`

```python
@app.get("/api/offers/{offer_id}/cv")
async def get_offer_cv(offer_id: int, db: AsyncSession = Depends(get_db)):
    """Redirige a la URL del PDF en Cloudinary."""
    result = await db.execute(select(JobOffer).where(JobOffer.id == offer_id))
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    if not offer.optimized_cv_url:
        raise HTTPException(status_code=404, detail="CV no generado aún para esta oferta")
    
    return RedirectResponse(url=offer.optimized_cv_url)
```

### 3.6 Endpoint `/api/upload-master-cv`

```python
@app.post("/api/upload-master-cv", response_model=UploadCVResponse)
async def upload_master_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Sube el CV maestro a Cloudinary y actualiza la URL en la BD del usuario."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    contents = await file.read()
    
    if len(contents) > 10 * 1024 * 1024:  # 10MB límite
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx 10MB)")
    
    cv_url = upload_bytes(contents, "cv/master")
    
    # Actualizar URL en BD del usuario único
    user_id = os.environ.get("USER_ID")
    if user_id:
        from sqlalchemy import update
        await db.execute(
            update(User).where(User.id == user_id).values(master_cv_url=cv_url)
        )
        await db.commit()
    
    return UploadCVResponse(
        master_cv_url=cv_url,
        message="CV maestro actualizado correctamente"
    )
```

---

## Paso 4: CORS para el dashboard

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

## Paso 5: Verificación de endpoints

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
| `main.py` | Añadir 5 endpoints + CORS + schemas Pydantic |
| `src/schemas.py` | Crear (opcional, mover schemas si main.py crece) |
