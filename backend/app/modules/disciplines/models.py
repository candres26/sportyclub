import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Discipline(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Disciplina deportiva del club (p. ej. boxeo, natacion)."""

    __tablename__ = "disciplines"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_disciplines_tenant_name"),
        UniqueConstraint("tenant_id", "id", name="uq_disciplines_tenant_id_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )


class MetricDefinition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Medida de la ficha tecnica que el club registra (estatura, peso, alcance...)."""

    __tablename__ = "metric_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_metric_definitions_tenant_name"),
        UniqueConstraint("tenant_id", "id", name="uq_metric_definitions_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "discipline_id"],
            ["disciplines.tenant_id", "disciplines.id"],
            name="fk_metric_definitions_discipline_tenant",
            # Solo anula discipline_id (PostgreSQL 15+); tenant_id es NOT NULL.
            ondelete="SET NULL (discipline_id)",
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    # Sin disciplina = aplica a todos los deportistas del club.
    discipline_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
