from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy import update
from src.api.schemas import CVUploadResponse, CVGenerationResponse
from src.api.dependencies import get_user_id
from src.storage import upload_bytes
from src.database import AsyncSessionLocal, User
from src.cv_generator import CVGenerator

router = APIRouter(prefix="/api", tags=["cv"])


@router.post("/upload-master-cv", response_model=CVUploadResponse)
async def upload_master_cv(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id)
):
    """
    Uploads master CV to Cloudinary and updates user.master_cv_url.

    Args:
        file: PDF file from multipart/form-data
        user_id: Inyectado desde .env via Depends()

    Returns:
        JSON con cv_url (enlace Cloudinary) y status
    """
    try:
        # Read file content
        content = await file.read()

        # Upload to Cloudinary
        cv_url = upload_bytes(content, public_id="cv/master")

        # Update user
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(User).where(User.id == user_id).values(master_cv_url=cv_url)
            )
            await session.commit()

        return CVUploadResponse(cv_url=cv_url, status="success")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/{offer_id}", response_model=CVGenerationResponse)
async def generate_optimized_cv(offer_id: int):
    """
    Generates and uploads optimized CV for a job offer.

    Args:
        offer_id: ID from job_offers table

    Returns:
        JSON con cv_url (enlace Cloudinary)
    """
    try:
        cv_url = await CVGenerator.generate_for_offer(offer_id)
        return CVGenerationResponse(cv_url=cv_url, status="success")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ERROR] CV generation failed: {e}")
        raise HTTPException(status_code=500, detail="CV generation failed")
