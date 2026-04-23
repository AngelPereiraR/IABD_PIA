"""
Manual migration script to add cv_data column to users table
Run: python apply_migration.py
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

async def apply_migration():
    """Apply the cv_data column migration"""
    database_url = os.environ.get("DATABASE_URL", "postgresql://localhost/opticv")

    # Convert postgresql:// to postgresql+asyncpg://
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    # Remove query parameters that asyncpg doesn't support
    if "?" in database_url:
        database_url = database_url.split("?")[0]

    print(f"[INFO] Connecting to database...")
    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.begin() as conn:
            # Check and add cv_data column
            print(f"[INFO] Checking if cv_data column exists...")
            result = await conn.execute(
                text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'cv_data'
                """)
            )

            if not result.fetchone():
                print(f"[INFO] Adding cv_data column to users table...")
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN cv_data JSONB NULL")
                )
                print("[OK] cv_data column added")
            else:
                print("[OK] cv_data column already exists")

            # Check and add avatar_url column
            print(f"[INFO] Checking if avatar_url column exists...")
            result = await conn.execute(
                text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'avatar_url'
                """)
            )

            if not result.fetchone():
                print(f"[INFO] Adding avatar_url column to users table...")
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN avatar_url TEXT NULL")
                )
                print("[OK] avatar_url column added")
            else:
                print("[OK] avatar_url column already exists")

            # Check and add role column
            print(f"[INFO] Checking if role column exists...")
            result = await conn.execute(
                text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'role'
                """)
            )

            if not result.fetchone():
                print(f"[INFO] Adding role column to users table...")
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user'")
                )
                print("[OK] role column added")
            else:
                print("[OK] role column already exists")

            print("[OK] All migrations applied successfully")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(apply_migration())
