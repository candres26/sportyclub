import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")
RESERVED_SLUGS = {"www", "api", "app", "admin", "static", "assets", "mail"}


class TenantCreate(BaseModel):
    name: str
    slug: str
    owner_email: EmailStr | None = None
    owner_full_name: str | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        value = value.lower().strip()
        if not SLUG_PATTERN.match(value):
            raise ValueError(
                "El slug debe tener entre 3 y 63 caracteres, minusculas, numeros y guiones"
            )
        if value in RESERVED_SLUGS:
            raise ValueError("Ese slug esta reservado")
        return value


class TenantUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    is_active: bool
    created_at: datetime


class ClubCreatedRead(TenantRead):
    invite_url: str | None = None
