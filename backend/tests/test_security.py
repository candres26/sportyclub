import pytest
from pydantic import ValidationError

from tests.conftest import _token_from_mailbox, auth_headers
from tests.test_rbac import _invite_and_login


async def _create_role(client, club, name: str, permissions: list[str]) -> dict:
    resp = await client.post(
        "/api/v1/roles",
        json={"name": name, "permissions": permissions},
        headers=auth_headers(club),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _roles_by_name(client, club) -> dict[str, dict]:
    resp = await client.get("/api/v1/roles", headers=auth_headers(club))
    return {role["name"]: role for role in resp.json()}


async def _me_id(client, club) -> str:
    return (await client.get("/api/v1/auth/me", headers=auth_headers(club))).json()["id"]


# --------------------------------------------------------------------------- #
# Configuracion
# --------------------------------------------------------------------------- #
def test_production_rejects_default_secrets():
    from app.core.config import DEFAULT_SECRET_KEY, Settings

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(environment="production", secret_key=DEFAULT_SECRET_KEY, _env_file=None)


def test_production_accepts_strong_secrets():
    from app.core.config import Settings

    settings = Settings(
        environment="production",
        secret_key="x" * 64,
        platform_admin_password="otra-clave-segura",
        postgres_password="pg-segura",
        app_db_password="app-segura",
        _env_file=None,
    )
    assert settings.is_dev is False


# --------------------------------------------------------------------------- #
# Contrasenas
# --------------------------------------------------------------------------- #
async def test_password_over_72_bytes_is_rejected_not_500(client, club_factory, mailbox):
    club = await club_factory("sec-pwd")
    roles = await _roles_by_name(client, club)
    invite = await client.post(
        "/api/v1/invitations",
        json={"email": "largo@example.com", "role_id": roles["member"]["id"]},
        headers=auth_headers(club),
    )
    assert invite.status_code == 201, invite.text
    token = await _token_from_mailbox(mailbox, "largo@example.com")

    long_password = "contraseña" * 10  # 100 caracteres, 110 bytes en UTF-8
    resp = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": token, "full_name": "Largo", "password": long_password},
        headers=club["headers"],
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# RBAC: no conceder mas de lo que se tiene
# --------------------------------------------------------------------------- #
async def test_user_manager_cannot_grant_admin_to_self(client, club_factory, mailbox):
    club = await club_factory("sec-esc")
    await _create_role(client, club, "gestor", ["users:read", "users:update"])
    gestor = await _invite_and_login(client, club, mailbox, "gestor@example.com", "gestor")

    roles = await _roles_by_name(client, club)
    gestor_id = await _me_id(client, gestor)
    resp = await client.put(
        f"/api/v1/users/{gestor_id}/roles",
        json={"role_ids": [roles["admin"]["id"]]},
        headers=auth_headers(gestor),
    )
    assert resp.status_code == 403


async def test_user_manager_cannot_deactivate_admin(client, club_factory, mailbox):
    club = await club_factory("sec-deact")
    await _create_role(client, club, "gestor", ["users:read", "users:update"])
    gestor = await _invite_and_login(client, club, mailbox, "gestor2@example.com", "gestor")

    owner_id = await _me_id(client, club)
    resp = await client.patch(
        f"/api/v1/users/{owner_id}",
        json={"is_active": False},
        headers=auth_headers(gestor),
    )
    assert resp.status_code == 403


async def test_inviter_cannot_invite_with_higher_role(client, club_factory, mailbox):
    club = await club_factory("sec-inv")
    await _create_role(client, club, "reclutador", ["invitations:create", "roles:read"])
    reclutador = await _invite_and_login(
        client, club, mailbox, "reclutador@example.com", "reclutador"
    )

    roles = await _roles_by_name(client, club)
    resp = await client.post(
        "/api/v1/invitations",
        json={"email": "nuevo-admin@example.com", "role_id": roles["admin"]["id"]},
        headers=auth_headers(reclutador),
    )
    assert resp.status_code == 403


async def test_system_role_permissions_cannot_change(client, club_factory):
    club = await club_factory("sec-sys")
    roles = await _roles_by_name(client, club)
    resp = await client.patch(
        f"/api/v1/roles/{roles['admin']['id']}",
        json={"permissions": ["club:read"]},
        headers=auth_headers(club),
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# El club no se queda sin dueno
# --------------------------------------------------------------------------- #
async def test_admin_cannot_deactivate_self(client, club_factory):
    club = await club_factory("sec-self")
    owner_id = await _me_id(client, club)
    resp = await client.patch(
        f"/api/v1/users/{owner_id}",
        json={"is_active": False},
        headers=auth_headers(club),
    )
    assert resp.status_code == 400


async def test_last_owner_cannot_drop_owner_role(client, club_factory):
    club = await club_factory("sec-last")
    roles = await _roles_by_name(client, club)
    owner_id = await _me_id(client, club)
    resp = await client.put(
        f"/api/v1/users/{owner_id}/roles",
        json={"role_ids": [roles["member"]["id"]]},
        headers=auth_headers(club),
    )
    assert resp.status_code == 400


async def test_owner_can_be_removed_when_another_owner_exists(client, club_factory, mailbox):
    club = await club_factory("sec-two")
    second = await _invite_and_login(client, club, mailbox, "owner2@example.com", "owner")
    second_id = await _me_id(client, second)

    resp = await client.delete(f"/api/v1/users/{second_id}", headers=auth_headers(club))
    assert resp.status_code == 204


# --------------------------------------------------------------------------- #
# Sesiones
# --------------------------------------------------------------------------- #
async def test_password_reset_revokes_refresh_tokens(client, club_factory, mailbox):
    club = await club_factory("sec-reset")
    forgot = await client.post(
        "/api/v1/auth/password/forgot",
        json={"email": club["owner_email"]},
        headers=club["headers"],
    )
    assert forgot.status_code == 202
    reset_msg = next(m for m in mailbox if m["type"] == "reset")
    token = reset_msg["url"].split("token=")[1]

    reset = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "password": "nuevaclave123"},
        headers=club["headers"],
    )
    assert reset.status_code == 204

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": club["refresh_token"]},
        headers=club["headers"],
    )
    assert refresh.status_code == 401


