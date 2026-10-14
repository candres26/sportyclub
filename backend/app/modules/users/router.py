import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import TenantContext, get_tenant_context, require_permission
from app.modules.users import service
from app.modules.users.schemas import UserRead, UserRolesUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]


@router.get("", response_model=list[UserRead])
async def list_users(
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("users:read"))],
) -> list[UserRead]:
    return await service.list_users(ctx.session)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("users:read"))],
) -> UserRead:
    user = await service.get_user(ctx.session, user_id)
    return await service.to_read(ctx.session, user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("users:update"))],
) -> UserRead:
    return await service.update_user(ctx.session, user_id, payload)


@router.put("/{user_id}/roles", response_model=UserRead)
async def set_user_roles(
    user_id: uuid.UUID,
    payload: UserRolesUpdate,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("users:update"))],
) -> UserRead:
    return await service.set_user_roles(ctx.session, ctx.tenant.id, user_id, payload.role_ids)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("users:delete"))],
) -> None:
    await service.delete_user(ctx.session, user_id)
