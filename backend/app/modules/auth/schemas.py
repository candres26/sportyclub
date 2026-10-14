import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class AcceptInvitationRequest(BaseModel):
    token: str
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class TenantSummary(BaseModel):
    id: uuid.UUID
    slug: str
    name: str


class MeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    roles: list[str]
    tenant: TenantSummary


class PlatformMeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