async def test_refresh_reuse_revokes_all_sessions(client, club_factory):
    club = await club_factory("sec-reuse")
    first = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": club["refresh_token"]},
        headers=club["headers"],
    )
    assert first.status_code == 200
    new_refresh = first.json()["refresh_token"]

    reuse = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": club["refresh_token"]},
        headers=club["headers"],
    )
    assert reuse.status_code == 401

    after = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh},
        headers=club["headers"],
    )
    assert after.status_code == 401


async def test_login_is_rate_limited_per_account(client, club_factory):
    club = await club_factory("sec-rate")
    for _ in range(10):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": club["owner_email"], "password": "incorrecta"},
            headers=club["headers"],
        )
        assert resp.status_code == 401

    blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": club["owner_email"], "password": "password123"},
        headers=club["headers"],
    )
    assert blocked.status_code == 429


# --------------------------------------------------------------------------- #
# Validaciones varias
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("slug", ["a", "ab", "platform"])
async def test_short_or_reserved_slug_rejected(client, platform_headers, slug):
    resp = await client.post(
        "/api/v1/platform/clubs",
        json={"name": "Corto", "slug": slug},
        headers=platform_headers,
    )
    assert resp.status_code == 422


async def test_cannot_invite_existing_user(client, club_factory):
    club = await club_factory("sec-dupinv")
    roles = await _roles_by_name(client, club)
    resp = await client.post(
        "/api/v1/invitations",
        json={"email": club["owner_email"], "role_id": roles["member"]["id"]},
        headers=auth_headers(club),
    )
    assert resp.status_code == 409


async def test_platform_admin_cannot_deactivate_self(client, platform_headers):
    other = await client.post(
        "/api/v1/platform/admins",
        json={"email": "otro@example.com", "full_name": "Otro", "password": "supersecret123"},
        headers=platform_headers,
    )
    assert other.status_code == 201

    me = await client.get("/api/v1/platform/auth/me", headers=platform_headers)
    resp = await client.patch(
        f"/api/v1/platform/admins/{me.json()['id']}",
        json={"is_active": False},
        headers=platform_headers,
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Dueno, administrador y entrenador
# --------------------------------------------------------------------------- #
async def test_admin_cannot_appoint_owner(client, club_factory, mailbox):
    club = await club_factory("sec-appoint")
    admin = await _invite_and_login(client, club, mailbox, "secre@example.com", "admin")
    admin_id = await _me_id(client, admin)

    roles = await _roles_by_name(client, club)
    resp = await client.put(
        f"/api/v1/users/{admin_id}/roles",
        json={"role_ids": [roles["owner"]["id"]]},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 403


async def test_admin_cannot_manage_roles(client, club_factory, mailbox):
    club = await club_factory("sec-adminroles")
    admin = await _invite_and_login(client, club, mailbox, "secre2@example.com", "admin")
    resp = await client.post(
        "/api/v1/roles",
        json={"name": "nuevo", "permissions": ["club:read"]},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 403


async def test_admin_can_invite_coach(client, club_factory, mailbox):
    club = await club_factory("sec-coach")
    admin = await _invite_and_login(client, club, mailbox, "secre3@example.com", "admin")
    # El admin invita con sus propias credenciales: coach ⊆ permisos de admin.
    coach = await _invite_and_login(client, admin, mailbox, "profe@example.com", "coach")
    me = await client.get("/api/v1/auth/me", headers=auth_headers(coach))
    assert me.json()["roles"] == ["coach"]


async def test_sync_system_roles_completes_existing_club(client, club_factory):
    """Un club creado antes de existir `coach` o los permisos nuevos se completa al arrancar."""
    from sqlalchemy import text

    from app.core.database import async_session_factory
    from app.modules.rbac import service as rbac_service
    from tests.conftest import _owner_session_factory

    club = await club_factory("sec-sync")
    tenant_id = club["tenant"]["id"]
    async with _owner_session_factory() as owner, owner.begin():
        await owner.execute(
            text("DELETE FROM roles WHERE tenant_id = :tid AND name = 'coach'"), {"tid": tenant_id}
        )
        await owner.execute(
            text(
                "DELETE FROM role_permissions rp USING roles r, permissions p "
                "WHERE rp.role_id = r.id AND p.id = rp.permission_id "
                "AND r.tenant_id = :tid AND r.name = 'admin' AND p.code = 'people:read'"
            ),
            {"tid": tenant_id},
        )

    async with async_session_factory() as session, session.begin():
        await rbac_service.sync_system_roles(session)

    roles = await _roles_by_name(client, club)
    assert "coach" in roles
    assert "people:read" in roles["admin"]["permissions"]
