import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Person(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persona del club: deportista, acudiente o ambos a la vez."""

    __tablename__ = "people"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_people_tenant_id_id"),
        Index(
            "uq_people_tenant_document",
            "tenant_id",
            "document_number",
            unique=True,
            postgresql_where=text("document_number IS NOT NULL"),
        ),
        Index("ix_people_tenant_last_name", "tenant_id", "last_name"),
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_people_user_tenant",
            ondelete="SET NULL (user_id)",
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    # Cuenta de acceso opcional (portal de padres o deportistas en el futuro).
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)


class Guardianship(TimestampMixin, Base):
    """Acudiente (`guardian`) responsable de un deportista (`athlete`)."""

    __tablename__ = "guardianships"
    __table_args__ = (
        CheckConstraint("guardian_id <> athlete_id", name="ck_guardianships_not_self"),
        ForeignKeyConstraint(
            ["tenant_id", "guardian_id"],
            ["people.tenant_id", "people.id"],
            name="fk_guardianships_guardian_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "athlete_id"],
            ["people.tenant_id", "people.id"],
            name="fk_guardianships_athlete_tenant",
            ondelete="CASCADE",
        ),
    )

    guardian_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    athlete_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # padre, madre, tutor, abuelo...
    relation: Mapped[str] = mapped_column(String(30), nullable=False)


class AthleteProfile(TimestampMixin, Base):
    """Datos fijos de la ficha tecnica de un deportista (1 por persona)."""

    __tablename__ = "athlete_profiles"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            name="fk_athlete_profiles_person_tenant",
            ondelete="CASCADE",
        ),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    blood_type: Mapped[str | None] = mapped_column(String(5), nullable=True)
    insurance: Mapped[str | None] = mapped_column(String(150), nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    dominant_side: Mapped[str | None] = mapped_column(String(20), nullable=True)


class AthleteMeasurement(UUIDPrimaryKeyMixin, Base):
    """Una toma de una metrica de la ficha tecnica en una fecha."""

    __tablename__ = "athlete_measurements"
    __table_args__ = (
        Index("ix_athlete_measurements_person_date", "tenant_id", "person_id", "measured_at"),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            name="fk_athlete_measurements_person_tenant",
            ondelete="CASCADE",
        ),
        # RESTRICT: una metrica con historial se desactiva, no se borra.
        ForeignKeyConstraint(
            ["tenant_id", "metric_id"],
            ["metric_definitions.tenant_id", "metric_definitions.id"],
            name="fk_athlete_measurements_metric_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "recorded_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_athlete_measurements_recorded_by_tenant",
            ondelete="SET NULL (recorded_by_user_id)",
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    person_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    metric_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    measured_at: Mapped[date] = mapped_column(Date, nullable=False)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
