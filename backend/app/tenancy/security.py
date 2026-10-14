import uuid
from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.exceptions import TenantNotFoundError
from app.modules.clubs.models import Tenant
from app.tenancy.context import TenantContext


async def set_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Fija el tenant actual para las politicas RLS de la transaccion en curso."""
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def resolve_tenant_by_slug(session: AsyncSession, slug: str) -> Tenant | None:
    return await session.scalar(select(Tenant).where(Tenant.slug == slug))


async def get_tenant_context(request: Request) -> AsyncIterator[TenantContext]:
    slug = getattr(request.state, "tenant_slug", None)
    if not slug:
        raise TenantNotFoundError(
            "No se pudo determinar el club a partir del subdominio"
        )

    async with async_session_factory() as session, session.begin():
        tenant = await resolve_tenant_by_slug(session, slug)
        if tenant is None or not tenant.is_active:
            raise TenantNotFoundError()
        await set_tenant(session, tenant.id)
        yield TenantContext(tenant=tenant, session=session)
