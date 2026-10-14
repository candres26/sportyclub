import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.rbac.models import Role, UserRole
from app.modules.users.models import User
from app.modules.users.schemas import UserRead, UserUpdate


async def _user_role_names(session: AsyncSession, user_id: uuid.UUID) -> list[str]:
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .order_by(Role.name)
    )
    return list((await session.scalars(stmt)).all())


async def to_read(session: AsyncSession, user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        roles=await _user_role_names(session, user.id),
    )


async def list_users(session: AsyncSession) -> list[UserRead]:
    users = (await session.scalars(select(User).order_by(User.full_name))).all()
    return [await to_read(session, user) for user in users]


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")
    return user


async def update_user(session: AsyncSession, user_id: uuid.UUID, data: UserUpdate) -> UserRead:
    user = await get_user(session, user_id)
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.is_active is not None:
        user.is_active = data.is_active
    await session.flush()
    return await to_read(session, user)


async def set_user_roles(
    session: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, role_ids: list[uuid.UUID]
) -> UserRead:
    user = await get_user(session, user_id)

    if role_ids:
        found = (await session.scalars(select(Role.id).where(Role.id.in_(role_ids)))).all()
        missing = set(role_ids) - set(found)
        if missing:
            raise BadRequestError("Alguno de los roles no existe en el club")

    await session.execute(delete(UserRole).where(UserRole.user_id == user.id))
    for role_id in role_ids:
        session.add(UserRole(user_id=user.id, role_id=role_id, tenant_id=tenant_id))
    await session.flush()
    return await to_read(session, user)


async def delete_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    user = await get_user(session, user_id)
    await session.delete(user)
