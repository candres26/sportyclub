import uuid

from pydantic import BaseModel, ConfigDict, Field


class DisciplineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DisciplineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class DisciplineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_active: bool


class MetricCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    unit: str = Field(min_length=1, max_length=20)
    discipline_id: uuid.UUID | None = None


class MetricUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    discipline_id: uuid.UUID | None = None
    is_active: bool | None = None


class MetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    unit: str
    discipline_id: uuid.UUID | None
    is_active: bool
