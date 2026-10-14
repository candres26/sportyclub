import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.modules.platform.models import PlatformAdmin
from app.modules.rbac.models import Permission, Role, RolePermission, UserRole
from app.modules.users.models import User
from app.tenancy.context import TenantContext
from app.tenancy.security import get_tenant_context


async def get_bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        raise UnauthorizedError("Falta el token de acceso")
    return header[7:].strip()


def _subject_uuid(payload: dict[str, Any]) -> uuid.UUID:
    try:
        return uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Token invalido") from exc


async def get_current_user(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    token: Annotated[str, Depends(get_bearer_token)],
) -> User:
    payload = decode_token(token, "access")
    if payload.get("scope") != "tenant" or payload.get("tenant_id") != str(ctx.tenant.id):
        raise UnauthorizedError("Token no pertenece a este club")

    user = await ctx.session.get(User, _subject_uuid(payload))
    if user is None or not user.is_active:
        raise UnauthorizedError("Usuario inactivo o inexistente")
    return user


async def get_current_platform_admin(
    session: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(get_bearer_token)],
) -> PlatformAdmin:
    payload = decode_token(token, "access")
    if payload.get("scope") != "platform":
        raise UnauthorizedError("Token no es de plataforma")

    admin = await session.get(PlatformAdmin, _subject_uuid(payload))
    if admin is None or not admin.is_active:
        raise UnauthorizedError("Administrador inactivo o inexistente")
    return admin


async def get_user_permission_codes(session: AsyncSession, user_id: uuid.UUID) -> set[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    result = await session.scalars(stmt)
    return set(result.all())


def require_permission(
    *codes: str,
) -> Callable[..., Coroutine[Any, Any, User]]:
    async def dependency(
        ctx: Annotated[TenantContext, Depends(get_tenant_context)],
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        permissions = await get_user_permission_codes(ctx.session, user.id)
        missing = set(codes) - permissions
        if missing:
            raise ForbiddenError(
                f"Faltan permisos requeridos: {', '.join(sorted(missing))}"
            )
        return user

    return dependency
