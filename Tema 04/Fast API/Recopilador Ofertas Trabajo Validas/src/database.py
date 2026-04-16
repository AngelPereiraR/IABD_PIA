"""
Database configuration with SQLAlchemy async + Neon (PostgreSQL).
Modelos: User, JobOffer
"""
import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno desde .env

# --- CONFIGURACION ---
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/opticv")

# Convertir postgresql:// a postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Remove query parameters that asyncpg doesn't support
# asyncpg handles SSL automatically for secure connections
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

# Engine asincrono
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Cambia a True para debug SQL
    future=True
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True
)


# --- MODELOS ---
class Base(DeclarativeBase):
    """Base para todos los modelos ORM."""
    pass


class User(Base):
    """Usuario único del sistema."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    master_cv_url = Column(Text, nullable=True)  # URL Cloudinary del CV maestro
    telegram_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobOffer(Base):
    """Oferta de trabajo detectada."""
    __tablename__ = "job_offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=True)  # Contenido HTML/markdown scrapeado
    offer_url = Column(Text, nullable=True)

    score = Column(Integer, nullable=True)  # 0-100 del análisis DeepSeek
    optimized_cv_url = Column(Text, nullable=True)  # URL Cloudinary del CV generado

    status = Column(
        String(50),
        default="pending",
        nullable=False
    )  # pending | processing | done | error

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- FUNCIONES DE UTILIDAD ---
def init_db_sync():
    """Crear todas las tablas de forma síncrona (para desarrollo en Windows)."""
    from sqlalchemy import create_engine

    # Usar engine síncrono para evitar problemas con ProactorEventLoop en Windows
    sync_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    sync_engine = create_engine(sync_url, echo=False)

    try:
        with sync_engine.begin() as conn:
            Base.metadata.create_all(conn)
        print("[DB] ✅ Tablas inicializadas correctamente.")
    finally:
        sync_engine.dispose()


async def init_db():
    """Crear todas las tablas (versión async para FastAPI)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] ✅ Tablas inicializadas correctamente.")


async def get_db():
    """Dependency injection para FastAPI."""
    async with AsyncSessionLocal() as session:
        yield session
