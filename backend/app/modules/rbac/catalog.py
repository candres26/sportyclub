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
    "disciplines:manage": "Gestionar disciplinas y metricas de la ficha tecnica",
    "people:read": "Ver deportistas y acudientes",
    "people:create": "Registrar deportistas y acudientes",
    "people:update": "Editar deportistas y acudientes",
    "people:delete": "Eliminar deportistas y acudientes",
    "athletes:read": "Ver la ficha tecnica de los deportistas",
    "athletes:update": "Editar la ficha tecnica y registrar mediciones",
}

ALL_PERMISSIONS: list[str] = list(PERMISSIONS.keys())

# Permisos que solo tiene el dueno: configuracion del club y definicion de roles.
OWNER_ONLY_PERMISSIONS: frozenset[str] = frozenset(
    {"club:update", "roles:create", "roles:update", "roles:delete"}
)

OWNER_ROLE_NAME = "owner"

DEFAULT_ROLES: dict[str, dict] = {
    OWNER_ROLE_NAME: {
        "description": "Dueno del club con acceso total",
        "permissions": ALL_PERMISSIONS,
    },
    "admin": {
        "description": "Administrador del club (sin configuracion ni gestion de roles)",
        "permissions": [p for p in ALL_PERMISSIONS if p not in OWNER_ONLY_PERMISSIONS],
    },
    "coach": {
        "description": "Entrenador: ve deportistas y gestiona su ficha tecnica",
        "permissions": ["club:read", "people:read", "athletes:read", "athletes:update"],
    },
    "staff": {
        "description": "Personal con acceso de lectura",
        "permissions": [
            "club:read",
            "users:read",
            "invitations:read",
            "roles:read",
            "audit:read",
            "people:read",
            "athletes:read",
        ],
    },
    "member": {
        "description": "Socio o deportista",
        "permissions": ["club:read"],
    },
}
