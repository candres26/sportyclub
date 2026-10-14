import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_token
from app.modules.invitations.models import Invitation
from app.modules.invitations.schemas import InvitationRead
from app.modules.rbac.models import Role

INVITATION_TTL_DAYS = 7


def _new_token() -> str:
    return secrets.token_urlsafe(32)


async def _to_read(session: AsyncSession, invitation: Invitation) -> InvitationRead:
    role_name = await session.scalar(select(Role.name).where(Role.id == invitation.role_id))
    return InvitationRead(
        id=invitation.id,
        email=invitation.email,
        role_id=invitation.role_id,
        role_name=role_name,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        created_at=invitation.created_at,
    )


async def create_invitation(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    email: str,
    role_id: uuid.UUID,
    invited_by_user_id: uuid.UUID | None,
) -> tuple[InvitationRead, str]:
    email = email.lower().strip()

    role = await session.get(Role, role_id)
    if role is None:
        raise NotFoundError("Rol no encontrado en el club")

    pending = await session.scalar(
        select(Invitation).where(
            Invitation.email == email,
            Invitation.accepted_at.is_(None),
            Invitation.expires_at > datetime.now(UTC),
        )
    )
    if pending is not None:
        raise ConflictError("Ya existe una invitacion pendiente para ese correo")

    raw_token = _new_token()
    invitation = Invitation(
        tenant_id=tenant_id,
        email=email,
        role_id=role_id,
        invited_by_user_id=invited_by_user_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=INVITATION_TTL_DAYS),
    )
    session.add(invitation)
    await session.flush()
    return await _to_read(session, invitation), raw_token


async def list_invitations(session: AsyncSession) -> list[InvitationRead]:
    invitations = (
        await session.scalars(select(Invitation).order_by(Invitation.created_at.desc()))
    ).all()
    return [await _to_read(session, invitation) for invitation in invitations]


async def get_invitation(session: AsyncSession, invitation_id: uuid.UUID) -> Invitation:
    invitation = await session.get(Invitation, invitation_id)
    if invitation is None:
        raise NotFoundError("Invitacion no encontrada")
    return invitation


async def get_pending_by_token(session: AsyncSession, raw_token: str) -> Invitation | None:
    invitation = await session.scalar(
        select(Invitation).where(Invitation.token_hash == hash_token(raw_token))
    )
    if invitation is None:
        return None
    if invitation.accepted_at is not None:
        return None
    if invitation.expires_at <= datetime.now(UTC):
        return None
    return invitation


async def revoke_invitation(session: AsyncSession, invitation_id: uuid.UUID) -> None:
    invitation = await get_invitation(session, invitation_id)
    await session.delete(invitation)


async def mark_accepted(session: AsyncSession, invitation: Invitation) -> None:
    invitation.accepted_at = datetime.now(UTC)
    await session.flush()
