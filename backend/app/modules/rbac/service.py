import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.modules.rbac.catalog import DEFAULT_ROLES, PERMISSIONS
from app.modules.rbac.models import Permission, Role, RolePermission
from app.modules.rbac.schemas import RoleCreate, RoleRead, RoleUpdate


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


async def create_role(session: AsyncSession, tenant_id: uuid.UUID, data: RoleCreate) -> RoleRead:
    exists = await session.scalar(select(Role).where(Role.name == data.name))
    if exists is not None:
        raise ConflictError("Ya existe un rol con ese nombre")

    role = Role(tenant_id=tenant_id, name=data.name, description=data.description)
    session.add(role)
    await session.flush()
    await _replace_permissions(session, role, data.permissions)
    return await role_to_read(session, role)


async def update_role(
    session: AsyncSession, role_id: uuid.UUID, data: RoleUpdate
) -> RoleRead:
    role = await get_role(session, role_id)

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


async def delete_role(session: AsyncSession, role_id: uuid.UUID) -> None:
    role = await get_role(session, role_id)
    if role.is_system:
        raise BadRequestError("No se puede eliminar un rol del sistema")
    await session.delete(role)
