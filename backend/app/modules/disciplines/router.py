import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import TenantContext, get_tenant_context, require_permission
from app.modules.disciplines import service
from app.modules.disciplines.schemas import (
    DisciplineCreate,
    DisciplineRead,
    DisciplineUpdate,
    MetricCreate,
    MetricRead,
    MetricUpdate,
)

router = APIRouter(tags=["disciplines"])

TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]


@router.get("/disciplines", response_model=list[DisciplineRead])
async def list_disciplines(
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("club:read"))],
) -> list[DisciplineRead]:
    disciplines = await service.list_disciplines(ctx.session)
    return [DisciplineRead.model_validate(d) for d in disciplines]


@router.post(
    "/disciplines", response_model=DisciplineRead, status_code=status.HTTP_201_CREATED
)
async def create_discipline(
    payload: DisciplineCreate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("disciplines:manage"))],
) -> DisciplineRead:
    discipline = await service.create_discipline(ctx.session, ctx.tenant.id, payload)
    return DisciplineRead.model_validate(discipline)


@router.patch("/disciplines/{discipline_id}", response_model=DisciplineRead)
async def update_discipline(
    discipline_id: uuid.UUID,
    payload: DisciplineUpdate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("disciplines:manage"))],
) -> DisciplineRead:
    discipline = await service.update_discipline(ctx.session, discipline_id, payload)
    return DisciplineRead.model_validate(discipline)


@router.get("/metrics", response_model=list[MetricRead])
async def list_metrics(
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("athletes:read"))],
    include_inactive: bool = Query(False),
) -> list[MetricRead]:
    metrics = await service.list_metrics(ctx.session, include_inactive)
    return [MetricRead.model_validate(m) for m in metrics]


@router.post("/metrics", response_model=MetricRead, status_code=status.HTTP_201_CREATED)
async def create_metric(
    payload: MetricCreate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("disciplines:manage"))],
) -> MetricRead:
    metric = await service.create_metric(ctx.session, ctx.tenant.id, payload)
    return MetricRead.model_validate(metric)


@router.patch("/metrics/{metric_id}", response_model=MetricRead)
async def update_metric(
    metric_id: uuid.UUID,
    payload: MetricUpdate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("disciplines:manage"))],
) -> MetricRead:
    metric = await service.update_metric(ctx.session, metric_id, payload)
    return MetricRead.model_validate(metric)
