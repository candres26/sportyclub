import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_platform_admin
from app.core.email import send_invitation_email
from app.core.urls import panel_url
from app.modules.clubs import service
from app.modules.clubs.schemas import (
    ClubCreatedRead,
    TenantCreate,
    TenantRead,
    TenantUpdate,
)
from app.modules.platform.models import PlatformAdmin

router = APIRouter(prefix="/platform/clubs", tags=["platform-clubs"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[PlatformAdmin, Depends(get_current_platform_admin)]


@router.get("", response_model=list[TenantRead])
async def list_clubs(session: DbDep, _: AdminDep) -> list[TenantRead]:
    return await service.list_tenants(session)


@router.post("", response_model=ClubCreatedRead, status_code=status.HTTP_201_CREATED)
async def create_club(
    payload: TenantCreate, session: DbDep, _: AdminDep
) -> ClubCreatedRead:
    tenant, raw_token = await service.create_tenant(session, payload)

    invite_url: str | None = None
    if raw_token is not None and payload.owner_email is not None:
        invite_url = panel_url(tenant.slug, f"/accept-invitation?token={raw_token}")
        send_invitation_email(
            to=str(payload.owner_email),
            club_name=tenant.name,
            invite_url=invite_url,
        )
    return ClubCreatedRead(**tenant.model_dump(), invite_url=invite_url)


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_club(
    tenant_id: uuid.UUID, session: DbDep, _: AdminDep
) -> TenantRead:
    tenant = await service.get_tenant(session, tenant_id)
    return TenantRead.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_club(
    tenant_id: uuid.UUID, payload: TenantUpdate, session: DbDep, _: AdminDep
) -> TenantRead:
    return await service.update_tenant(session, tenant_id, payload)
