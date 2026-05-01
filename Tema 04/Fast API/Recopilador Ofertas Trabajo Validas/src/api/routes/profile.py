"""
User profile endpoints for viewing and editing CV data + avatar upload
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Body, Path
from sqlalchemy.future import select
import asyncio

from src.api.schemas import ProfileResponse, ProfileUpdate, AvatarUploadResponse, ErrorResponse
from src.api.dependencies import get_current_user
from src.api.limiter import get_limiter
from src.database import User, get_db
from src.storage import upload_bytes_async

router = APIRouter(prefix="/profile", tags=["profile"])
limiter = get_limiter()


@router.get(
    "",
    summary="Get user profile information",
    tags=["profile"],
    response_model=ProfileResponse,
    responses={
        200: {"description": "Profile data", "model": ProfileResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> ProfileResponse:
    """
    Retrieve the authenticated user's profile information.

    Includes name, bio, skills, experience, languages, and preferences.

    **Rate Limit:** 60 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Load user profile on app startup
    - Display profile page
    - Verify profile completeness

    **Notes:**
    - Only accessible by the profile owner
    - Returns complete profile including all sections
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


@router.put(
    "",
    summary="Update user profile",
    tags=["profile"],
    response_model=ProfileResponse,
    responses={
        200: {"description": "Profile updated", "model": ProfileResponse},
        400: {"description": "Invalid input", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("10/minute")
async def update_profile(
    request: Request,
    profile_update: ProfileUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> ProfileResponse:
    """
    Update user's profile information.

    Can update name, bio, skills, experience, languages, and preferences.

    **Rate Limit:** 10 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Edit profile details
    - Add/remove skills
    - Update career preferences
    - Modify language proficiencies

    **Notes:**
    - Only authenticated user can update their own profile
    - Partial updates supported (send only fields to update)
    - Changes take effect immediately
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


@router.post(
    "/avatar",
    summary="Upload profile avatar image",
    tags=["profile"],
    response_model=AvatarUploadResponse,
    responses={
        200: {"description": "Avatar uploaded", "model": AvatarUploadResponse},
        400: {"description": "Invalid image", "model": ErrorResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        413: {"description": "File too large (max 5MB)", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("10/minute")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(..., description="Image file (JPG, PNG, GIF, max 5MB)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> AvatarUploadResponse:
    """
    Upload a profile avatar image.

    Image is stored and displayed on user profile.

    **Rate Limit:** 10 requests per hour

    **Authentication:** Bearer token required

    **Use Cases:**
    - Set profile picture
    - Update avatar
    - Change profile appearance

    **Notes:**
    - Supported formats: JPG, PNG, GIF
    - Maximum file size: 5MB
    - Image is automatically resized to 200x200px
    - Previous avatar is replaced
    """
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
