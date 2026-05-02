from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_async_session, get_current_user
from src.api.schemas import UserRegister, UserLogin, TokenResponse, UserResponse, ErrorResponse
from src.api.auth_service import AuthService
from src.database import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    summary="Register a new user account",
    tags=["auth"],
    response_model=TokenResponse,
    responses={
        200: {"description": "Registration successful", "model": TokenResponse},
        400: {"description": "Invalid input", "model": ErrorResponse},
        409: {"description": "Email already registered", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def register(
    user: UserRegister = Body(..., examples={
        "example": {
            "value": {
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "auth_provider": "email"
            }
        }
    }),
    session: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """
    Create a new user account and return authentication token.

    Validates email uniqueness and password strength. Returns JWT token for immediate use.

    **Rate Limit:** 5 requests per hour

    **Authentication:** None (public endpoint)

    **Use Cases:**
    - New user account creation
    - Self-registration from frontend signup form

    **Notes:**
    - Email must be valid and unique
    - Password must be at least 8 characters
    - Token expires in 30 days
    """
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


@router.post(
    "/login",
    summary="Authenticate user and get access token",
    tags=["auth"],
    response_model=TokenResponse,
    responses={
        200: {"description": "Login successful", "model": TokenResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        400: {"description": "Invalid input", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def login(
    credentials: UserLogin = Body(..., examples={
        "example": {
            "value": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    }),
    session: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """
    Authenticate user with email and password.

    Returns JWT token valid for 30 days. Use token in Authorization header for protected endpoints.

    **Rate Limit:** 10 requests per hour

    **Authentication:** None (public endpoint)

    **Use Cases:**
    - User login from web application
    - Obtaining fresh token for API access

    **Notes:**
    - Credentials are checked against stored hash
    - Failed attempts are logged for security
    - Token should be stored securely in client (httpOnly cookie recommended)
    """
    try:
        user = await AuthService.login_user(session, email=credentials.email, password=credentials.password)
        return AuthService.create_token_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post(
    "/google-callback",
    summary="Handle Google OAuth callback",
    tags=["auth"],
    response_model=TokenResponse,
    responses={
        200: {"description": "Google auth successful", "model": TokenResponse},
        400: {"description": "Invalid OAuth code", "model": ErrorResponse},
        401: {"description": "Google auth failed", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def google_callback(
    code: str = Query(..., description="Authorization code from Google OAuth flow"),
    session: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """
    Complete Google OAuth login flow using authorization code.

    Exchanges Google authorization code for user credentials and returns JWT token.

    **Rate Limit:** 10 requests per hour

    **Authentication:** None (OAuth redirect endpoint)

    **Use Cases:**
    - Google Sign-In button callback
    - OAuth-based user authentication

    **Notes:**
    - Code must be valid and not expired
    - Automatically creates user account if first login
    - Requires valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
    """
    try:
        user = await AuthService.get_or_create_oauth_user(
            session,
            email=code,
            auth_provider="google",
        )
        return AuthService.create_token_response(user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/me",
    summary="Get current user information",
    tags=["auth"],
    response_model=UserResponse,
    responses={
        200: {"description": "Current user data", "model": UserResponse},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Retrieve information about the currently authenticated user.

    Used to verify token validity and get user profile details.

    **Rate Limit:** 60 requests per minute

    **Authentication:** Bearer token required

    **Use Cases:**
    - Verify user authentication on app startup
    - Refresh user profile in frontend
    - Check current user identity

    **Notes:**
    - Only accessible with valid, non-expired token
    - Hitting this endpoint confirms token is still valid
    """
    return current_user
