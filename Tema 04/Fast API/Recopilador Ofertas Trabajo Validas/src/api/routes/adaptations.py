from fastapi import APIRouter, HTTPException, Depends, Request, Query
from src.api.schemas import (
    AdaptationCreate,
    AdaptationResponse,
    AdaptationListResponse,
)
from src.api.dependencies import get_current_user
from src.api.limiter import get_limiter
from src.api.adaptation_service import AdaptationService
from src.database import User, get_db

router = APIRouter(prefix="/adaptations", tags=["adaptations"])
limiter = get_limiter()


@router.post("/create", response_model=AdaptationResponse)
@limiter.limit("5/minute")
async def create_adaptation(
    request: Request,
    adaptation: AdaptationCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Generate adapted CV for a job offer.
    Requires: analysis_id with is_valid=TRUE (score ≥60)
    Returns: HTML preview + Cloudinary PDF URL
    """
    try:
        result = await AdaptationService.create_adaptation(
            db=db,
            user_id=current_user.id,
            analysis_id=adaptation.analysis_id,
        )

        return AdaptationResponse(
            id=result["id"],
            adapted_cv_html=result["adapted_cv_html"][:1000] if result["adapted_cv_html"] else None,
            adapted_cv_url=result["adapted_cv_url"],
            created_at=result.get("created_at"),
            analysis_id=result.get("analysis_id"),
            job_title=result.get("job_title"),
            company=result.get("company"),
            score=result.get("score"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptation failed: {str(e)}")


@router.get("/list", response_model=AdaptationListResponse)
@limiter.limit("60/minute")
async def list_adaptations(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """List all adaptations for current user with pagination"""
    try:
        result = await AdaptationService.list_adaptations(db, current_user.id, limit, offset)
        return AdaptationListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{adaptation_id}", response_model=AdaptationResponse)
@limiter.limit("60/minute")
async def get_adaptation(
    request: Request,
    adaptation_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get details of a specific adaptation"""
    try:
        result = await AdaptationService.get_adaptation(db, current_user.id, adaptation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Adaptation not found")

        return AdaptationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{adaptation_id}/download")
@limiter.limit("60/minute")
async def download_adaptation_pdf(
    request: Request,
    adaptation_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Download adapted CV as PDF.
    Redirects to Cloudinary secure URL.
    """
    try:
        result = await AdaptationService.get_adaptation(db, current_user.id, adaptation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Adaptation not found")

        if not result.get("adapted_cv_url"):
            raise HTTPException(status_code=404, detail="PDF not available")

        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=result["adapted_cv_url"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
