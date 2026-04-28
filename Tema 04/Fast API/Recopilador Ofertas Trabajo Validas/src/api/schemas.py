from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

class OfferDetail(BaseModel):
    """Modelo de respuesta para ofertas listadas"""
    id: int
    job_title: Optional[str] = None
    company: Optional[str] = None
    score: Optional[int] = None
    status: str
    offer_url: Optional[str] = None
    optimized_cv_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CVUploadResponse(BaseModel):
    """Modelo de respuesta para upload de CV"""
    cv_url: str
    user_id: UUID
    status: str = "success"


class CVCurrentResponse(BaseModel):
    """Modelo de respuesta para CV actual del usuario"""
    cv_url: Optional[str] = None
    user_id: UUID


class CVGenerationResponse(BaseModel):
    """Modelo de respuesta para generación de CV optimizado"""
    cv_url: str
    status: str


# --- Auth Schemas ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    auth_provider: str = "email"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    auth_provider: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Analysis Schemas ---
class AnalysisCreate(BaseModel):
    offer_text: Optional[str] = None
    offer_url: Optional[str] = None


class AnalysisResponse(BaseModel):
    id: int
    score: Optional[int] = None
    is_valid: Optional[bool] = None
    title: Optional[str] = None
    company: Optional[str] = None
    offer_url: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    benefits: Optional[str] = None
    key_skills: Optional[list[str]] = None
    summary: Optional[str] = None
    created_at: Optional[datetime] = None


class AnalysisListItem(BaseModel):
    id: int
    score: Optional[int] = None
    is_valid: Optional[bool] = None
    title: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime


class AnalysisListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AnalysisListItem]


# --- Adaptation Schemas ---
class AdaptationCreate(BaseModel):
    analysis_id: int


class AdaptationResponse(BaseModel):
    id: UUID
    adapted_cv_html: Optional[str] = None
    adapted_cv_url: Optional[str] = None
    created_at: datetime
    analysis_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    score: Optional[int] = None


class AdaptationListItem(BaseModel):
    id: UUID
    created_at: datetime
    job_offer_id: int
    adapted_cv_url: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    score: Optional[int] = None


class AdaptationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AdaptationListItem]


# --- Profile Schemas ---
class ProfileFormacion(BaseModel):
    titulo: Optional[str] = None
    centro: Optional[str] = None
    anio: Optional[str] = None


class ProfileExperiencia(BaseModel):
    puesto: Optional[str] = None
    empresa: Optional[str] = None
    duracion: Optional[str] = None
    logros: list[str] = []
    impacto: Optional[str] = None


class ProfileProyecto(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tecnologias: list[str] = []


class ProfileIdioma(BaseModel):
    idioma: Optional[str] = None
    nivel: Optional[str] = None


class ProfileCertificacion(BaseModel):
    nombre: Optional[str] = None
    emisor: Optional[str] = None
    anio: Optional[str] = None


class ProfileCurso(BaseModel):
    nombre: Optional[str] = None
    plataforma: Optional[str] = None
    anio: Optional[str] = None


class ProfileVoluntariado(BaseModel):
    organizacion: Optional[str] = None
    rol: Optional[str] = None
    descripcion: Optional[str] = None
    anio: Optional[str] = None


class ProfileCVData(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    telefono: Optional[str] = None
    ubicacion: Optional[str] = None
    web: Optional[str] = None
    resumen_base: Optional[str] = None
    formacion: list[ProfileFormacion] = []
    experiencia_base: list[ProfileExperiencia] = []
    proyectos: list[ProfileProyecto] = []
    habilidades_base: dict[str, list[str]] = {}
    idiomas: list[ProfileIdioma] = []
    certificaciones: list[ProfileCertificacion] = []
    cursos: list[ProfileCurso] = []
    voluntariado: list[ProfileVoluntariado] = []


class ProfileResponse(BaseModel):
    email: str
    telegram_id: Optional[str] = None
    master_cv_url: Optional[str] = None
    avatar_url: Optional[str] = None
    cv_data: Optional[ProfileCVData] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    cv_data: Optional[ProfileCVData] = None
    telegram_id: Optional[str] = None


class AvatarUploadResponse(BaseModel):
    avatar_url: str
    status: str = "success"
