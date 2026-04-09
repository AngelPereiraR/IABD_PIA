#!/usr/bin/env python3
"""
Seed script to insert base user in PostgreSQL.
Runs once to initialize the database with the primary user.
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import insert, select
from src.database import User, AsyncSessionLocal

load_dotenv()


async def seed_user():
    """Insert or update base user in database."""
    user_id = os.getenv("USER_ID")
    user_email = os.getenv("USER_EMAIL", "user@example.com")
    telegram_id = os.getenv("TELEGRAM_CHAT_ID")

    if not user_id:
        print("❌ USER_ID not set in .env")
        return

    async with AsyncSessionLocal() as session:
        # Check if user already exists
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ User already exists: {user_id}")
            print(f"   Email: {existing_user.email}")
            return

        # Create new user
        stmt = insert(User).values(
            id=user_id,
            email=user_email,
            telegram_id=telegram_id
        )
        await session.execute(stmt)
        await session.commit()
        print(f"✅ User created successfully!")
        print(f"   ID: {user_id}")
        print(f"   Email: {user_email}")
        print(f"   Telegram ID: {telegram_id}")


if __name__ == "__main__":
    asyncio.run(seed_user())
