from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User, Wallet
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegister) -> Token:
        # Check if user exists
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
        )
        self.db.add(user)
        await self.db.flush()

        # Create wallet for user
        wallet = Wallet(user_id=user.id)
        self.db.add(wallet)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Email already registered")

        await self.db.refresh(user)
        await self.db.refresh(wallet)

        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def login(self, data: UserLogin) -> Token:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at.isoformat(),
        )