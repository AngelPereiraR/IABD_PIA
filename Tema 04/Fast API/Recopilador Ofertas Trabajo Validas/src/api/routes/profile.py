"""
User profile endpoints for viewing and editing CV data + avatar upload
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.future import select
import asyncio

from src.api.schemas import ProfileResponse, ProfileUpdate, AvatarUploadResponse
from src.api.dependencies import get_current_user
from src.api.limiter import get_limiter
from src.database import User, get_db
from src.storage import upload_bytes_async

router = APIRouter(prefix="/profile", tags=["profile"])
limiter = get_limiter()


@router.get("", response_model=ProfileResponse)
@limiter.limit("10/minute")
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get current user's profile with CV data.

    Note: telegram_id is only visible to admin users.
    """
    # Refresh user to get latest data
    stmt = select(User).where(User.id == current_user.id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return ProfileResponse(
        email=user.email,
        telegram_id=user.telegram_id if user.role == "admin" else None,
        master_cv_url=user.master_cv_url,
        avatar_url=user.avatar_url,
        cv_data=user.cv_data,
    )


@router.put("", response_model=ProfileResponse)
@limiter.limit("5/minute")
async def update_profile(
    request: Request,
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Update user's profile (CV data and/or telegram_id).

    Note: telegram_id can only be updated by admin users.
    """
    stmt = select(User).where(User.id == current_user.id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update cv_data if provided (allowed for all users)
    if profile_update.cv_data is not None:
        user.cv_data = profile_update.cv_data.model_dump() if hasattr(profile_update.cv_data, 'model_dump') else profile_update.cv_data
        print(f"[INFO] Updated cv_data for user {user.email}")

    # Update telegram_id if provided (only for admin users)
    if profile_update.telegram_id is not None:
        if user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admin users can update telegram_id"
            )
        user.telegram_id = profile_update.telegram_id
        print(f"[INFO] Updated telegram_id for admin user {user.email}")

    await db.commit()
    await db.refresh(user)

    return ProfileResponse(
        email=user.email,
        telegram_id=user.telegram_id if user.role == "admin" else None,
        master_cv_url=user.master_cv_url,
        avatar_url=user.avatar_url,
        cv_data=user.cv_data,
    )


@router.post("/avatar", response_model=AvatarUploadResponse)
@limiter.limit("10/minute")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """Upload user profile avatar photo to Cloudinary"""
    try:
        # Validate file type
        if not file.content_type or "image" not in file.content_type:
            raise HTTPException(status_code=400, detail="Only image files allowed")

        # Read file bytes
        content = await file.read()

        # Upload to Cloudinary in thread pool
        def upload_to_cloudinary():
            import cloudinary.uploader
            response = cloudinary.uploader.upload(
                content,
                resource_type="image",
                public_id=f"avatars/{current_user.id}",
                overwrite=True,
                folder="opticv",
            )
            return response.get("secure_url")

        avatar_url = await asyncio.to_thread(upload_to_cloudinary)
        print(f"[INFO] Avatar uploaded for user {current_user.id}: {avatar_url}")

        # Update user's avatar_url in database
        stmt = select(User).where(User.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(user)
            print(f"[OK] User record updated with avatar_url")

        return AvatarUploadResponse(avatar_url=avatar_url, status="success")

    except Exception as e:
        print(f"[ERROR] Avatar upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Avatar upload failed: {str(e)}")
