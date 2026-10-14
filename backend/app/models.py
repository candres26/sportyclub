"""Agrega todos los modelos para registrarlos en el metadata de SQLAlchemy."""

from app.core.database import Base
from app.modules.audit.models import AuditLog
from app.modules.auth.models import (
    PasswordResetToken,
    PlatformRefreshToken,
    RefreshToken,
)
from app.modules.clubs.models import Tenant
from app.modules.invitations.models import Invitation
from app.modules.platform.models import PlatformAdmin
from app.modules.rbac.models import Permission, Role, RolePermission, UserRole
from app.modules.users.models import User

__all__ = [
    "Base",
    "Tenant",
    "PlatformAdmin",
    "User",
    "Permission",
    "Role",
    "RolePermission",
    "UserRole",
    "RefreshToken",
    "PasswordResetToken",
    "PlatformRefreshToken",
    "Invitation",
    "AuditLog",
]
