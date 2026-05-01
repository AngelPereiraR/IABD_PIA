from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path, Body
from fastapi.responses import RedirectResponse
from src.api.schemas import (
    AdaptationCreate,
    AdaptationResponse,
    AdaptationListResponse,
    ErrorResponse,
)
from src.api.dependencies import get_current_user
from src.api.limiter import get_limiter
from src.api.adaptation_service import AdaptationService
from src.database import User, get_db

router = APIRouter(prefix="/adaptations", tags=["adaptations"])
limiter = get_limiter()


@router.post(
    "/create",
    summary="Create adapted CV for a job offer",
    tags=["adaptations"],
    response_model=AdaptationResponse,
    responses={
        200: {"description": "Adaptation created", "model": AdaptationResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "Offer or CV not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("10/minute")
async def create_adaptation(
    request: Request,
    adaptation: AdaptationCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> AdaptationResponse:
    """
    Generate a CV adapted specifically for a job offer.

    Uses AI to tailor CV content, keywords, and formatting to match offer requirements.

    **Rate Limit:** 10 requests per hour

    **Authentication:** Bearer token required

    **Use Cases:**
    - Generate tailored CV for applying
    - Optimize CV content for specific role
    - Create multiple versions for different offers

    **Notes:**
    - Processing takes 20-40 seconds
    - Uses base CV plus offer details and analysis
    - Output is PDF ready for submission
    - Caches result for future downloads
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


@router.get(
    "/list",
    summary="List all adapted CVs",
    tags=["adaptations"],
    response_model=AdaptationListResponse,
    responses={
        200: {"description": "Adaptation list", "model": AdaptationListResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("30/minute")
async def list_adaptations(
    request: Request,
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> AdaptationListResponse:
    """
    Retrieve list of all CVs adapted for specific offers.

    Shows which offers have been adapted, with timestamps and status.

    **Rate Limit:** 30 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - View all created adaptations
    - Find previously adapted CVs
    - Track CV generation history

    **Notes:**
    - Sorted by newest first
    - Shows metadata only (use detail endpoint for full CV)
    """
    try:
        result = await AdaptationService.list_adaptations(db, current_user.id, limit, offset)
        return AdaptationListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{adaptation_id}",
    summary="Get adaptation details",
    tags=["adaptations"],
    response_model=AdaptationResponse,
    responses={
        200: {"description": "Adaptation data", "model": AdaptationResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "Adaptation not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def get_adaptation(
    request: Request,
    adaptation_id: str = Path(..., description="Adaptation unique identifier"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> AdaptationResponse:
    """
    Retrieve details of a specific adapted CV.

    Shows metadata, timestamps, and download URL.

    **Rate Limit:** 60 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Check adaptation status
    - Get download link for adapted CV
    - Verify adaptation details

    **Notes:**
    - Only accessible to owner of adaptation
    - Returns metadata and download URL
    """
    try:
        result = await AdaptationService.get_adaptation(db, current_user.id, adaptation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Adaptation not found")

        return AdaptationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{adaptation_id}/download",
    summary="Download adapted CV as PDF",
    tags=["adaptations"],
    responses={
        200: {"description": "PDF file"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "Adaptation not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("20/minute")
async def download_adaptation_pdf(
    request: Request,
    adaptation_id: str = Path(..., description="Adaptation unique identifier"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> RedirectResponse:
    """
    Download the generated adapted CV as a PDF file.

    Returns ready-to-submit PDF tailored for the target job offer.

    **Rate Limit:** 20 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Download CV to submit in job application
    - Preview generated adaptation
    - Save CV locally

    **Notes:**
    - PDF is pre-generated and cached
    - First request may take 2-5 seconds
    - Subsequent requests return cached version
    """
    try:
        result = await AdaptationService.get_adaptation(db, current_user.id, adaptation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Adaptation not found")

        if not result.get("adapted_cv_url"):
            raise HTTPException(status_code=404, detail="PDF not available")

        return RedirectResponse(url=result["adapted_cv_url"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
