import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class InvitationCreate(BaseModel):
    email: EmailStr
    role_id: uuid.UUID


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role_id: uuid.UUID
    role_name: str | None = None
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime
