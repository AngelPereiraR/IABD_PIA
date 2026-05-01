from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path, Body
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from src.api.schemas import (
    OfferDetail,
    AnalysisCreate,
    AnalysisResponse,
    AnalysisListResponse,
    AdaptationResponse,
    ErrorResponse,
)
from src.api.dependencies import get_user_id, get_current_user
from src.api.limiter import get_limiter
from src.api.analysis_service import AnalysisService
from src.api.adaptation_service import AdaptationService
from src.database import AsyncSessionLocal, JobOffer, User, get_db

router = APIRouter(tags=["offers"])
limiter = get_limiter()


@router.get(
    "/offers",
    summary="List all job offers",
    tags=["offers"],
    response_model=list[OfferDetail],
    responses={
        200: {"description": "Offers retrieved", "model": list[OfferDetail]},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def list_offers(
    request: Request,
    skip: int = Query(0, description="Number of results to skip (pagination)"),
    limit: int = Query(20, description="Maximum results per page (1-100)"),
    user_id: str = Depends(get_user_id)
) -> list[OfferDetail]:
    """
    Retrieve paginated list of all job offers captured for the user.

    Includes pending, viewed, applied, and archived offers. Default sorting by newest first.

    **Rate Limit:** 60 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Show offers feed/dashboard
    - Paginate through multiple offers
    - Filter and sort offers

    **Notes:**
    - Returns offers regardless of compatibility score
    - Default limit is 20, maximum is 100
    - Skip parameter starts from 0 (pagination offset)
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


@router.get(
    "/offers/{offer_id}",
    summary="Get detailed offer information",
    tags=["offers"],
    response_model=OfferDetail,
    responses={
        200: {"description": "Offer details", "model": OfferDetail},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "Offer not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def get_offer(
    request: Request,
    offer_id: int = Path(..., description="Unique offer identifier"),
    user_id: str = Depends(get_user_id)
) -> OfferDetail:
    """
    Retrieve complete details for a specific job offer.

    Includes title, company, salary, AI compatibility score, and optimized CV link.

    **Rate Limit:** 60 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - View offer detail page
    - Check compatibility score before applying
    - Access optimized CV for the offer

    **Notes:**
    - Only offers belonging to authenticated user are accessible
    - Score is 0-100 (higher = better match)
    """
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


@router.get(
    "/offers/{offer_id}/cv",
    summary="Download CV optimized for specific offer",
    tags=["offers"],
    responses={
        200: {"description": "PDF file"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "Offer or CV not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("20/minute")
async def get_offer_cv(
    request: Request,
    offer_id: int = Path(..., description="Unique offer identifier"),
    user_id: str = Depends(get_user_id)
) -> RedirectResponse:
    """
    Download the CV optimized specifically for a job offer.

    Returns PDF with content tailored to match offer requirements.

    **Rate Limit:** 20 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Download CV to apply for offer
    - Verify optimizations made by AI
    - Submit to job application

    **Notes:**
    - Generates PDF on-demand or returns cached version
    - Processing may take 5-10 seconds for first request
    """
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
@router.post(
    "/analysis/create",
    summary="Create analysis of job offer",
    tags=["offers"],
    response_model=AnalysisResponse,
    responses={
        200: {"description": "Analysis created", "model": AnalysisResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("10/minute")
async def create_analysis(
    request: Request,
    analysis: AnalysisCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> AnalysisResponse:
    """
    Analyze a job offer against user's CV and skills.

    Performs AI-powered compatibility assessment using DeepSeek LLM.

    **Rate Limit:** 10 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Analyze new job offer
    - Get AI assessment of compatibility
    - Determine if worth applying for

    **Notes:**
    - Processing takes 15-30 seconds (async)
    - Returns score 0-100 with detailed breakdown
    - Requires CV to be uploaded first
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


@router.get(
    "/analysis/list",
    summary="List all offer analyses",
    tags=["offers"],
    response_model=AnalysisListResponse,
    responses={
        200: {"description": "Analysis list", "model": AnalysisListResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("30/minute")
async def list_analyses(
    request: Request,
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> AnalysisListResponse:
    """
    Retrieve all completed offer analyses for the user.

    Lists analysis results with scores and timestamps.

    **Rate Limit:** 30 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - View analysis history
    - Paginate through past analyses
    - Track compatibility scores over time

    **Notes:**
    - Results sorted by newest first
    - Shows summary only (use detail endpoint for full info)
    """
    try:
        result = await AnalysisService.list_analyses(db, current_user.id, limit, offset)
        return AnalysisListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/{analysis_id}",
    summary="Get analysis details",
    tags=["offers"],
    response_model=AnalysisResponse,
    responses={
        200: {"description": "Analysis data", "model": AnalysisResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "Analysis not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def get_analysis(
    request: Request,
    analysis_id: int = Path(..., description="Analysis unique identifier"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> AnalysisResponse:
    """
    Retrieve complete analysis details for a specific job offer.

    Shows compatibility score, extracted offer details, and AI assessment.

    **Rate Limit:** 60 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Review detailed analysis of offer
    - Check AI reasoning for score
    - Verify offer data extraction

    **Notes:**
    - Only accessible to owner of analysis
    - Shows full analysis details including summary
    """
    try:
        result = await AnalysisService.get_analysis(db, current_user.id, analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return AnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- TELEGRAM BOT ENDPOINT (NO AUTH REQUIRED) ---
@router.post(
    "/generate/{offer_id}",
    summary="Generate adapted CV for offer",
    tags=["offers"],
    response_model=AdaptationResponse,
    responses={
        200: {"description": "CV generated", "model": AdaptationResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
        404: {"description": "Offer not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("10/minute")
async def generate_cv_for_offer(
    request: Request,
    offer_id: int = Path(..., description="Offer/Analysis ID"),
    user_id: str = Depends(get_user_id),
    db = Depends(get_db),
) -> AdaptationResponse:
    """
    Generate optimized CV for a job offer.

    Requires: offer_id with is_valid=TRUE (score ≥60). Returns: Cloudinary PDF URL.

    **Rate Limit:** 10 requests per minute

    **Authentication:** Optional (bot-compatible, can work without Bearer token)

    **Use Cases:**
    - Generate optimized CV for qualified offer
    - Create tailored application materials
    - Automate CV adaptation workflow

    **Notes:**
    - Only generates for offers with compatibility score ≥60
    - Processing takes 20-40 seconds
    - Output cached for future downloads
    """
    try:
        result = await AdaptationService.create_adaptation(
            db=db,
            user_id=user_id,
            analysis_id=offer_id,
        )
        return AdaptationResponse(
            id=result["id"],
            adapted_cv_html=result["adapted_cv_html"][:1000] if result["adapted_cv_html"] else None,
            adapted_cv_url=result["adapted_cv_url"],
            created_at=result["created_at"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")
