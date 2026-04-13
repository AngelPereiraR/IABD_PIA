#!/usr/bin/env python3
"""
Seed script to insert base user in PostgreSQL.
Runs once to initialize the database with the primary user.
Also uploads the master CV to Cloudinary and saves the URL.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import insert, select, update
from src.database import User, AsyncSessionLocal
from src.storage import upload_pdf

load_dotenv()

CV_PATH = Path(__file__).parent / "data" / "cv_usuario.pdf"


def _upload_master_cv() -> str | None:
    """Sube cv_usuario.pdf a Cloudinary y retorna la URL, o None si no existe."""
    if not CV_PATH.exists():
        print(f"⚠️  CV no encontrado en {CV_PATH} — se omite subida")
        return None
    print(f"📤 Subiendo CV maestro desde {CV_PATH}...")
    url = upload_pdf(str(CV_PATH), public_id="cv/master")
    print(f"   CV subido: {url}")
    return url


async def seed_user():
    """Insert or update base user in database."""
    user_id = os.getenv("USER_ID")
    user_email = os.getenv("USER_EMAIL", "user@example.com")
    telegram_id = os.getenv("TELEGRAM_CHAT_ID")

    if not user_id:
        print("❌ USER_ID not set in .env")
        return

    master_cv_url = _upload_master_cv()

    async with AsyncSessionLocal() as session:
        # Check if user already exists
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ User already exists: {user_id}")
            print(f"   Email: {existing_user.email}")
            if master_cv_url:
                stmt = update(User).where(User.id == user_id).values(master_cv_url=master_cv_url)
                await session.execute(stmt)
                await session.commit()
                print(f"   master_cv_url actualizado: {master_cv_url}")
            return

        # Create new user
        stmt = insert(User).values(
            id=user_id,
            email=user_email,
            telegram_id=telegram_id,
            master_cv_url=master_cv_url
        )
        await session.execute(stmt)
        await session.commit()
        print(f"✅ User created successfully!")
        print(f"   ID: {user_id}")
        print(f"   Email: {user_email}")
        print(f"   Telegram ID: {telegram_id}")
        print(f"   master_cv_url: {master_cv_url}")


if __name__ == "__main__":
    import selectors
    loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(seed_user())
    finally:
        loop.close()
