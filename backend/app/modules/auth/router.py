from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import get_current_user, get_tenant_context
from app.core.email import send_password_reset_email
from app.core.urls import panel_url
from app.modules.auth import service
from app.modules.auth.schemas import (
    AcceptInvitationRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TenantSummary,
    TokenPair,
)
from app.modules.users.models import User
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/auth", tags=["auth"])

TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, ctx: TenantDep) -> TokenPair:
    user = await service.authenticate(ctx.session, str(payload.email), payload.password)
    return await service.issue_tokens(ctx.session, user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, ctx: TenantDep) -> TokenPair:
    return await service.rotate_refresh(ctx.session, payload.refresh_token, ctx.tenant.id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, ctx: TenantDep) -> None:
    await service.revoke_refresh(ctx.session, payload.refresh_token)


@router.post("/accept-invitation", response_model=TokenPair)
async def accept_invitation(
    payload: AcceptInvitationRequest, ctx: TenantDep
) -> TokenPair:
    user = await service.accept_invitation(
        ctx.session,
        tenant=ctx.tenant,
        raw_token=payload.token,
        full_name=payload.full_name,
        password=payload.password,
    )
    return await service.issue_tokens(ctx.session, user)


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: ForgotPasswordRequest, ctx: TenantDep) -> dict[str, str]:
    raw_token = await service.request_password_reset(ctx.session, str(payload.email))
    if raw_token is not None:
        reset_url = panel_url(
            ctx.tenant.slug, f"/reset-password?token={raw_token}"
        )
        send_password_reset_email(to=str(payload.email), reset_url=reset_url)
    return {"detail": "Si el correo existe recibiras instrucciones"}


@router.post("/password/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(payload: ResetPasswordRequest, ctx: TenantDep) -> None:
    await service.reset_password(ctx.session, payload.token, payload.password)


@router.get("/me", response_model=MeResponse)
async def me(ctx: TenantDep, user: CurrentUser) -> MeResponse:
    roles = await service.get_user_roles(ctx.session, user.id)
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=roles,
        tenant=TenantSummary(
            id=ctx.tenant.id, slug=ctx.tenant.slug, name=ctx.tenant.name
        ),
    )
