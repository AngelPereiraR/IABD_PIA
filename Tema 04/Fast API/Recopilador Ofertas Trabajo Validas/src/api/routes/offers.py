from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from src.api.schemas import OfferDetail
from src.api.dependencies import get_user_id
from src.api.limiter import get_limiter
from src.database import AsyncSessionLocal, JobOffer

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
