"""认证相关的API模式定义."""


from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """用户注册请求."""

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=100)


class LoginRequest(BaseModel):
    """用户登录请求."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """用户响应."""

    id: str
    username: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    status: str
    role: str
    is_active: bool
    created_at: str
    last_login_at: str | None = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """认证响应."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenResponse(BaseModel):
    """令牌响应."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UpdateUserRequest(BaseModel):
    """更新用户信息请求."""

    display_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)

