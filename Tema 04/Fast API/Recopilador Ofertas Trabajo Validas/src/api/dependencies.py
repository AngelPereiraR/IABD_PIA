import os
from fastapi import HTTPException
from src.database import AsyncSessionLocal


async def get_user_id() -> str:
    """Extrae USER_ID del .env. Lanza excepción si no está configurado."""
    user_id = os.getenv("USER_ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="USER_ID not configured in .env")
    return user_id


async def get_async_session():
    """Retorna una sesión de base de datos asíncrona."""
    async with AsyncSessionLocal() as session:
        yield session
