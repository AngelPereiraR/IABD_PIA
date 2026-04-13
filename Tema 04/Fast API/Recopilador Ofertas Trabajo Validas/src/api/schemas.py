from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class OfferDetail(BaseModel):
    """Modelo de respuesta para ofertas listadas"""
    id: int
    job_title: Optional[str] = None
    company: Optional[str] = None
    score: Optional[int] = None
    status: str
    offer_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CVUploadResponse(BaseModel):
    """Modelo de respuesta para upload de CV"""
    cv_url: str
    status: str


class CVGenerationResponse(BaseModel):
    """Modelo de respuesta para generación de CV optimizado"""
    cv_url: str
    status: str
