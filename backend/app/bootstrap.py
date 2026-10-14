import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.modules.platform.models import PlatformAdmin
from app.modules.rbac import service as rbac_service

logger = logging.getLogger("sportyclub.bootstrap")


async def ensure_platform_admin(session: AsyncSession) -> None:
    email = settings.platform_admin_email.lower().strip()
    existing = await session.scalar(select(PlatformAdmin).where(PlatformAdmin.email == email))
    if existing is not None:
        return
    session.add(
        PlatformAdmin(
            email=email,
            full_name="Platform Admin",
            password_hash=hash_password(settings.platform_admin_password),
            is_active=True,
        )
    )
    await session.flush()
    logger.info("Superadmin de plataforma creado: %s", email)


async def bootstrap() -> None:
    async with async_session_factory() as session, session.begin():
        await rbac_service.sync_permissions(session)
        await ensure_platform_admin(session)
