from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy import update
from src.api.schemas import CVUploadResponse, CVGenerationResponse, CVCurrentResponse
from src.api.dependencies import get_user_id, get_current_user
from src.api.limiter import get_limiter
from src.api.cv_service import CVService
from src.storage import upload_bytes
from src.database import AsyncSessionLocal, User, get_db
from src.cv_generator import CVGenerator
import tempfile
import os

router = APIRouter(prefix="/cv", tags=["cv"])
limiter = get_limiter()


@router.post("/upload", response_model=CVUploadResponse)
@limiter.limit("5/minute")
async def upload_cv(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Upload CV to Cloudinary (requires Bearer token)"""
    try:
        # Validate PDF
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files allowed")

        # Save to temp file
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Upload to Cloudinary
            result = await CVService.upload_cv(db, current_user.id, tmp_path)
            return CVUploadResponse(
                cv_url=result["cv_url"],
                user_id=current_user.id,
                status="success"
            )
        finally:
            # Clean temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/current", response_model=CVCurrentResponse)
async def get_current_cv(
    current_user: User = Depends(get_current_user),
):
    """Get current user's CV URL"""
    return CVCurrentResponse(
        cv_url=current_user.master_cv_url,
        user_id=current_user.id
    )


@router.delete("/current")
async def delete_cv(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Delete current user's CV"""
    try:
        result = await CVService.delete_cv(db, current_user.id)
        if result:
            return {"status": "success", "message": "CV deleted"}
        else:
            raise HTTPException(status_code=404, detail="CV not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
