import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
)
from app.core.security import (
    burn_password_check,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.models import (
    PasswordResetToken,
    PlatformRefreshToken,
    RefreshToken,
)
from app.modules.auth.schemas import TokenPair
from app.modules.clubs.models import Tenant
from app.modules.invitations import service as invitations_service
from app.modules.platform.models import PlatformAdmin
from app.modules.rbac.models import UserRole
from app.modules.users.models import User

PASSWORD_RESET_TTL_HOURS = 1


def _now() -> datetime:
    return datetime.now(UTC)


def _expires_in_seconds() -> int:
    return settings.access_token_expire_minutes * 60


# --------------------------------------------------------------------------- #
# Tenant (club) auth
# --------------------------------------------------------------------------- #
async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await session.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None or user.password_hash is None:
        burn_password_check(password)
        raise UnauthorizedError("Credenciales invalidas")
    if not verify_password(password, user.password_hash):
        raise UnauthorizedError("Credenciales invalidas")
    if not user.is_active:
        raise ForbiddenError("Usuario inactivo")

    user.last_login_at = _now()
    await session.flush()
    return user


async def issue_tokens(session: AsyncSession, user: User) -> TokenPair:
    subject = str(user.id)
    tenant_id = str(user.tenant_id)
    access = create_access_token(subject, "tenant", tenant_id)
    refresh, _jti, expires_at = create_refresh_token(subject, "tenant", tenant_id)
    session.add(
        RefreshToken(
            tenant_id=user.tenant_id,
            user_id=user.id,
            token_hash=hash_token(refresh),
            expires_at=expires_at,
        )
    )
    await session.flush()
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=_expires_in_seconds(),
    )


async def rotate_refresh(
    session: AsyncSession, raw_refresh: str, tenant_id: uuid.UUID
) -> TokenPair:
    payload = decode_token(raw_refresh, "refresh")
    if payload.get("scope") != "tenant" or payload.get("tenant_id") != str(tenant_id):
        raise UnauthorizedError("Token de refresco no pertenece a este club")

    row = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )
    if row is not None and row.revoked_at is not None:
        # Reutilizacion de un token ya rotado: probablemente robado. Se cierran
        # todas las sesiones del usuario.
        await revoke_user_refresh_tokens(session, row.user_id)
        # Commit explicito: el 401 haria rollback y se perderia la revocacion.
        await session.commit()
        raise UnauthorizedError("Token de refresco invalido o revocado")
    if row is None or row.expires_at <= _now():
        raise UnauthorizedError("Token de refresco invalido o revocado")

    row.revoked_at = _now()

    user = await session.get(User, row.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Usuario inactivo o inexistente")

    await session.flush()
    return await issue_tokens(session, user)


async def revoke_user_refresh_tokens(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )


async def revoke_refresh(session: AsyncSession, raw_refresh: str) -> None:
    row = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = _now()
        await session.flush()


async def accept_invitation(
    session: AsyncSession,
    tenant: Tenant,
    raw_token: str,
    full_name: str,
    password: str,
) -> User:
    invitation = await invitations_service.get_pending_by_token(session, raw_token)
    if invitation is None:
        raise BadRequestError("Invitacion invalida o expirada")

    existing = await session.scalar(select(User).where(User.email == invitation.email))
    if existing is not None:
        raise ConflictError("Ya existe un usuario con ese correo en el club")

    user = User(
        tenant_id=tenant.id,
        email=invitation.email,
        full_name=full_name,
        password_hash=hash_password(password),
        is_active=True,
    )
    session.add(user)
    await session.flush()

    session.add(
        UserRole(user_id=user.id, role_id=invitation.role_id, tenant_id=tenant.id)
    )
    await invitations_service.mark_accepted(session, invitation)
    await session.flush()
    return user


async def request_password_reset(session: AsyncSession, email: str) -> str | None:
    user = await session.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None:
        return None

    raw_token = secrets.token_urlsafe(32)
    session.add(
        PasswordResetToken(
            tenant_id=user.tenant_id,
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=_now() + timedelta(hours=PASSWORD_RESET_TTL_HOURS),
        )
    )
    await session.flush()
    return raw_token


async def reset_password(session: AsyncSession, raw_token: str, password: str) -> None:
    row = await session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw_token))
    )
    if row is None or row.used_at is not None or row.expires_at <= _now():
        raise BadRequestError("Token de restablecimiento invalido o expirado")

    user = await session.get(User, row.user_id)
    if user is None:
        raise BadRequestError("Usuario inexistente")

    user.password_hash = hash_password(password)
    row.used_at = _now()
    await revoke_user_refresh_tokens(session, user.id)
    await session.flush()


async def get_user_roles(session: AsyncSession, user_id: uuid.UUID) -> list[str]:
    from app.modules.rbac.models import Role

    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .order_by(Role.name)
    )
    return list((await session.scalars(stmt)).all())


# --------------------------------------------------------------------------- #
# Platform auth
# --------------------------------------------------------------------------- #
async def authenticate_platform(
    session: AsyncSession, email: str, password: str
) -> PlatformAdmin:
    admin = await session.scalar(
        select(PlatformAdmin).where(PlatformAdmin.email == email.lower().strip())
    )
    if admin is None:
        burn_password_check(password)
        raise UnauthorizedError("Credenciales invalidas")
    if not verify_password(password, admin.password_hash):
        raise UnauthorizedError("Credenciales invalidas")
    if not admin.is_active:
        raise ForbiddenError("Administrador inactivo")
    return admin


async def issue_platform_tokens(session: AsyncSession, admin: PlatformAdmin) -> TokenPair:
    subject = str(admin.id)
    access = create_access_token(subject, "platform")
    refresh, _jti, expires_at = create_refresh_token(subject, "platform")
    session.add(
        PlatformRefreshToken(
            platform_admin_id=admin.id,
            token_hash=hash_token(refresh),
            expires_at=expires_at,
        )
    )
    await session.flush()
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=_expires_in_seconds(),
    )


async def rotate_platform_refresh(session: AsyncSession, raw_refresh: str) -> TokenPair:
    payload = decode_token(raw_refresh, "refresh")
    if payload.get("scope") != "platform":
        raise UnauthorizedError("Token de refresco invalido")

    row = await session.scalar(
        select(PlatformRefreshToken).where(
            PlatformRefreshToken.token_hash == hash_token(raw_refresh)
        )
    )
    if row is not None and row.revoked_at is not None:
        await session.execute(
            update(PlatformRefreshToken)
            .where(
                PlatformRefreshToken.platform_admin_id == row.platform_admin_id,
                PlatformRefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=_now())
        )
        await session.commit()
        raise UnauthorizedError("Token de refresco invalido o revocado")
    if row is None or row.expires_at <= _now():
        raise UnauthorizedError("Token de refresco invalido o revocado")

    row.revoked_at = _now()
    admin = await session.get(PlatformAdmin, row.platform_admin_id)
    if admin is None or not admin.is_active:
        raise UnauthorizedError("Administrador inactivo o inexistente")

    await session.flush()
    return await issue_platform_tokens(session, admin)


async def revoke_platform_refresh(session: AsyncSession, raw_refresh: str) -> None:
    row = await session.scalar(
        select(PlatformRefreshToken).where(
            PlatformRefreshToken.token_hash == hash_token(raw_refresh)
        )
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = _now()
        await session.flush()
