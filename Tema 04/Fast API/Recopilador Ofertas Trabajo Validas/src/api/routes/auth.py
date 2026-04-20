from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_async_session, get_current_user
from src.api.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from src.api.auth_service import AuthService
from src.database import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister, session: AsyncSession = Depends(get_async_session)):
    try:
        new_user = await AuthService.register_user(
            session,
            email=user.email,
            password=user.password,
            auth_provider=user.auth_provider,
        )
        return AuthService.create_token_response(new_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, session: AsyncSession = Depends(get_async_session)):
    try:
        user = await AuthService.login_user(session, email=credentials.email, password=credentials.password)
        return AuthService.create_token_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/google-callback", response_model=TokenResponse)
async def google_callback(code: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    try:
        user = await AuthService.get_or_create_oauth_user(
            session,
            email=code,
            auth_provider="google",
        )
        return AuthService.create_token_response(user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
