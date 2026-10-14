from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_platform_admin
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    PlatformMeResponse,
    RefreshRequest,
    TokenPair,
)
from app.modules.platform.models import PlatformAdmin

router = APIRouter(prefix="/platform/auth", tags=["platform-auth"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
PlatformAdminDep = Annotated[PlatformAdmin, Depends(get_current_platform_admin)]


@router.post("/login", response_model=TokenPair)
async def platform_login(payload: LoginRequest, session: DbDep) -> TokenPair:
    admin = await service.authenticate_platform(session, str(payload.email), payload.password)
    return await service.issue_platform_tokens(session, admin)


@router.post("/refresh", response_model=TokenPair)
async def platform_refresh(payload: RefreshRequest, session: DbDep) -> TokenPair:
    return await service.rotate_platform_refresh(session, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def platform_logout(payload: RefreshRequest, session: DbDep) -> None:
    await service.revoke_platform_refresh(session, payload.refresh_token)


@router.get("/me", response_model=PlatformMeResponse)
async def platform_me(admin: PlatformAdminDep) -> PlatformMeResponse:
    return PlatformMeResponse(id=admin.id, email=admin.email, full_name=admin.full_name)
