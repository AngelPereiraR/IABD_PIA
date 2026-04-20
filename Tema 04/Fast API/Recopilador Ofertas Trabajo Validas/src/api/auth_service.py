from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dotenv import load_dotenv
import os
import uuid

from src.database import User
from src.api.schemas import TokenResponse

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: uuid.UUID, email: str, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

        expire = datetime.utcnow() + expires_delta
        to_encode = {"user_id": str(user_id), "email": email, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    async def register_user(
        db: AsyncSession,
        email: str,
        password: str,
        auth_provider: str = "email",
    ) -> User:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError(f"User with email {email} already exists")

        password_hash = AuthService.hash_password(password) if password else None
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            auth_provider=auth_provider,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def login_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not AuthService.verify_password(password, user.password_hash or ""):
            raise ValueError("Invalid email or password")

        return user

    @staticmethod
    async def get_or_create_oauth_user(
        db: AsyncSession,
        email: str,
        auth_provider: str = "google",
    ) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = await AuthService.register_user(db, email, None, auth_provider)

        return user

    @staticmethod
    def create_token_response(user: User) -> TokenResponse:
        access_token = AuthService.create_access_token(user.id, user.email)
        return TokenResponse(
            access_token=access_token,
            user_id=user.id,
            email=user.email,
        )
