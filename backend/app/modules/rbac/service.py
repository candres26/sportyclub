import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_permission_codes
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.modules.clubs.models import Tenant
from app.modules.rbac.catalog import DEFAULT_ROLES, OWNER_ROLE_NAME, PERMISSIONS
from app.modules.rbac.models import Permission, Role, RolePermission, UserRole
from app.modules.rbac.schemas import RoleCreate, RoleRead, RoleUpdate
from app.modules.users.models import User
from app.tenancy.security import set_tenant


async def sync_permissions(session: AsyncSession) -> None:
    """Inserta/actualiza el catalogo global de permisos (idempotente)."""
    existing = {p.code: p for p in (await session.scalars(select(Permission))).all()}
    for code, description in PERMISSIONS.items():
        permission = existing.get(code)
        if permission is None:
            session.add(Permission(code=code, description=description))
        elif permission.description != description:
            permission.description = description
    await session.flush()


async def _permission_ids(session: AsyncSession, codes: list[str]) -> list[uuid.UUID]:
    if not codes:
        return []
    found = (await session.scalars(select(Permission).where(Permission.code.in_(codes)))).all()
    by_code = {p.code: p.id for p in found}
    missing = set(codes) - set(by_code)
    if missing:
        raise BadRequestError(f"Permisos desconocidos: {', '.join(sorted(missing))}")
    return [by_code[code] for code in codes]


async def _role_permission_codes(session: AsyncSession, role_id: uuid.UUID) -> list[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
        .order_by(Permission.code)
    )
    return list((await session.scalars(stmt)).all())


async def permission_codes_for_roles(
    session: AsyncSession, role_ids: set[uuid.UUID]
) -> set[str]:
    if not role_ids:
        return set()
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id.in_(role_ids))
    )
    return set((await session.scalars(stmt)).all())


async def ensure_can_grant(
    session: AsyncSession, actor_id: uuid.UUID, codes: set[str]
) -> None:
    """Impide que un usuario conceda (o retire) permisos que el mismo no tiene."""
    missing = codes - await get_user_permission_codes(session, actor_id)
    if missing:
        raise ForbiddenError(
            f"No puedes gestionar permisos que no tienes: {', '.join(sorted(missing))}"
        )


async def ensure_can_manage_user(
    session: AsyncSession, actor_id: uuid.UUID, target_id: uuid.UUID
) -> None:
    """Impide actuar sobre un usuario que tiene permisos que el actor no tiene."""
    await ensure_can_grant(
        session, actor_id, await get_user_permission_codes(session, target_id)
    )


async def owner_role_id(session: AsyncSession) -> uuid.UUID | None:
    return await session.scalar(
        select(Role.id).where(Role.name == OWNER_ROLE_NAME, Role.is_system.is_(True))
    )


