import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    last_login_at: datetime | None = None
    roles: list[str] = []


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None


class UserRolesUpdate(BaseModel):
    role_ids: list[uuid.UUID]
