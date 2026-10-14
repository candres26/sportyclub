import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import TenantContext, get_tenant_context, require_permission
from app.core.email import send_invitation_email
from app.core.urls import panel_url
from app.modules.audit import service as audit_service
from app.modules.invitations import service
from app.modules.invitations.schemas import InvitationCreate, InvitationRead
from app.modules.users.models import User

router = APIRouter(prefix="/invitations", tags=["invitations"])

TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]


@router.get("", response_model=list[InvitationRead])
async def list_invitations(
    ctx: TenantDep,
    _: Annotated[object, Depends(require_permission("invitations:read"))],
) -> list[InvitationRead]:
    return await service.list_invitations(ctx.session)


@router.post("", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InvitationCreate,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("invitations:create"))],
) -> InvitationRead:
    invitation, raw_token = await service.create_invitation(
        ctx.session,
        tenant_id=ctx.tenant.id,
        email=str(payload.email),
        role_id=payload.role_id,
        invited_by_user_id=current_user.id,
    )
    invite_url = panel_url(
        ctx.tenant.slug, f"/accept-invitation?token={raw_token}"
    )
    send_invitation_email(
        to=str(payload.email),
        club_name=ctx.tenant.name,
        invite_url=invite_url,
    )
    await audit_service.record(
        ctx.session,
        tenant_id=ctx.tenant.id,
        actor_type="user",
        actor_id=current_user.id,
        action="invitation.create",
        entity_type="invitation",
        entity_id=str(invitation.id),
        data={"email": str(payload.email)},
    )
    return invitation


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    ctx: TenantDep,
    current_user: Annotated[User, Depends(require_permission("invitations:delete"))],
) -> None:
    await service.revoke_invitation(ctx.session, invitation_id)
    await audit_service.record(
        ctx.session,
        tenant_id=ctx.tenant.id,
        actor_type="user",
        actor_id=current_user.id,
        action="invitation.revoke",
        entity_type="invitation",
        entity_id=str(invitation_id),
    )