async def is_owner(session: AsyncSession, user_id: uuid.UUID) -> bool:
    role_id = await owner_role_id(session)
    if role_id is None:
        return False
    found = await session.scalar(
        select(UserRole.user_id).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    return found is not None


async def ensure_other_active_owner(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Garantiza que el club conserve al menos un dueno activo ademas de `user_id`."""
    role_id = await owner_role_id(session)
    if role_id is None:
        return
    # Bloquea las filas de los duenos activos para evitar carreras entre peticiones
    # concurrentes que desactiven o degraden duenos a la vez.
    others = (
        await session.scalars(
            select(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .where(
                UserRole.role_id == role_id,
                User.is_active.is_(True),
                User.id != user_id,
            )
            .with_for_update(of=User)
        )
    ).all()
    if not others:
        raise BadRequestError("El club debe conservar al menos un dueno activo")


async def role_to_read(session: AsyncSession, role: Role) -> RoleRead:
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permissions=await _role_permission_codes(session, role.id),
    )


async def create_default_roles(session: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for name, config in DEFAULT_ROLES.items():
        role = Role(
            tenant_id=tenant_id,
            name=name,
            description=config["description"],
            is_system=True,
        )
        session.add(role)
        await session.flush()
        for permission_id in await _permission_ids(session, config["permissions"]):
            session.add(
                RolePermission(
                    role_id=role.id, permission_id=permission_id, tenant_id=tenant_id
                )
            )
        roles[name] = role
    await session.flush()
    return roles


async def sync_system_roles(session: AsyncSession) -> None:
    """Alinea los roles del sistema de todos los clubes con DEFAULT_ROLES.

    Crea los roles que falten y anade los permisos que falten. Nunca quita
    permisos: un cambio que restrinja un rol existente requiere una migracion.
    """
    tenant_ids = (await session.scalars(select(Tenant.id))).all()
    for tenant_id in tenant_ids:
        await set_tenant(session, tenant_id)
        existing = {
            role.name: role
            for role in (await session.scalars(select(Role).where(Role.is_system.is_(True)))).all()
        }
        for name, config in DEFAULT_ROLES.items():
            role = existing.get(name)
            if role is None:
                role = Role(
                    tenant_id=tenant_id,
                    name=name,
                    description=config["description"],
                    is_system=True,
                )
                session.add(role)
                await session.flush()
            elif role.description != config["description"]:
                role.description = config["description"]
            current = set(await _role_permission_codes(session, role.id))
            missing = [code for code in config["permissions"] if code not in current]
            for permission_id in await _permission_ids(session, missing):
                session.add(
                    RolePermission(
                        role_id=role.id, permission_id=permission_id, tenant_id=tenant_id
                    )
                )
        await session.flush()


async def list_permissions(session: AsyncSession) -> list[Permission]:
    return list((await session.scalars(select(Permission).order_by(Permission.code))).all())


async def list_roles(session: AsyncSession) -> list[RoleRead]:
    roles = (await session.scalars(select(Role).order_by(Role.name))).all()
    return [await role_to_read(session, role) for role in roles]


async def get_role(session: AsyncSession, role_id: uuid.UUID) -> Role:
    role = await session.get(Role, role_id)
    if role is None:
        raise NotFoundError("Rol no encontrado")
    return role


async def create_role(
    session: AsyncSession, tenant_id: uuid.UUID, data: RoleCreate, actor_id: uuid.UUID
) -> RoleRead:
    await _permission_ids(session, data.permissions)  # rechaza codigos desconocidos (400)
    await ensure_can_grant(session, actor_id, set(data.permissions))
    exists = await session.scalar(select(Role).where(Role.name == data.name))
    if exists is not None:
        raise ConflictError("Ya existe un rol con ese nombre")

    role = Role(tenant_id=tenant_id, name=data.name, description=data.description)
    session.add(role)
    await session.flush()
    await _replace_permissions(session, role, data.permissions)
    return await role_to_read(session, role)


async def update_role(
    session: AsyncSession, role_id: uuid.UUID, data: RoleUpdate, actor_id: uuid.UUID
) -> RoleRead:
    role = await get_role(session, role_id)

    if role.is_system and (
        (data.name is not None and data.name != role.name) or data.permissions is not None
    ):
        raise BadRequestError("No se puede renombrar ni cambiar los permisos de un rol del sistema")

    if data.permissions is not None:
        await _permission_ids(session, data.permissions)  # rechaza codigos desconocidos (400)
        current = set(await _role_permission_codes(session, role.id))
        await ensure_can_grant(session, actor_id, current ^ set(data.permissions))

    if data.name is not None and data.name != role.name:
        exists = await session.scalar(
            select(Role).where(Role.name == data.name, Role.id != role.id)
        )
        if exists is not None:
            raise ConflictError("Ya existe un rol con ese nombre")
        role.name = data.name

    if data.description is not None:
        role.description = data.description

    if data.permissions is not None:
        await _replace_permissions(session, role, data.permissions)

    await session.flush()
    return await role_to_read(session, role)


async def _replace_permissions(
    session: AsyncSession, role: Role, codes: list[str]
) -> None:
    await session.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    for permission_id in await _permission_ids(session, codes):
        session.add(
            RolePermission(role_id=role.id, permission_id=permission_id, tenant_id=role.tenant_id)
        )
    await session.flush()


async def delete_role(session: AsyncSession, role_id: uuid.UUID, actor_id: uuid.UUID) -> None:
    role = await get_role(session, role_id)
    if role.is_system:
        raise BadRequestError("No se puede eliminar un rol del sistema")
    await ensure_can_grant(session, actor_id, set(await _role_permission_codes(session, role.id)))
    await session.delete(role)
