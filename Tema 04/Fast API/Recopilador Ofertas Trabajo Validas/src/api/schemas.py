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
    extracted_title: Optional[str] = None
    extracted_company: Optional[str] = None
    scoring_details: Optional[dict] = None
    offer_url: Optional[str] = None


class AnalysisListItem(BaseModel):
    id: int
    score: Optional[int] = None
    is_valid: Optional[bool] = None
    extracted_title: Optional[str] = None
    extracted_company: Optional[str] = None
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


class AdaptationListItem(BaseModel):
    id: UUID
    created_at: datetime
    job_offer_id: int
    adapted_cv_url: Optional[str] = None


class AdaptationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AdaptationListItem]
