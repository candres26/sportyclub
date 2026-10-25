import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.clubs.models import Tenant
from app.modules.clubs.schemas import TenantCreate, TenantRead, TenantUpdate
from app.modules.disciplines import service as disciplines_service
from app.modules.invitations import service as invitations_service
from app.modules.rbac import service as rbac_service
from app.modules.rbac.catalog import OWNER_ROLE_NAME
from app.tenancy.security import set_tenant


async def list_tenants(session: AsyncSession) -> list[TenantRead]:
    tenants = (await session.scalars(select(Tenant).order_by(Tenant.name))).all()
    return [TenantRead.model_validate(tenant) for tenant in tenants]


async def get_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise NotFoundError("Club no encontrado")
    return tenant


async def create_tenant(
    session: AsyncSession, data: TenantCreate
) -> tuple[TenantRead, str | None]:
    existing = await session.scalar(select(Tenant).where(Tenant.slug == data.slug))
    if existing is not None:
        raise ConflictError("Ya existe un club con ese slug")

    tenant = Tenant(slug=data.slug, name=data.name, is_active=True)
    session.add(tenant)
    await session.flush()

    await set_tenant(session, tenant.id)
    await rbac_service.sync_permissions(session)
    roles = await rbac_service.create_default_roles(session, tenant.id)
    sport = data.sport.strip() if data.sport else None
    await disciplines_service.create_defaults(session, tenant.id, sport)

    raw_token: str | None = None
    if data.owner_email is not None:
        owner_role = roles[OWNER_ROLE_NAME]
        _invitation, raw_token = await invitations_service.create_invitation(
            session,
            tenant_id=tenant.id,
            email=str(data.owner_email),
            role_id=owner_role.id,
            invited_by_user_id=None,
        )

    await session.flush()
    return TenantRead.model_validate(tenant), raw_token


async def update_tenant(
    session: AsyncSession, tenant_id: uuid.UUID, data: TenantUpdate
) -> TenantRead:
    tenant = await get_tenant(session, tenant_id)
    if data.name is not None:
        tenant.name = data.name
    if data.is_active is not None:
        tenant.is_active = data.is_active
    await session.flush()
    return TenantRead.model_validate(tenant)
