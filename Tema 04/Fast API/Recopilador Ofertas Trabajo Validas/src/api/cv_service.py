import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import cloudinary
import cloudinary.uploader
import uuid

from src.database import User

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.getenv("CLOUDINARY_API_KEY", ""),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
)


class CVService:
    @staticmethod
    async def upload_cv(
        db: AsyncSession,
        user_id: uuid.UUID,
        file_path: str,
    ) -> dict:
        """Upload CV to Cloudinary and update user's master_cv_url"""
        try:
            response = cloudinary.uploader.upload(
                file_path,
                resource_type="raw",
                folder="cv_uploads",
                public_id=f"{user_id}_{uuid.uuid4()}",
                type="authenticated",
            )
            file_url = response.get("secure_url")

            # Update user's master CV
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user:
                user.master_cv_url = file_url
                await db.commit()
                await db.refresh(user)

            return {
                "cv_url": file_url,
                "user_id": str(user_id),
                "file_path": file_path,
            }
        except Exception as e:
            raise Exception(f"Error uploading CV to Cloudinary: {str(e)}")

    @staticmethod
    async def get_current_cv(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[str]:
        """Get user's current CV URL"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            return user.master_cv_url
        return None

    @staticmethod
    async def delete_cv(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> bool:
        """Remove CV from user profile"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.master_cv_url = None
            await db.commit()
            return True
        return False
