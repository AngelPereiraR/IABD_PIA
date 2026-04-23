#!/usr/bin/env python3
"""
Seed script to insert base user in PostgreSQL.
Runs once to initialize the database with the primary user.
Also uploads the master CV to Cloudinary and saves the URL.
Extracts structured CV data and saves it to user.cv_data and local JSON.
"""
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import insert, select, update
from src.database import User, AsyncSessionLocal
from src.storage import upload_pdf
from src.loader import load_cv_context
from src.api.cv_service import CVService

load_dotenv()

CV_PATH = Path(__file__).parent / "data" / "cv_usuario.pdf"
CV_DATA_PATH = Path(__file__).parent / "data" / "cv_master_data.json"


def _upload_master_cv() -> str | None:
    """Sube cv_usuario.pdf a Cloudinary y retorna la URL, o None si no existe."""
    if not CV_PATH.exists():
        print(f"[WARNING] CV no encontrado en {CV_PATH} — se omite subida")
        return None
    print(f"[UPLOAD] Subiendo CV maestro desde {CV_PATH}...")
    url = upload_pdf(str(CV_PATH), public_id="cv/master")
    print(f"   CV subido: {url}")
    return url


async def _extract_cv_data() -> dict | None:
    """
    Extrae datos estructurados del CV maestro y retorna un dict,
    o None si el CV no existe o la extracción falla.
    También guarda los datos en cv_master_data.json para debugging.
    """
    if not CV_PATH.exists():
        print(f"[WARNING] CV no encontrado en {CV_PATH} — se omite extracción")
        return None

    print(f"[EXTRACT] Extrayendo datos del CV...")
    try:
        # Extraer texto del PDF
        pdf_text = load_cv_context(str(CV_PATH))
        if not pdf_text:
            print("[WARNING] CV appears to be empty or unreadable")
            return None

        # Extraer datos estructurados con DeepSeek
        cv_data = await CVService.extract_cv_data(pdf_text)
        cv_dict = cv_data if isinstance(cv_data, dict) else cv_data.model_dump()
        print(f"[OK] CV data extracted: {cv_dict.get('nombre', '?')}")

        # Guardar datos localmente en JSON para debugging
        _save_cv_data_local(cv_dict)

        return cv_dict
    except Exception as e:
        print(f"[WARNING] Failed to extract CV data: {e}")
        return None


def _save_cv_data_local(cv_data: dict) -> None:
    """Guarda los datos del CV extraídos en cv_master_data.json para debugging."""
    try:
        CV_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CV_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(cv_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] CV data saved locally to {CV_DATA_PATH}")
    except Exception as e:
        print(f"[WARN] Failed to save CV data locally: {e}")


async def seed_user():
    """Insert or update base user in database, including CV data extraction."""
    from src.api.auth_service import AuthService

    user_id = os.getenv("USER_ID")
    user_email = os.getenv("USER_EMAIL", "user@example.com")
    user_password = os.getenv("USER_PASSWORD")
    telegram_id = os.getenv("TELEGRAM_CHAT_ID")

    if not user_id:
        print("[ERROR] USER_ID not set in .env")
        return

    master_cv_url = _upload_master_cv()
    cv_data = await _extract_cv_data()

    async with AsyncSessionLocal() as session:
        # Check if user already exists
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"[OK] User already exists: {user_id}")
            print(f"   Email: {existing_user.email}")
            # Always update role to admin and telegram_id from .env
            update_data = {
                "role": "admin",  # Ensure this is the admin user
                "telegram_id": telegram_id,  # Update from .env
            }
            if master_cv_url:
                update_data["master_cv_url"] = master_cv_url
            if cv_data:
                update_data["cv_data"] = cv_data

            stmt = update(User).where(User.id == user_id).values(**update_data)
            await session.execute(stmt)
            await session.commit()
            print(f"   role actualizado: admin")
            print(f"   telegram_id actualizado: {telegram_id}")
            if master_cv_url:
                print(f"   master_cv_url actualizado: {master_cv_url}")
            if cv_data:
                print(f"   cv_data actualizado: nombre={cv_data.get('nombre', '?')}")
            return

        # Hash password if provided
        hashed_password = AuthService.hash_password(user_password) if user_password else None

        # Create new user (as admin - propietario del CV maestro local)
        stmt = insert(User).values(
            id=user_id,
            email=user_email,
            password_hash=hashed_password,
            role="admin",  # Este usuario es el propietario del CV maestro
            telegram_id=telegram_id,
            master_cv_url=master_cv_url,
            cv_data=cv_data
        )
        await session.execute(stmt)
        await session.commit()
        print(f"[OK] User created successfully!")
        print(f"   ID: {user_id}")
        print(f"   Email: {user_email}")
        print(f"   Password: {'Set' if user_password else 'Not set'}")
        print(f"   Telegram ID: {telegram_id}")
        print(f"   master_cv_url: {master_cv_url}")
        if cv_data:
            print(f"   cv_data: nombre={cv_data.get('nombre', '?')}")


if __name__ == "__main__":
    import selectors
    loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(seed_user())
    finally:
        loop.close()
