import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.pagination import Page, PageParams
from app.modules.disciplines.models import MetricDefinition
from app.modules.people.models import (
    AthleteMeasurement,
    AthleteProfile,
    Guardianship,
    Person,
)
from app.modules.people.schemas import (
    AthleteProfileFields,
    AthleteProfileRead,
    MeasurementCreate,
    MeasurementRead,
    PersonCreate,
    PersonRead,
    PersonUpdate,
    RelatedPersonRead,
)


# --------------------------------------------------------------------------- #
# Personas
# --------------------------------------------------------------------------- #
async def list_people(
    session: AsyncSession, page: PageParams, q: str | None, is_active: bool | None
) -> Page[PersonRead]:
    stmt = select(Person)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                func.concat(Person.first_name, " ", Person.last_name).ilike(pattern),
                Person.document_number.ilike(pattern),
            )
        )
    if is_active is not None:
        stmt = stmt.where(Person.is_active.is_(is_active))

    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    people = (
        await session.scalars(
            stmt.order_by(Person.last_name, Person.first_name).limit(page.limit).offset(page.offset)
        )
    ).all()
    return Page[PersonRead](
        items=[PersonRead.model_validate(p) for p in people],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


async def get_person(session: AsyncSession, person_id: uuid.UUID) -> Person:
    person = await session.get(Person, person_id)
    if person is None:
        raise NotFoundError("Persona no encontrada")
    return person


async def _ensure_document_free(
    session: AsyncSession, document_number: str | None, exclude_id: uuid.UUID | None = None
) -> None:
    if document_number is None:
        return
    stmt = select(Person.id).where(Person.document_number == document_number)
    if exclude_id is not None:
        stmt = stmt.where(Person.id != exclude_id)
    if await session.scalar(stmt) is not None:
        raise ConflictError("Ya existe una persona con ese numero de documento en el club")


async def create_person(session: AsyncSession, tenant_id: uuid.UUID, data: PersonCreate) -> Person:
    await _ensure_document_free(session, data.document_number)
    values = data.model_dump()
    if values["email"] is not None:
        values["email"] = values["email"].lower()
    person = Person(tenant_id=tenant_id, **values)
    session.add(person)
    await session.flush()
    return person


async def update_person(
    session: AsyncSession, person_id: uuid.UUID, data: PersonUpdate
) -> Person:
    person = await get_person(session, person_id)
    changes = data.model_dump(exclude_unset=True)
    for required in ("first_name", "last_name", "is_active"):
        if changes.get(required, "") is None:
            raise BadRequestError(f"El campo {required} no puede quedar vacio")
    if "document_number" in changes:
        await _ensure_document_free(session, changes["document_number"], exclude_id=person.id)
    if changes.get("email") is not None:
        changes["email"] = changes["email"].lower()
    for field, value in changes.items():
        setattr(person, field, value)
    await session.flush()
    return person


async def delete_person(session: AsyncSession, person_id: uuid.UUID) -> None:
    person = await get_person(session, person_id)
    await session.delete(person)
    await session.flush()


# --------------------------------------------------------------------------- #
# Acudientes y deportistas a cargo
# --------------------------------------------------------------------------- #
async def list_guardians(session: AsyncSession, athlete_id: uuid.UUID) -> list[RelatedPersonRead]:
    await get_person(session, athlete_id)
    rows = (
        await session.execute(
            select(Guardianship.relation, Person)
            .join(Person, Person.id == Guardianship.guardian_id)
            .where(Guardianship.athlete_id == athlete_id)
            .order_by(Person.last_name, Person.first_name)
        )
    ).all()
    return [
        RelatedPersonRead(relation=relation, person=PersonRead.model_validate(person))
        for relation, person in rows
    ]


async def list_dependents(
    session: AsyncSession, guardian_id: uuid.UUID
) -> list[RelatedPersonRead]:
    await get_person(session, guardian_id)
    rows = (
        await session.execute(
            select(Guardianship.relation, Person)
            .join(Person, Person.id == Guardianship.athlete_id)
            .where(Guardianship.guardian_id == guardian_id)
            .order_by(Person.last_name, Person.first_name)
        )
    ).all()
    return [
        RelatedPersonRead(relation=relation, person=PersonRead.model_validate(person))
        for relation, person in rows
    ]


async def add_guardian(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    athlete_id: uuid.UUID,
    guardian_id: uuid.UUID,
    relation: str,
) -> RelatedPersonRead:
    if athlete_id == guardian_id:
        raise BadRequestError("Una persona no puede ser su propio acudiente")
    await get_person(session, athlete_id)
    guardian = await get_person(session, guardian_id)

    existing = await session.get(Guardianship, (guardian_id, athlete_id))
    if existing is not None:
        raise ConflictError("Esa persona ya es acudiente de este deportista")

    session.add(
        Guardianship(
            tenant_id=tenant_id,
            guardian_id=guardian_id,
            athlete_id=athlete_id,
            relation=relation.strip(),
        )
    )
    await session.flush()
    return RelatedPersonRead(relation=relation.strip(), person=PersonRead.model_validate(guardian))


async def remove_guardian(
    session: AsyncSession, athlete_id: uuid.UUID, guardian_id: uuid.UUID
) -> None:
    link = await session.get(Guardianship, (guardian_id, athlete_id))
    if link is None:
        raise NotFoundError("Esa persona no es acudiente de este deportista")
    await session.delete(link)
    await session.flush()


# --------------------------------------------------------------------------- #
# Ficha tecnica
# --------------------------------------------------------------------------- #
async def get_profile(session: AsyncSession, person_id: uuid.UUID) -> AthleteProfileRead:
    await get_person(session, person_id)
    profile = await session.get(AthleteProfile, person_id)
    if profile is None:
        return AthleteProfileRead(person_id=person_id)
    return AthleteProfileRead.model_validate(profile, from_attributes=True)


async def upsert_profile(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    person_id: uuid.UUID,
    data: AthleteProfileFields,
) -> AthleteProfileRead:
    await get_person(session, person_id)
    profile = await session.get(AthleteProfile, person_id)
    if profile is None:
        profile = AthleteProfile(tenant_id=tenant_id, person_id=person_id)
        session.add(profile)
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    await session.flush()
    await session.refresh(profile)
    return AthleteProfileRead.model_validate(profile, from_attributes=True)


async def list_measurements(
    session: AsyncSession, person_id: uuid.UUID, metric_id: uuid.UUID | None
) -> list[MeasurementRead]:
    await get_person(session, person_id)
    stmt = (
        select(AthleteMeasurement, MetricDefinition)
        .join(MetricDefinition, MetricDefinition.id == AthleteMeasurement.metric_id)
        .where(AthleteMeasurement.person_id == person_id)
        .order_by(AthleteMeasurement.measured_at.desc(), AthleteMeasurement.created_at.desc())
    )
    if metric_id is not None:
        stmt = stmt.where(AthleteMeasurement.metric_id == metric_id)
    rows = (await session.execute(stmt)).all()
    return [_measurement_read(m, metric) for m, metric in rows]


def _measurement_read(
    measurement: AthleteMeasurement, metric: MetricDefinition
) -> MeasurementRead:
    return MeasurementRead(
        id=measurement.id,
        metric_id=metric.id,
        metric_name=metric.name,
        unit=metric.unit,
        value=measurement.value,
        measured_at=measurement.measured_at,
        recorded_by_user_id=measurement.recorded_by_user_id,
        created_at=measurement.created_at,
    )


async def add_measurement(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    person_id: uuid.UUID,
    data: MeasurementCreate,
    recorded_by_user_id: uuid.UUID,
) -> MeasurementRead:
    await get_person(session, person_id)
    metric = await session.get(MetricDefinition, data.metric_id)
    if metric is None:
        raise NotFoundError("Metrica no encontrada")
    if not metric.is_active:
        raise BadRequestError("La metrica esta desactivada")

    measurement = AthleteMeasurement(
        tenant_id=tenant_id,
        person_id=person_id,
        metric_id=metric.id,
        value=data.value,
        measured_at=data.measured_at,
        recorded_by_user_id=recorded_by_user_id,
    )
    session.add(measurement)
    await session.flush()
    await session.refresh(measurement)
    return _measurement_read(measurement, metric)


async def delete_measurement(
    session: AsyncSession, person_id: uuid.UUID, measurement_id: uuid.UUID
) -> None:
    measurement = await session.get(AthleteMeasurement, measurement_id)
    if measurement is None or measurement.person_id != person_id:
        raise NotFoundError("Medicion no encontrada")
    await session.delete(measurement)
    await session.flush()
