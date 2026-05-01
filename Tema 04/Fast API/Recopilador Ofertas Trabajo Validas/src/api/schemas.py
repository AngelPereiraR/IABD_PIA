from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class OfferDetail(BaseModel):
    """Job offer details in list and detail responses"""
    id: int = Field(..., description="Unique offer identifier (primary key)")
    job_title: Optional[str] = Field(
        None,
        description="Job position title (e.g., Senior Python Developer, Product Manager)"
    )
    company: Optional[str] = Field(
        None,
        description="Hiring company name"
    )
    score: Optional[int] = Field(
        None,
        description="AI compatibility score (0-100, where 100 is perfect match)"
    )
    status: str = Field(
        ...,
        description="Current status: 'pending' (new), 'viewed' (reviewed), 'applied' (submitted), or 'archived' (hidden)"
    )
    offer_url: Optional[str] = Field(
        None,
        description="Direct URL to original job posting on LinkedIn, InfoJobs, or other platform"
    )
    optimized_cv_url: Optional[str] = Field(
        None,
        description="Download URL for CV optimized specifically for this job offer"
    )
    created_at: datetime = Field(
        ...,
        description="When the offer was captured/analyzed (UTC timestamp)"
    )

    class Config:
        from_attributes = True
        example = {
            "id": 42,
            "job_title": "Senior Python Developer",
            "company": "TechCorp Inc",
            "score": 87,
            "status": "pending",
            "offer_url": "https://linkedin.com/jobs/view/123456789",
            "optimized_cv_url": "https://storage.example.com/cv_offer_42_optimized.pdf",
            "created_at": "2026-05-01T10:00:00Z"
        }


class CVUploadResponse(BaseModel):
    """Response after uploading a CV file"""
    cv_url: str = Field(
        ...,
        description="Public URL where the uploaded CV is stored"
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user who uploaded the CV"
    )
    status: str = Field(
        default="success",
        description="Upload status: 'success' or 'error'"
    )

    class Config:
        example = {
            "cv_url": "https://storage.example.com/cv_user_uuid.pdf",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "success"
        }


class CVCurrentResponse(BaseModel):
    """Response with current CV information"""
    cv_url: Optional[str] = Field(
        None,
        description="Public URL to the user's current CV (null if not uploaded)"
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user"
    )

    class Config:
        example = {
            "cv_url": "https://storage.example.com/cv_user_uuid.pdf",
            "user_id": "550e8400-e29b-41d4-a716-446655440000"
        }


class CVGenerationResponse(BaseModel):
    """Response after generating an optimized CV for a specific offer"""
    cv_url: str = Field(
        ...,
        description="Download URL for the generated CV optimized for the target job offer"
    )
    status: str = Field(
        default="success",
        description="Generation status: 'success' or 'error'"
    )

    class Config:
        example = {
            "cv_url": "https://storage.example.com/cv_offer_42_optimized.pdf",
            "status": "success"
        }


# --- Auth Schemas ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    auth_provider: str = "email"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing authentication token after login/register"""
    access_token: str = Field(
        ...,
        description="JWT bearer token for authenticating subsequent requests"
    )
    token_type: str = Field(
        default="bearer",
        description="Type of token (always 'bearer')"
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the authenticated user"
    )
    email: str = Field(
        ...,
        description="Email address of the authenticated user"
    )

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com"
        }


class UserResponse(BaseModel):
    """Current authenticated user information"""
    id: UUID = Field(..., description="Unique user identifier (UUID)")
    email: str = Field(..., description="User email address")
    auth_provider: str = Field(..., description="Authentication method used (email, google, etc)")
    created_at: datetime = Field(..., description="Account creation date (UTC)")

    class Config:
        from_attributes = True
        example = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "auth_provider": "email",
            "created_at": "2026-01-15T08:30:00Z"
        }


# --- Analysis Schemas ---
class AnalysisCreate(BaseModel):
    offer_text: Optional[str] = None
    offer_url: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Complete analysis result for a job offer"""
    id: int = Field(..., description="Analysis ID")
    score: Optional[int] = Field(None, description="AI compatibility score (0-100)")
    is_valid: Optional[bool] = Field(None, description="Whether offer meets minimum criteria")
    title: Optional[str] = Field(None, description="Job title extracted from offer")
    company: Optional[str] = Field(None, description="Company name extracted from offer")
    offer_url: Optional[str] = Field(None, description="Original job posting URL")
    salary: Optional[str] = Field(None, description="Salary information if available")
    job_type: Optional[str] = Field(None, description="Employment type (full-time, contract, etc)")
    location: Optional[str] = Field(None, description="Job location")
    benefits: Optional[str] = Field(None, description="Benefits offered")
    key_skills: Optional[list[str]] = Field(None, description="Required skills extracted from offer")
    summary: Optional[str] = Field(None, description="AI summary of the offer")
    created_at: Optional[datetime] = Field(None, description="When analysis was created (UTC)")


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
    """Adapted CV for a specific job offer"""
    id: UUID = Field(..., description="Adaptation unique identifier (UUID)")
    adapted_cv_html: Optional[str] = Field(None, description="HTML content of adapted CV")
    adapted_cv_url: Optional[str] = Field(None, description="Download URL for adapted CV PDF")
    created_at: datetime = Field(..., description="When adaptation was created (UTC)")
    analysis_id: Optional[int] = Field(None, description="ID of the analysis this adaptation is based on")
    job_title: Optional[str] = Field(None, description="Target job title for adaptation")
    company: Optional[str] = Field(None, description="Target company for adaptation")
    score: Optional[int] = Field(None, description="Compatibility score for target offer")


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


# --- Error Response Schema ---
class ErrorResponse(BaseModel):
    """Standard error response for all API endpoints"""
    detail: str = Field(
        ...,
        description="Human-readable error message describing what went wrong"
    )
    error_code: str = Field(
        ...,
        description="Machine-readable error code for programmatic handling (e.g., AUTH_001, VALID_001)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred (UTC timestamp)"
    )

    class Config:
        example = {
            "detail": "Invalid credentials provided",
            "error_code": "AUTH_001",
            "timestamp": "2026-05-01T10:30:00Z"
        }
