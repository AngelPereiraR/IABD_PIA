from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from src.database import JobOffer, User
from src.scraper import scrape_offer_content
from src.brain import RecruitmentBrain
from src.loader import load_cv_context


class AnalysisService:
    """Service for analyzing job offers using existing brain + scraper modules"""

    @staticmethod
    async def analyze_offer(
        db: AsyncSession,
        user_id: uuid.UUID,
        offer_text: Optional[str] = None,
        offer_url: Optional[str] = None,
        cv_path: str = "data/cv_usuario.pdf",
    ) -> Dict[str, Any]:
        """
        Analyze a job offer and store result in DB.

        Returns:
            {
                "id": int,  # JobOffer.id
                "score": int,  # 0-100
                "is_valid": bool,  # score >= 60
                "extracted_title": str,
                "extracted_company": str,
                "scoring_details": dict,
            }
        """

        # 1. Get offer text (from param or scrape URL)
        if offer_url:
            offer_markdown = scrape_offer_content(offer_url)
            if not offer_markdown:
                raise ValueError(f"Could not scrape offer from {offer_url}")
        elif offer_text:
            offer_markdown = offer_text
        else:
            raise ValueError("Either offer_text or offer_url required")

        # 2. Load user's CV
        cv_text = load_cv_context(cv_path)
        if not cv_text:
            raise ValueError("Could not load CV")

        # 3. Analyze with DeepSeek brain
        brain = RecruitmentBrain()
        decision = brain.analyze_offer(cv_text, offer_markdown)

        # 4. Extract structured data
        score = decision.get("score", 0)
        is_valid = score >= 60
        extracted_title = decision.get("job_title", "")
        extracted_company = decision.get("company", "")

        scoring_details = {
            "ats_score": decision.get("ats_score"),
            "recruiter_score": decision.get("recruiter_score"),
            "reasoning": decision.get("summary", ""),
        }

        # 5. Store in database
        job_offer = JobOffer(
            user_id=user_id,
            offer_text=offer_markdown[:5000] if offer_markdown else None,  # Limit size
            offer_url=offer_url,
            job_title=extracted_title,
            company=extracted_company,
            score=score,
            is_valid=is_valid,
            scoring_details=scoring_details,
            analysis_result=decision,
            status="done",
        )

        db.add(job_offer)
        await db.commit()
        await db.refresh(job_offer)

        return {
            "id": job_offer.id,
            "score": score,
            "is_valid": is_valid,
            "extracted_title": extracted_title,
            "extracted_company": extracted_company,
            "scoring_details": scoring_details,
        }

    @staticmethod
    async def get_analysis(
        db: AsyncSession,
        user_id: uuid.UUID,
        analysis_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific analysis by ID"""
        result = await db.execute(
            select(JobOffer).where(
                (JobOffer.id == analysis_id) & (JobOffer.user_id == user_id)
            )
        )
        offer = result.scalar_one_or_none()

        if not offer:
            return None

        return {
            "id": offer.id,
            "score": offer.score,
            "is_valid": offer.is_valid,
            "extracted_title": offer.job_title,
            "extracted_company": offer.company,
            "offer_url": offer.offer_url,
            "scoring_details": offer.scoring_details,
            "analysis_result": offer.analysis_result,
            "created_at": offer.created_at,
        }

    @staticmethod
    async def list_analyses(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List user's analyses with pagination"""
        # Count total
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count(JobOffer.id)).where(JobOffer.user_id == user_id)
        )
        total = count_result.scalar()

        # Get paginated results
        result = await db.execute(
            select(JobOffer)
            .where(JobOffer.user_id == user_id)
            .order_by(JobOffer.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        offers = result.scalars().all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": o.id,
                    "score": o.score,
                    "is_valid": o.is_valid,
                    "extracted_title": o.job_title,
                    "extracted_company": o.company,
                    "created_at": o.created_at,
                }
                for o in offers
            ],
        }
