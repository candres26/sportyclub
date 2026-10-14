from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.tenancy.resolver import extract_subdomain


class TenantMiddleware(BaseHTTPMiddleware):
    """Resuelve el club a partir del subdominio y lo deja en request.state."""

    async def dispatch(self, request: Request, call_next) -> Response:
        host = request.headers.get("host", "")
        if settings.trust_forwarded_host:
            forwarded = request.headers.get("x-forwarded-host")
            if forwarded:
                host = forwarded.split(",")[0].strip()
        request.state.tenant_slug = extract_subdomain(host, settings.base_domain)
        return await call_next(request)
