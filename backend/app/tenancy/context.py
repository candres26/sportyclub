from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clubs.models import Tenant


@dataclass
class TenantContext:
    tenant: Tenant
    session: AsyncSession
