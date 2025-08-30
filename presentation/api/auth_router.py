from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from application.use_cases.auth_use_cases import AuthUseCases
from application.dto.user_dto import UserCreateDTO, UserLoginDTO, TokenRefreshDTO, TokenResponseDTO, UserResponseDTO
from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from infrastructure.auth.password_service import password_service
from infrastructure.auth.jwt_service import jwt_service
from infrastructure.database.base import get_session
from presentation.middleware.auth import get_current_active_user
from domain.entities.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_use_cases(session: AsyncSession = Depends(get_session)) -> AuthUseCases:
    """Dependency to get auth use cases"""
    user_repository = UserRepositoryImpl(session)
    return AuthUseCases(user_repository, password_service, jwt_service)


@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def sign_up(
    user_data: UserCreateDTO,
    auth_use_cases: AuthUseCases = Depends(get_auth_use_cases)
):
    """Register a new user"""
    try:
        result = await auth_use_cases.register_user(user_data)
        return {
            "message": "User registered successfully",
            "user": result["user"],
            "tokens": result["tokens"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


@router.post("/login", response_model=dict)
async def login(
    login_data: UserLoginDTO,
    auth_use_cases: AuthUseCases = Depends(get_auth_use_cases)
):
    """Login user and return tokens"""
    try:
        result = await auth_use_cases.login_user(login_data)
        return {
            "message": "Login successful",
            "user": result["user"],
            "tokens": result["tokens"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/refresh", response_model=TokenResponseDTO)
async def refresh_token(
    token_data: TokenRefreshDTO,
    auth_use_cases: AuthUseCases = Depends(get_auth_use_cases)
):
    """Refresh access token"""
    try:
        tokens = await auth_use_cases.refresh_token(token_data.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@router.post("/logout")
async def logout():
    """Logout user (client should discard tokens)"""
    return {"message": "Logout successful. Please discard your tokens."}


@router.get("/me", response_model=UserResponseDTO)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponseDTO(
        id=str(current_user.id),
        email=str(current_user.email),
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )