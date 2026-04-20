from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from src.api.schemas import (
    OfferDetail,
    AnalysisCreate,
    AnalysisResponse,
    AnalysisListResponse,
)
from src.api.dependencies import get_user_id, get_current_user
from src.api.limiter import get_limiter
from src.api.analysis_service import AnalysisService
from src.database import AsyncSessionLocal, JobOffer, User, get_db

router = APIRouter(prefix="/api", tags=["offers"])
limiter = get_limiter()


@router.get("/offers", response_model=list[OfferDetail])
@limiter.limit("60/minute")
async def list_offers(request: Request, skip: int = 0, limit: int = 20, user_id: str = Depends(get_user_id)):
    """
    Lists saved job offers with pagination.

    Args:
        skip: Number of offers to skip (default: 0)
        limit: Maximum offers to return (default: 20, max: 100)
        user_id: Inyectado desde .env via Depends()

    Returns:
        List of offers ordered by creation date (descending)
    """
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(JobOffer)
                .where(JobOffer.user_id == user_id)
                .order_by(JobOffer.created_at.desc())
                .offset(skip)
                .limit(min(limit, 100))
            )
            result = await session.execute(stmt)
            offers = result.scalars().all()

        return [
            OfferDetail(
                id=o.id,
                job_title=o.job_title,
                company=o.company,
                score=o.score,
                status=o.status,
                offer_url=o.offer_url,
                created_at=o.created_at
            )
            for o in offers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offers/{offer_id}", response_model=OfferDetail)
@limiter.limit("60/minute")
async def get_offer(request: Request, offer_id: int, user_id: str = Depends(get_user_id)):
    """Retorna el detalle completo de una oferta por ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(JobOffer).where(JobOffer.id == offer_id, JobOffer.user_id == user_id)
        )
        offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return OfferDetail(
        id=offer.id,
        job_title=offer.job_title,
        company=offer.company,
        score=offer.score,
        status=offer.status,
        offer_url=offer.offer_url,
        optimized_cv_url=offer.optimized_cv_url,
        created_at=offer.created_at,
    )


@router.get("/offers/{offer_id}/cv")
@limiter.limit("60/minute")
async def get_offer_cv(request: Request, offer_id: int, user_id: str = Depends(get_user_id)):
    """Redirige a la URL del CV optimizado para una oferta."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(JobOffer).where(JobOffer.id == offer_id, JobOffer.user_id == user_id)
        )
        offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    if not offer.optimized_cv_url:
        raise HTTPException(status_code=404, detail="CV aún no generado para esta oferta")
    return RedirectResponse(url=offer.optimized_cv_url)


# --- NEW ANALYSIS ENDPOINTS (JWT AUTH) ---
@router.post("/analysis/create", response_model=AnalysisResponse)
@limiter.limit("10/minute")
async def create_analysis(
    request: Request,
    analysis: AnalysisCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Analyze a job offer (text or URL) against user's CV.
    Returns score 0-100 and determines if valid (≥60).
    Requires Bearer token authentication.
    """
    try:
        if not analysis.offer_text and not analysis.offer_url:
            raise HTTPException(
                status_code=400,
                detail="Either offer_text or offer_url required"
            )

        result = await AnalysisService.analyze_offer(
            db=db,
            user_id=current_user.id,
            offer_text=analysis.offer_text,
            offer_url=analysis.offer_url,
        )

        return AnalysisResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
@limiter.limit("60/minute")
async def get_analysis(
    request: Request,
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get details of a specific analysis"""
    try:
        result = await AnalysisService.get_analysis(db, current_user.id, analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return AnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/list", response_model=AnalysisListResponse)
@limiter.limit("60/minute")
async def list_analyses(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """List all analyses for current user with pagination"""
    try:
        result = await AnalysisService.list_analyses(db, current_user.id, limit, offset)
        return AnalysisListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
