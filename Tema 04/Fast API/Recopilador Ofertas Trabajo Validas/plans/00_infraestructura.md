# Plan 00: Infraestructura Base

## Objetivo
Preparar el entorno de despliegue en Hugging Face Spaces, configurar variables de entorno, y establecer la conexión con Neon (PostgreSQL) y Cloudinary antes de implementar cualquier módulo funcional.

## Prerrequisitos
- Cuenta en Hugging Face Spaces activa
- Cuenta en Neon (neon.tech) con proyecto creado
- Cuenta en Cloudinary con credenciales disponibles
- Cuenta en DeepSeek con API key
- Repositorio clonado localmente

---

## Paso 1 ✅: Migración Render → Hugging Face Spaces

### 1.1 Crear Space en HF
- Ir a huggingface.co → New Space
- SDK: **Docker**
- Visibilidad: Public o Private (según preferencia)
- Nombre sugerido: `opticv-engine`

### 1.2 Modificar puerto en `main.py`
```python
# Cambiar default de 10000 a 7860
PORT = int(os.environ.get("PORT", 7860))
```

### 1.3 Modificar `entrypoint.sh`
```bash
#!/bin/bash
# Inyectar secrets desde env vars
echo "$GOOGLE_CREDENTIALS_JSON" > credentials.json
echo "$GOOGLE_TOKEN_JSON" > token.json

# Crear .env desde variables de entorno
cat > .env << EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
JINA_API_KEY=${JINA_API_KEY}
FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
DATABASE_URL=${DATABASE_URL}
CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME}
CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY}
CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
EOF

uvicorn main:app --host 0.0.0.0 --port 7860
```

---

## Paso 2 ✅: Dockerfile con texlive-full

### 2.1 Modificar `Dockerfile`
```dockerfile
FROM python:3.9

# LaTeX engine (necesario para compilar CVs en PDF)
RUN apt-get update && apt-get install -y \
    texlive-full \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
```

> **Nota**: `texlive-full` ocupa ~5 GB. Build inicial lento pero imagen cacheada en HF.

### 2.2 Verificar localmente
```bash
docker build -t opticv-engine .
docker run -p 7860:7860 --env-file .env opticv-engine
curl http://localhost:7860/health
```

---

## Paso 3 ✅: Base de Datos Neon (PostgreSQL)

### 3.1 Crear tablas en Neon Console
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  master_cv_url TEXT,
  telegram_id VARCHAR(50)
);

CREATE TABLE job_offers (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  job_title VARCHAR(255),
  company VARCHAR(255),
  raw_text TEXT,
  offer_url TEXT,
  score INTEGER,
  optimized_cv_url TEXT,
  status VARCHAR(50) DEFAULT 'pending',  -- pending | processing | done | error
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Crear `src/database.py`
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import os
from datetime import datetime

DATABASE_URL = os.environ["DATABASE_URL"].replace(
    "postgresql://", "postgresql+asyncpg://"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    master_cv_url = Column(Text)
    telegram_id = Column(String(50))

class JobOffer(Base):
    __tablename__ = "job_offers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_title = Column(String(255))
    company = Column(String(255))
    raw_text = Column(Text)
    offer_url = Column(Text)
    score = Column(Integer)
    optimized_cv_url = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 3.3 Verificación
```bash
python -c "
import asyncio
from src.database import engine, Base

async def test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('OK - Conexión Neon establecida')

asyncio.run(test())
"
```

---

## Paso 4 ✅: Cloudinary SDK

### 4.1 Crear `src/storage.py`
```python
import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True
)

def upload_pdf(file_path: str, public_id: str) -> str:
    """Sube un PDF a Cloudinary y retorna su URL segura."""
    result = cloudinary.uploader.upload(
        file_path,
        public_id=public_id,
        resource_type="raw",
        overwrite=True
    )
    return result["secure_url"]

def upload_bytes(data: bytes, public_id: str) -> str:
    """Sube bytes directamente (útil para CV maestro desde form)."""
    result = cloudinary.uploader.upload(
        data,
        public_id=public_id,
        resource_type="raw",
        overwrite=True
    )
    return result["secure_url"]

def get_url(public_id: str) -> str:
    """Construye URL de un asset ya subido."""
    return cloudinary.CloudinaryImage(public_id).build_url(resource_type="raw")
```

### 4.2 Verificación
```bash
python -c "
from src.storage import upload_pdf
url = upload_pdf('data/cv_usuario.pdf', 'test/cv_maestro')
print('OK - URL:', url)
"
```

---

## Paso 5 ✅: Actualizar `requirements.txt`

```
# Existentes
fastapi
uvicorn[standard]
python-dotenv
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
requests
beautifulsoup4
PyMuPDF
python-telegram-bot
google-generativeai

# Nuevos
langchain
langchain-community
langchain-openai
sqlalchemy[asyncio]
asyncpg
cloudinary
python-multipart
aiofiles
```

---

## Paso 6 ✅: Variables de Entorno en HF Spaces

En Settings → Repository secrets, añadir:

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` (de Neon) |
| `CLOUDINARY_CLOUD_NAME` | Nombre del cloud Cloudinary |
| `CLOUDINARY_API_KEY` | API key Cloudinary |
| `CLOUDINARY_API_SECRET` | API secret Cloudinary |
| `DEEPSEEK_API_KEY` | API key DeepSeek |
| `GOOGLE_CREDENTIALS_JSON` | JSON completo de credenciales Gmail |
| `GOOGLE_TOKEN_JSON` | JSON del token OAuth Gmail |
| `TELEGRAM_BOT_TOKEN` | Token del bot Telegram |
| `TELEGRAM_CHAT_ID` | Chat ID Telegram |
| `JINA_API_KEY` | API key Jina |
| `FIRECRAWL_API_KEY` | API key FireCrawl |

---

## Paso 7 ✅: Keep-Alive con cron-job.org

- URL a monitorizar: `https://<user>-opticv-engine.hf.space/health`
- Intervalo: cada 5 minutos
- Método: GET
- Respuesta esperada: `200 OK`

---

## Verificación Final del Módulo ✅

```bash
# 1. Health endpoint responde
curl https://<user>-opticv-engine.hf.space/health

# 2. BD conectada
python -c "from src.database import engine; print('DB OK')"

# 3. Cloudinary conectado
python -c "from src.storage import upload_pdf; print('Storage OK')"

# 4. Docker build sin errores
docker build -t opticv-engine . && echo "Docker OK"
```

## Archivos Modificados/Creados

| Archivo | Acción |
|---------|--------|
| `Dockerfile` | Añadir `texlive-full` |
| `entrypoint.sh` | Añadir nuevas env vars |
| `requirements.txt` | Añadir nuevas dependencias |
| `src/database.py` | Crear - modelos SQLAlchemy + Neon |
| `src/storage.py` | Crear - wrapper Cloudinary |
| `main.py` | Cambiar puerto default a 7860 |
