"""owner role for existing clubs

Introduce el rol del sistema `owner` (dueno). En los clubes existentes el rol
`admin` lo tenian los duenos, asi que:

1. Renombra roles personalizados que choquen con los nuevos nombres del sistema.
2. Crea `owner` en cada club con los permisos actuales de su `admin`.
3. Pasa a `owner` a quienes tenian `admin`.
4. Quita al `admin` los permisos exclusivos del dueno.

Los demas roles nuevos (p. ej. `coach`) y los permisos nuevos los crea
`rbac_service.sync_system_roles()` al arrancar la API.

Revision ID: 0003_owner_role
Revises: 0002_tenant_composite_fks
Create Date: 2026-10-25

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0003_owner_role"
down_revision: str | None = "0002_tenant_composite_fks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Copia congelada del catalogo en el momento de esta migracion.
OWNER_ONLY = ("club:update", "roles:create", "roles:update", "roles:delete")
NEW_SYSTEM_ROLES = ("owner", "coach")
OWNER_DESCRIPTION = "Dueno del club con acceso total"
ADMIN_DESCRIPTION = "Administrador del club (sin configuracion ni gestion de roles)"
OLD_ADMIN_DESCRIPTION = "Administrador del club con acceso total"


def _codes(codes: Sequence[str]) -> str:
    return ", ".join(f"'{code}'" for code in codes)


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE roles SET name = left(name || '-personalizado', 50)
        WHERE is_system = false AND name IN ({_codes(NEW_SYSTEM_ROLES)})
        """
    )
    op.execute(
        f"""
        INSERT INTO roles (id, tenant_id, name, description, is_system)
        SELECT gen_random_uuid(), t.id, 'owner', '{OWNER_DESCRIPTION}', true
        FROM tenants t
        WHERE NOT EXISTS (
            SELECT 1 FROM roles r WHERE r.tenant_id = t.id AND r.name = 'owner'
        )
        """
    )
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id, tenant_id)
        SELECT o.id, rp.permission_id, rp.tenant_id
        FROM roles o
        JOIN roles a ON a.tenant_id = o.tenant_id AND a.name = 'admin' AND a.is_system
        JOIN role_permissions rp ON rp.role_id = a.id
        WHERE o.name = 'owner' AND o.is_system
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id, tenant_id)
        SELECT ur.user_id, o.id, ur.tenant_id
        FROM user_roles ur
        JOIN roles a ON a.id = ur.role_id AND a.name = 'admin' AND a.is_system
        JOIN roles o ON o.tenant_id = ur.tenant_id AND o.name = 'owner' AND o.is_system
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        DELETE FROM user_roles ur
        USING roles a
        WHERE ur.role_id = a.id AND a.name = 'admin' AND a.is_system
        """
    )
    op.execute(
        f"""
        DELETE FROM role_permissions rp
        USING roles a, permissions p
        WHERE rp.role_id = a.id AND a.name = 'admin' AND a.is_system
          AND p.id = rp.permission_id AND p.code IN ({_codes(OWNER_ONLY)})
        """
    )
    op.execute(
        f"UPDATE roles SET description = '{ADMIN_DESCRIPTION}' "
        "WHERE name = 'admin' AND is_system"
    )


def downgrade() -> None:
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id, tenant_id)
        SELECT a.id, p.id, a.tenant_id
        FROM roles a CROSS JOIN permissions p
        WHERE a.name = 'admin' AND a.is_system AND p.code IN ({_codes(OWNER_ONLY)})
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id, tenant_id)
        SELECT ur.user_id, a.id, ur.tenant_id
        FROM user_roles ur
        JOIN roles o ON o.id = ur.role_id AND o.name = 'owner' AND o.is_system
        JOIN roles a ON a.tenant_id = ur.tenant_id AND a.name = 'admin' AND a.is_system
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        f"UPDATE roles SET description = '{OLD_ADMIN_DESCRIPTION}' "
        "WHERE name = 'admin' AND is_system"
    )
    # Las FKs con ON DELETE CASCADE eliminan sus role_permissions y user_roles.
    op.execute("DELETE FROM roles WHERE name = 'owner' AND is_system")
