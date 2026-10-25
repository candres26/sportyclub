import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.disciplines.models import Discipline, MetricDefinition
from app.modules.disciplines.schemas import (
    DisciplineCreate,
    DisciplineUpdate,
    MetricCreate,
    MetricUpdate,
)

DEFAULT_DISCIPLINE_NAME = "General"
DEFAULT_METRICS: tuple[tuple[str, str], ...] = (
    ("Estatura", "cm"),
    ("Peso", "kg"),
    ("Alcance", "cm"),
)


async def create_defaults(
    session: AsyncSession, tenant_id: uuid.UUID, sport: str | None
) -> None:
    """Disciplina inicial y metricas basicas de la ficha tecnica de un club nuevo."""
    session.add(Discipline(tenant_id=tenant_id, name=sport or DEFAULT_DISCIPLINE_NAME))
    for name, unit in DEFAULT_METRICS:
        session.add(MetricDefinition(tenant_id=tenant_id, name=name, unit=unit))
    await session.flush()


# --------------------------------------------------------------------------- #
# Disciplinas
# --------------------------------------------------------------------------- #
async def list_disciplines(session: AsyncSession) -> list[Discipline]:
    return list((await session.scalars(select(Discipline).order_by(Discipline.name))).all())


async def get_discipline(session: AsyncSession, discipline_id: uuid.UUID) -> Discipline:
    discipline = await session.get(Discipline, discipline_id)
    if discipline is None:
        raise NotFoundError("Disciplina no encontrada")
    return discipline


async def _ensure_discipline_name_free(
    session: AsyncSession, name: str, exclude_id: uuid.UUID | None = None
) -> None:
    stmt = select(Discipline.id).where(Discipline.name == name)
    if exclude_id is not None:
        stmt = stmt.where(Discipline.id != exclude_id)
    if await session.scalar(stmt) is not None:
        raise ConflictError("Ya existe una disciplina con ese nombre")


async def create_discipline(
    session: AsyncSession, tenant_id: uuid.UUID, data: DisciplineCreate
) -> Discipline:
    name = data.name.strip()
    await _ensure_discipline_name_free(session, name)
    discipline = Discipline(tenant_id=tenant_id, name=name)
    session.add(discipline)
    await session.flush()
    return discipline


async def update_discipline(
    session: AsyncSession, discipline_id: uuid.UUID, data: DisciplineUpdate
) -> Discipline:
    discipline = await get_discipline(session, discipline_id)
    if data.name is not None:
        name = data.name.strip()
        await _ensure_discipline_name_free(session, name, exclude_id=discipline.id)
        discipline.name = name
    if data.is_active is not None:
        discipline.is_active = data.is_active
    await session.flush()
    return discipline


# --------------------------------------------------------------------------- #
# Metricas de la ficha tecnica
# --------------------------------------------------------------------------- #
async def list_metrics(session: AsyncSession, include_inactive: bool) -> list[MetricDefinition]:
    stmt = select(MetricDefinition).order_by(MetricDefinition.name)
    if not include_inactive:
        stmt = stmt.where(MetricDefinition.is_active.is_(True))
    return list((await session.scalars(stmt)).all())


async def get_metric(session: AsyncSession, metric_id: uuid.UUID) -> MetricDefinition:
    metric = await session.get(MetricDefinition, metric_id)
    if metric is None:
        raise NotFoundError("Metrica no encontrada")
    return metric


async def _ensure_metric_name_free(
    session: AsyncSession, name: str, exclude_id: uuid.UUID | None = None
) -> None:
    stmt = select(MetricDefinition.id).where(MetricDefinition.name == name)
    if exclude_id is not None:
        stmt = stmt.where(MetricDefinition.id != exclude_id)
    if await session.scalar(stmt) is not None:
        raise ConflictError("Ya existe una metrica con ese nombre")


async def create_metric(
    session: AsyncSession, tenant_id: uuid.UUID, data: MetricCreate
) -> MetricDefinition:
    name = data.name.strip()
    await _ensure_metric_name_free(session, name)
    if data.discipline_id is not None:
        await get_discipline(session, data.discipline_id)
    metric = MetricDefinition(
        tenant_id=tenant_id, name=name, unit=data.unit.strip(), discipline_id=data.discipline_id
    )
    session.add(metric)
    await session.flush()
    return metric


async def update_metric(
    session: AsyncSession, metric_id: uuid.UUID, data: MetricUpdate
) -> MetricDefinition:
    metric = await get_metric(session, metric_id)
    if data.name is not None:
        name = data.name.strip()
        await _ensure_metric_name_free(session, name, exclude_id=metric.id)
        metric.name = name
    if data.unit is not None:
        metric.unit = data.unit.strip()
    if "discipline_id" in data.model_fields_set:
        if data.discipline_id is not None:
            await get_discipline(session, data.discipline_id)
        metric.discipline_id = data.discipline_id
    if data.is_active is not None:
        metric.is_active = data.is_active
    await session.flush()
    return metric
