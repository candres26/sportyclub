from fastapi import APIRouter

from app.modules.audit.router import router as audit_router
from app.modules.auth.platform_router import router as platform_auth_router
from app.modules.auth.router import router as auth_router
from app.modules.clubs.router import router as clubs_router
from app.modules.invitations.router import router as invitations_router
from app.modules.platform.router import router as platform_admins_router
from app.modules.rbac.router import router as rbac_router
from app.modules.users.router import router as users_router

api_router = APIRouter(prefix="/api/v1")

# Rutas de plataforma (superadmin de plataforma)
api_router.include_router(platform_auth_router)
api_router.include_router(platform_admins_router)
api_router.include_router(clubs_router)

# Rutas del club (tenant, resueltas por subdominio)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(rbac_router)
api_router.include_router(invitations_router)
api_router.include_router(audit_router)
