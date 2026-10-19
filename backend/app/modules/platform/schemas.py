import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PlatformAdminCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class PlatformAdminUpdate(BaseModel):
    is_active: bool | None = None


class PlatformAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
