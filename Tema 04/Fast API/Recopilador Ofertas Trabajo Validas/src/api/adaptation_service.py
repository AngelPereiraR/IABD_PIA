from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import cloudinary
import cloudinary.uploader
import tempfile
import os

from src.database import CVAdaptation, JobOffer, User
from src.cv_generator import CVGenerator
from src.loader import load_cv_context

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.getenv("CLOUDINARY_API_KEY", ""),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
)


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
        Generate adapted CV for a job offer.

        Returns:
            {
                "id": uuid,
                "adapted_cv_html": str,
                "adapted_cv_url": str,  # Cloudinary PDF
                "analysis_id": int,
            }
        """

        # 1. Get analysis (verify user owns it and is_valid)
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

        # 2. Load CV and offer text
        cv_text = load_cv_context(cv_path)
        if not cv_text:
            raise ValueError("Could not load CV")

        offer_text = offer.offer_text or offer.offer_url or ""
        if not offer_text:
            raise ValueError("No offer text or URL available")

        # 3. Generate adapted CV using CVGenerator
        try:
            cv_generator = CVGenerator()
            adapted_html = cv_generator.generate_adapted_cv(
                original_cv=cv_text,
                job_offer=offer_text,
                job_title=offer.job_title or "Job",
                company=offer.company or "Company",
            )
        except Exception as e:
            raise ValueError(f"CV generation failed: {str(e)}")

        # 4. Generate PDF from HTML and upload to Cloudinary
        try:
            pdf_bytes = cv_generator.render_pdf(adapted_html)

            # Save PDF to temp file for Cloudinary upload
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            try:
                response = cloudinary.uploader.upload(
                    tmp_path,
                    resource_type="raw",
                    folder="cv_adaptations",
                    public_id=f"{user_id}_{analysis_id}_{uuid.uuid4()}",
                    type="authenticated",
                )
                adapted_cv_url = response.get("secure_url")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            raise ValueError(f"PDF generation/upload failed: {str(e)}")

        # 5. Store in database
        adaptation = CVAdaptation(
            id=uuid.uuid4(),
            user_id=user_id,
            job_offer_id=analysis_id,
            adapted_cv_html=adapted_html,
            adapted_cv_url=adapted_cv_url,
        )

        db.add(adaptation)
        await db.commit()
        await db.refresh(adaptation)

        return {
            "id": adaptation.id,
            "adapted_cv_html": adapted_html,
            "adapted_cv_url": adapted_cv_url,
            "analysis_id": analysis_id,
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
            "job_offer_id": adaptation.job_offer_id,
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
