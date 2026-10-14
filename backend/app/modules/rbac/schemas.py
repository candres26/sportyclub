import uuid

from pydantic import BaseModel, ConfigDict


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    description: str | None = None


class RoleRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    is_system: bool
    permissions: list[str] = []


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None
