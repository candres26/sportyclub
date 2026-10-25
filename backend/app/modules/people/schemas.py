import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator


def _blank_to_none(value: object) -> object:
    """Los formularios envian "" en campos vacios: se guardan como NULL."""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def age_on(birth_date: date | None, today: date | None = None) -> int | None:
    if birth_date is None:
        return None
    today = today or date.today()
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)


class _PersonFields(BaseModel):
    document_type: str | None = Field(default=None, max_length=20)
    document_number: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    gender: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    emergency_contact_name: str | None = Field(default=None, max_length=150)
    emergency_contact_phone: str | None = Field(default=None, max_length=30)
    notes: str | None = None

    @field_validator(
        "document_type",
        "document_number",
        "gender",
        "email",
        "phone",
        "address",
        "emergency_contact_name",
        "emergency_contact_phone",
        "notes",
        "birth_date",
        mode="before",
    )
    @classmethod
    def _optional_blank(cls, value: object) -> object:
        return _blank_to_none(value)


class PersonCreate(_PersonFields):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class PersonUpdate(_PersonFields):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    document_type: str | None
    document_number: str | None
    birth_date: date | None
    gender: str | None
    email: str | None
    phone: str | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    notes: str | None
    is_active: bool
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def age(self) -> int | None:
        return age_on(self.birth_date)


class GuardianLinkCreate(BaseModel):
    guardian_id: uuid.UUID
    relation: str = Field(min_length=1, max_length=30)


class RelatedPersonRead(BaseModel):
    """Acudiente o deportista a cargo, con el parentesco de la relacion."""

    relation: str
    person: PersonRead


class AthleteProfileFields(BaseModel):
    blood_type: str | None = Field(default=None, max_length=5)
    insurance: str | None = Field(default=None, max_length=150)
    allergies: str | None = None
    medical_notes: str | None = None
    dominant_side: str | None = Field(default=None, max_length=20)

    @field_validator("*", mode="before")
    @classmethod
    def _optional_blank(cls, value: object) -> object:
        return _blank_to_none(value)


class AthleteProfileRead(AthleteProfileFields):
    person_id: uuid.UUID
    updated_at: datetime | None = None


class MeasurementCreate(BaseModel):
    metric_id: uuid.UUID
    value: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    measured_at: date


class MeasurementRead(BaseModel):
    id: uuid.UUID
    metric_id: uuid.UUID
    metric_name: str
    unit: str
    value: Decimal
    measured_at: date
    recorded_by_user_id: uuid.UUID | None
    created_at: datetime
