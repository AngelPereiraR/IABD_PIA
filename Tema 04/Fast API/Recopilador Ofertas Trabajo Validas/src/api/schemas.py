from pydantic import BaseModel
from datetime import datetime

class OfferDetail(BaseModel):
    """Modelo de respuesta para ofertas listadas"""
    id: int
    job_title: str
    company: str
    score: int
    status: str
    offer_url: str
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
