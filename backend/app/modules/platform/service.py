import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.platform.models import PlatformAdmin
from app.modules.platform.schemas import (
    PlatformAdminCreate,
    PlatformAdminRead,
    PlatformAdminUpdate,
)


async def list_admins(session: AsyncSession) -> list[PlatformAdminRead]:
    admins = (
        await session.scalars(select(PlatformAdmin).order_by(PlatformAdmin.created_at))
    ).all()
    return [PlatformAdminRead.model_validate(admin) for admin in admins]


async def create_admin(
    session: AsyncSession, data: PlatformAdminCreate
) -> PlatformAdminRead:
    email = str(data.email).lower().strip()
    existing = await session.scalar(
        select(PlatformAdmin).where(PlatformAdmin.email == email)
    )
    if existing is not None:
        raise ConflictError("Ya existe un administrador con ese correo")

    admin = PlatformAdmin(
        email=email,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    return PlatformAdminRead.model_validate(admin)


async def update_admin(
    session: AsyncSession,
    admin_id: uuid.UUID,
    data: PlatformAdminUpdate,
    actor_id: uuid.UUID,
) -> PlatformAdminRead:
    admin = await session.get(PlatformAdmin, admin_id)
    if admin is None:
        raise NotFoundError("Administrador no encontrado")

    if data.is_active is not None and data.is_active != admin.is_active:
        if not data.is_active:
            if admin.id == actor_id:
                raise BadRequestError("No puedes desactivar tu propia cuenta")
            # Bloquea las filas activas para que dos desactivaciones concurrentes
            # no dejen la plataforma sin administradores.
            active_ids = (
                await session.scalars(
                    select(PlatformAdmin.id)
                    .where(PlatformAdmin.is_active.is_(True))
                    .with_for_update()
                )
            ).all()
            if len(active_ids) <= 1:
                raise BadRequestError(
                    "No se puede desactivar al ultimo administrador activo"
                )
        admin.is_active = data.is_active

    await session.flush()
    return PlatformAdminRead.model_validate(admin)
