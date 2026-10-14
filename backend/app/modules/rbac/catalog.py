"""Catalogo de permisos y roles por defecto."""

PERMISSIONS: dict[str, str] = {
    "club:read": "Ver la informacion del club",
    "club:update": "Editar la informacion del club",
    "users:read": "Ver usuarios del club",
    "users:create": "Invitar/crear usuarios",
    "users:update": "Editar usuarios y asignar roles",
    "users:delete": "Eliminar usuarios",
    "invitations:read": "Ver invitaciones",
    "invitations:create": "Crear invitaciones",
    "invitations:delete": "Revocar invitaciones",
    "roles:read": "Ver roles y permisos",
    "roles:create": "Crear roles",
    "roles:update": "Editar roles",
    "roles:delete": "Eliminar roles",
    "audit:read": "Ver el registro de auditoria",
}

ALL_PERMISSIONS: list[str] = list(PERMISSIONS.keys())

DEFAULT_ROLES: dict[str, dict] = {
    "admin": {
        "description": "Administrador del club con acceso total",
        "permissions": ALL_PERMISSIONS,
    },
    "staff": {
        "description": "Personal con acceso de lectura",
        "permissions": [
            "club:read",
            "users:read",
            "invitations:read",
            "roles:read",
            "audit:read",
        ],
    },
    "member": {
        "description": "Socio o deportista",
        "permissions": ["club:read"],
    },
}
