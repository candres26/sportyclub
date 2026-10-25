import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import TenantContext, get_tenant_context, require_permission
from app.core.pagination import Page, PageParams, page_params
from app.modules.audit import service as audit_service
from app.modules.people import service
from app.modules.people.schemas import (
    AthleteProfileFields,
    AthleteProfileRead,
    GuardianLinkCreate,
    MeasurementCreate,
    MeasurementRead,
    PersonCreate,
    PersonRead,
    PersonUpdate,
    RelatedPersonRead,
)
from app.modules.users.models import User

router = APIRouter(prefix="/people", tags=["people"])

TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]
PageDep = Annotated[PageParams, Depends(page_params)]


async def _audit(
    ctx: TenantContext,
    user: User,
    action: str,
    entity_id: uuid.UUID,
    data: dict | None = None,
) -> None:
    await audit_service.record(
        ctx.session,
        tenant_id=ctx.tenant.id,
        actor_type="user",
        actor_id=user.id,
        action=action,
        entity_type="person",
        entity_id=str(entity_id),
        data=data,
    )


# --------------------------------------------------------------------------- #
# Personas
# --------------------------------------------------------------------------- #
@router.get("", response_model=Page[PersonRead])
async def list_people(
    ctx: TenantDep,
    page: PageDep,
    _: Annotated[object, Depends(require_permission("people:read"))],
    q: str | None = Query(None, max_length=100),
    is_active: bool | None = Query(None),
) -> Page[PersonRead]:
    return await service.list_people(ctx.session, page, q, is_active)


@router.post("", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: PersonCreate,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("people:create"))],
) -> PersonRead:
    person = await service.create_person(ctx.session, ctx.tenant.id, payload)
    await _audit(
        ctx,
        current_user,
        "person.create",
        person.id,
        {"name": f"{person.first_name} {person.last_name}"},
    )
    return PersonRead.model_validate(person)


@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("people:read"))],
) -> PersonRead:
    return PersonRead.model_validate(await service.get_person(ctx.session, person_id))


@router.patch("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: uuid.UUID,
    payload: PersonUpdate,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("people:update"))],
) -> PersonRead:
    person = await service.update_person(ctx.session, person_id, payload)
    await _audit(
        ctx,
        current_user,
        "person.update",
        person.id,
        {"fields": sorted(payload.model_fields_set)},
    )
    return PersonRead.model_validate(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: uuid.UUID,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("people:delete"))],
) -> None:
    await service.delete_person(ctx.session, person_id)
    await _audit(ctx, current_user, "person.delete", person_id)


# --------------------------------------------------------------------------- #
# Acudientes y deportistas a cargo
# --------------------------------------------------------------------------- #
@router.get("/{person_id}/guardians", response_model=list[RelatedPersonRead])
async def list_guardians(
    person_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("people:read"))],
) -> list[RelatedPersonRead]:
    return await service.list_guardians(ctx.session, person_id)


@router.post(
    "/{person_id}/guardians",
    response_model=RelatedPersonRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_guardian(
    person_id: uuid.UUID,
    payload: GuardianLinkCreate,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("people:update"))],
) -> RelatedPersonRead:
    link = await service.add_guardian(
        ctx.session, ctx.tenant.id, person_id, payload.guardian_id, payload.relation
    )
    await _audit(
        ctx,
        current_user,
        "guardian.add",
        person_id,
        {"guardian_id": str(payload.guardian_id), "relation": link.relation},
    )
    return link


@router.delete(
    "/{person_id}/guardians/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_guardian(
    person_id: uuid.UUID,
    guardian_id: uuid.UUID,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("people:update"))],
) -> None:
    await service.remove_guardian(ctx.session, person_id, guardian_id)
    await _audit(
        ctx, current_user, "guardian.remove", person_id, {"guardian_id": str(guardian_id)}
    )


@router.get("/{person_id}/dependents", response_model=list[RelatedPersonRead])
async def list_dependents(
    person_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("people:read"))],
) -> list[RelatedPersonRead]:
    return await service.list_dependents(ctx.session, person_id)


# --------------------------------------------------------------------------- #
# Ficha tecnica
# --------------------------------------------------------------------------- #
@router.get("/{person_id}/profile", response_model=AthleteProfileRead)
async def get_profile(
    person_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("athletes:read"))],
) -> AthleteProfileRead:
    return await service.get_profile(ctx.session, person_id)


@router.put("/{person_id}/profile", response_model=AthleteProfileRead)
async def upsert_profile(
    person_id: uuid.UUID,
    payload: AthleteProfileFields,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("athletes:update"))],
) -> AthleteProfileRead:
    return await service.upsert_profile(ctx.session, ctx.tenant.id, person_id, payload)


@router.get("/{person_id}/measurements", response_model=list[MeasurementRead])
async def list_measurements(
    person_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("athletes:read"))],
    metric_id: uuid.UUID | None = Query(None),
) -> list[MeasurementRead]:
    return await service.list_measurements(ctx.session, person_id, metric_id)


@router.post(
    "/{person_id}/measurements",
    response_model=MeasurementRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_measurement(
    person_id: uuid.UUID,
    payload: MeasurementCreate,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("athletes:update"))],
) -> MeasurementRead:
    return await service.add_measurement(
        ctx.session, ctx.tenant.id, person_id, payload, current_user.id
    )


@router.delete(
    "/{person_id}/measurements/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_measurement(
    person_id: uuid.UUID,
    measurement_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("athletes:update"))],
) -> None:
    await service.delete_measurement(ctx.session, person_id, measurement_id)
