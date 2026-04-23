from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from src.database import CVAdaptation, JobOffer
from src.cv_generator import CVGenerator


class AdaptationService:
    """Service for generating and storing adapted CVs"""

    @staticmethod
    async def create_adaptation(
        db: AsyncSession,
        user_id: uuid.UUID,
        analysis_id: int,
        cv_path: str = "data/cv_usuario.pdf",
    ) -> Dict[str, Any]:
        """
        Generate adapted CV for a job offer using LaTeX pipeline.
        CVGenerator.generate_for_offer() handles compilation and Cloudinary upload.

        Returns:
            {
                "id": uuid,
                "adapted_cv_html": None,
                "adapted_cv_url": str,
                "created_at": datetime,
            }
        """
        # 1. Validate offer exists and belongs to user, with valid score (>= 60)
        result = await db.execute(
            select(JobOffer).where(
                (JobOffer.id == analysis_id) & (JobOffer.user_id == user_id)
            )
        )
        offer = result.scalar_one_or_none()

        if not offer:
            raise ValueError("Analysis not found")

        if not offer.is_valid:
            raise ValueError("Analysis score < 60, cannot generate adaptation")

        # 2. Generate LaTeX-based PDF via CVGenerator (handles all compilation and upload)
        try:
            adapted_cv_url = await CVGenerator.generate_for_offer(analysis_id, db=db)
        except Exception as e:
            raise ValueError(f"LaTeX PDF generation failed: {str(e)}")

        # 3. Store adaptation record in database
        adaptation = CVAdaptation(
            id=uuid.uuid4(),
            user_id=user_id,
            job_offer_id=analysis_id,
            adapted_cv_html=None,  # LaTeX flow doesn't produce HTML preview
            adapted_cv_url=adapted_cv_url,
        )

        db.add(adaptation)
        await db.commit()
        await db.refresh(adaptation)

        return {
            "id": adaptation.id,
            "adapted_cv_html": None,
            "adapted_cv_url": adapted_cv_url,
            "created_at": adaptation.created_at,
        }

    @staticmethod
    async def get_adaptation(
        db: AsyncSession,
        user_id: uuid.UUID,
        adaptation_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific adaptation by ID"""
        result = await db.execute(
            select(CVAdaptation).where(
                (CVAdaptation.id == adaptation_id) & (CVAdaptation.user_id == user_id)
            )
        )
        adaptation = result.scalar_one_or_none()

        if not adaptation:
            return None

        return {
            "id": adaptation.id,
            "adapted_cv_html": adaptation.adapted_cv_html,
            "adapted_cv_url": adaptation.adapted_cv_url,
            "created_at": adaptation.created_at,
        }

    @staticmethod
    async def list_adaptations(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List user's adaptations with pagination"""
        from sqlalchemy import func

        count_result = await db.execute(
            select(func.count(CVAdaptation.id)).where(CVAdaptation.user_id == user_id)
        )
        total = count_result.scalar()

        result = await db.execute(
            select(CVAdaptation)
            .where(CVAdaptation.user_id == user_id)
            .order_by(CVAdaptation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        adaptations = result.scalars().all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": a.id,
                    "created_at": a.created_at,
                    "job_offer_id": a.job_offer_id,
                    "adapted_cv_url": a.adapted_cv_url,
                }
                for a in adaptations
            ],
        }
