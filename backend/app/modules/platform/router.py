import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_platform_admin
from app.modules.platform import service
from app.modules.platform.models import PlatformAdmin
from app.modules.platform.schemas import (
    PlatformAdminCreate,
    PlatformAdminRead,
    PlatformAdminUpdate,
)

router = APIRouter(prefix="/platform/admins", tags=["platform-admins"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[PlatformAdmin, Depends(get_current_platform_admin)]


@router.get("", response_model=list[PlatformAdminRead])
async def list_admins(session: DbDep, _: AdminDep) -> list[PlatformAdminRead]:
    return await service.list_admins(session)


@router.post(
    "", response_model=PlatformAdminRead, status_code=status.HTTP_201_CREATED
)
async def create_admin(
    payload: PlatformAdminCreate, session: DbDep, _: AdminDep
) -> PlatformAdminRead:
    return await service.create_admin(session, payload)


@router.patch("/{admin_id}", response_model=PlatformAdminRead)
async def update_admin(
    admin_id: uuid.UUID,
    payload: PlatformAdminUpdate,
    session: DbDep,
    current_admin: AdminDep,
) -> PlatformAdminRead:
    return await service.update_admin(session, admin_id, payload, current_admin.id)
