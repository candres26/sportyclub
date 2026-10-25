"""composite foreign keys scoped by tenant

Las comprobaciones de FK de PostgreSQL ignoran RLS, asi que una FK simple
(`role_id -> roles.id`) acepta filas que apuntan a otro club. Las FKs pasan a
ser compuestas `(tenant_id, x_id) -> tabla(tenant_id, id)` para que la propia
BD garantice que toda referencia se queda dentro del mismo club.

Revision ID: 0002_tenant_composite_fks
Revises: 0001_initial
Create Date: 2026-10-25

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_tenant_composite_fks"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (tabla, columna, tabla referenciada, FK simple original, FK compuesta, ON DELETE)
COMPOSITE_FKS = (
    (
        "role_permissions", "role_id", "roles",
        "role_permissions_role_id_fkey", "fk_role_permissions_role_tenant", "CASCADE",
    ),
    (
        "user_roles", "user_id", "users",
        "user_roles_user_id_fkey", "fk_user_roles_user_tenant", "CASCADE",
    ),
    (
        "user_roles", "role_id", "roles",
        "user_roles_role_id_fkey", "fk_user_roles_role_tenant", "CASCADE",
    ),
    (
        "refresh_tokens", "user_id", "users",
        "refresh_tokens_user_id_fkey", "fk_refresh_tokens_user_tenant", "CASCADE",
    ),
    (
        "password_reset_tokens", "user_id", "users",
        "password_reset_tokens_user_id_fkey", "fk_password_reset_tokens_user_tenant", "CASCADE",
    ),
    (
        "invitations", "role_id", "roles",
        "invitations_role_id_fkey", "fk_invitations_role_tenant", "CASCADE",
    ),
    (
        "invitations", "invited_by_user_id", "users",
        "invitations_invited_by_user_id_fkey", "fk_invitations_invited_by_tenant",
        # PostgreSQL 15+: pone a NULL solo esa columna; un SET NULL normal
        # intentaria anular tambien tenant_id, que es NOT NULL.
        "SET NULL (invited_by_user_id)",
    ),
)

UNIQUE_TARGETS = (
    ("users", "uq_users_tenant_id_id"),
    ("roles", "uq_roles_tenant_id_id"),
)


def _check_no_cross_tenant_rows() -> None:
    bind = op.get_bind()
    problems: list[str] = []
    for table, column, ref_table, *_ in COMPOSITE_FKS:
        count = bind.execute(
            sa.text(
                f"SELECT count(*) FROM {table} t JOIN {ref_table} r ON r.id = t.{column} "
                "WHERE r.tenant_id <> t.tenant_id"
            )
        ).scalar_one()
        if count:
            problems.append(f"{table}.{column}: {count} filas")
    if problems:
        raise RuntimeError(
            "Hay referencias entre clubes distintos; corrigelas antes de migrar: "
            + "; ".join(problems)
        )


def upgrade() -> None:
    _check_no_cross_tenant_rows()

    for table, name in UNIQUE_TARGETS:
        op.create_unique_constraint(name, table, ["tenant_id", "id"])

    for table, column, ref_table, old_fk, new_fk, ondelete in COMPOSITE_FKS:
        op.drop_constraint(old_fk, table, type_="foreignkey")
        op.create_foreign_key(
            new_fk,
            table,
            ref_table,
            ["tenant_id", column],
            ["tenant_id", "id"],
            ondelete=ondelete,
        )


def downgrade() -> None:
    for table, column, ref_table, old_fk, new_fk, ondelete in COMPOSITE_FKS:
        op.drop_constraint(new_fk, table, type_="foreignkey")
        op.create_foreign_key(
            old_fk,
            table,
            ref_table,
            [column],
            ["id"],
            ondelete="SET NULL" if ondelete.startswith("SET NULL") else ondelete,
        )

    for table, name in UNIQUE_TARGETS:
        op.drop_constraint(name, table, type_="unique")
