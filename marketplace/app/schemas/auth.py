from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str  # user_id
    exp: int
    type: str = "access"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None
    is_active: bool
    is_admin: bool
    created_at: str

    class Config:
        from_attributes = True