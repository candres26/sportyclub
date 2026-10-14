import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page, PageParams
from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditLogRead


async def record(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_type: str,
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> AuditLog:
    log = AuditLog(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        data=data,
    )
    session.add(log)
    await session.flush()
    return log


async def list_logs(session: AsyncSession, page: PageParams) -> Page[AuditLogRead]:
    total = await session.scalar(select(func.count()).select_from(AuditLog)) or 0
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(page.limit)
        .offset(page.offset)
    )
    logs = (await session.scalars(stmt)).all()
    return Page[AuditLogRead](
        items=[AuditLogRead.model_validate(log) for log in logs],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )
