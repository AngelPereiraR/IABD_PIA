"""
Database configuration with SQLAlchemy async + Neon (PostgreSQL).
Modelos: User, JobOffer
"""
import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, select, Boolean, Enum as SQLEnum, create_engine
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship, Session
import enum
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

# Engine asincrono (para FastAPI - API requests)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=3,        # Reducido: solo para API requests
    max_overflow=5,     # Overflow limitado
    pool_pre_ping=True, # Verify connections before using
    pool_recycle=3600,  # Recycle connections every hour
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True
)

# Synchronous engine and session (for bot thread - separate pool)
sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
sync_engine = create_engine(
    sync_url,
    echo=False,
    future=True,
    pool_size=2,        # Muy pequeño: bot solo necesita 1-2 conexiones
    max_overflow=1,     # Overflow mínimo
    pool_pre_ping=True, # Verify connections before using
    pool_recycle=3600,  # Recycle connections every hour
)
SessionLocal = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
    future=True
)


# --- ENUMS ---
class AuthProvider(str, enum.Enum):
    GOOGLE = "google"
    EMAIL = "email"


class UserRole(str, enum.Enum):
    ADMIN = "admin"       # Usuario propietario del CV maestro local
    USER = "user"         # Usuarios regulares


# --- MODELOS ---
class Base(DeclarativeBase):
    """Base para todos los modelos ORM."""
    pass


class User(Base):
    """Usuario único del sistema con autenticación."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    auth_provider = Column(SQLEnum(AuthProvider), nullable=False, default=AuthProvider.EMAIL)
    password_hash = Column(String(255), nullable=True)  # NULL si OAuth
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)  # admin o user
    master_cv_url = Column(Text, nullable=True)  # URL Cloudinary del CV maestro
    cv_data = Column(JSONB, nullable=True)  # Datos estructurados del CV extraídos del PDF con DeepSeek
    avatar_url = Column(Text, nullable=True)  # URL Cloudinary de la foto de perfil
    telegram_id = Column(String(50), nullable=True)  # Solo para admin
    preferred_language = Column(String(5), default="es", nullable=False)  # User's language preference: 'es' or 'en'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job_offers = relationship("JobOffer", back_populates="user", cascade="all, delete-orphan")
    cv_adaptations = relationship("CVAdaptation", back_populates="user", cascade="all, delete-orphan")


class JobOffer(Base):
    """Oferta de trabajo analizada."""
    __tablename__ = "job_offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=True)  # Contenido HTML/markdown scrapeado
    offer_url = Column(Text, nullable=True)

    score = Column(Integer, nullable=True)  # 0-100 del análisis DeepSeek
    is_valid = Column(Boolean, default=None, nullable=True)  # TRUE if score >= 60
    analysis_result = Column(JSONB, nullable=True)  # Full RecruitmentDecision from DeepSeek: is_relevant, score, job_title, company, salary, posted_date, benefits, key_skills, rejection_reason, summary
    optimized_cv_url = Column(Text, nullable=True)  # URL Cloudinary del CV generado

    status = Column(
        String(50),
        default="pending",
        nullable=False
    )  # pending | processing | done | error

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="job_offers")
    cv_adaptations = relationship("CVAdaptation", back_populates="job_offer", cascade="all, delete-orphan")


class CVAdaptation(Base):
    """CV adaptado para una oferta específica."""
    __tablename__ = "cv_adaptations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_offer_id = Column(Integer, ForeignKey("job_offers.id", ondelete="CASCADE"), nullable=False, index=True)

    adapted_cv_html = Column(Text, nullable=True)  # HTML preview
    adapted_cv_url = Column(Text, nullable=True)  # Cloudinary PDF URL

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="cv_adaptations")
    job_offer = relationship("JobOffer", back_populates="cv_adaptations")


class TelegramNotification(Base):
    """Cola de notificaciones de Telegram para envío asíncrono."""
    __tablename__ = "telegram_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_offer_id = Column(Integer, ForeignKey("job_offers.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, sent, failed
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    job_offer = relationship("JobOffer")


# --- FUNCIONES DE UTILIDAD ---
def init_db_sync():
    """Crear todas las tablas de forma síncrona (para desarrollo en Windows)."""
    from sqlalchemy import create_engine

    # Usar engine síncrono para evitar problemas con ProactorEventLoop en Windows
    # Reemplazar asyncpg por psycopg2 (driver síncrono)
    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
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
