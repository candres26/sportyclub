import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import TenantContext, get_tenant_context, require_permission
from app.modules.rbac import service
from app.modules.rbac.schemas import PermissionRead, RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/roles", tags=["roles"])

TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("roles:read"))],
) -> list[PermissionRead]:
    permissions = await service.list_permissions(ctx.session)
    return [PermissionRead.model_validate(p) for p in permissions]


@router.get("", response_model=list[RoleRead])
async def list_roles(
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("roles:read"))],
) -> list[RoleRead]:
    return await service.list_roles(ctx.session)


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("roles:create"))],
) -> RoleRead:
    return await service.create_role(ctx.session, ctx.tenant.id, payload)


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("roles:read"))],
) -> RoleRead:
    role = await service.get_role(ctx.session, role_id)
    return await service.role_to_read(ctx.session, role)


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("roles:update"))],
) -> RoleRead:
    return await service.update_role(ctx.session, role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("roles:delete"))],
) -> None:
    await service.delete_role(ctx.session, role_id)
