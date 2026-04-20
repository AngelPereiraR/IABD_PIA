import os
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import AsyncSessionLocal, User
from src.api.auth_service import AuthService

security = HTTPBearer()


async def get_user_id() -> str:
    """Extrae USER_ID del .env. Lanza excepción si no está configurado."""
    user_id = os.getenv("USER_ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="USER_ID not configured in .env")
    return user_id


async def get_async_session() -> AsyncSession:
    """Retorna una sesión de base de datos asíncrona."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Extrae el usuario autenticado del token JWT Bearer."""
    token = credentials.credentials
    payload = AuthService.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
