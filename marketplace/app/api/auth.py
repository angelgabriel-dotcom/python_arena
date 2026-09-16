from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    try:
        token = await auth_service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    response = Response(content=token.model_dump_json())
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token.access_token}",
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=15 * 60,  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )
    return response


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    try:
        token = await auth_service.login(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    response.set_cookie(
        key="access_token",
        value=f"Bearer {token.access_token}",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=15 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return token


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at.isoformat(),
    )