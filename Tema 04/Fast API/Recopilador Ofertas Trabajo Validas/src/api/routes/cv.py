from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy import update
from src.api.schemas import CVUploadResponse, CVGenerationResponse, CVCurrentResponse, ErrorResponse
from src.api.dependencies import get_user_id, get_current_user
from src.api.limiter import get_limiter
from src.api.cv_service import CVService
from src.storage import upload_bytes
from src.database import AsyncSessionLocal, User, get_db
from src.cv_generator import CVGenerator
import tempfile
import os
import asyncio

router = APIRouter(prefix="/cv", tags=["cv"])
limiter = get_limiter()


@router.post(
    "/upload",
    summary="Upload user's CV file",
    tags=["cv"],
    response_model=CVUploadResponse,
    responses={
        200: {"description": "Upload successful", "model": CVUploadResponse},
        400: {"description": "Invalid file", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        413: {"description": "File too large (max 10MB)", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("5/minute")
async def upload_cv(
    request: Request,
    file: UploadFile = File(..., description="PDF or DOCX file (max 10MB)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> CVUploadResponse:
    """
    Upload a CV file (PDF or DOCX) to replace the user's current CV.

    File is stored securely and used as the base for all offer-specific adaptations.

    **Rate Limit:** 5 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Upload initial CV when creating account
    - Update CV with new experience/skills
    - Switch to different CV version

    **Notes:**
    - Only PDF and DOCX formats accepted
    - Maximum file size: 10MB
    - Previous CV is replaced (not versioned)
    - Processing may take 10-30 seconds for large files
    """
    try:
        # Validate PDF
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files allowed")

        # Save to temp file (run sync I/O in thread pool)
        content = await file.read()

        def save_temp_file():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                return tmp.name

        tmp_path = await asyncio.to_thread(save_temp_file)

        try:
            # Upload to Cloudinary
            result = await CVService.upload_cv(db, current_user.id, tmp_path)
            return CVUploadResponse(
                cv_url=result["cv_url"],
                user_id=current_user.id,
                status="success"
            )
        finally:
            # Clean temp file (run sync I/O in thread pool)
            def cleanup_file():
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            await asyncio.to_thread(cleanup_file)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get(
    "/current",
    summary="Get URL to user's current CV",
    tags=["cv"],
    response_model=CVCurrentResponse,
    responses={
        200: {"description": "CV URL retrieved", "model": CVCurrentResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "No CV uploaded", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def get_current_cv(
    current_user: User = Depends(get_current_user),
) -> CVCurrentResponse:
    """
    Retrieve the download URL for the user's current CV file.

    URL is valid for 24 hours and can be used to download the PDF/DOCX.

    **Rate Limit:** 60 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Preview current CV
    - Share CV link with others
    - Download CV for manual editing

    **Notes:**
    - Returns null URL if no CV has been uploaded yet
    - URLs expire after 24 hours (refresh to get new URL)
    """
    return CVCurrentResponse(
        cv_url=current_user.master_cv_url,
        user_id=current_user.id
    )


@router.delete(
    "/current",
    summary="Delete user's current CV",
    tags=["cv"],
    responses={
        204: {"description": "CV deleted successfully"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        404: {"description": "No CV to delete", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def delete_cv(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> None:
    """
    Delete the user's current CV from the system.

    Removes the file and clears all generated adaptations. Cannot be undone.

    **Rate Limit:** 5 requests per hour

    **Authentication:** Bearer token required

    **Use Cases:**
    - Remove old/outdated CV
    - Clean up account before deleting
    - Switch to completely different CV

    **Notes:**
    - All optimized CVs for specific offers are also deleted
    - No recovery possible - consider downloading CV first
    - User must re-upload CV before generating new adaptations
    """
    try:
        result = await CVService.delete_cv(db, current_user.id)
        if result:
            return {"status": "success", "message": "CV deleted"}
        else:
            raise HTTPException(status_code=404, detail="CV not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
