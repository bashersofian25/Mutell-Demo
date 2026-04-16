from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserBrief"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class AcceptInviteRequest(BaseModel):
    token: str
    full_name: str
    password: str = Field(..., min_length=8)


class UserBrief(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str | None = None

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    tenant_slug: str | None = None


class GoogleAuthRequest(BaseModel):
    id_token: str
