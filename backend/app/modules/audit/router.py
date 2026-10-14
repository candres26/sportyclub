from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import TenantContext, get_tenant_context, require_permission
from app.core.pagination import Page, PageParams, page_params
from app.modules.audit import service
from app.modules.audit.schemas import AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["audit"])

TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]
PageDep = Annotated[PageParams, Depends(page_params)]


@router.get("", response_model=Page[AuditLogRead])
async def list_audit_logs(
    ctx: TenantDep,
    page: PageDep,
    _: Annotated[object, Depends(require_permission("audit:read"))],
) -> Page[AuditLogRead]:
    return await service.list_logs(ctx.session, page)
